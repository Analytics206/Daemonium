-- Create philosophers table
CREATE TABLE IF NOT EXISTS philosophers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    dob VARCHAR(20),
    dod VARCHAR(20),
    summary TEXT,
    content TEXT,
    school_id INTEGER,
    tag_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add unique constraint on name
ALTER TABLE philosophers 
ADD CONSTRAINT philosophers_name_key UNIQUE (name);
