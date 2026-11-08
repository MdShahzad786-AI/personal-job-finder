import requests
from ..models import Job
class RemotiveCollector:
    def collect(self):
        r=requests.get('https://remotive.com/api/remote-jobs',timeout=25); r.raise_for_status(); out=[]
        for x in r.json().get('jobs',[]):
            out.append(Job('remotive',str(x.get('id','')),x.get('title',''),x.get('company_name',''),x.get('candidate_required_location','Remote'),x.get('candidate_required_location',''),'Remote',x.get('publication_date'),x.get('url',''),x.get('description','')))
        return out
