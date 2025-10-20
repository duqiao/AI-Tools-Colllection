import React from 'react';
import { View, StyleSheet } from 'react-native';
import { useTheme } from '@/theme';

interface LoadingSpinnerProps {
  size?: 'small' | 'large';
  color?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'large', 
  color 
}) => {
  const theme = useTheme();

  return (
    <View style={styles.container}>
      <View style={styles.spinner}>
        {/* Custom spinner implementation */}
        <View 
          style={[
            styles.spinnerCircle,
            {
              width: size === 'small' ? 20 : 40,
              height: size === 'small' ? 20 : 40,
              borderTopColor: color || theme.colors.primary,
            }
          ]} 
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  spinner: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  spinnerCircle: {
    borderWidth: 2,
    borderRadius: 9999,
    borderColor: '#E5E7EB',
    borderStyle: 'solid',
  },
});