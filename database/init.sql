-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Product Master Table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Event Log Table (General Business Events)
CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(100) NOT NULL,
    session_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    product_id INTEGER REFERENCES products(product_id),
    metadata JSONB,
    user_agent TEXT
);

-- 3. [EARS v4] Dedicated Error Logs Table (Storage Isolation)
CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    error_code VARCHAR(100) NOT NULL,
    error_msg TEXT,
    severity VARCHAR(20) NOT NULL,
    request_path TEXT,
    metadata JSONB
);

-- 4. [EARS v4] Metrics Summary Table (High-Performance Aggregation)
CREATE TABLE IF NOT EXISTS error_metrics_summary (
    minute_bucket TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    error_code VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    error_count INTEGER DEFAULT 0,
    PRIMARY KEY (minute_bucket, error_code, severity)
);

-- 5. Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_metadata ON events USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_error_logs_composite ON error_logs(timestamp DESC, severity, error_code);
CREATE INDEX IF NOT EXISTS idx_summary_bucket ON error_metrics_summary(minute_bucket DESC);

-- 6. Initial Seed Data
INSERT INTO products (name, category, price) VALUES 
('iPhone 15', 'Electronics', 1200000),
('Galaxy S24', 'Electronics', 1150000),
('MacBook Air', 'Electronics', 1500000),
('Samsung Refrigerator', 'Electronics', 2500000),
('Organic Apple', 'Food', 5000),
('Premium Steak', 'Food', 45000),
('Instant Noodle Pack', 'Food', 6000),
('Denim Jacket', 'Fashion', 85000),
('Classic Hoodie', 'Fashion', 55000),
('Leather Sneakers', 'Fashion', 120000)
ON CONFLICT DO NOTHING;
