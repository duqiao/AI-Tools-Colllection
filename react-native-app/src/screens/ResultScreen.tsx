import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/MaterialIcons';
import { useTheme } from '@/theme';
import { StatusBar } from '@/components/layout/StatusBar';
import { Header } from '@/components/layout/Header';

export const ResultScreen: React.FC<{ route?: { params: { taskId: string } } }> = ({ route }) => {
  const theme = useTheme();
  const { taskId } = route?.params || { taskId: '' };

  // Mock data - in real app, this would come from API
  const mockResult = {
    originalFilename: 'demo-audio.mp3',
    transcribedText: '这是模拟的转录文本内容。在实际应用中，这里会显示从语音识别服务获取的真实文本结果。',
    confidence: 0.95,
    duration: 120,
    wordCount: 45,
    createdAt: new Date().toISOString(),
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <StatusBar />
      <Header title="翻译结果" showBackButton />
      
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        <View style={styles.content}>
          {/* File Info */}
          <View style={[styles.fileInfo, { backgroundColor: theme.colors.backgroundSecondary }]}>
            <View style={styles.fileHeader}>
              <Icon name="audio-file" size={24} color={theme.colors.primary} />
              <View style={styles.fileDetails}>
                <Text style={[styles.fileName, { color: theme.colors.text.primary }]}>
                  {mockResult.originalFilename}
                </Text>
                <Text style={[styles.fileMeta, { color: theme.colors.text.secondary }]}>
                  时长: {Math.floor(mockResult.duration / 60)}:{(mockResult.duration % 60).toString().padStart(2, '0')} | 
                  字数: {mockResult.wordCount}
                </Text>
              </View>
            </View>
            
            <View style={styles.confidenceInfo}>
              <Text style={[styles.confidenceLabel, { color: theme.colors.text.secondary }]}>
                识别准确度
              </Text>
              <View style={styles.confidenceBar}>
                <View 
                  style={[
                    styles.confidenceProgress, 
                    { 
                      width: `${mockResult.confidence * 100}%`,
                      backgroundColor: theme.colors.success
                    }
                  ]} 
                />
              </View>
              <Text style={[styles.confidenceValue, { color: theme.colors.text.primary }]}>
                {(mockResult.confidence * 100).toFixed(1)}%
              </Text>
            </View>
          </View>

          {/* Transcribed Text */}
          <View style={styles.textSection}>
            <Text style={[styles.sectionTitle, { color: theme.colors.text.primary }]}>
              转录文本
            </Text>
            <View style={[styles.textContainer, { backgroundColor: theme.colors.backgroundSecondary }]}>
              <Text style={[styles.transcribedText, { color: theme.colors.text.primary }]}>
                {mockResult.transcribedText}
              </Text>
            </View>
          </View>

          {/* Action Buttons */}
          <View style={styles.actionSection}>
            <TouchableOpacity 
              style={[styles.actionButton, { backgroundColor: theme.colors.primary }]}
              onPress={() => console.log('Copy text')}
            >
              <Icon name="content-copy" size={20} color="white" />
              <Text style={styles.actionButtonText}>复制文本</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={[styles.actionButton, { backgroundColor: theme.colors.secondary }]}
              onPress={() => console.log('Share result')}
            >
              <Icon name="share" size={20} color="white" />
              <Text style={styles.actionButtonText}>分享结果</Text>
            </TouchableOpacity>
          </View>

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
});

export default ResultScreen;