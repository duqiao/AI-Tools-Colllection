import React, { useEffect } from 'react';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from '@expo/vector-icons/MaterialIcons';
import { useTheme } from '@/theme';
import { HomeScreen } from '@/screens/HomeScreen';
import { UploadScreen } from '@/screens/UploadScreen';
import { ResultScreen } from '@/screens/ResultScreen';
import { HistoryScreen } from '@/screens/HistoryScreen';
import { ProfileScreen } from '@/screens/ProfileScreen';
import { DebugGuestLogin } from '@/screens/DebugGuestLogin';
import { setupMySelectedUser } from '@/services/setupSelectedUser';

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

const TabNavigator = () => {
  const theme = useTheme();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: keyof typeof Icon.glyphMap;

          switch (route.name) {
            case 'Home':
              iconName = 'home';
              break;
            case 'Upload':
              iconName = 'cloud-upload';
              break;
            case 'History':
              iconName = 'history';
              break;
            case 'Profile':
              iconName = 'person';
              break;
            default:
              iconName = 'help';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.text.secondary,
        headerShown: false,
        tabBarStyle: {
          backgroundColor: theme.colors.background,
          borderTopColor: theme.colors.border,
        },
      })}
    >
      <Tab.Screen 
        name="Home" 
        component={HomeScreen}
        options={{ title: '首页' }}
      />
      <Tab.Screen 
        name="Upload" 
        component={UploadScreen}
        options={{ title: '上传' }}
      />
      <Tab.Screen 
        name="History" 
        component={HistoryScreen}
        options={{ title: '历史' }}
      />
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen}
        options={{ title: '我的' }}
      />
    </Tab.Navigator>
  );
};

export const AppNavigator = () => {
  // Setup selected user when navigator initializes
  useEffect(() => {
    const initializeUser = async () => {
      try {
        await setupMySelectedUser();
      } catch (error) {
        console.error('Failed to setup selected user:', error);
      }
    };
    
    initializeUser();
  }, []);

  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
      }}
    >
      <Stack.Screen name="MainTabs" component={TabNavigator} />
      <Stack.Screen 
        name="Result" 
        component={ResultScreen}
        options={{
          headerShown: true,
          title: '翻译结果',
          presentation: 'modal',
        }}
        initialParams={{ taskId: '' }}
      />
      <Stack.Screen 
        name="Debug" 
        component={DebugGuestLogin}
        options={{
          headerShown: true,
          title: '游客登录调试',
        }}
      />
    </Stack.Navigator>
  );
};