import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '@/theme';
import { MediaFile, MediaUploadService } from '@/services/MediaUploadService';

interface FilePreviewProps {
  file: MediaFile;
  onRemove?: () => void;
  removable?: boolean;
  showDetails?: boolean;
}

export const FilePreview: React.FC<FilePreviewProps> = ({
  file,
  onRemove,
  removable = false,
  showDetails = true,
}) => {
  const theme = useTheme();
  const [imageError, setImageError] = useState(false);

  const getFileIcon = () => {
    if (file.type === 'audio') {
      return '🎵';
    } else if (file.type === 'video') {
      return '🎬';
    }
    return '📄';
  };

  const getFileColor = () => {
    if (file.type === 'audio') {
      return theme.colors.primary;
    } else if (file.type === 'video') {
      return theme.colors.secondary || theme.colors.primary;
    }
    return theme.colors.text;
  };

  const formatDuration = (duration?: number) => {
    if (!duration) return '';
    
    const minutes = Math.floor(duration / 60);
    const seconds = Math.floor(duration % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  return (
    <View style={[styles.container, { 
      backgroundColor: theme.colors.background,
      borderColor: theme.colors.border,
      borderWidth: 1,
    }]}>
      {/* File Icon/Thumbnail */}
      <View style={[styles.iconContainer, { backgroundColor: getFileColor() + '20' }]}>
        {file.type === 'video' && file.uri && !imageError ? (
          <Image
            source={{ uri: file.uri }}
            style={styles.thumbnail}
            resizeMode="cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <Text style={[styles.fileIcon, { color: getFileColor() }]}>
            {getFileIcon()}
          </Text>
        )}
      </View>

      {/* File Information */}
      <View style={styles.fileInfo}>
        <Text style={[styles.fileName, { color: theme.colors.text }]} numberOfLines={2}>
          {file.name}
        </Text>
        
        {showDetails && (
          <View style={styles.fileDetails}>
            <Text style={[styles.fileSize, { color: theme.colors.textSecondary }]}>
              {MediaUploadService.getFormattedFileSize(file.size)}
            </Text>
            
            {file.duration && (
              <Text style={[styles.fileDuration, { color: theme.colors.textSecondary }]}>
                {formatDuration(file.duration)}
              </Text>
            )}
            
            <Text style={[styles.fileType, { color: theme.colors.textSecondary }]}>
              {file.mimeType}
            </Text>
          </View>
        )}
      </View>

      {/* Remove Button */}
      {removable && onRemove && (
        <TouchableOpacity
          style={[styles.removeButton, { backgroundColor: theme.colors.error + '20' }]}
          onPress={onRemove}
          activeOpacity={0.7}
        >
          <Text style={[styles.removeIcon, { color: theme.colors.error }]}>✕</Text>
        </TouchableOpacity>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
    marginVertical: 4,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  thumbnail: {
    width: '100%',
    height: '100%',
    borderRadius: 8,
  },
  fileIcon: {
    fontSize: 24,
  },
  fileInfo: {
    flex: 1,
  },
  fileName: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 4,
  },
  fileDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  fileSize: {
    fontSize: 12,
    marginRight: 8,
  },
  fileDuration: {
    fontSize: 12,
    marginRight: 8,
  },
  fileType: {
    fontSize: 12,
  },
  removeButton: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  removeIcon: {
    fontSize: 16,
    fontWeight: '600',
  },
});

export default FilePreview;