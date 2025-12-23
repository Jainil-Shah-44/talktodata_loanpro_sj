'use client';

import { useState, useEffect, useMemo } from 'react';
import { 
  Container, 
  Group, 
  Title, 
  TextInput, 
  Button, 
  Card, 
  Table, 
  Select, 
  Badge, 
  Text, 
  Menu, 
  ActionIcon, 
  rem, 
  Loader, 
  Center, 
  Pagination, 
  Flex, 
  Box, 
  Paper, 
  ScrollArea, 
  Modal, 
  Grid, 
  Divider, 
  List,
  Alert,
  SimpleGrid,
  Accordion,
  Stack
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { 
  IconSearch, 
  IconFilter, 
  IconSortAscending, 
  IconSortDescending, 
  IconDownload,
  IconArrowLeft,
  IconInfoCircle,
  IconAdjustments,
  IconEye,
  IconDotsVertical,
  IconChevronDown,
  IconX,
  IconRefresh,
  IconDatabase
} from '@tabler/icons-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useDatasets } from '@/hooks/useDatasets';
import { useLoanRecords, LoanRecord } from '@/hooks/useLoanRecords';
import Link from 'next/link';

// Mock loan record type - in a real app, you would define this in your types file
// interface LoanRecord {
//   id: string;
//   loan_id: string;
//   customer_name: string;
//   disbursement_date: string;
//   pos_amount: number;
//   disbursement_amount: number;
//   dpd: number;
//   status: string;
//   has_validation_errors: boolean;
//   validation_error_types?: string[];
// }

// Mock loan records data - in a real app, you would fetch this from your API
// const mockLoanRecords: LoanRecord[] = Array.from({ length: 100 }, (_, i) => ({
//   id: `record-${i + 1}`,
//   loan_id: `LOAN-${10000 + i}`,
//   customer_name: `Customer ${i + 1}`,
//   disbursement_date: new Date(2025, 0, Math.floor(Math.random() * 30) + 1).toISOString(),
//   pos_amount: Math.floor(Math.random() * 1000000) + 50000,
//   disbursement_amount: Math.floor(Math.random() * 1000000) + 50000,
//   dpd: Math.floor(Math.random() * 90),
//   status: ['Active', 'Closed', 'Defaulted'][Math.floor(Math.random() * 3)],
//   has_validation_errors: Math.random() > 0.7,
//   validation_error_types: Math.random() > 0.7 ? 
//     ['POS_vs_Disbursement', 'DPD_Consistency', 'Date_Validation']
//       .filter(() => Math.random() > 0.5) : 
//     undefined
// }));

export default function RecordsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const datasetId = searchParams.get('dataset');
  const filterParam = searchParams.get('filter');
  
  const { datasets, loading: datasetsLoading } = useDatasets();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<string>('agreement_no');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [validationFilter, setValidationFilter] = useState<string>(filterParam === 'validation_errors' ? 'errors_only' : 'all');
  const [activePage, setActivePage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState<LoanRecord | null>(null);
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [records, setRecords] = useState<LoanRecord[]>([]);
  
  const { records: fetchedRecords, loading: recordsLoading, error: recordsError, totalRecords } = useLoanRecords(
    datasetId, 
    { 
      validationErrorsOnly: filterParam === 'validation_errors',
      sortField,
      sortDirection
    }
  );
  const itemsPerPage = 20;

  // Update local records state when fetchedRecords changes
  useEffect(() => {
    if (fetchedRecords && fetchedRecords.length > 0) {
      console.log('Setting records from useLoanRecords:', fetchedRecords.length);
      setRecords(fetchedRecords);
    } else {
      console.log('No records received from useLoanRecords');
    }
  }, [fetchedRecords]);

  // Get the current dataset
  const currentDataset = useMemo(() => {
    return datasets.find(d => d.id === datasetId) || null;
  }, [datasets, datasetId]);

  // Simulate loading data
  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1000);
    
    return () => clearTimeout(timer);
  }, []);

  // Filter records based on search query
  const filteredRecords = useMemo(() => {
    if (!records || records.length === 0) return [];
    
    return records.filter(record => {
      if (!searchQuery) return true;
      
      // Convert search query to lowercase for case-insensitive search
      const query = searchQuery.toLowerCase();
      
      // Search in common fields
      return (
        (record.agreement_no?.toLowerCase().includes(query) || false) ||
        (record.customer_name?.toLowerCase().includes(query) || false) ||
        (record.product_type?.toLowerCase().includes(query) || false) ||
        (record.classification?.toLowerCase().includes(query) || false) ||
        (record.state?.toLowerCase().includes(query) || false) ||
        (String(record.principal_os_amt).includes(query)) ||
        (String(record.dpd_as_on_31st_jan_2025).includes(query)) ||
        (String(record.bureau_score).includes(query))
      );
    });
  }, [records, searchQuery]);

  // Apply status filter
  const filteredRecordsWithStatus = useMemo(() => {
    if (!filteredRecords || filteredRecords.length === 0) return [];
    
    if (statusFilter === 'all') return filteredRecords;
    
    return filteredRecords.filter(record => record.status?.toLowerCase() === statusFilter.toLowerCase());
  }, [filteredRecords, statusFilter]);

  // Apply validation filter
  const filteredRecordsWithValidation = useMemo<LoanRecord[]>(() => {
    if (!filteredRecordsWithStatus) return [];
    
    if (validationFilter === 'all') return filteredRecordsWithStatus;
    
    return filteredRecordsWithStatus.filter((record: LoanRecord) => record.has_validation_errors === true);
  }, [filteredRecordsWithStatus, validationFilter]);

  // Apply sorting
  const sortedRecords = useMemo(() => {
    if (!filteredRecordsWithValidation || filteredRecordsWithValidation.length === 0) return [];
    
    return [...filteredRecordsWithValidation].sort((a: LoanRecord, b: LoanRecord) => {
      let comparison = 0;
      
      try {
        switch (sortField) {
          case 'agreement_no':
            comparison = (a.agreement_no || '').localeCompare(b.agreement_no || '');
            break;
          case 'customer_name':
            comparison = (a.customer_name || '').localeCompare(b.customer_name || '');
            break;
          case 'disbursement_date':
            comparison = (a.disbursement_date || '').localeCompare(b.disbursement_date || '');
            break;
          case 'principal_os_amt':
            comparison = (a.principal_os_amt || 0) - (b.principal_os_amt || 0);
            break;
          case 'disbursement_amount':
            comparison = (a.disbursement_amount || 0) - (b.disbursement_amount || 0);
            break;
          case 'dpd_as_on_31st_jan_2025':
            comparison = (a.dpd_as_on_31st_jan_2025 || 0) - (b.dpd_as_on_31st_jan_2025 || 0);
            break;
          default:
            comparison = 0;
        }
      } catch (error) {
        console.error('Error during sorting:', error);
      }
      
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [filteredRecordsWithValidation, sortField, sortDirection]);

  // Paginate records
  const paginatedRecords = useMemo(() => {
    const startIndex = (activePage - 1) * itemsPerPage;
    return sortedRecords.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedRecords, activePage]);

  const totalPages = Math.ceil(sortedRecords.length / itemsPerPage);

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

  const formatCurrency = (amount: number | undefined) => {
    if (amount === undefined || isNaN(amount)) {
      return 'N/A';
    }

    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) {
      return 'N/A';
    }

    try {
      // Handle Excel serial dates (numbers)
      if (!isNaN(Number(dateString))) {
        // Excel dates are days since 1900-01-01 (or 1904-01-01 on Mac)
        // We'll assume the 1900 date system
        const excelEpoch = new Date(1899, 11, 30); // Dec 30, 1899
        const daysSinceEpoch = Number(dateString);
        const millisecondsSinceEpoch = daysSinceEpoch * 24 * 60 * 60 * 1000;
        const date = new Date(excelEpoch.getTime() + millisecondsSinceEpoch);
        
        // Check if date is valid
        if (!isNaN(date.getTime())) {
          return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
          });
        }
      }
      
      // Try different date formats
      let date: Date;
      
      // First try standard ISO format
      date = new Date(dateString);
      
      // If that doesn't work, try different formats
      if (isNaN(date.getTime())) {
        // Try DD/MM/YYYY format
        const parts = dateString.split(/[\/\-\.]/);
        if (parts.length === 3) {
          // Try both DD/MM/YYYY and MM/DD/YYYY
          date = new Date(`${parts[2]}-${parts[1]}-${parts[0]}`); // DD/MM/YYYY
          
          if (isNaN(date.getTime())) {
            date = new Date(`${parts[2]}-${parts[0]}-${parts[1]}`); // MM/DD/YYYY
          }
        }
      }

      // Check if date is valid
      if (isNaN(date.getTime())) {
        console.debug(`Invalid date format: ${dateString}`);
        return 'N/A';
      }

      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (error) {
      console.error('Error formatting date:', error, 'Date string:', dateString);
      return 'N/A';
    }
  };

  const getStatusBadge = (status: string | undefined) => {
    if (!status) {
      return <Badge color="gray">Unknown</Badge>;
    }

    switch (status.toLowerCase()) {
      case 'active':
        return <Badge color="green">Active</Badge>;
      case 'closed':
        return <Badge color="blue">Closed</Badge>;
      case 'default':
      case 'defaulted':
        return <Badge color="red">Defaulted</Badge>;
      case 'restructured':
        return <Badge color="yellow">Restructured</Badge>;
      case 'w/off':
        return <Badge color="orange">Write-off</Badge>;
      case 'standard':
        return <Badge color="teal">Standard</Badge>;
      case 'sub-standard':
        return <Badge color="pink">Sub-standard</Badge>;
      default:
        return <Badge color="gray">{status}</Badge>;
    }
  };

  const getValidationErrorBadge = (record: LoanRecord) => {
    if (!record || record.has_validation_errors === undefined) return null;

    if (!record.has_validation_errors) return null;

    return (
      <Badge color="red" variant="dot">
        {record.validation_error_types?.length || 0} Errors
      </Badge>
    );
  };

  const handleViewDetails = (record: LoanRecord) => {
    setSelectedRecord(record);
    setDetailsModalOpen(true);
  };

  useEffect(() => {
    console.log('Dataset ID:', datasetId);
    console.log('Records:', records);
    console.log('Loading:', loading);
    console.log('Error:', recordsError);
    console.log('Total Records:', totalRecords);
    
    // Debug record structure if available
    if (records && records.length > 0) {
      console.log('First record keys:', Object.keys(records[0]));
      console.log('First record:', records[0]);
      
      // Debug additional_fields content
      if (records[0].additional_fields) {
        try {
          const additionalFields = typeof records[0].additional_fields === 'string' 
            ? JSON.parse(records[0].additional_fields) 
            : records[0].additional_fields;
          
          console.log('Additional fields keys:', Object.keys(additionalFields));
          
          // Log all field names and values for debugging
          console.log('All additional fields:');
          Object.entries(additionalFields).forEach(([key, value]) => {
            console.log(`${key}: ${value}`);
          });
          
          // Check specific fields we're trying to display
          const fieldsToCheck = [
            'agreement_no', 'dpd', 'classification', 'principal_os_amt', 
            'disbursement_date', 'sanction_date', 'date_of_npa', 'product_type',
            'ltv_at_sanction', 'customer_name', 'tenor_at_disbursment', 
            'no_of_emi_paid', 'balance_tenor', 'roi_at_booking', 
            'sanction_amt', 'total_amt_disb'
          ];
          
          console.log('Checking specific fields:');
          fieldsToCheck.forEach(field => {
            console.log(`Looking for ${field}:`);
            // Check direct match
            if (records[0][field] !== undefined) {
              console.log(`  Direct match: ${records[0][field]}`);
            }
            
            // Check in additional_fields
            const matches = Object.keys(additionalFields).filter(key => 
              key.toLowerCase().includes(field.toLowerCase()) || 
              field.toLowerCase().includes(key.toLowerCase())
            );
            
            if (matches.length > 0) {
              console.log(`  Possible matches in additional_fields: ${matches.join(', ')}`);
              matches.forEach(match => {
                console.log(`    ${match}: ${additionalFields[match]}`);
              });
            } else {
              console.log('  No matches found');
            }
          });
        } catch (error) {
          console.error('Error parsing additional_fields:', error);
        }
      } else {
        console.log('No additional_fields available');
      }
    } else {
      console.log('No records available to display');
    }
  }, [datasetId, records, loading, recordsError, totalRecords]);

  // Add direct API call to debug
  useEffect(() => {
    if (datasetId) {
      // Make a direct API call to check if we can get records
      const checkRecords = async () => {
        try {
          console.log(`Direct API check: Fetching records for dataset ${datasetId}`);
          // Use the apiClient instead of fetch to ensure proper headers and base URL
          const response = await fetch(`http://localhost:8000/api/datasets/${datasetId}/records`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
              'Content-Type': 'application/json'
            }
          });
          
          if (!response.ok) {
            console.error(`API error: ${response.status} ${response.statusText}`);
            const text = await response.text();
            console.error('Response text:', text);
            return;
          }
          
          const data = await response.json();
          console.log('Direct API response:', data);
          
          if (Array.isArray(data) && data.length > 0) {
            console.log('Direct API found records:', data.length);
            console.log('Sample record:', data[0]);
          } else {
            console.log('Direct API found no records');
          }
        } catch (err) {
          console.error('Direct API check error:', err);
        }
      };
      
      checkRecords();
    }
  }, [datasetId]);

  // Add reprocessing functionality
  const [reprocessing, setReprocessing] = useState(false);
  
  // Add state for creating test data
  const [creatingTestData, setCreatingTestData] = useState(false);

  const handleReprocessDataset = async () => {
    if (!datasetId) return;
    
    try {
      setReprocessing(true);
      console.log(`Reprocessing dataset: ${datasetId}`);
      
      const response = await fetch(`http://localhost:8000/api/datasets/${datasetId}/reprocess`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Error reprocessing dataset: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Reprocessing successful:', data);
      
      // Reload the page to fetch the new records
      window.location.reload();
      
      notifications.show({
        title: 'Success',
        message: `Dataset reprocessed successfully with ${data.total_records} records`,
        color: 'green'
      });
    } catch (error) {
      console.error('Error reprocessing dataset:', error);
      notifications.show({
        title: 'Error',
        message: 'An unexpected error occurred while reprocessing the dataset',
        color: 'red'
      });
    } finally {
      setReprocessing(false);
    }
  };
  
  // Function to create sample records for testing
  const handleCreateSampleRecords = async () => {
    if (!datasetId) return;
    
    try {
      setCreatingTestData(true);
      console.log(`Creating sample records for dataset: ${datasetId}`);
      
      const response = await fetch(`http://localhost:8000/api/datasets/${datasetId}/create_samples`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        if (response.status === 500) {
          console.error('Database connection issue:', response.statusText);
          notifications.show({
            title: 'Error',
            message: 'Failed to create sample records due to database connection issue',
            color: 'red'
          });
        } else {
          throw new Error(`Error creating sample records: ${response.statusText}`);
        }
      }
      
      const data = await response.json();
      console.log('Sample records created successfully:', data);
      
      // Reload the page to fetch the new records
      window.location.reload();
      
      notifications.show({
        title: 'Success',
        message: `Created ${data.total_records} sample records successfully`,
        color: 'green'
      });
    } catch (error) {
      console.error('Error creating sample records:', error);
      notifications.show({
        title: 'Error',
        message: 'An unexpected error occurred while creating sample records',
        color: 'red'
      });
    } finally {
      setCreatingTestData(false);
    }
  };

  if (datasetsLoading || recordsLoading || loading) {
    return (
      <Container size="xl" py="md">
        <Group justify="center" h={400}>
          <Loader size="lg" />
        </Group>
      </Container>
    );
  }

  if (!currentDataset) {
    return (
      <Container size="xl" py="md">
        <Alert icon={<IconInfoCircle size="1rem" />} title="Dataset Not Found" color="red">
          The requested dataset could not be found. Please select a valid dataset.
        </Alert>
        <Button 
          component={Link} 
          href="/dashboard/datasets" 
          leftSection={<IconArrowLeft size="1rem" />}
          mt="lg"
        >
          Back to Dataset Selection
        </Button>
      </Container>
    );
  }

  if (recordsError) {
    return (
      <Container size="xl" py="md">
        <Alert icon={<IconInfoCircle size="1rem" />} title="Error Loading Records" color="red">
          {recordsError}
        </Alert>
      </Container>
    );
  }

  return (
    <Container size="xl" py="md">
      <Group justify="space-between" mb="lg">
        <Group>
          <Button 
            component={Link} 
            href="/dashboard/datasets" 
            variant="subtle" 
            leftSection={<IconArrowLeft size="1rem" />}
          >
            Back
          </Button>
          <Title order={2}>Loan Records</Title>
        </Group>
        <Button 
          leftSection={<IconDownload size="1rem" />}
          variant="outline"
        >
          Export Data
        </Button>
        <Button
          onClick={handleReprocessDataset}
          loading={reprocessing}
          disabled={!datasetId}
          leftSection={<IconRefresh size={16} />}
          size="sm"
          variant="light"
          color="blue"
          mr="xs"
        >
          Reprocess
        </Button>
        <Button
          onClick={handleCreateSampleRecords}
          loading={creatingTestData}
          disabled={!datasetId}
          leftSection={<IconDatabase size={16} />}
          size="sm"
          variant="light"
          color="green"
        >
          Create Test Data
        </Button>
      </Group>
      
      <Card withBorder p="md" radius="md" mb="md">
        <Group mb="md">
          <div>
            <Text fw={500} size="lg">{currentDataset.name}</Text>
            {currentDataset.description && (
              <Text size="sm" c="dimmed">{currentDataset.description}</Text>
            )}
          </div>
          <Badge size="lg" ml="auto">{filteredRecords.length} Records</Badge>
        </Group>
      </Card>
      
      <Card withBorder p="md" radius="md" mb="lg">
        <Group mb="md">
          <TextInput
            placeholder="Search by loan ID or customer name..."
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
              { value: 'active', label: 'Active' },
              { value: 'closed', label: 'Closed' },
              { value: 'defaulted', label: 'Defaulted' }
            ]}
            value={statusFilter}
            onChange={(value) => setStatusFilter(value || 'all')}
            w={180}
          />
          
          <Select
            placeholder="Validation filter"
            leftSection={<IconFilter size="1rem" />}
            data={[
              { value: 'all', label: 'All Records' },
              { value: 'errors_only', label: 'Validation Errors Only' }
            ]}
            value={validationFilter}
            onChange={(value) => setValidationFilter(value || 'all')}
            w={200}
          />
        </Group>
        
        <ScrollArea>
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th onClick={() => handleSort('agreement_no')}>
                  Agreement No {getSortIcon('agreement_no')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('dpd')}>
                  DPD {getSortIcon('dpd')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('classification')}>
                  Classification {getSortIcon('classification')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('principal_os_amt')}>
                  Principal Outstanding {getSortIcon('principal_os_amt')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('total_balance_amt')}>
                  Total Balance {getSortIcon('total_balance_amt')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('disbursement_date')}>
                  Disbursement Date {getSortIcon('disbursement_date')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('sanction_date')}>
                  Sanction Date {getSortIcon('sanction_date')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('date_of_npa')}>
                  Date of NPA {getSortIcon('date_of_npa')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('date_of_woff')}>
                  Date of Write-off {getSortIcon('date_of_woff')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('product_type')}>
                  Product Type {getSortIcon('product_type')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('property_value')}>
                  Property Value {getSortIcon('property_value')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('ltv_at_sanction')}>
                  LTV {getSortIcon('ltv_at_sanction')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('state')}>
                  State {getSortIcon('state')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('no_of_emi_paid')}>
                  No. of EMI Paid {getSortIcon('no_of_emi_paid')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('balance_tenor')}>
                  Balance Tenor {getSortIcon('balance_tenor')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('legal_status')}>
                  Legal Status {getSortIcon('legal_status')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('post_npa_collection')}>
                  Post NPA Collection {getSortIcon('post_npa_collection')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('6m_col')}>
                  6m Collection {getSortIcon('6m_col')}
                </Table.Th>
                <Table.Th onClick={() => handleSort('12m_col')}>
                  12m Collection {getSortIcon('12m_col')}
                </Table.Th>
                <Table.Th>
                  Actions
                </Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {paginatedRecords.length === 0 ? (
                <Table.Tr>
                  <Table.Td colSpan={17}>
                    <Text ta="center" py="lg" c="dimmed">
                      No loan records match your filters.
                    </Text>
                  </Table.Td>
                </Table.Tr>
              ) : (
                paginatedRecords.map((record) => {
                  return (
                    <Table.Tr key={record.id}>
                      <Table.Td>{getFieldValue('agreement_no', record, [])}</Table.Td>
                      <Table.Td>{getFieldValue('dpd', record, ['dpd_as_per_string', 'dpd_by_skc', 'auto_dpd', 'days_past_due'])}</Table.Td>
                      <Table.Td>{getFieldValue('classification', record, ['npa_write_off', 'npa/write_off', 'classification_(writeoff/npa/sma)'])}</Table.Td>
                      <Table.Td>{formatCurrency(getFieldValue('principal_os_amt', record, ['principal_outstanding_amt', 'principal outstanding amt', 'principal_os', 'pos_amount']))}</Table.Td>
                      <Table.Td>{formatCurrency(getFieldValue('total_balance_amt', record, ['total_balance_amount', 'total_balanceamt', 'total balance', 'Total_BalanceAmt']))}</Table.Td>
                      <Table.Td>{formatDate(getFieldValue('disbursement_date', record, ['first_disb_date', 'last_disb_date']))}</Table.Td>
                      <Table.Td>{formatDate(getFieldValue('sanction_date', record, ['sanction_date']))}</Table.Td>
                      <Table.Td>{formatDate(getFieldValue('date_of_npa', record, ['date_of_npa']))}</Table.Td>
                      <Table.Td>{formatDate(getFieldValue('date_of_woff', record, ['date_of_write_off', 'date_of_woff']))}</Table.Td>
                      <Table.Td>{getFieldValue('product_type', record, ['product_type__skc', 'product_type_-_skc'])}</Table.Td>
                      <Table.Td>{formatCurrency(getFieldValue('property_value', record, ['asset_cost', 'vehicle_value']))}</Table.Td>
                      <Table.Td>{getFieldValue('ltv_at_sanction', record, ['ltv', 'ltv_at_sanction', 'current_ltv'])}</Table.Td>
                      <Table.Td>{getFieldValue('state', record, ['state_by_skc'])}</Table.Td>
                      <Table.Td>{getFieldValue('no_of_emi_paid', record, ['no_of_emi_paid_months', 'no_of_emi'])}</Table.Td>
                      <Table.Td>{getFieldValue('balance_tenor', record, ['balance_tenor_months'])}</Table.Td>
                      <Table.Td>{getFieldValue('legal_status', record, ['arbitration_status', 'if_action_taken_under_s.138_of_ni_act'])}</Table.Td>
                      <Table.Td>{formatCurrency(getFieldValue('post_npa_collection', record, []))}</Table.Td>
                      <Table.Td>{formatCurrency(getFieldValue('6m_col', record, []))}</Table.Td>
                      <Table.Td>{formatCurrency(getFieldValue('12m_col', record, []))}</Table.Td>
                      <Table.Td>
                        <Menu position="bottom-end" withArrow>
                          <Menu.Target>
                            <ActionIcon variant="subtle">
                              <IconDotsVertical size="1rem" />
                            </ActionIcon>
                          </Menu.Target>
                          <Menu.Dropdown>
                            <Menu.Item 
                              leftSection={<IconEye size="1rem" />}
                              onClick={() => handleViewDetails(record)}
                            >
                              View Details
                            </Menu.Item>
                          </Menu.Dropdown>
                        </Menu>
                      </Table.Td>
                    </Table.Tr>
                  );
                })
              )}
            </Table.Tbody>
          </Table>
        </ScrollArea>
        
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
      
      {/* Record Details Modal */}
      <Modal 
        opened={detailsModalOpen} 
        onClose={() => setDetailsModalOpen(false)}
        title="Loan Record Details"
        size="xl"
      >
        {selectedRecord && (
          <>
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
              <Stack>
                <Title order={4}>Basic Information</Title>
                <Table>
                  <Table.Tbody>
                    <Table.Tr>
                      <Table.Td fw={600}>Agreement No</Table.Td>
                      <Table.Td>{getFieldValue('agreement_no', selectedRecord, [])}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Customer Name</Table.Td>
                      <Table.Td>{getFieldValue('customer_name', selectedRecord, ['customer', 'borrower_name'])}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Product Type</Table.Td>
                      <Table.Td>{getFieldValue('product_type', selectedRecord, ['product_type__skc'])}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Classification</Table.Td>
                      <Table.Td>{getFieldValue('classification', selectedRecord, ['npa_write_off'])}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>State</Table.Td>
                      <Table.Td>{getFieldValue('state', selectedRecord, [])}</Table.Td>
                    </Table.Tr>
                  </Table.Tbody>
                </Table>
              </Stack>
              
              <Stack>
                <Title order={4}>Financial Details</Title>
                <Table>
                  <Table.Tbody>
                    <Table.Tr>
                      <Table.Td fw={600}>Principal Outstanding</Table.Td>
                      <Table.Td>{formatCurrency(getFieldValue('principal_os_amt', selectedRecord, ['principal_outstanding_amt', 'total_balanceamt', 'pos_amount']))}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Sanction Amount</Table.Td>
                      <Table.Td>{formatCurrency(getFieldValue('sanction_amt', selectedRecord, ['sanction_amt']))}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Total Disbursement</Table.Td>
                      <Table.Td>{formatCurrency(getFieldValue('total_amt_disb', selectedRecord, ['total_amt_disb']))}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>DPD</Table.Td>
                      <Table.Td>{getFieldValue('dpd', selectedRecord, ['dpd_as_per_string', 'dpd_by_skc', 'auto_dpd', 'days_past_due'])}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>ROI at Booking</Table.Td>
                      <Table.Td>{getFieldValue('roi_at_booking', selectedRecord, ['roi_at_booking', 'current_roi'])}</Table.Td>
                    </Table.Tr>
                  </Table.Tbody>
                </Table>
              </Stack>
              
              <Stack>
                <Title order={4}>Dates</Title>
                <Table>
                  <Table.Tbody>
                    <Table.Tr>
                      <Table.Td fw={600}>Disbursement Date</Table.Td>
                      <Table.Td>{formatDate(getFieldValue('disbursement_date', selectedRecord, ['first_disb_date', 'last_disb_date']))}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Sanction Date</Table.Td>
                      <Table.Td>{formatDate(getFieldValue('sanction_date', selectedRecord, ['sanction_date']))}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Date of NPA</Table.Td>
                      <Table.Td>{formatDate(getFieldValue('date_of_npa', selectedRecord, ['date_of_npa']))}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Created At</Table.Td>
                      <Table.Td>{formatDate(selectedRecord.created_at)}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Updated At</Table.Td>
                      <Table.Td>{formatDate(selectedRecord.updated_at)}</Table.Td>
                    </Table.Tr>
                  </Table.Tbody>
                </Table>
              </Stack>
              
              <Stack>
                <Title order={4}>Loan Terms</Title>
                <Table>
                  <Table.Tbody>
                    <Table.Tr>
                      <Table.Td fw={600}>Tenor at Disbursement</Table.Td>
                      <Table.Td>{getFieldValue('tenor_at_disbursment', selectedRecord, ['tenor_at_disbursment_months', 'current_tenor_months'])}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>No. of EMI Paid</Table.Td>
                      <Table.Td>{getFieldValue('no_of_emi_paid', selectedRecord, ['no_of_emi_paid_months', 'no_of_emi'])}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Balance Tenor</Table.Td>
                      <Table.Td>{getFieldValue('balance_tenor', selectedRecord, ['balance_tenor_months'])}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>LTV at Sanction</Table.Td>
                      <Table.Td>{getFieldValue('ltv_at_sanction', selectedRecord, ['ltv', 'ltv_at_sanction'])}</Table.Td>
                    </Table.Tr>
                    <Table.Tr>
                      <Table.Td fw={600}>Bureau Score</Table.Td>
                      <Table.Td>{getFieldValue('bureau_score', selectedRecord, [])}</Table.Td>
                    </Table.Tr>
                  </Table.Tbody>
                </Table>
              </Stack>
            </SimpleGrid>
            
            {/* Show all additional fields in an expandable section */}
            <Accordion mt="xl">
              <Accordion.Item value="all-fields">
                <Accordion.Control>
                  <Title order={4}>All Fields</Title>
                </Accordion.Control>
                <Accordion.Panel>
                  <ScrollArea h={300}>
                    <Table>
                      <Table.Thead>
                        <Table.Tr>
                          <Table.Th>Field</Table.Th>
                          <Table.Th>Value</Table.Th>
                        </Table.Tr>
                      </Table.Thead>
                      <Table.Tbody>
                        {Object.entries({
                          ...selectedRecord,
                          additional_fields: undefined, // Remove this to avoid duplication
                          ...(selectedRecord.additional_fields && typeof selectedRecord.additional_fields === 'string' 
                            ? JSON.parse(selectedRecord.additional_fields) 
                            : selectedRecord.additional_fields || {})
                        }).map(([key, value]) => (
                          <Table.Tr key={key}>
                            <Table.Td fw={600}>{key}</Table.Td>
                            <Table.Td>
                              {typeof value === 'object' && value !== null
                                ? JSON.stringify(value)
                                : String(value !== null && value !== undefined ? value : 'N/A')}
                            </Table.Td>
                          </Table.Tr>
                        ))}
                      </Table.Tbody>
                    </Table>
                  </ScrollArea>
                </Accordion.Panel>
              </Accordion.Item>
            </Accordion>
          </>
        )}
      </Modal>
    </Container>
  );
}

