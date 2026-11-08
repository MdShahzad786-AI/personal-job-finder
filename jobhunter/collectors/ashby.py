import requests
from .base import Collector
from ..models import Job

class AshbyCollector(Collector):
    def __init__(self, boards): self.boards=boards or []
    def collect(self):
        out=[]
        for board in self.boards:
            r=requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{board}",params={'includeCompensation':'true'},timeout=25)
            if r.status_code!=200: continue
            for x in r.json().get('jobs',[]):
                loc=x.get('location','') or ''
                out.append(Job(
                    source=f'ashby:{board}', external_id=str(x.get('id') or x.get('jobUrl') or ''),
                    title=x.get('title',''), company=board.replace('-',' ').title(), location=loc,
                    country=((x.get('address') or {}).get('postalAddress') or {}).get('addressCountry','') or loc,
                    remote_type=x.get('workplaceType') or ('Remote' if x.get('isRemote') else 'Unknown'),
                    posted_at=x.get('publishedAt'), url=x.get('applyUrl') or x.get('jobUrl') or '',
                    description=x.get('descriptionPlain') or x.get('descriptionHtml') or ''
                ))
        return out
