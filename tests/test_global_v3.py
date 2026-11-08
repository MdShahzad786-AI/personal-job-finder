from jobhunter.config import load_config
from jobhunter.filters import title_allowed, experience_allowed
from jobhunter.models import Job

def test_associate_ml_title_allowed():
    assert title_allowed('Associate Machine Learning Engineer',load_config())

def test_ai_engineer_i_allowed():
    assert title_allowed('AI Engineer I',load_config())

def test_senior_rejected():
    assert not title_allowed('Senior AI Engineer',load_config())

def test_unknown_experience_kept():
    j=Job('x','1','Junior AI Engineer','C','India','India','On-site',None,'https://x','Python role')
    assert experience_allowed(j,2)
