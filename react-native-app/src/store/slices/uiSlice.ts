import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UIState {
  isLoading: boolean;
  isOnline: boolean;
  activeScreen: string;
  toast: {
    visible: boolean;
    message: string;
    type: 'success' | 'error' | 'info';
  } | null;
  bottomSheet: {
    visible: boolean;
    content: string;
  } | null;
}

const initialState: UIState = {
  isLoading: false,
  isOnline: true,
  activeScreen: 'Home',
  toast: null,
  bottomSheet: null,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setOnlineStatus: (state, action: PayloadAction<boolean>) => {
      state.isOnline = action.payload;
    },
    setActiveScreen: (state, action: PayloadAction<string>) => {
      state.activeScreen = action.payload;
    },
    showToast: (state, action: PayloadAction<{
      message: string;
      type: 'success' | 'error' | 'info';
    }>) => {
      state.toast = {
        visible: true,
        message: action.payload.message,
        type: action.payload.type,
      };
    },
    hideToast: (state) => {
      state.toast = null;
    },
    showBottomSheet: (state, action: PayloadAction<string>) => {
      state.bottomSheet = {
        visible: true,
        content: action.payload,
      };
    },
    hideBottomSheet: (state) => {
      state.bottomSheet = null;
    },
  },
});

export const {
  setLoading,
  setOnlineStatus,
  setActiveScreen,
  showToast,
  hideToast,
  showBottomSheet,
  hideBottomSheet,
} = uiSlice.actions;

export default uiSlice.reducer;