import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '@/theme';

interface InfoBannerProps {
  icon: string;
  message: string;
  type?: 'info' | 'warning' | 'error' | 'success';
}

export const InfoBanner: React.FC<InfoBannerProps> = ({
  icon,
  message,
  type = 'info',
}) => {
  const theme = useTheme();

  const getBannerStyle = () => {
    const typeStyles = {
      info: {
        backgroundColor: theme.colors.backgroundSecondary,
        borderColor: theme.colors.info,
      },
      warning: {
        backgroundColor: '#FEF3C7',
        borderColor: theme.colors.warning,
      },
      error: {
        backgroundColor: '#FEE2E2',
        borderColor: theme.colors.error,
      },
      success: {
        backgroundColor: '#D1FAE5',
        borderColor: theme.colors.success,
      },
    };

    return {
      ...typeStyles[type],
    };
  };

  return (
    <View style={[styles.container, getBannerStyle()]}>
      <Text style={styles.icon}>{icon}</Text>
      <Text style={[styles.message, { color: theme.colors.text.secondary }]}>
        {message}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 20,
    marginBottom: 16,
    padding: 12,
    borderRadius: 8,
    borderLeftWidth: 4,
  },
  icon: {
    fontSize: 16,
    marginRight: 8,
  },
  message: {
    flex: 1,
    fontSize: 14,
    fontWeight: '400',
  },
});