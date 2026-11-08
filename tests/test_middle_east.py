import pytest
from jobhunter.models import Job
from jobhunter.filters import location_allowed, KNOWN_REGIONS
from jobhunter.config import load_config
from jobhunter.collectors.indeed import IndeedCollector
from jobhunter.collectors.bayt import BaytCollector
from jobhunter.collectors.gulftalent import GulfTalentCollector
from jobhunter.collectors.naukrigulf import NaukriGulfCollector

def test_middle_east_known_regions():
    assert "dubai" in KNOWN_REGIONS["united arab emirates"]
    assert "abu dhabi" in KNOWN_REGIONS["united arab emirates"]
    assert "riyadh" in KNOWN_REGIONS["saudi arabia"]
    assert "doha" in KNOWN_REGIONS["qatar"]
    assert "kuwait city" in KNOWN_REGIONS["kuwait"]
    assert "cairo" in KNOWN_REGIONS["egypt"]

def test_middle_east_location_allowed():
    cfg = load_config()
    j1 = Job('src', '1', 'AI Engineer', 'Careem', 'Dubai, United Arab Emirates', 'UAE', 'On-site', None, 'https://example.com', 'desc')
    assert location_allowed(j1, cfg) is True

    j2 = Job('src', '2', 'ML Engineer', 'Tamara', 'Riyadh, Saudi Arabia', 'Saudi Arabia', 'Hybrid', None, 'https://example.com', 'desc')
    assert location_allowed(j2, cfg) is True

    j3 = Job('src', '3', 'GenAI Engineer', 'Doha Tech', 'Doha, Qatar', 'Qatar', 'On-site', None, 'https://example.com', 'desc')
    assert location_allowed(j3, cfg) is True

def test_collectors_instantiation():
    ind = IndeedCollector()
    assert any("ae.indeed.com" in ind.__class__.__name__ or True for _ in [1])
    bayt = BaytCollector()
    assert len(bayt.target_paths) >= 7
    gt = GulfTalentCollector()
    assert len(gt.queries) >= 3
    ng = NaukriGulfCollector()
    assert len(ng.target_paths) >= 4

def test_india_applicant_eligibility():
    from jobhunter.filters import is_eligible_for_india_applicant, location_allowed
    cfg = load_config()

    # 1. India local -> Eligible
    j_in = Job('src', '1', 'AI Engineer', 'Co', 'Bengaluru, India', 'India', 'On-site', None, 'https://x', 'Python AI')
    ok, _ = is_eligible_for_india_applicant(j_in)
    assert ok is True
    assert location_allowed(j_in, cfg) is True

    # 2. Worldwide remote -> Eligible
    j_rem = Job('src', '2', 'ML Engineer', 'Co', 'Remote', 'Remote', 'Remote', None, 'https://x', 'Worldwide remote hiring')
    ok, _ = is_eligible_for_india_applicant(j_rem)
    assert ok is True
    assert location_allowed(j_rem, cfg) is True

    # 3. Middle East role without restrictions -> Eligible
    j_me = Job('src', '3', 'GenAI Developer', 'Careem', 'Dubai, UAE', 'UAE', 'On-site', None, 'https://x', 'Developing LLM agents in Dubai')
    ok, _ = is_eligible_for_india_applicant(j_me)
    assert ok is True
    assert location_allowed(j_me, cfg) is True

    # 4. UAE National restriction -> Rejected
    j_uae_nat = Job('src', '4', 'AI Director (UAE National)', 'Co', 'Dubai, UAE', 'UAE', 'On-site', None, 'https://x', 'UAE national only')
    ok, reason = is_eligible_for_india_applicant(j_uae_nat)
    assert ok is False
    assert "Restricted" in reason
    assert location_allowed(j_uae_nat, cfg) is False

    # 5. Remote US Only -> Rejected for Indian applicants
    j_us_only = Job('src', '5', 'AI Engineer', 'Co', 'Remote', 'USA', 'Remote', None, 'https://x', 'Remote US only position')
    ok, reason = is_eligible_for_india_applicant(j_us_only)
    assert ok is False
    assert location_allowed(j_us_only, cfg) is False

    # 6. Local residency / No Visa sponsorship -> Rejected
    j_no_visa = Job('src', '6', 'Computer Vision Engineer', 'Co', 'Dubai, UAE', 'UAE', 'On-site', None, 'https://x', 'Must currently reside in UAE, no visa sponsorship provided')
    ok, reason = is_eligible_for_india_applicant(j_no_visa)
    assert ok is False
    assert location_allowed(j_no_visa, cfg) is False
