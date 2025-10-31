import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiClient } from './api';

// Constants for storage
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_INFO_KEY = 'user_info';

// Selected user information
const SELECTED_USER = {
  username: 'MySelectedUser',
  userId: '68fc5af3d27a3e281b1e8b68',
  token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjhmYzVhZjNkMjdhM2UyODFiMWU4YjY4Iiwib3BlbmlkIjoiZ3Vlc3RfMTc2MTM2ODgxOV9hM2VjNjM1MyIsInN1YnNjcmlwdGlvbl9sZXZlbCI6ImZyZWUiLCJleHAiOjE3NjE0MjY0MTksImlhdCI6MTc2MTM0MDAxOX0.XBRcjvltxqT9fDS2NSBhpfPZ2QR1kLNz5xKFnZBUX1M'
};

/**
 * Setup Selected User Service
 * This service configures the app to use the selected user instead of creating random guest users
 */
export class SelectedUserService {
  /**
   * Set up the selected user in the app
   * This will replace any existing authentication with the selected user
   */
  static async setupSelectedUser(): Promise<{ success: boolean; error?: string }> {
    try {
      console.log('🔧 Setting up selected user:', SELECTED_USER.username);
      
      // Store the selected user token
      await AsyncStorage.setItem(ACCESS_TOKEN_KEY, SELECTED_USER.token);
      
      // Store user info
      const userInfo = {
        id: SELECTED_USER.userId,
        username: SELECTED_USER.username,
        openid: `selected_user_${Date.now()}`,
        avatar_url: `https://ui-avatars.com/api/?name=${SELECTED_USER.username}&background=10B981&color=fff`,
        subscription_level: 'free',
        quota_used: 0,
        quota_limit: 1000, // Large limit for testing
        quota_reset_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        is_active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      
      await AsyncStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
      
      // Update API client token
      apiClient.setToken(SELECTED_USER.token);
      
      console.log('✅ Selected user setup complete!');
      console.log(`📱 Username: ${SELECTED_USER.username}`);
      console.log(`🆔 User ID: ${SELECTED_USER.userId}`);
      console.log(`🔑 Token: ${SELECTED_USER.token.substring(0, 50)}...`);
      
      return { success: true };
      
    } catch (error: any) {
      console.error('❌ Failed to setup selected user:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Check if selected user is already configured
   */
  static async isSelectedUserConfigured(): Promise<boolean> {
    try {
      const token = await AsyncStorage.getItem(ACCESS_TOKEN_KEY);
      const userInfo = await AsyncStorage.getItem(USER_INFO_KEY);
      
      if (!token || !userInfo) {
        return false;
      }
      
      const user = JSON.parse(userInfo);
      return user.username === SELECTED_USER.username;
      
    } catch (error) {
      console.error('Error checking selected user configuration:', error);
      return false;
    }
  }

  /**
   * Get current selected user info
   */
  static async getSelectedUser(): Promise<{ username: string; userId: string; token: string } | null> {
    try {
      const token = await AsyncStorage.getItem(ACCESS_TOKEN_KEY);
      const userInfo = await AsyncStorage.getItem(USER_INFO_KEY);
      
      if (!token || !userInfo) {
        return null;
      }
      
      const user = JSON.parse(userInfo);
      
      if (user.username === SELECTED_USER.username) {
        return {
          username: user.username,
          userId: user.id,
          token: token
        };
      }
      
      return null;
      
    } catch (error) {
      console.error('Error getting selected user:', error);
      return null;
    }
  }

  /**
   * Clear selected user (useful for testing)
   */
  static async clearSelectedUser(): Promise<void> {
    try {
      await AsyncStorage.multiRemove([
        ACCESS_TOKEN_KEY, 
        REFRESH_TOKEN_KEY, 
        USER_INFO_KEY
      ]);
      console.log('✅ Selected user cleared');
    } catch (error) {
      console.error('Error clearing selected user:', error);
    }
  }

  /**
   * Force refresh the selected user token
   * This creates a fresh token for the selected user
   */
  static async refreshSelectedUserToken(): Promise<{ success: boolean; error?: string }> {
    try {
      console.log('🔄 Refreshing selected user token...');
      
      // Create a new guest user with the same username
      const response = await apiClient.request({
        method: 'POST',
        url: '/auth/guest',
        data: {
          username: SELECTED_USER.username,
          openid: `selected_user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        }
      });
      
      if (response.success && response.data) {
        const newToken = response.data.token || response.data.access_token;
        
        if (newToken) {
          // Update stored token
          await AsyncStorage.setItem(ACCESS_TOKEN_KEY, newToken);
          
          // Update API client
          apiClient.setToken(newToken);
          
          console.log('✅ Selected user token refreshed');
          return { success: true };
        }
      }
      
      return { success: false, error: 'Failed to refresh token' };
      
    } catch (error: any) {
      console.error('Error refreshing selected user token:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Verify selected user is working by making a test API call
   */
  static async verifySelectedUser(): Promise<{ success: boolean; error?: string }> {
    try {
      console.log('🔍 Verifying selected user...');
      
      // Test with a sample job (or health check)
      const response = await apiClient.healthCheck();
      
      if (response.success) {
        console.log('✅ Selected user is working!');
        return { success: true };
      } else {
        return { success: false, error: 'API test failed' };
      }
      
    } catch (error: any) {
      console.error('Error verifying selected user:', error);
      return { success: false, error: error.message };
    }
  }
}

export default SelectedUserService;