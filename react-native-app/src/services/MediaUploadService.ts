import { 
  launchImageLibraryAsync, 
  MediaTypeOptions, 
  ImagePickerResult,
  MediaType 
} from 'expo-image-picker';
import { DocumentPickerOptions, DocumentPickerResult, getDocumentAsync } from 'expo-document-picker';
import * as FileSystem from 'expo-file-system/legacy';

// Supported file types
export const SUPPORTED_AUDIO_TYPES = [
  'audio/mpeg',      // MP3
  'audio/wav',       // WAV
  'audio/x-wav',     // WAV
  'audio/mp4',       // M4A
  'audio/ogg',       // OGG
  'audio/flac',      // FLAC
  'audio/aac',       // AAC
];

export const SUPPORTED_VIDEO_TYPES = [
  'video/mp4',       // MP4
  'video/quicktime', // MOV
  'video/x-msvideo', // AVI
  'video/x-matroska', // MKV
  'video/webm',      // WebM
];

export const SUPPORTED_FILE_EXTENSIONS = [
  // Audio
  '.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac',
  // Video
  '.mp4', '.mov', '.avi', '.mkv', '.webm',
];

// File size limits (in bytes)
export const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
export const MAX_AUDIO_SIZE = 50 * 1024 * 1024; // 50MB for audio
export const MAX_VIDEO_SIZE = 100 * 1024 * 1024; // 100MB for video

// Media file interface
export interface MediaFile {
  uri: string;
  name: string;
  size: number;
  mimeType: string;
  type: 'audio' | 'video';
  duration?: number;
  lastModified?: number;
}

// File picker options
interface FilePickerOptions {
  allowMultiple?: boolean;
  maxFiles?: number;
  maxFileSize?: number;
  mediaTypes?: 'audio' | 'video' | 'all';
}

export class MediaUploadService {
  
  /**
   * Pick media files using device's media library
   */
  static async pickMediaFromLibrary(options: FilePickerOptions = {}): Promise<{
    success: boolean;
    files?: MediaFile[];
    error?: string;
  }> {
    try {
      const {
        allowMultiple = false,
        maxFiles = 1,
        maxFileSize = MAX_FILE_SIZE,
        mediaTypes = 'all'
      } = options;

      // Determine media type for image picker
      let mediaType: MediaType;
      switch (mediaTypes) {
        case 'audio':
          // Image picker doesn't support audio only, use document picker
          return await this.pickAudioFiles(options);
        case 'video':
          mediaType = MediaTypeOptions.videos;
          break;
        case 'all':
        default:
          mediaType = MediaTypeOptions.videos; // We'll handle audio separately
          break;
      }

      // Launch image picker for videos
      const result: ImagePickerResult = await launchImageLibraryAsync({
        mediaTypes: mediaType,
        allowsMultipleSelection: allowMultiple,
        maxResults: allowMultiple ? maxFiles : 1,
        quality: 1,
        videoMaxDuration: 600, // 10 minutes max
      });

      if (result.canceled) {
        return { success: false, error: 'User cancelled selection' };
      }

      const files: MediaFile[] = [];
      
      for (const asset of result.assets) {
        if (!asset.uri) continue;

        const fileInfo = await this.getFileInfo(asset.uri);
        if (!fileInfo) continue;

        // Validate file size
        if (fileInfo.size > maxFileSize) {
          return { 
            success: false, 
            error: `File ${fileInfo.name} exceeds maximum size limit` 
          };
        }

        // Validate file type
        if (!this.isValidVideoFile(fileInfo.mimeType)) {
          return { 
            success: false, 
            error: `Unsupported file type: ${fileInfo.mimeType}` 
          };
        }

        files.push({
          uri: asset.uri,
          name: asset.fileName || fileInfo.name,
          size: fileInfo.size,
          mimeType: fileInfo.mimeType,
          type: 'video',
          duration: asset.duration,
        });
      }

      // If we need audio files and didn't pick any videos, try audio picker
      if (mediaTypes === 'all' && files.length === 0) {
        return await this.pickAudioFiles(options);
      }

      return { success: true, files };

    } catch (error: any) {
      return { 
        success: false, 
        error: error.message || 'Failed to pick media from library' 
      };
    }
  }

