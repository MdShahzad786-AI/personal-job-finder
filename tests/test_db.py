from datetime import datetime, timezone, timedelta
from jobhunter.db import init_db, upsert_job, get_unemailed_jobs, cleanup_old_jobs
from jobhunter.models import Job

def test_db(tmp_path):
    db=tmp_path/'t.db'; init_db(db); j=Job('t','1','Junior AI Engineer','X','India','India','Remote',None,'https://example.com','Python AI'); m={'score':80,'matched_skills':['python'],'missing_skills':[],'why_match':'ok','resume_suggestion':'tailor'}
    assert upsert_job(db,j,'fp',m); assert not upsert_job(db,j,'fp',m); assert len(get_unemailed_jobs(db,0))==1

def test_cleanup_old_jobs(tmp_path):
    db = tmp_path / 'clean.db'
    init_db(db)
    now = datetime.now(timezone.utc)
    fresh_time = (now - timedelta(days=1)).isoformat()
    old_time = (now - timedelta(days=5)).isoformat()

    j_fresh = Job('src', '1', 'AI Engineer', 'Co A', 'India', 'India', 'Remote', fresh_time, 'https://a.com', 'desc')
    j_old = Job('src', '2', 'ML Engineer', 'Co B', 'India', 'India', 'Remote', old_time, 'https://b.com', 'desc')
    m = {'score': 75, 'matched_skills': ['ai'], 'missing_skills': [], 'why_match': 'ok', 'resume_suggestion': ''}

    upsert_job(db, j_fresh, 'fp1', m)
    upsert_job(db, j_old, 'fp2', m)

    # Clean up jobs older than 3 days
    purged = cleanup_old_jobs(db, days=3)
    assert purged == 1
