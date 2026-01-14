import { FilterBase, FilterCriteria } from '../types';
import apiClient from './client';

// Authentication
export const authService = {
  login: async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login-json', { email, password });
    return response.data;
  },
  register: async (userData: any) => {
    const response = await apiClient.post('/auth/register', userData);
    return response.data;
  },
  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};

// Datasets
export const datasetService = {
  getDatasets: async () => {
    const response = await apiClient.get('/datasets');
    return response.data;
  },
  getDatasetById: async (id: string) => {
    const response = await apiClient.get(`/datasets/${id}`);
    return response.data;
  },
  uploadDataset: async (formData: FormData) => {
    const response = await apiClient.post('/datasets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  //Added hvb @ 19/10/2025 for new mapping based upload
  uploadDatasetWithMapping: async (formData: FormData) => {
    const response = await apiClient.post('/datasets/upload-mapped', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  reprocessDataset: async (id: string) => {
    const response = await apiClient.post(`/datasets/${id}/reprocess`);
    return response.data;
  },
  deleteDataset: async (id: string) => {
    const response = await apiClient.delete(`/datasets/${id}`);
    return response.data;
  },
  validateDataset: async (id: string) => {
    const response = await apiClient.post(`/datasets/${id}/validate`);
    return response.data;
  },
  generateSummary: async (id: string, config: any) => {
    const response = await apiClient.post(`/datasets/${id}/summary`, config);
    return response.data;
  },
  //Added hvb @ 05/12/2025
  getDatasetFileType: async (id?: string) => {
  try {
    if (!id) {
    throw new Error("datasetId is required");
    }
    const res = await apiClient.get(
      `/datasets/${id}/dataset-file-type`
    );
    return res.data.file_type;
  } catch (error: any) {
    console.error("Axios error:", {
      message: error.message,
      code: error.code,
      config: error.config,
    });
    throw error;
  }
}

};

// Excel Download of Records
export const recordService = {
  exportExcel: async (datasetId: string): Promise<Blob> => {
  const res = await apiClient.get(
    `/datasets/${datasetId}/records/export`,
    { responseType: "blob" }
  );
  return res.data;
},

};


// Validations
export const validationService = {
  getValidations: async (datasetId: string) => {
    const response = await apiClient.get(`/datasets/${datasetId}/validations`);
    return response.data;
  },
  getValidationErrors: async (datasetId: string, errorType: string) => {
    const response = await apiClient.get(`/datasets/${datasetId}/validation-errors/${errorType}`);
    return response.data;
  },
};

// Summaries
export const summaryService = {
  getSummary: async (datasetId: string) => {
    const url = `/datasets/${datasetId}/summary`;
    // Print the full URL being called (with base URL)
    console.log('[summaryService.getSummary] Calling:', (typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api') : '') + url);
    const response = await apiClient.get(url);
    return response.data;
  },
  getFilteredSummary: async (datasetId: string, filterCriteria: any) => {
    //Mod hvb @ 08/12/2025
    //const url = `/datasets/${datasetId}/summary`;
    const url = `/datasets/${datasetId}/summary-v2`;
    console.log('[summaryService.getFilteredSummary] Calling POST:', (typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api') : '') + url);
    console.log('[summaryService.getFilteredSummary] Filter criteria:', filterCriteria);
    const response = await apiClient.post(url, filterCriteria);
    return response.data;
  },
  updateBuckets: async (datasetId: string, payload: any) => {
    const response = await apiClient.put(`/datasets/${datasetId}/summary/buckets`, payload);
    return response.data;
  },
};

// Filters
export const filterManagementServices = {
  //filters list
  getFilters: async() => {
    try {
      const response = await apiClient.get(`/filters/`);
      console.log('API response:', response);      
      return response.data;
    } catch (error: any) {
      console.error('API error in getFilters:', error);
      throw error;
    }
  },
  getConditions: async(filterId:number) => {
    try {
      const response = await apiClient.get(`/filters/${filterId}`);
      console.log('API response:', response);
      return response.data;
    } catch (error: any) {
      console.error('API error in getFilters:', error);
       // Handle other specific errors
      if (error.response?.status === 404) {
        console.error(`Filter ${filterId} not found`);
        throw new Error(`Filter not found. Please select a valid filter.`);
      }
      throw error;
    }
  },
  createFilter: async(filter:FilterBase) => {
     try {
      console.log('[filterManagementServices.createFilter] Filter data:', filter);
      const response = await apiClient.post(`/filters/`, filter);
      return response;
     } catch (error: any) {
      console.error('API error in createFilters:', error);
       // Handle other specific errors
      if (error.response?.status === 400) {
        console.error(`Filter ${filter.filter_name} already exists`);
        throw new Error(`Specified filter ${filter.filter_name} already exists.Try setting other name or click update!`);
      }
      throw error;
    }
  },
  deleteFilter: async(filterId:number) => {
     try {
      const response = await apiClient.delete(`/filters/${filterId}`);
      return response.data;
     } catch (error: any) {
      console.error('API error in deleteFilter:', error);
       // Handle other specific errors
      if (error.response?.status === 404) {
        console.error(`Filter not found`);
        throw new Error(`Filter not found, it could have been already removed`);
      }
      throw error;
    }
  },
  markLastUsedFilter: async (filterId:number) => {
    try{
    const response = await apiClient.put(`/filters/${filterId}/last_used`);
    return response.data;
    } catch (error: any) {
      console.error('API error in markLastUsedFilter:', error);
       // Handle other specific errors
      if (error.response?.status === 404) {
        console.error(`Filter not found`);
        throw new Error(`Filter not found, select valid filter`);
      }
      throw error;
    }
  },
  renameFilter: async (filterId:number,newName:string) => {
    try{
    const newNameEncoded = encodeURI(newName)
    const response = await apiClient.put(`/filters/${filterId}/rename?new_name=${newNameEncoded}`);
    return response.data;
    } catch (error: any) {
      console.error('API error in renameFilter:', error);
       // Handle other specific errors
       switch(error.response?.status){
        case 404:
        {
          console.error(`Filter not found`);
          throw new Error(`Invalid filter for rename:not found!`);
        }
        case 400:{
          console.error(`Filter not found`);
          throw new Error(`Another filter with this name exists.`);
        }
        default:
          throw error; 
       }
      throw error;
    }
  },
  updateConditions: async(filterId:number,updatedConditions:FilterCriteria[])=>{
    try{
    console.log('[filterManagementServices.updateConditions] filterId :', filterId);
    console.log('[filterManagementServices.updateConditions] updated conditions :', updatedConditions);

    const response = await apiClient.put(`/filters/${filterId}/conditions`,updatedConditions);
    return response.data;

    } catch (error: any) {
      console.error('API error in updateConditions:', error);
       // Handle other specific errors
      if (error.response?.status === 404) {
        console.error(`Filter not found`);
        throw new Error(`Filter not found, select valid filter`);
      }
      throw error;
    }
  }
};

// Loan Records
export const loanRecordService = {
  getRecords: async (datasetId: string, params?: any) => {
    console.log(`API call: GET /datasets/${datasetId}/records with params:`, params);
    try {
      const response = await apiClient.get(`/datasets/${datasetId}/records`, { params });
      console.log('API response:', response);
      
      // Check if we have empty records but the dataset exists
      if (Array.isArray(response.data) && response.data.length === 0) {
        console.warn(`Dataset ${datasetId} returned 0 records. Fetching debug info...`);
        try {
          // Try to get debug information about the dataset
          const debugResponse = await apiClient.get(`/datasets/${datasetId}/debug_records`);
          console.log('Debug info for empty dataset:', debugResponse.data);
        } catch (debugError) {
          console.error('Failed to fetch debug info:', debugError);
        }
      }
      
      return response.data;
    } catch (error: any) {
      console.error('API error in getRecords:', error);
      
      // Handle database connection errors
      if (error.isDatabaseError) {
        console.error('Database connection error detected in getRecords');
        throw new Error(error.friendlyMessage || 'Database connection error');
      }
      
      // Handle other specific errors
      if (error.response?.status === 404) {
        console.error(`Dataset ${datasetId} not found`);
        throw new Error(`Dataset not found. Please select a valid dataset.`);
      }
      
      throw error;
    }
  },
  getRecordById: async (datasetId: string, recordId: string) => {
    try {
      const response = await apiClient.get(`/datasets/${datasetId}/records/${recordId}`);
      return response.data;
    } catch (error) {
      console.error('API error in getRecordById:', error);
      throw error;
    }
  },
  getValidationErrorRecords: async (datasetId: string) => {
    try {
      const response = await apiClient.get(`/datasets/${datasetId}/records/validation-errors`);
      return response.data;
    } catch (error) {
      console.error('API error in getValidationErrorRecords:', error);
      throw error;
    }
  },
};
