import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { summaryService } from '@/src/api/services';

//Added hvb @ 26/10/2025 we don't want key-val pair we are passing array now.
// import {FilterCriteria as FrontFilterCriteria} from '@/components/FilterCriteriaModal'
import {FilterCriteria as FrontFilterCriteria} from '@/src/types/index';

export interface SummaryTable {
  id: string;
  title: string;
  description?: string;
  columns: {
    key: string;
    title: string;
    format?: (value: any) => string;
  }[];
  rows: Record<string, any>[];
}

export interface SummaryData {
  writeOffPool: SummaryTable;
  dpdSummary: SummaryTable;
  // We'll add more tables as needed
  [key: string]: SummaryTable;
}

interface FilterCriteria {
  [key: string]: {
    operator: string;
    value: number | string | null;
    min_value?: number;
    max_value?: number;
  };
}

const fetchSummaryData = async (datasetId: string, filterCriteria?: FilterCriteria) => {
  try {
    console.log('[useSummaries] Fetching summary for dataset:', datasetId);
    if (filterCriteria) {
      console.log('[useSummaries] Using filter criteria:', filterCriteria);
      return await summaryService.getFilteredSummary(datasetId, filterCriteria);
    } else {
      console.log('[useSummaries] Fetching all records summary');
      return await summaryService.getSummary(datasetId);
    }
  } catch (error) {
    console.error('[useSummaries] Error fetching summary:', error);
    throw error;
  }
};

//Added hvb @ 26/10/2025 for passing array rather than a dictionary
const fetchSummaryDataV2 = async (datasetId: string, filterCriteria?: FrontFilterCriteria[]) => {
  try {
    console.log('[useSummaries] Fetching summary for dataset:', datasetId);
    //Mod hvb @ 08/12/2025 handled in back-end
    /*if (filterCriteria) {
      console.log('[useSummaries] Using filter criteria:', filterCriteria);
      return await summaryService.getFilteredSummary(datasetId, filterCriteria);
    } else {
      console.log('[useSummaries] Fetching all records summary');
      return await summaryService.getSummary(datasetId);
    }*/
   return await summaryService.getFilteredSummary(datasetId, filterCriteria);
  } catch (error) {
    console.error('[useSummaries] Error fetching summary:', error);
    throw error;
  }
};

export function useSummariesV2(datasetId: string | null, filterCriteria?: FrontFilterCriteria[]) {
  return useQuery({
    queryKey: ['summary', datasetId, filterCriteria],
    queryFn: () => {
      if (!datasetId) throw new Error('Dataset ID is required');
      return fetchSummaryDataV2(datasetId, filterCriteria);
    },
    enabled: !!datasetId,
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 1 minute (formerly cacheTime)
  });
}

export function useSummaries(datasetId: string | null, filterCriteria?: FilterCriteria) {
  return useQuery({
    queryKey: ['summary', datasetId, filterCriteria],
    queryFn: () => {
      if (!datasetId) throw new Error('Dataset ID is required');
      return fetchSummaryData(datasetId, filterCriteria);
    },
    enabled: !!datasetId,
    staleTime: 30000, // 30 seconds
    gcTime: 60000, // 1 minute (formerly cacheTime)
  });
}

// No mock data - we'll only use real data from the backend
