import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { useTheme } from '@/theme';

export const StatusBarComponent: React.FC = () => {
  const theme = useTheme();

  return (
    <StatusBar 
      style="auto" 
    />
  );
};

export { StatusBarComponent as StatusBar };