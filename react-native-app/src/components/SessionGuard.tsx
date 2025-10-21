import React, { useEffect } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { useSession } from '@/contexts/SessionContext';
import { AppNavigator } from '@/navigation/AppNavigator';
import { AuthNavigator } from '@/navigation/AuthNavigator';

interface SessionGuardProps {
  children?: React.ReactNode;
}

export const SessionGuard: React.FC<SessionGuardProps> = () => {
  const { state, refreshSession } = useSession();

  useEffect(() => {
    // Set up session monitoring
    const sessionCheckInterval = setInterval(async () => {
      await refreshSession();
    }, 10 * 60 * 1000); // Check every 10 minutes

    return () => clearInterval(sessionCheckInterval);
  }, [refreshSession]);

  // Show loading indicator while checking session
  if (state.isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  // Show auth screens if not authenticated
  if (!state.isAuthenticated) {
    return <AuthNavigator />;
  }

  // Show main app if authenticated
  return <AppNavigator />;
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
});

export default SessionGuard;