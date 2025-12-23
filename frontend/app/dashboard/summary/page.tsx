'use client';

import { useState, useEffect } from 'react';
import { 
  Title, 
  Card, 
  Text, 
  Group, 
  Button, 
  Center, 
  Stack, 
  Container, 
  Paper, 
  Alert, 
  Badge, 
  Select, 
  Table, 
  Loader, 
  ScrollArea, 
  Box, 
  SimpleGrid 
} from '@mantine/core';
import { IconDatabase, IconInfoCircle, IconRefresh, IconFilter } from '@tabler/icons-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useDatasets } from '@/hooks/useDatasets';
import { useUserStore } from '@/src/store/userStore';
import { useSummaries, useSummariesV2,SummaryTable } from '@/hooks/useSummaries'; //added useSummariesv2 hvb @ 26/10/2025
import { FilterCriteriaModal, PoolSelectionTarget } from '@/components/FilterCriteriaModal'; //FilterCriteria shifted to types hvb @ 08/12/2025 merging
import { FilterResultsSummary } from '@/components/FilterResultsSummary';
import { usePoolSelection } from '@/hooks/usePoolSelection';
import { FilterErrorModal } from '@/components/FilterErrorModal';

import { FilterCriteria } from '@/src/types/index';
import CustomBucketSummaryPage from '@/components/customBuckets/BucketSummaryPage';
import { datasetService } from '@/src/api/services';
import { ColumnInfo } from '@/src/types/mappings';
import { bucketService } from '@/src/api/customBucketService';

