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
    WHERE file_name = 'Pool file software - Credit Card Pool-Format.xlsx'
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
                    {"min": 0, "max": 10000, "label": "0 to 10000"},
	                {"min": 10000, "max": 30000, "label": "10000 to 30000"},
	                {"min": 30000, "max": 50000, "label": "30000 to 50000"},
	                {"min": 50000, "max": 80000, "label": "50000 to 80000"},
	                {"min": 80000, "max": 100000, "label": "80000 to 100000"},
	                {"min": 100000, "max": 150000, "label": "100000 to 150000"},
	                {"min": 150000, "max": 200000, "label": "150000 to 200000"},
	                {"min": 200000, "max": 250000, "label": "200000 to 250000"},
	                {"min": 250000, "max": 300000, "label": "250000 to 300000"},
	                {"min": 300000, "max": 350000, "label": "300000 to 350000"},
	                {"min": 350000, "max": 400000, "label": "350000 to 400000"},
					{"min": 400000, "max": 450000, "label": "400000 to 450000"},
					{"min": 650000, "max": null, "label": "650000 to +"}
                ]'::jsonb,                        -- bucket_config
                'principal_os_amt',               -- target_field
                FALSE                             -- target_field_is_json
            ),
            ----------------------------------------------------------------
            -- 🔵 BUCKET 2: DPD Bucket 
            ----------------------------------------------------------------
            (
                'dpd_bucket',
                'DPD Buckets',
                '[
                    {"min": 0, "max": 540, "label": "0 to 540"},
					{"min": 540, "max": 720, "label": "540 to 720"},
					{"min": 720, "max": 900, "label": "720 to 900"},
					{"min": 900, "max": 1080, "label": "900 to 1080"},
					{"min": 1080, "max": 1260, "label": "1080 to 1260"},
					{"min": 1260, "max": 1440, "label": "1260 to 1440"},
					{"min": 1440, "max": 1800, "label": "1440 to 1800"},
					{"min": 1800, "max": null, "label": "1800 to +"}
                ]'::jsonb,
                'dpd',
                FALSE
            ),

            ----------------------------------------------------------------
            -- 🔵 BUCKET 3: Category-Wise BUCKET
            ----------------------------------------------------------------
            (
                'category_bucket',
                'Borrower Category Summary',
                '[
                    { "values": ["ALL"], "label": "All category" }
                ]'::jsonb,
                'category',
                FALSE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 4: Borrower Gender Wise Summary BUCKET
            ----------------------------------------------------------------
			(
                'extras_gender_bucket',
                'Borrower Gender Wise Summary',
                '[
                    {"values": ["M"], "label": "Males"},
			        {"values": ["F"], "label": "Females"},
			        {"values": ["O"], "label": "Other"},
					{"values": [null], "label": "BLANK"},
			        {"values": [], "label": "Other genders"}
                ]'::jsonb,
                'additional_fields->gender',
                TRUE
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
            -- 🔵 BUCKET 6: Origin Bureau Score BUCKET
            ----------------------------------------------------------------
			(
                'origin_bureau_score_bucket',
                'Bureau Score at the origination',
                '[
                    {"min": -1, "max": -1, "label": "-1 to -1"},
					{"min": -1, "max": 500, "label": "-1 to 500"},
					{"min": 500, "max": 550, "label": "500 to 550"},
					{"min": 550, "max": 600, "label": "550 to 600"},
					{"min": 600, "max": 650, "label": "600 to 650"},
					{"min": 650, "max": 700, "label": "650 to 700"},
					{"min": 700, "max": 750, "label": "700 to 750"},
					{"min": 750, "max": 800, "label": "750 to 800"},
					{"min": 800, "max": 850, "label": "800 to 850"},
					{"min": 850, "max": null, "label": "850 to +"},
					{"min": null, "max": -1, "label": "NEGATIVE"}
					{"min": null, "max": null, "label": "NA"}
                ]'::jsonb,
                'bureau_score',
                FALSE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 7: Vintage Wise Summary BUCKET
            ----------------------------------------------------------------
			(
                'extras_vintage_bucket',
                'Vintage-wise Bucket',
                '[
                    {"values": ["V4"], "label": "V4"},
			        {"values": ["V3"], "label": "V3"},
			        {"values": ["V5"], "label": "V5"},
			        {"values": [], "label": "Other Vintages"}
                ]'::jsonb,
                'additional_fields->vintage',
                TRUE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 8: Risk-Wise Band BUCKET
            ----------------------------------------------------------------
			(
                'extras_riks_band_bucket',
                'Risk-Band Wise Bucket',
                '[
                    {"values": ["R5"], "label": "R5"},
			        {"values": ["R4"], "label": "R4"},
			        {"values": ["R3"], "label": "R3"},
					{"values": ["R2"], "label": "R2"},
			        {"values": [], "label": "Other Risk-Bands"}
                ]'::jsonb,
                'additional_fields->risk_band',
                TRUE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 9: Vintage + Risk-Wise Band BUCKET
            ----------------------------------------------------------------
			(
                'extras_riks_N_vintage_bucket',
                'Vintage & Riws Band Summary',
                '[
                    {"values": ["V4 - R5"], "label": "V4 - R5"},
			        {"values": ["V3 - R5"], "label": "V3 - R5"},
					{"values": ["V3 - R4"], "label": "V3 - R4"},
			        {"values": ["V4 - R4"], "label": "V4 - R4"},
					{"values": ["V4 - R3"], "label": "V4 - R3"},
					{"values": ["V5 - R2"], "label": "V5 - R2"},
			        {"values": [], "label": "Other Vintage & Risk-Bands"}
                ]'::jsonb,
                'additional_fields->auto_buc_vintage_risk_band',
                TRUE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 10: Credit Limit Summary BUCKET
            ----------------------------------------------------------------
			(
                'extras_credit_scroe_bucket',
                'Credit Limit Summary',
                '[
                    {"min": 0, "max": 10000, "label": "0 to 10000"},
	                {"min": 10000, "max": 30000, "label": "10000 to 30000"},
	                {"min": 30000, "max": 50000, "label": "30000 to 50000"},
	                {"min": 50000, "max": 70000, "label": "50000 to 70000"},
	                {"min": 70000, "max": 100000, "label": "70000 to 100000"},
	                {"min": 100000, "max": 150000, "label": "100000 to 150000"},
	                {"min": 150000, "max": 200000, "label": "150000 to 200000"},
	                {"min": 200000, "max": 250000, "label": "200000 to 250000"},
	                {"min": 250000, "max": 300000, "label": "250000 to 300000"},
	                {"min": 300000, "max": 500000, "label": "300000 to 500000"},
	                {"min": 500000, "max": 1000000, "label": "500000 to 1000000"},
					{"min": 1000000, "max": null, "label": "1000000 to +"}
                ]'::jsonb,
                'additional_fields->credit_score',
                TRUE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 11: Rent Spend Summary BUCKET
            ----------------------------------------------------------------
			(
                'rent_spend_bucket',
                'Rent Spend Summary',
                '[
                    {"min": null, "max": 0.1, "label": " to 0.1"},
	                {"min": 0.1, "max": 0.2, "label": "0.1 to 0.2"},
	                {"min": 0.2, "max": 0.3, "label": "0.2 to 0.3"},
	                {"min": 0.3, "max": 0.4, "label": "0.3 to 0.4"},
	                {"min": 0.4, "max": 0.5, "label": "0.4 to 0.5"},
	                {"min": 0.5, "max": 0.55, "label": "0.5 to 0.55"},
	                {"min": 0.55, "max": 0.6, "label": "0.55 to 0.6"},
	                {"min": 0.6, "max": 0.65, "label": "0.6 to 0.65"},
	                {"min": 0.65, "max": 0.7, "label": "0.65 to 0.7"},
	                {"min": 0.7, "max": 0.75, "label": "0.7 to 0.75"},
	                {"min": 0.75, "max": 0.8, "label": "0.75 to 0.8"},
					{"min": 0.8, "max": 0.9, "label": "0.8 to 0.9"},
					{"min": 0.9, "max": 1.0, "label": "0.9 to 1"},
					{"min": 1.0, "max": null, "label": "1 to +"}
                ]'::jsonb,
                'additional_fields->rent_spend',
                TRUE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 12: Fuel Spends Summary BUCKET
            ----------------------------------------------------------------
			(
                'fuel_spend_bucket',
                'Fuel Spends Summary',
                '[
                    {"min": null, "max": 0.1, "label": " to 0.1"},
	                {"min": 0.1, "max": 0.2, "label": "0.1 to 0.2"},
	                {"min": 0.2, "max": 0.3, "label": "0.2 to 0.3"},
	                {"min": 0.3, "max": 0.4, "label": "0.3 to 0.4"},
	                {"min": 0.4, "max": 0.5, "label": "0.4 to 0.5"},
	                {"min": 0.5, "max": 0.55, "label": "0.5 to 0.55"},
	                {"min": 0.55, "max": 0.6, "label": "0.55 to 0.6"},
	                {"min": 0.6, "max": 0.65, "label": "0.6 to 0.65"},
	                {"min": 0.65, "max": 0.7, "label": "0.65 to 0.7"},
	                {"min": 0.7, "max": 0.75, "label": "0.7 to 0.75"},
	                {"min": 0.75, "max": 0.8, "label": "0.75 to 0.8"},
					{"min": 0.8, "max": 0.9, "label": "0.8 to 0.9"},
					{"min": 0.9, "max": 1.0, "label": "0.9 to 1"},
					{"min": 1.0, "max": null, "label": "1 to +"}
                ]'::jsonb,
                'additional_fields->fuel_spend',
                TRUE
            ),
			----------------------------------------------------------------
            -- 🔵 BUCKET 13: Utility Spends Summary BUCKET
            ----------------------------------------------------------------
			(
                'utility_spend_bucket',
                'Utility Spends Summary',
                '[
                    {"min": null, "max": 0.1, "label": " to 0.1"},
	                {"min": 0.1, "max": 0.2, "label": "0.1 to 0.2"},
	                {"min": 0.2, "max": 0.3, "label": "0.2 to 0.3"},
	                {"min": 0.3, "max": 0.4, "label": "0.3 to 0.4"},
	                {"min": 0.4, "max": 0.5, "label": "0.4 to 0.5"},
	                {"min": 0.5, "max": 0.55, "label": "0.5 to 0.55"},
	                {"min": 0.55, "max": 0.6, "label": "0.55 to 0.6"},
	                {"min": 0.6, "max": 0.65, "label": "0.6 to 0.65"},
	                {"min": 0.65, "max": 0.7, "label": "0.65 to 0.7"},
	                {"min": 0.7, "max": 0.75, "label": "0.7 to 0.75"},
	                {"min": 0.75, "max": 0.8, "label": "0.75 to 0.8"},
					{"min": 0.8, "max": 0.9, "label": "0.8 to 0.9"},
					{"min": 0.9, "max": 1.0, "label": "0.9 to 1"},
					{"min": 1.0, "max": null, "label": "1 to +"}
                ]'::jsonb,
                'additional_fields->utility_spend',
                TRUE
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
