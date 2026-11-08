import requests
from ..models import Job
class ArbeitnowCollector:
    def collect(self):
        r=requests.get('https://www.arbeitnow.com/api/job-board-api',timeout=25); r.raise_for_status(); out=[]
        for x in r.json().get('data',[]):
            out.append(Job('arbeitnow',str(x.get('slug','')),x.get('title',''),x.get('company_name',''),x.get('location',''),x.get('location',''),'Remote' if x.get('remote') else 'On-site/Hybrid',x.get('created_at'),x.get('url',''),x.get('description','')))
        return out
