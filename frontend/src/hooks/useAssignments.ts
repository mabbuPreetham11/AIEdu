import { useEffect, useState } from "react";

import { assignmentService } from "../services/assignment.service";
import type { Assignment } from "../types";

export const useAssignments = () => {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    assignmentService
      .list()
      .then(setAssignments)
      .finally(() => setIsLoading(false));
  }, []);

  return { assignments, isLoading };
};

