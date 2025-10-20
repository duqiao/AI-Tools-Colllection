import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import Icon from '@expo/vector-icons/MaterialIcons';
import { useTheme } from '@/theme';
import { TranslationService } from '@/services/translation';
import { useAppDispatch } from '@/store';
import { uploadStart, uploadSuccess, uploadFailure } from '@/store/slices/translationSlice';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export const FileUploader: React.FC = () => {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async () => {
    try {
      setIsUploading(true);
      dispatch(uploadStart());

      const fileInfo = await TranslationService.pickFile();
      
      if (!fileInfo) {
        dispatch(uploadFailure('未选择文件'));
        return;
      }

      const result = await TranslationService.uploadFile(dispatch, fileInfo);
      
      if (result.success && result.taskId) {
        // Start translation simulation
        await TranslationService.simulateTranslation(dispatch, result.taskId);
      } else {
        Alert.alert('上传失败', result.error || '文件上传失败，请重试');
      }
    } catch (error: any) {
      const errorMessage = error.message || '上传过程中发生错误';
      Alert.alert('上传错误', errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  const handleRecording = () => {
    Alert.alert('录音功能', '录音功能将在后续版本中实现');
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.backgroundSecondary }]}>
      <View style={styles.uploadArea}>
        <View style={[styles.iconContainer, { backgroundColor: theme.colors.primary + '20' }]}>
          <Icon name="cloud-upload" size={48} color={theme.colors.primary} />
        </View>
        
        <Text style={[styles.title, { color: theme.colors.text.primary }]}>
          上传音频或视频文件
        </Text>
        
        <Text style={[styles.subtitle, { color: theme.colors.text.secondary }]}>
          点击选择文件，或拖拽文件到此处
        </Text>
        
        <Text style={[styles.fileTypes, { color: theme.colors.text.tertiary }]}>
          支持 MP3, WAV, MP4, AVI 等格式，最大 50MB
        </Text>
      </View>

      <View style={styles.buttonContainer}>
        <Button
          title="选择文件"
          onPress={handleFileUpload}
          loading={isUploading}
          disabled={isUploading}
          style={styles.uploadButton}
        />
        
        <TouchableOpacity
          style={[styles.recordButton, { borderColor: theme.colors.primary }]}
          onPress={handleRecording}
          disabled={isUploading}
        >
          <Icon name="mic" size={20} color={theme.colors.primary} />
          <Text style={[styles.recordButtonText, { color: theme.colors.primary }]}>
            录音
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    padding: 24,
    marginBottom: 24,
  },
  uploadArea: {
    alignItems: 'center',
    marginBottom: 20,
  },
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    fontWeight: '400',
    marginBottom: 8,
    textAlign: 'center',
  },
  fileTypes: {
    fontSize: 12,
    fontWeight: '400',
    textAlign: 'center',
  },
  buttonContainer: {
    gap: 12,
  },
  uploadButton: {
    width: '100%',
  },
  recordButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    gap: 8,
  },
  recordButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});