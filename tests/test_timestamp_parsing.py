from datetime import datetime, timezone, timedelta
from jobhunter.filters import parse_dt, is_fresh

def test_unix_seconds_int():
    now = int(datetime.now(timezone.utc).timestamp())
    dt = parse_dt(now)
    assert dt is not None
    assert abs((datetime.now(timezone.utc) - dt).total_seconds()) < 5

def test_unix_milliseconds_int():
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    dt = parse_dt(now_ms)
    assert dt is not None
    assert abs((datetime.now(timezone.utc) - dt).total_seconds()) < 5

def test_numeric_string_timestamp():
    now = str(int(datetime.now(timezone.utc).timestamp()))
    assert parse_dt(now) is not None

def test_relative_hours():
    dt = parse_dt("2 hours ago")
    assert dt is not None
    assert datetime.now(timezone.utc) - dt < timedelta(hours=3)

def test_fresh_int_timestamp():
    now = int(datetime.now(timezone.utc).timestamp())
    assert is_fresh(now, 24, True)
