import os, requests
from .base import Collector
from ..models import Job

class AdzunaCollector(Collector):
    def __init__(self,countries,queries): self.countries=countries or []; self.queries=queries or []
    def collect(self):
        app_id=os.getenv('ADZUNA_APP_ID'); app_key=os.getenv('ADZUNA_APP_KEY')
        if not app_id or not app_key: return []
        out=[]
        for country in self.countries:
            for q in self.queries:
                r=requests.get(f'https://api.adzuna.com/v1/api/jobs/{country}/search/1',params={
                    'app_id':app_id,'app_key':app_key,'results_per_page':50,'what':q,'sort_by':'date','max_days_old':1,'content-type':'application/json'
                },timeout=25)
                if r.status_code!=200: continue
                for x in r.json().get('results',[]):
                    loc=(x.get('location') or {}).get('display_name','')
                    out.append(Job(source='adzuna',external_id=str(x.get('id','')),title=x.get('title',''),
                        company=(x.get('company') or {}).get('display_name',''),location=loc,country=loc,
                        remote_type='Remote' if 'remote' in (x.get('description','')+' '+loc).lower() else 'Unknown',
                        posted_at=x.get('created'),url=x.get('redirect_url',''),description=x.get('description','')))
        return out
