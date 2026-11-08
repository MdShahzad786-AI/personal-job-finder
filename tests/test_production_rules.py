from datetime import datetime, timezone
from jobhunter.filters import relative_to_iso, parse_dt, classify_remote_eligibility, extract_experience
from jobhunter.models import Job
from jobhunter.normalize import fingerprint


def make_job(location='Remote worldwide', description='Remote worldwide'):
    return Job(source='t',external_id='1',title='Junior AI Engineer',company='Acme',location=location,country='',remote_type='Remote',posted_at='2 hours ago',url='https://x',description=description)


def test_relative_time_parses():
    iso=relative_to_iso('2 hours ago')
    assert iso is not None
    assert parse_dt(iso) <= datetime.now(timezone.utc)


def test_remote_worldwide():
    assert classify_remote_eligibility(make_job()) == 'worldwide'


def test_remote_restricted():
    j=make_job('Remote', 'Remote US only')
    assert classify_remote_eligibility(j) == 'country_restricted'


def test_experience_plus():
    assert extract_experience('3+ years of experience') == (3.0, None)


def test_cross_source_fingerprint_ignores_external_id():
    a=fingerprint('AI Engineer','Acme Inc.','Bengaluru, India')
    b=fingerprint('AI Engineer','Acme','Bengaluru, India')
    assert a == b
