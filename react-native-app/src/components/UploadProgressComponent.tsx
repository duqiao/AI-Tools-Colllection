import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { useTheme } from '@/theme';
import { UploadProgressManager, UploadProgress } from '@/services/UploadProgressManager';
import Icon from '@expo/vector-icons/MaterialIcons';

interface UploadProgressComponentProps {
  visible?: boolean;
  uploadIds?: string[];
  showCompleted?: boolean;
  maxVisibleItems?: number;
  onDismiss?: () => void;
}

export const UploadProgressComponent: React.FC<UploadProgressComponentProps> = ({
  visible = true,
  uploadIds = [],
  showCompleted = true,
  maxVisibleItems = 5,
  onDismiss,
}) => {
  const theme = useTheme();
  const [uploads, setUploads] = useState<UploadProgress[]>([]);
  const [manager] = useState(() => UploadProgressManager.getInstance());

  useEffect(() => {
    if (!visible) return;

    // Subscribe to upload progress updates
    const unsubscribe = manager.addListener((updatedUploads) => {
      let filteredUploads = updatedUploads;
      
      // Filter by specific upload IDs if provided
      if (uploadIds.length > 0) {
        filteredUploads = filteredUploads.filter(upload => 
          uploadIds.includes(upload.fileId)
        );
      }
      
      // Filter out completed uploads if not showing them
      if (!showCompleted) {
        filteredUploads = filteredUploads.filter(upload => 
          upload.status !== 'completed' && upload.status !== 'error' && upload.status !== 'cancelled'
        );
      }
      
      // Limit visible items
      if (maxVisibleItems > 0) {
        filteredUploads = filteredUploads.slice(0, maxVisibleItems);
      }
      
      setUploads(filteredUploads);
    });

    return unsubscribe;
  }, [visible, uploadIds, showCompleted, maxVisibleItems, manager]);

  const handleCancelUpload = (uploadId: string) => {
    manager.cancelUpload(uploadId);
  };

  const handleRetryUpload = (uploadId: string) => {
    manager.retryUpload(uploadId);
  };

  const handleClearCompleted = () => {
    manager.clearCompletedUploads();
  };

  const renderUploadItem = (upload: UploadProgress) => (
    <View key={upload.fileId} style={[styles.uploadItem, { backgroundColor: theme.colors.background }]}>
      {/* File Info */}
      <View style={styles.uploadHeader}>
        <View style={styles.fileInfo}>
          <Text style={[styles.fileName, { color: theme.colors.text }]} numberOfLines={1}>
            {upload.fileName}
          </Text>
          <Text style={[styles.fileSize, { color: theme.colors.textSecondary }]}>
            {(upload.bytesUploaded / 1024 / 1024).toFixed(1)}MB / {(upload.totalBytes / 1024 / 1024).toFixed(1)}MB
          </Text>
        </View>
        
        {/* Status Icon */}
        <View style={styles.statusContainer}>
          {upload.status === 'uploading' && (
            <ActivityIndicator size="small" color={theme.colors.primary} />
          )}
          {upload.status === 'processing' && (
            <ActivityIndicator size="small" color={theme.colors.secondary} />
          )}
          {upload.status === 'completed' && (
            <Icon name="check-circle" size={20} color={theme.colors.success} />
          )}
          {upload.status === 'error' && (
            <Icon name="error" size={20} color={theme.colors.error} />
          )}
          {upload.status === 'cancelled' && (
            <Icon name="cancel" size={20} color={theme.colors.textSecondary} />
          )}
        </View>
      </View>

      {/* Progress Bar */}
      {upload.status === 'uploading' && (
        <View style={styles.progressSection}>
          <View style={[styles.progressBar, { backgroundColor: theme.colors.backgroundSecondary }]}>
            <View 
              style={[
                styles.progressFill, 
                { 
                  backgroundColor: theme.colors.primary,
                  width: `${upload.progress}%` 
                }
              ]} 
            />
          </View>
          <Text style={[styles.progressText, { color: theme.colors.textSecondary }]}>
            {upload.progress.toFixed(1)}%
          </Text>
        </View>
      )}

      {/* Status and Speed Info */}
      <View style={styles.statusInfo}>
        <Text style={[styles.statusText, { color: theme.colors.textSecondary }]}>
          {getStatusText(upload.status)}
        </Text>
        
        {upload.uploadSpeed && upload.status === 'uploading' && (
          <Text style={[styles.speedText, { color: theme.colors.textSecondary }]}>
            {UploadProgressManager.formatUploadSpeed(upload.uploadSpeed)}
          </Text>
        )}
        
        {upload.estimatedTimeRemaining && upload.status === 'uploading' && (
          <Text style={[styles.timeText, { color: theme.colors.textSecondary }]}>
            剩余 {UploadProgressManager.formatTimeRemaining(upload.estimatedTimeRemaining)}
          </Text>
        )}
      </View>

      {/* Error Message */}
      {upload.error && (
        <Text style={[styles.errorText, { color: theme.colors.error }]}>
          {upload.error}
        </Text>
      )}

      {/* Action Buttons */}
      <View style={styles.actionButtons}>
        {upload.status === 'uploading' && (
          <TouchableOpacity
            style={[styles.actionButton, { borderColor: theme.colors.error }]}
            onPress={() => handleCancelUpload(upload.fileId)}
          >
            <Icon name="close" size={16} color={theme.colors.error} />
            <Text style={[styles.actionButtonText, { color: theme.colors.error }]}>
              取消
            </Text>
          </TouchableOpacity>
        )}
        
        {upload.status === 'error' && (
          <TouchableOpacity
            style={[styles.actionButton, { borderColor: theme.colors.primary }]}
            onPress={() => handleRetryUpload(upload.fileId)}
          >
            <Icon name="refresh" size={16} color={theme.colors.primary} />
            <Text style={[styles.actionButtonText, { color: theme.colors.primary }]}>
              重试
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  if (!visible || uploads.length === 0) {
    return null;
  }

  const hasActiveUploads = uploads.some(u => u.status === 'uploading' || u.status === 'processing');
  const hasCompletedUploads = uploads.some(u => u.status === 'completed' || u.status === 'error');

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: theme.colors.border }]}>
        <Text style={[styles.title, { color: theme.colors.text }]}>
          上传进度 {hasActiveUploads && `(${uploads.filter(u => u.status === 'uploading').length})`}
        </Text>
        
        <View style={styles.headerActions}>
          {hasCompletedUploads && (
            <TouchableOpacity onPress={handleClearCompleted}>
              <Text style={[styles.clearButtonText, { color: theme.colors.primary }]}>
                清除已完成
              </Text>
            </TouchableOpacity>
          )}
          
          {onDismiss && (
            <TouchableOpacity onPress={onDismiss}>
              <Icon name="close" size={24} color={theme.colors.text} />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Upload List */}
      <ScrollView style={styles.uploadList} showsVerticalScrollIndicator={false}>
        {uploads.map(renderUploadItem)}
      </ScrollView>
    </View>
  );
};

