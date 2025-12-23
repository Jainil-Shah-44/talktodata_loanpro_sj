'use client';

import { useState, useEffect } from 'react';
import { Title, SimpleGrid, Card, Text, Group, Button, Center, Stack, Container, Paper, Alert, Badge, Select, Table, Loader, ScrollArea, Tabs } from '@mantine/core';
import { IconDatabase, IconInfoCircle, IconChartBar, IconRefresh, IconSettings } from '@tabler/icons-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useDatasets } from '@/hooks/useDatasets';
import { useUserStore } from '@/src/store/userStore';
import { useSummaries, SummaryTable } from '@/hooks/useSummaries';

// Format number with commas and optional decimal places
const formatNumber = (num: number, decimals = 2) => {
  if (num === null || num === undefined) return '-';
  return num.toLocaleString('en-IN', { 
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

// Format currency in lakhs/crores for Indian format
const formatCurrency = (num: number) => {
  if (num === null || num === undefined) return '-';
  if (num === 0) return '0.00';
  
  console.log('Formatting currency value:', num, typeof num);
  
  // Convert to appropriate scale based on value
  if (num >= 10000000) { // 1 crore = 10,000,000
    return `${(num / 10000000).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} Cr`;
  } else if (num >= 100000) { // 1 lakh = 100,000
    return `${(num / 100000).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} L`;
  } else if (num >= 1000) { // For thousands
    return `${(num / 1000).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}K`;
  } else {
    return num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
};

// Format percentage
const formatPercent = (num: number) => {
  if (num === null || num === undefined) return '-';
  return `${num.toFixed(2)}%`;
};

export default function SummaryGenerationPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const datasetId = searchParams.get('dataset');
  const { datasets, loading: datasetsLoading, error: datasetsError } = useDatasets();
  const { summaryData, loading: summaryLoading, error: summaryError, fetchSummaryData } = useSummaries(datasetId);
  const user = useUserStore((state) => state.user);
  const isAuthenticated = useUserStore((state) => state.isAuthenticated);
  
  // Get the current dataset
  const currentDataset = datasets.find(d => d.id === datasetId) || (datasets.length > 0 ? datasets[0] : null);

  // Define the type for collection values
  type CollectionValues = {
    '3mCol': number;
    '6mCol': number;
    '12mCol': number;
    'totalCollection': number;
  };

  // No hardcoded values - we'll use real data from the backend
  
  useEffect(() => {
    // Redirect to datasets page if no dataset is selected
    if (!datasetId && datasets.length > 0) {
      router.push(`/dashboard/summary?dataset=${datasets[0].id}`);
    }
    
    // Debug logging for summary data
    console.log('Summary data:', summaryData);
    
    // Use the real data from the backend without modification
    if (summaryData?.writeOffPool) {
      console.log('Write-Off Pool data from backend:', JSON.stringify(summaryData.writeOffPool, null, 2));
      
      // Detailed debugging of collection values in each row
      console.log('DETAILED COLLECTION VALUES DEBUGGING:');
      summaryData.writeOffPool.rows.forEach((row, index) => {
        console.log(`Row ${index} - ${row.bucket}:`, {
          '3mCol': row['3mCol'],
          '3mCol_type': typeof row['3mCol'],
          '6mCol': row['6mCol'],
          '6mCol_type': typeof row['6mCol'],
          '12mCol': row['12mCol'],
          '12mCol_type': typeof row['12mCol'],
          'totalCollection': row['totalCollection'],
          'totalCollection_type': typeof row['totalCollection']
        });
      });
    }
  }, [datasetId, datasets, router, summaryData]);

  if (datasetsLoading || summaryLoading) {
    return (
      <Container size="xl" py="md">
        <Center h={400}>
          <Loader size="lg" />
        </Center>
      </Container>
    );
  }

  if (!isAuthenticated || !user) {
    // Redirect to login if not authenticated
    router.push('/login');
    return null;
  }
  
  // Render a summary table
  const renderSummaryTable = (table: SummaryTable) => {
    console.log('Rendering summary table:', table.title);
    console.log('Table columns:', table.columns);
    console.log('Table rows:', table.rows);
    
    // Debug the first row's collection values
    if (table.rows.length > 0) {
      const firstRow = table.rows[0];
      console.log('First row values:', firstRow);
      console.log('Collection values in first row:', {
        '3mCol': firstRow['3mCol'],
        '6mCol': firstRow['6mCol'],
        '12mCol': firstRow['12mCol'],
        'totalCollection': firstRow['totalCollection']
      });
    }
    
    // Add debug log for all rows before rendering
    if (table.id === 'writeOffPool') {
      console.log('DEBUG: All Write-Off Pool rows about to render:', JSON.stringify(table.rows, null, 2));
    }
    
    return (
      <Paper withBorder p="md" radius="md" mb="lg">
        <Group justify="space-between" mb="md">
          <Title order={4}>{table.title}</Title>
        </Group>
        
        {table.description && (
          <Text size="sm" c="dimmed" mb="md">{table.description}</Text>
        )}
        
        <ScrollArea>
          <Table striped highlightOnHover withTableBorder withColumnBorders>
            <Table.Thead>
              <Table.Tr>
                {table.columns.map((column) => (
                  <Table.Th key={column.key}>{column.title}</Table.Th>
                ))}
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {table.rows.map((row, rowIndex) => (
                <Table.Tr key={rowIndex} bg={row.bucket === 'Grand Total' ? 'var(--mantine-color-blue-0)' : undefined}>
                  {table.columns.map((column, colIndex) => (
                    <Table.Td key={`${rowIndex}-${colIndex}`}>
                      {(() => {
                        // Debug the actual values being displayed
                        if (['3mCol', '6mCol', '12mCol', 'totalCollection'].includes(column.key)) {
                          const rawValue = row[column.key];
                          console.log(`${row.bucket} - ${column.key}: ${rawValue} (${typeof rawValue})`);
                        }
                        
                        // Format the values for display
                        if (column.key === 'percentOfPos') {
                          return formatPercent(row[column.key] as number);
                        } else if (column.key === 'pos') {
                          return formatCurrency(row[column.key] as number);
                        } else if (['3mCol', '6mCol', '12mCol', 'totalCollection'].includes(column.key)) {
                        // For collection columns, ensure we're dealing with numbers
                        const rawValue = row[column.key];
                        console.log(`Rendering ${row.bucket} ${column.key} with value:`, rawValue, typeof rawValue);
                        
                        // Handle zero, null, or undefined values
                        if (rawValue === 0 || rawValue === '0' || rawValue === null || rawValue === undefined) {
                          return '0.00';
                        }
                        
                        // Force conversion to number and use formatCurrency
                        const numValue = parseFloat(rawValue);
                        console.log(`After conversion: ${numValue} (${typeof numValue})`);
                        
                        // For all non-zero values, use the formatCurrency function
                        return formatCurrency(numValue);
                        } else if (typeof row[column.key] === 'number') {
                          return formatNumber(row[column.key] as number);
                        } else {
                          return row[column.key]?.toString() || '-';
                        }
                      })()}
                    </Table.Td>
                  ))}
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </ScrollArea>
      </Paper>
    );
  };

  return (
    <Container size="xl" py="md">
      <Group justify="space-between" mb="lg">
        <Title order={2}>Summary Generation</Title>
        <Group>
          <Button 
            leftSection={<IconRefresh size="1rem" />}
            variant="light"
            onClick={() => fetchSummaryData()}
          >
            Refresh Data
          </Button>
          <Button 
            leftSection={<IconSettings size="1rem" />}
            variant="outline"
          >
            Configure Buckets
          </Button>
        </Group>
      </Group>

      {(datasetsError || summaryError) && (
        <Alert icon={<IconInfoCircle size="1rem" />} title="API Error" color="red" mb="md">
          {datasetsError || summaryError}
        </Alert>
      )}
      
      <Card withBorder p="md" radius="md" mb="lg">
        <Group justify="space-between">
          <Group>
            <IconDatabase size="1.5rem" stroke={1.5} />
            <div>
              <Text fw={500} size="lg">
                {currentDataset ? currentDataset.name : 'No Dataset Selected'}
              </Text>
              {currentDataset?.description && (
                <Text size="xs" c="dimmed">{currentDataset.description}</Text>
              )}
            </div>
          </Group>
          
          <Group>
            {currentDataset && (
              <Badge size="lg" color={currentDataset.status === 'validated' ? 'green' : 'blue'}>
                {currentDataset.status === 'validated' ? 'Validated' : 'Pending Validation'}
              </Badge>
            )}
            
            <Select
              placeholder="Change Dataset"
              data={datasets.map(d => ({ value: d.id, label: d.name }))}
              value={currentDataset?.id}
              onChange={(value) => {
                if (value) {
                  router.push(`/dashboard/summary?dataset=${value}`);
                }
              }}
              w={220}
            />
          </Group>
        </Group>
      </Card>

      {summaryLoading ? (
        <Center h={200}>
          <Loader size="lg" />
        </Center>
      ) : !summaryData ? (
        <Paper withBorder p="lg" mb="lg">
          <Center py="xl">
            <Stack align="center" gap="md">
              <IconChartBar size="3rem" stroke={1.5} color="var(--mantine-color-blue-6)" />
              <Title order={3}>No Summary Data Available</Title>
              <Text c="dimmed" ta="center" maw={500}>
                {summaryError ? 
                  "The summary API endpoint returned a 404 error. This likely means the summary generation functionality needs to be implemented on the backend." :
                  "There is no summary data available for this dataset yet. Click the button below to generate summaries."}
              </Text>
              {!summaryError && (
                <Button mt="md" onClick={() => fetchSummaryData()}>
                  Generate Summaries
                </Button>
              )}
            </Stack>
          </Center>
        </Paper>
      ) : (
        <Tabs defaultValue="writeOffPool">
          <Tabs.List mb="md">
            <Tabs.Tab value="writeOffPool" leftSection={<IconChartBar size="0.8rem" />}>
              Write-Off Pool
            </Tabs.Tab>
            <Tabs.Tab value="dpdSummary" leftSection={<IconChartBar size="0.8rem" />}>
              DPD Summary
            </Tabs.Tab>
            {/* Additional tabs can be added here as more summaries are implemented */}
          </Tabs.List>

          <Tabs.Panel value="writeOffPool">
            {summaryData.writeOffPool && renderSummaryTable(summaryData.writeOffPool)}
          </Tabs.Panel>

          <Tabs.Panel value="dpdSummary">
            {summaryData.dpdSummary && renderSummaryTable(summaryData.dpdSummary)}
          </Tabs.Panel>
        </Tabs>
      )}
    </Container>
  );
}
