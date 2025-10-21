import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  Modal,
  ScrollView,
} from 'react-native';
import { useTheme } from '@/theme';
import { MediaUploadService, MediaFile } from '@/services/MediaUploadService';
import { FilePreview } from './FilePreview';
import { FileValidator, ValidationResult } from '@/utils/FileValidator';

interface FileUploaderProps {
  onFilesSelected?: (files: MediaFile[]) => void;
  onError?: (error: string) => void;
  onValidationComplete?: (result: ValidationResult) => void;
  maxFiles?: number;
  maxFileSize?: number;
  maxAudioSize?: number;
  maxVideoSize?: number;
  allowedTypes?: 'audio' | 'video' | 'all';
  enableValidation?: boolean;
  disabled?: boolean;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  onFilesSelected,
  onError,
  onValidationComplete,
  maxFiles = 1,
  maxFileSize,
  maxAudioSize,
  maxVideoSize,
  allowedTypes = 'all',
  enableValidation = true,
  disabled = false,
}) => {
  const theme = useTheme();
  const [isLoading, setIsLoading] = useState(false);
  const [showPickerModal, setShowPickerModal] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<MediaFile[]>([]);

  const handleFileSelection = useCallback(async (source: 'library' | 'files') => {
    if (disabled || isLoading) return;

    try {
      setIsLoading(true);
      setShowPickerModal(false);

      let result;
      
      if (source === 'library') {
        result = await MediaUploadService.pickMediaFromLibrary({
          allowMultiple: maxFiles > 1,
          maxFiles,
          maxFileSize,
          mediaTypes: allowedTypes,
        });
      } else {
        result = await MediaUploadService.pickFiles({
          allowMultiple: maxFiles > 1,
          maxFiles,
          maxFileSize,
        });
      }

      if (result.success && result.files) {
        // Validate files if validation is enabled
        if (enableValidation) {
          const validationOptions = {
            maxFileSize,
            maxAudioSize,
            maxVideoSize,
          };
          
          const validationResult = FileValidator.validateFiles(result.files, validationOptions);
          
          // Notify validation result
          onValidationComplete?.(validationResult);
          
          if (!validationResult.isValid) {
            // Show validation errors
            const errorMessage = validationResult.errors[0] || '文件验证失败';
            onError?.(errorMessage);
            Alert.alert('文件验证失败', errorMessage);
            return;
          }
          
          // Show warnings if any
          if (validationResult.warnings.length > 0) {
            Alert.alert(
              '文件警告',
              validationResult.warnings.join('\n'),
              [{ text: '继续', onPress: () => {} }]
            );
          }
        }
        
        setSelectedFiles(result.files);
        onFilesSelected?.(result.files);
      } else {
        const errorMessage = result.error || 'File selection failed';
        onError?.(errorMessage);
        
        // Show user-friendly error message
        Alert.alert('选择失败', errorMessage);
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Unknown error occurred';
      onError?.(errorMessage);
      Alert.alert('选择失败', errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [disabled, isLoading, maxFiles, maxFileSize, allowedTypes, onFilesSelected, onError]);

  const handleRemoveFile = useCallback((index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(newFiles);
    onFilesSelected?.(newFiles);
  }, [selectedFiles, onFilesSelected]);

  const handleClearAll = useCallback(() => {
    setSelectedFiles([]);
    onFilesSelected?.([]);
  }, [onFilesSelected]);

  const renderFileItem = (file: MediaFile, index: number) => (
    <View key={index} style={styles.fileItem}>
      <FilePreview
        file={file}
        onRemove={() => handleRemoveFile(index)}
        removable={true}
      />
    </View>
  );

  const renderPickerOptions = () => (
    <ScrollView style={styles.pickerContent}>
      <TouchableOpacity
        style={[styles.pickerOption, { backgroundColor: theme.colors.background }]}
        onPress={() => handleFileSelection('library')}
        disabled={isLoading}
      >
        <Text style={[styles.pickerOptionIcon, { fontSize: 24 }]}>📱</Text>
        <View style={styles.pickerOptionText}>
          <Text style={[styles.pickerOptionTitle, { color: theme.colors.text }]}>
            从相册选择
          </Text>
          <Text style={[styles.pickerOptionSubtitle, { color: theme.colors.textSecondary }]}>
            选择相册中的音频或视频文件
          </Text>
        </View>
        {isLoading && (
          <ActivityIndicator size="small" color={theme.colors.primary} />
        )}
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.pickerOption, { backgroundColor: theme.colors.background }]}
        onPress={() => handleFileSelection('files')}
        disabled={isLoading}
      >
        <Text style={[styles.pickerOptionIcon, { fontSize: 24 }]}>📁</Text>
        <View style={styles.pickerOptionText}>
          <Text style={[styles.pickerOptionTitle, { color: theme.colors.text }]}>
            从文件选择
          </Text>
          <Text style={[styles.pickerOptionSubtitle, { color: theme.colors.textSecondary }]}>
            浏览设备中的所有音频和视频文件
          </Text>
        </View>
        {isLoading && (
          <ActivityIndicator size="small" color={theme.colors.primary} />
        )}
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.pickerOption, { backgroundColor: theme.colors.background }]}
        onPress={() => setShowPickerModal(false)}
        disabled={isLoading}
      >
        <Text style={[styles.pickerOptionIcon, { fontSize: 24 }]}>❌</Text>
        <View style={styles.pickerOptionText}>
          <Text style={[styles.pickerOptionTitle, { color: theme.colors.text }]}>
            取消
          </Text>
        </View>
      </TouchableOpacity>
    </ScrollView>
  );

  if (disabled) {
    return (
      <View style={[styles.container, styles.disabledContainer]}>
        <Text style={[styles.disabledText, { color: theme.colors.textSecondary }]}>
          文件上传功能已禁用
        </Text>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Upload Button Area */}
      {selectedFiles.length === 0 && (
        <TouchableOpacity
          style={[styles.uploadArea, { 
            backgroundColor: theme.colors.background,
            borderColor: theme.colors.border,
            borderWidth: 2,
            borderStyle: 'dashed',
          }]}
          onPress={() => setShowPickerModal(true)}
          disabled={isLoading}
          activeOpacity={0.7}
        >
          <View style={styles.uploadContent}>
            <Text style={[styles.uploadIcon, { fontSize: 48 }]}>📁</Text>
            <Text style={[styles.uploadTitle, { color: theme.colors.text }]}>
              选择音频或视频文件
            </Text>
            <Text style={[styles.uploadSubtitle, { color: theme.colors.textSecondary }]}>
              支持 MP3, WAV, M4A, MP4, MOV 等格式
            </Text>
            <Text style={[styles.uploadHint, { color: theme.colors.textSecondary }]}>
              最大文件大小: {maxFileSize ? MediaUploadService.getFormattedFileSize(maxFileSize) : '100MB'}
            </Text>
          </View>
        </TouchableOpacity>
      )}

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <View style={styles.selectedFilesContainer}>
          <View style={styles.selectedFilesHeader}>
            <Text style={[styles.selectedFilesTitle, { color: theme.colors.text }]}>
              已选择的文件 ({selectedFiles.length})
            </Text>
            <TouchableOpacity
              onPress={handleClearAll}
              style={[styles.clearButton, { borderColor: theme.colors.border }]}
            >
              <Text style={[styles.clearButtonText, { color: theme.colors.textSecondary }]}>
                清空
              </Text>
            </TouchableOpacity>
          </View>
          
          {selectedFiles.map(renderFileItem)}
          
          {selectedFiles.length < maxFiles && (
            <TouchableOpacity
              style={[styles.addMoreButton, { 
                backgroundColor: theme.colors.background,
                borderColor: theme.colors.border,
                borderWidth: 1,
              }]}
              onPress={() => setShowPickerModal(true)}
              disabled={isLoading}
            >
              <Text style={[styles.addMoreText, { color: theme.colors.primary }]}>
                + 添加更多文件
              </Text>
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Loading Indicator */}
      {isLoading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={[styles.loadingText, { color: theme.colors.textSecondary }]}>
            正在处理文件...
          </Text>
        </View>
      )}

      {/* File Picker Modal */}
      <Modal
        visible={showPickerModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowPickerModal(false)}
      >
        <View style={[styles.modalContainer, { backgroundColor: theme.colors.background }]}>
          <View style={[styles.modalHeader, { borderBottomColor: theme.colors.border }]}>
            <Text style={[styles.modalTitle, { color: theme.colors.text }]}>
              选择文件来源
            </Text>
          </View>
          {renderPickerOptions()}
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  disabledContainer: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  disabledText: {
    fontSize: 16,
    textAlign: 'center',
  },
  uploadArea: {
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 200,
  },
  uploadContent: {
    alignItems: 'center',
  },
  uploadIcon: {
    marginBottom: 16,
  },
  uploadTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  uploadSubtitle: {
    fontSize: 14,
    marginBottom: 8,
    textAlign: 'center',
  },
  uploadHint: {
    fontSize: 12,
    textAlign: 'center',
  },
  selectedFilesContainer: {
    flex: 1,
  },
  selectedFilesHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    paddingHorizontal: 4,
  },
  selectedFilesTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  clearButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
  },
  clearButtonText: {
    fontSize: 12,
  },
  fileItem: {
    marginBottom: 12,
  },
  addMoreButton: {
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  addMoreText: {
    fontSize: 16,
    fontWeight: '500',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
  },
  modalContainer: {
    flex: 1,
  },
  modalHeader: {
    padding: 16,
    borderBottomWidth: 1,
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  pickerContent: {
    flex: 1,
  },
  pickerOption: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  pickerOptionIcon: {
    marginRight: 16,
    width: 40,
    textAlign: 'center',
  },
  pickerOptionText: {
    flex: 1,
  },
  pickerOptionTitle: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 4,
  },
  pickerOptionSubtitle: {
    fontSize: 14,
    lineHeight: 20,
  },
});

export default FileUploader;