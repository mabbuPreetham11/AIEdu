import { api } from "./api";
import type { StudentClassroom, TeacherClassroom } from "../types";

export const classroomService = {
  async listTeacherClassrooms(): Promise<TeacherClassroom[]> {
    const { data } = await api.get<TeacherClassroom[]>("/classrooms/teacher");
    return data;
  },
  async createClassroom(name: string): Promise<TeacherClassroom> {
    const { data } = await api.post<TeacherClassroom>("/classrooms/", { name });
    return data;
  },
  async joinClassroom(invite_code: string): Promise<StudentClassroom> {
    const { data } = await api.post<StudentClassroom>("/classrooms/join", { invite_code });
    return data;
  },
  async listStudentClassrooms(): Promise<StudentClassroom[]> {
    const { data } = await api.get<StudentClassroom[]>("/classrooms/student");
    return data;
  },
};
