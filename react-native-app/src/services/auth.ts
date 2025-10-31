import AsyncStorage from '@react-native-async-storage/async-storage';
import { useDispatch } from '@/store';
import { loginStart, loginSuccess, loginFailure, logout, updateUser } from '@/store/slices/authSlice';
import { apiClient } from './api';
import { WeChatUserInfo, User } from '@/types';

// Constants for storage
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_INFO_KEY = 'user_info';

export class AuthService {
  // Initialize auth service with app startup
  static async initializeAuth(): Promise<void> {
    try {
      const token = await this.getAccessToken();
      const userInfo = await this.getStoredUserInfo();
      
      if (token && userInfo) {
        // Validate token with backend
        const isValid = await this.validateToken(token);
        if (!isValid) {
          // Token invalid, try refresh
          const refreshSuccess = await this.refreshAccessToken();
          if (!refreshSuccess) {
            // Refresh failed, clear session
            await this.clearStoredAuth();
            return;
          }
        }
        
        // Check if session needs periodic refresh
        await this.setupPeriodicTokenRefresh();
      }
    } catch (error) {
      console.error('Auth initialization failed:', error);
      await this.clearStoredAuth();
    }
  }

  // WeChat OAuth login for React Native
  static async wechatLogin(dispatch: any): Promise<{ success: boolean; error?: string }> {
    dispatch(loginStart());

    try {
      // WeChat SDK integration for React Native
      // Note: In production, you would use a proper WeChat SDK
      // For now, implementing with Expo's Web browser approach
      
      // For demo purposes, use mock implementation
      // In production, replace with actual WeChat SDK calls
      const mockWeChatCode = await this.getMockWeChatCode();
      const mockUserInfo: WeChatUserInfo = {
        openid: 'mock_openid_' + Date.now(),
        nickname: 'AI翻译用户',
        headimgurl: 'https://example.com/avatar.jpg',
        unionid: 'mock_unionid_' + Date.now(),
      };

      const response = await apiClient.wechatLogin(mockWeChatCode, mockUserInfo);

      if (response.success && response.data) {
        // Store tokens and user info
        await this.storeTokens(response.data.token, response.data.refreshToken);
        await this.storeUserInfo(response.data.user);
        
        dispatch(loginSuccess({
          user: response.data.user,
          token: response.data.token,
        }));
        
        return { success: true };
      } else {
        const errorMessage = response.error || 'Login failed';
        dispatch(loginFailure(errorMessage));
        return { success: false, error: errorMessage };
      }
    } catch (error: any) {
      const errorMessage = error.message || 'Login failed';
      dispatch(loginFailure(errorMessage));
      return { success: false, error: errorMessage };
    }
  }

  // Logout user
  static async logoutUser(dispatch: any): Promise<void> {
    try {
      // Call backend logout endpoint
      await apiClient.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
      // Clear all stored auth data
      await this.clearStoredAuth();
      // Clear session data
      await AsyncStorage.removeItem('user_session');
      // Update Redux state
      dispatch(logout());
    }
  }

  // Get current user profile
  static async getCurrentUser(dispatch: any): Promise<User | null> {
    try {
      const response = await apiClient.getUserProfile();
      if (response.success && response.data) {
        dispatch(updateUser(response.data));
        return response.data;
      }
      return null;
    } catch (error) {
      console.error('Failed to get current user:', error);
      return null;
    }
  }

