import { Paper, Text, Group, Box } from '@mantine/core';

interface FilterResultsSummaryProps {
  totalPoolValue: number;
  filteredRecordCount: number;
  targetPoolLimit: number;
  selectedSubPoolCount: number;
  selectedSubPoolValue: number;
}

export function FilterResultsSummary({
  totalPoolValue,
  filteredRecordCount,
  targetPoolLimit,
  selectedSubPoolCount,
  selectedSubPoolValue
}: FilterResultsSummaryProps) {
  
  // Format currency for Indian format (lakhs/crores)
  const formatCurrency = (num: number) => {
    if (num >= 10000000) { // 1 crore = 10,000,000
      return `₹${(num / 10000000).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} Cr`;
    } else if (num >= 100000) { // 1 lakh = 100,000
      return `₹${(num / 100000).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} L`;
    } else {
      return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
  };
  
  return (
    <Paper withBorder p="md" radius="md" mb="lg">
      <Box mb="xs">
        <Text fw={700} size="lg">🗂️ Filter Result Summary:</Text>
      </Box>
      
      <Group gap="xl" style={{ borderTop: '1px dashed #e0e0e0', paddingTop: '10px' }}>
        <Box>
          <Text size="sm">• Total Pool Value:</Text>
          <Text fw={600}>{formatCurrency(totalPoolValue)}</Text>
        </Box>
        
        <Box>
          <Text size="sm">• Filters Matched:</Text>
          <Text fw={600}>{filteredRecordCount} records</Text>
        </Box>
        
        <Box>
          <Text size="sm">• 🎯 Target Pool Limit:</Text>
          <Text fw={600}>{formatCurrency(targetPoolLimit)}</Text>
        </Box>
        
        <Box>
          <Text size="sm">• ✅ Selected Sub-Pool:</Text>
          <Text fw={600}>{selectedSubPoolCount} records</Text>
        </Box>
        
        <Box>
          <Text size="sm">• 💰 Sub-Pool Value:</Text>
          <Text fw={600}>{formatCurrency(selectedSubPoolValue)}</Text>
        </Box>
      </Group>
    </Paper>
  );
}
