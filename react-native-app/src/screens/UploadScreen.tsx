import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/MaterialIcons';
import { useTheme } from '@/theme';
import { StatusBar } from '@/components/layout/StatusBar';
import { Header } from '@/components/layout/Header';
import { FileUploader } from '@/components/FileUploader';
import { Button } from '@/components/ui/Button';
import { MediaFile } from '@/services/MediaUploadService';
import { useNavigation } from '@react-navigation/native';
import UploadProgressManager, { UploadProgress } from '@/services/UploadProgressManager';
import { apiClient } from '@/services/api';

export const UploadScreen: React.FC = () => {
  const theme = useTheme();
  const navigation = useNavigation();
  const [selectedFiles, setSelectedFiles] = useState<MediaFile[]>([]);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadManager] = useState(() => UploadProgressManager.getInstance());

  React.useEffect(() => {
    // Set up progress listener
    const unsubscribe = uploadManager.addListener((uploads) => {
      setUploadProgress(uploads);
    });

    return unsubscribe;
  }, [uploadManager]);

  const handleFilesSelected = (files: MediaFile[]) => {
    setSelectedFiles(files);
  };

  const handleError = (error: string) => {
    console.error('File upload error:', error);
    Alert.alert('错误', error);
  };

  const handleUploadStart = async () => {
    if (selectedFiles.length === 0) {
      Alert.alert('提示', '请先选择要上传的文件');
      return;
    }

    setIsUploading(true);
    
    try {
      // Ensure authentication before upload
      await ensureAuthenticated();
      
      // Upload files one by one
      const uploadPromises = selectedFiles.map((file) => 
        uploadFile(file)
      );
      
      const jobIds = await Promise.all(uploadPromises);
      
      // Navigate to results screen with job IDs
      navigation.navigate('Result' as never, { 
        taskId: `batch_${Date.now()}`,
        jobIds: jobIds 
      } as never);
      
    } catch (error: any) {
      console.error('Upload failed:', error);
      Alert.alert('上传失败', error.message || '文件上传过程中发生错误');
    } finally {
      setIsUploading(false);
    }
  };

  const ensureAuthenticated = async () => {
    try {
      // Always create a fresh guest user for simplicity in development
      console.log('=== CREATING FRESH GUEST USER FOR UPLOAD ===');
      
      // Clear any existing token first
      apiClient['client'].defaults.headers.Authorization = undefined;
      console.log('Cleared any existing token');
      
      // Create guest user (matching debug script format)
      const guestData = {
        username: `Guest_${Date.now()}`,
        openid: `guest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      };
      
      console.log('Creating guest user with data:', guestData);
      console.log('Sending POST request to /auth/guest');
      
      const response = await apiClient.client.post('/auth/guest', guestData);
      
      console.log('Guest auth response status:', response.status);
      console.log('Guest auth response data:', response.data);
      
      // Try multiple possible token locations (matching different response formats)
      const token = response.data?.token || 
                   response.data?.user?.token || 
                   response.data?.access_token;
      
      if (token) {
        apiClient['client'].defaults.headers.Authorization = `Bearer ${token}`;
        console.log('✅ Guest authentication successful, fresh token set');
        console.log('Token preview:', token.substring(0, 30) + '...');
      } else {
        console.error('❌ No token found in response:', response.data);
        throw new Error('Failed to get token from guest authentication');
      }
    } catch (error) {
      console.error('❌ Authentication failed:', error);
      console.error('❌ Error details:', error.response?.data || error.message);
      throw new Error('Authentication failed: ' + error.message);
    }
  };

  const uploadFile = async (file: MediaFile): Promise<string> => {
    return new Promise((resolve, reject) => {
      uploadManager.startUpload(file, {
        onProgress: (progress) => {
          console.log(`Upload progress for ${file.name}: ${progress.progress}%`);
        },
        onComplete: (result) => {
          console.log('Upload complete:', result);
          const jobId = result?.job_id || result?.id;
          if (jobId) {
            resolve(jobId);
          } else {
            reject(new Error('No job ID received from server'));
          }
        },
        onError: (error) => {
          console.error('Upload error:', error);
          reject(error);
        }
      });
    });
  };

  const getProgressForFile = (file: MediaFile): UploadProgress | null => {
    return uploadProgress.find(progress => progress.fileName === file.name) || null;
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <StatusBar />
      <Header title="文件上传" />
      
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        <View style={styles.content}>
          <Text style={[styles.title, { color: theme.colors.text.primary }]}>
            选择文件进行翻译
          </Text>
          <Text style={[styles.subtitle, { color: theme.colors.text.secondary }]}>
            支持音频和视频文件，最大50MB
          </Text>

          <FileUploader
            onFilesSelected={handleFilesSelected}
            onError={handleError}
            maxFiles={5}
            maxFileSize={100 * 1024 * 1024} // 100MB
            allowedTypes="all"
          />

          {selectedFiles.length > 0 && (
            <View style={styles.uploadButtonContainer}>
              <Button
                title={isUploading ? `上传中...` : `开始翻译 (${selectedFiles.length} 个文件)`}
                onPress={handleUploadStart}
                disabled={selectedFiles.length === 0 || isUploading}
              />
              
              {/* Upload Progress */}
              {uploadProgress.length > 0 && (
                <View style={styles.progressContainer}>
                  <Text style={[styles.progressTitle, { color: theme.colors.text.primary }]}>
                    上传进度
                  </Text>
                  {selectedFiles.map((file, index) => {
                    const progress = getProgressForFile(file);
                    if (!progress) return null;
                    
                    return (
                      <View key={index} style={[styles.progressItem, { backgroundColor: theme.colors.backgroundSecondary }]}>
                        <View style={styles.progressInfo}>
                          <Text style={[styles.progressFileName, { color: theme.colors.text.primary }]}>
                            {file.name}
                          </Text>
                          <Text style={[styles.progressText, { color: theme.colors.text.secondary }]}>
                            {progress.status === 'uploading' ? `${Math.round(progress.progress)}%` : 
                             progress.status === 'completed' ? '已完成' :
                             progress.status === 'error' ? '失败' :
                             progress.status === 'processing' ? '处理中...' : '等待中...'}
                          </Text>
                        </View>
                        
                        {progress.status === 'uploading' && (
                          <View style={styles.progressBar}>
                            <View 
                              style={[
                                styles.progressFill, 
                                { 
                                  width: `${progress.progress}%`,
                                  backgroundColor: theme.colors.primary
                                }
                              ]} 
                            />
                          </View>
                        )}
                        
                        {progress.status === 'error' && (
                          <Icon name="error" size={20} color={theme.colors.error} />
                        )}
                        
                        {progress.status === 'completed' && (
                          <Icon name="check-circle" size={20} color={theme.colors.success} />
                        )}
                      </View>
                    );
                  })}
                </View>
              )}
            </View>
          )}

          <View style={styles.featuresSection}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text.primary }]}>
              支持的文件格式
            </Text>
            
            <View style={styles.formatGrid}>
              <View style={[styles.formatCard, { backgroundColor: theme.colors.backgroundSecondary }]}>
                <Icon name="mic" size={24} color={theme.colors.primary} />
                <Text style={[styles.formatTitle, { color: theme.colors.text.primary }]}>
                  音频文件
                </Text>
                <Text style={[styles.formatList, { color: theme.colors.text.secondary }]}>
                  MP3, WAV, AAC, M4A, FLAC
                </Text>
              </View>

              <View style={[styles.formatCard, { backgroundColor: theme.colors.backgroundSecondary }]}>
                <Icon name="videocam" size={24} color={theme.colors.secondary} />
                <Text style={[styles.formatTitle, { color: theme.colors.text.primary }]}>
                  视频文件
                </Text>
                <Text style={[styles.formatList, { color: theme.colors.text.secondary }]}>
                  MP4, AVI, MOV, WMV, FLV
                </Text>
              </View>
            </View>
          </View>

          <View style={styles.tipsSection}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text.primary }]}>
              使用提示
            </Text>
            <View style={styles.tipList}>
              <View style={styles.tipItem}>
                <Icon name="check-circle" size={16} color={theme.colors.success} />
                <Text style={[styles.tipText, { color: theme.colors.text.secondary }]}>
                  音频清晰度越高，识别准确度越高
                </Text>
              </View>
              <View style={styles.tipItem}>
                <Icon name="check-circle" size={16} color={theme.colors.success} />
                <Text style={[styles.tipText, { color: theme.colors.text.secondary }]}>
                  建议使用普通话进行录音
                </Text>
              </View>
              <View style={styles.tipItem}>
                <Icon name="check-circle" size={16} color={theme.colors.success} />
                <Text style={[styles.tipText, { color: theme.colors.text.secondary }]}>
                  避免背景噪音干扰
                </Text>
              </View>
            </View>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    fontWeight: '400',
    marginBottom: 32,
    textAlign: 'center',
  },
  featuresSection: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  formatGrid: {
    flexDirection: 'row',
    gap: 16,
  },
  formatCard: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  formatTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 8,
    marginBottom: 4,
  },
  formatList: {
    fontSize: 12,
    fontWeight: '400',
    textAlign: 'center',
  },
  tipsSection: {
    marginBottom: 32,
  },
  tipList: {
    gap: 12,
  },
  tipItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  tipText: {
    fontSize: 14,
    fontWeight: '400',
    flex: 1,
  },
  uploadButtonContainer: {
    marginVertical: 24,
  },
  progressContainer: {
    marginTop: 16,
  },
  progressTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
  },
  progressItem: {
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  progressInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  progressFileName: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
    marginRight: 12,
  },
  progressText: {
    fontSize: 12,
    fontWeight: '400',
  },
  progressBar: {
    height: 4,
    backgroundColor: '#E5E7EB',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
    },
});

export default UploadScreen;