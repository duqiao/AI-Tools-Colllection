import { useDispatch } from '@/store';
import { 
  uploadStart, 
  uploadProgress, 
  uploadSuccess, 
  uploadFailure,
  processingStart,
  updateTaskStatus,
  processingComplete,
  setTasks,
  clearCurrentTask
} from '@/store/slices/translationSlice';
import { apiClient } from './api';
import { FileInfo, TranslationTask } from '@/types';
import * as DocumentPicker from 'expo-document-picker';

export class TranslationService {
  // Pick file from device
  static async pickFile(): Promise<FileInfo | null> {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: [
          'audio/*',
          'video/*',
        ],
        copyToCacheDirectory: true,
        multiple: false,
      });

      if (result.canceled || !result.assets || result.assets.length === 0) {
        return null;
      }

      const asset = result.assets[0];
      return {
        uri: asset.uri,
        name: asset.name,
        size: asset.size || 0,
        type: this.getFileType(asset.name, asset.mimeType),
        mimeType: asset.mimeType,
      };
    } catch (error) {
      console.error('Error picking file:', error);
      return null;
    }
  }

  // Determine file type from name and MIME type
  private static getFileType(fileName: string, mimeType?: string): string {
    if (mimeType) {
      if (mimeType.startsWith('audio/')) return 'audio';
      if (mimeType.startsWith('video/')) return 'video';
    }
    
    const extension = fileName.split('.').pop()?.toLowerCase();
    if (extension) {
      const audioExtensions = ['mp3', 'wav', 'aac', 'm4a', 'flac', 'ogg'];
      const videoExtensions = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'];
      
      if (audioExtensions.includes(extension)) return 'audio';
      if (videoExtensions.includes(extension)) return 'video';
    }
    
    return 'audio'; // Default fallback
  }

  // Upload file for translation
  static async uploadFile(dispatch: any, fileInfo: FileInfo): Promise<{ success: boolean; error?: string; taskId?: string }> {
    dispatch(uploadStart());

    try {
      // Simulate upload progress
      let progressInterval: any = null;
      progressInterval = setInterval(() => {
        const currentProgress = Math.random() * 90 + 10; // 10-100%
        dispatch(uploadProgress(currentProgress));
      }, 500);

      const response = await apiClient.uploadFile(fileInfo, fileInfo.type);
      
      if (progressInterval) {
        clearInterval(progressInterval);
      }
      dispatch(uploadProgress(100));

      if (response.success && response.data) {
        const mockTask: TranslationTask = {
          id: response.data.task_id,
          user_id: 1, // Would get from auth state
          original_filename: fileInfo.name,
          original_file_url: response.data.file_url,
          file_size: fileInfo.size,
          file_type: fileInfo.type as any,
          mime_type: fileInfo.mimeType,
          processing_status: 'pending',
          is_quota_used: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };

        dispatch(uploadSuccess(mockTask));
        return { success: true, taskId: response.data.task_id };
      } else {
        const errorMessage = response.error || 'Upload failed';
        dispatch(uploadFailure(errorMessage));
        return { success: false, error: errorMessage };
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Upload failed';
      dispatch(uploadFailure(errorMessage));
      return { success: false, error: errorMessage };
    }
  }

  // Start translation processing
  static async startTranslation(dispatch: any, taskId: string): Promise<{ success: boolean; error?: string }> {
    dispatch(processingStart());

    try {
      const response = await apiClient.startTranslation(taskId);
      
      if (response.success && response.data) {
        dispatch(updateTaskStatus(response.data));
        return { success: true };
      } else {
        return { success: false, error: response.error || 'Failed to start translation' };
      }
    } catch (error: any) {
      return { success: false, error: error.message || 'Failed to start translation' };
    }
  }

  // Poll translation status
  static async pollTranslationStatus(dispatch: any, taskId: string, maxAttempts: number = 30): Promise<{ success: boolean; completed: boolean; result?: TranslationTask; error?: string }> {
    let attempts = 0;

    const poll = async (): Promise<any> => {
      attempts++;
      
      try {
        const response = await apiClient.getTranslationStatus(taskId);
        
        if (response.success && response.data) {
          dispatch(updateTaskStatus(response.data));
          
          if (response.data.processing_status === 'completed') {
            dispatch(processingComplete());
            return { success: true, completed: true, result: response.data };
          } else if (response.data.processing_status === 'failed') {
            dispatch(processingComplete());
            return { success: false, completed: true, error: response.data.processing_error || 'Translation failed' };
          } else if (attempts < maxAttempts) {
            // Still processing, continue polling
            setTimeout(poll, 2000); // Poll every 2 seconds
          } else {
            return { success: false, completed: false, error: 'Translation timeout' };
          }
        } else {
          return { success: false, completed: false, error: response.error || 'Failed to check status' };
        }
      } catch (error: any) {
        return { success: false, completed: false, error: error.message || 'Status check failed' };
      }
    };

    return poll();
  }

  // Get translation history
  static async getTranslationHistory(dispatch: any, page: number = 1): Promise<{ success: boolean; tasks?: TranslationTask[]; error?: string }> {
    try {
      const response = await apiClient.getTranslationHistory(page);
      
      if (response.success && response.data) {
        dispatch(setTasks(response.data.items));
        return { success: true, tasks: response.data.items };
      } else {
        return { success: false, error: response.error || 'Failed to get history' };
      }
    } catch (error: any) {
      return { success: false, error: error.message || 'Failed to get history' };
    }
  }

  // Delete translation
  static async deleteTranslation(taskId: string): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await apiClient.deleteTranslation(taskId);
      return { success: response.success, error: response.error || 'Failed to delete translation' };
    } catch (error: any) {
      return { success: false, error: error.message || 'Failed to delete translation' };
    }
  }

  // Clear current task
  static clearCurrentTask(dispatch: any): void {
    dispatch(clearCurrentTask());
  }

  // Simulate translation (for demo purposes)
  static async simulateTranslation(dispatch: any, taskId: string): Promise<void> {
    dispatch(processingStart());

    // Simulate processing with status updates
    const statuses: Array<{ status: 'processing' | 'completed'; text?: string; confidence?: number }> = [
      { status: 'processing' },
      { status: 'processing', text: '正在处理音频文件...' },
      { status: 'processing', text: '正在进行语音识别...' },
      { status: 'completed', text: '这是模拟的转录文本内容。实际使用时，这里会是真实的语音识别结果。', confidence: 0.95 }
    ];

    for (let i = 0; i < statuses.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
      
      const statusUpdate = statuses[i];
      const mockTask: TranslationTask = {
        id: taskId,
        user_id: 1,
        original_filename: 'demo-file.mp3',
        original_file_url: 'https://example.com/demo-file.mp3',
        file_size: 1024000,
        file_type: 'audio',
        mime_type: 'audio/mpeg',
        duration_seconds: 120,
        processing_status: statusUpdate.status,
        transcribed_text: statusUpdate.text,
        confidence_score: statusUpdate.confidence,
        word_count: statusUpdate.text ? statusUpdate.text.length : 0,
        is_quota_used: true,
        quota_deducted_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      dispatch(updateTaskStatus(mockTask));

      if (statusUpdate.status === 'completed') {
        dispatch(processingComplete());
        break;
      }
    }
  }
}

export default TranslationService;