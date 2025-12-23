import { useState, useCallback } from 'react';
import apiClient from '../src/api/client';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface FilterCriteria {
  field: string;
  operator: string;
  value: number | string | null;
  min_value?: number;
  max_value?: number;
}

interface PoolSelectionCriteria {
  [key: string]: {
    operator: string;
    value: number | string | null;
    min_value?: number;
    max_value?: number;
  };
}

interface LoanRecord {
  id: string;
  account_number: string;
  customer_name: string;
  principal_os_amt: number;
  total_amt_disb: number;
  dpd: number;
  collection_12m: number;
  state: string;
  product_type: string;
  [key: string]: any;
}

interface PoolSelection {
  id: number;
  name: string;
  description?: string;
  dataset_id: string;
  total_amount: number;
  account_count: number;
  created_at: string;
}

interface FilterResponse {
  success: boolean;
  filtered_count: number;
  total_principal: number;
  records: LoanRecord[];
}

interface OptimizeResponse {
  success: boolean;
  target_amount: number;
  selected_amount: number;
  difference: number;
  selected_count: number;
  optimization_field: string;
  selected_records: LoanRecord[];
}

interface SaveSelectionResponse {
  success: boolean;
  pool_id: number;
  name: string;
  total_amount: number;
  account_count: number;
}

