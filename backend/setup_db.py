"""Create Vulnora database tables in Supabase."""
import psycopg2

DB_HOST = "db.ssmrlzlhufbghmjwswta.supabase.co"
DB_PORT = 5432
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "Maharaaj_251"

SQL = """
CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    repo_path TEXT,
    scan_status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    content TEXT,
    language TEXT DEFAULT 'unknown',
    size INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vulnerabilities (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    vulnerability_type TEXT DEFAULT 'Unknown',
    severity TEXT DEFAULT 'Medium',
    description TEXT,
    file_path TEXT,
    line_start INTEGER DEFAULT 0,
    line_end INTEGER DEFAULT 0,
    vulnerable_code TEXT,
    exploit TEXT,
    exploit_script TEXT,
    patch TEXT,
    patch_explanation TEXT,
    risk_score FLOAT DEFAULT 50,
    confidence FLOAT DEFAULT 50,
    exploitability FLOAT DEFAULT 50,
    impact FLOAT DEFAULT 50,
    cwe_id TEXT,
    cvss_vector TEXT,
    attack_path JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id TEXT PRIMARY KEY,
    project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    message TEXT,
    log_type TEXT DEFAULT 'info',
    data JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- RLS is bypassed by service_role key, no policies needed for backend access
"""

def main():
    print("Connecting to Supabase PostgreSQL...")
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS, connect_timeout=15
    )
    conn.autocommit = True
    cur = conn.cursor()

    print("Creating tables...")
    cur.execute(SQL)
    print("Tables created successfully!")

    # Verify
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name"
    )
    print("\nTables in database:")
    for row in cur.fetchall():
        print(f"  - {row[0]}")

    cur.close()
    conn.close()
    print("\nDatabase setup complete!")

if __name__ == "__main__":
    main()
