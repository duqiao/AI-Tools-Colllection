import React from 'react';
import { Alert, View, Text, TouchableOpacity, StyleSheet } from 'react-native';

// Error severity levels
export enum ErrorSeverity {
  LOW = 'low',       // User can continue
  MEDIUM = 'medium', // User attention needed
  HIGH = 'high',     // User action required
  CRITICAL = 'critical' // Blocker error
}

// Error categories
export enum ErrorCategory {
  NETWORK = 'network',
  VALIDATION = 'validation',
  PERMISSION = 'permission',
  STORAGE = 'storage',
  PROCESSING = 'processing',
  AUTHENTICATION = 'authentication',
  SERVER = 'server',
  UNKNOWN = 'unknown'
}

// Standardized error interface
export interface UploadError {
  code: string;
  message: string;
  category: ErrorCategory;
  severity: ErrorSeverity;
  details?: any;
  retryable: boolean;
  userAction?: string;
  technicalDetails?: string;
}

// Error handler class
export class UploadErrorHandler {
  
  /**
   * Create standardized error from exception
   */
  static createError(error: any, context?: string): UploadError {
    // Handle common error types
    if (error.name === 'AbortError') {
      return {
        code: 'UPLOAD_CANCELLED',
        message: '上传已取消',
        category: ErrorCategory.UNKNOWN,
        severity: ErrorSeverity.LOW,
        retryable: false,
        technicalDetails: error.message,
      };
    }

    if (error.message?.includes('Network request failed')) {
      return {
        code: 'NETWORK_ERROR',
        message: '网络连接失败，请检查网络设置',
        category: ErrorCategory.NETWORK,
        severity: ErrorSeverity.MEDIUM,
        retryable: true,
        userAction: '请检查网络连接后重试',
        technicalDetails: error.message,
      };
    }

    if (error.message?.includes('timeout')) {
      return {
        code: 'UPLOAD_TIMEOUT',
        message: '上传超时，请重试',
        category: ErrorCategory.NETWORK,
        severity: ErrorSeverity.MEDIUM,
        retryable: true,
        userAction: '检查网络连接或稍后重试',
        technicalDetails: error.message,
      };
    }

    if (error.message?.includes('413') || error.message?.includes('too large')) {
      return {
        code: 'FILE_TOO_LARGE',
        message: '文件过大，请选择较小的文件',
        category: ErrorCategory.VALIDATION,
        severity: ErrorSeverity.HIGH,
        retryable: false,
        userAction: '请选择小于100MB的文件',
        technicalDetails: error.message,
      };
    }

    if (error.message?.includes('415') || error.message?.includes('unsupported')) {
      return {
        code: 'UNSUPPORTED_FORMAT',
        message: '不支持的文件格式',
        category: ErrorCategory.VALIDATION,
        severity: ErrorSeverity.HIGH,
        retryable: false,
        userAction: '请选择支持的音频或视频格式',
        technicalDetails: error.message,
      };
    }

    if (error.message?.includes('401') || error.message?.includes('Unauthorized')) {
      return {
        code: 'AUTHENTICATION_ERROR',
        message: '身份验证失败，请重新登录',
        category: ErrorCategory.AUTHENTICATION,
        severity: ErrorSeverity.HIGH,
        retryable: false,
        userAction: '请重新登录后重试',
        technicalDetails: error.message,
      };
    }

    if (error.message?.includes('403') || error.message?.includes('Forbidden')) {
      return {
        code: 'PERMISSION_DENIED',
        message: '权限不足，无法上传文件',
        category: ErrorCategory.PERMISSION,
        severity: ErrorSeverity.HIGH,
        retryable: false,
        userAction: '请联系管理员获取权限',
        technicalDetails: error.message,
      };
    }

    if (error.message?.includes('429') || error.message?.includes('rate limit')) {
      return {
        code: 'RATE_LIMIT_EXCEEDED',
        message: '上传过于频繁，请稍后重试',
        category: ErrorCategory.SERVER,
        severity: ErrorSeverity.MEDIUM,
        retryable: true,
        userAction: '请稍后重试',
        technicalDetails: error.message,
      };
    }

    if (error.message?.includes('500') || error.message?.includes('Internal Server Error')) {
      return {
        code: 'SERVER_ERROR',
        message: '服务器内部错误，请稍后重试',
        category: ErrorCategory.SERVER,
        severity: ErrorSeverity.MEDIUM,
        retryable: true,
        userAction: '稍后重试，如问题持续存在请联系客服',
        technicalDetails: error.message,
      };
    }

    if (error.message?.includes('503') || error.message?.includes('Service Unavailable')) {
      return {
        code: 'SERVICE_UNAVAILABLE',
        message: '服务暂时不可用，请稍后重试',
        category: ErrorCategory.SERVER,
        severity: ErrorSeverity.MEDIUM,
        retryable: true,
        userAction: '稍后重试，如问题持续存在请联系客服',
        technicalDetails: error.message,
      };
    }

    // Storage related errors
    if (error.message?.includes('storage') || error.message?.includes('disk space')) {
      return {
        code: 'STORAGE_ERROR',
        message: '存储空间不足',
        category: ErrorCategory.STORAGE,
        severity: ErrorSeverity.HIGH,
        retryable: false,
        userAction: '请清理设备存储空间后重试',
        technicalDetails: error.message,
      };
    }

    // Default error
    return {
      code: 'UNKNOWN_ERROR',
      message: '上传失败，请重试',
      category: ErrorCategory.UNKNOWN,
      severity: ErrorSeverity.MEDIUM,
      retryable: true,
      userAction: '请重试，如问题持续存在请联系客服',
      technicalDetails: error.message || String(error),
      details: context,
    };
  }

