import * as XLSX from "xlsx";
import { toCrores } from "@/src/utils/numberFormat";

export function exportBucketSummaryToExcel(
  buckets: any[],
  fileName: string
) {
  const rows = buckets.map((b) => ({
    Bucket: b.label,
    Count: b.count,
    "POS (Cr)": toCrores(b.POS),
    "Disbursement (Cr)": toCrores(b.disbursement_amount),
    "POS %": b.POS_Per,
    "POS Rundown %": b.POS_Rundown_Per,
    "Post NPA (Cr)": toCrores(b.Post_NPA_Coll),
    "Post W/OFF (Cr)": toCrores(b.Post_W_Off_Coll),
    "6M Collection (Cr)": toCrores(b.M6_Collection),
    "12M Collection (Cr)": toCrores(b.M12_Collection),
    "Total Collection (Cr)": toCrores(b.total_collection),
  }));

  const worksheet = XLSX.utils.json_to_sheet(rows);
  const workbook = XLSX.utils.book_new();

  XLSX.utils.book_append_sheet(workbook, worksheet, "Bucket Summary");
  XLSX.writeFile(workbook, `${fileName}.xlsx`);
}