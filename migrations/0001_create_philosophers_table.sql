-- Create philosophers table
CREATE TABLE IF NOT EXISTS philosophers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    summary TEXT,
    content TEXT,
    dob DATE,
    dod DATE,
    school_id INTEGER REFERENCES schools(id) ON DELETE SET NULL,
    tag_id INTEGER REFERENCES tags(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add index on foreign keys for better join performance
CREATE INDEX IF NOT EXISTS idx_philosophers_school_id ON philosophers(school_id);
CREATE INDEX IF NOT EXISTS idx_philosophers_tag_id ON philosophers(tag_id);

-- Add updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_philosophers_updated_at
BEFORE UPDATE ON philosophers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
