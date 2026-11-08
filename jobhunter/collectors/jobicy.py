import logging
import requests
from .base import Collector
from ..models import Job

log = logging.getLogger(__name__)

class JobicyCollector(Collector):
    API_URL = "https://jobicy.com/api/v2/remote-jobs"

    def __init__(self, count=50):
        self.count = count

    def collect(self):
        jobs = []
        try:
            r = requests.get(f"{self.API_URL}?count={self.count}", timeout=20)
            if r.status_code != 200:
                log.warning("Jobicy returned status %s", r.status_code)
                return []
            data = r.json()
            items = data.get("jobs", [])
            for x in items:
                title = x.get("jobTitle", "")
                company = x.get("companyName", "")
                geo = x.get("jobGeo", "") or "Remote Worldwide"
                pub_date = x.get("pubDate")
                url = x.get("url", "")
                desc = x.get("jobDescription", "")
                ext_id = str(x.get("id") or url)

                jobs.append(Job(
                    source="jobicy",
                    external_id=ext_id,
                    title=title,
                    company=company,
                    location=geo,
                    country=geo,
                    remote_type="Remote",
                    posted_at=pub_date,
                    url=url,
                    description=desc,
                    posted_verified=bool(pub_date),
                ))
        except Exception as e:
            log.warning("Jobicy collection failed: %s", e)
        log.info("JobicyCollector collected %d jobs", len(jobs))
        return jobs
