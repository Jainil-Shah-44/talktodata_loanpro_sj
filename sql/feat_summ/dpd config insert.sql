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
    '9eb87711-f9e2-495c-9e24-f22d746a6111',
    '41ebe6ef-01a3-439b-9b54-01564010ff4f',
    NULL,
    'Default DPD Buckets',
    'dpd_summary',
    '[
        {"min": 0, "max": 360, "label": "0 to 360"},
        {"min": 360, "max": 365, "label": "360 to 365"},
        {"min": 365, "max": 450, "label": "365 to 450"},
        {"min": 450, "max": 540, "label": "450 to 540"},
        {"min": 540, "max": 630, "label": "540 to 630"},
        {"min": 630, "max": 720, "label": "630 to 720"},
        {"min": 720, "max": 900, "label": "720 to 900"},
        {"min": 900, "max": 1080, "label": "900 to 1080"},
        {"min": 1080, "max": 1440, "label": "1080 to 1440"},
        {"min": 1440, "max": 1800, "label": "1440 to 1800"},
        {"min": 1800, "max": 999999, "label": "1800+"}
    ]'::jsonb,
    TRUE,
    '2025-05-04 05:55:37.577393+05:30',
    '2025-05-04 05:55:37.577393+05:30',
    'dpd',
    FALSE
);
