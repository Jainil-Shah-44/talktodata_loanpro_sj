// types/mapping-form.ts
import { SheetConfig, ColumnMapping, Relation } from "./mappings";

export type FormValues = {
  name: string;
  description: string | null;
  is_global: boolean;
  file_type?:string; //Added hvb @ 03/12/2025
  sheets: SheetConfig[];
  column_mappings: ColumnMapping[];
  relations: Relation[];
};