// Helper function to format date values from various formats
const formatDateValue = (value: any): string => {
  // Handle null, undefined, or empty values
  if (!value) return 'N/A';
  
  // Handle special cases
  if (value === '1/0/00' || value === 0 || value === '0') return 'N/A';
  
  // If it's a string, try to parse it as a date
  if (typeof value === 'string') {
    // Handle special cases
    if (value.trim().toUpperCase() === '#N/A' || value.trim().toUpperCase() === 'N/A' || 
        value.trim() === '' || value.trim().toUpperCase() === 'NULL' || value.trim().toUpperCase() === 'NONE') {
      return 'N/A';
    }
    
    // If it's already a date string in ISO format, just format it
    if (value.match(/^\d{4}-\d{2}-\d{2}/)) {
      return new Date(value).toLocaleDateString();
    }
    
    // Handle MM/DD/YY format
    if (value.match(/^\d{1,2}\/\d{1,2}\/\d{2}$/)) {
      const parts = value.split('/');
      // Assume 20xx for two-digit years
      const year = parseInt(parts[2]) < 50 ? `20${parts[2]}` : `19${parts[2]}`;
      return new Date(`${parts[0]}/${parts[1]}/${year}`).toLocaleDateString();
    }
    
    // Handle DD-MM-YYYY format
    if (value.match(/^\d{1,2}-\d{1,2}-\d{4}$/)) {
      const parts = value.split('-');
      return new Date(`${parts[1]}/${parts[0]}/${parts[2]}`).toLocaleDateString();
    }
    
    // Handle DD.MM.YYYY format
    if (value.match(/^\d{1,2}\.\d{1,2}\.\d{4}$/)) {
      const parts = value.split('.');
      return new Date(`${parts[1]}/${parts[0]}/${parts[2]}`).toLocaleDateString();
    }
    
    // Last resort: try direct parsing
    try {
      const date = new Date(value);
      if (!isNaN(date.getTime())) {
        return date.toLocaleDateString();
      }
    } catch (e) {
      console.error('Error parsing date string:', e);
    }
    
    // If we can't parse it as a date, return the original value
    return value;
  }
  
  // If it's a number (Excel date serial), convert it to a date
  if (typeof value === 'number') {
    // Excel dates are number of days since 1/1/1900
    // JavaScript dates are milliseconds since 1/1/1970
    try {
      const excelEpoch = new Date(1899, 11, 30); // Excel's epoch is 12/30/1899
      const msPerDay = 24 * 60 * 60 * 1000;
      const date = new Date(excelEpoch.getTime() + value * msPerDay);
      if (!isNaN(date.getTime())) {
        return date.toLocaleDateString();
      }
    } catch (e) {
      console.error('Error converting Excel date:', e);
    }
  }
  
  // If it's a Date object, format it
  if (value instanceof Date) {
    return value.toLocaleDateString();
  }
  
  // If all else fails, return the value as a string
  return String(value);
};

