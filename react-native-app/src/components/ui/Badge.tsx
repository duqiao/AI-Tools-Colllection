import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '@/theme';

interface BadgeProps {
  text: string;
  variant?: 'default' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ text, variant = 'default', size = 'sm' }) => {
  const theme = useTheme();

  const getBadgeStyle = () => {
    const baseStyle = {
      borderRadius: theme.borderRadius.round,
      alignItems: 'center' as const,
      justifyContent: 'center' as const,
      paddingHorizontal: theme.spacing.xs,
      paddingVertical: theme.spacing.xs / 2,
    };

    const sizeStyles = {
      sm: {
        paddingHorizontal: theme.spacing.xs,
        paddingVertical: 2,
        minWidth: 40,
      },
      md: {
        paddingHorizontal: theme.spacing.sm,
        paddingVertical: theme.spacing.xs,
        minWidth: 48,
      },
    };

    const variantStyles = {
      default: {
        backgroundColor: theme.colors.primary,
      },
      secondary: {
        backgroundColor: theme.colors.backgroundSecondary,
        borderWidth: 1,
        borderColor: theme.colors.border,
      },
      success: {
        backgroundColor: theme.colors.success,
      },
      warning: {
        backgroundColor: theme.colors.warning,
      },
      error: {
        backgroundColor: theme.colors.error,
      },
    };

    return {
      ...baseStyle,
      ...sizeStyles[size],
      ...variantStyles[variant],
    };
  };

  const getTextStyle = () => {
    const baseStyle = {
      fontWeight: '600' as const,
    };

    const sizeStyles = {
      sm: { fontSize: 10 },
      md: { fontSize: 12 },
    };

    const variantStyles = {
      default: { color: 'white' },
      secondary: { color: theme.colors.text.secondary },
      success: { color: 'white' },
      warning: { color: 'white' },
      error: { color: 'white' },
    };

    return {
      ...baseStyle,
      ...sizeStyles[size],
      ...variantStyles[variant],
    };
  };

  return (
    <View style={[styles.badge, getBadgeStyle()]}>
      <Text style={[styles.text, getTextStyle()]}>{text}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
  },
  text: {
    textAlign: 'center',
  },
});