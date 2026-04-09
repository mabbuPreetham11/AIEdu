import { api } from "./api";
import type { Assignment } from "../types";

export const assignmentService = {
  async list(): Promise<Assignment[]> {
    const { data } = await api.get<Assignment[]>("/assignments/");
    return data;
  },
};

