import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from '@expo/vector-icons/MaterialIcons';
import { useTheme } from '@/theme';

interface CTAButtonProps {
  title: string;
  subtitle: string;
  icon: string;
  onPress: () => void;
}

export const CTAButton: React.FC<CTAButtonProps> = ({
  title,
  subtitle,
  icon,
  onPress,
}) => {
  const theme = useTheme();

  return (
    <TouchableOpacity
      style={[styles.container, { backgroundColor: theme.colors.primary }]}
      onPress={onPress}
      activeOpacity={0.8}
    >
      <View style={styles.content}>
        <View style={styles.textContainer}>
          <Text style={styles.title}>{title}</Text>
        </View>
        <View style={[styles.subtitleContainer, { backgroundColor: 'rgba(255,255,255,0.2)' }]}>
          <Text style={styles.subtitle}>{subtitle}</Text>
        </View>
      </View>
      <View style={[styles.iconContainer, { backgroundColor: 'rgba(255,255,255,0.2)' }]}>
        <Text style={styles.iconText}>{icon}</Text>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderRadius: 12,
    marginHorizontal: 20,
  },
  content: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  textContainer: {
    flex: 1,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: 'white',
  },
  subtitleContainer: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginLeft: 12,
  },
  subtitle: {
    fontSize: 14,
    fontWeight: '600',
    color: 'white',
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 12,
  },
  iconText: {
    fontSize: 20,
  },
});