// Helper function to get status text
const getStatusText = (status: UploadProgress['status']): string => {
  switch (status) {
    case 'pending':
      return '等待上传...';
    case 'uploading':
      return '正在上传...';
    case 'processing':
      return '处理中...';
    case 'completed':
      return '上传完成';
    case 'error':
      return '上传失败';
    case 'cancelled':
      return '已取消';
    default:
      return '未知状态';
  }
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: -2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 8,
    maxHeight: 400,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  clearButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  uploadList: {
    flex: 1,
  },
  uploadItem: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  uploadHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  fileInfo: {
    flex: 1,
  },
  fileName: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  fileSize: {
    fontSize: 12,
  },
  statusContainer: {
    alignItems: 'center',
  },
  progressSection: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  progressBar: {
    flex: 1,
    height: 4,
    borderRadius: 2,
    marginRight: 12,
  },
  progressFill: {
    height: '100%',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    fontWeight: '500',
    minWidth: 40,
    textAlign: 'right',
  },
  statusInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  statusText: {
    fontSize: 12,
    flex: 1,
  },
  speedText: {
    fontSize: 12,
    marginLeft: 8,
  },
  timeText: {
    fontSize: 12,
    marginLeft: 8,
  },
  errorText: {
    fontSize: 12,
    marginBottom: 8,
  },
  actionButtons: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    marginLeft: 8,
  },
  actionButtonText: {
    fontSize: 12,
    fontWeight: '500',
    marginLeft: 4,
  },
});

export default UploadProgressComponent;