import requests
from ..models import Job
class GreenhouseCollector:
    def __init__(self,boards): self.boards=boards or []
    def collect(self):
        out=[]
        for board in self.boards:
            try:
                r=requests.get(f'https://boards-api.greenhouse.io/v1/boards/{board}/jobs',timeout=12)
                if r.status_code!=200: continue
                for x in r.json().get('jobs',[]):
                    loc=(x.get('location') or {}).get('name','')
                    out.append(Job(f'greenhouse:{board}',str(x.get('id','')),x.get('title',''),board.replace('-',' ').title(),loc,loc,'Remote' if 'remote' in loc.lower() else 'On-site/Hybrid',x.get('updated_at'),x.get('absolute_url',''),f"{x.get('title','')} at {board} in {loc}"))
            except Exception:
                continue
        return out
