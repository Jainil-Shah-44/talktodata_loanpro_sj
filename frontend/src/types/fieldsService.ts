export interface ColumnStatsResponse {
  type: "distinct" | "range";
  values?: string[];
  min?: number | string | null;
  max?: number | string | null;
}

export interface ColumnStatRequest{
    column_name: string,
    column_type: string,
    is_json_column: boolean,
    pk_id:string
}