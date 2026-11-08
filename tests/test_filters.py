from jobhunter.filters import extract_experience,title_allowed
from jobhunter.config import load_config
def test_exp(): assert extract_experience('Requires 0-2 years of experience')==(0.0,2.0)
def test_senior(): assert not title_allowed('Senior Machine Learning Engineer',load_config())
def test_junior(): assert title_allowed('Junior AI Engineer',load_config())