// Helper function to get value from multiple possible field names
const getFieldValue = (mainFieldName: string, record: LoanRecord, alternateNames: string[] = []): any => {
  // Direct field mappings to database columns
  const directFieldMappings: Record<string, string[]> = {
    'agreement_no': ['agreement_no', 'loan_id'],
    'loan_id': ['loan_id', 'agreement_no'],
    'customer_name': ['customer_name'],
    'disbursement_date': ['first_disb_date', 'last_disb_date'],
    'product_type': ['product_type'],
    'state': ['state'],
    'principal_os_amt': ['principal_os_amt', 'pos_amount', 'principal_outstanding_amt', 'principal_os'],
    'total_balance_amt': ['total_balance_amt', 'total_balance_amount', 'total_balanceamt'],
    'dpd': ['dpd', 'dpd_as_on_31st_jan_2025', 'dpd_as_per_string', 'dpd_by_skc'],
    'classification': ['classification'],
    'bureau_score': ['bureau_score'],
    'sanction_date': ['sanction_date'],
    'date_of_npa': ['date_of_npa'],
    'date_of_woff': ['date_of_woff'],
    'total_collection': ['total_collection'],
    'post_npa_collection': ['post_npa_collection'],
    'post_woff_collection': ['post_woff_collection'],
    'interest_overdue_amt': ['interest_overdue_amt'],
    'penal_interest_overdue': ['penal_interest_overdue'],
    'chq_bounce_other_charges_amt': ['chq_bounce_other_charges_amt'],
    'provision_done_till_date': ['provision_done_till_date'],
    'carrying_value_as_on_date': ['carrying_value_as_on_date'],
    'sanction_amt': ['sanction_amt'],
    'total_amt_disb': ['total_amt_disb'],
    'pos_amount': ['pos_amount', 'principal_os_amt'],
    'disbursement_amount': ['disbursement_amount', 'total_amt_disb'],
    'status': ['status'],
    'june_24_pool': ['june_24_pool'],
    'm1_collection': ['m1_collection'],
    'm2_collection': ['m2_collection'],
    'm3_collection': ['m3_collection'],
    'm4_collection': ['m4_collection'],
    'm5_collection': ['m5_collection'],
    'm6_collection': ['m6_collection'],
    'm7_collection': ['m7_collection'],
    'm8_collection': ['m8_collection'],
    'm9_collection': ['m9_collection'],
    'm10_collection': ['m10_collection'],
    'm11_collection': ['m11_collection'],
    'm12_collection': ['m12_collection'],
    'auto_dpd_bucket': ['auto_dpd_bucket'],
    'auto_pos_bucket': ['auto_pos_bucket'],
    'auto_model_year_skc_bucket': ['auto_model_year_skc_bucket'],
    'auto_roi_at_booking_bucket': ['auto_roi_at_booking_bucket'],
    'auto_bureau_score_bucket': ['auto_bureau_score_bucket'],
    'auto_current_ltv_bucket': ['auto_current_ltv_bucket'],
    'arbitration_status': ['arbitration_status'],
    'action_taken_under_s138_ni_act': ['action_taken_under_s138_ni_act']
  };
  
  // Map of exact field names to check in additional_fields as fallback
  const exactFieldMap: Record<string, string[]> = {
    'agreement_no': ['Agreement No', 'Loan No', 'Agreement Number', 'Loan Number', 'AGREEMENT_NO', 'LOAN_NO'],
    'loan_id': ['Loan ID', 'Loan Account Number', 'LOAN_ID', 'LOAN_ACCOUNT_NUMBER'],
    'customer_name': ['Customer Name', 'Borrower Name', 'Customer', 'CUSTOMER_NAME', 'BORROWER_NAME'],
    'disbursement_date': ['Disbursement Date', 'First Disb Date', 'First Disbursement Date', 'DISBURSEMENT_DATE', 'FIRST_DISB_DATE'],
    'product_type': ['Product Type', 'Product', 'Loan Type', 'PRODUCT_TYPE', 'LOAN_TYPE'],
    'state': ['State', 'Customer State', 'Borrower State', 'STATE', 'CUSTOMER_STATE'],
    'principal_os_amt': ['Principal O/S', 'Principal Outstanding', 'POS', 'Principal OS Amt', 'PRINCIPAL_OS_AMT', 'PRINCIPAL_OUTSTANDING', 'Principal_outstanding_Amt'],
    'total_balance_amt': ['Total Balance Amt', 'Total Balance', 'Total_BalanceAmt', 'TOTAL_BALANCE_AMT', 'Total_Balance_Amount'],
    'dpd': ['DPD', 'Days Past Due', 'Overdue Days', 'DPD_AS_ON_31ST_JAN_2025', 'DAYS_PAST_DUE'],
    'classification': ['Classification', 'Asset Classification', 'Loan Classification', 'CLASSIFICATION', 'ASSET_CLASSIFICATION'],
    'bureau_score': ['Bureau Score', 'CIBIL Score', 'Credit Score', 'BUREAU_SCORE', 'CIBIL_SCORE'],
    'sanction_date': ['Sanction Date', 'Date of Sanction', 'SANCTION_DATE', 'DATE_OF_SANCTION'],
    'date_of_npa': ['Date of NPA', 'NPA Date', 'DATE_OF_NPA', 'Date_of_NPA'],
    'date_of_woff': ['Date of Write-off', 'Date of W/off', 'Write-off Date', 'Date of Writ e.off', 'DATE_OF_WRITE_OFF', 'Date_of_Write_off'],
    'property_value': ['Property Value', 'Asset Cost', 'Vehicle Value', 'ASSET_COST'],
    'ltv': ['LTV', 'LTV at Sanction', 'Current LTV', 'LTV_AT_SANCTION', 'LTV_at_Sanction', 'Current_LTV'],
    'ltv_at_sanction': ['LTV at Sanction', 'LTV', 'Current LTV', 'LTV_AT_SANCTION', 'LTV_at_Sanction'],
    'no_of_emi_paid': ['No. of EMI Paid', 'No of EMI Paid Months', 'No of EMI', 'NO_OF_EMI_PAID', 'NO_OF_EMI_PAID_Months', 'EMI Paid', 'NO_OF_EMI_PAID_Months'],
    'balance_tenor': ['Balance Tenor', 'Balance Tenor Months', 'Remaining Tenor', 'BALANCE_TENOR_Months'],
    'legal_status': ['Legal Status', 'Arbitration Status', 'If action taken under S.138 of NI Act', 'LEGAL_STATUS', 'Arbitration_status', 'If_action_taken_under_S138_of_NI_Act'],
    'post_npa_collection': ['POST NPA COLLECTION', 'Post NPA Collection', 'NPA Collection', 'Post NPA Coll', 'POST_NPA_COLLECTION'],
    'post_woff_collection': ['POST W OFF COLLECTION', 'Post W/off Collection', 'Write-off Collection', 'Post Write Off Collection', 'POST_W_OFF_COLLECTION'],
    '6m_col': ['6M Collection', '6 Month Collection', 'Col_6M'],
    '12m_col': ['12M Collection', '12 Month Collection', 'Col_12M'],
    '24m_col': ['24M Collection', '24 Month Collection']
  };
  
  // Special handling for total_balance_amt field
  if (mainFieldName === 'total_balance_amt') {
    // First check if total_balance_amt exists directly in the record
    if (record.total_balance_amt !== undefined && record.total_balance_amt !== null) {
      console.log(`Found total_balance_amt directly in record: ${record.total_balance_amt}`);
      return record.total_balance_amt;
    }
    
    // Try to find it in additional_fields
    try {
      if (record.additional_fields) {
        const additionalFields = typeof record.additional_fields === 'string' ? 
          JSON.parse(record.additional_fields) : record.additional_fields;
        
        // Check for common field names
        const totalBalanceFieldNames = [
          'total_balance_amt', 'total balance amt', 'total_balance_amount',
          'total balance amount', 'total balanceamt', 'total_balanceamt',
          'Total Balance Amt', 'Total Balance', 'Total_BalanceAmt',
          'TOTAL_BALANCE_AMT', 'Total_Balance_Amount'
        ];
        
        for (const fieldName of totalBalanceFieldNames) {
          // Try exact match
          if (additionalFields[fieldName] !== undefined && additionalFields[fieldName] !== null) {
            console.log(`Found total_balance_amt in additional_fields as ${fieldName}: ${additionalFields[fieldName]}`);
            return additionalFields[fieldName];
          }
          
          // Try case-insensitive match
          const lowerFieldName = fieldName.toLowerCase();
          for (const key in additionalFields) {
            if (key.toLowerCase() === lowerFieldName) {
              console.log(`Found total_balance_amt in additional_fields with case-insensitive match ${key}: ${additionalFields[key]}`);
              return additionalFields[key];
            }
          }
        }
        
        // Try fuzzy matching - any field containing 'total' and 'balance'
        for (const key in additionalFields) {
          const keyLower = key.toLowerCase();
          if (keyLower.includes('total') && keyLower.includes('balance')) {
            console.log(`Found total_balance_amt in additional_fields with fuzzy match ${key}: ${additionalFields[key]}`);
            return additionalFields[key];
          }
        }
      }
    } catch (e) {
      console.error('Error parsing additional_fields for total_balance_amt:', e);
    }
  }
  
  // Special handling for principal_os_amt field
  if (mainFieldName === 'principal_os_amt') {
    // First check if principal_os_amt exists directly in the record
    if (record.principal_os_amt !== undefined && record.principal_os_amt !== null) {
      console.log(`Found principal_os_amt directly in record: ${record.principal_os_amt}`);
      return record.principal_os_amt;
    }
    
    // Then check for pos_amount as an alternative
    if (record.pos_amount !== undefined && record.pos_amount !== null) {
      console.log(`Using pos_amount as fallback: ${record.pos_amount}`);
      return record.pos_amount;
    }
    
    // Finally check additional_fields for any principal outstanding related field
    try {
      if (record.additional_fields) {
        const additionalFields = typeof record.additional_fields === 'string' ? 
          JSON.parse(record.additional_fields) : record.additional_fields;
        
        // Check for common field names
        const principalFieldNames = [
          'principal_os_amt', 'principal os amt', 'principal_outstanding_amt',
          'principal outstanding amt', 'pos', 'pos_amount', 'principal_os',
          'principal outstanding', 'principal_outstanding', 'principal o/s',
          'Principal O/S', 'Principal Outstanding', 'POS', 'Principal OS Amt',
          'PRINCIPAL_OS_AMT', 'PRINCIPAL_OUTSTANDING'
        ];
        
        for (const fieldName of principalFieldNames) {
          // Try exact match
          if (additionalFields[fieldName] !== undefined && additionalFields[fieldName] !== null) {
            console.log(`Found principal_os_amt in additional_fields as ${fieldName}: ${additionalFields[fieldName]}`);
            return additionalFields[fieldName];
          }
          
          // Try case-insensitive match
          const lowerFieldName = fieldName.toLowerCase();
          for (const key in additionalFields) {
            if (key.toLowerCase() === lowerFieldName) {
              console.log(`Found principal_os_amt in additional_fields with case-insensitive match ${key}: ${additionalFields[key]}`);
              return additionalFields[key];
            }
          }
        }
        
        // Try fuzzy matching - any field containing 'principal' and ('os' or 'outstanding')
        for (const key in additionalFields) {
          const keyLower = key.toLowerCase();
          if ((keyLower.includes('principal') || keyLower.includes('pos')) && 
              (keyLower.includes('os') || keyLower.includes('outstanding'))) {
            console.log(`Found principal_os_amt in additional_fields with fuzzy match ${key}: ${additionalFields[key]}`);
            return additionalFields[key];
          }
        }
      }
    } catch (e) {
      console.error('Error parsing additional_fields for principal_os_amt:', e);
    }
  }
  
  // Special handling for DPD field
  if (mainFieldName === 'dpd') {
    if (record.dpd_as_on_31st_jan_2025 !== undefined && record.dpd_as_on_31st_jan_2025 !== null) {
      const dpdValue = Number(record.dpd_as_on_31st_jan_2025);
      // If it's 999, it's a write-off loan
      if (dpdValue === 999) {
        return 'Write-off';
      }
      return String(dpdValue);
    }
    
    // Then check if dpd exists in the record
    if (record.dpd !== undefined && record.dpd !== null && String(record.dpd) !== '') {
      return String(record.dpd);
    }
    
    // Finally check additional_fields for original_dpd
    try {
      if (record.additional_fields) {
        const additionalFields = typeof record.additional_fields === 'string' ? 
          JSON.parse(record.additional_fields) : record.additional_fields;
        
        if (additionalFields && additionalFields.original_dpd !== undefined && additionalFields.original_dpd !== null) {
          return String(additionalFields.original_dpd);
        }
        
        // Try to find any field with DPD in the name
        for (const key in additionalFields) {
          if (key.toUpperCase().includes('DPD') && additionalFields[key] !== null && additionalFields[key] !== undefined) {
            return String(additionalFields[key]);
          }
        }
      }
    } catch (e) {
      console.error('Error parsing additional_fields for DPD:', e);
    }
  }
  
  // Special handling for date fields
  if (['sanction_date', 'date_of_npa', 'date_of_woff', 'disbursement_date'].includes(mainFieldName)) {
    // First check if the field is directly available in the record
    if (mainFieldName === 'disbursement_date' && record.disbursement_date) {
      return formatDateValue(record.disbursement_date);
    }
    
    try {
      if (record.additional_fields) {
        const additionalFields = typeof record.additional_fields === 'string' ? 
          JSON.parse(record.additional_fields) : record.additional_fields;
        
        // Direct field mapping for CSV columns
        const csvFieldMapping: Record<string, string[]> = {
          'sanction_date': ['SANCTION_DATE', 'sanction_date', 'Sanction Date'],
          'disbursement_date': ['FIRST_DISB_DATE', 'LAST_DISB_DATE', 'disbursement_date', 'Disbursement Date'],
          'date_of_npa': ['Date_of_NPA', 'date_of_npa', 'NPA Date'],
          'date_of_woff': ['Date_of_Write_off', 'date_of_woff', 'Write-off Date']
        };
        
        // First check for formatted date fields (our backend adds these)
        const exactFields = csvFieldMapping[mainFieldName] || [];
        for (const field of exactFields) {
          const formattedField = `${field}_formatted`;
          if (additionalFields[formattedField]) {
            return formatDateValue(additionalFields[formattedField]);
          }
        }
        
        // Then check for exact field names from the CSV
        for (const field of exactFields) {
          if (additionalFields[field]) {
            return formatDateValue(additionalFields[field]);
          }
        }
        
        // Look for original date values
        const originalFieldName = `original_${mainFieldName}`;
        if (additionalFields[originalFieldName]) {
          return formatDateValue(additionalFields[originalFieldName]);
        }
        
        // More aggressive search for date fields
        const dateFieldPatterns = {
          'sanction_date': ['sanction', 'sanctioned', 'sanct'],
          'disbursement_date': ['disbursement', 'disb', 'disburse'],
          'date_of_npa': ['npa', 'non performing'],
          'date_of_woff': ['write', 'woff', 'w/off', 'written']
        };
        
        const patterns = dateFieldPatterns[mainFieldName as keyof typeof dateFieldPatterns] || [];
        
        // Look for any field containing the date name
        for (const key in additionalFields) {
          const keyLower = key.toLowerCase();
          const value = additionalFields[key];
          
          // Skip null or undefined values
          if (value === null || value === undefined) continue;
          
          // Check if key contains any of our patterns
          const matchesPattern = patterns.some(pattern => keyLower.includes(pattern));
          const containsDate = keyLower.includes('date');
          
          if (matchesPattern && (containsDate || typeof value === 'string' && /\d{1,2}[\/\-\.]\d{1,2}/.test(value))) {
            return formatDateValue(value);
          }
        }
      }
    } catch (e) {
      console.error(`Error parsing additional_fields for ${mainFieldName}:`, e);
    }
  }
  
  // Special handling for LTV
  if (mainFieldName === 'ltv' || mainFieldName === 'ltv_at_sanction') {
    try {
      if (record.additional_fields) {
        const additionalFields = typeof record.additional_fields === 'string' ? 
          JSON.parse(record.additional_fields) : record.additional_fields;
          
        // Look for any field containing LTV
        for (const key in additionalFields) {
          if (key.toUpperCase().includes('LTV') && additionalFields[key] !== null && additionalFields[key] !== undefined) {
            const ltvValue = additionalFields[key];
            // Format as percentage if it's a number
            if (!isNaN(Number(ltvValue))) {
              return `${ltvValue}%`;
            }
            return String(ltvValue);
          }
        }
      }
    } catch (e) {
      console.error('Error parsing additional_fields for LTV:', e);
    }
  }
  
  // Special handling for EMI paid
  if (mainFieldName === 'no_of_emi_paid') {
    try {
      if (record.additional_fields) {
        const additionalFields = typeof record.additional_fields === 'string' ? 
          JSON.parse(record.additional_fields) : record.additional_fields;
          
        // Look for any field containing EMI and PAID
        for (const key in additionalFields) {
          const keyLower = key.toLowerCase();
          if (keyLower.includes('emi') && keyLower.includes('paid') && 
              additionalFields[key] !== null && additionalFields[key] !== undefined) {
            return String(additionalFields[key]);
          }
        }
      }
    } catch (e) {
      console.error('Error parsing additional_fields for EMI paid:', e);
    }
  }
  
  // Special handling for legal status
  if (mainFieldName === 'legal_status') {
    try {
      if (record.additional_fields) {
        const additionalFields = typeof record.additional_fields === 'string' ? 
          JSON.parse(record.additional_fields) : record.additional_fields;
          
        // Look for any field containing legal or arbitration
        for (const key in additionalFields) {
          const keyLower = key.toLowerCase();
          if ((keyLower.includes('legal') || keyLower.includes('arbitration')) && 
              additionalFields[key] !== null && additionalFields[key] !== undefined) {
            return String(additionalFields[key]);
          }
        }
      }
    } catch (e) {
      console.error('Error parsing additional_fields for legal status:', e);
    }
  }
  
  // Special handling for post NPA collection
  if (mainFieldName === 'post_npa_collection') {
    try {
      if (record.additional_fields) {
        const additionalFields = typeof record.additional_fields === 'string' ? 
          JSON.parse(record.additional_fields) : record.additional_fields;
          
        // Look for any field containing post npa collection
        for (const key in additionalFields) {
          const keyLower = key.toLowerCase();
          if (keyLower.includes('post') && keyLower.includes('npa') && keyLower.includes('coll') &&
            additionalFields[key] !== null && additionalFields[key] !== undefined) {
            // Format as currency if it's a number
            const value = additionalFields[key];
            if (!isNaN(Number(value))) {
              return `₹${Number(value).toLocaleString()}`;
            }
            return String(value);
          }
        }
      }
    } catch (e) {
      console.error('Error parsing additional_fields for post NPA collection:', e);
    }
  }

  // Check if record is defined
  if (!record) {
    return 'N/A';
  }

  // STEP 1: First check direct database fields using our mapping
  if (mainFieldName in directFieldMappings) {
    for (const directField of directFieldMappings[mainFieldName]) {
      if (record[directField] !== undefined && record[directField] !== null && record[directField] !== '') {
        return record[directField];
      }
    }
  }

  // STEP 2: Check if the main field name exists directly in the record
  if (record[mainFieldName] !== undefined && record[mainFieldName] !== null && record[mainFieldName] !== '') {
    return record[mainFieldName];
  }

  // STEP 3: Check alternate names provided in the function call
  for (const altName of alternateNames) {
    if (record[altName] !== undefined && record[altName] !== null && record[altName] !== '') {
      return record[altName];
    }
  }

  // STEP 4: Only now fall back to additional_fields if we couldn't find the value in direct fields
  let additionalFields: Record<string, any> = {};
  try {
    if (record.additional_fields) {
      additionalFields = typeof record.additional_fields === 'string' ?
        JSON.parse(record.additional_fields) : record.additional_fields;
    }
  } catch (e) {
    console.error('Error parsing additional_fields:', e);
  }

  // Check for exact field names in additional_fields using our mapping
  if (mainFieldName in exactFieldMap) {
    for (const exactField of exactFieldMap[mainFieldName]) {
      // Try exact match
      if (additionalFields[exactField] !== undefined && additionalFields[exactField] !== null) {
        return additionalFields[exactField];
      }

      // Try case-insensitive match
      const lowerExactField = exactField.toLowerCase();
      for (const key in additionalFields) {
        if (key.toLowerCase() === lowerExactField) {
          return additionalFields[key];
        }
      }
    }
  }

  // Check alternate names in additional_fields
  for (const altName of alternateNames) {
    if (additionalFields[altName] !== undefined && additionalFields[altName] !== null) {
      return additionalFields[altName];
    }

    // Try case-insensitive match
    const lowerAltName = altName.toLowerCase();
    for (const key in additionalFields) {
      if (key.toLowerCase() === lowerAltName) {
        return additionalFields[key];
      }
    }
  }

  // Try fuzzy matching for field names in additional_fields
  const lowerMainField = mainFieldName.toLowerCase();

  // First try fields that contain our field name
  for (const key in additionalFields) {
    if (key.toLowerCase().includes(lowerMainField)) {
      return additionalFields[key];
    }
  }

  // Then try fields where our field name contains the key
  for (const key in additionalFields) {
    if (lowerMainField.includes(key.toLowerCase()) && key.length > 3) { // Only match keys longer than 3 chars
      return additionalFields[key];
    }
  }

  // If we still haven't found a value, return N/A
  return 'N/A';
};
