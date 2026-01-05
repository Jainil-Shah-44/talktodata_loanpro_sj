import { FilterCriteria } from ".";

export type BucketConfigListItem = {
  id: string;
  name: string;
  summary_type: string;
  is_default?: boolean;

  //Added hvb @ 03/12/2025 for missing info
  dataset_id: string | null;
  target_field: string;
  bucket_config:any[];
  created_at: string;
  updated_at: string;
};

export type BucketSummaryRequest = {
  config_ids?: string[];
  config_types?: string[];
  //Mod hvb @ 08/12/2025 after merging this is array of filtercriteria's
  //filters?: Record<string, any>;
  filters?: FilterCriteria[];
  show_empty_buckets?: boolean;
};

export type BucketRow = {
  label: string;
  count: number;
  POS: number;
  POS_Per: number;
  disbursement_amount: number; 
  POS_Rundown_Per: number;       
  Post_NPA_Coll: number;
  Post_W_Off_Coll: number;
  M6_Collection: number;
  M12_Collection: number;
  total_collection: number;
};

export type BucketSummaryResponse = {
  id: string;
  name: string;
  summary_type: string;
  buckets: BucketRow[];
};

export interface BucketConfigCreate {
  name: string;
  summary_type: string;
  target_field: string;
  bucket_config: any[];
  is_default: boolean;
  target_field_is_json:boolean;
}


export interface BucketConfigUpdate {
  name?: string;
  target_field?: string;
  bucket_config?: any[];
  is_default?: boolean;
  target_field_is_json:boolean;
}