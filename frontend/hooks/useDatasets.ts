'use client';

import { useState, useEffect } from 'react';
import { datasetService } from '@/src/api/services';
import { Dataset } from '@/src/types';

export function useDatasets() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        setLoading(true);
        // Check if we have an auth token
        const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
        
        if (!token) {
          throw new Error('No authentication token found. Please log in.');
        }
        
        const data = await datasetService.getDatasets();
        setDatasets(data);
        setError(null);
      } catch (err: any) {
        console.error('Error fetching datasets:', err);
        setError(err.message || 'Failed to fetch datasets');
        
        // Only use mock data if specifically requested or during development
        if (process.env.NODE_ENV === 'development') {
          console.log('Using mock data for development');
          // Don't override real data if we have it
          if (datasets.length === 0) {
            setDatasets([
              {
                id: '1',
                user_id: '00000000-0000-0000-0000-000000000000',
                name: 'Loan Portfolio Q1 2025',
                description: 'First quarter loan data',
                file_name: 'loan_portfolio_q1_2025.csv',
                file_size: 2500000,
                total_records: 1250,
                upload_date: '2025-01-15T10:30:00Z',
                status: 'validated'
              },
              {
                id: '2',
                user_id: '00000000-0000-0000-0000-000000000000',
                name: 'Loan Portfolio Q2 2025',
                description: 'Second quarter loan data',
                file_name: 'loan_portfolio_q2_2025.csv',
                file_size: 2800000,
                total_records: 1420,
                upload_date: '2025-04-10T14:20:00Z',
                status: 'uploaded'
              }
            ]);
          }
        }
      } finally {
        setLoading(false);
      }
    };

    fetchDatasets();
  }, []);

  return { datasets, loading, error };
}
