import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Provider } from 'react-redux';
import { NavigationContainer } from '@react-navigation/native';
import { store } from '@/store';
import { SessionGuard } from '@/components/SessionGuard';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SessionProvider } from '@/contexts/SessionContext';

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <Provider store={store}>
        <SessionProvider>
          <SafeAreaProvider>
            <NavigationContainer>
              <StatusBar style="auto" />
              <SessionGuard />
            </NavigationContainer>
          </SafeAreaProvider>
        </SessionProvider>
      </Provider>
    </GestureHandlerRootView>
  );
}