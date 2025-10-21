import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import { useTheme } from '@/theme';
import { useNavigation } from '@react-navigation/native';
import { GuestUserManager } from '@/utils/GuestUserManager';
import Icon from '@expo/vector-icons/MaterialIcons';

interface GuestModeBannerProps {
  visible?: boolean;
  showUpsell?: boolean;
}

export const GuestModeBanner: React.FC<GuestModeBannerProps> = ({
  visible = true,
  showUpsell = true,
}) => {
  const theme = useTheme();
  const navigation = useNavigation();
  const [quotaInfo, setQuotaInfo] = useState<any>(null);
  const [isGuest, setIsGuest] = useState(false);

  useEffect(() => {
    loadGuestInfo();
  }, []);

  const loadGuestInfo = async () => {
    try {
      const guestStatus = await GuestUserManager.isGuestUser();
      setIsGuest(guestStatus);

      if (guestStatus) {
        const info = await GuestUserManager.getGuestQuotaInfo();
        setQuotaInfo(info);
      }
    } catch (error) {
      console.error('Failed to load guest info:', error);
    }
  };

  const handleUpgrade = () => {
    // Navigate to login screen for upgrade
    navigation.navigate('Auth' as never);
  };

  const handleDismiss = () => {
    // In a real app, you might want to store user preference
    console.log('Guest banner dismissed');
  };

  if (!visible || !isGuest || !quotaInfo) {
    return null;
  }

  const remainingPercentage = (quotaInfo.remaining / quotaInfo.limit) * 100;
  const quotaColor = quotaInfo.remaining === 0 ? theme.colors.error : 
                   quotaInfo.remaining === 1 ? theme.colors.warning : 
                   theme.colors.success;

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.backgroundSecondary }]}>
      <View style={styles.content}>
        {/* Guest indicator */}
        <View style={styles.guestIndicator}>
          <Icon name="person-outline" size={16} color={theme.colors.primary} />
          <Text style={[styles.guestText, { color: theme.colors.primary }]}>
            游客模式
          </Text>
        </View>

        {/* Quota information */}
        <View style={styles.quotaSection}>
          <View style={styles.quotaHeader}>
            <Text style={[styles.quotaTitle, { color: theme.colors.text }]}>
              今日翻译额度
            </Text>
            <Text style={[styles.quotaCount, { color: quotaColor }]}>
              {quotaInfo.remaining}/{quotaInfo.limit}
            </Text>
          </View>
          
          {/* Progress bar */}
          <View style={[styles.quotaProgressBar, { backgroundColor: theme.colors.border }]}>
            <View 
              style={[
                styles.quotaProgressFill, 
                { 
                  backgroundColor: quotaColor,
                  width: `${remainingPercentage}%` 
                }
              ]} 
            />
          </View>
          
          <Text style={[styles.quotaSubtitle, { color: theme.colors.textSecondary }]}>
            {quotaInfo.remaining === 0 
              ? '今日额度已用完，请明天再试或升级账号' 
              : `还可翻译 ${quotaInfo.remaining} 次`}
          </Text>
        </View>

        {/* Guest limitations */}
        <View style={styles.limitations}>
          <Text style={[styles.limitationTitle, { color: theme.colors.text }]}>
            游客限制：
          </Text>
          <View style={styles.limitationList}>
            <View style={styles.limitationItem}>
              <Icon name="check-circle-outline" size={14} color={theme.colors.success} />
              <Text style={[styles.limitationText, { color: theme.colors.textSecondary }]}>
                每日免费翻译
              </Text>
            </View>
            <View style={styles.limitationItem}>
              <Icon name="cancel" size={14} color={theme.colors.textSecondary} />
              <Text style={[styles.limitationText, { color: theme.colors.textSecondary }]}>
                无法保存历史
              </Text>
            </View>
            <View style={styles.limitationItem}>
              <Icon name="cancel" size={14} color={theme.colors.textSecondary} />
              <Text style={[styles.limitationText, { color: theme.colors.textSecondary }]}>
                无法同步设置
              </Text>
            </View>
          </View>
        </View>

        {/* Upsell section */}
        {showUpsell && (
          <View style={styles.upsellSection}>
            <View style={[styles.upsellContent, { backgroundColor: theme.colors.primary + '10' }]}>
              <View style={styles.upsellText}>
                <Text style={[styles.upsellTitle, { color: theme.colors.primary }]}>
                  升级解锁全部功能
                </Text>
                <Text style={[styles.upsellSubtitle, { color: theme.colors.textSecondary }]}>
                  无限翻译 • 历史记录 • 高级功能
                </Text>
              </View>
              <TouchableOpacity
                style={[styles.upgradeButton, { backgroundColor: theme.colors.primary }]}
                onPress={handleUpgrade}
              >
                <Text style={styles.upgradeButtonText}>
                  立即升级
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Dismiss button */}
        <TouchableOpacity
          style={styles.dismissButton}
          onPress={handleDismiss}
        >
          <Icon name="close" size={20} color={theme.colors.textSecondary} />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  content: {
    padding: 16,
  },
  guestIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderRadius: 16,
    marginBottom: 12,
  },
  guestText: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
  quotaSection: {
    marginBottom: 16,
  },
  quotaHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  quotaTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  quotaCount: {
    fontSize: 16,
    fontWeight: '600',
  },
  quotaProgressBar: {
    height: 6,
    borderRadius: 3,
    marginBottom: 8,
  },
  quotaProgressFill: {
    height: '100%',
    borderRadius: 3,
  },
  quotaSubtitle: {
    fontSize: 12,
    textAlign: 'center',
  },
  limitations: {
    marginBottom: 16,
  },
  limitationTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 8,
  },
  limitationList: {
    gap: 4,
  },
  limitationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  limitationText: {
    fontSize: 12,
    flex: 1,
  },
  upsellSection: {
    marginBottom: 12,
  },
  upsellContent: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 8,
  },
  upsellText: {
    flex: 1,
  },
  upsellTitle: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 2,
  },
  upsellSubtitle: {
    fontSize: 12,
  },
  upgradeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
  },
  upgradeButtonText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  dismissButton: {
    alignSelf: 'flex-end',
    padding: 4,
  },
});

export default GuestModeBanner;