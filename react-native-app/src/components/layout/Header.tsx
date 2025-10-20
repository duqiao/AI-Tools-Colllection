import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from '@expo/vector-icons/MaterialIcons';
import { useTheme } from '@/theme';

interface HeaderProps {
  title?: string;
  showBackButton?: boolean;
  onBackPress?: () => void;
  rightAction?: {
    icon: keyof typeof Icon.glyphMap;
    onPress: () => void;
  };
}

export const Header: React.FC<HeaderProps> = ({
  title,
  showBackButton = false,
  onBackPress,
  rightAction,
}) => {
  const theme = useTheme();

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <View style={styles.content}>
        {showBackButton && (
          <TouchableOpacity
            style={[styles.backButton, { backgroundColor: theme.colors.backgroundSecondary }]}
            onPress={onBackPress}
          >
            <Icon name="arrow-back" size={24} color={theme.colors.text.primary} />
          </TouchableOpacity>
        )}

        <View style={styles.titleContainer}>
          {title && (
            <Text style={[styles.title, { color: theme.colors.text.primary }]}>
              {title}
            </Text>
          )}
        </View>

        <View style={styles.rightContainer}>
          {rightAction && (
            <TouchableOpacity
              style={[styles.rightButton, { backgroundColor: theme.colors.backgroundSecondary }]}
              onPress={rightAction.onPress}
            >
              <Icon name={rightAction.icon} size={24} color={theme.colors.text.primary} />
            </TouchableOpacity>
          )}
          
          {!showBackButton && !rightAction && (
            <TouchableOpacity
              style={[styles.menuButton, { backgroundColor: theme.colors.backgroundSecondary }]}
              onPress={() => console.log('Menu pressed')}
            >
              <Icon name="menu" size={24} color={theme.colors.text.primary} />
            </TouchableOpacity>
          )}
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
    minHeight: 56,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  titleContainer: {
    flex: 1,
    alignItems: 'center',
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
  },
  rightContainer: {
    width: 40,
    alignItems: 'flex-end',
  },
  rightButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
});