  /**
   * Pick audio files using document picker
   */
  static async pickAudioFiles(options: FilePickerOptions = {}): Promise<{
    success: boolean;
    files?: MediaFile[];
    error?: string;
  }> {
    try {
      const {
        allowMultiple = false,
        maxFiles = 1,
        maxFileSize = MAX_AUDIO_SIZE
      } = options;

      const result: DocumentPickerResult = await getDocumentAsync({
        type: SUPPORTED_AUDIO_TYPES,
        copyToCacheDirectory: true,
        multiple: allowMultiple,
        maxFiles: allowMultiple ? maxFiles : 1,
      });

      if (result.canceled) {
        return { success: false, error: 'User cancelled selection' };
      }

      const files: MediaFile[] = [];

      for (const asset of result.assets) {
        // Validate file size
        if (asset.size && asset.size > maxFileSize) {
          return { 
            success: false, 
            error: `File ${asset.name} exceeds maximum size limit` 
          };
        }

        // Validate file type
        if (!this.isValidAudioFile(asset.mimeType)) {
          return { 
            success: false, 
            error: `Unsupported file type: ${asset.mimeType}` 
          };
        }

        // Get file info for additional details
        const fileInfo = asset.uri ? await this.getFileInfo(asset.uri) : null;

        files.push({
          uri: asset.uri,
          name: asset.name,
          size: asset.size || fileInfo?.size || 0,
          mimeType: asset.mimeType,
          type: 'audio',
          lastModified: fileInfo?.lastModified,
        });
      }

      return { success: true, files };

    } catch (error: any) {
      return { 
        success: false, 
        error: error.message || 'Failed to pick audio files' 
      };
    }
  }

  /**
   * Pick files using document picker (for all file types)
   */
  static async pickFiles(options: FilePickerOptions = {}): Promise<{
    success: boolean;
    files?: MediaFile[];
    error?: string;
  }> {
    try {
      const {
        allowMultiple = false,
        maxFiles = 1,
        maxFileSize = MAX_FILE_SIZE
      } = options;

      const result: DocumentPickerResult = await getDocumentAsync({
        type: [...SUPPORTED_AUDIO_TYPES, ...SUPPORTED_VIDEO_TYPES],
        copyToCacheDirectory: true,
        multiple: allowMultiple,
        maxFiles: allowMultiple ? maxFiles : 1,
      });

      if (result.canceled) {
        return { success: false, error: 'User cancelled selection' };
      }

      const files: MediaFile[] = [];

      for (const asset of result.assets) {
        // Validate file size
        if (asset.size && asset.size > maxFileSize) {
          return { 
            success: false, 
            error: `File ${asset.name} exceeds maximum size limit` 
          };
        }

        // Validate file type
        const isAudio = this.isValidAudioFile(asset.mimeType);
        const isVideo = this.isValidVideoFile(asset.mimeType);
        
        if (!isAudio && !isVideo) {
          return { 
            success: false, 
            error: `Unsupported file type: ${asset.mimeType}` 
          };
        }

        // Get file info for additional details
        const fileInfo = asset.uri ? await this.getFileInfo(asset.uri) : null;

        files.push({
          uri: asset.uri,
          name: asset.name,
          size: asset.size || fileInfo?.size || 0,
          mimeType: asset.mimeType,
          type: isAudio ? 'audio' : 'video',
          lastModified: fileInfo?.lastModified,
        });
      }

      return { success: true, files };

    } catch (error: any) {
      return { 
        success: false, 
        error: error.message || 'Failed to pick files' 
      };
    }
  }

