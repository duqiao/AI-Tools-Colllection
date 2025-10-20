import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Platform } from 'react-native';
import Icon from '@expo/vector-icons/MaterialIcons';
import { useTheme } from '@/theme';

interface FeatureCardProps {
  icon: keyof typeof Icon.glyphMap;
  title: string;
  description: string;
  badge?: string;
  iconBg?: string;
  onPress: () => void;
}

export const FeatureCard: React.FC<FeatureCardProps> = ({
  icon,
  title,
  description,
  badge,
  iconBg,
  onPress,
}) => {
  const theme = useTheme();

  return (
    <TouchableOpacity
      style={[styles.card, { backgroundColor: theme.colors.background }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={[styles.iconContainer, { backgroundColor: iconBg || theme.colors.primary }]}>
        <Icon name={icon} size={24} color="white" />
      </View>
      
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={[styles.title, { color: theme.colors.text.primary }]}>
            {title}
          </Text>
          {badge && (
            <View style={[styles.badge, { backgroundColor: theme.colors.success }]}>
              <Text style={styles.badgeText}>{badge}</Text>
            </View>
          )}
        </View>
        
        <Text style={[styles.description, { color: theme.colors.text.secondary }]}>
          {description}
        </Text>
      </View>
      
      <Icon name="chevron-right" size={24} color={theme.colors.text.tertiary} />
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginBottom: 12,
    borderRadius: 12,
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: {
          width: 0,
          height: 1,
        },
        shadowOpacity: 0.05,
        shadowRadius: 2,
      },
      android: {
        elevation: 1,
      },
    }),
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  content: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    marginLeft: 8,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '600',
    color: 'white',
  },
  description: {
    fontSize: 14,
    fontWeight: '400',
    lineHeight: 20,
  },
});