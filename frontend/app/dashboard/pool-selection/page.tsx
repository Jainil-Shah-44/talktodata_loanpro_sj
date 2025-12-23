'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { 
  Container, 
  Title, 
  Text, 
  Group, 
  Card, 
  Stack, 
  Select, 
  NumberInput, 
  Button, 
  Paper, 
  Table, 
  TextInput,
  Badge,
  Progress,
  SimpleGrid,
  Divider,
  Tabs,
  Modal,
  rem,
  LoadingOverlay
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { 
  IconFilter, 
  IconSearch, 
  IconCheck, 
  IconX, 
  IconArrowsExchange,
  IconFileCheck,
  IconCurrencyRupee,
  IconUsers,
  IconPercentage,
  IconChartBar,
  IconReportAnalytics,
  IconDeviceFloppy
} from '@tabler/icons-react';
import { useDatasets } from '@/hooks/useDatasets';
import { usePoolSelection } from '@/hooks/usePoolSelection';
import { notifications } from '@mantine/notifications';

const formatAmount = (amount: number) => {
  return `₹ ${(amount / 100000).toFixed(2)} lakhs`;
};

const formatPercentage = (value: number, total: number) => {
  if (total === 0) return '0.00%';
  return `${((value / total) * 100).toFixed(2)}%`;
};

