import { ColumnStatRequest, ColumnStatsResponse } from '../types/fieldsService';
import apiClient from './client';

export const fieldsService = {
    stats: async (req_data:ColumnStatRequest,signal?: AbortSignal): Promise<ColumnStatsResponse|undefined> => {
        try{
        const res = await apiClient.post<ColumnStatsResponse>(`/fields-mgmt/field-stats-loan`,req_data,{signal});
        return res.data;
        }
        catch (error: any) {
        if (error.code === "ERR_CANCELED") 
            return undefined; // ignore abort
        
            console.error('API error in list:', error);
        
            // Handle database connection errors
            if (error.isDatabaseError) {
                console.error('Database connection error detected in list:');
                throw new Error(error.friendlyMessage || 'Database connection error');
            }
            
            // Handle other specific errors
            if (error.response?.status === 404) {
                console.error(`Dataset ${req_data.pk_id} not found`);
                throw new Error(`Dataset not found. Please select a valid dataset.`);
            }
            
            throw error;
        }
    },
}