export function usePoolSelection(datasetId: string | null) {
  const [filteredRecords, setFilteredRecords] = useState<LoanRecord[]>([]);
  const [selectedRecords, setSelectedRecords] = useState<LoanRecord[]>([]);
  const [filterCriteria, setFilterCriteria] = useState<PoolSelectionCriteria>({
    // Default criteria based on actual data values
    collection_12m: { operator: ">=", value: 5000.00 }, // Set to near average value
    dpd: { operator: "between", value: null, min_value: 360, max_value: 370 } // All records have DPD=364
  });
  
  const queryClient = useQueryClient();

  // Filter loan records based on criteria
  const filterMutation = useMutation({
    mutationFn: async (criteria: PoolSelectionCriteria) => {
      if (!datasetId) throw new Error('Dataset ID is required');
      
      console.log('===== FILTER REQUEST =====');
      console.log('Dataset ID:', datasetId);
      console.log('Sending filter request with criteria:', JSON.stringify(criteria, null, 2));
      
      // Validate each field in criteria
      Object.entries(criteria).forEach(([field, condition]) => {
        console.log(`Filter field '${field}':`, JSON.stringify(condition));
        if (field === 'dpd') {
          console.log('⚠️ USING DPD FIELD - Will be mapped to dpd_as_per_string in backend');
        }
        
        // Check for potential issues with value types
        if (condition.value !== null) {
          console.log(`  Value type: ${typeof condition.value}`);
          if (typeof condition.value === 'string' && !isNaN(Number(condition.value))) {
            console.log(`  ⚠️ Warning: String value that could be numeric: '${condition.value}'`);
          }
        }
      });
      
      try {
        // Make sure to use the same URL pattern as registered in backend
        // The router uses /api/pool-selection prefix
        const response = await apiClient.post<FilterResponse>(
          `/pool-selection/filter?dataset_id=${datasetId}`,
          criteria
        );
        
        console.log('===== FILTER RESPONSE =====');
        console.log(`Success: ${response.data.success}`);
        console.log(`Filtered count: ${response.data.filtered_count}`);
        console.log(`Total principal: ${response.data.total_principal}`);
        console.log(`Records returned: ${response.data.records?.length || 0}`);
        
        if (response.data.records && response.data.records.length > 0) {
          console.log('First record example:', response.data.records[0]);
          // Check if records have the expected fields
          const sampleRecord = response.data.records[0];
          console.log('DPD value in first record:', sampleRecord.dpd);
          console.log('Principal OS value in first record:', sampleRecord.principal_os_amt);
          console.log('Collection 12m value in first record:', sampleRecord.collection_12m);
        } else {
          console.log('⚠️ No records returned from filter API');
        }
        
        return response.data;
      } catch (error) {
        console.error('Error in filter API call:', error);
        throw error;
      }
    },
    onSuccess: (data) => {
      console.log(`Setting filtered records: ${data.records?.length || 0} items with total principal: ${data.total_principal}`);
      
      // Log detailed record info to help diagnose issues
      if (data.records && data.records.length > 0) {
        console.log(`DPD values in records:`, data.records.map(r => r.dpd).slice(0, 10));
        console.log(`Collection values in records:`, data.records.map(r => r.collection_12m).slice(0, 10));
        console.log(`First 3 records:`, JSON.stringify(data.records.slice(0, 3), null, 2));
        
        // Check for duplicate records that might be causing issues
        const accountNumbers = data.records.map(r => r.account_number);
        const uniqueAccountNumbers = new Set(accountNumbers);
        console.log(`Total records: ${data.records.length}, Unique account numbers: ${uniqueAccountNumbers.size}`);
        
        if (data.records.length !== uniqueAccountNumbers.size) {
          console.warn('⚠️ Warning: Duplicate account numbers detected in filtered records');
          
          // Remove duplicates to fix the filtering issue
          const uniqueRecords = [];
          const seen = new Set();
          
          for (const record of data.records) {
            if (!seen.has(record.account_number)) {
              seen.add(record.account_number);
              uniqueRecords.push(record);
            }
          }
          
          console.log(`After removing duplicates: ${uniqueRecords.length} records`);
          setFilteredRecords(uniqueRecords);
        } else {
          // No duplicates found, set records as normal
          setFilteredRecords(data.records);
        }
      } else {
        setFilteredRecords([]);
      }
      
      // Validate that we have records and they have the proper fields
      if (data.records && data.records.length > 0) {
        const hasDpd = data.records.some(r => r.dpd !== undefined && r.dpd !== null);
        const hasPrincipal = data.records.some(r => r.principal_os_amt !== undefined && r.principal_os_amt !== null);
        const hasCollection = data.records.some(r => r.collection_12m !== undefined && r.collection_12m !== null);
        
        console.log('Records validation:');
        console.log(`- Has DPD values: ${hasDpd}`);
        console.log(`- Has Principal values: ${hasPrincipal}`);
        console.log(`- Has Collection values: ${hasCollection}`);
        
        if (!hasDpd) console.warn('⚠️ Missing DPD values in filtered records');
        if (!hasPrincipal) console.warn('⚠️ Missing Principal values in filtered records');
        if (!hasCollection) console.warn('⚠️ Missing Collection values in filtered records');
      }
    },
    onError: (error) => {
      console.error('Filter mutation error:', error);
      setFilteredRecords([]);
    }
  });

  // Optimize selection to reach target amount
  const optimizeMutation = useMutation({
    mutationFn: async ({ 
      targetAmount, 
      optimizationField 
    }: { 
      targetAmount: number, 
      optimizationField: string 
    }) => {
      if (!datasetId) throw new Error('Dataset ID is required');
      
      const response = await apiClient.post<OptimizeResponse>(
        `/pool-selection/optimize?dataset_id=${datasetId}`,
        {
          target_amount: targetAmount,
          filter_criteria: filterCriteria,
          optimization_field: optimizationField,
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      setSelectedRecords(data.selected_records || []);
    },
  });

  // Save pool selection
  const saveMutation = useMutation({
    mutationFn: async ({ 
      name, 
      description 
    }: { 
      name: string, 
      description?: string 
    }) => {
      if (!datasetId) throw new Error('Dataset ID is required');
      if (selectedRecords.length === 0) throw new Error('No records selected');
      
      const response = await apiClient.post<SaveSelectionResponse>(
        `/pool-selection/save?dataset_id=${datasetId}`,
        {
          name,
          description,
          records: selectedRecords,
        }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['poolSelections', datasetId] });
    },
  });

  // Get saved selections
  const { data: savedSelections, isLoading: isLoadingSaved } = useQuery({
    queryKey: ['poolSelections', datasetId],
    queryFn: async () => {
      if (!datasetId) return { selections: [] };
      
      const response = await apiClient.get(
        `/pool-selection/list?dataset_id=${datasetId}`
      );
      return response.data;
    },
    enabled: !!datasetId,
  });

  // Get specific selection
  const getSelection = useCallback(async (selectionId: number) => {
    if (!datasetId) throw new Error('Dataset ID is required');
    
    const response = await apiClient.get(
      `/pool-selection/${selectionId}`
    );
    return response.data;
  }, [datasetId]);

  // Update filter criteria
  const updateFilterCriteria = useCallback((field: string, operator: string, value: any, min_value?: number, max_value?: number) => {
    setFilterCriteria(prev => ({
      ...prev,
      [field]: { 
        operator, 
        value,
        ...(min_value !== undefined && { min_value }),
        ...(max_value !== undefined && { max_value }),
      },
    }));
  }, []);

  // Apply filters
  const applyFilters = useCallback(() => {
    filterMutation.mutate(filterCriteria);
  }, [filterCriteria, filterMutation]);

  // Optimize selection
  const optimizeSelection = useCallback((targetAmount: number, optimizationField: string = 'collection_12m') => {
    optimizeMutation.mutate({ targetAmount, optimizationField });
  }, [optimizeMutation]);

  // Save selection
  const saveSelection = useCallback((name: string, description?: string) => {
    saveMutation.mutate({ name, description });
  }, [saveMutation]);

  return {
    filteredRecords,
    selectedRecords,
    filterCriteria,
    updateFilterCriteria,
    applyFilters,
    optimizeSelection,
    saveSelection,
    getSelection,
    savedSelections: savedSelections?.selections || [],
    isFiltering: filterMutation.isPending,
    isOptimizing: optimizeMutation.isPending,
    isSaving: saveMutation.isPending,
    isLoadingSaved,
    filterError: filterMutation.error,
    optimizeError: optimizeMutation.error,
    saveError: saveMutation.error,
    totalFilteredAmount: filteredRecords.reduce((sum, record) => sum + (record.principal_os_amt || 0), 0),
    totalSelectedAmount: selectedRecords.reduce((sum, record) => sum + (record.principal_os_amt || 0), 0),
    filteredCount: filteredRecords.length,
    selectedCount: selectedRecords.length,
  };
}
