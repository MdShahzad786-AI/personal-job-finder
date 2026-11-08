from jobhunter.models import Job
from jobhunter.match import score_job
from jobhunter.config import load_candidate,load_config
def test_score():
    j=Job('test','1','Junior Generative AI Engineer','Example','India Remote','India','Remote',None,'https://example.com','Python LangChain RAG ChromaDB Docker 0-1 years Bachelor degree')
    j.required_experience_min=0
    r=score_job(j,load_candidate(),load_config()); assert r['score']>=70; assert 'python' in r['matched_skills']
