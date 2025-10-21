import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useTheme } from '@/theme';
import { useSession } from '@/contexts/SessionContext';
import { AuthService } from '@/services/auth';

export const WelcomeScreen: React.FC = () => {
  const theme = useTheme();
  const { login } = useSession();
  const [isLoading, setIsLoading] = useState(false);

  const handleGuestMode = async () => {
    console.log('🎯 handleGuestMode STARTED');
    try {
      console.log('🔧 Setting loading to true...');
      setIsLoading(true);
      
      console.log('💬 About to show Alert dialog...');
      
      // For React Native Web, Alert.alert might not work properly
      // Try using window.confirm as fallback for web environment
      if (typeof window !== 'undefined' && window.confirm) {
        console.log('🌐 Using browser confirm dialog');
        const confirmed = window.confirm(
          '游客体验模式\n\n您将以游客身份体验应用功能。\n\n• 每日限制翻译次数\n• 无法保存历史记录\n• 部分功能受限\n\n点击确定继续体验，取消退出'
        );
        
        if (confirmed) {
          console.log('✅ User confirmed via browser dialog');
          executeGuestLogin();
        } else {
          console.log('❌ User cancelled via browser dialog');
          setIsLoading(false);
        }
      } else {
        console.log('📱 Using React Native Alert');
        // Show guest mode confirmation for React Native
        Alert.alert(
          '游客体验模式',
          '您将以游客身份体验应用功能。\n\n• 每日限制翻译次数\n• 无法保存历史记录\n• 部分功能受限',
          [
            {
              text: '取消',
              style: 'cancel',
              onPress: () => {
                console.log('❌ Cancel button pressed');
                setIsLoading(false);
              },
            },
            {
              text: '继续体验',
              onPress: () => {
                console.log('✅ Continue button pressed');
                executeGuestLogin();
              },
            },
          ]
        );
      }
      
      console.log('✅ Dialog called successfully');
    } catch (error) {
      console.error('❌ Guest mode error:', error);
      console.error('❌ Error stack:', error.stack);
      setIsLoading(false);
    }
  };

  const executeGuestLogin = async () => {
    try {
      console.log('🚀 WelcomeScreen executeGuestLogin START...');
      console.log('🔍 Current loading state before:', isLoading);
      
      // Create guest user data with correct types
      const timestamp = Date.now();
      const guestUser = {
        id: Math.floor(timestamp / 1000), // Convert to number
        openid: `guest_${timestamp}`,
        username: '游客用户',
        avatar_url: 'https://ui-avatars.com/api/?name=Guest&background=10B981&color=fff',
        subscription_level: 'free' as const,
        quota_used: 0,
        quota_limit: 3, // 3 free translations per day for guests
        quota_reset_date: new Date().toISOString().split('T')[0],
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      console.log('👤 Created guest user:', guestUser);

      // Store guest user info
      console.log('💾 STEP 1: Storing guest user info...');
      await AuthService.storeUserInfo(guestUser);
      console.log('✅ STEP 1 COMPLETE: Stored guest user info');
      
      // Create mock tokens for guest session
      console.log('🔐 STEP 2: Creating guest tokens...');
      const guestToken = `guest_token_${timestamp}`;
      const guestRefreshToken = `guest_refresh_${timestamp}`;
      await AuthService.storeTokens(guestToken, guestRefreshToken);
      console.log('✅ STEP 2 COMPLETE: Stored guest tokens');

      // Verify user is stored
      console.log('🔍 STEP 3: Verifying stored user...');
      const storedUser = await AuthService.getStoredUserInfo();
      console.log('✅ STEP 3 COMPLETE: Verified stored user:', storedUser);

      // Initialize session
      console.log('🔐 STEP 4: Calling login() from SessionContext...');
      const result = await login();
      console.log('✅ STEP 4 COMPLETE: Login() returned');
      
      console.log('📋 FINAL RESULT:', result);
      
      if (!result.success) {
        console.error('❌ FINAL: Login failed:', result.error);
        Alert.alert('登录失败', result.error || '游客登录失败，请重试');
      } else {
        console.log('🎉 FINAL: Guest login successful!');
      }
    } catch (error: any) {
      console.error('❌ CATCH: Guest login failed:', error);
      console.error('❌ CATCH: Error stack:', error.stack);
      Alert.alert('登录失败', `游客登录失败: ${error.message || '请重试'}`);
    } finally {
      console.log('🏁 FINALLY: Setting loading to false');
      setIsLoading(false);
      console.log('🏁 FINALLY: executeGuestLogin END');
    }
  };

  const handleWeChatLogin = async () => {
    // Navigate to full login screen for WeChat login
    // This would typically navigate to LoginScreen
    console.log('Navigate to WeChat login');
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.content}>
        {/* Logo and Title */}
        <View style={styles.header}>
          <View style={[styles.logoPlaceholder, { backgroundColor: theme.colors.primary + '20' }]}>
            <Text style={[styles.logoText, { color: theme.colors.primary }]}>🎵</Text>
          </View>
          <Text style={[styles.title, { color: theme.colors.text }]}>
            AI 语音翻译
          </Text>
          <Text style={[styles.subtitle, { color: theme.colors.text.secondary }]}>
            智能语音识别与翻译工具
          </Text>
        </View>

        {/* Features */}
        <View style={styles.features}>
          <View style={styles.featureItem}>
            <View style={[styles.featureIcon, { backgroundColor: theme.colors.primary + '20' }]}>
              <Text style={[styles.featureIconText, { color: theme.colors.primary }]}>🎵</Text>
            </View>
            <Text style={[styles.featureText, { color: theme.colors.text }]}>
              支持音频和视频文件翻译
            </Text>
          </View>
          
          <View style={styles.featureItem}>
            <View style={[styles.featureIcon, { backgroundColor: theme.colors.primary + '20' }]}>
              <Text style={[styles.featureIconText, { color: theme.colors.primary }]}>⚡</Text>
            </View>
            <Text style={[styles.featureText, { color: theme.colors.text }]}>
              快速准确的AI语音识别
            </Text>
          </View>
          
          <View style={styles.featureItem}>
            <View style={[styles.featureIcon, { backgroundColor: theme.colors.primary + '20' }]}>
              <Text style={[styles.featureIconText, { color: theme.colors.primary }]}>🌍</Text>
            </View>
            <Text style={[styles.featureText, { color: theme.colors.text }]}>
              多语言翻译支持
            </Text>
          </View>
        </View>

        {/* Guest Mode Button */}
        <TouchableOpacity
          style={[styles.getStartedButton, { backgroundColor: theme.colors.primary }]}
          onPress={handleGuestMode}
          disabled={isLoading}
          activeOpacity={0.8}
        >
          {isLoading ? (
            <ActivityIndicator color="#ffffff" size="small" />
          ) : (
            <Text style={styles.getStartedButtonText}>游客体验</Text>
          )}
        </TouchableOpacity>

        {/* WeChat Login */}
        <TouchableOpacity
          style={[styles.wechatButton, { borderColor: theme.colors.border }]}
          onPress={handleWeChatLogin}
          disabled={isLoading}
          activeOpacity={0.8}
        >
          <Text style={[styles.wechatButtonText, { color: theme.colors.text }]}>
            微信快速登录
          </Text>
        </TouchableOpacity>

        {/* Direct Test Button (for debugging) */}
        <TouchableOpacity
          style={[styles.wechatButton, { backgroundColor: '#FF9500', marginTop: 10 }]}
          onPress={() => {
            console.log('🔧 Direct test button pressed');
            executeGuestLogin();
          }}
          disabled={isLoading}
          activeOpacity={0.8}
        >
          <Text style={[styles.wechatButtonText, { color: '#ffffff' }]}>
            🧪 直接登录测试 (跳过对话框)
          </Text>
        </TouchableOpacity>

        {/* Guest Mode Info */}
        <View style={styles.guestInfo}>
          <Text style={[styles.guestInfoText, { color: theme.colors.text.secondary }]}>
            游客模式每日可免费翻译3次
          </Text>
          <Text style={[styles.guestInfoText, { color: theme.colors.text.secondary }]}>
            登录后可享受更多功能
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
  logoPlaceholder: {
    width: 80,
    height: 80,
    borderRadius: 40,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  logoText: {
    fontSize: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 32,
  },
  features: {
    marginBottom: 48,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  featureIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  featureIconText: {
    fontSize: 20,
  },
  featureText: {
    fontSize: 16,
    flex: 1,
  },
  getStartedButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  getStartedButtonText: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600',
  },
  wechatButton: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
  },
  wechatButtonText: {
    fontSize: 16,
    fontWeight: '500',
  },
  guestInfo: {
    alignItems: 'center',
    marginTop: 16,
  },
  guestInfoText: {
    fontSize: 12,
    textAlign: 'center',
    lineHeight: 18,
  },
});

export default WelcomeScreen;