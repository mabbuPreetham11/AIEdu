from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from collections import Counter
from typing import Any

import httpx
from PyPDF2 import PdfReader

from app.core.config import settings
from app.core.exceptions import LMSException
from app.services.groq_rate_limit import acquire_groq_slot


@dataclass
class RetrievedChunk:
    text: str
    doc_name: str
    page_number: int
    score: float


def _token_chunks(tokens: list[str], chunk_size: int = 500, overlap: int = 50) -> list[list[str]]:
    if not tokens:
        return []
    if overlap >= chunk_size:
        overlap = 0

    chunks: list[list[str]] = []
    start = 0
    step = chunk_size - overlap
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk = tokens[start:end]
        if chunk:
            chunks.append(chunk)
        if end >= len(tokens):
            break
        start += step
    return chunks


class RAGService:
    def __init__(self) -> None:
        self._collection = None
        self._embedder = None
        self._fallback_path = Path("chroma") / "fallback_chunks.jsonl"
        self._fallback_path.parent.mkdir(parents=True, exist_ok=True)

    def _get_collection(self):
        if self._collection is not None:
            return self._collection

        try:
            import chromadb
        except ImportError:
            return None

        base_dir = Path("chroma")
        base_dir.mkdir(parents=True, exist_ok=True)
        client = chromadb.PersistentClient(path=str(base_dir.resolve()))
        self._collection = client.get_or_create_collection(name="aie_du_course_materials")
        return self._collection

    def _embed(self, texts: list[str]) -> list[list[float]]:
        if settings.openai_api_key:
            return self._embed_openai(texts)
        return self._embed_local(texts)

    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        if not settings.openai_api_key:
            raise LMSException(status_code=500, detail="OPENAI API key is missing for embeddings")

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": "text-embedding-ada-002", "input": texts},
            )
        if response.status_code >= 400:
            raise LMSException(status_code=500, detail=f"OpenAI embedding error: {response.text}")
        payload = response.json()
        ordered = sorted(payload["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in ordered]

    def _embed_local(self, texts: list[str]) -> list[list[float]]:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise LMSException(
                status_code=500,
                detail="No embedding backend available. Set OPENAI API key or install sentence-transformers.",
            ) from exc

        if self._embedder is None:
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
        vectors = self._embedder.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]

    def _extract_pdf_chunks(self, file_path: Path) -> list[tuple[str, int]]:
        try:
            reader = PdfReader(str(file_path))
        except Exception as exc:  # pragma: no cover - depends on parser internals
            raise LMSException(status_code=400, detail=f"Failed to read PDF: {exc}") from exc

        chunks: list[tuple[str, int]] = []
        for page_index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            tokens = text.split()
            for token_chunk in _token_chunks(tokens, chunk_size=500, overlap=50):
                chunk_text = " ".join(token_chunk).strip()
                if chunk_text:
                    chunks.append((chunk_text, page_index))
        return chunks

    def index_pdf(self, *, classroom_id: int, material_id: int, doc_name: str, file_path: Path) -> None:
        chunks = self._extract_pdf_chunks(file_path)
        if not chunks:
            return

        collection = self._get_collection()
        if collection is not None:
            texts = [item[0] for item in chunks]
            embeddings = self._embed(texts)
            ids = [f"{classroom_id}:{material_id}:{i}" for i in range(len(chunks))]
            metadatas = [
                {"doc_name": doc_name, "page_number": page_number, "classroom_id": classroom_id, "material_id": material_id}
                for _, page_number in chunks
            ]
            collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
            return

        self._index_fallback(classroom_id=classroom_id, material_id=material_id, doc_name=doc_name, chunks=chunks)

    def retrieve(self, *, classroom_id: int, question: str, k: int = 5) -> list[RetrievedChunk]:
        collection = self._get_collection()
        if collection is not None:
            question_embedding = self._embed([question])[0]
            result = collection.query(
                query_embeddings=[question_embedding],
                n_results=k,
                where={"classroom_id": classroom_id},
            )

            docs = result.get("documents", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0]
            retrieved: list[RetrievedChunk] = []
            for index, text in enumerate(docs):
                metadata = metadatas[index] if index < len(metadatas) else {}
                distance = distances[index] if index < len(distances) else 0.0
                similarity = 1.0 / (1.0 + float(distance))
                retrieved.append(
                    RetrievedChunk(
                        text=text,
                        doc_name=str(metadata.get("doc_name", "Unknown document")),
                        page_number=int(metadata.get("page_number", 1)),
                        score=similarity,
                    )
                )
            return retrieved

        return self._retrieve_fallback(classroom_id=classroom_id, question=question, k=k)

    def answer_with_llm(self, *, question: str, chunks: list[RetrievedChunk]) -> str:
        if settings.groq_api_key:
            return self._answer_with_groq(question=question, chunks=chunks)
        return self.answer_locally(question=question, chunks=chunks)

    def _answer_with_groq(self, *, question: str, chunks: list[RetrievedChunk]) -> str:
        if not settings.groq_api_key:
            raise LMSException(status_code=500, detail="GROQ API key is missing")
        acquire_groq_slot()

        context = "\n\n".join(
            [
                f"[Source {i + 1}] {chunk.doc_name} (page {chunk.page_number})\n{chunk.text}"
                for i, chunk in enumerate(chunks)
            ]
        )
        system_prompt = "Answer only from the provided course material. Do not answer from general knowledge."
        user_prompt = (
            f"Course material context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "If the answer is not in the provided context, say that the material does not contain it."
        )

        payload: dict[str, Any] = {
            "model": settings.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        if response.status_code >= 400:
            raise LMSException(status_code=500, detail=f"Groq API error: {response.text}")

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise LMSException(status_code=500, detail=f"Unexpected Groq response: {json.dumps(data)}")
        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise LMSException(status_code=500, detail=f"Unexpected Groq response: {json.dumps(data)}")
        return content.strip()

    def answer_locally(self, *, question: str, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return "I could not find relevant content in the uploaded course material."

        question_tokens = {token.lower() for token in question.split() if len(token) > 2}
        best_chunk = chunks[0]
        best_score = -1
        for chunk in chunks:
            chunk_tokens = {token.lower() for token in chunk.text.split() if len(token) > 2}
            score = len(question_tokens.intersection(chunk_tokens))
            if score > best_score:
                best_score = score
                best_chunk = chunk

        sentences = [segment.strip() for segment in best_chunk.text.replace("\n", " ").split(".") if segment.strip()]
        preview = ". ".join(sentences[:3]).strip()
        if preview and not preview.endswith("."):
            preview += "."

        return (
            "Answer from uploaded course material:\n\n"
            f"{preview if preview else best_chunk.text[:700]}\n\n"
            "Note: This answer is generated locally from retrieved document chunks."
        )

    def _index_fallback(self, *, classroom_id: int, material_id: int, doc_name: str, chunks: list[tuple[str, int]]) -> None:
        existing = []
        if self._fallback_path.exists():
            for line in self._fallback_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("classroom_id") == classroom_id and row.get("material_id") == material_id:
                    continue
                existing.append(row)

        for index, (text, page_number) in enumerate(chunks):
            existing.append(
                {
                    "id": f"{classroom_id}:{material_id}:{index}",
                    "classroom_id": classroom_id,
                    "material_id": material_id,
                    "doc_name": doc_name,
                    "page_number": page_number,
                    "text": text,
                }
            )

        content = "\n".join(json.dumps(item, ensure_ascii=True) for item in existing)
        self._fallback_path.write_text(content + ("\n" if content else ""), encoding="utf-8")

    def _retrieve_fallback(self, *, classroom_id: int, question: str, k: int) -> list[RetrievedChunk]:
        if not self._fallback_path.exists():
            return []

        question_vector = self._text_vector(question)
        if not question_vector:
            return []

        rows = []
        for line in self._fallback_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if int(row.get("classroom_id", -1)) != classroom_id:
                continue
            text = str(row.get("text", ""))
            score = self._cosine_similarity(question_vector, self._text_vector(text))
            rows.append(
                RetrievedChunk(
                    text=text,
                    doc_name=str(row.get("doc_name", "Unknown document")),
                    page_number=int(row.get("page_number", 1)),
                    score=score,
                )
            )

        rows.sort(key=lambda item: item.score, reverse=True)
        return rows[:k]

    def _text_vector(self, text: str) -> Counter[str]:
        tokens = [token.lower().strip(".,:;!?()[]{}\"'") for token in text.split()]
        filtered = [token for token in tokens if len(token) > 2]
        return Counter(filtered)

    def _cosine_similarity(self, left: Counter[str], right: Counter[str]) -> float:
        if not left or not right:
            return 0.0
        dot = 0.0
        for token, left_value in left.items():
            dot += float(left_value * right.get(token, 0))
        left_norm = math.sqrt(sum(float(value * value) for value in left.values()))
        right_norm = math.sqrt(sum(float(value * value) for value in right.values()))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return dot / (left_norm * right_norm)
