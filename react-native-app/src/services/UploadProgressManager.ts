import { Platform } from 'react-native';
import * as FileSystem from 'expo-file-system';
import { MediaFile } from '@/services/MediaUploadService';
import { apiClient } from '@/services/api';
import { UploadErrorHandler, UploadError } from '@/utils/UploadErrorHandler';

// Upload progress interface
export interface UploadProgress {
  fileId: string;
  fileName: string;
  progress: number; // 0-100
  bytesUploaded: number;
  totalBytes: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error' | 'cancelled';
  error?: string;
  uploadError?: UploadError;
  startTime?: number;
  estimatedTimeRemaining?: number;
  uploadSpeed?: number; // bytes per second
  retryCount?: number;
  maxRetries?: number;
}

// Upload task interface
export interface UploadTask {
  id: string;
  file: MediaFile;
  progress: UploadProgress;
  abortController?: AbortController;
  onProgress?: (progress: UploadProgress) => void;
  onComplete?: (result: any) => void;
  onError?: (error: UploadError) => void;
  onRetry?: (attemptCount: number) => void;
}

// Upload manager class
export class UploadProgressManager {
  private static instance: UploadProgressManager;
  private activeUploads: Map<string, UploadTask> = new Map();
  private listeners: Set<(uploads: UploadProgress[]) => void> = new Set();
  private updateInterval: NodeJS.Timeout | null = null;

  private constructor() {
    // Start progress update interval
    this.startProgressUpdates();
  }

  static getInstance(): UploadProgressManager {
    if (!UploadProgressManager.instance) {
      UploadProgressManager.instance = new UploadProgressManager();
    }
    return UploadProgressManager.instance;
  }

