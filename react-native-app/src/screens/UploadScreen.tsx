import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/MaterialIcons';
import { useTheme } from '@/theme';
import { StatusBar } from '@/components/layout/StatusBar';
import { Header } from '@/components/layout/Header';
import { FileUploader } from '@/components/features/FileUploader';
import { Button } from '@/components/ui/Button';

export const UploadScreen: React.FC = () => {
  const theme = useTheme();

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

          <FileUploader />

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
});

export default UploadScreen;