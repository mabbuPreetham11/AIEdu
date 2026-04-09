import { useDispatch, useSelector } from "react-redux";

import type { AppDispatch, RootState } from "../store";

export const useAuth = () => {
  const dispatch = useDispatch<AppDispatch>();
  const auth = useSelector((state: RootState) => state.auth);
  return { dispatch, ...auth };
};

