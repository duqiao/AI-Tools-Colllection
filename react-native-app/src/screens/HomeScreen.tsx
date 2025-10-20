import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/MaterialIcons';
import { useTheme } from '@/theme';
import { useAppSelector } from '@/store';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { FeatureCard } from '@/components/features/FeatureCard';
import { StatusBar } from '@/components/layout/StatusBar';
import { Header } from '@/components/layout/Header';
import { InfoBanner } from '@/components/layout/InfoBanner';
import { CTAButton } from '@/components/ui/CTAButton';

type RootStackParamList = {
  MainTabs: undefined;
  Result: { taskId: string };
  Upload: undefined;
  History: undefined;
  Profile: undefined;
  Home: undefined;
};

type HomeScreenNavigationProp = StackNavigationProp<RootStackParamList, 'Home'>;

interface FeatureProps {
  id: number;
  icon: keyof typeof Icon.glyphMap;
  iconBg: string;
  title: string;
  description: string;
  badge?: string;
  onPress: () => void;
}

export const HomeScreen: React.FC = () => {
  const theme = useTheme();
  const navigation = useNavigation<HomeScreenNavigationProp>();
  const { user } = useAppSelector(state => state.auth);
  const { quota_used, quota_limit } = user || { quota_used: 0, quota_limit: 1 };

  const features: FeatureProps[] = [
    {
      id: 1,
      icon: 'mic',
      iconBg: theme.colors.primary,
      title: '实时语音转文字',
      description: '实时录音同步生成文字',
      badge: '高级功能',
      onPress: () => navigation.navigate('Upload'),
    },
    {
      id: 2,
      icon: 'videocam',
      iconBg: theme.colors.secondary,
      title: '视频文件转文字',
      description: '上传视频文件提取音频转文字',
      badge: '热门功能',
      onPress: () => navigation.navigate('Upload'),
    },
    {
      id: 3,
      icon: 'audio-file',
      iconBg: theme.colors.accent,
      title: '音频文件转文字',
      description: '支持多种音频格式转换',
      onPress: () => navigation.navigate('Upload'),
    },
    {
      id: 4,
      icon: 'history',
      iconBg: theme.colors.success,
      title: '翻译历史',
      description: '查看和管理翻译记录',
      onPress: () => navigation.navigate('History'),
    },
  ];

  const quotaPercentage = quota_limit > 0 ? (quota_used / quota_limit) * 100 : 0;
  const remainingQuota = Math.max(0, quota_limit - quota_used);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <StatusBar />
      <Header />
      
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Title Section */}
        <View style={styles.titleSection}>
          <Text style={[styles.mainTitle, { color: theme.colors.text.primary }]}>
            AI语音视频工具
          </Text>
          <Text style={[styles.subtitle, { color: theme.colors.text.secondary }]}>
            智能语音识别，精准文字转换
          </Text>
        </View>

        {/* Quota Status Banner */}
        <View style={[styles.quotaBanner, { backgroundColor: theme.colors.backgroundSecondary }]}>
          <View style={styles.quotaInfo}>
            <Text style={[styles.quotaText, { color: theme.colors.text.primary }]}>
              今日配额: {remainingQuota}/{quota_limit}
            </Text>
            <Text style={[styles.quotaSubtext, { color: theme.colors.text.secondary }]}>
              已使用 {quotaPercentage.toFixed(0)}%
            </Text>
          </View>
          <View style={styles.quotaProgress}>
            <View 
              style={[
                styles.quotaProgressBar, 
                { 
                  width: `${Math.min(100, quotaPercentage)}%`,
                  backgroundColor: quotaPercentage > 80 ? theme.colors.error : theme.colors.primary
                }
              ]} 
            />
          </View>
        </View>

        {/* Info Banner */}
        <InfoBanner 
          icon="🔊"
          message="本工具，升级套餐解锁更多权限"
          type="info"
        />

        {/* Feature Cards */}
        <View style={styles.featuresSection}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text.primary }]}>
            功能选择
          </Text>
          {features.map((feature) => (
            <FeatureCard
              key={feature.id}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              badge={feature.badge}
              iconBg={feature.iconBg}
              onPress={feature.onPress}
            />
          ))}
        </View>

        {/* CTA Button */}
        <View style={styles.ctaSection}>
          <CTAButton
            title="超全工具包！神器汇总！"
            subtitle="GO"
            icon="💼"
            onPress={() => navigation.navigate('Upload')}
          />
        </View>

        {/* Bottom padding */}
        <View style={styles.bottomPadding} />
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
  titleSection: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  mainTitle: {
    fontSize: 28,
    fontWeight: '700',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    fontWeight: '400',
  },
  quotaBanner: {
    marginHorizontal: 20,
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },
  quotaInfo: {
    flex: 1,
  },
  quotaText: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  quotaSubtext: {
    fontSize: 14,
    fontWeight: '400',
  },
  quotaProgress: {
    width: 100,
    height: 8,
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    overflow: 'hidden',
  },
  quotaProgressBar: {
    height: '100%',
    borderRadius: 4,
  },
  featuresSection: {
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 16,
  },
  ctaSection: {
    paddingHorizontal: 20,
    marginBottom: 16,
  },
  bottomPadding: {
    height: 20,
  },
});

export default HomeScreen;