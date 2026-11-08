import sqlite3
from pathlib import Path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS jobs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 source TEXT NOT NULL, external_id TEXT, title TEXT NOT NULL, company TEXT NOT NULL,
 location TEXT, country TEXT, remote_type TEXT, remote_eligibility TEXT,
 posted_at TEXT, posted_verified INTEGER DEFAULT 0, url TEXT NOT NULL, canonical_url TEXT,
 description TEXT, fingerprint TEXT NOT NULL UNIQUE, match_score REAL,
 matched_skills TEXT, missing_skills TEXT, why_match TEXT, resume_suggestion TEXT,
 first_seen_at TEXT DEFAULT CURRENT_TIMESTAMP, last_seen_at TEXT DEFAULT CURRENT_TIMESTAMP,
 emailed_at TEXT, application_status TEXT DEFAULT 'Not Applied', saved INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_jobs_fp ON jobs(fingerprint);
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(match_score);
CREATE INDEX IF NOT EXISTS idx_jobs_email ON jobs(emailed_at);

CREATE TABLE IF NOT EXISTS collection_runs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 started_at TEXT DEFAULT CURRENT_TIMESTAMP, finished_at TEXT,
 sources_attempted INTEGER DEFAULT 0, sources_failed INTEGER DEFAULT 0,
 raw_jobs INTEGER DEFAULT 0, eligible_jobs INTEGER DEFAULT 0,
 inserted_jobs INTEGER DEFAULT 0, duplicates_removed INTEGER DEFAULT 0,
 errors TEXT
);
CREATE TABLE IF NOT EXISTS email_runs (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP, recipients TEXT,
 jobs_count INTEGER, success INTEGER, error TEXT
);
'''

REQUIRED_COLUMNS = {
    "remote_eligibility": "TEXT", "posted_verified": "INTEGER DEFAULT 0",
    "canonical_url": "TEXT", "last_seen_at": "TEXT", "application_status": "TEXT DEFAULT 'Not Applied'",
    "saved": "INTEGER DEFAULT 0"
}

def connect(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    return c

def init_db(path: Path):
    with connect(path) as c:
        c.executescript(SCHEMA)
        cols = {r[1] for r in c.execute("PRAGMA table_info(jobs)").fetchall()}
        for name, definition in REQUIRED_COLUMNS.items():
            if name not in cols:
                c.execute(f"ALTER TABLE jobs ADD COLUMN {name} {definition}")

def upsert_job(path: Path, job, fp, match):
    with connect(path) as c:
        row = c.execute("SELECT id FROM jobs WHERE fingerprint=?", (fp,)).fetchone()
        if row:
            c.execute("UPDATE jobs SET last_seen_at=CURRENT_TIMESTAMP WHERE id=?", (row["id"],))
            return False
        from .filters import parse_dt
        dt = parse_dt(job.posted_at)
        iso_posted_at = dt.isoformat() if dt else (job.posted_at or "")
        c.execute('''INSERT INTO jobs
        (source,external_id,title,company,location,country,remote_type,remote_eligibility,
         posted_at,posted_verified,url,canonical_url,description,fingerprint,match_score,
         matched_skills,missing_skills,why_match,resume_suggestion)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (job.source,job.external_id,job.title,job.company,job.location,job.country,job.remote_type,
         job.remote_eligibility,iso_posted_at,int(bool(job.posted_verified)),job.url,
         job.canonical_url,job.description,fp,match['score'],', '.join(match['matched_skills']),
         ', '.join(match['missing_skills']),match['why_match'],match['resume_suggestion']))
        return True

def get_unemailed_jobs(path: Path, min_score=0):
    with connect(path) as c:
        return c.execute('''SELECT * FROM jobs WHERE emailed_at IS NULL AND match_score>=?
            ORDER BY match_score DESC, posted_at DESC''',(min_score,)).fetchall()

def mark_emailed(path: Path, ids):
    if not ids: return
    q=','.join('?' for _ in ids)
    with connect(path) as c:
        c.execute(f'UPDATE jobs SET emailed_at=CURRENT_TIMESTAMP WHERE id IN ({q})', list(ids))

def dashboard_rows(path: Path):
    with connect(path) as c:
        return c.execute('SELECT * FROM jobs ORDER BY first_seen_at DESC').fetchall()

def update_job_state(path: Path, job_id: int, status: str, saved: bool):
    with connect(path) as c:
        c.execute('UPDATE jobs SET application_status=?, saved=? WHERE id=?', (status, int(saved), job_id))

def record_collection_run(path: Path, stats: dict, errors: str = ""):
    with connect(path) as c:
        c.execute('''INSERT INTO collection_runs
          (finished_at,sources_attempted,sources_failed,raw_jobs,eligible_jobs,inserted_jobs,duplicates_removed,errors)
          VALUES (CURRENT_TIMESTAMP,?,?,?,?,?,?,?)''',
          (stats.get('sources_attempted',0),stats.get('sources_failed',0),stats.get('raw_jobs',0),
           stats.get('filtered',0),stats.get('inserted',0),stats.get('duplicates',0),errors))

def record_email_run(path: Path, recipient: str, jobs_count: int, success: bool, error: str = ""):
    with connect(path) as c:
        c.execute('INSERT INTO email_runs(recipients,jobs_count,success,error) VALUES (?,?,?,?)',
                  (recipient,jobs_count,int(success),error))

def cleanup_old_jobs(path: Path, days: int = 3, keep_saved: bool = True) -> int:
    """Delete jobs older than `days` days from the database.
    If keep_saved is True, preserves jobs marked as saved or with custom application status.
    """
    from datetime import datetime, timezone, timedelta
    from .filters import parse_dt

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    deleted_ids = []

    with connect(path) as c:
        rows = c.execute("SELECT id, posted_at, first_seen_at, saved, application_status FROM jobs").fetchall()
        for r in rows:
            if keep_saved and (r["saved"] or (r["application_status"] and r["application_status"] != "Not Applied")):
                continue

            p_dt = parse_dt(r["posted_at"])
            fs_dt = parse_dt(r["first_seen_at"])
            dt = p_dt or fs_dt

            if dt and dt < cutoff:
                deleted_ids.append(r["id"])

        if deleted_ids:
            for i in range(0, len(deleted_ids), 500):
                chunk = deleted_ids[i:i+500]
                q = ",".join("?" for _ in chunk)
                c.execute(f"DELETE FROM jobs WHERE id IN ({q})", chunk)

    return len(deleted_ids)

