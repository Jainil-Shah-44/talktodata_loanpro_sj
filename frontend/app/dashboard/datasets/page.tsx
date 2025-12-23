'use client';

import { useState, useMemo } from 'react';
import { 
  Container, 
  Title, 
  Text, 
  Button, 
  Group, 
  Table, 
  Badge, 
  ActionIcon, 
  TextInput,
  Menu,
  Select,
  Pagination,
  Card,
  Tooltip,
  Loader,
  Alert,
  Modal
} from '@mantine/core';
import { 
  IconSearch, 
  IconUpload, 
  IconFilter, 
  IconSortAscending, 
  IconSortDescending, 
  IconEye, 
  IconCheck, 
  IconChartBar,
  IconTrash,
  IconDotsVertical,
  IconAlertCircle,
  IconInfoCircle,
  IconDatabase,
  IconPencil
} from '@tabler/icons-react';
import { useRouter } from 'next/navigation';
import { useDatasets } from '@/hooks/useDatasets';
import { useDisclosure } from '@mantine/hooks';
import { Dataset } from '@/src/types';
import { formatFileSize, formatDate } from '@/src/utils/formatters';
import { notifications } from '@mantine/notifications';
import { datasetService } from '@/src/api/services';
import UpdateFileTypeModal from '@/components/UpdateFileTypeModal';

