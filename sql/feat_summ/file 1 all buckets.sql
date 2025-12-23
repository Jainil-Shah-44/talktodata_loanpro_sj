DO $$
DECLARE
    DS_ID UUID;
    USR_ID UUID;

    -- Record type for bucket config
    rec RECORD;
BEGIN
    --------------------------------------------------------------------
    -- Fetch dataset and user
    --------------------------------------------------------------------
    SELECT id INTO DS_ID
    FROM public.datasets
    WHERE file_name = 'Pool file -  Unsecured NPA  and  Microfinance.xlsx'
      AND status = 'uploaded'
    LIMIT 1;

    SELECT id INTO USR_ID
    FROM public.users
    WHERE is_superuser = true
    LIMIT 1;

    IF DS_ID IS NULL OR USR_ID IS NULL THEN
        RAISE EXCEPTION 'dataset_id not found OR superuser not found';
    END IF;

    --------------------------------------------------------------------
    -- LOOP over all bucket configs
    --------------------------------------------------------------------
    FOR rec IN
        SELECT *
        FROM (
            VALUES
            ----------------------------------------------------------------
            -- 🔵 BUCKET 1: POS BUCKET
            ----------------------------------------------------------------
            (
                'pos_bucket',                     -- summary_type
                'POS Buckets',            		  -- name
                '[
                    {"min": 0, "max": 5000, "label": "0 to 5000"},
	                {"min": 5000, "max": 10000, "label": "5000 to 10000"},
	                {"min": 10000, "max": 15000, "label": "10000 to 15000"},
	                {"min": 15000, "max": 20000, "label": "15000 to 20000"},
	                {"min": 20000, "max": 25000, "label": "20000 to 25000"},
	                {"min": 25000, "max": 30000, "label": "25000 to 30000"},
	                {"min": 30000, "max": 40000, "label": "30000 to 40000"},
	                {"min": 40000, "max": 50000, "label": "40000 to 50000"},
	                {"min": 50000, "max": 70000, "label": "50000 to 70000"},
	                {"min": 70000, "max": 90000, "label": "70000 to 90000"},
	                {"min": 90000, "max": 120000, "label": "90000 to 120000"}
                ]'::jsonb,                        -- bucket_config
                'principal_os_amt',                            -- target_field
                FALSE                             -- target_field_is_json
            ),

            ----------------------------------------------------------------
            -- 🔵 BUCKET 2: DPD Bucket 
            ----------------------------------------------------------------
            (
                'dpd_bucket',
                'DPD Buckets',
                '[
                    {"min": 0, "max": 30, "label": "0 to 30"},
					{"min": 30, "max": 60, "label": "30 to 60"},
					{"min": 60, "max": 90, "label": "60 to 90"},
					{"min": 90, "max": 120, "label": "90 to 120"},
					{"min": 120, "max": 150, "label": "120 to 150"},
					{"min": 150, "max": 180, "label": "150 to 180"}
                ]'::jsonb,
                'dpd',
                FALSE
            ),

            ----------------------------------------------------------------
            -- 🔵 BUCKET 3: Product-Type BUCKET
            ----------------------------------------------------------------
            (
                'prod_type_bucket',
                'Product Type Buckets',
                '[
                    { "values": ["ALL"], "label": "All Products" }
                ]'::jsonb,
                'product_type',
                FALSE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 4: Legal1-Status BUCKET
            ----------------------------------------------------------------
			(
                'legal_status_1_bucket',
                'Legal Status 1 Bucket',
                '[
                    {"values": ["Under Arbitration"], "label": "Under Arbitration"},
			        {"values": ["Sec 138 (2) filed"], "label": "Sec 138 (2) filed"},
			        {"values": ["No action"], "label": "No action"},
					{"values": ["Sec 138 (2) WIP"], "label": "Sec 138 (2) WIP"},
			        {"values": [], "label": "Other actions"}
                ]'::jsonb,
                'arbitration_status',
                FALSE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 5: State BUCKET
            ----------------------------------------------------------------
			(
                'states_bucket',
                'States Bucket',
                '[
                    { "values": ["ALL"], "label": "All States" }
                ]'::jsonb,
                'state',
                FALSE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 6: Classification BUCKET
            ----------------------------------------------------------------
			(
                'classification_bucket',
                'Classification Bucket',
                '[
                    { "values": ["ALL"], "label": "All Classifications" }
                ]'::jsonb,
                'classification',
                FALSE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 7: Citywise BUCKET
            ----------------------------------------------------------------
			(
                'city_bucket',
                'City Wise Bucket',
                '[
                    {"values": ["MYSORE"], "label": "MYSORE"},
			        {"values": ["BARDHAMAN"], "label": "BARDHAMAN"},
			        {"values": ["KOLKATA"], "label": "KOLKATA"},
					{"values": ["NORTH 24 PARGANAS"], "label": "NORTH 24 PARGANAS"},
					{"values": ["HOOGHLY"], "label": "HOOGHLY"},
					{"values": ["MANDYA"], "label": "MANDYA"},
					{"values": ["KOLAR"], "label": "KOLAR"},
					{"values": ["TIRUNELVELI"], "label": "TIRUNELVELI"},
					{"values": ["TUMKUR"], "label": "TUMKUR"},
					{"values": ["EAST CHAMPARAN"], "label": "EAST CHAMPARAN"},
					{"values": ["NILGIRIS"], "label": "NILGIRIS"},
			        {"values": [], "label": "Other cities"}
                ]'::jsonb,
                'city',
                FALSE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 8: Origin Bureau Score BUCKET
            ----------------------------------------------------------------
			(
                'origin_bureau_score_bucket',
                'Bureau Score at the origination',
                '[
                    {"min": 0, "max": 0, "label": "0 to 0"},
					{"min": 0, "max": 500, "label": "0 to 500"},
					{"min": 500, "max": 600, "label": "500 to 600"},
					{"min": 600, "max": 700, "label": "600 to 700"},
					{"min": 700, "max": 800, "label": "700 to 800"},
					{"min": 800, "max": null, "label": "800 to +"},
					{"min": null, "max": null, "label": "BLANK"},
					{"min": null, "max": -1, "label": "NEGATIVE"}
                ]'::jsonb,
                'bureau_score',
                FALSE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 9: Latest Bureau Score BUCKET
            ----------------------------------------------------------------
			(
                'latest_bureau_score_bucket',
                'Latest Bureau Score',
                '[
                    {"min": 0, "max": 0, "label": "0 to 0"},
					{"min": 0, "max": 500, "label": "0 to 500"},
					{"min": 500, "max": 600, "label": "500 to 600"},
					{"min": 600, "max": 700, "label": "600 to 700"},
					{"min": 700, "max": 800, "label": "700 to 800"},
					{"min": 800, "max": null, "label": "800 to +"},
					{"min": null, "max": null, "label": "BLANK"},
					{"min": null, "max": -1, "label": "NEGATIVE"}
                ]'::jsonb,
                'current_bureau_score',
                FALSE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 10: Claim status BUCKET
            ----------------------------------------------------------------
			(
                'claim_info_bucket',
                'CGTMSE Claim Status',
                '[
                    { "values": ["ALL"], "label": "All Claim status" }
                ]'::jsonb,
                'claim_info',
                FALSE
            )
            ----------------------------------------------------------------
            -- 👉 Don't touch query after this line.
            ----------------------------------------------------------------
        ) AS t(summary_type, name, bucket_config, target_field, target_field_is_json)
    LOOP

        INSERT INTO bucket_configs (
            user_id,
            dataset_id,
            name,
            summary_type,
            bucket_config,
            is_default,
            target_field,
            target_field_is_json
        ) VALUES (
            USR_ID,
            DS_ID,
            rec.name,
            rec.summary_type,
            rec.bucket_config,
            FALSE,
            rec.target_field,
            rec.target_field_is_json
        )
        ON CONFLICT (dataset_id, summary_type,is_default,user_id) DO UPDATE
        SET
            user_id = EXCLUDED.user_id,
            name = EXCLUDED.name,
            bucket_config = EXCLUDED.bucket_config,
            is_default = EXCLUDED.is_default,
            target_field = EXCLUDED.target_field,
            target_field_is_json = EXCLUDED.target_field_is_json;

        RAISE NOTICE 'Inserted/Updated bucket: %', rec.summary_type;

    END LOOP;

END $$;
