-- database/setup.sql
CREATE DATABASE IF NOT EXISTS scheme_categorizer;
USE scheme_categorizer;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    preferences TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS schemes (
    scheme_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    government_entity VARCHAR(100),
    category VARCHAR(50),
    eligibility TEXT,
    benefits TEXT,
    application_link VARCHAR(255),
    publish_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    raw_text TEXT,
    vectorized_data LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    scheme_id INT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (scheme_id) REFERENCES schemes(scheme_id)
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    keywords TEXT
);

-- Add some test data
INSERT INTO schemes (title, description, category, publish_date) VALUES
('Farmers Subsidy Scheme', 'Financial assistance for small farmers to buy equipment', 'Category_1', '2023-01-15'),
('Startup India', 'Funding and support for new tech startups', 'Category_2', '2023-02-20'),
('Women Entrepreneurship', 'Loans and training for women starting businesses', 'Category_1', '2023-03-10'),
('Digital India', 'Promoting digital literacy and infrastructure', 'Category_3', '2023-04-05');