-- Create databases for different services
CREATE DATABASE auth_db;
CREATE DATABASE chat_db;

-- Create users for each service
CREATE USER auth_user WITH PASSWORD 'auth_password';
CREATE USER chat_user WITH PASSWORD 'chat_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;
GRANT ALL PRIVILEGES ON DATABASE chat_db TO chat_user;

-- Connect to auth_db and create schema
\c auth_db;
GRANT ALL ON SCHEMA public TO auth_user;

-- Connect to chat_db and create schema
\c chat_db;
GRANT ALL ON SCHEMA public TO chat_user;
