class PlagiarismService:
    def scan_text(self, text: str) -> dict:
        score = 12.0 if len(text) > 200 else 4.0
        return {
            "provider": "mock",
            "score": score,
            "flagged": score > 30,
            "matches": [],
        }

