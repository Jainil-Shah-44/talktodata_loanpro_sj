// types/mapping.ts
export type ExtraColumn = {
  source_col: string;
  target_name: string;
};

export type CleanupRule = {
  col: number;
  type: string; // 'dt'|'int'|'float'|'str' etc.
};

export type SheetConfig = {
  id?: number;
  sheet_index: number;
  //alias?: string | null;
  sheet_alias?: string | null;
  header_row: number;
  skip_rows: number;
  cols_to_read?: string | null;
  key_columns?: number[] | null;
  extra?: ExtraColumn[] | null;
  cleanup?: CleanupRule[] | null;
};

export type ColumnMapping = {
  sheet_index: number;
  source_col: string;
  target_column: string;
};

export type Relation = {
  left_sheet: number;
  right_sheet: number;
  left_col: string;
  right_col: string;
  how?: string;
};

export type MappingProfileSummary = {
  id: number;
  name: string;
  description?: string | null;
  file_type?:string | null; //Added hvb @ 02/12/2025 to save file type
  is_global: boolean;
  is_active?: boolean;
  created_by?: number | null;
};

export type FullProfileResponse = {
  id: number;
  name: string;
  description?: string | null;
  file_type?:string | null; //Added hvb @ 02/12/2025 to save file type
  is_global: boolean;
  is_active?: boolean;
  sheets: SheetConfig[];
  column_mappings: ColumnMapping[];
  relations: Relation[];
};

export type ColumnInfo = {
  column_name:string,
  is_compulsory: boolean,
  data_type:string,
  is_json_col:boolean //Added hvb @ 05/12/2025
}

export type updateRespose = {
  id:number,
  ok:boolean
}