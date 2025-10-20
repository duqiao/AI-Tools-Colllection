import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '@/theme';

interface QuotaDisplayProps {
  used: number;
  limit: number;
  resetDate?: string;
}

export const QuotaDisplay: React.FC<QuotaDisplayProps> = ({
  used,
  limit,
  resetDate,
}) => {
  const theme = useTheme();
  
  const percentage = limit > 0 ? (used / limit) * 100 : 0;
  const remaining = Math.max(0, limit - used);
  const isNearLimit = percentage >= 80;

  const getResetDateText = () => {
    if (!resetDate) return '每日重置';
    const date = new Date(resetDate);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === tomorrow.toDateString()) {
      return '明天重置';
    }
    
    return date.toLocaleDateString('zh-CN');
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.backgroundSecondary }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.colors.text.primary }]}>
          今日配额
        </Text>
        <View style={styles.countContainer}>
          <Text style={[
            styles.count, 
            { color: isNearLimit ? theme.colors.error : theme.colors.text.primary }
          ]}>
            {remaining}
          </Text>
          <Text style={[styles.total, { color: theme.colors.text.secondary }]}>
            /{limit}
          </Text>
        </View>
      </View>
      
      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View 
            style={[
              styles.progressFill,
              { 
                width: `${Math.min(100, percentage)}%`,
                backgroundColor: isNearLimit ? theme.colors.error : theme.colors.primary
              }
            ]} 
          />
        </View>
        <Text style={[styles.percentage, { color: theme.colors.text.secondary }]}>
          {Math.round(percentage)}%
        </Text>
      </View>
      
      <Text style={[styles.resetText, { color: theme.colors.text.tertiary }]}>
        {getResetDateText()}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    margin: 20,
    padding: 16,
    borderRadius: 12,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
  },
  countContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  count: {
    fontSize: 20,
    fontWeight: '700',
  },
  total: {
    fontSize: 16,
    fontWeight: '400',
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  progressBar: {
    flex: 1,
    height: 8,
    backgroundColor: '#E5E7EB',
    borderRadius: 4,
    marginRight: 12,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  percentage: {
    fontSize: 12,
    fontWeight: '600',
    minWidth: 30,
    textAlign: 'right',
  },
  resetText: {
    fontSize: 12,
    fontWeight: '400',
    textAlign: 'center',
  },
});