import { createSlice } from "@reduxjs/toolkit";

interface UiState {
  sidebarOpen: boolean;
}

const uiSlice = createSlice({
  name: "ui",
  initialState: { sidebarOpen: true } as UiState,
  reducers: {
    toggleSidebar(state) {
      state.sidebarOpen = !state.sidebarOpen;
    },
  },
});

export const { toggleSidebar } = uiSlice.actions;
export default uiSlice.reducer;

