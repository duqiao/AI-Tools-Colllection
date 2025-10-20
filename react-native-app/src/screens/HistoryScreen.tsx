import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/MaterialIcons';
import { useTheme } from '@/theme';
import { useAppSelector, useAppDispatch } from '@/store';
import { TranslationService } from '@/services/translation';
import { StatusBar } from '@/components/layout/StatusBar';
import { Header } from '@/components/layout/Header';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';

export const HistoryScreen: React.FC = () => {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const { tasks } = useAppSelector(state => state.translation);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadHistory = async (refresh: boolean = false) => {
    if (refresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }

    try {
      const result = await TranslationService.getTranslationHistory(dispatch);
      // Result is handled by the service which updates Redux state
    } catch (error) {
      console.error('Failed to load history:', error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return '刚刚';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}小时前`;
    } else if (diffInHours < 48) {
      return '昨天';
    } else {
      return date.toLocaleDateString('zh-CN');
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '未知';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return 'check-circle';
      case 'processing':
        return 'sync';
      case 'failed':
        return 'error';
      default:
        return 'schedule';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return theme.colors.success;
      case 'processing':
        return theme.colors.warning;
      case 'failed':
        return theme.colors.error;
      default:
        return theme.colors.text.tertiary;
    }
  };

  const handleDeleteTask = async (taskId: string) => {
    try {
      await TranslationService.deleteTranslation(taskId);
      loadHistory(true);
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  if (isLoading && tasks.length === 0) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <StatusBar />
        <Header title="翻译历史" />
        <LoadingSpinner />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <StatusBar />
      <Header title="翻译历史" />
      
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={() => loadHistory(true)}
            tintColor={theme.colors.primary}
          />
        }
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.content}>
          {tasks.length === 0 ? (
            <EmptyState
              icon="history"
              title="暂无翻译记录"
              description="您还没有进行过语音翻译，快去试试吧！"
              actionText="开始翻译"
              onAction={() => console.log('Navigate to upload')}
            />
          ) : (
            <View style={styles.historyList}>
              {tasks.map((task) => (
                <View
                  key={task.id}
                  style={[styles.historyItem, { backgroundColor: theme.colors.backgroundSecondary }]}
                >
                  <View style={styles.itemHeader}>
                    <View style={styles.fileInfo}>
                      <Icon 
                        name={task.file_type === 'video' ? 'videocam' : 'audiotrack'} 
                        size={20} 
                        color={theme.colors.primary} 
                      />
                      <View style={styles.fileDetails}>
                        <Text style={[styles.fileName, { color: theme.colors.text.primary }]} numberOfLines={1}>
                          {task.original_filename}
                        </Text>
                        <Text style={[styles.fileMeta, { color: theme.colors.text.secondary }]}>
                          {formatDuration(task.duration_seconds)} • {formatDate(task.created_at)}
                        </Text>
                      </View>
                    </View>
                    
                    <View style={styles.statusInfo}>
                      <Icon 
                        name={getStatusIcon(task.processing_status)} 
                        size={20} 
                        color={getStatusColor(task.processing_status)} 
                      />
                    </View>
                  </View>

                  {task.transcribed_text && (
                    <Text style={[styles.previewText, { color: theme.colors.text.secondary }]} numberOfLines={2}>
                      {task.transcribed_text}
                    </Text>
                  )}

                  {task.processing_status === 'completed' && (
                    <View style={styles.statsRow}>
                      <View style={styles.statItem}>
                        <Text style={[styles.statValue, { color: theme.colors.text.primary }]}>
                          {task.word_count || 0}
                        </Text>
                        <Text style={[styles.statLabel, { color: theme.colors.text.secondary }]}>
                          字数
                        </Text>
                      </View>
                      {task.confidence_score && (
                        <View style={styles.statItem}>
                          <Text style={[styles.statValue, { color: theme.colors.text.primary }]}>
                            {(task.confidence_score * 100).toFixed(0)}%
                          </Text>
                          <Text style={[styles.statLabel, { color: theme.colors.text.secondary }]}>
                            准确度
                          </Text>
                        </View>
                      )}
                    </View>
                  )}

                  <View style={styles.itemActions}>
                    <TouchableOpacity
                      style={[styles.actionButton, { backgroundColor: theme.colors.primary }]}
                      onPress={() => console.log('View result', task.id)}
                    >
                      <Icon name="visibility" size={16} color="white" />
                      <Text style={styles.actionButtonText}>查看</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={[styles.actionButton, { backgroundColor: theme.colors.error }]}
                      onPress={() => handleDeleteTask(task.id)}
                    >
                      <Icon name="delete" size={16} color="white" />
                      <Text style={styles.actionButtonText}>删除</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ))}
            </View>
          )}
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
  historyList: {
    gap: 16,
  },
  historyItem: {
    padding: 16,
    borderRadius: 12,
  },
  itemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  fileInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
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
    fontSize: 12,
    fontWeight: '400',
  },
  statusInfo: {
    alignItems: 'center',
  },
  previewText: {
    fontSize: 14,
    fontWeight: '400',
    lineHeight: 20,
    marginBottom: 12,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 24,
    marginBottom: 12,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 2,
  },
  statLabel: {
    fontSize: 12,
    fontWeight: '400',
  },
  itemActions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    gap: 6,
  },
  actionButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
});

export default HistoryScreen;