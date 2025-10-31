/**
 * SETUP SELECTED USER
 * ===================
 * 
 * This script sets up the app to use your selected user instead of random guest users.
 * 
 * HOW TO USE:
 * 1. Import this file in your app's entry point (App.tsx or main screen)
 * 2. Call setupMySelectedUser() before making any API calls
 * 3. The app will now use "MySelectedUser" for all requests
 */

import { SelectedUserService } from '@/services/SelectedUserService';

/**
 * Setup the selected user for the entire app
 * Call this function when your app starts
 */
export const setupMySelectedUser = async (): Promise<void> => {
  try {
    console.log('🚀 Setting up MySelectedUser...');
    
    // Check if already configured
    const isConfigured = await SelectedUserService.isSelectedUserConfigured();
    
    if (isConfigured) {
      console.log('✅ MySelectedUser is already configured');
      
      // Verify it's working
      const verification = await SelectedUserService.verifySelectedUser();
      if (verification.success) {
        console.log('✅ MySelectedUser is working perfectly!');
        return;
      } else {
        console.log('⚠️ MySelectedUser needs refresh');
      }
    }
    
    // Setup the selected user
    const setupResult = await SelectedUserService.setupSelectedUser();
    
    if (setupResult.success) {
      console.log('🎉 MySelectedUser setup complete!');
      
      // Verify it's working
      const verification = await SelectedUserService.verifySelectedUser();
      if (verification.success) {
        console.log('🎯 MySelectedUser is ready to use!');
        console.log('');
        console.log('📋 USER INFO:');
        console.log('   Username: MySelectedUser');
        console.log('   User ID: 68fc5af3d27a3e281b1e8b68');
        console.log('   All jobs are now accessible!');
      } else {
        console.log('❌ Verification failed:', verification.error);
      }
    } else {
      console.error('❌ Failed to setup MySelectedUser:', setupResult.error);
    }
    
  } catch (error) {
    console.error('❌ Setup error:', error);
  }
};

/**
 * Get the current selected user information
 */
export const getMySelectedUser = async () => {
  return await SelectedUserService.getSelectedUser();
};

/**
 * Clear the selected user (for testing)
 */
export const clearMySelectedUser = async () => {
  await SelectedUserService.clearSelectedUser();
  console.log('🧹 MySelectedUser cleared');
};

/**
 * Refresh the selected user token
 */
export const refreshMySelectedUser = async () => {
  const result = await SelectedUserService.refreshSelectedUserToken();
  if (result.success) {
    console.log('🔄 MySelectedUser token refreshed');
  } else {
    console.error('❌ Failed to refresh token:', result.error);
  }
  return result;
};

// Export the user constants for easy access
export const MY_SELECTED_USER = {
  username: 'MySelectedUser',
  userId: '68fc5af3d27a3e281b1e8b68',
  token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiNjhmYzVhZjNkMjdhM2UyODFiMWU4YjY4Iiwib3BlbmlkIjoiZ3Vlc3RfMTc2MTM2ODgxOV9hM2VjNjM1MyIsInN1YnNjcmlwdGlvbl9sZXZlbCI6ImZyZWUiLCJleHAiOjE3NjE0MjY0MTksImlhdCI6MTc2MTM0MDAxOX0.XBRcjvltxqT9fDS2NSBhpfPZ2QR1kLNz5xKFnZBUX1M'
};

export default {
  setupMySelectedUser,
  getMySelectedUser,
  clearMySelectedUser,
  refreshMySelectedUser,
  MY_SELECTED_USER
};