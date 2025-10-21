import { apiClient } from '@/services/api';
import { MediaFile } from '@/services/MediaUploadService';
import { TranslationTask, TranslationRequest } from '@/types';

// Translation status enum
export enum TranslationStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

// Translation progress interface
export interface TranslationProgress {
  taskId: string;
  fileName: string;
  status: TranslationStatus;
  progress: number; // 0-100
  stage: string; // Current processing stage
  message?: string; // Status message
  result?: TranslationResult;
  error?: string;
  startTime?: number;
  estimatedTimeRemaining?: number;
}

// Translation result interface
export interface TranslationResult {
  taskId: string;
  originalText: string;
  translatedText: string;
  confidence?: number;
  language?: string;
  duration?: number;
  processedAt: string;
  metadata?: {
    speakerCount?: number;
    wordCount?: number;
    segmentCount?: number;
  };
}

// Translation service class
export class TranslationService {
  private static activeTranslations: Map<string, TranslationProgress> = new Map();
  private static progressListeners: Set<(progress: TranslationProgress[]) => void> = new Set();
  private static pollingIntervals: Map<string, NodeJS.Timeout> = new Map();

  /**
   * Start translation for uploaded files
   */
  static async startTranslation(
    files: MediaFile[],
    options: {
      sourceLanguage?: string;
      targetLanguage?: string;
      onProgress?: (progress: TranslationProgress) => void;
      onComplete?: (result: TranslationResult) => void;
      onError?: (error: string) => void;
    } = {}
  ): Promise<string[]> {
    const taskIds: string[] = [];

    try {
      for (const file of files) {
        // Create translation request
        const request: TranslationRequest = {
          fileUrl: file.uri,
          fileName: file.name,
          fileType: file.type,
          sourceLanguage: options.sourceLanguage || 'auto',
          targetLanguage: options.targetLanguage || 'zh',
        };

        // Start translation via API
        const response = await apiClient.startTranslation(request.taskId || '');
        
        if (response.success && response.data) {
          const taskId = response.data.id;
          taskIds.push(taskId);

          // Initialize progress tracking
          const progress: TranslationProgress = {
            taskId,
            fileName: file.name,
            status: TranslationStatus.PENDING,
            progress: 0,
            stage: '等待处理',
            startTime: Date.now(),
          };

          this.activeTranslations.set(taskId, progress);
          this.notifyProgressListeners();

          // Start status polling
          this.startStatusPolling(taskId, options);
        } else {
          throw new Error(response.error || 'Failed to start translation');
        }
      }

      return taskIds;
    } catch (error: any) {
      console.error('Failed to start translation:', error);
      throw error;
    }
  }

  /**
   * Start status polling for a translation task
   */
  private static startStatusPolling(
    taskId: string,
    options: {
      onProgress?: (progress: TranslationProgress) => void;
      onComplete?: (result: TranslationResult) => void;
      onError?: (error: string) => void;
    }
  ): void {
    // Clear existing polling for this task
    if (this.pollingIntervals.has(taskId)) {
      clearInterval(this.pollingIntervals.get(taskId)!);
    }

    // Start polling every 2 seconds
    const interval = setInterval(async () => {
      try {
        const response = await apiClient.getTranslationStatus(taskId);
        
        if (response.success && response.data) {
          const task = response.data;
          const progress = this.updateTranslationProgress(taskId, task);
          
          // Notify progress callback
          options.onProgress?.(progress);

          // Check if translation is complete
          if (task.status === 'completed' && task.result) {
            clearInterval(interval);
            this.pollingIntervals.delete(taskId);
            
            const result: TranslationResult = {
              taskId: task.id,
              originalText: task.result.originalText || '',
              translatedText: task.result.translatedText || '',
              confidence: task.result.confidence,
              language: task.result.language,
              duration: task.result.duration,
              processedAt: task.result.processedAt || new Date().toISOString(),
              metadata: task.result.metadata,
            };

            // Update progress with result
            progress.result = result;
            progress.status = TranslationStatus.COMPLETED;
            progress.progress = 100;
            progress.stage = '翻译完成';
            this.notifyProgressListeners();

            // Notify completion
            options.onComplete?.(result);

            // Remove from active translations after delay
            setTimeout(() => {
              this.activeTranslations.delete(taskId);
              this.notifyProgressListeners();
            }, 10000);
          } else if (task.status === 'failed') {
            clearInterval(interval);
            this.pollingIntervals.delete(taskId);
            
            progress.status = TranslationStatus.FAILED;
            progress.error = task.error || 'Translation failed';
            progress.stage = '翻译失败';
            this.notifyProgressListeners();

            // Notify error
            options.onError?.(progress.error);

            // Remove from active translations after delay
            setTimeout(() => {
              this.activeTranslations.delete(taskId);
              this.notifyProgressListeners();
            }, 10000);
          }
        }
      } catch (error: any) {
        console.error(`Failed to poll translation status for ${taskId}:`, error);
        
        // Update progress with error
        const progress = this.activeTranslations.get(taskId);
        if (progress) {
          progress.status = TranslationStatus.FAILED;
          progress.error = error.message || 'Status check failed';
          this.notifyProgressListeners();
          options.onError?.(progress.error);
        }

        clearInterval(interval);
        this.pollingIntervals.delete(taskId);
      }
    }, 2000);

    this.pollingIntervals.set(taskId, interval);
  }

