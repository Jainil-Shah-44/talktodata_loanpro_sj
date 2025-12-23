-- 1. mapping_profiles
CREATE TABLE mapping_profiles (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  created_by uuid NOT NULL REFERENCES users(id), -- FK to users.id (optional)
  is_global BOOLEAN DEFAULT TRUE,
  is_active BOOLEAN DEFAULT TRUE,
  profile_json JSONB, -- optional: store full JSON snapshot for export / import
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. mapping_sheets
CREATE TABLE mapping_sheets (
  id SERIAL PRIMARY KEY,
  profile_id INTEGER NOT NULL REFERENCES mapping_profiles(id) ON DELETE CASCADE,
  sheet_index INTEGER NOT NULL, -- sheet number or name index
  sheet_alias TEXT,
  header_row INTEGER DEFAULT -1,
  skip_rows INTEGER DEFAULT 0,
  cols_to_read TEXT,        -- CSV "0,2,6" or JSON text array
  key_columns JSONB,        -- [0] etc.
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (profile_id, sheet_index)
);

-- 3. sheet_extra_columns
CREATE TABLE sheet_extra_columns (
  id SERIAL PRIMARY KEY,
  sheet_id INTEGER NOT NULL REFERENCES mapping_sheets(id) ON DELETE CASCADE,
  source_col TEXT NOT NULL,
  target_name TEXT NOT NULL
);

-- 4. sheet_cleanup
CREATE TABLE sheet_cleanup (
  id SERIAL PRIMARY KEY,
  sheet_id INTEGER NOT NULL REFERENCES mapping_sheets(id) ON DELETE CASCADE,
  rules JSONB NOT NULL  -- e.g. [{"col":7,"type":"dt"},{"col":8,"type":"int"}]
);

-- 5. sheet_column_mappings (multi-target allowed)
CREATE TABLE sheet_column_mappings (
  id SERIAL PRIMARY KEY,
  profile_id INTEGER NOT NULL REFERENCES mapping_profiles(id) ON DELETE CASCADE,
  sheet_index INTEGER NOT NULL,
  source_col TEXT NOT NULL,
  target_column TEXT NOT NULL,
  UNIQUE(profile_id, sheet_index, source_col, target_column)
);

-- 6. sheet_relations
CREATE TABLE sheet_relations (
  id SERIAL PRIMARY KEY,
  profile_id INTEGER NOT NULL REFERENCES mapping_profiles(id) ON DELETE CASCADE,
  left_sheet INTEGER NOT NULL,
  right_sheet INTEGER NOT NULL,
  left_col TEXT NOT NULL,
  right_col TEXT NOT NULL,
  how TEXT NOT NULL DEFAULT 'left'
);
