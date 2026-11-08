import requests
from ..models import Job
class LeverCollector:
    def __init__(self,sites): self.sites=sites or []
    def collect(self):
        out=[]
        for site in self.sites:
            r=requests.get(f'https://api.lever.co/v0/postings/{site}?mode=json',timeout=25)
            if r.status_code!=200: continue
            for x in r.json():
                cats=x.get('categories') or {}; loc=cats.get('location',''); workplace=x.get('workplaceType','') or ''
                out.append(Job(f'lever:{site}',str(x.get('id','')),x.get('text',''),site.replace('-',' ').title(),loc,loc,workplace or ('Remote' if 'remote' in loc.lower() else 'Unknown'),None,x.get('hostedUrl',''),x.get('descriptionPlain') or x.get('description') or ''))
        return out