  // Update user profile
  static async updateProfile(dispatch: any, updates: Partial<User>): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await apiClient.updateUserProfile(updates);
      if (response.success && response.data) {
        dispatch(updateUser(response.data));
        return { success: true };
      } else {
        return { success: false, error: response.error || 'Update failed' };
      }
    } catch (error: any) {
      return { success: false, error: error.message || 'Update failed' };
    }
  }

  // Check if user is authenticated
  static async isAuthenticated(): Promise<boolean> {
    try {
      const token = await this.getAccessToken();
      return !!token && await this.validateToken(token);
    } catch (error) {
      return false;
    }
  }

  // Get stored access token
  static async getAccessToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(ACCESS_TOKEN_KEY);
    } catch (error) {
      return null;
    }
  }

  // Get stored refresh token
  static async getRefreshToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(REFRESH_TOKEN_KEY);
    } catch (error) {
      return null;
    }
  }

  // Get stored user info
  static async getStoredUserInfo(): Promise<User | null> {
    try {
      const userInfoStr = await AsyncStorage.getItem(USER_INFO_KEY);
      return userInfoStr ? JSON.parse(userInfoStr) : null;
    } catch (error) {
      return null;
    }
  }

  // Store tokens with session persistence
  static async storeTokens(accessToken: string, refreshToken: string): Promise<void> {
    try {
      await AsyncStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
      await AsyncStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      // Update session persistence
      await this.persistSession();
    } catch (error) {
      console.error('Failed to store tokens:', error);
      throw error;
    }
  }

  // Store user info with session persistence
  static async storeUserInfo(user: User): Promise<void> {
    try {
      await AsyncStorage.setItem(USER_INFO_KEY, JSON.stringify(user));
      // Update session persistence
      await this.persistSession();
    } catch (error) {
      console.error('Failed to store user info:', error);
      throw error;
    }
  }

  // Clear stored auth data
  static async clearStoredAuth(): Promise<void> {
    try {
      await AsyncStorage.multiRemove([ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY, USER_INFO_KEY]);
      // Also clear session data
      await AsyncStorage.removeItem('user_session');
    } catch (error) {
      console.error('Failed to clear stored auth:', error);
    }
  }

  // Validate token with backend
  static async validateToken(token: string): Promise<boolean> {
    try {
      // For guest tokens, skip backend validation
      if (token && token.startsWith('guest_token_')) {
        console.log('🔓 Skipping validation for guest token');
        return true;
      }
      
      const response = await apiClient.getUserProfile();
      return response.success;
    } catch (error) {
      console.error('Token validation error:', error);
      return false;
    }
  }

  // Refresh access token
  static async refreshAccessToken(): Promise<boolean> {
    try {
      const refreshToken = await this.getRefreshToken();
      if (!refreshToken) {
        return false;
      }

      // For guest refresh tokens, skip backend validation and just return true
      if (refreshToken.startsWith('guest_refresh_')) {
        console.log('🔄 Skipping refresh for guest token');
        return true;
      }

      const response = await apiClient.refreshToken(refreshToken);
      
      if (response.success && response.data) {
        await this.storeTokens(response.data.accessToken, response.data.refreshToken);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  // Auto-refresh token method
  static async autoRefreshToken(): Promise<boolean> {
    const maxRetries = 3;
    let retryCount = 0;
    
    while (retryCount < maxRetries) {
      try {
        const success = await this.refreshAccessToken();
        if (success) {
          return true;
        }
        retryCount++;
        
        // Wait before retry with exponential backoff
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, retryCount)));
      } catch (error) {
        retryCount++;
        if (retryCount >= maxRetries) {
          return false;
        }
      }
    }
    
    return false;
  }

  // Setup periodic token refresh
  static async setupPeriodicTokenRefresh(): Promise<void> {
    // Refresh token every 30 minutes to ensure validity
    const REFRESH_INTERVAL = 30 * 60 * 1000; // 30 minutes
    
    setInterval(async () => {
      try {
        const token = await this.getAccessToken();
        if (token) {
          await this.refreshAccessToken();
        }
      } catch (error) {
        console.error('Periodic token refresh failed:', error);
      }
    }, REFRESH_INTERVAL);
  }

  // Session persistence management
  static async persistSession(): Promise<void> {
    try {
      const token = await this.getAccessToken();
      const refreshToken = await this.getRefreshToken();
      const userInfo = await this.getStoredUserInfo();
      
      if (token && refreshToken && userInfo) {
        const sessionData = {
          token,
          refreshToken,
          userInfo,
          lastActivity: new Date().toISOString(),
        };
        
        await AsyncStorage.setItem('user_session', JSON.stringify(sessionData));
      }
    } catch (error) {
      console.error('Failed to persist session:', error);
    }
  }

  // Restore session from storage
  static async restoreSession(): Promise<{ success: boolean; error?: string }> {
    try {
      const sessionDataStr = await AsyncStorage.getItem('user_session');
      if (!sessionDataStr) {
        return { success: false, error: 'No session found' };
      }
      
      const sessionData = JSON.parse(sessionDataStr);
      const { token, refreshToken, userInfo, lastActivity } = sessionData;
      
      // Check if session is too old (24 hours)
      const sessionAge = new Date().getTime() - new Date(lastActivity).getTime();
      const MAX_SESSION_AGE = 24 * 60 * 60 * 1000; // 24 hours
      
      if (sessionAge > MAX_SESSION_AGE) {
        await this.clearStoredAuth();
        return { success: false, error: 'Session expired' };
      }
      
      // Validate token with backend
      const isValid = await this.validateToken(token);
      if (!isValid) {
        // Try refresh token
        if (refreshToken) {
          const refreshSuccess = await this.refreshAccessToken();
          if (!refreshSuccess) {
            await this.clearStoredAuth();
            return { success: false, error: 'Session invalid' };
          }
        } else {
          await this.clearStoredAuth();
          return { success: false, error: 'No refresh token' };
        }
      }
      
      // Update last activity
      await this.persistSession();
      
      return { success: true };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  // Update session activity
  static async updateSessionActivity(): Promise<void> {
    try {
      const sessionDataStr = await AsyncStorage.getItem('user_session');
      if (sessionDataStr) {
        const sessionData = JSON.parse(sessionDataStr);
        sessionData.lastActivity = new Date().toISOString();
        await AsyncStorage.setItem('user_session', JSON.stringify(sessionData));
      }
    } catch (error) {
      console.error('Failed to update session activity:', error);
    }
  }

  // Check session validity
  static async isSessionValid(): Promise<boolean> {
    try {
      const token = await this.getAccessToken();
      if (!token) {
        return false;
      }
      
      const isValid = await this.validateToken(token);
      if (!isValid) {
        // Try refresh token
        return await this.refreshAccessToken();
      }
      
      return true;
    } catch (error) {
      console.error('Session validation failed:', error);
      return false;
    }
  }

  // Handle session timeout
  static async handleSessionTimeout(): Promise<void> {
    try {
      await this.clearStoredAuth();
      // You could navigate to login screen here or emit an event
      console.log('Session timed out, user needs to login again');
    } catch (error) {
      console.error('Failed to handle session timeout:', error);
    }
  }

  // Mock method for demo purposes
  static async mockLogin(dispatch: any): Promise<{ success: boolean; error?: string }> {
    dispatch(loginStart());

    try {
      // Mock user data
      const mockUser: User = {
        id: 1,
        openid: 'mock_openid_' + Date.now(),
        username: 'Demo User',
        avatar_url: 'https://example.com/avatar.jpg',
        subscription_level: 'free',
        quota_used: 0,
        quota_limit: 1,
        quota_reset_date: new Date().toISOString().split('T')[0],
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      const mockToken = 'mock_jwt_token_' + Date.now();
      const mockRefreshToken = 'mock_refresh_token_' + Date.now();

      // Store tokens
      await this.storeTokens(mockToken, mockRefreshToken);
      await this.storeUserInfo(mockUser);

      dispatch(loginSuccess({
        user: mockUser,
        token: mockToken,
      }));

      return { success: true };
    } catch (error: any) {
      const errorMessage = error.message || 'Mock login failed';
      dispatch(loginFailure(errorMessage));
      return { success: false, error: errorMessage };
    }
  }

  // Get mock WeChat code (for demo purposes)
  private static async getMockWeChatCode(): Promise<string> {
    // In production, this would come from WeChat SDK
    // For demo, generate a mock code
    return 'mock_wechat_code_' + Date.now();
  }

  // WeChat SDK setup instructions
  static getWeChatSDKSetupInstructions(): string[] {
    return [
      '1. Install WeChat SDK for React Native:',
      '   npm install react-native-wechat-lib',
      '',
      '2. Configure Android (android/app/build.gradle):',
      '   - Add WeChat app package',
      '   - Configure appid and app secret',
      '',
      '3. Configure iOS (ios/Podfile):',
      '   - pod install WechatSDK',
      '   - Configure Info.plist',
      '',
      '4. Initialize WeChat SDK in your app:',
      '   import { Wechat } from "react-native-wechat-lib"',
      '   Wechat.registerApp("your_appid", "universal_linking");',
      '',
      '5. Handle WeChat login:',
      '   Wechat.sendAuthRequest("your_appid", "snsapi_userinfo");',
      '   // Handle response in WeChat callback',
      '',
      '6. For development, use web-based WeChat login:',
      '   - Use expo-web-browser to open WeChat login page',
      '   - Handle callback with deep linking',
    ];
  }

  // Check if WeChat app is installed (mock implementation)
  static async isWeChatInstalled(): Promise<boolean> {
    // In production, you would check if WeChat app is installed
    // For React Native, this would be platform-specific
    try {
      // This is a mock implementation
      // In production, use platform-specific APIs
      return true; // Assume WeChat is installed for demo
    } catch (error) {
      return false;
    }
  }

  // Open WeChat for login (mock implementation)
  static async openWeChatLogin(): Promise<{ success: boolean; error?: string }> {
    try {
      // In production, this would open the WeChat app
      // For demo, we return success and use mock login
      
      // You might use Linking API for React Native
      // const url = 'weixin://dl/business/?appid=YOUR_APPID&path=pages/index/index';
      // Linking.openURL(url);
      
      return { success: true };
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }
}

export default AuthService;
  // Create guest user with required openid field
  const createGuestUser = async () => {
    try {
      const timestamp = Date.now();
      const randomId = Math.random().toString(36).substr(2, 9);
      const response = await apiClient.request({
        method: 'POST',
        url: '/auth/guest',
        data: {
          username: 'test_user',
          openid: 'test_user_ai'
        }
      });
      
      if (response.success && response.data) {
        const { token } = response.data;
        await AsyncStorage.setItem(ACCESS_TOKEN_KEY, token);
        return { success: true, token, user: response.data.user };
      }
      
      return { success: false, error: response.error || 'Guest login failed' };
    } catch (error) {
      console.error('Guest login failed:', error);
      return { success: false, error: error.message };
    }
  };
