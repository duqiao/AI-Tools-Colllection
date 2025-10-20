import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/MaterialIcons';
import { useTheme } from '@/theme';
import { useAppSelector, useAppDispatch } from '@/store';
import { AuthService } from '@/services/auth';
import { logout } from '@/store/slices/authSlice';
import { StatusBar } from '@/components/layout/StatusBar';
import { Header } from '@/components/layout/Header';
import { QuotaDisplay } from '@/components/features/QuotaDisplay';
import { Button } from '@/components/ui/Button';

export const ProfileScreen: React.FC = () => {
  const theme = useTheme();
  const dispatch = useAppDispatch();
  const { user } = useAppSelector(state => state.auth);

  const handleLogout = async () => {
    await AuthService.logoutUser(dispatch);
  };

  const menuItems = [
    {
      icon: 'person' as keyof typeof Icon.glyphMap,
      title: '个人信息',
      subtitle: '编辑个人资料',
      onPress: () => console.log('Edit profile'),
    },
    {
      icon: 'security' as keyof typeof Icon.glyphMap,
      title: '账号安全',
      subtitle: '密码与安全设置',
      onPress: () => console.log('Security settings'),
    },
    {
      icon: 'notifications' as keyof typeof Icon.glyphMap,
      title: '通知设置',
      subtitle: '管理通知偏好',
      onPress: () => console.log('Notification settings'),
    },
    {
      icon: 'help' as keyof typeof Icon.glyphMap,
      title: '帮助中心',
      subtitle: '使用说明和常见问题',
      onPress: () => console.log('Help center'),
    },
    {
      icon: 'info' as keyof typeof Icon.glyphMap,
      title: '关于我们',
      subtitle: '应用版本和开发信息',
      onPress: () => console.log('About us'),
    },
  ];

  if (!user) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <StatusBar />
        <Header title="我的" />
        <View style={styles.loginPrompt}>
          <Icon name="account-circle" size={80} color={theme.colors.text.tertiary} />
          <Text style={[styles.loginTitle, { color: theme.colors.text.primary }]}>
            请先登录
          </Text>
          <Text style={[styles.loginSubtitle, { color: theme.colors.text.secondary }]}>
            登录后可以使用完整功能
          </Text>
          <Button
            title="立即登录"
            onPress={() => console.log('Navigate to login')}
            style={styles.loginButton}
          />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <StatusBar />
      <Header title="我的" />
      
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* User Profile Section */}
        <View style={[styles.profileSection, { backgroundColor: theme.colors.backgroundSecondary }]}>
          <View style={styles.profileHeader}>
            {user.avatar_url ? (
              <View style={[styles.avatar, { backgroundColor: theme.colors.primary }]}>
                <Text style={styles.avatarText}>
                  {user.username?.charAt(0).toUpperCase() || 'U'}
                </Text>
              </View>
            ) : (
              <Icon name="account-circle" size={80} color={theme.colors.text.tertiary} />
            )}
            
            <View style={styles.profileInfo}>
              <Text style={[styles.username, { color: theme.colors.text.primary }]}>
                {user.username || '用户'}
              </Text>
              <Text style={[styles.userId, { color: theme.colors.text.secondary }]}>
                ID: {user.id}
              </Text>
              <View style={[styles.subscriptionBadge, { backgroundColor: theme.colors.primary }]}>
                <Text style={styles.subscriptionText}>
                  {user.subscription_level === 'free' ? '免费用户' : 
                   user.subscription_level === 'basic_vip' ? '基础VIP' : '高级VIP'}
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Quota Status */}
        <QuotaDisplay
          used={user.quota_used}
          limit={user.quota_limit}
          resetDate={user.quota_reset_date}
        />

        {/* Menu Items */}
        <View style={styles.menuSection}>
          {menuItems.map((item, index) => (
            <TouchableOpacity
              key={index}
              style={[styles.menuItem, { backgroundColor: theme.colors.backgroundSecondary }]}
              onPress={item.onPress}
            >
              <View style={styles.menuLeft}>
                <Icon name={item.icon} size={24} color={theme.colors.primary} />
                <View style={styles.menuContent}>
                  <Text style={[styles.menuTitle, { color: theme.colors.text.primary }]}>
                    {item.title}
                  </Text>
                  <Text style={[styles.menuSubtitle, { color: theme.colors.text.secondary }]}>
                    {item.subtitle}
                  </Text>
                </View>
              </View>
              <Icon name="chevron-right" size={24} color={theme.colors.text.tertiary} />
            </TouchableOpacity>
          ))}
        </View>

        {/* Logout Button */}
        <View style={styles.logoutSection}>
          <Button
            title="退出登录"
            onPress={handleLogout}
            variant="outline"
            style={styles.logoutButton}
          />
        </View>

        {/* App Version */}
        <View style={styles.versionSection}>
          <Text style={[styles.versionText, { color: theme.colors.text.tertiary }]}>
            版本 1.0.0
          </Text>
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
  profileSection: {
    margin: 20,
    padding: 20,
    borderRadius: 12,
  },
  profileHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  avatarText: {
    fontSize: 32,
    fontWeight: '700',
    color: 'white',
  },
  profileInfo: {
    flex: 1,
  },
  username: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
  },
  userId: {
    fontSize: 14,
    fontWeight: '400',
    marginBottom: 8,
  },
  subscriptionBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  subscriptionText: {
    fontSize: 12,
    fontWeight: '600',
    color: 'white',
  },
  menuSection: {
    marginHorizontal: 20,
    marginBottom: 24,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  menuLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  menuContent: {
    marginLeft: 16,
    flex: 1,
  },
  menuTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  menuSubtitle: {
    fontSize: 14,
    fontWeight: '400',
  },
  logoutSection: {
    marginHorizontal: 20,
    marginBottom: 24,
  },
  logoutButton: {
    width: '100%',
  },
  versionSection: {
    alignItems: 'center',
    paddingBottom: 20,
  },
  versionText: {
    fontSize: 12,
    fontWeight: '400',
  },
  loginPrompt: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
  },
  loginTitle: {
    fontSize: 24,
    fontWeight: '600',
    marginTop: 16,
    marginBottom: 8,
  },
  loginSubtitle: {
    fontSize: 16,
    fontWeight: '400',
    textAlign: 'center',
    marginBottom: 24,
  },
  loginButton: {
    width: '100%',
  },
});

export default ProfileScreen;