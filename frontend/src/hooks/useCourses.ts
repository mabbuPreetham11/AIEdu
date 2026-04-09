import { useEffect, useState } from "react";

import { courseService } from "../services/course.service";
import type { Course } from "../types";

export const useCourses = () => {
  const [courses, setCourses] = useState<Course[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    courseService
      .list()
      .then(setCourses)
      .finally(() => setIsLoading(false));
  }, []);

  return { courses, isLoading };
};

