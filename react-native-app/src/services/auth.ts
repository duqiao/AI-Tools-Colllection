import { useDispatch } from '@/store';
import { loginStart, loginSuccess, loginFailure, logout, updateUser } from '@/store/slices/authSlice';
import { apiClient } from './api';
import { WeChatUserInfo, User } from '@/types';

export class AuthService {
  // WeChat OAuth login for React Native
  static async wechatLogin(dispatch: any): Promise<{ success: boolean; error?: string }> {
    dispatch(loginStart());

    try {
      // In React Native, we would use a WeChat SDK
      // For now, this is a placeholder implementation
      // You would integrate with WeChat OAuth SDK for React Native
      
      // Mock implementation - replace with actual WeChat SDK integration
      const mockWeChatCode = 'mock_wechat_code';
      const mockUserInfo: WeChatUserInfo = {
        openid: 'mock_openid',
        nickname: 'Test User',
        headimgurl: 'https://example.com/avatar.jpg',
      };

      const response = await apiClient.wechatLogin(mockWeChatCode, mockUserInfo);

      if (response.success && response.data) {
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
      await apiClient.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {
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
  static isAuthenticated(): boolean {
    // This would be handled by Redux state
    // You can also check if token exists in AsyncStorage
    return true; // Placeholder
  }

  // Refresh token
  static async refreshToken(): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await apiClient.refreshToken();
      return { success: response.success };
    } catch (error: any) {
      return { success: false, error: error.message || 'Token refresh failed' };
    }
  }

  // WeChat SDK integration for React Native
  // This would require installing and configuring WeChat SDK
  static async installWeChatSDK(): Promise<void> {
    // Placeholder for WeChat SDK installation
    // In a real implementation, you would:
    // 1. Install WeChat SDK for React Native
    // 2. Configure app credentials
    // 3. Handle WeChat app callbacks
    console.log('WeChat SDK integration required');
  }

  // Mock method for demo purposes
  static async mockLogin(dispatch: any): Promise<{ success: boolean; error?: string }> {
    dispatch(loginStart());

    try {
      // Mock user data
      const mockUser: User = {
        id: 1,
        openid: 'mock_openid_123',
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

      const mockToken = 'mock_jwt_token_123';

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
}

export default AuthService;