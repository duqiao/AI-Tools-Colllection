import AsyncStorage from '@react-native-async-storage/async-storage';
import { User } from '@/types';
import { AuthService } from '@/services/auth';

// Guest user configuration
export interface GuestUserConfig {
  dailyQuotaLimit: number;
  subscriptionLevel: 'free';
  features: {
    canSaveHistory: boolean;
    canSyncSettings: boolean;
    canShareResults: boolean;
    canExportResults: boolean;
    hasAdvancedFeatures: boolean;
  };
}

// Default guest configuration
export const DEFAULT_GUEST_CONFIG: GuestUserConfig = {
  dailyQuotaLimit: 3,
  subscriptionLevel: 'free',
  features: {
    canSaveHistory: false,
    canSyncSettings: false,
    canShareResults: true,
    canExportResults: false,
    hasAdvancedFeatures: false,
  },
};

// Guest user manager class
export class GuestUserManager {
  private static readonly GUEST_USER_KEY = 'guest_user_info';
  private static readonly GUEST_QUOTA_KEY = 'guest_quota_usage';
  private static readonly GUEST_LAST_RESET_KEY = 'guest_last_reset_date';

  /**
   * Check if current user is a guest
   */
  static async isGuestUser(): Promise<boolean> {
    try {
      const userInfo = await AuthService.getStoredUserInfo();
      return userInfo?.username === '游客用户' || userInfo?.openid?.startsWith('guest_') || false;
    } catch (error) {
      console.error('Failed to check guest status:', error);
      return false;
    }
  }

