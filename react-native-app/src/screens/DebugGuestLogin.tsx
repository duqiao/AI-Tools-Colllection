import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
  SafeAreaView,
} from 'react-native';
import { useTheme } from '@/theme';
import { AuthService } from '@/services/auth';
import { useSession } from '@/contexts/SessionContext';

export const DebugGuestLogin: React.FC = () => {
  const theme = useTheme();
  const { login, state } = useSession();
  const [logs, setLogs] = useState<string[]>([]);
  const [testResults, setTestResults] = useState<any>({});
  const [isLoading, setIsLoading] = useState(false);

  const addLog = (log: string) => {
    setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: ${log}`]);
  };

  const testAuthService = async () => {
    addLog('🧪 Testing AuthService...');
    
    try {
      // Test user creation
      const guestUser = {
        id: Math.floor(Date.now() / 1000),
        openid: `guest_${Date.now()}`,
        username: '测试游客',
        subscription_level: 'free' as const,
        quota_used: 0,
        quota_limit: 3,
        quota_reset_date: new Date().toISOString().split('T')[0],
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      
      addLog(`✅ Created test user: ${guestUser.username}`);
      
      // Test storage
      await AuthService.storeUserInfo(guestUser);
      addLog('✅ Stored user info');
      
      const guestToken = `test_token_${Date.now()}`;
      const guestRefreshToken = `test_refresh_${Date.now()}`;
      await AuthService.storeTokens(guestToken, guestRefreshToken);
      addLog('✅ Stored tokens');
      
      // Test retrieval
      const storedUser = await AuthService.getStoredUserInfo();
      addLog(`✅ Retrieved user: ${storedUser?.username}`);
      
      const accessToken = await AuthService.getAccessToken();
      addLog(`✅ Retrieved access token: ${accessToken ? 'Yes' : 'No'}`);
      
      setTestResults({ user: storedUser, hasToken: !!accessToken });
      
    } catch (error: any) {
      addLog(`❌ Test failed: ${error.message}`);
      addLog(`Stack: ${error.stack}`);
    }
  };

  const testSessionLogin = async () => {
    addLog('🔐 Testing Session login...');
    
    try {
      const result = await login();
      addLog(`✅ Login result: ${result.success ? 'Success' : 'Failed'}`);
      
      if (!result.success) {
        addLog(`❌ Login error: ${result.error}`);
      }
      
      setTestResults(prev => ({ ...prev, loginResult: result }));
      
    } catch (error: any) {
      addLog(`❌ Session login failed: ${error.message}`);
      addLog(`Stack: ${error.stack}`);
    }
  };

  const testFullGuestLogin = async () => {
    addLog('🚀 Testing full guest login flow...');
    
    try {
      // Create and store guest user
      const guestUser = {
        id: Math.floor(Date.now() / 1000),
        openid: `guest_${Date.now()}`,
        username: '测试游客用户',
        avatar_url: 'https://ui-avatars.com/api/?name=Guest&background=10B981&color=fff',
        subscription_level: 'free' as const,
        quota_used: 0,
        quota_limit: 3,
        quota_reset_date: new Date().toISOString().split('T')[0],
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      addLog(`👤 Creating guest user: ${guestUser.username}`);
      await AuthService.storeUserInfo(guestUser);
      
      const guestToken = `guest_token_${Date.now()}`;
      const guestRefreshToken = `guest_refresh_${Date.now()}`;
      await AuthService.storeTokens(guestToken, guestRefreshToken);
      
      addLog('💾 Stored user data and tokens');
      
      // Test login
      const result = await login();
      addLog(`🔐 Login result: ${result.success ? 'Success' : 'Failed - ' + result.error}`);
      
      if (result.success) {
        addLog('✅ Full guest login successful!');
        Alert.alert('成功', '游客登录测试成功！');
      }
      
    } catch (error: any) {
      addLog(`❌ Full guest login failed: ${error.message}`);
      addLog(`Stack: ${error.stack}`);
      Alert.alert('失败', `游客登录测试失败: ${error.message}`);
    }
  };

  const testWelcomeScreenFlow = async () => {
    addLog('🚀 Testing WelcomeScreen exact flow...');
    
    try {
      // Simulate the exact flow from WelcomeScreen
      setIsLoading(true);
      
      // Create guest user data with correct types (exact same as WelcomeScreen)
      const guestUser = {
        id: Math.floor(Date.now() / 1000),
        openid: `guest_${Date.now()}`,
        username: '游客用户',
        avatar_url: 'https://ui-avatars.com/api/?name=Guest&background=10B981&color=fff',
        subscription_level: 'free' as const,
        quota_used: 0,
        quota_limit: 3,
        quota_reset_date: new Date().toISOString().split('T')[0],
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      addLog(`👤 Created guest user: ${guestUser.username}`);

      // Store guest user info
      await AuthService.storeUserInfo(guestUser);
      addLog('💾 Stored guest user info');
      
      // Create mock tokens for guest session (exact same as WelcomeScreen)
      const guestToken = `guest_token_${Date.now()}`;
      const guestRefreshToken = `guest_refresh_${Date.now()}`;
      await AuthService.storeTokens(guestToken, guestRefreshToken);
      addLog('🔐 Stored guest tokens');

      // Verify user is stored
      const storedUser = await AuthService.getStoredUserInfo();
      addLog('✅ Verified stored user');

      // Initialize session (this is where it might hang)
      addLog('🔐 Initializing session...');
      const result = await login();
      
      addLog(`📋 Login result: ${JSON.stringify(result)}`);
      
      if (result.success) {
        addLog('✅ WelcomeScreen flow successful!');
        Alert.alert('成功', 'WelcomeScreen流程测试成功！');
      } else {
        addLog(`❌ WelcomeScreen flow failed: ${result.error}`);
        Alert.alert('失败', `WelcomeScreen流程失败: ${result.error}`);
      }
      
    } catch (error: any) {
      addLog(`❌ WelcomeScreen flow error: ${error.message}`);
      addLog(`Stack: ${error.stack}`);
      Alert.alert('失败', `WelcomeScreen流程失败: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const clearData = async () => {
    addLog('🗑️ Clearing all stored data...');
    
    try {
      await AuthService.clearStoredAuth();
      addLog('✅ Cleared stored auth data');
      setLogs([]);
      setTestResults({});
    } catch (error: any) {
      addLog(`❌ Clear failed: ${error.message}`);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.content}>
        <Text style={[styles.title, { color: theme.colors.text }]}>
          游客登录调试测试
        </Text>
        
        <View style={styles.sessionInfo}>
          <Text style={[styles.sessionText, { color: theme.colors.textSecondary }]}>
            当前状态: {state.isAuthenticated ? '已登录' : '未登录'}
          </Text>
          {state.user && (
            <Text style={[styles.sessionText, { color: theme.colors.textSecondary }]}>
              用户: {state.user.username}
            </Text>
          )}
        </View>

        <View style={styles.buttonGroup}>
          <TouchableOpacity
            style={[styles.button, { backgroundColor: theme.colors.primary }]}
            onPress={testAuthService}
          >
            <Text style={styles.buttonText}>测试AuthService</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.button, { backgroundColor: theme.colors.secondary }]}
            onPress={testSessionLogin}
          >
            <Text style={styles.buttonText}>测试Session Login</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.button, { backgroundColor: theme.colors.success }]}
            onPress={testFullGuestLogin}
          >
            <Text style={styles.buttonText}>完整游客登录测试</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.button, { backgroundColor: '#FF9500' }]}
            onPress={testWelcomeScreenFlow}
          >
            <Text style={styles.buttonText}>测试WelcomeScreen流程</Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.button, { backgroundColor: theme.colors.error }]}
            onPress={clearData}
          >
            <Text style={styles.buttonText}>清除数据</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.testResults}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            测试结果:
          </Text>
          {testResults.user && (
            <Text style={[styles.resultText, { color: theme.colors.textSecondary }]}>
              用户: {testResults.user.username}
            </Text>
          )}
          {testResults.loginResult && (
            <Text style={[
              styles.resultText, 
              { color: testResults.loginResult.success ? theme.colors.success : theme.colors.error }
            ]}>
              登录: {testResults.loginResult.success ? '成功' : '失败'}
            </Text>
          )}
        </View>

        <ScrollView style={styles.logContainer}>
          <Text style={[styles.logTitle, { color: theme.colors.text }]}>
            日志:
          </Text>
          {logs.map((log, index) => (
            <Text key={index} style={[styles.logText, { color: theme.colors.textSecondary }]}>
              {log}
            </Text>
          ))}
        </ScrollView>
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
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
  },
  sessionInfo: {
    backgroundColor: '#f5f5f5',
    padding: 15,
    borderRadius: 8,
    marginBottom: 20,
  },
  sessionText: {
    fontSize: 14,
    marginBottom: 5,
  },
  buttonGroup: {
    marginBottom: 20,
    gap: 10,
  },
  button: {
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  testResults: {
    backgroundColor: '#f5f5f5',
    padding: 15,
    borderRadius: 8,
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 10,
  },
  resultText: {
    fontSize: 14,
    marginBottom: 5,
  },
  logContainer: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 15,
    borderRadius: 8,
    maxHeight: 300,
  },
  logTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 10,
  },
  logText: {
    fontSize: 12,
    fontFamily: 'monospace',
    marginBottom: 2,
  },
});

export default DebugGuestLogin;