export default function DatasetSelectionPage() {
  const router = useRouter();
  const { datasets, loading, error } = useDatasets();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<string>('upload_date');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [activePage, setActivePage] = useState(1);
  const [opened, { open, close }] = useDisclosure(false);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);

  const [showFileTypeModal, setShowFileTypeModal] = useState(false);
  const [updatingDataSetId, setUpdatingDatasetId] = useState("");
  const [currentDatasetFileType,setCurrentDsFileType] = useState("");

  const handleUpdateFileType = (dataset: Dataset) => {
    // Navigate to the loan records listing page for this dataset
    //router.push(`/dashboard/records?dataset=${dataset.id}`);
    setUpdatingDatasetId(dataset.id);
    setCurrentDsFileType(dataset.file_type??"");
    setShowFileTypeModal(true);
  };
  
  const itemsPerPage = 10;

  // Filter and sort datasets
  const filteredDatasets = useMemo(() => {
    let result = [...datasets];
    
    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(dataset => 
        dataset.name.toLowerCase().includes(query) || 
        dataset.description?.toLowerCase().includes(query)
      );
    }
    
    // Apply status filter
    if (statusFilter !== 'all') {
      result = result.filter(dataset => dataset.status === statusFilter);
    }
    
    // Apply sorting
    result.sort((a, b) => {
      let comparison = 0;
      
      switch (sortField) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'total_records':
          comparison = (a.total_records || 0) - (b.total_records || 0);
          break;
        case 'upload_date':
          comparison = new Date(a.upload_date).getTime() - new Date(b.upload_date).getTime();
          break;
        case 'file_size':
          comparison = (a.file_size ?? 0) - (b.file_size ?? 0);
          break;
        default:
          comparison = 0;
      }
      
      return sortDirection === 'asc' ? comparison : -comparison;
    });
    
    return result;
  }, [datasets, searchQuery, statusFilter, sortField, sortDirection]);
  
  // Paginate datasets
  const paginatedDatasets = useMemo(() => {
    const startIndex = (activePage - 1) * itemsPerPage;
    return filteredDatasets.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredDatasets, activePage]);
  
  const totalPages = Math.ceil(filteredDatasets.length / itemsPerPage);
  
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };
  
  const getSortIcon = (field: string) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <IconSortAscending size="1rem" /> : <IconSortDescending size="1rem" />;
  };
  
  const handleViewDashboard = (dataset: Dataset) => {
    // In a real app, you would set the selected dataset in a store
    // and then navigate to the dashboard
    router.push(`/dashboard?dataset=${dataset.id}`);
  };
  
  const handleViewRecords = (dataset: Dataset) => {
    // Navigate to the loan records listing page for this dataset
    router.push(`/dashboard/records?dataset=${dataset.id}`);
  };
  
  const handleValidate = (dataset: Dataset) => {
    // In a real app, you would call the validation API
    console.log(`Validating dataset: ${dataset.id}`);
    // For now, just navigate to the validation dashboard
    router.push(`/dashboard/validation?dataset=${dataset.id}`);
  };
  
  const handleViewValidationErrors = (dataset: Dataset) => {
    // Navigate to the loan records listing with validation error filter
    router.push(`/dashboard/records?dataset=${dataset.id}&filter=validation_errors`);
  };
  
  const handleGenerateSummary = (dataset: Dataset) => {
    // In a real app, you would navigate to the summary generation page
    router.push(`/dashboard/summary?dataset=${dataset.id}`);
  };
  
  const handleDeleteClick = (dataset: Dataset) => {
    setSelectedDataset(dataset);
    open();
  };
  
  const handleDeleteConfirm = async () => {
    if (!selectedDataset) return;
    
    try {
      // Call the API to delete the dataset
      await datasetService.deleteDataset(selectedDataset.id);
      
      // Show success notification
      notifications.show({
        title: 'Success',
        message: `Dataset "${selectedDataset.name}" has been deleted`,
        color: 'green'
      });
      
      // Close the modal
      close();
      
      // Refresh the datasets list
      window.location.reload();
    } catch (error) {
      console.error('Error deleting dataset:', error);
      
      // Show error notification
      notifications.show({
        title: 'Error',
        message: 'Failed to delete dataset. Please try again.',
        color: 'red'
      });
    }
  };
  
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'validated':
        return <Badge color="green">Validated</Badge>;
      case 'validation_failed':
        return <Badge color="red">Validation Failed</Badge>;
      case 'validating':
        return <Badge color="yellow">Validating</Badge>;
      case 'uploaded':
        return <Badge color="blue">Uploaded</Badge>;
      default:
        return <Badge color="gray">Unknown</Badge>;
    }
  };

  if (loading) {
    return (
      <Container size="xl" py="md">
        <Group justify="center" h={400}>
          <Loader size="lg" />
        </Group>
      </Container>
    );
  }

  return (
    <Container size="xl" py="md">
      <Group justify="space-between" mb="lg">
        <Title order={2}>Dataset Selection</Title>
        <Button 
          leftSection={<IconUpload size="1rem" />}
          onClick={() => router.push('/dashboard/upload')}
        >
          Upload New Dataset
        </Button>
      </Group>
      
      {error && (
        <Alert icon={<IconInfoCircle size="1rem" />} title="Connection Error" color="yellow" mb="md">
          {error}. Using mock data for demonstration.
        </Alert>
      )}
      
      <Card withBorder p="md" radius="md" mb="lg">
        <Group mb="md">
          <TextInput
            placeholder="Search datasets..."
            leftSection={<IconSearch size="1rem" />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.currentTarget.value)}
            style={{ flex: 1 }}
          />
          
          <Select
            placeholder="Filter by status"
            leftSection={<IconFilter size="1rem" />}
            data={[
              { value: 'all', label: 'All Statuses' },
              { value: 'uploaded', label: 'Uploaded' },
              { value: 'validating', label: 'Validating' },
              { value: 'validated', label: 'Validated' },
              { value: 'validation_failed', label: 'Validation Failed' }
            ]}
            value={statusFilter}
            onChange={(value) => setStatusFilter(value || 'all')}
            w={200}
          />
        </Group>
        
        <Table striped highlightOnHover withTableBorder>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>
                <Group gap="xs" onClick={() => handleSort('name')} style={{ cursor: 'pointer' }}>
                  <Text>Name</Text>
                  {getSortIcon('name')}
                </Group>
              </Table.Th>
              <Table.Th>
                <Group gap="xs" onClick={() => handleSort('total_records')} style={{ cursor: 'pointer' }}>
                  <Text>Records</Text>
                  {getSortIcon('total_records')}
                </Group>
              </Table.Th>
              <Table.Th>
                <Group gap="xs" onClick={() => handleSort('upload_date')} style={{ cursor: 'pointer' }}>
                  <Text>Upload Date</Text>
                  {getSortIcon('upload_date')}
                </Group>
              </Table.Th>
              <Table.Th>
                <Group gap="xs" onClick={() => handleSort('file_size')} style={{ cursor: 'pointer' }}>
                  <Text>File Size</Text>
                  {getSortIcon('file_size')}
                </Group>
              </Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {paginatedDatasets.length === 0 ? (
              <Table.Tr>
                <Table.Td colSpan={6}>
                  <Text ta="center" py="lg" c="dimmed">
                    No datasets found. Upload a new dataset to get started.
                  </Text>
                </Table.Td>
              </Table.Tr>
            ) : (
              paginatedDatasets.map((dataset) => (
                <Table.Tr key={dataset.id}>
                  <Table.Td>
                    <Text fw={500}>{dataset.name}</Text>
                    {dataset.description && (
                      <Text size="xs" c="dimmed">{dataset.description}</Text>
                    )}
                  </Table.Td>
                  <Table.Td>{dataset.total_records?.toLocaleString() || 'N/A'}</Table.Td>
                  <Table.Td>{formatDate(dataset.upload_date)}</Table.Td>
                  <Table.Td>{formatFileSize(dataset.file_size || 0)}</Table.Td>
                  <Table.Td>{getStatusBadge(dataset.status)}</Table.Td>
                  <Table.Td>
                    <Group gap="xs">
                      <Tooltip label="View Dashboard">
                        <ActionIcon variant="subtle" color="blue" onClick={() => handleViewDashboard(dataset)}>
                          <IconEye size="1rem" />
                        </ActionIcon>
                      </Tooltip>
                      
                      <Tooltip label="View Records">
                        <ActionIcon variant="subtle" color="indigo" onClick={() => handleViewRecords(dataset)}>
                          <IconDatabase size="1rem" />
                        </ActionIcon>
                      </Tooltip>

                      <Tooltip label="Update File Type">
                        <ActionIcon variant="subtle" color="indigo" onClick={() => handleUpdateFileType(dataset)}>
                          <IconPencil size="1rem" />
                        </ActionIcon>
                      </Tooltip>
                      
                      {dataset.status !== 'validated' && (
                        <Tooltip label="Validate Dataset">
                          <ActionIcon variant="subtle" color="green" onClick={() => handleValidate(dataset)}>
                            <IconCheck size="1rem" />
                          </ActionIcon>
                        </Tooltip>
                      )}
                      
                      {dataset.status === 'validation_failed' && (
                        <Tooltip label="View Validation Errors">
                          <ActionIcon variant="subtle" color="red" onClick={() => handleViewValidationErrors(dataset)}>
                            <IconAlertCircle size="1rem" />
                          </ActionIcon>
                        </Tooltip>
                      )}
                      
                      {dataset.status === 'validated' && (
                        <Tooltip label="Generate Summary">
                          <ActionIcon variant="subtle" color="violet" onClick={() => handleGenerateSummary(dataset)}>
                            <IconChartBar size="1rem" />
                          </ActionIcon>
                        </Tooltip>
                      )}
                      
                      <Menu position="bottom-end" withArrow>
                        <Menu.Target>
                          <ActionIcon variant="subtle">
                            <IconDotsVertical size="1rem" />
                          </ActionIcon>
                        </Menu.Target>
                        <Menu.Dropdown>
                          <Menu.Item leftSection={<IconEye size="1rem" />} onClick={() => handleViewDashboard(dataset)}>
                            View Dashboard
                          </Menu.Item>
                          
                          {dataset.status !== 'validated' && (
                            <Menu.Item leftSection={<IconCheck size="1rem" />} onClick={() => handleValidate(dataset)}>
                              Validate Dataset
                            </Menu.Item>
                          )}
                          
                          {dataset.status === 'validated' && (
                            <Menu.Item leftSection={<IconChartBar size="1rem" />} onClick={() => handleGenerateSummary(dataset)}>
                              Generate Summary
                            </Menu.Item>
                          )}
                          
                          <Menu.Item leftSection={<IconEye size="1rem" />} onClick={() => handleViewRecords(dataset)}>
                            View Records
                          </Menu.Item>
                          
                          {dataset.status === 'validation_failed' && (
                            <Menu.Item leftSection={<IconAlertCircle size="1rem" />} onClick={() => handleViewValidationErrors(dataset)}>
                              View Validation Errors
                            </Menu.Item>
                          )}
                          
                          <Menu.Divider />
                          
                          <Menu.Item 
                            leftSection={<IconTrash size="1rem" />} 
                            color="red"
                            onClick={() => handleDeleteClick(dataset)}
                          >
                            Delete Dataset
                          </Menu.Item>
                        </Menu.Dropdown>
                      </Menu>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))
            )}
          </Table.Tbody>
        </Table>
        
        {totalPages > 1 && (
          <Group justify="center" mt="md">
            <Pagination 
              total={totalPages} 
              value={activePage} 
              onChange={setActivePage} 
              withEdges
            />
          </Group>
        )}
      </Card>
      
      <Modal opened={opened} onClose={close} title="Delete Dataset" centered>
        <Text mb="lg">
          Are you sure you want to delete the dataset <strong>{selectedDataset?.name}</strong>? This action cannot be undone.
        </Text>
        <Group justify="flex-end">
          <Button variant="outline" onClick={close}>Cancel</Button>
          <Button color="red" onClick={handleDeleteConfirm}>Delete</Button>
        </Group>
      </Modal>

      <UpdateFileTypeModal
        datasetId={updatingDataSetId}
        opened={showFileTypeModal}
        currentFileType={currentDatasetFileType}
        onClose={() => setShowFileTypeModal(false)}
        onUpdated={() => {
          // Refresh summaries, table, sidebar, etc.
          console.log("Refresh file types");
        }}
      />
    </Container>
  );
}
