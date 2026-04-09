import { api } from "./api";
import type { Course } from "../types";

export const courseService = {
  async list(): Promise<Course[]> {
    const { data } = await api.get<Course[]>("/courses/");
    return data;
  },
  async enroll(class_code: string) {
    const { data } = await api.post("/courses/enroll", { class_code });
    return data;
  },
};

