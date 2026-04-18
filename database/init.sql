-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Product Master Table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL, -- Electronics, Food, Fashion, etc.
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Event Log Table (Hybrid Schema)
CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(100) NOT NULL,
    session_id UUID NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- page_view, search, add_to_cart, purchase
    product_id INTEGER REFERENCES products(product_id),
    metadata JSONB, -- Flexible context: {query, price_at_event, original_price, etc.}
    user_agent TEXT
);

-- 3. Performance Indexes
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_product ON events(product_id);
CREATE INDEX idx_products_category ON products(category);
-- GIN index for fast searching inside JSONB
CREATE INDEX idx_events_metadata ON events USING GIN (metadata);

-- 4. Initial Product Categories (Seed Data)
-- This allows us to start with some predefined categories as discussed.
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
('Leather Sneakers', 'Fashion', 120000);
