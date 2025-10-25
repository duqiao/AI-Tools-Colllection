import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/MaterialIcons';
import { useTheme } from '@/theme';
import { StatusBar } from '@/components/layout/StatusBar';
import { Header } from '@/components/layout/Header';
import { apiClient } from '@/services/api';

interface TranscriptionResult {
  id: string;
  originalFilename: string;
  transcribedText?: string;
  confidence?: number;
  duration?: number;
  wordCount?: number;
  status: 'pending' | 'processing' | 'completed' | 'error';
  error?: string;
  createdAt: string;
  completedAt?: string;
}

export const ResultScreen: React.FC<{ route?: { params: { taskId: string; jobIds?: string[] } } }> = ({ route }) => {
  const theme = useTheme();
  const { taskId, jobIds } = route?.params || { taskId: '', jobIds: [] };
  const [results, setResults] = useState<TranscriptionResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Initialize results for each job ID
  useEffect(() => {
    if (jobIds && jobIds.length > 0) {
      const initialResults: TranscriptionResult[] = jobIds.map(jobId => ({
        id: jobId,
        originalFilename: `文件 ${jobId.slice(0, 8)}`,
        status: 'pending',
        createdAt: new Date().toISOString(),
      }));
      setResults(initialResults);
    }
  }, [jobIds]);

  // Poll for results
  useEffect(() => {
    if (!jobIds || jobIds.length === 0) return;

    const pollResults = async () => {
      try {
        const updatedResults = [...results];
        let allCompleted = true;

        for (let i = 0; i < jobIds.length; i++) {
          const jobId = jobIds[i];
          
          try {
            interface UploadStatusResponse {
              job_id: string;
              status: 'pending' | 'processing' | 'completed' | 'failed';
              progress: number;
              file_info: {
                original_name: string;
                file_size: number;
                mime_type: string;
                duration?: number;
              };
              settings: {
                language: string;
                speaker_diarization: boolean;
              };
              results?: {
                text: string;
                language: string;
                confidence: number;
                duration: number;
                words: Array<{
                  word: string;
                  start: number;
                  end: number;
                  confidence: number;
                }>;
                segments: Array<{
                  id: number;
                  start: number;
                  end: number;
                  text: string;
                  speaker?: string;
                  confidence: number;
                }>;
              };
              processing_info: {
                started_at?: string;
                completed_at?: string;
                processing_time?: number;
                cost: number;
              };
              error?: string;
              created_at: string;
              updated_at: string;
            }

            console.log(`Fetching status for job ${jobId}...`);
            const response = await apiClient.request<UploadStatusResponse>({
              method: 'GET',
              url: `/upload/${jobId}`,
              params: {
                t: Date.now() // Add cache-busting parameter
              }
            });
            
            console.log('API Response:', {
              success: response.success,
              error: response.error,
              data: response.data,
              jobId
            });
            
            if (!response.success) {
              console.error(`API Error for job ${jobId}:`, {
                error: response.error,
                endpoint: `/upload/${jobId}`
              });
              throw new Error(response.error || 'API request failed');
            }
            
            if (!response.data) {
              console.error(`No data returned for job ${jobId}`, {
                response: {
                  success: response.success,
                  error: response.error
                },
                jobId,
                endpoint: `/upload/${jobId}`
              });
              throw new Error('No data returned from API');
            }

            const data = response.data;
            console.log(`Status for job ${jobId}:`, data.status);

            updatedResults[i] = {
              ...updatedResults[i],
              transcribedText: data.results?.text,
              confidence: data.results?.confidence,
              duration: data.file_info?.duration,
              wordCount: (data.results?.words || []).length,
              status: data.status === 'completed' ? 'completed' :
                     data.status === 'failed' ? 'error' :
                     data.status === 'processing' ? 'processing' : 'pending',
              error: data.error,
              completedAt: data.processing_info?.completed_at,
            };

            if (data.status !== 'completed' && data.status !== 'failed') {
              allCompleted = false;
            }
          } catch (error: any) {
            const errorMessage = error?.message || 'Unknown error';
            console.error(`Failed to fetch result for job ${jobId}:`, {
              error: {
                name: error?.name,
                message: error?.message,
                stack: error?.stack,
                code: error?.code,
                response: error?.response?.data,
                status: error?.response?.status,
              },
              jobId,
              endpoint: `/upload/${jobId}`
            });
            updatedResults[i] = {
              ...updatedResults[i],
              status: 'error',
              error: `Failed to fetch result: ${errorMessage}`,
            };
          }
        }

        setResults(updatedResults);

        if (!allCompleted && !isRefreshing) {
          // Continue polling every 3 seconds
          setTimeout(pollResults, 3000);
        } else {
          setIsLoading(false);
          setIsRefreshing(false);
        }
      } catch (error) {
        console.error('Error polling results:', error);
        setIsLoading(false);
        setIsRefreshing(false);
      }
    };

    // Start polling after a short delay
    const timeoutId = setTimeout(pollResults, 1000);
    return () => clearTimeout(timeoutId);
  }, [jobIds, results.length, isRefreshing]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setIsLoading(true);
    // This will trigger the polling useEffect
  };

  const handleCopyText = (text: string) => {
    // TODO: Implement clipboard copy
    console.log('Copy text:', text);
  };

  const handleShareResult = (result: TranscriptionResult) => {
    // TODO: Implement share functionality
    console.log('Share result:', result);
  };

  const getMainResult = () => results[0] || {
    id: taskId,
    originalFilename: '未知文件',
    status: 'pending',
    createdAt: new Date().toISOString(),
  };

  const mainResult = getMainResult();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Icon name="schedule" size={24} color={theme.colors.text.secondary} />;
      case 'processing':
        return <ActivityIndicator size={24} color={theme.colors.primary} />;
      case 'completed':
        return <Icon name="check-circle" size={24} color={theme.colors.success} />;
      case 'error':
        return <Icon name="error" size={24} color={theme.colors.error} />;
      default:
        return <Icon name="help" size={24} color={theme.colors.text.secondary} />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return '等待处理';
      case 'processing':
        return '正在转录...';
      case 'completed':
        return '转录完成';
      case 'error':
        return '转录失败';
      default:
        return '未知状态';
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <StatusBar />
      <Header title="翻译结果" showBackButton />
      
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        <View style={styles.content}>
          {/* Status and File Info */}
          <View style={[styles.fileInfo, { backgroundColor: theme.colors.backgroundSecondary }]}>
            <View style={styles.fileHeader}>
              {getStatusIcon(mainResult.status)}
              <View style={styles.fileDetails}>
                <Text style={[styles.fileName, { color: theme.colors.text.primary }]}>
                  {mainResult.originalFilename}
                </Text>
                <Text style={[styles.fileMeta, { color: theme.colors.text.secondary }]}>
                  状态: {getStatusText(mainResult.status)}
                  {mainResult.duration && ` | 时长: ${Math.floor(mainResult.duration / 60)}:${(mainResult.duration % 60).toString().padStart(2, '0')}`}
                  {mainResult.wordCount && ` | 字数: ${mainResult.wordCount}`}
                </Text>
              </View>
              
              {/* Refresh Button */}
              {(mainResult.status === 'pending' || mainResult.status === 'processing') && (
                <TouchableOpacity 
                  onPress={handleRefresh}
                  style={[styles.refreshButton, { opacity: isRefreshing ? 0.5 : 1 }]}
                  disabled={isRefreshing}
                >
                  {isRefreshing ? (
                    <ActivityIndicator size={20} color={theme.colors.primary} />
                  ) : (
                    <Icon name="refresh" size={20} color={theme.colors.primary} />
                  )}
                </TouchableOpacity>
              )}
            </View>
            
            {/* Error Display */}
            {mainResult.status === 'error' && (
              <View style={[styles.errorContainer, { backgroundColor: theme.colors.error + '20' }]}>
                <Icon name="error-outline" size={20} color={theme.colors.error} />
                <Text style={[styles.errorText, { color: theme.colors.error }]}>
                  {mainResult.error || '转录过程中发生错误'}
                </Text>
              </View>
            )}
            
            {/* Confidence Bar (only shown when completed) */}
            {mainResult.status === 'completed' && mainResult.confidence && (
              <View style={styles.confidenceInfo}>
                <Text style={[styles.confidenceLabel, { color: theme.colors.text.secondary }]}>
                  识别准确度
                </Text>
                <View style={styles.confidenceBar}>
                  <View 
                    style={[
                      styles.confidenceProgress, 
                      { 
                        width: `${mainResult.confidence * 100}%`,
                        backgroundColor: theme.colors.success
                      }
                    ]} 
                  />
                </View>
                <Text style={[styles.confidenceValue, { color: theme.colors.text.primary }]}>
                  {(mainResult.confidence * 100).toFixed(1)}%
                </Text>
              </View>
            )}
          </View>

          {/* Transcribed Text */}
          {mainResult.status === 'completed' && mainResult.transcribedText ? (
            <View style={styles.textSection}>
              <Text style={[styles.sectionTitle, { color: theme.colors.text.primary }]}>
                转录文本
              </Text>
              <View style={[styles.textContainer, { backgroundColor: theme.colors.backgroundSecondary }]}>
                <Text style={[styles.transcribedText, { color: theme.colors.text.primary }]}>
                  {mainResult.transcribedText}
                </Text>
              </View>
              
              {/* Action Buttons */}
              <View style={styles.actionSection}>
                <TouchableOpacity 
                  style={[styles.actionButton, { backgroundColor: theme.colors.primary }]}
                  onPress={() => handleCopyText(mainResult.transcribedText!)}
                >
                  <Icon name="content-copy" size={20} color="white" />
                  <Text style={styles.actionButtonText}>复制文本</Text>
                </TouchableOpacity>

                <TouchableOpacity 
                  style={[styles.actionButton, { backgroundColor: theme.colors.secondary }]}
                  onPress={() => handleShareResult(mainResult)}
                >
                  <Icon name="share" size={20} color="white" />
                  <Text style={styles.actionButtonText}>分享结果</Text>
                </TouchableOpacity>
              </View>
            </View>
          ) : mainResult.status === 'pending' || mainResult.status === 'processing' ? (
            <View style={styles.textSection}>
              <View style={[styles.textContainer, { backgroundColor: theme.colors.backgroundSecondary }]}>
                <View style={styles.loadingContainer}>
                  <ActivityIndicator size={40} color={theme.colors.primary} />
                  <Text style={[styles.loadingText, { color: theme.colors.text.secondary }]}>
                    {mainResult.status === 'pending' ? '等待开始转录...' : '正在转录中，请稍候...'}
                  </Text>
                </View>
              </View>
            </View>
          ) : null}

          {/* Additional Options */}
          <View style={styles.optionsSection}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text.primary }]}>
              更多选项
            </Text>
            
            <TouchableOpacity style={styles.optionItem}>
              <Icon name="translate" size={24} color={theme.colors.accent} />
              <View style={styles.optionContent}>
                <Text style={[styles.optionTitle, { color: theme.colors.text.primary }]}>
                  翻译文本
                </Text>
                <Text style={[styles.optionDescription, { color: theme.colors.text.secondary }]}>
                  将文本翻译成其他语言
                </Text>
              </View>
              <Icon name="chevron-right" size={24} color={theme.colors.text.tertiary} />
            </TouchableOpacity>

            <TouchableOpacity style={styles.optionItem}>
              <Icon name="edit" size={24} color={theme.colors.primary} />
              <View style={styles.optionContent}>
                <Text style={[styles.optionTitle, { color: theme.colors.text.primary }]}>
                  编辑文本
                </Text>
                <Text style={[styles.optionDescription, { color: theme.colors.text.secondary }]}>
                  修正识别错误的内容
                </Text>
              </View>
              <Icon name="chevron-right" size={24} color={theme.colors.text.tertiary} />
            </TouchableOpacity>

            <TouchableOpacity style={styles.optionItem}>
              <Icon name="download" size={24} color={theme.colors.success} />
              <View style={styles.optionContent}>
                <Text style={[styles.optionTitle, { color: theme.colors.text.primary }]}>
                  导出文本
                </Text>
                <Text style={[styles.optionDescription, { color: theme.colors.text.secondary }]}>
                  下载为TXT或PDF文件
                </Text>
              </View>
              <Icon name="chevron-right" size={24} color={theme.colors.text.tertiary} />
            </TouchableOpacity>
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
  fileInfo: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 24,
  },
  fileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  fileDetails: {
    marginLeft: 12,
    flex: 1,
  },
  fileName: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  fileMeta: {
    fontSize: 14,
    fontWeight: '400',
  },
  confidenceInfo: {
    alignItems: 'center',
  },
  confidenceLabel: {
    fontSize: 12,
    fontWeight: '400',
    marginBottom: 8,
  },
  confidenceBar: {
    width: '100%',
    height: 8,
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  confidenceProgress: {
    height: '100%',
    borderRadius: 4,
  },
  confidenceValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  textSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  textContainer: {
    padding: 16,
    borderRadius: 12,
    minHeight: 120,
  },
  transcribedText: {
    fontSize: 16,
    fontWeight: '400',
    lineHeight: 24,
  },
  actionSection: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    gap: 8,
  },
  actionButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  optionsSection: {
    marginBottom: 24,
  },
  optionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  optionContent: {
    flex: 1,
    marginLeft: 16,
  },
  optionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  optionDescription: {
    fontSize: 14,
    fontWeight: '400',
  },
  refreshButton: {
    padding: 8,
    borderRadius: 20,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    marginTop: 12,
    gap: 8,
  },
  errorText: {
    fontSize: 14,
    fontWeight: '500',
    flex: 1,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '500',
    textAlign: 'center',
  },
});

export default ResultScreen;