// Define LoanRecord interface
interface LoanRecord {
  id: string;
  account_number: string;
  customer_name?: string;
  principal_os_amt: number;
  total_amt_disb?: number;
  dpd: number;
  collection_12m?: number;
  state?: string;
  product_type?: string;
  [key: string]: any;
}

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
  const [datasetFileType , setDsFileType] = useState("");
  //HVB Need to use store for better performance for this field
  const [targetFields, setTargetFields] = useState<ColumnInfo[]>([]);
  //let availableFields = [{ value: '...', label: 'Loading...' }];

 
 // changed by jainil due to error - @23-12-25
  useEffect(() => {
  if (!datasetId) return;

  (async () => {
    const res = await datasetService.getDatasetFileType(datasetId);
    if (res != null) setDsFileType(res);

    const res1 = await bucketService.getSummaryFields(datasetId);
    setTargetFields(res1);
  })();
}, [datasetId]);

  
  // Read filter criteria from URL parameters if they exist
  const urlFilterCriteria = searchParams.get('filters');
  const parsedUrlFilters = urlFilterCriteria ? JSON.parse(decodeURIComponent(urlFilterCriteria)) : null;

  //Added hvb @ 26/10/2025 for filter errors popup
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [errorModalOpened, setErrorModalOpened] = useState(false);
  
  //Added hvb @ 30/11/2025 to pass over custom summary page, HVB NOTE: in this use array of filter, criteria
  const [appliedHookFilter,setAppliedHookFilter] = useState<Record<string, any>>({});

  // Filter state - initialize from URL if available
  const [filterModalOpen, setFilterModalOpen] = useState(false);
  const [filters, setFilters] = useState<FilterCriteria[]>(() => {
    if (parsedUrlFilters) {
      // Convert URL filter format to component filter format
      return Object.entries(parsedUrlFilters).map(([field, criteria]: [string, any]) => ({
        field,
        operator: criteria.operator,
        value: criteria.value,
        min_value: criteria.min_value,
        max_value: criteria.max_value,
        enabled: true
      }));
    }
    //Mod hvb @ 12/12/2025 don't load any filters!
    // return [{
    //   field: 'collection_12m',
    //   operator: '>=',
    //   value: 5000,
    //   enabled: true
    // }];
    return[];
  });

  const [target, setTarget] = useState<PoolSelectionTarget>({
    maxPoolValue: 2500000,
    sortField: 'collection_12m',
    sortDirection: 'desc',
    sumValueField: 'principal_os_amt'
  });

  const [savedFilters, setSavedFilters] = useState<{ id: string; name: string; criteria: FilterCriteria[] }[]>([]);
  const [filterResults, setFilterResults] = useState<{
    totalPoolValue: number;
    filteredRecordCount: number;
    selectedSubPoolCount: number;
    selectedSubPoolValue: number;
  } | null>(null);
  
  // Pool selection hook for filtering functionality
  const { 
    filteredRecords, 
    selectedRecords, 
    applyFilters,
    optimizeSelection,
    saveSelection,
    updateFilterCriteria,
    isFiltering,
    isOptimizing,
    isSaving,
    filterError: poolSelectionError,
    totalSelectedAmount
  } = usePoolSelection(datasetId);
  
  // Convert current filters to the format expected by useSummaries
  const filterCriteria = filters.length > 0 && filters.some(f => f.enabled) ? 
    filters.reduce((acc, filter) => {
      if (filter.enabled) {
        acc[filter.field] = {
          operator: filter.operator,
          value: filter.value,
          min_value: filter.min_value,
          max_value: filter.max_value
        };
      }
      return acc;
    }, {} as any) : undefined;
  
  // Debug logging for filter criteria
  useEffect(() => {
    console.log('[Summary Page] URL filter criteria:', urlFilterCriteria);
    console.log('[Summary Page] Parsed URL filters:', parsedUrlFilters);
    console.log('[Summary Page] Current filters state:', filters);
    console.log('[Summary Page] Filter criteria for useSummaries:', filterCriteria);
  }, [urlFilterCriteria, parsedUrlFilters, filters, filterCriteria]);
  
  //Mod hvb @ 05/12/2025 old poc, commented for testing.
  //const { data: summaryData, isLoading: summaryLoading, error: summaryError } = useSummaries(datasetId, filterCriteria);
  //Mod hvb @ 26/10/2025, HVB NOTE: in this compute summary counts and respond
  const { data: summaryData, isLoading: summaryLoading, error: summaryError } = useSummariesV2(datasetId, filters);
  /*const summaryData = {writeOffPool:{rows:[{bucket:"Total",pos:0,noOfAccs:0,totalCollection:0,"12mCol":0}]}};
  const summaryLoading = false;
  const summaryError = {message:""};*/

  const user = useUserStore((state) => state.user);
  const isAuthenticated = useUserStore((state) => state.isAuthenticated);
  const [writeOffRows, setWriteOffRows] = useState<any[] | null>(null);
  const [dpdRows, setDpdRows] = useState<any[] | null>(null);
  const [savingWriteOff, setSavingWriteOff] = useState(false);
  const [savingDpd, setSavingDpd] = useState(false);
  
  // Since filtering is now handled by the backend, we don't need the old manual filtering logic
  // The summaryData will already be filtered based on the filterCriteria passed to useSummaries

  useEffect(() => {
  if (!datasetId && datasets.length > 0) {
    router.replace(
      `/dashboard/summary?dataset=${datasets[0].id}`
    );
  }
}, [datasetId, datasets, router]);


  console.log("summaryData raj", summaryData);

  const currentDataset = datasets.find(d => d.id === datasetId) || (datasets.length > 0 ? datasets[0] : null);

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
    router.push('/login');
    return null;
  }

  // Helper to recalculate bounds for a table
  function recalculateBounds(rows: any[], changedIdx: number, key: 'lowerBound' | 'upperBound', value: number) {
    const updated = rows.map((r, i) => ({ ...r }));
    updated[changedIdx][key] = value;
    // Calculate new interval for the changed row
    const interval = Math.abs((updated[changedIdx].upperBound ?? 0) - (updated[changedIdx].lowerBound ?? 0));
    // If lowerBound changed, update previous row's upperBound
    if (key === 'lowerBound' && changedIdx > 0) {
      updated[changedIdx - 1].upperBound = value;
    }
    // If upperBound changed, update next row's lowerBound
    if (key === 'upperBound' && changedIdx + 1 < updated.length) {
      updated[changedIdx + 1].lowerBound = value;
    }
    // Recalculate all subsequent rows to keep the same interval
    for (let i = changedIdx + 1; i < updated.length; i++) {
      updated[i].lowerBound = updated[i - 1].upperBound;
      // For the last bucket, keep upperBound open-ended
      if (i === updated.length - 1) {
        updated[i].upperBound = 9999999999;
      } else {
        updated[i].upperBound = updated[i].lowerBound + interval;
      }
    }
    return updated;
  }

  // Save handler for Write-Off Pool
  const handleSaveWriteOff = async () => {
    setSavingWriteOff(true);
    // For now, just log the save action - bucket updating can be added later if needed
    console.log('Write-off pool data would be saved:', writeOffRows);
    setSavingWriteOff(false);
  };

  // Save handler for DPD Summary
  const handleSaveDpd = async () => {
    setSavingDpd(true);
    // For now, just log the save action - bucket updating can be added later if needed
    console.log('DPD summary data would be saved:', dpdRows);
    setSavingDpd(false);
  };

  // Render a summary table
  const renderSummaryTable = (table: SummaryTable, rows: any[] | null, setRows: ((rows: any[]) => void) | undefined, onSave: (() => void) | undefined, saving: boolean) => {
    // Ensure lowerBound and upperBound columns exist
    let columns = table.columns;
    const colKeys = columns.map(c => c.key);
    if (!colKeys.includes('lowerBound')) {
      columns = [
        ...columns.slice(0, 1),
        { key: 'lowerBound', title: 'Lower Bound' },
        ...columns.slice(1)
      ];
    }
    if (!colKeys.includes('upperBound')) {
      columns = [
        ...columns.slice(0, 2),
        { key: 'upperBound', title: 'Upper Bound' },
        ...columns.slice(2)
      ];
    }
    const editableRows = rows ? rows : table.rows;

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
                {columns.map((column) => (
                  <Table.Th key={column.key}>{column.title}</Table.Th>
                ))}
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {editableRows.map((row, rowIndex) => (
                <Table.Tr key={rowIndex} bg={row.bucket === 'Grand Total' ? 'var(--mantine-color-blue-0)' : undefined}>
                  {columns.map((column, colIndex) => (
                    <Table.Td key={`${rowIndex}-${colIndex}`}>
                      {(() => {
                        if ((column.key === 'lowerBound' || column.key === 'upperBound') && setRows) {
                          return (
                            <input
                              type="number"
                              value={row[column.key] ?? ''}
                              min={0}
                              onChange={e => {
                                const updated = recalculateBounds(editableRows, rowIndex, column.key as 'lowerBound' | 'upperBound', Number(e.target.value));
                                setRows(updated);
                              }}
                              style={{ width: 90 }}
                            />
                          );
                        }
                        if (column.key === 'percentOfPos') {
                          return formatPercent(row[column.key] as number);
                        } else if (column.key === 'pos') {
                          return formatCurrency(row[column.key] as number);
                        } else if ([
                          '3mCol', '6mCol', '12mCol', 'totalCollection'
                        ].includes(column.key)) {
                          const rawValue = row[column.key];
                          if (rawValue === 0 || rawValue === '0' || rawValue === null || rawValue === undefined) {
                            return '0.00';
                          }
                          const numValue = parseFloat(rawValue);
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
        {setRows && onSave && (
          <Group justify="flex-end" mt="md">
            <Button onClick={onSave} loading={saving} disabled={saving}>
              Save & Recompute
            </Button>
          </Group>
        )}
      </Paper>
    );
  };

  // Handle filter modal
  const handleOpenFilterModal = () => setFilterModalOpen(true);
  const handleCloseFilterModal = () => setFilterModalOpen(false);
  
  // Available fields for filtering
  // for more fields this needs to be extended, hvb note @ 26/10/2025
  // Mod hvb @ 10/12/2025 creating from state 
  // const availableFields = [
  //   { value: 'collection_12m', label: '12M Collection' },
  //   { value: 'dpd', label: 'DPD' },
  //   { value: 'state', label: 'State' },
  //   { value: 'principal_os_amt', label: 'Principal Outstanding' },
  //   { value: 'product_type', label: 'Product Type' }
  // ];

  //Added hvb @ 26/10/2025 for validate filters for any logical errors or invalid selections
  //
  function validateFilters(filters: FilterCriteria[]): string[] {
  
    const numericOperators = ['>=', '<=', '>', '<', '=', 'between'];
    const stringOperators = ['=', '!=', 'contains', 'startsWith', 'endsWith'];
    const errors: string[] = [];

    // Convert array to object map
    const fieldLabelMap = Object.fromEntries(
      // availableFields.map(item => [item.value, item.label])
      targetFields.map(item => [item.column_name, item.column_name])
    );

    // Group filters by field
    const fieldGroups = filters.reduce((acc, filter) => {
      if (!filter.enabled) return acc;
      if (!acc[filter.field]) acc[filter.field] = [];
      acc[filter.field].push(filter);
      return acc;
    }, {} as Record<string, FilterCriteria[]>);

    for (const field in fieldGroups) {
      const fList = fieldGroups[field];

      let effectiveMin: number | null = null;
      let effectiveMax: number | null = null;
      const stringEquals: string[] = [];

      let fieldLabel = fieldLabelMap[field];
      if(fieldLabel == undefined||fieldLabel == null||fieldLabel == "")
        fieldLabel = field;

      for (const filter of fList) {
        // Numeric filters
        if (numericOperators.includes(filter.operator) && typeof filter.value === 'number' || filter.operator === 'between') {
          if (filter.operator === 'between') {
            if (filter.min_value == null || filter.max_value == null) {
              errors.push(`Field "${fieldLabel}" with 'between' operator must have min_value and max_value`);
              continue;
            }
            const minVal = filter.min_value;
            const maxVal = filter.max_value;

            if (minVal > maxVal) {
              errors.push(`Field "${fieldLabel}" has invalid 'between' range: min_value (${minVal}) > max_value(${maxVal})`);
              continue;
            }

            effectiveMin = effectiveMin !== null ? Math.max(effectiveMin, minVal) : minVal;
            effectiveMax = effectiveMax !== null ? Math.min(effectiveMax, maxVal) : maxVal;

          } else if (filter.operator === '>=') {
            effectiveMin = effectiveMin !== null ? Math.max(effectiveMin, filter.value as number) : filter.value as number;
          } else if (filter.operator === '>') {
            effectiveMin = effectiveMin !== null ? Math.max(effectiveMin, (filter.value as number) + 0.000001) : (filter.value as number) + 0.000001;
          } else if (filter.operator === '<=') {
            effectiveMax = effectiveMax !== null ? Math.min(effectiveMax, filter.value as number) : filter.value as number;
          } else if (filter.operator === '<') {
            effectiveMax = effectiveMax !== null ? Math.min(effectiveMax, (filter.value as number) - 0.000001) : (filter.value as number) - 0.000001;
          } else if (filter.operator === '=') {
            const val = filter.value as number;
            if ((effectiveMin !== null && val < effectiveMin) || (effectiveMax !== null && val > effectiveMax)) {
              errors.push(`Field "${fieldLabel}" has '=' value ${val} conflicting with existing numeric filters`);
            }
            effectiveMin = effectiveMax = val;
          }

          // Check conflict
          if (effectiveMin !== null && effectiveMax !== null && effectiveMin > effectiveMax) {
            errors.push(`Field "${fieldLabel}" has conflicting numeric filters: effectiveMin ${effectiveMin} > effectiveMax ${effectiveMax}`);
          }

        // String filters
        } else if (stringOperators.includes(filter.operator) && typeof filter.value === 'string') {
          if (filter.operator === '=') {
            if (stringEquals.length > 0 && !stringEquals.includes(filter.value as string)) {
              errors.push(`Field "${fieldLabel}" has conflicting string '=' filters: ${stringEquals.join(', ')} vs ${filter.value}`);
            }
            stringEquals.push(filter.value as string);
          }
          // Other string operators like !=, contains, etc. can also be validated if needed
        }
      }
    }

    return errors;
}

  
  // Handle applying filters
  const handleApplyFilters = (newFilters: FilterCriteria[], target: PoolSelectionTarget) => {
    console.log('handleApplyFilters called with filters:', JSON.stringify(newFilters, null, 2));
    
    // Convert from component filter format to hook format
    // commented hvb @ 26/10/2025 we are now using filterToPass array
    //const hookFilterCriteria: Record<string, any> = {};
    


    // Added hvb @ 26/10/2025 bug fix for passing multiple filters over same field
    const filterToPass = newFilters.filter((filter)=>{
        if(filter.enabled)
        {
          // Convert string values to numbers where needed
            let value = filter.value;
            // For fields that should be numeric (like collection_12m), ensure proper type conversion
            if (['collection_12m', 'principal_os_amt', 'dpd', 'total_amt_disb'].includes(filter.field)) {
              // Force numeric conversion for known numeric fields
              if (typeof value === 'string') {
                value = Number(value);
                console.log(`Converting ${filter.field} value to number: ${value}`);
                filter.value = value;
              }
            }
            
            let minValue = filter.min_value;
            if (typeof minValue === 'string' && !isNaN(Number(minValue))) {
              minValue = Number(minValue);
              filter.min_value = minValue;
            }
            
            let maxValue = filter.max_value;
            if (typeof maxValue === 'string' && !isNaN(Number(maxValue))) {
              maxValue = Number(maxValue);
              filter.max_value = maxValue;
            }
            return filter;
        }
    });

    // Testing
    /*const filters: FilterCriteria[] = [
      { field: 'abc', operator: '>=', value: 50, enabled: true },
      { field: 'abc', operator: 'between', min_value: 60, max_value: 70, enabled: true },
      { field: 'name', operator: '=', value: 'John', enabled: true },
      { field: 'name', operator: '=', value: 'Doe', enabled: true },
    ];

    const validationErrors = validateFilters(filters);*/
    const validationErrors = validateFilters(filterToPass);

    if (validationErrors.length > 0) {
      //alert('Filter validation failed:\n' + validationErrors.join('\n'));
      setValidationErrors(validationErrors);
      setErrorModalOpened(true);
      return;
    } else {
      console.log('Filters are valid!');
    }

    // Make sure we're working with number values not strings
    //Commented hvb @ 26/10/2025 code shifted above
    // newFilters.forEach(filter => {
    //   if (filter.enabled) {
    //     // Convert string values to numbers where needed
    //     let value = filter.value;
    //     // For fields that should be numeric (like collection_12m), ensure proper type conversion
    //     if (['collection_12m', 'principal_os_amt', 'dpd', 'total_amt_disb'].includes(filter.field)) {
    //       // Force numeric conversion for known numeric fields
    //       if (typeof value === 'string') {
    //         value = Number(value);
    //         console.log(`Converting ${filter.field} value to number: ${value}`);
    //       }
    //     }
        
    //     let minValue = filter.min_value;
    //     if (typeof minValue === 'string' && !isNaN(Number(minValue))) {
    //       minValue = Number(minValue);
    //     }
        
    //     let maxValue = filter.max_value;
    //     if (typeof maxValue === 'string' && !isNaN(Number(maxValue))) {
    //       maxValue = Number(maxValue);
    //     }
        
    //     hookFilterCriteria[filter.field] = {
    //       operator: filter.operator,
    //       value: value,
    //       ...(minValue !== undefined && { min_value: minValue }),
    //       ...(maxValue !== undefined && { max_value: maxValue })
    //     };
        
    //     console.log(`Filter on '${filter.field}': ${filter.operator} ${value || ''} ${minValue !== undefined ? `min: ${minValue}` : ''} ${maxValue !== undefined ? `max: ${maxValue}` : ''}`);
    //   }
    // });
    
    //console.log('Final hook filter criteria:', JSON.stringify(hookFilterCriteria, null, 2));
    console.log('Final filter criteria:', JSON.stringify(filterToPass, null, 2));

    //Added hvb @ 30/11/2025 for passing to custom bucket page,PENDING: Note. this requires merging with muli-filter bug
    //setAppliedHookFilter(hookFilterCriteria);
    
    // Save filter state
    //Mod hvb @ 26/10/2025
    //setFilters(newFilters);
    setFilters(filterToPass);
    setTarget(target);
    
    // Close the modal
    setFilterModalOpen(false);
    
    // Set loading state for better UX
    setFilterResults({
      totalPoolValue: 0,
      filteredRecordCount: 0,
      selectedSubPoolCount: 0,
      selectedSubPoolValue: 0
    });
    
    // We can't directly clear filteredRecords since it comes from the hook
    // The applyFilters() call below will reset the results
    
    // Update filter criteria in the hook
    //Mod hvb @ 26/10/2025
    /*Object.entries(hookFilterCriteria).forEach(([field, criteria]) => {
      console.log(`Setting filter criterion for '${field}'`);
      // Apply the filter criteria to the hook
      updateFilterCriteria(
        field, 
        // @ts-ignore - we know these properties exist
        criteria.operator, 
        criteria.value, 
        criteria.min_value, 
        criteria.max_value
      );
    });*/

    filterToPass.map((filter)=>{
      console.log(`Setting filter criterion for '${filter.field}'`);
      updateFilterCriteria(filter.field,filter.operator,filter.value,filter.min_value??0,filter.max_value??0);
    });
    
    console.log('Applying filters to API - waiting for results...');
    
    // Apply filters to get filtered records from API
    // This is async and will update filteredRecords when complete
    applyFilters();
    
    // After filtering, optimize selection based on target amount
    setTimeout(() => {
      console.log('Optimizing selection with target amount:', target.maxPoolValue);
      optimizeSelection(target.maxPoolValue, target.sortField);
    }, 1000); // Small delay to let the filter complete first
  };

  // Handle saving filter
  const handleSaveFilter = (name: string, criteria: FilterCriteria[]) => {
    const newSavedFilter = {
      id: `filter-${Date.now()}`,
      name,
      criteria
    };
    
    setSavedFilters([...savedFilters, newSavedFilter]);
    // In a real app, you would save this to the backend
  };
  
  return (
    <Container size="xl" py="md">
      <Group justify="space-between" mb="lg">
        <Title order={2}>Summary Generation</Title>
        <Group>
          <Button 
            leftSection={<IconFilter size="1rem" />} 
            variant="outline" 
            onClick={handleOpenFilterModal}
          >
            Apply Selection Criteria
          </Button>
          <Button 
            leftSection={<IconRefresh size="1rem" />} 
            variant="light" 
            onClick={() => window.location.reload()}
          >
            Refresh Data
          </Button>
        </Group>
      </Group>

      {(datasetsError || summaryError || poolSelectionError) && (
        <Alert icon={<IconInfoCircle size="1rem" />} title="API Error" color="red" mb="md">
          {datasetsError || summaryError?.message || String(poolSelectionError)}
        </Alert>
      )}
      
      {/* Filter Results Summary */}
      {/* Mod hvb @ 12/12/2025 display summaries without filters */}
      <Box mb="md">
        <Paper withBorder p="md" radius="md">
          <Title order={5} mb="sm">Applied Filters</Title>

          <Group gap="xs" mb="md">
            {filters.filter(f => f.enabled).length > 0 ? (
              filters
                .filter(f => f.enabled)
                .map((filter, index) => (
                  <Badge key={index} variant="light">
                    {filter.field} {filter.operator} {filter.value}
                    {filter.min_value !== undefined &&
                      ` (${filter.min_value}-${filter.max_value})`}
                  </Badge>
                ))
            ) : (
              <Text size="sm" c="dimmed">None</Text>
            )}
          </Group>

          {parsedUrlFilters && (
            <Text size="sm" c="dimmed" mb="md">
              Filters imported from Pool Selection page
            </Text>
          )}

          {/* Pool Statistics */}
          {summaryData && (
            <Paper withBorder p="sm" radius="sm" bg="gray.0">
              <SimpleGrid cols={{ base: 2, md: 5 }} spacing="md">
                <div>
                  <Text size="xs" c="dimmed" mb={2}>📦 Total Pool Value</Text>
                  <Text fw={500} size="sm">
                    ₹{summaryData?.total_pos?.toLocaleString('en-IN') || '0'}
                  </Text>
                </div>

                <div>
                  <Text size="xs" c="dimmed" mb={2}>{filters && filters.length > 0 ? "🔍 Filters Matched" : "📦 Total records"}</Text>
                  <Text fw={500} size="sm">
                    {summaryData?.total_acs || 0} records
                  </Text>
                </div>

                <div>
                  <Text size="xs" c="dimmed" mb={2}>🎯 Target Pool Limit</Text>
                  <Text fw={500} size="sm">
                    ₹{target.maxPoolValue.toLocaleString('en-IN')}
                  </Text>
                </div>

                <div>
                  <Text size="xs" c="dimmed" mb={2}>✅ Selected Sub-Pool</Text>
                  <Text fw={500} size="sm">{selectedRecords.length} records</Text>
                </div>

                <div>
                  <Text size="xs" c="dimmed" mb={2}>💰 Sub-Pool Value</Text>
                  <Text fw={500} size="sm">
                    ₹{totalSelectedAmount.toLocaleString('en-IN')}
                  </Text>
                </div>
              </SimpleGrid>

              {/* Collection Summary */}
              <Group mt="md" gap="lg">
                <div>
                  <Text size="xs" c="dimmed">12M Collection</Text>
                  <Text fw={500} c="green">
                    ₹{(summaryData?.total_12m_col ?? 0).toLocaleString('en-IN')}
                  </Text>
                </div>

                <div>
                  <Text size="xs" c="dimmed">Total Collection</Text>
                  <Text fw={500} c="blue">
                    ₹{(summaryData?.totalCollection ?? 0).toLocaleString('en-IN')}
                  </Text>
                </div>
              </Group>
            </Paper>
          )}
        </Paper>
      </Box>

      
      {/* Filter Criteria Modal */}
      <FilterCriteriaModal
        opened={filterModalOpen}
        onClose={handleCloseFilterModal}
        onApply={handleApplyFilters}
        // availableFields={availableFields}
        availableFields={targetFields}
        savedFilters={savedFilters}
        onSaveFilter={handleSaveFilter}
        initialFilters={filters}
        initialTarget={target}
        datasetId={datasetId}
      />

      <FilterErrorModal
        errors={validationErrors}
        opened={errorModalOpened}
        onClose={() => setErrorModalOpened(false)}
      />
      
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
      </Card>
      {/* Commented hvb @ 29/11/2025 to use our new componenet */}
      {/* {summaryLoading ? (
        <Center h={200}>
          <Loader size="lg" />
        </Center>
      ) : !summaryData ? (
        <Paper withBorder p="lg" mb="lg">
          <Center py="xl">
            <Stack align="center" gap="md">
              <Title order={3}>No Summary Data Available</Title>
              <Text c="dimmed" ta="center" maw={500}>
                {summaryError ? 
                  "The summary API endpoint returned a 404 error. This likely means the summary generation functionality needs to be implemented on the backend." :
                  "There is no summary data available for this dataset yet. Click the button below to generate summaries."}
              </Text>
              {!summaryError && (
                <Button mt="md" onClick={() => window.location.reload()}>
                  Generate Summaries
                </Button>
              )}
            </Stack>
          </Center>
        </Paper>
      ) : (
        <>
          {summaryData.writeOffPool && renderSummaryTable(summaryData.writeOffPool, writeOffRows, setWriteOffRows, handleSaveWriteOff, savingWriteOff)}
          {summaryData.dpdSummary && renderSummaryTable(summaryData.dpdSummary, dpdRows, setDpdRows, handleSaveDpd, savingDpd)}
        </>
      )} */}
      {/* Added hvb @ 29/11/2025 for custom bucket page componenet */}
      <Card withBorder p="md" radius="md" mb="lg">
        <ScrollArea>
          {/* Mod hvb @ 08/12/2025 */}
          {/* <CustomBucketSummaryPage datasetId={datasetId as string} pageFilters={appliedHookFilter} fileType={datasetFileType}/> */}
          <CustomBucketSummaryPage datasetId={datasetId as string} pageFilters={filters} fileType={datasetFileType}/>
        </ScrollArea>
      </Card>
    </Container>
  );
}