  /**
   * Get file information from URI
   */
  static async getFileInfo(uri: string): Promise<{
    name: string;
    size: number;
    mimeType?: string;
    lastModified?: number;
  } | null> {
    try {
      // Extract filename from URI
      const uriParts = uri.split('/');
      const fileName = uriParts[uriParts.length - 1] || 'unknown_file';

      // Try to determine MIME type from file extension
      const extension = fileName.split('.').pop()?.toLowerCase();
      const mimeType = this.getMimeTypeFromExtension(extension);

      // Handle different platforms
      if (typeof window !== 'undefined' && window.document) {
        // Web platform - handle different URI types
        try {
          // Check if it's a blob URL or file object URL
          if (uri.startsWith('blob:') || uri.startsWith('data:')) {
            // For blob URLs, we need to fetch the actual content to get size
            try {
              const response = await fetch(uri);
              const blob = await response.blob();
              return {
                name: fileName,
                size: blob.size,
                mimeType: mimeType || blob.type || undefined,
                lastModified: undefined,
              };
            } catch (blobError) {
              console.warn('Blob fetch failed, using defaults:', blobError);
              return {
                name: fileName,
                size: 0,
                mimeType: mimeType,
              };
            }
          } else if (uri.startsWith('http://') || uri.startsWith('https://')) {
            // For HTTP URLs, try HEAD request first
            try {
              const response = await fetch(uri, { method: 'HEAD' });
              const contentLength = response.headers.get('content-length');
              const lastModified = response.headers.get('last-modified');
              
              return {
                name: fileName,
                size: contentLength ? parseInt(contentLength, 10) : 0,
                mimeType: mimeType || response.headers.get('content-type') || undefined,
                lastModified: lastModified ? new Date(lastModified).getTime() : undefined,
              };
            } catch (httpError) {
              console.warn('HTTP HEAD request failed, trying GET:', httpError);
              // Fallback to GET request to at least get some info
              try {
                const response = await fetch(uri);
                const blob = await response.blob();
                return {
                  name: fileName,
                  size: blob.size,
                  mimeType: mimeType || blob.type || undefined,
                  lastModified: undefined,
                };
              } catch (fallbackError) {
                console.warn('HTTP fallback failed, using defaults:', fallbackError);
                return {
                  name: fileName,
                  size: 0,
                  mimeType: mimeType,
                };
              }
            }
          } else {
            // For local file paths or other URI schemes on web, use defaults
            console.warn('Unsupported URI scheme on web, using defaults:', uri);
            return {
              name: fileName,
              size: 0,
              mimeType: mimeType,
            };
          }
        } catch (webError) {
          console.warn('Web file processing failed, using defaults:', webError);
          return {
            name: fileName,
            size: 0,
            mimeType: mimeType,
          };
        }
      } else {
        // Native platform - use expo-file-system
        const info = await FileSystem.getInfoAsync(uri);
        
        if (!info.exists) {
          return null;
        }

        return {
          name: fileName,
          size: info.size || 0,
          mimeType: mimeType,
          lastModified: info.modificationTime ? info.modificationTime * 1000 : undefined,
        };
      }
    } catch (error) {
      console.error('Failed to get file info:', error);
      
      // Fallback to basic info
      try {
        const uriParts = uri.split('/');
        const fileName = uriParts[uriParts.length - 1] || 'unknown_file';
        const extension = fileName.split('.').pop()?.toLowerCase();
        const mimeType = this.getMimeTypeFromExtension(extension);
        
        return {
          name: fileName,
          size: 0,
          mimeType: mimeType,
        };
      } catch (fallbackError) {
        console.error('Fallback file info failed:', fallbackError);
        return null;
      }
    }
  }

  /**
   * Get MIME type from file extension
   */
  static getMimeTypeFromExtension(extension?: string): string | undefined {
    if (!extension) return undefined;

    const extensionMap: Record<string, string> = {
      // Audio
      'mp3': 'audio/mpeg',
      'wav': 'audio/wav',
      'm4a': 'audio/mp4',
      'aac': 'audio/aac',
      'ogg': 'audio/ogg',
      'flac': 'audio/flac',
      
      // Video
      'mp4': 'video/mp4',
      'mov': 'video/quicktime',
      'avi': 'video/x-msvideo',
      'mkv': 'video/x-matroska',
      'webm': 'video/webm',
    };

    return extensionMap[extension];
  }

  /**
   * Validate if file is a supported audio type
   */
  static isValidAudioFile(mimeType?: string): boolean {
    if (!mimeType) return false;
    return SUPPORTED_AUDIO_TYPES.includes(mimeType);
  }

  /**
   * Validate if file is a supported video type
   */
  static isValidVideoFile(mimeType?: string): boolean {
    if (!mimeType) return false;
    return SUPPORTED_VIDEO_TYPES.includes(mimeType);
  }

  /**
   * Validate if file is supported (audio or video)
   */
  static isValidMediaFile(mimeType?: string): boolean {
    return this.isValidAudioFile(mimeType) || this.isValidVideoFile(mimeType);
  }

  /**
   * Check if file size is within limits
   */
  static isFileSizeValid(size: number, type: 'audio' | 'video'): boolean {
    const maxSize = type === 'audio' ? MAX_AUDIO_SIZE : MAX_VIDEO_SIZE;
    return size <= maxSize;
  }

  /**
   * Get human readable file size
   */
  static getFormattedFileSize(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Check if file picker permissions are available
   */
  static async checkPermissions(): Promise<{
    hasPermission: boolean;
    canAskAgain: boolean;
  }> {
    try {
      // For expo-image-picker, permissions are handled automatically
      // In production, you might want to explicitly check media library permissions
      return {
        hasPermission: true,
        canAskAgain: true,
      };
    } catch (error) {
      console.error('Permission check failed:', error);
      return {
        hasPermission: false,
        canAskAgain: false,
      };
    }
  }
}

export default MediaUploadService;