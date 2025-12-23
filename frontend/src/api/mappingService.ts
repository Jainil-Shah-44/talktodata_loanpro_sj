// lib/mappingService.ts
import apiClient from './client';

import {
  MappingProfileSummary,
  FullProfileResponse,
  ColumnInfo,
  updateRespose
} from "../types/mappings";

export const mappingService = {
  list: async (): Promise<MappingProfileSummary[]> => {
    const res = await apiClient.get<MappingProfileSummary[]>("/upload-profile");
    return res.data;
  },

  getById: async (id: number): Promise<FullProfileResponse> => {
    const res = await apiClient.get<FullProfileResponse>(`/upload-profile/${id}`);
    return res.data;
  },

  getConfig: async (id: number): Promise<Record<string, unknown>> => {
    const res = await apiClient.get<Record<string, unknown>>(`/upload-profile/${id}/config`);
    return res.data;
  },

  getFields: async(): Promise<ColumnInfo[]> => {
    const res = await apiClient.get<ColumnInfo[]>("/upload-profile/target-fields");
    return res.data;
  },

  //Added hvb @ 02/12/2025
  getFileType: async(): Promise<string[]> => {
    const res = await apiClient.get<string[]>("/upload-profile/file-types");
    return res.data;
  },

  create: async (payload: FullProfileResponse): Promise<FullProfileResponse> => {
    const res = await apiClient.post<FullProfileResponse>("/upload-profile", payload);
    return res.data;
  },

  update: async (id: number, payload: Partial<FullProfileResponse>): Promise<updateRespose> => {
    const res = await apiClient.put(`/upload-profile/${id}`, payload);
    return res.data;
  },

  remove: async (id: number): Promise<void> => {
    const res = await apiClient.delete(`/upload-profile/${id}`);
    return res.data
  },

  removePermenant: async (id: number): Promise<void> => {
    const res = await apiClient.delete(`/upload-profile/${id}/permanent`);
    return res.data;
  }
};
