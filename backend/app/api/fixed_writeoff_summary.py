import math

def generate_writeoff_pool_summary(loan_records, pos_buckets=None):
    """Generate a summary table for the Write-Off Pool."""
    print("\n==== STARTING WRITE-OFF POOL SUMMARY GENERATION ====\n*******START HERE ******")
    if loan_records:
        print("DEBUG: First record fields:", dir(loan_records[0]))
        print("DEBUG: First record as dict:", vars(loan_records[0]))
    
    # Define POS buckets
    if pos_buckets is None:
        pos_buckets = [
            (0, 1000, "0 to 1000"),
            (1000, 10000, "1000 to 10000"),
            (10000, 25000, "10000 to 25000"),
            (25000, 50000, "25000 to 50000"),
            (50000, 75000, "50000 to 75000"),
            (75000, 200000, "75000 to 200000"),
            (200000, 500000, "200000 to 500000"),
            (500000, 1000000, "500000 to 1000000"),
            (1000000, 9999999999, "1000000 to +")
        ]
    print("Defined POS buckets", pos_buckets)
    
    # No fallback values - we'll only use real data
    
    # Initialize buckets with 0 values
    bucket_data = {}
    for lower, upper, name in pos_buckets:
        bucket_data[name] = {
            "bucket": name,
            "lowerBound": lower,
            "upperBound": upper,
            "noOfAccs": 0,
            "pos": 0,
            "percentOfPos": 0,
            "3mCol": 0.0,
            "6mCol": 0.0,
            "12mCol": 0.0,
            "totalCollection": 0.0
        }
        print(f"Initialized bucket {lower} to {upper if upper != 9999999999 else '+'}")
    
    # Add a Grand Total row
    bucket_data["Grand Total"] = {
        "bucket": "Grand Total",
        "lowerBound": 0,
        "upperBound": 0,
        "noOfAccs": 0,
        "pos": 0,
        "percentOfPos": 0,
        "3mCol": 0.0,
        "6mCol": 0.0,
        "12mCol": 0.0,
        "totalCollection": 0.0
    }
    print("Initialized Grand Total")
    
    # Check if we have loan records to process
    if not loan_records or len(loan_records) == 0:
        print("No loan records found, returning empty buckets")
        
        # Create the result list with empty values
        result = []
        for lower, upper, name in pos_buckets:
            result.append(bucket_data[name])
        result.append(bucket_data["Grand Total"])
        
        # Create and return the summary table
        summary_table = {
            "id": "writeOffPool",
            "title": "Write-Off Pool Summary",
            "description": "Summary of loan records by POS buckets",
            "columns": [
                {"key": "bucket", "title": "Bucket"},
                {"key": "noOfAccs", "title": "No. of Accounts"},
                {"key": "pos", "title": "POS (in Rs.)"},
                {"key": "percentOfPos", "title": "% of POS"},
                {"key": "3mCol", "title": "3M Col"},
                {"key": "6mCol", "title": "6M Col"},
                {"key": "12mCol", "title": "12M Col"},
                {"key": "totalCollection", "title": "Total Collection"}
            ],
            "rows": result
        }
        
        print("\n==== Final Write-Off Pool Summary Result ====\n")
        print(f"Number of rows: {len(result)}")
        print(f"Number of columns: {len(summary_table['columns'])}")
        print(f"Column keys: {[col['key'] for col in summary_table['columns']]}")
        print(f"Write-Off Pool summary generated with {len(result)} rows")
        
        return summary_table
    
    # Process loan records for account counts, POS values, and collection values
    print(f"Processing {len(loan_records)} loan records for summary calculation")
    
    # Print sample collection values from the first few records
    for i, record in enumerate(loan_records[:5]):
        try:
            # Safely get collection values
            m3 = 0
            m6 = 0
            m12 = 0
            total = 0
            
            if hasattr(record, 'm3_collection'):
                m3 = float(record.m3_collection or 0)
            if hasattr(record, 'm6_collection'):
                m6 = float(record.m6_collection or 0)
            if hasattr(record, 'm12_collection'):
                m12 = float(record.m12_collection or 0)
            if hasattr(record, 'total_collection'):
                total = float(record.total_collection or 0)
                
            print(f"Record {i+1} collection values: m3={m3:.2f}, m6={m6:.2f}, m12={m12:.2f}, total={total:.2f}")
        except Exception as e:
            print(f"Error getting collection values for record {i+1}: {e}")
    
    # Explanation of collection periods
    print("Collection periods explanation:")
    print("- 3M Col: Collections made within 3 months after NPA date")
    print("- 6M Col: Collections made within 6 months after NPA date")
    print("- 12M Col: Collections made within 12 months after NPA date")
    print("- Total Collection: All collections made after NPA date")
    print("Reference date for NPA is typically the date_of_npa field in the loan records")
    print("For this dataset, the reference date is 31/01/2025")
    
    # Debug: Print some sample records to see what collection values are available
    print("\n==== Sample Records Collection Values ====\n")
    for i, record in enumerate(loan_records[:5]):
        if hasattr(record, 'id'):
            print(f"Record ID: {record.id}")
        if hasattr(record, 'principal_os_amt'):
            print(f"  principal_os_amt: {record.principal_os_amt}")
        if hasattr(record, 'm3_collection'):
            print(f"  m3_collection: {record.m3_collection}")
        if hasattr(record, 'm6_collection'):
            print(f"  m6_collection: {record.m6_collection}")
        if hasattr(record, 'm12_collection'):
            print(f"  m12_collection: {record.m12_collection}")
        if hasattr(record, 'total_collection'):
            print(f"  total_collection: {record.total_collection}")
        print("---")
    print("\n==== End Sample Records ====\n")
    
    # Process loan records for account counts, POS values, and collection values
    total_pos = 0
    total_3m_col = 0.0
    total_6m_col = 0.0
    total_12m_col = 0.0
    total_collection = 0.0
    
    for record in loan_records:
        try:
            # Get the POS value (principal outstanding) - safely handle missing attributes
            pos = 0
            if hasattr(record, 'principal_os_amt') and record.principal_os_amt is not None:
                try:
                    pos = float(record.principal_os_amt)
                except (ValueError, TypeError):
                  #  print(f"Error converting principal_os_amt: {record.principal_os_amt}")
                    pos = 0
            elif hasattr(record, 'pos_amount') and record.pos_amount is not None:
                try:
                    pos = float(record.pos_amount)
                except (ValueError, TypeError):
                    print(f"Error converting pos_amount: {record.pos_amount}")
                    pos = 0
            else:
                # If no POS field is found, skip this record
                print(f"No POS value found for record {record.id if hasattr(record, 'id') else 'unknown'}, skipping")
                continue
                
            # Get collection values with safe conversion to float
            m3_col = 0.0
            m6_col = 0.0
            m12_col = 0.0
            total_col = 0.0
            
            if hasattr(record, 'm3_collection') and record.m3_collection is not None:
                try:
                    m3_col = float(record.m3_collection)
                   # print(f"Found m3_collection: {m3_col} for record {record.id if hasattr(record, 'id') else 'unknown'}")
                except (ValueError, TypeError):
                    print(f"Error converting m3_collection: {record.m3_collection}")
                    m3_col = 0.0
            
            if hasattr(record, 'm6_collection') and record.m6_collection is not None:
                try:
                    m6_col = float(record.m6_collection)
                   # print(f"Found m6_collection: {m6_col} for record {record.id if hasattr(record, 'id') else 'unknown'}")
                except (ValueError, TypeError):
                    print(f"Error converting m6_collection: {record.m6_collection}")
                    m6_col = 0.0
            
            if hasattr(record, 'm12_collection') and record.m12_collection is not None:
                try:
                    m12_col = float(record.m12_collection)
                    print(f"Found m12_collection: {m12_col} for record {record.id if hasattr(record, 'id') else 'unknown'}")
                except (ValueError, TypeError):
                    print(f"Error converting m12_collection: {record.m12_collection}")
                    m12_col = 0.0
            
            if hasattr(record, 'total_collection') and record.total_collection is not None:
                try:
                    total_col = float(record.total_collection)
                   # print(f"Found total_collection: {total_col} for record {record.id if hasattr(record, 'id') else 'unknown'}")
                except (ValueError, TypeError):
                    print(f"Error converting total_collection: {record.total_collection}")
                    total_col = 0.0
        except Exception as e:
            print(f"Error processing record: {e}")
            continue
        
        # Add to totals
        total_pos += pos
        total_3m_col += m3_col
        total_6m_col += m6_col
        total_12m_col += m12_col
        total_collection += total_col
        
        # Find the appropriate bucket
        bucket_name = None
        for lower, upper, name in pos_buckets:
            if lower <= pos < upper:
                bucket_name = name
                break
        
        if bucket_name:
            # Update bucket data
            bucket_data[bucket_name]["noOfAccs"] += 1
            bucket_data[bucket_name]["pos"] += pos
            # Add collection values without dividing by 1,000,000 to show actual values
            bucket_data[bucket_name]["3mCol"] += m3_col
            bucket_data[bucket_name]["6mCol"] += m6_col
            bucket_data[bucket_name]["12mCol"] += m12_col
            bucket_data[bucket_name]["totalCollection"] += total_col       
        # Add to Grand Total
        bucket_data["Grand Total"]["noOfAccs"] += 1
        bucket_data["Grand Total"]["pos"] += pos
        
        # Debug output for collection values
        if m3_col > 0 or m6_col > 0 or m12_col > 0 or total_col > 0:
            print(f"Record {record.id if hasattr(record, 'id') else 'unknown'} has collection values: m3={m3_col}, m6={m6_col}, m12={m12_col}, total={total_col}")
    
    # Update Grand Total collection values
    bucket_data["Grand Total"]["3mCol"] = total_3m_col
    bucket_data["Grand Total"]["6mCol"] = total_6m_col
    bucket_data["Grand Total"]["12mCol"] = total_12m_col
    bucket_data["Grand Total"]["totalCollection"] = total_collection
    
    # Log collection values for debugging
    print(f"Total 3M Collection: {total_3m_col}")
    print(f"Total 6M Collection: {total_6m_col}")
    print(f"Total 12M Collection: {total_12m_col}")
    print(f"Total Collection: {total_collection}")
    
    # Ensure all float values are JSON serializable and properly formatted for frontend
    for bucket_name, bucket in bucket_data.items():
        for key, value in bucket.items():
            # Handle NaN or infinity values
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                bucket[key] = 0.0  # Replace non-JSON-serializable floats with 0.0
            # Remove string conversion for collection values; keep as float
            if key in ['3mCol', '6mCol', '12mCol', 'totalCollection']:
                bucket[key] = float(value)
            elif isinstance(value, float):
                # Round other float values to 2 decimal places
                bucket[key] = round(value, 2)
    
    print(f"Processed {len(loan_records)} loan records")
    print(f"Total POS: {total_pos}")
    print(f"Total 3M Collection: {total_3m_col}")
    print(f"Total 6M Collection: {total_6m_col}")
    print(f"Total 12M Collection: {total_12m_col}")
    print(f"Total Collection: {total_collection}")
    
    # Calculate percentages
    if total_pos > 0:
        for bucket in bucket_data.values():
            bucket["percentOfPos"] = (bucket["pos"] / total_pos) * 100
    
    # Convert to list and sort by lowerBound
    result = []
    for lower, upper, name in pos_buckets:
        bucket = bucket_data[name]
        # Ensure all required keys are present in each row
        for col in ['3mCol', '6mCol', '12mCol', 'totalCollection']:
            if col not in bucket:
                bucket[col] = 0.0
        result.append(bucket)
        # Print debug info for each bucket
        print(f"Row data for bucket {lower} to {upper if upper != 9999999999 else '+'}:")
        print(f"  3mCol: {bucket['3mCol']} (type: {type(bucket['3mCol'])})")
        print(f"  6mCol: {bucket['6mCol']} (type: {type(bucket['6mCol'])})")
        print(f"  12mCol: {bucket['12mCol']} (type: {type(bucket['12mCol'])})")
    # Add Grand Total row to the result
    grand_total = bucket_data["Grand Total"]
    for col in ['3mCol', '6mCol', '12mCol', 'totalCollection']:
        if col not in grand_total:
            grand_total[col] = 0.0
    result.append(grand_total)
    
    # Create and return the summary table
    summary_table = {
        "id": "writeOffPool",
        "title": "Write-Off Pool Summary",
        "description": "Summary of loan records by POS buckets",
        "columns": [
            {"key": "bucket", "title": "Bucket"},
            {"key": "noOfAccs", "title": "No. of Accounts"},
            {"key": "pos", "title": "POS (in Rs.)"},
            {"key": "percentOfPos", "title": "% of POS"},
            {"key": "3mCol", "title": "3M Col"},
            {"key": "6mCol", "title": "6M Col"},
            {"key": "12mCol", "title": "12M Col"},
            {"key": "totalCollection", "title": "Total Collection"}
        ],
        "rows": result
    }
    
    print("\n==== Final Write-Off Pool Summary Result ====\n")
    print(f"Number of rows: {len(result)}")
    print(f"Number of columns: {len(summary_table['columns'])}")
    print(f"Column keys: {[col['key'] for col in summary_table['columns']]}")
    print(f"Write-Off Pool summary generated with {len(result)} rows")
    
    # Debug the final result
    print("\n==== Debug Write-Off Pool Summary ====\n")
    for i, row in enumerate(result):
        print(f"Row {i+1} - Bucket: {row['bucket']}")
        print(f"  3M Col: {row['3mCol']}")
        print(f"  6M Col: {row['6mCol']}")
        print(f"  12M Col: {row['12mCol']}")
        print(f"  Total Collection: {row['totalCollection']}")
        print("---")
    print("\n==== End Debug Write-Off Pool Summary ====\n****** END HERE ******")
    
    return summary_table
