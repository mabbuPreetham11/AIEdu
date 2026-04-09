import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";
import axios from "axios";

import { authService, type LoginPayload } from "../../services/auth.service";
import type { User } from "../../types";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isLoading: false,
  isAuthenticated: Boolean(localStorage.getItem("accessToken")),
  error: null,
};

export const login = createAsyncThunk("auth/login", async (payload: LoginPayload, { rejectWithValue }) => {
  try {
    return await authService.login(payload);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const detail = error.response?.data?.detail;
      if (typeof detail === "string") {
        return rejectWithValue(detail);
      }
      if (Array.isArray(detail) && detail.length > 0 && typeof detail[0]?.msg === "string") {
        return rejectWithValue(detail[0].msg);
      }
      if (!error.response) {
        return rejectWithValue("Backend is not reachable. Start backend and try again.");
      }
    }
    return rejectWithValue("Unable to sign in");
  }
});

export const loadCurrentUser = createAsyncThunk("auth/me", async () => {
  return authService.me();
});

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.isLoading = false;
        state.isAuthenticated = true;
        state.user = action.payload.user;
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = typeof action.payload === "string" ? action.payload : "Unable to sign in";
      })
      .addCase(loadCurrentUser.fulfilled, (state, action) => {
        state.user = action.payload;
        state.isAuthenticated = true;
      })
      .addCase(loadCurrentUser.rejected, (state) => {
        state.isAuthenticated = false;
        state.user = null;
      });
  },
});

export default authSlice.reducer;