  /**
   * Update translation progress from API response
   */
  private static updateTranslationProgress(
    taskId: string,
    taskData: any
  ): TranslationProgress {
    const progress = this.activeTranslations.get(taskId);
    if (!progress) {
      // Create new progress if not exists
      const newProgress: TranslationProgress = {
        taskId,
        fileName: taskData.fileName || 'Unknown',
        status: this.mapApiStatus(taskData.status),
        progress: this.calculateProgress(taskData),
        stage: this.getStageText(taskData.status, taskData.stage),
        message: taskData.message,
        startTime: taskData.startTime || Date.now(),
      };
      
      this.activeTranslations.set(taskId, newProgress);
      return newProgress;
    }

    // Update existing progress
    progress.status = this.mapApiStatus(taskData.status);
    progress.progress = this.calculateProgress(taskData);
    progress.stage = this.getStageText(taskData.status, taskData.stage);
    progress.message = taskData.message;

    return progress;
  }

  /**
   * Map API status to internal status
   */
  private static mapApiStatus(apiStatus: string): TranslationStatus {
    switch (apiStatus) {
      case 'pending':
        return TranslationStatus.PENDING;
      case 'processing':
        return TranslationStatus.PROCESSING;
      case 'completed':
        return TranslationStatus.COMPLETED;
      case 'failed':
        return TranslationStatus.FAILED;
      case 'cancelled':
        return TranslationStatus.CANCELLED;
      default:
        return TranslationStatus.PENDING;
    }
  }

  /**
   * Calculate progress percentage
   */
  private static calculateProgress(taskData: any): number {
    if (taskData.status === 'completed') return 100;
    if (taskData.status === 'failed') return 0;
    if (taskData.status === 'cancelled') return 0;
    
    // Use progress from API if available
    if (taskData.progress !== undefined) {
      return Math.min(Math.max(taskData.progress, 0), 100);
    }

    // Estimate progress based on stage
    const stageProgress: Record<string, number> = {
      'uploading': 10,
      'extracting_audio': 20,
      'speech_recognition': 60,
      'translating': 90,
      'finalizing': 95,
    };

    return stageProgress[taskData.stage] || 0;
  }

  /**
   * Get user-friendly stage text
   */
  private static getStageText(status: string, stage?: string): string {
    if (status === 'pending') return '等待处理';
    if (status === 'processing') {
      const stageMap: Record<string, string> = {
        'uploading': '上传文件中...',
        'extracting_audio': '提取音频中...',
        'speech_recognition': '语音识别中...',
        'translating': '翻译处理中...',
        'finalizing': '完成处理中...',
      };
      return stageMap[stage || ''] || '处理中...';
    }
    if (status === 'completed') return '翻译完成';
    if (status === 'failed') return '翻译失败';
    if (status === 'cancelled') return '已取消';
    
    return '处理中...';
  }

  /**
   * Cancel translation task
   */
  static async cancelTranslation(taskId: string): Promise<boolean> {
    try {
      const response = await apiClient.deleteTranslation(taskId);
      
      if (response.success) {
        // Update local progress
        const progress = this.activeTranslations.get(taskId);
        if (progress) {
          progress.status = TranslationStatus.CANCELLED;
          progress.stage = '已取消';
          this.notifyProgressListeners();
        }

        // Clear polling
        if (this.pollingIntervals.has(taskId)) {
          clearInterval(this.pollingIntervals.get(taskId)!);
          this.pollingIntervals.delete(taskId);
        }

        // Remove from active translations
        setTimeout(() => {
          this.activeTranslations.delete(taskId);
          this.notifyProgressListeners();
        }, 2000);

        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Failed to cancel translation:', error);
      return false;
    }
  }

  /**
   * Get translation progress
   */
  static getTranslationProgress(taskId: string): TranslationProgress | null {
    return this.activeTranslations.get(taskId) || null;
  }

  /**
   * Get all active translations
   */
  static getAllActiveTranslations(): TranslationProgress[] {
    return Array.from(this.activeTranslations.values());
  }

  /**
   * Add progress listener
   */
  static addProgressListener(listener: (progress: TranslationProgress[]) => void): () => void {
    this.progressListeners.add(listener);
    return () => this.progressListeners.delete(listener);
  }

  /**
   * Notify all progress listeners
   */
  private static notifyProgressListeners(): void {
    const progressList = Array.from(this.activeTranslations.values());
    this.progressListeners.forEach(listener => listener(progressList));
  }

  /**
   * Get translation history
   */
  static async getTranslationHistory(
    page: number = 1,
    perPage: number = 20
  ): Promise<{
    items: TranslationTask[];
    total: number;
    page: number;
    pages: number;
  }> {
    try {
      const response = await apiClient.getTranslationHistory(page, perPage);
      
      if (response.success && response.data) {
        return response.data;
      }
      
      return {
        items: [],
        total: 0,
        page: 1,
        pages: 0,
      };
    } catch (error) {
      console.error('Failed to get translation history:', error);
      return {
        items: [],
        total: 0,
        page: 1,
        pages: 0,
      };
    }
  }

  /**
   * Retry failed translation
   */
  static async retryTranslation(taskId: string): Promise<boolean> {
    try {
      const progress = this.activeTranslations.get(taskId);
      if (progress) {
        // Reset progress
        progress.status = TranslationStatus.PENDING;
        progress.progress = 0;
        progress.stage = '重新处理中';
        progress.error = undefined;
        this.notifyProgressListeners();

        // Restart status polling
        this.startStatusPolling(taskId, {
          onProgress: (p) => this.notifyProgressListeners(),
        });
      }

      return true;
    } catch (error) {
      console.error('Failed to retry translation:', error);
      return false;
    }
  }

  /**
   * Cleanup resources
   */
  static cleanup(): void {
    // Clear all polling intervals
    this.pollingIntervals.forEach(interval => clearInterval(interval));
    this.pollingIntervals.clear();
    
    // Clear active translations
    this.activeTranslations.clear();
    
    // Clear listeners
    this.progressListeners.clear();
  }
}

export default TranslationService;