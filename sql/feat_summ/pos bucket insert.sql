INSERT INTO bucket_configs (
    id,
    user_id,
	dataset_id,
    name,
    summary_type,
    bucket_config,
    is_default,
    created_at,
    updated_at,
    target_field,
    target_field_is_json
) VALUES (
    'c5230183-188b-4da1-bb4b-c02f1090c0fc',
    '41ebe6ef-01a3-439b-9b54-01564010ff4f',
	NULL,
    'Default POS Buckets',
    'pos_bucket',
    '[
        {"min": 0, "max": 1000, "label": "0 to 1000"},
        {"min": 1000, "max": 10000, "label": "1000 to 10000"},
        {"min": 10000, "max": 25000, "label": "10000 to 25000"},
        {"min": 25000, "max": 50000, "label": "25000 to 50000"},
        {"min": 50000, "max": 75000, "label": "50000 to 75000"},
        {"min": 75000, "max": 200000, "label": "75000 to 200000"},
        {"min": 200000, "max": 500000, "label": "200000 to 500000"},
        {"min": 500000, "max": 1000000, "label": "500000 to 1000000"},
        {"min": 1000000, "max": 999999999, "label": "1000000+"}
    ]'::jsonb,
    TRUE,
    '2025-05-04 05:55:37.577393+05:30',
    '2025-05-04 05:55:37.577393+05:30',
    'pos',
    FALSE
);