  /**
   * Get user-friendly message for error
   */
  static getUserMessage(error: UploadError): string {
    return error.message;
  }

  /**
   * Get detailed error information for debugging
   */
  static getDebugInfo(error: UploadError): string {
    return `Error: ${error.code}\nMessage: ${error.message}\nCategory: ${error.category}\nSeverity: ${error.severity}\nRetryable: ${error.retryable}\nTechnical Details: ${error.technicalDetails || 'N/A'}`;
  }

  /**
   * Show appropriate user alert based on error
   */
  static showErrorAlert(error: UploadError, onRetry?: () => void): void {
    const title = this.getAlertTitle(error);
    const message = this.getAlertMessage(error);
    const buttons = this.getAlertButtons(error, onRetry);

    Alert.alert(title, message, buttons, { cancelable: true });
  }

  /**
   * Get alert title based on error severity
   */
  private static getAlertTitle(error: UploadError): string {
    switch (error.severity) {
      case ErrorSeverity.CRITICAL:
        return '严重错误';
      case ErrorSeverity.HIGH:
        return '上传失败';
      case ErrorSeverity.MEDIUM:
        return '注意';
      case ErrorSeverity.LOW:
        return '提示';
      default:
        return '错误';
    }
  }

  /**
   * Get alert message based on error
   */
  private static getAlertMessage(error: UploadError): string {
    let message = error.message;
    
    if (error.userAction) {
      message += `\n\n${error.userAction}`;
    }

    // Add retry information
    if (error.retryable) {
      message += '\n\n您可以重试此操作。';
    }

    return message;
  }

  /**
   * Get alert buttons based on error
   */
  private static getAlertButtons(error: UploadError, onRetry?: () => void): any[] {
    const buttons = [];

    if (error.retryable && onRetry) {
      buttons.push({
        text: '重试',
        onPress: onRetry,
        style: 'default',
      });
    }

    buttons.push({
      text: '确定',
      style: 'cancel',
    });

    return buttons;
  }

  /**
   * Log error for analytics/debugging
   */
  static logError(error: UploadError, context?: any): void {
    const logData = {
      timestamp: new Date().toISOString(),
      error: {
        code: error.code,
        message: error.message,
        category: error.category,
        severity: error.severity,
        retryable: error.retryable,
      },
      context,
    };

    // In production, send to analytics service
    console.error('Upload Error:', JSON.stringify(logData, null, 2));
    
    // You could integrate with services like Firebase Crashlytics, Sentry, etc.
    // Crashlytics.recordError(new Error(error.message), logData);
  }

  /**
   * Check if error should be automatically retried
   */
  static shouldAutoRetry(error: UploadError, attemptCount: number): boolean {
    if (!error.retryable || attemptCount >= 3) {
      return false;
    }

    // Auto-retry only for network and server errors
    return [
      ErrorCategory.NETWORK,
      ErrorCategory.SERVER,
    ].includes(error.category);
  }

  /**
   * Get retry delay in milliseconds
   */
  static getRetryDelay(attemptCount: number): number {
    // Exponential backoff: 1s, 2s, 4s, 8s, max 30s
    const delay = Math.min(1000 * Math.pow(2, attemptCount - 1), 30000);
    return delay;
  }
}

// Error boundary component for React
export class UploadErrorBoundary extends React.Component<
  { children: React.ReactNode; onError?: (error: Error) => void },
  { hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const uploadError = UploadErrorHandler.createError(error, 'React Error Boundary');
    UploadErrorHandler.logError(uploadError, { errorInfo });
    
    this.props.onError?.(error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 }}>
          <Text style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 16 }}>
            出现了错误
          </Text>
          <Text style={{ textAlign: 'center', marginBottom: 20 }}>
            上传组件遇到了意外错误，请重试或联系客服。
          </Text>
          <TouchableOpacity
            style={{
              backgroundColor: '#007AFF',
              paddingHorizontal: 20,
              paddingVertical: 10,
              borderRadius: 8,
            }}
            onPress={() => this.setState({ hasError: false, error: undefined })}
          >
            <Text style={{ color: 'white', fontWeight: '500' }}>
              重试
            </Text>
          </TouchableOpacity>
        </View>
      );
    }

    return this.props.children;
  }
}

export default UploadErrorHandler;