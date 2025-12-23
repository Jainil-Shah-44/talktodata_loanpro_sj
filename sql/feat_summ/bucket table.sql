-- Create config table
CREATE TABLE bucket_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
	dataset_id UUID NULL, -- mapped for particual dataset
    name TEXT NOT NULL,
    summary_type TEXT NOT NULL,
    bucket_config JSONB NOT NULL,
    target_field TEXT NOT NULL,
    target_field_is_json BOOLEAN NOT NULL DEFAULT FALSE,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Fetch configs per user
CREATE INDEX idx_bucket_configs_user_id ON bucket_configs(user_id);

-- Fetch configs for dataset-id
CREATE INDEX idx_bucket_configs_dataset_id ON bucket_configs(dataset_id);

-- Fast filtering by summary type if needed
CREATE INDEX idx_bucket_configs_summary_type ON bucket_configs(summary_type);

-- Avoid FULL table scans when selecting defaults
CREATE INDEX idx_bucket_configs_is_default ON bucket_configs(is_default);

-- Add unique check for duplicancy removal
ALTER TABLE bucket_configs
ADD CONSTRAINT uq_bucket UNIQUE (dataset_id, summary_type,is_default,user_id);


