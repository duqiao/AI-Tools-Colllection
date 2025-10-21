import { MediaFile } from '@/services/MediaUploadService';

// File validation result interface
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

// File validation options interface
export interface ValidationOptions {
  maxFileSize?: number;
  maxAudioSize?: number;
  maxVideoSize?: number;
  allowedAudioTypes?: string[];
  allowedVideoTypes?: string[];
  allowedExtensions?: string[];
  requireDuration?: boolean;
  maxDuration?: number; // in seconds
  minDuration?: number; // in seconds
}

// Default validation options
const DEFAULT_VALIDATION_OPTIONS: ValidationOptions = {
  maxFileSize: 100 * 1024 * 1024, // 100MB
  maxAudioSize: 50 * 1024 * 1024, // 50MB
  maxVideoSize: 100 * 1024 * 1024, // 100MB
  requireDuration: false,
  maxDuration: 600, // 10 minutes
  minDuration: 1, // 1 second
};

export class FileValidator {
  
  /**
   * Validate a single media file
   */
  static validateFile(
    file: MediaFile, 
    options: ValidationOptions = {}
  ): ValidationResult {
    const opts = { ...DEFAULT_VALIDATION_OPTIONS, ...options };
    const errors: string[] = [];
    const warnings: string[] = [];

    // Basic file validation
    this.validateBasicProperties(file, errors);
    
    // File size validation
    this.validateFileSize(file, opts, errors, warnings);
    
    // File type validation
    this.validateFileType(file, opts, errors);
    
    // File extension validation
    this.validateFileExtension(file, opts, errors);
    
    // Duration validation
    this.validateDuration(file, opts, errors, warnings);
    
    // Quality validation
    this.validateQuality(file, warnings);

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
    };
  }

  /**
   * Validate multiple media files
   */
  static validateFiles(
    files: MediaFile[], 
    options: ValidationOptions = {}
  ): ValidationResult {
    const allErrors: string[] = [];
    const allWarnings: string[] = [];

    files.forEach((file, index) => {
      const result = this.validateFile(file, options);
      
      // Add file index to errors/warnings for context
      result.errors.forEach(error => {
        allErrors.push(`文件 ${index + 1}: ${error}`);
      });
      
      result.warnings.forEach(warning => {
        allWarnings.push(`文件 ${index + 1}: ${warning}`);
      });
    });

    return {
      isValid: allErrors.length === 0,
      errors: allErrors,
      warnings: allWarnings,
    };
  }

  /**
   * Validate basic file properties
   */
  private static validateBasicProperties(file: MediaFile, errors: string[]): void {
    if (!file.name || file.name.trim() === '') {
      errors.push('文件名不能为空');
    }

    if (!file.uri || file.uri.trim() === '') {
      errors.push('文件路径不能为空');
    }

    if (!file.mimeType || file.mimeType.trim() === '') {
      errors.push('文件类型不能为空');
    }

    if (file.size <= 0) {
      errors.push('文件大小必须大于0');
    }
  }

  /**
   * Validate file size
   */
  private static validateFileSize(
    file: MediaFile, 
    options: ValidationOptions,
    errors: string[],
    warnings: string[]
  ): void {
    const { maxFileSize, maxAudioSize, maxVideoSize } = options;

    // Check overall size limit
    if (maxFileSize && file.size > maxFileSize) {
      errors.push(`文件大小超过限制 (${this.formatFileSize(maxFileSize)})`);
    }

    // Check type-specific size limits
    if (file.type === 'audio' && maxAudioSize && file.size > maxAudioSize) {
      errors.push(`音频文件大小超过限制 (${this.formatFileSize(maxAudioSize)})`);
    }

    if (file.type === 'video' && maxVideoSize && file.size > maxVideoSize) {
      errors.push(`视频文件大小超过限制 (${this.formatFileSize(maxVideoSize)})`);
    }

    // Add warnings for large files
    if (file.size > 50 * 1024 * 1024) { // > 50MB
      warnings.push('文件较大，上传和处理时间可能较长');
    }
  }

  /**
   * Validate file type
   */
  private static validateFileType(
    file: MediaFile, 
    options: ValidationOptions,
    errors: string[]
  ): void {
    const { allowedAudioTypes, allowedVideoTypes } = options;

    if (file.type === 'audio' && allowedAudioTypes) {
      if (!allowedAudioTypes.includes(file.mimeType)) {
        errors.push(`不支持的音频格式: ${file.mimeType}`);
      }
    }

    if (file.type === 'video' && allowedVideoTypes) {
      if (!allowedVideoTypes.includes(file.mimeType)) {
        errors.push(`不支持的视频格式: ${file.mimeType}`);
      }
    }
  }

  /**
   * Validate file extension
   */
  private static validateFileExtension(
    file: MediaFile, 
    options: ValidationOptions,
    errors: string[]
  ): void {
    const { allowedExtensions } = options;
    
    if (allowedExtensions && allowedExtensions.length > 0) {
      const extension = this.getFileExtension(file.name);
      if (!extension || !allowedExtensions.includes(extension.toLowerCase())) {
        errors.push(`不支持的文件扩展名: ${extension || '未知'}`);
      }
    }
  }

  /**
   * Validate file duration
   */
  private static validateDuration(
    file: MediaFile, 
    options: ValidationOptions,
    errors: string[],
    warnings: string[]
  ): void {
    const { requireDuration, maxDuration, minDuration } = options;

    // Check if duration is required
    if (requireDuration && (!file.duration || file.duration <= 0)) {
      errors.push('无法获取文件时长信息');
      return;
    }

    // Validate duration range
    if (file.duration) {
      if (maxDuration && file.duration > maxDuration) {
        errors.push(`文件时长超过限制 (${Math.floor(maxDuration / 60)}分钟)`);
      }

      if (minDuration && file.duration < minDuration) {
        errors.push(`文件时长过短 (至少${minDuration}秒)`);
      }

      // Add warnings for very long files
      if (file.duration > 300) { // > 5 minutes
        warnings.push('文件时长较长，处理时间可能较长');
      }
    }
  }

  /**
   * Validate file quality (warnings only)
   */
  private static validateQuality(file: MediaFile, warnings: string[]): void {
    // Check for very small files (potential quality issues)
    if (file.type === 'audio' && file.size < 1024 * 1024) { // < 1MB
      warnings.push('音频文件较小，可能影响识别准确度');
    }

    if (file.type === 'video' && file.size < 5 * 1024 * 1024) { // < 5MB
      warnings.push('视频文件较小，可能影响识别准确度');
    }

    // Check for very short duration
    if (file.duration && file.duration < 3) {
      warnings.push('文件时长过短，可能影响识别准确度');
    }
  }

  /**
   * Get file extension from filename
   */
  private static getFileExtension(filename: string): string | null {
    const parts = filename.split('.');
    if (parts.length < 2) return null;
    return parts[parts.length - 1];
  }

  /**
   * Format file size for display
   */
  private static formatFileSize(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Get validation summary for display
   */
  static getValidationSummary(result: ValidationResult): {
    message: string;
    type: 'success' | 'warning' | 'error';
  } {
    if (!result.isValid) {
      return {
        message: `验证失败: ${result.errors[0]}`,
        type: 'error',
      };
    }

    if (result.warnings.length > 0) {
      return {
        message: `验证通过，但有${result.warnings.length}个警告`,
        type: 'warning',
      };
    }

    return {
      message: '文件验证通过',
      type: 'success',
    };
  }

  /**
   * Get detailed validation report
   */
  static getValidationReport(result: ValidationResult): {
    errors: string[];
    warnings: string[];
    summary: string;
    canProceed: boolean;
  } {
    return {
      errors: result.errors,
      warnings: result.warnings,
      summary: this.getValidationSummary(result).message,
      canProceed: result.isValid,
    };
  }

  /**
   * Check if file is likely to cause processing issues
   */
  static isProblematicFile(file: MediaFile): {
    isProblematic: boolean;
    reasons: string[];
    suggestions: string[];
  } {
    const reasons: string[] = [];
    const suggestions: string[] = [];

    // Check file size issues
    if (file.size > 50 * 1024 * 1024) {
      reasons.push('文件较大');
      suggestions.push('考虑压缩文件或分段处理');
    }

    // Check duration issues
    if (file.duration && file.duration > 300) {
      reasons.push('文件时长较长');
      suggestions.push('考虑分段处理以提高准确度');
    }

    // Check very small files
    if (file.size < 1024 * 1024) {
      reasons.push('文件较小');
      suggestions.push('确保音频质量足够清晰');
    }

    // Check very short files
    if (file.duration && file.duration < 3) {
      reasons.push('文件时长过短');
      suggestions.push('确保包含足够的语音内容');
    }

    return {
      isProblematic: reasons.length > 0,
      reasons,
      suggestions,
    };
  }
}

export default FileValidator;