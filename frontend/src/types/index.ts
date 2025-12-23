// User types
export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

// Dataset types
export interface Dataset {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  file_name: string;
  file_size?: number;
  file_type?:string; //Added hvb @ 03/12/2025
  total_records?: number;
  upload_date: string;
  status: string;
}

// Loan Record types
export interface LoanRecord {
  id: string;
  dataset_id: string;
  agreement_no: string;
  principal_os_amt?: number;
  dpd_as_on_31st_jan_2025?: number;
  classification?: string;
  product_type?: string;
  customer_name?: string;
  state?: string;
  bureau_score?: number;
  total_collection?: number;
  created_at: string;
  // Additional fields will be added as needed
}

// Validation types
export interface ValidationResult {
  id: string;
  dataset_id: string;
  validation_date: string;
  total_records: number;
  valid_records: number;
  invalid_records: number;
  validation_summary: ValidationSummary;
}

export interface ValidationSummary {
  pos_disbursement_check: number;
  dpd_consistency_check: number;
  date_consistency_check: number;
  tenor_calculation_check: number;
  classification_verification: number;
}

export interface ValidationError {
  id: string;
  validation_id: string;
  loan_record_id: string;
  error_type: string;
  error_message: string;
  created_at: string;
}

// Summary types
export interface SummaryConfig {
  id: string;
  dataset_id: string;
  user_id: string;
  name: string;
  bucket_type: string;
  buckets: Bucket[];
  created_at: string;
}

export interface Bucket {
  id: string;
  name: string;
  min_value: number;
  max_value: number;
}

export interface SummaryResult {
  id: string;
  summary_config_id: string;
  dataset_id: string;
  generation_date: string;
  results: BucketResult[];
}

export interface BucketResult {
  bucket_id: string;
  bucket_name: string;
  count: number;
  sum: number;
  percentage: number;
}

//Added hvb @ 27/10/2025 for processing filter management
export interface FilterBase {
  id: number;
  filter_name: string;
  join_type: "AND" | "OR";
  last_used: boolean;
  created_at: string;
  updated_at: string;
  conditions: FilterCriteria[]
}

export interface FilterCriteria {
  field: string;
  operator: string;
  value?: number | string | null;
  min_value?: number | null;
  max_value?: number | null;
  enabled: boolean;
}