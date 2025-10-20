import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface TranslationTask {
  id: string;
  user_id: number;
  original_filename: string;
  original_file_url: string;
  file_size: number;
  file_type: string;
  mime_type?: string;
  duration_seconds?: number;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  processing_error?: string;
  processing_started_at?: string;
  processing_completed_at?: string;
  transcribed_text?: string;
  confidence_score?: number;
  word_count?: number;
  service_provider?: string;
  service_request_id?: string;
  service_cost?: number;
  is_quota_used: boolean;
  quota_deducted_at?: string;
  created_at: string;
  updated_at: string;
}

interface TranslationState {
  tasks: TranslationTask[];
  currentTask: TranslationTask | null;
  isProcessing: boolean;
  isUploading: boolean;
  uploadProgress: number;
  error: string | null;
}

const initialState: TranslationState = {
  tasks: [],
  currentTask: null,
  isProcessing: false,
  isUploading: false,
  uploadProgress: 0,
  error: null,
};

const translationSlice = createSlice({
  name: 'translation',
  initialState,
  reducers: {
    uploadStart: (state) => {
      state.isUploading = true;
      state.uploadProgress = 0;
      state.error = null;
    },
    uploadProgress: (state, action: PayloadAction<number>) => {
      state.uploadProgress = action.payload;
    },
    uploadSuccess: (state, action: PayloadAction<TranslationTask>) => {
      state.isUploading = false;
      state.uploadProgress = 100;
      state.currentTask = action.payload;
      state.tasks.unshift(action.payload);
      state.error = null;
    },
    uploadFailure: (state, action: PayloadAction<string>) => {
      state.isUploading = false;
      state.uploadProgress = 0;
      state.error = action.payload;
    },
    processingStart: (state) => {
      state.isProcessing = true;
      state.error = null;
    },
    updateTaskStatus: (state, action: PayloadAction<TranslationTask>) => {
      const { id } = action.payload;
      const taskIndex = state.tasks.findIndex(task => task.id === id);
      if (taskIndex !== -1) {
        state.tasks[taskIndex] = action.payload;
      }
      if (state.currentTask && state.currentTask.id === id) {
        state.currentTask = action.payload;
      }
    },
    processingComplete: (state) => {
      state.isProcessing = false;
    },
    setTasks: (state, action: PayloadAction<TranslationTask[]>) => {
      state.tasks = action.payload;
    },
    clearCurrentTask: (state) => {
      state.currentTask = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  uploadStart,
  uploadProgress,
  uploadSuccess,
  uploadFailure,
  processingStart,
  updateTaskStatus,
  processingComplete,
  setTasks,
  clearCurrentTask,
  clearError,
} = translationSlice.actions;

export default translationSlice.reducer;