export default function PoolSelectionPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const datasetId = searchParams.get('dataset');
  
  const { datasets, loading: datasetsLoading } = useDatasets();
  const {
    filteredRecords,
    selectedRecords,
    filterCriteria,
    updateFilterCriteria,
    applyFilters,
    optimizeSelection,
    saveSelection,
    savedSelections,
    isFiltering,
    isOptimizing,
    isSaving,
    isLoadingSaved,
    totalFilteredAmount,
    totalSelectedAmount,
    filteredCount,
    selectedCount,
  } = usePoolSelection(datasetId);

  // Form states
  const [collectionThreshold, setCollectionThreshold] = useState<number>(60.00);
  const [minDpd, setMinDpd] = useState<number>(200);
  const [maxDpd, setMaxDpd] = useState<number>(900);
  const [stateFilter, setStateFilter] = useState<string | null>(null);
  const [targetAmount, setTargetAmount] = useState<number>(25);
  const [selectionName, setSelectionName] = useState('');
  const [selectionDescription, setSelectionDescription] = useState('');
  
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  const [opened, { open, close }] = useDisclosure(false);

  // Redirect to dataset selection if no dataset is selected
  useEffect(() => {
    if (!datasetId && datasets.length > 0) {
      router.push(`/dashboard/pool-selection?dataset=${datasets[0].id}`);
    }
  }, [datasetId, datasets, router]);

  // Initialize filter values based on query params or defaults
  useEffect(() => {
    if (isFirstLoad && datasetId) {
      setCollectionThreshold(60.00);
      setMinDpd(200);
      setMaxDpd(900);
      setTargetAmount(25);
      
      updateFilterCriteria('collection_12m', '>=', 60.00);
      updateFilterCriteria('dpd', 'between', null, 200, 900);
      
      setIsFirstLoad(false);
    }
  }, [isFirstLoad, datasetId, updateFilterCriteria]);

  const currentDataset = datasets.find(d => d.id === datasetId) || (datasets.length > 0 ? datasets[0] : null);

  const handleApplyFilters = () => {
    updateFilterCriteria('collection_12m', '>=', collectionThreshold);
    updateFilterCriteria('dpd', 'between', null, minDpd, maxDpd);
    
    if (stateFilter) {
      updateFilterCriteria('state', '=', stateFilter);
    } else if (filterCriteria.state) {
      // Remove state filter if it was set before but now it's not
      const newCriteria = { ...filterCriteria };
      delete newCriteria.state;
      // TODO: updateFilterCriteria should handle this case
    }
    
    applyFilters();
  };

  const handleOptimizeSelection = () => {
    if (targetAmount) {
      optimizeSelection(targetAmount * 100000, 'collection_12m');
    }
  };

  const handleSaveSelection = () => {
    if (!selectionName.trim()) {
      notifications.show({
        title: 'Error',
        message: 'Please provide a name for your selection',
        color: 'red',
      });
      return;
    }
    
    saveSelection(selectionName, selectionDescription);
    close();
    
    notifications.show({
      title: 'Success',
      message: 'Selection saved successfully',
      color: 'green',
    });
  };

  // Navigate to summary page with current filters
  const handleViewSummary = () => {
    if (!datasetId) return;
    
    // Encode the current filter criteria for the URL
    const encodedFilters = encodeURIComponent(JSON.stringify(filterCriteria));
    const summaryUrl = `/dashboard/summary?dataset=${datasetId}&filters=${encodedFilters}`;
    
    router.push(summaryUrl);
  };

  // Get unique states for filter dropdown
  const states = [...new Set(filteredRecords.map(record => record.state))].filter(Boolean);

  const targetCompletionPercentage = targetAmount ? Math.min(Math.round((totalSelectedAmount / (targetAmount * 100000)) * 100), 100) : 0;
  
  return (
    <Container fluid>
      <LoadingOverlay visible={datasetsLoading} />
      
      {/* Dataset Info Card */}
      <Card withBorder shadow="sm" mb="md">
        <Group justify="space-between" align="center" mb="md">
          <Stack gap="xs">
            <Title order={3}>Loan Pool Selection</Title>
            <Text size="sm">Create an optimal loan sub-pool based on custom criteria</Text>
          </Stack>
          
          <Select
            placeholder="Select Dataset"
            data={datasets.map(d => ({ value: d.id, label: d.name }))}
            value={datasetId || ''}
            onChange={(value: string | null) => {
              if (value) {
                router.push(`/dashboard/pool-selection?dataset=${value}`);
                setIsFirstLoad(true);
              }
            }}
            style={{ minWidth: '200px' }}
          />
        </Group>
        
        {currentDataset && (
          <Group>
            <Badge color={currentDataset.status === 'validated' ? 'green' : 'blue'}>
              {currentDataset.status === 'validated' ? 'Validated' : 'Pending Validation'}
            </Badge>
            <Text size="sm">{currentDataset.total_records} records</Text>
            <Text size="sm">Uploaded on {new Date(currentDataset.upload_date).toLocaleDateString()}</Text>
          </Group>
        )}
      </Card>

      <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
        {/* Filter Panel */}
        <Card withBorder shadow="sm">
          <Title order={4} mb="md">Selection Criteria</Title>
          
          <Stack gap="md">
            <NumberInput
              label="12-Month Collection Threshold (≥)"
              value={collectionThreshold}
              onChange={(value) => setCollectionThreshold(typeof value === 'number' ? value : 60)}
              min={0}
              step={1}
              prefix="₹ "
              decimalScale={2}
              rightSection={<IconCurrencyRupee size={rem(16)} />}
            />
            
            <Group grow>
              <NumberInput
                label="DPD Range (Min)"
                value={minDpd}
                onChange={(value) => setMinDpd(typeof value === 'number' ? value : 200)}
                min={0}
              />
              <NumberInput
                label="DPD Range (Max)"
                value={maxDpd}
                onChange={(value) => setMaxDpd(typeof value === 'number' ? value : 900)}
                min={minDpd}
              />
            </Group>
            
            <Select
              label="State (Optional)"
              placeholder="All States"
              clearable
              data={states.map(state => ({ value: state, label: state }))}
              value={stateFilter}
              onChange={setStateFilter}
            />
            
            <Divider my="sm" />
            
            <NumberInput
              label="Target Pool Amount (in Lakhs)"
              description="The target amount for your optimized loan pool"
              value={targetAmount}
              onChange={(value) => setTargetAmount(typeof value === 'number' ? value : 25)}
              min={1}
              step={0.01}
              prefix="₹ "
              decimalScale={2}
              rightSection={<IconCurrencyRupee size={rem(16)} />}
            />
            
            <Group grow mt="md">
              <Button 
                leftSection={<IconFilter size="1.2rem" />}
                onClick={handleApplyFilters}
                loading={isFiltering}
              >
                Apply Filters
              </Button>
              
              <Button 
                leftSection={<IconArrowsExchange size="1.2rem" />}
                onClick={handleOptimizeSelection}
                loading={isOptimizing}
                disabled={filteredRecords.length === 0}
                color="green"
              >
                Optimize Selection
              </Button>
            </Group>
          </Stack>
        </Card>

        {/* Results Summary */}
        <Card withBorder shadow="sm">
          <Title order={4} mb="md">Results Summary</Title>
          
          <SimpleGrid cols={2} spacing="md">
            <Paper withBorder p="md" radius="md">
              <Group justify="space-between">
                <Text size="sm" c="dimmed">Filtered Pool</Text>
                <Badge color="blue">{filteredCount} accounts</Badge>
              </Group>
              <Group mt="xs">
                <IconCurrencyRupee size="1.5rem" color="blue" />
                <div>
                  <Text fw={500}>{formatAmount(totalFilteredAmount)}</Text>
                  <Text size="xs" c="dimmed">Total Principal Outstanding</Text>
                </div>
              </Group>
            </Paper>
            
            <Paper withBorder p="md" radius="md">
              <Group justify="space-between">
                <Text size="sm" c="dimmed">Selected Pool</Text>
                <Badge color="green">{selectedCount} accounts</Badge>
              </Group>
              <Group mt="xs">
                <IconCurrencyRupee size="1.5rem" color="green" />
                <div>
                  <Text fw={500}>{formatAmount(totalSelectedAmount)}</Text>
                  <Text size="xs" c="dimmed">Total Principal Outstanding</Text>
                </div>
              </Group>
            </Paper>
          </SimpleGrid>
          
          <Card withBorder mt="md" padding="sm">
            <Text fw={500} mb="xs">Target Completion ({targetCompletionPercentage}%)</Text>
            <Progress value={targetCompletionPercentage} color={targetCompletionPercentage === 100 ? 'green' : 'blue'} />
            <Group mt="xs" justify="space-between">
              <Text size="xs" c="dimmed">Current: {formatAmount(totalSelectedAmount)}</Text>
              <Text size="xs" c="dimmed">Target: {formatAmount((targetAmount || 0) * 100000)}</Text>
            </Group>
          </Card>
          
          <Button 
            fullWidth 
            mt="lg"
            leftSection={<IconDeviceFloppy size="1.2rem" />}
            onClick={open}
            disabled={selectedRecords.length === 0}
          >
            Save Selection
          </Button>
          
          <Button 
            fullWidth 
            mt="md"
            variant="outline"
            leftSection={<IconReportAnalytics size="1.2rem" />}
            onClick={handleViewSummary}
            disabled={filteredRecords.length === 0}
          >
            View Summary with Filters
          </Button>
        </Card>
      </SimpleGrid>

      {/* Results Tabs */}
      <Card withBorder shadow="sm" mt="md">
        <Tabs defaultValue="filtered">
          <Tabs.List>
            <Tabs.Tab 
              value="filtered" 
              leftSection={<IconFilter size="0.8rem" />}
              rightSection={<Badge size="xs" variant="light">{filteredCount}</Badge>}
            >
              Filtered Pool
            </Tabs.Tab>
            <Tabs.Tab 
              value="selected" 
              leftSection={<IconFileCheck size="0.8rem" />}
              rightSection={<Badge size="xs" variant="light">{selectedCount}</Badge>}
            >
              Selected Pool
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Panel value="filtered" pt="md">
            <Paper withBorder p="xs">
              <Text size="sm">Showing {filteredRecords.length} accounts matching your filter criteria</Text>
            </Paper>
            
            <Table striped highlightOnHover withTableBorder mt="md">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Account Number</Table.Th>
                  <Table.Th>Customer Name</Table.Th>
                  <Table.Th>Principal Outstanding</Table.Th>
                  <Table.Th>DPD</Table.Th>
                  <Table.Th>12M Collection</Table.Th>
                  <Table.Th>State</Table.Th>
                  <Table.Th>Product Type</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {filteredRecords.slice(0, 100).map((record) => (
                  <Table.Tr key={record.id}>
                    <Table.Td>{record.account_number}</Table.Td>
                    <Table.Td>{record.customer_name}</Table.Td>
                    <Table.Td>₹ {record.principal_os_amt.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</Table.Td>
                    <Table.Td>{record.dpd}</Table.Td>
                    <Table.Td>₹ {record.collection_12m?.toLocaleString('en-IN', { maximumFractionDigits: 2 }) || '0.00'}</Table.Td>
                    <Table.Td>{record.state}</Table.Td>
                    <Table.Td>{record.product_type}</Table.Td>
                  </Table.Tr>
                ))}
                {filteredRecords.length > 100 && (
                  <Table.Tr>
                    <Table.Td colSpan={7} align="center">
                      <Text size="sm">Showing 100 of {filteredRecords.length} records</Text>
                    </Table.Td>
                  </Table.Tr>
                )}
                {filteredRecords.length === 0 && (
                  <Table.Tr>
                    <Table.Td colSpan={7} align="center">
                      <Text>No records match your filter criteria</Text>
                    </Table.Td>
                  </Table.Tr>
                )}
              </Table.Tbody>
            </Table>
          </Tabs.Panel>

          <Tabs.Panel value="selected" pt="md">
            <Paper withBorder p="xs">
              <Text size="sm">Showing {selectedRecords.length} accounts in your optimized selection</Text>
            </Paper>
            
            <Table striped highlightOnHover withTableBorder mt="md">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Account Number</Table.Th>
                  <Table.Th>Customer Name</Table.Th>
                  <Table.Th>Principal Outstanding</Table.Th>
                  <Table.Th>DPD</Table.Th>
                  <Table.Th>12M Collection</Table.Th>
                  <Table.Th>State</Table.Th>
                  <Table.Th>Product Type</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {selectedRecords.map((record) => (
                  <Table.Tr key={record.id}>
                    <Table.Td>{record.account_number}</Table.Td>
                    <Table.Td>{record.customer_name}</Table.Td>
                    <Table.Td>₹ {record.principal_os_amt.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</Table.Td>
                    <Table.Td>{record.dpd}</Table.Td>
                    <Table.Td>₹ {record.collection_12m?.toLocaleString('en-IN', { maximumFractionDigits: 2 }) || '0.00'}</Table.Td>
                    <Table.Td>{record.state}</Table.Td>
                    <Table.Td>{record.product_type}</Table.Td>
                  </Table.Tr>
                ))}
                {selectedRecords.length === 0 && (
                  <Table.Tr>
                    <Table.Td colSpan={7} align="center">
                      <Text>No records have been selected yet. Click "Optimize Selection" to create your pool.</Text>
                    </Table.Td>
                  </Table.Tr>
                )}
              </Table.Tbody>
            </Table>
          </Tabs.Panel>
        </Tabs>
      </Card>
      
      {/* Save Selection Modal */}
      <Modal opened={opened} onClose={close} title="Save Selection" centered>
        <Stack>
          <TextInput
            label="Selection Name"
            placeholder="Enter a name for this selection"
            value={selectionName}
            onChange={(e) => setSelectionName(e.target.value)}
            required
          />
          
          <TextInput
            label="Description (Optional)"
            placeholder="Enter a description"
            value={selectionDescription}
            onChange={(e) => setSelectionDescription(e.target.value)}
          />
          
          <Group mt="md">
            <Text size="sm">Selected Amount: {formatAmount(totalSelectedAmount)}</Text>
            <Text size="sm">Account Count: {selectedCount}</Text>
          </Group>
          
          <Group justify="right" mt="md">
            <Button variant="default" onClick={close}>Cancel</Button>
            <Button onClick={handleSaveSelection} loading={isSaving}>Save</Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}
