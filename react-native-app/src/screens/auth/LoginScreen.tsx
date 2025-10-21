import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  SafeAreaView,
  Alert,
} from 'react-native';
import { useTheme } from '@/theme';
import { useSession } from '@/contexts/SessionContext';
import { AuthService } from '@/services/auth';

export const LoginScreen: React.FC = () => {
  const theme = useTheme();
  const { login } = useSession();
  const [isLoading, setIsLoading] = useState(false);

  const handleWeChatLogin = async () => {
    try {
      setIsLoading(true);
      
      // Check if WeChat is available (mock check)
      const isWeChatAvailable = await AuthService.isWeChatInstalled();
      
      if (!isWeChatAvailable) {
        // For demo purposes, continue with mock login
        Alert.alert(
          '微信未安装',
          '检测到未安装微信，将使用演示模式登录',
          [{ text: '确定', onPress: handleMockLogin }]
        );
        return;
      }
      
      // Attempt WeChat login
      const wechatResult = await AuthService.openWeChatLogin();
      if (!wechatResult.success) {
        Alert.alert('登录失败', wechatResult.error || '无法打开微信');
        return;
      }
      
      // In production, handle WeChat callback here
      // For demo, use mock login
      await handleMockLogin();
      
    } catch (error: any) {
      Alert.alert('登录失败', error.message || '未知错误');
    } finally {
      setIsLoading(false);
    }
  };

  const handleMockLogin = async () => {
    try {
      setIsLoading(true);
      
      // Use mock login for demo purposes
      const mockResult = await AuthService.mockLogin(null); // dispatch not needed here
      
      if (mockResult.success) {
        // Trigger session login
        const sessionResult = await login();
        if (!sessionResult.success) {
          Alert.alert('登录失败', sessionResult.error || '会话初始化失败');
        }
      } else {
        Alert.alert('登录失败', mockResult.error || '模拟登录失败');
      }
    } catch (error: any) {
      Alert.alert('登录失败', error.message || '未知错误');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    try {
      setIsLoading(true);
      
      // Show guest mode confirmation dialog
      Alert.alert(
        '游客体验模式',
        '以游客身份体验应用功能：\n\n✓ 每日3次免费翻译\n✗ 无法保存历史记录\n✗ 无法同步设置\n✗ 部分高级功能受限',
        [
          {
            text: '取消',
            style: 'cancel',
          },
          {
            text: '继续体验',
            onPress: () => executeGuestLogin(),
          },
        ]
      );
    } catch (error: any) {
      console.error('Guest login error:', error);
      Alert.alert('登录失败', '游客登录失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  const executeGuestLogin = async () => {
    try {
      setIsLoading(true);
      
      // Create guest user with comprehensive data and correct types
      const guestUser = {
        id: Math.floor(Date.now() / 1000), // Convert to number
        openid: `guest_${Date.now()}`,
        username: '游客用户',
        avatar_url: `https://ui-avatars.com/api/?name=Guest&background=10B981&color=fff&size=128`,
        subscription_level: 'free' as const,
        quota_used: 0,
        quota_limit: 3, // 3 free translations per day
        quota_reset_date: new Date().toISOString().split('T')[0],
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      // Store guest user data
      await AuthService.storeUserInfo(guestUser);
      
      // Create guest session tokens
      const guestToken = `guest_token_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const guestRefreshToken = `guest_refresh_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      await AuthService.storeTokens(guestToken, guestRefreshToken);
      
      // Persist session
      await AuthService.persistSession();

      // Trigger session login
      const sessionResult = await login();
      
      if (!sessionResult.success) {
        Alert.alert('登录失败', sessionResult.error || '游客登录失败');
      }
    } catch (error: any) {
      console.error('Guest login execution failed:', error);
      Alert.alert('登录失败', '游客登录失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.title, { color: theme.colors.text }]}>
            登录账号
          </Text>
          <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
            选择登录方式开始使用
          </Text>
        </View>

        {/* Login Options */}
        <View style={styles.loginOptions}>
          {/* WeChat Login */}
          <TouchableOpacity
            style={[styles.loginButton, { backgroundColor: '#07C160' }]}
            onPress={handleWeChatLogin}
            disabled={isLoading}
            activeOpacity={0.8}
          >
            {isLoading ? (
              <ActivityIndicator color="#ffffff" size="small" />
            ) : (
              <Text style={styles.loginButtonText}>微信登录</Text>
            )}
          </TouchableOpacity>

          {/* Guest Login */}
          <View style={styles.guestLoginContainer}>
            <TouchableOpacity
              style={[styles.guestLoginButton, { 
                backgroundColor: theme.colors.background, 
                borderColor: theme.colors.border,
                borderWidth: 2,
              }]}
              onPress={handleGuestLogin}
              disabled={isLoading}
              activeOpacity={0.8}
            >
              {isLoading ? (
                <ActivityIndicator color={theme.colors.primary} size="small" />
              ) : (
                <View style={styles.guestLoginContent}>
                  <Text style={styles.guestIcon}>👤</Text>
                  <View style={styles.guestTextContainer}>
                    <Text style={[styles.guestTitle, { color: theme.colors.text }]}>
                      游客体验
                    </Text>
                    <Text style={[styles.guestSubtitle, { color: theme.colors.text.secondary }]}>
                      无需注册，立即体验
                    </Text>
                  </View>
                </View>
              )}
            </TouchableOpacity>
            
            {/* Guest mode features */}
            <View style={styles.guestFeatures}>
              <Text style={[styles.guestFeatureText, { color: theme.colors.text.secondary }]}>
                ✓ 每日3次免费翻译
              </Text>
              <Text style={[styles.guestFeatureText, { color: theme.colors.text.secondary }]}>
                ✓ 无需注册登录
              </Text>
            </View>
          </View>
        </View>

        {/* Features */}
        <View style={styles.features}>
          <Text style={[styles.featuresTitle, { color: theme.colors.text }]}>
            登录后可享受：
          </Text>
          
          <View style={styles.featureItem}>
            <Text style={[styles.featureText, { color: theme.colors.textSecondary }]}>
              • 每日免费翻译额度
            </Text>
          </View>
          
          <View style={styles.featureItem}>
            <Text style={[styles.featureText, { color: theme.colors.textSecondary }]}>
              • 翻译历史记录保存
            </Text>
          </View>
          
          <View style={styles.featureItem}>
            <Text style={[styles.featureText, { color: theme.colors.textSecondary }]}>
              • 个性化设置同步
            </Text>
          </View>
          
          <View style={styles.featureItem}>
            <Text style={[styles.featureText, { color: theme.colors.textSecondary }]}>
              • 优先客服支持
            </Text>
          </View>
        </View>

        {/* Terms */}
        <View style={styles.terms}>
          <Text style={[styles.termsText, { color: theme.colors.textSecondary }]}>
            登录即表示同意《用户协议》和《隐私政策》
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 48,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
  },
  loginOptions: {
    marginBottom: 40,
  },
  loginButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  loginButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
  },
  guestLoginContainer: {
    marginBottom: 16,
  },
  guestLoginButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  guestLoginContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  guestIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  guestTextContainer: {
    flex: 1,
  },
  guestTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 2,
  },
  guestSubtitle: {
    fontSize: 14,
  },
  guestFeatures: {
    alignItems: 'flex-start',
    paddingHorizontal: 8,
  },
  guestFeatureText: {
    fontSize: 12,
    lineHeight: 20,
  },
  features: {
    marginBottom: 32,
  },
  featuresTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 16,
  },
  featureItem: {
    marginBottom: 8,
  },
  featureText: {
    fontSize: 16,
    lineHeight: 24,
  },
  terms: {
    alignItems: 'center',
  },
  termsText: {
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
});

export default LoginScreen;