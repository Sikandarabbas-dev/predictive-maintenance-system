-- Predictive Maintenance System - Database Schema
-- Run this against your MySQL server:  mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS predictive_maintenance_db;
USE predictive_maintenance_db;

CREATE TABLE IF NOT EXISTS machines (
    machine_id      INT AUTO_INCREMENT PRIMARY KEY,
    machine_name    VARCHAR(150) NOT NULL,
    machine_type    VARCHAR(100),
    installed_at    DATE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    reading_id      INT AUTO_INCREMENT PRIMARY KEY,
    machine_id      INT NOT NULL,
    reading_date    DATE NOT NULL,
    runtime_hours   DECIMAL(10,2) NOT NULL,   -- cumulative hours since last maintenance
    temperature     DECIMAL(6,2) NOT NULL,    -- degrees C
    vibration       DECIMAL(6,3) NOT NULL,    -- mm/s
    pressure        DECIMAL(6,2) NOT NULL,    -- bar
    failed          TINYINT(1) DEFAULT 0,     -- 1 if a failure occurred at/after this reading
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE CASCADE,
    INDEX idx_machine_date (machine_id, reading_date)
);

CREATE TABLE IF NOT EXISTS maintenance_alerts (
    alert_id        INT AUTO_INCREMENT PRIMARY KEY,
    machine_id      INT NOT NULL,
    failure_risk    DECIMAL(5,2) NOT NULL,    -- 0-100
    risk_level      VARCHAR(20) NOT NULL,     -- low / medium / high
    generated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE CASCADE
);
