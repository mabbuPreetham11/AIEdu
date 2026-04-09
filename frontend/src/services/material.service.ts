import { api } from "./api";
import type { Material, MaterialType } from "../types";

const backendOrigin = (() => {
  try {
    return new URL(import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1").origin;
  } catch {
    return "http://127.0.0.1:8000";
  }
})();

export const materialService = {
  async list(classroomId: number): Promise<Material[]> {
    const { data } = await api.get<Material[]>(`/classrooms/${classroomId}/materials`);
    return data;
  },
  async upload(payload: {
    classroomId: number;
    title: string;
    type: MaterialType;
    file?: File | null;
    url?: string;
  }): Promise<Material> {
    const formData = new FormData();
    formData.append("title", payload.title);
    formData.append("type", payload.type);
    if (payload.url) formData.append("url", payload.url);
    if (payload.file) formData.append("file", payload.file);
    const { data } = await api.post<Material>(`/classrooms/${payload.classroomId}/materials`, formData);
    return data;
  },
  async download(classroomId: number, materialId: number, filename: string): Promise<void> {
    const response = await api.get(`/classrooms/${classroomId}/materials/${materialId}/download`, {
      responseType: "blob",
    });
    const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
    const anchor = document.createElement("a");
    anchor.href = blobUrl;
    anchor.download = `${filename}.pdf`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(blobUrl);
  },
  resolvePublicUrl(fileUrl?: string | null): string | null {
    if (!fileUrl) return null;
    if (fileUrl.startsWith("http://") || fileUrl.startsWith("https://")) return fileUrl;
    return `${backendOrigin}${fileUrl}`;
  },
};

export const toYouTubeEmbedUrl = (url: string): string | null => {
  try {
    const parsed = new URL(url);
    if (parsed.hostname.includes("youtu.be")) {
      const videoId = parsed.pathname.replace("/", "");
      if (!videoId) return null;
      return `https://www.youtube.com/embed/${videoId}`;
    }
    if (parsed.hostname.includes("youtube.com")) {
      const videoId = parsed.searchParams.get("v");
      if (!videoId) return null;
      return `https://www.youtube.com/embed/${videoId}`;
    }
    return null;
  } catch {
    return null;
  }
};
