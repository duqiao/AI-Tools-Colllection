/**
 * TEST SELECTED USER COMPONENT
 * ============================
 * 
 * This component can be used to test if MySelectedUser is working correctly.
 * Add it to any screen to display user status and test functionality.
 */

import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { useTheme } from '@/theme';
import { 
  getMySelectedUser, 
  refreshMySelectedUser, 
  clearMySelectedUser,
  MY_SELECTED_USER 
} from '@/services/setupSelectedUser';
import { SelectedUserService } from '@/services/SelectedUserService';
import { apiClient } from '@/services/api';

export const TestSelectedUser = () => {
  const theme = useTheme();
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [userInfo, setUserInfo] = useState<any>(null);
  const [lastTest, setLastTest] = useState<string>('');

  useEffect(() => {
    checkUserStatus();
  }, []);

  const checkUserStatus = async () => {
    setStatus('loading');
    setLastTest('');
    
    try {
      const user = await getMySelectedUser();
      
      if (user) {
        setUserInfo(user);
        setStatus('ready');
        setLastTest('✅ Selected user found and working');
      } else {
        setStatus('error');
        setLastTest('❌ Selected user not configured');
      }
    } catch (error: any) {
      setStatus('error');
      setLastTest(`❌ Error: ${error.message}`);
    }
  };

  const testAPI = async () => {
    setLastTest('🔄 Testing API connection...');
    
    try {
      const response = await apiClient.healthCheck();
      
      if (response.success) {
        setLastTest('✅ API connection successful with selected user!');
      } else {
        setLastTest('❌ API connection failed');
      }
    } catch (error: any) {
      setLastTest(`❌ API test failed: ${error.message}`);
    }
  };

  const testUploadAPI = async () => {
    setLastTest('🔄 Testing upload API...');
    
    try {
      // Test with a sample job ID (replace with actual job ID)
      const sampleJobId = '255fcfda-e12f-45dd-89d4-58abdec0126e';
      const response = await apiClient.request({
        method: 'GET',
        url: `/upload/${sampleJobId}`
      });
      
      if (response.success) {
        setLastTest('✅ Upload API working! Job data retrieved.');
      } else {
        setLastTest(`❌ Upload API failed: ${response.error}`);
      }
    } catch (error: any) {
      setLastTest(`❌ Upload API test failed: ${error.message}`);
    }
  };

  const refreshUser = async () => {
    setLastTest('🔄 Refreshing user token...');
    
    try {
      const result = await refreshMySelectedUser();
      
      if (result.success) {
        setLastTest('✅ User token refreshed successfully!');
        await checkUserStatus(); // Refresh user info
      } else {
        setLastTest(`❌ Refresh failed: ${result.error}`);
      }
    } catch (error: any) {
      setLastTest(`❌ Refresh error: ${error.message}`);
    }
  };

  const resetUser = async () => {
    Alert.alert(
      'Reset Selected User',
      'This will clear MySelectedUser configuration. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reset',
          style: 'destructive',
          onPress: async () => {
            setLastTest('🔄 Resetting user...');
            try {
              await clearMySelectedUser();
              setLastTest('✅ User cleared. Restart app to reconfigure.');
              setUserInfo(null);
              setStatus('error');
            } catch (error: any) {
              setLastTest(`❌ Reset failed: ${error.message}`);
            }
          }
        }
      ]
    );
  };

  const getStatusColor = () => {
    switch (status) {
      case 'ready': return theme.colors.success;
      case 'error': return theme.colors.error;
      default: return theme.colors.text.secondary;
    }
  };

  return (
    <View style={{ flex: 1, padding: 16, backgroundColor: theme.colors.background }}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={{ marginBottom: 24 }}>
          <Text style={{ 
            fontSize: 24, 
            fontWeight: 'bold', 
            color: theme.colors.text.primary,
            marginBottom: 8 
          }}>
            MySelectedUser Test
          </Text>
          <Text style={{ 
            fontSize: 14, 
            color: theme.colors.text.secondary,
            marginBottom: 16 
          }}>
            Test if the selected user is configured and working correctly
          </Text>
        </View>

        {/* Status Card */}
        <View style={{
          backgroundColor: theme.colors.surface,
          padding: 16,
          borderRadius: 12,
          marginBottom: 16,
          borderWidth: 1,
          borderColor: theme.colors.border
        }}>
          <Text style={{ 
            fontSize: 16, 
            fontWeight: '600', 
            color: theme.colors.text.primary,
            marginBottom: 8 
          }}>
            Status
          </Text>
          <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 12 }}>
            <View style={{
              width: 12,
              height: 12,
              borderRadius: 6,
              backgroundColor: getStatusColor(),
              marginRight: 8
            }} />
            <Text style={{ 
              fontSize: 14, 
              color: theme.colors.text.primary,
              textTransform: 'capitalize'
            }}>
              {status}
            </Text>
          </View>
          
          {lastTest ? (
            <Text style={{ 
              fontSize: 12, 
              color: theme.colors.text.secondary,
              fontFamily: 'monospace'
            }}>
              {lastTest}
            </Text>
          ) : null}
        </View>

        {/* User Info */}
        {userInfo && (
          <View style={{
            backgroundColor: theme.colors.surface,
            padding: 16,
            borderRadius: 12,
            marginBottom: 16,
            borderWidth: 1,
            borderColor: theme.colors.border
          }}>
            <Text style={{ 
              fontSize: 16, 
              fontWeight: '600', 
              color: theme.colors.text.primary,
              marginBottom: 12 
            }}>
              User Information
            </Text>
            
            <Text style={{ fontSize: 14, color: theme.colors.text.secondary, marginBottom: 4 }}>
              Username: <Text style={{ color: theme.colors.text.primary, fontWeight: '500' }}>
                {userInfo.username}
              </Text>
            </Text>
            
            <Text style={{ fontSize: 14, color: theme.colors.text.secondary, marginBottom: 4 }}>
              User ID: <Text style={{ color: theme.colors.text.primary, fontWeight: '500' }}>
                {userInfo.userId}
              </Text>
            </Text>
            
            <Text style={{ fontSize: 14, color: theme.colors.text.secondary, marginBottom: 4 }}>
              Token: <Text style={{ color: theme.colors.text.primary, fontWeight: '500', fontFamily: 'monospace' }}>
                {userInfo.token.substring(0, 20)}...
              </Text>
            </Text>
          </View>
        )}

        {/* Action Buttons */}
        <View style={{ gap: 12 }}>
          <TouchableOpacity
            onPress={checkUserStatus}
            style={{
              backgroundColor: theme.colors.primary,
              padding: 14,
              borderRadius: 8,
              alignItems: 'center'
            }}
          >
            <Text style={{ 
              color: 'white', 
              fontSize: 16, 
              fontWeight: '600' 
            }}>
              Check User Status
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={testAPI}
            style={{
              backgroundColor: theme.colors.surface,
              padding: 14,
              borderRadius: 8,
              alignItems: 'center',
              borderWidth: 1,
              borderColor: theme.colors.border
            }}
          >
            <Text style={{ 
              color: theme.colors.text.primary, 
              fontSize: 16, 
              fontWeight: '600' 
            }}>
              Test API Connection
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={testUploadAPI}
            style={{
              backgroundColor: theme.colors.surface,
              padding: 14,
              borderRadius: 8,
              alignItems: 'center',
              borderWidth: 1,
              borderColor: theme.colors.border
            }}
          >
            <Text style={{ 
              color: theme.colors.text.primary, 
              fontSize: 16, 
              fontWeight: '600' 
            }}>
              Test Upload API
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={refreshUser}
            style={{
              backgroundColor: theme.colors.warning,
              padding: 14,
              borderRadius: 8,
              alignItems: 'center'
            }}
          >
            <Text style={{ 
              color: 'white', 
              fontSize: 16, 
              fontWeight: '600' 
            }}>
              Refresh Token
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={resetUser}
            style={{
              backgroundColor: theme.colors.error,
              padding: 14,
              borderRadius: 8,
              alignItems: 'center'
            }}
          >
            <Text style={{ 
              color: 'white', 
              fontSize: 16, 
              fontWeight: '600' 
            }}>
              Reset User
            </Text>
          </TouchableOpacity>
        </View>

        {/* Instructions */}
        <View style={{
          backgroundColor: theme.colors.surface,
          padding: 16,
          borderRadius: 12,
          marginTop: 16,
          borderWidth: 1,
          borderColor: theme.colors.border
        }}>
          <Text style={{ 
            fontSize: 16, 
            fontWeight: '600', 
            color: theme.colors.text.primary,
            marginBottom: 8 
          }}>
            Usage Instructions
          </Text>
          
          <Text style={{ fontSize: 14, color: theme.colors.text.secondary, lineHeight: 20 }}>
            1. <Text style={{ fontWeight: '500' }}>Check Status:</Text> Verify user is configured{'\n'}
            2. <Text style={{ fontWeight: '500' }}>Test API:</Text> Check basic connectivity{'\n'}
            3. <Text style={{ fontWeight: '500' }}>Test Upload:</Text> Verify job access{'\n'}
            4. <Text style={{ fontWeight: '500' }}>Refresh:</Text> Get new token if needed{'\n'}
            5. <Text style={{ fontWeight: '500' }}>Reset:</Text> Clear configuration
          </Text>
        </View>
      </ScrollView>
    </View>
  );
};

export default TestSelectedUser;