  /**
   * Add a progress listener
   */
  addListener(listener: (uploads: UploadProgress[]) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * Notify all listeners of progress updates
   */
  private notifyListeners(): void {
    const uploads = Array.from(this.activeUploads.values()).map(task => task.progress);
    this.listeners.forEach(listener => listener(uploads));
  }

  /**
   * Start upload progress tracking
   */
  async startUpload(
    file: MediaFile,
    options: {
      onProgress?: (progress: UploadProgress) => void;
      onComplete?: (result: any) => void;
      onError?: (error: string) => void;
    } = {}
  ): Promise<string> {
    const uploadId = this.generateUploadId();
    const abortController = new AbortController();

    const uploadProgress: UploadProgress = {
      fileId: uploadId,
      fileName: file.name,
      progress: 0,
      bytesUploaded: 0,
      totalBytes: file.size,
      status: 'pending',
      startTime: Date.now(),
      retryCount: 0,
      maxRetries: 3,
    };

    const uploadTask: UploadTask = {
      id: uploadId,
      file,
      progress: uploadProgress,
      abortController,
      ...options,
    };

    this.activeUploads.set(uploadId, uploadTask);
    this.notifyListeners();

    // Start the upload
    this.performUpload(uploadTask);

    return uploadId;
  }

  /**
   * Perform the actual file upload
   */
  private async performUpload(task: UploadTask): Promise<void> {
    try {
      // Update status to uploading
      task.progress.status = 'uploading';
      this.notifyListeners();

      // Create form data
      const formData = new FormData();
      
      if (task.file.uri.startsWith('file://') || task.file.uri.startsWith('/')) {
        formData.append('file', {
          uri: task.file.uri,
          type: task.file.mimeType || 'application/octet-stream',
          name: task.file.name,
        } as any);
      } else {
        // Handle blob or other formats
        const fileBlob = await this.uriToBlob(task.file.uri);
        formData.append('file', fileBlob, task.file.name);
      }

      formData.append('file_type', task.file.type);
      formData.append('original_filename', task.file.name);
      formData.append('file_size', task.file.size.toString());

      // Create upload request with progress tracking
      const response = await this.uploadWithProgress(
        formData,
        task,
        task.abortController?.signal
      );

      // Upload completed successfully
      task.progress.status = 'processing';
      task.progress.progress = 100;
      this.notifyListeners();

      // Call completion callback
      task.onComplete?.(response);

      // Mark as completed after processing
      setTimeout(() => {
        task.progress.status = 'completed';
        this.notifyListeners();
        
        // Remove from active uploads after a delay
        setTimeout(() => {
          this.activeUploads.delete(task.id);
          this.notifyListeners();
        }, 5000);
      }, 2000);

      } catch (error: any) {
      await this.handleUploadError(task, error);
    }
  }

  /**
   * Handle upload error with retry logic
   */
  private async handleUploadError(task: UploadTask, error: any): Promise<void> {
    const uploadError = UploadErrorHandler.createError(error, `Upload ${task.id}`);
    
    // Log error for analytics
    UploadErrorHandler.logError(uploadError, {
      fileId: task.id,
      fileName: task.file.name,
      fileSize: task.file.size,
      retryCount: task.progress.retryCount,
    });

    // Handle cancellation
    if (error.name === 'AbortError') {
      task.progress.status = 'cancelled';
      task.progress.uploadError = uploadError;
      this.notifyListeners();
      return;
    }

    // Check if we should retry
    const shouldRetry = UploadErrorHandler.shouldAutoRetry(
      uploadError, 
      task.progress.retryCount || 0
    );

    if (shouldRetry && (task.progress.retryCount || 0) < (task.progress.maxRetries || 3)) {
      // Increment retry count
      task.progress.retryCount = (task.progress.retryCount || 0) + 1;
      task.progress.status = 'pending';
      task.progress.uploadError = uploadError;
      
      this.notifyListeners();
      task.onRetry?.(task.progress.retryCount);

      // Wait before retry
      const retryDelay = UploadErrorHandler.getRetryDelay(task.progress.retryCount);
      await new Promise(resolve => setTimeout(resolve, retryDelay));

      // Retry upload
      try {
        await this.performUpload(task);
      } catch (retryError) {
        await this.handleUploadError(task, retryError);
      }
    } else {
      // Mark as failed
      task.progress.status = 'error';
      task.progress.error = uploadError.message;
      task.progress.uploadError = uploadError;
      
      this.notifyListeners();
      task.onError?.(uploadError);
      
      // Remove failed upload after a delay
      setTimeout(() => {
        this.activeUploads.delete(task.id);
        this.notifyListeners();
      }, 5000);
    }
  }

  /**
   * Upload file with progress tracking
   */
  private async uploadWithProgress(
    formData: FormData,
    task: UploadTask,
    signal?: AbortSignal
  ): Promise<any> {
    return new Promise((resolve, reject) => {
      // Use XMLHttpRequest for progress tracking
      const xhr = new XMLHttpRequest();
      
      // Track upload progress
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = (event.loaded / event.total) * 100;
          const currentTime = Date.now();
          const elapsedTime = (currentTime - (task.progress.startTime || currentTime)) / 1000;
          const uploadSpeed = event.loaded / elapsedTime;
          
          task.progress.progress = progress;
          task.progress.bytesUploaded = event.loaded;
          task.progress.uploadSpeed = uploadSpeed;
          
          // Calculate estimated time remaining
          if (uploadSpeed > 0) {
            const remainingBytes = event.total - event.loaded;
            task.progress.estimatedTimeRemaining = remainingBytes / uploadSpeed;
          }
          
          // Call progress callback
          task.onProgress?.(task.progress);
          this.notifyListeners();
        }
      });

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (error) {
            resolve({ success: true, data: xhr.responseText });
          }
        } else {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      });

      // Handle errors
      xhr.addEventListener('error', () => {
        reject(new Error('Network error during upload'));
      });

      xhr.addEventListener('abort', () => {
        reject(new Error('Upload aborted'));
      });

      // Configure and send request
      xhr.open('POST', `${apiClient['client'].defaults.baseURL}/translation/upload`);
      
      // Set up headers
      const token = apiClient['client'].defaults.headers.Authorization;
      if (token) {
        xhr.setRequestHeader('Authorization', token);
      }
      
      // Send abort signal if provided
      if (signal) {
        signal.addEventListener('abort', () => {
          xhr.abort();
        });
      }
      
      xhr.send(formData);
    });
  }

  /**
   * Convert URI to Blob
   */
  private async uriToBlob(uri: string): Promise<Blob> {
    const response = await fetch(uri);
    return response.blob();
  }

  /**
   * Cancel an upload
   */
  cancelUpload(uploadId: string): boolean {
    const task = this.activeUploads.get(uploadId);
    if (task && task.abortController) {
      task.abortController.abort();
      return true;
    }
    return false;
  }

  /**
   * Retry an upload
   */
  async retryUpload(uploadId: string): Promise<boolean> {
    const task = this.activeUploads.get(uploadId);
    if (!task) return false;

    // Reset progress
    task.progress = {
      ...task.progress,
      progress: 0,
      bytesUploaded: 0,
      status: 'pending',
      error: undefined,
      startTime: Date.now(),
      estimatedTimeRemaining: undefined,
      uploadSpeed: undefined,
    };

    this.notifyListeners();
    
    // Restart upload
    await this.performUpload(task);
    return true;
  }

  /**
   * Get current upload progress
   */
  getUploadProgress(uploadId: string): UploadProgress | null {
    const task = this.activeUploads.get(uploadId);
    return task ? task.progress : null;
  }

  /**
   * Get all active uploads
   */
  getAllUploads(): UploadProgress[] {
    return Array.from(this.activeUploads.values()).map(task => task.progress);
  }

  /**
   * Clear completed uploads
   */
  clearCompletedUploads(): void {
    const completedUploads = Array.from(this.activeUploads.entries())
      .filter(([_, task]) => 
        task.progress.status === 'completed' || 
        task.progress.status === 'error' || 
        task.progress.status === 'cancelled'
      );
    
    completedUploads.forEach(([id]) => {
      this.activeUploads.delete(id);
    });
    
    this.notifyListeners();
  }

  /**
   * Start progress update interval
   */
  private startProgressUpdates(): void {
    this.updateInterval = setInterval(() => {
      if (this.activeUploads.size > 0) {
        this.notifyListeners();
      }
    }, 1000);
  }

  /**
   * Stop progress update interval
   */
  stopProgressUpdates(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  }

  /**
   * Generate unique upload ID
   */
  private generateUploadId(): string {
    return `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Format upload speed for display
   */
  static formatUploadSpeed(bytesPerSecond: number): string {
    const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    if (bytesPerSecond === 0) return '0 B/s';
    
    const i = Math.floor(Math.log(bytesPerSecond) / Math.log(1024));
    return Math.round(bytesPerSecond / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Format time remaining for display
   */
  static formatTimeRemaining(seconds: number): string {
    if (seconds < 60) {
      return `${Math.round(seconds)}秒`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}分${remainingSeconds}秒`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}小时${minutes}分钟`;
    }
  }

  /**
   * Cleanup on app exit
   */
  cleanup(): void {
    this.stopProgressUpdates();
    this.activeUploads.clear();
    this.listeners.clear();
  }
}

export default UploadProgressManager;