import pandas as pd
import io


def read_excel_skip_blank_headers(excel_bytes, sheet_name, preview_rows=5):
    # Step 1: Create ExcelFile for efficient access
    excel_file = pd.ExcelFile(io.BytesIO(excel_bytes))

    # Step 2: Read first few rows only to detect header row
    preview = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=preview_rows, header=None)

    header_row = None
    for i, row in preview.iterrows():
        # If this row has at least 1 non-empty cell, treat it as header
        if row.notna().sum() > 0:
            header_row = i
            break

    # Default to first row if all are blank
    header_row = header_row if header_row is not None else 0

    # Step 3: Re-read the sheet using that header row
    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)

    return df