  /**
   * Create a new guest user
   */
  static async createGuestUser(): Promise<User> {
    const timestamp = Date.now();
    
    const guestUser: User = {
      id: Math.floor(timestamp / 1000), // Convert to number
      openid: `guest_${timestamp}`,
      username: '游客用户',
      avatar_url: `https://ui-avatars.com/api/?name=Guest&background=10B981&color=fff&size=128`,
      subscription_level: DEFAULT_GUEST_CONFIG.subscriptionLevel,
      quota_used: 0,
      quota_limit: DEFAULT_GUEST_CONFIG.dailyQuotaLimit,
      quota_reset_date: new Date().toISOString().split('T')[0],
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    // Store guest user info
    await AuthService.storeUserInfo(guestUser);
    await this.updateGuestQuotaUsage(0);
    await this.setLastResetDate(new Date().toISOString().split('T')[0]);

    return guestUser;
  }

  /**
   * Get guest user quota information
   */
  static async getGuestQuotaInfo(): Promise<{
    used: number;
    limit: number;
    remaining: number;
    resetDate: string;
    canTranslate: boolean;
  }> {
    try {
      const userInfo = await AuthService.getStoredUserInfo();
      const isGuest = await this.isGuestUser();

      if (!isGuest || !userInfo) {
        return {
          used: 0,
          limit: 0,
          remaining: 0,
          resetDate: '',
          canTranslate: false,
        };
      }

      // Check if we need to reset quota (new day)
      await this.checkAndResetQuotaIfNeeded();

      const used = await this.getGuestQuotaUsage();
      const limit = userInfo.quota_limit || DEFAULT_GUEST_CONFIG.dailyQuotaLimit;
      const remaining = Math.max(0, limit - used);
      const resetDate = userInfo.quota_reset_date || new Date().toISOString().split('T')[0];

      return {
        used,
        limit,
        remaining,
        resetDate,
        canTranslate: remaining > 0,
      };
    } catch (error) {
      console.error('Failed to get guest quota info:', error);
      return {
        used: 0,
        limit: DEFAULT_GUEST_CONFIG.dailyQuotaLimit,
        remaining: DEFAULT_GUEST_CONFIG.dailyQuotaLimit,
        resetDate: new Date().toISOString().split('T')[0],
        canTranslate: true,
      };
    }
  }

  /**
   * Increment guest quota usage
   */
  static async incrementGuestQuotaUsage(): Promise<boolean> {
    try {
      const quotaInfo = await this.getGuestQuotaInfo();
      
      if (!quotaInfo.canTranslate) {
        return false;
      }

      const newUsage = quotaInfo.used + 1;
      await this.updateGuestQuotaUsage(newUsage);
      
      // Update user info as well
      const userInfo = await AuthService.getStoredUserInfo();
      if (userInfo) {
        userInfo.quota_used = newUsage;
        await AuthService.storeUserInfo(userInfo);
      }

      return true;
    } catch (error) {
      console.error('Failed to increment guest quota:', error);
      return false;
    }
  }

  /**
   * Check and reset quota if needed (new day)
   */
  private static async checkAndResetQuotaIfNeeded(): Promise<void> {
    try {
      const lastResetDate = await this.getLastResetDate();
      const today = new Date().toISOString().split('T')[0];

      if (lastResetDate !== today) {
        await this.updateGuestQuotaUsage(0);
        await this.setLastResetDate(today);
        
        // Update user quota_reset_date
        const userInfo = await AuthService.getStoredUserInfo();
        if (userInfo) {
          userInfo.quota_used = 0;
          userInfo.quota_reset_date = today;
          await AuthService.storeUserInfo(userInfo);
        }
        
        console.log('Guest quota reset for new day');
      }
    } catch (error) {
      console.error('Failed to check/reset quota:', error);
    }
  }

  /**
   * Get guest quota usage
   */
  private static async getGuestQuotaUsage(): Promise<number> {
    try {
      const usage = await AsyncStorage.getItem(this.GUEST_QUOTA_KEY);
      return usage ? parseInt(usage, 10) : 0;
    } catch (error) {
      console.error('Failed to get guest quota usage:', error);
      return 0;
    }
  }

  /**
   * Update guest quota usage
   */
  private static async updateGuestQuotaUsage(usage: number): Promise<void> {
    try {
      await AsyncStorage.setItem(this.GUEST_QUOTA_KEY, usage.toString());
    } catch (error) {
      console.error('Failed to update guest quota usage:', error);
      throw error;
    }
  }

  /**
   * Get last reset date
   */
  private static async getLastResetDate(): Promise<string> {
    try {
      return await AsyncStorage.getItem(this.GUEST_LAST_RESET_KEY) || '';
    } catch (error) {
      console.error('Failed to get last reset date:', error);
      return '';
    }
  }

  /**
   * Set last reset date
   */
  private static async setLastResetDate(date: string): Promise<void> {
    try {
      await AsyncStorage.setItem(this.GUEST_LAST_RESET_KEY, date);
    } catch (error) {
      console.error('Failed to set last reset date:', error);
    }
  }

  /**
   * Get guest user features
   */
  static getGuestFeatures(): GuestUserConfig['features'] {
    return DEFAULT_GUEST_CONFIG.features;
  }

  /**
   * Check if guest can access a specific feature
   */
  static canAccessFeature(feature: keyof GuestUserConfig['features']): boolean {
    return DEFAULT_GUEST_CONFIG.features[feature];
  }

  /**
   * Get upgrade prompt message for guest users
   */
  static getUpgradeMessage(): string {
    const quotaInfo = this.getGuestQuotaInfo();
    return '升级为正式用户，享受无限翻译、历史记录保存等高级功能';
  }

  /**
   * Upgrade guest to regular user (would be called after successful registration/login)
   */
  static async upgradeGuestToRegularUser(regularUser: User): Promise<void> {
    try {
      const isGuest = await this.isGuestUser();
      
      if (isGuest) {
        // Clear guest-specific data
        await AsyncStorage.multiRemove([
          this.GUEST_USER_KEY,
          this.GUEST_QUOTA_KEY,
          this.GUEST_LAST_RESET_KEY,
        ]);
        
        console.log('Guest user upgraded to regular user');
      }
      
      // Store regular user info
      await AuthService.storeUserInfo(regularUser);
    } catch (error) {
      console.error('Failed to upgrade guest user:', error);
      throw error;
    }
  }

  /**
   * Get guest user session info
   */
  static async getGuestSessionInfo(): Promise<{
    isGuest: boolean;
    userId: string;
    sessionStart: string;
    quotaInfo: any;
  } | null> {
    try {
      const isGuest = await this.isGuestUser();
      const userInfo = await AuthService.getStoredUserInfo();
      
      if (!isGuest || !userInfo) {
        return null;
      }

      return {
        isGuest: true,
        userId: userInfo.openid,
        sessionStart: userInfo.created_at,
        quotaInfo: await this.getGuestQuotaInfo(),
      };
    } catch (error) {
      console.error('Failed to get guest session info:', error);
      return null;
    }
  }
}

export default GuestUserManager;