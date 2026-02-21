-- ============================================
-- VULNORA - Supabase Database Schema
-- Run this in Supabase SQL Editor
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    repo_path TEXT,
    scan_status TEXT DEFAULT 'pending' CHECK (scan_status IN ('pending','recon','analysis','exploit','patch','report','completed','failed')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Files table
CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    content TEXT,
    language TEXT DEFAULT 'unknown',
    size INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_files_project ON files(project_id);

-- Vulnerabilities table
CREATE TABLE IF NOT EXISTS vulnerabilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    vulnerability_type TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('Critical','High','Medium','Low')),
    description TEXT,
    file_path TEXT,
    line_start INTEGER DEFAULT 0,
    line_end INTEGER DEFAULT 0,
    vulnerable_code TEXT,
    exploit TEXT,
    exploit_script TEXT,
    patch TEXT,
    patch_explanation TEXT,
    risk_score FLOAT DEFAULT 0,
    confidence FLOAT DEFAULT 0,
    exploitability FLOAT DEFAULT 0,
    impact FLOAT DEFAULT 0,
    cwe_id TEXT,
    cvss_vector TEXT,
    attack_path JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vulns_project ON vulnerabilities(project_id);
CREATE INDEX IF NOT EXISTS idx_vulns_severity ON vulnerabilities(severity);

-- Agent Logs table
CREATE TABLE IF NOT EXISTS agent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    message TEXT NOT NULL,
    log_type TEXT DEFAULT 'info',
    data JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_project ON agent_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON agent_logs(timestamp);

-- Enable Row Level Security
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE vulnerabilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;

-- Policies (allow all for service role - adjust for production)
CREATE POLICY "Allow all for service role" ON projects FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON files FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON vulnerabilities FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON agent_logs FOR ALL USING (true);
