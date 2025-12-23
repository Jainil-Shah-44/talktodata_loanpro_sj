import { BucketConfigCreate, BucketConfigListItem, BucketConfigUpdate, BucketSummaryRequest, BucketSummaryResponse } from '../types/custombucket';
import { ColumnInfo } from '../types/mappings';
import apiClient from './client';

export const bucketService = {
    
    list: async (dataset_id:string,signal?: AbortSignal): Promise<BucketConfigListItem[]> => {
        try{
        const res = await apiClient.get<BucketConfigListItem[]>(`/data-bucket/${dataset_id}/bucket-configs`,{signal});
        return res.data;
        }catch (error: any) {
        if (error.code === "ERR_CANCELED") 
            return []; // ignore abort
        
            console.error('API error in list:', error);
        
            // Handle database connection errors
            if (error.isDatabaseError) {
                console.error('Database connection error detected in list:');
                throw new Error(error.friendlyMessage || 'Database connection error');
            }
            
            // Handle other specific errors
            if (error.response?.status === 404) {
                console.error(`Dataset ${dataset_id} not found`);
                throw new Error(`Dataset not found. Please select a valid dataset.`);
            }
            
            throw error;
        }
    },

    getSummaries:async (dataset_id:string,req_data: BucketSummaryRequest,signal?: AbortSignal): Promise<BucketSummaryResponse[]> => {
        try{
        const res = await apiClient.post<BucketSummaryResponse[]>(`/data-bucket/${dataset_id}/bucket-summary`, req_data,{signal});
        return res.data;
        }
        catch (error: any) {
        if (error.code === "ERR_CANCELED") 
            return []; // ignore abort
        
            console.error('API error in getSummaries:', error);
        
            // Handle database connection errors
            if (error.isDatabaseError) {
                console.error('Database connection error detected in getSummaries:');
                throw new Error(error.friendlyMessage || 'Database connection error');
            }
            
            // Handle other specific errors
            if (error.response?.status === 404) {
                console.error(`Dataset ${dataset_id} not found`);
                throw new Error(`Dataset not found. Please select a valid dataset.`);
            }
            
            throw error;
        }
    },

    //Added hvb @ 02/12/2025
    
  create: async (
    datasetId: string,
    payload: BucketConfigCreate
  ): Promise<BucketConfigListItem> => {
    const res = await apiClient.post(
      `/data-bucket/${datasetId}/file-bucket-configs`,
      payload
    );
    return res.data;
  },

  createforFileType: async (
    payload: BucketConfigCreate
  ): Promise<BucketConfigListItem> => {
    const res = await apiClient.post(
      `/data-bucket/default-bucket-configs`,
      payload
    );
    return res.data;
  },

  update: async (
    configId: string,
    payload: BucketConfigUpdate
  ): Promise<BucketConfigListItem> => {
    const res = await apiClient.put(
      `/data-bucket/bucket-configs/${configId}`,
      payload
    );
    return res.data;
  },

  remove: async (configId: string) => {
    return apiClient.delete(`/data-bucket/bucket-configs/${configId}`);
  },

  checkExists: async (datasetId: string, summaryType: string, targetField: string) => {
    const res = await apiClient.get(`/data-bucket/${datasetId}/check-config`, {
      params: { summaryType, targetField }
    });
    return res.data.exists; // boolean
  },

  fetchByScope: async (datasetIdOrNull: string | null, summaryType: string, targetField: string) => {
    const res = await apiClient.get("/data-bucket/lookup-config", {
      params: {
        dataset_id: datasetIdOrNull,
        summary_type: summaryType,
        target_field: targetField,
      },
    });
    return res.data; // { id, ... } OR null
  },

  getSummaryFields:async (dataset_id:string,signal?: AbortSignal): Promise<ColumnInfo[]> => {
        try{
        const res = await apiClient.get<ColumnInfo[]>(`/data-bucket/${dataset_id}/fields-list`,{signal});
        return res.data;
        }
        catch (error: any) {
        if (error.code === "ERR_CANCELED") 
            return []; // ignore abort
        
            console.error('API error in getSummaries:', error);
        
            // Handle database connection errors
            if (error.isDatabaseError) {
                console.error('Database connection error detected in getSummaries:');
                throw new Error(error.friendlyMessage || 'Database connection error');
            }
            
            // Handle other specific errors
            if (error.response?.status === 404) {
                console.error(`Dataset ${dataset_id} not found`);
                throw new Error(`Dataset not found. Please select a valid dataset.`);
            }
            
            throw error;
        }
    },

    //added by jainil @22-12-25

exportExcel: async (
  datasetId: string,
  payload: BucketSummaryRequest
): Promise<Blob> => {
  const cleanPayload: BucketSummaryRequest = {
    config_ids:
      payload.config_ids && payload.config_ids.length > 0
        ? payload.config_ids
        : undefined,

    config_types:
      payload.config_types && payload.config_types.length > 0
        ? payload.config_types
        : undefined,

    filters:
      Array.isArray(payload.filters) && payload.filters.length > 0
        ? payload.filters
        : undefined,

    show_empty_buckets: payload.show_empty_buckets ?? true,
  };

  const res = await apiClient.post(
    `/data-bucket/${datasetId}/export-bucket-summaries`,
    cleanPayload,
    { responseType: "blob" }
  );

  return res.data;
},


}