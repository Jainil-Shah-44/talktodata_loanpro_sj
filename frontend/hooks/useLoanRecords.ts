'use client';

import { useState, useEffect } from 'react';
import { loanRecordService } from '@/src/api/services';

export interface LoanRecord {
  id: string;
  dataset_id: string;
  agreement_no?: string;
  principal_os_amt?: number;
  dpd_as_on_31st_jan_2025?: number;
  classification?: string;
  product_type?: string;
  customer_name?: string;
  state?: string;
  bureau_score?: number;
  total_collection?: number;
  created_at?: string;
  updated_at?: string;
  loan_id?: string;
  disbursement_date?: string;
  pos_amount?: number;
  disbursement_amount?: number;
  dpd?: number;
  status?: string;
  has_validation_errors?: boolean;
  validation_error_types?: string[];
  [key: string]: any;
}

interface UseLoanRecordsOptions {
  validationErrorsOnly?: boolean;
  sortField?: string;
  sortDirection?: 'asc' | 'desc';
  filters?: Record<string, any>;
}

export function useLoanRecords(datasetId: string | null, options: UseLoanRecordsOptions = {}) {
  const [records, setRecords] = useState<LoanRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalRecords, setTotalRecords] = useState(0);

  useEffect(() => {
    const fetchRecords = async () => {
      if (!datasetId) {
        setRecords([]);
        setLoading(false);
        console.log('No datasetId provided, not fetching records');
        return;
      }

      console.log(`Fetching records for dataset: ${datasetId}`);
      console.log('Options:', options);

      try {
        setLoading(true);
        
        // Check if we have an auth token
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
        
        if (!token) {
          throw new Error('No authentication token found. Please log in.');
        }
        
        let data;
        
        if (options.validationErrorsOnly) {
          // Fetch only records with validation errors
          console.log('Fetching validation error records');
          data = await loanRecordService.getValidationErrorRecords(datasetId);
        } else {
          // Fetch all records with optional filters
          const params = {
            ...options.filters,
            sort_field: options.sortField,
            sort_direction: options.sortDirection,
          };
          
          console.log('Fetching all records with params:', params);
          data = await loanRecordService.getRecords(datasetId, params);
        }
        
        console.log('API response data:', data);
        
        // Check if data is an array or has a records property
        if (Array.isArray(data)) {
          console.log(`Received ${data.length} records as array`);
          setRecords(data);
          setTotalRecords(data.length);
        } else if (data && data.records) {
          console.log(`Received ${data.records.length} records in data.records`);
          setRecords(data.records);
          setTotalRecords(data.total || data.records.length);
        } else {
          console.log('No records found in response', data);
          setRecords([]);
          setTotalRecords(0);
        }
        
        setError(null);
      } catch (err: any) {
        console.error('Error fetching loan records:', err);
        setError(err.message || 'Failed to fetch loan records');
        
        // No mock data - show empty records when there's an error
        console.log('Error occurred, showing empty records');
        setRecords([]);
        setTotalRecords(0);
      } finally {
        setLoading(false);
      }
    };

    fetchRecords();
  }, [datasetId, options.validationErrorsOnly, options.sortField, options.sortDirection, options.filters]);

  return { records, loading, error, totalRecords };
}
