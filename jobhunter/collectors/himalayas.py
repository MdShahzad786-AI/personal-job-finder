import logging
import requests
from .base import Collector
from ..models import Job

log = logging.getLogger(__name__)

class HimalayasCollector(Collector):
    API_URL = "https://himalayas.app/jobs/api"

    def __init__(self, limit=50):
        self.limit = limit

    def collect(self):
        jobs = []
        try:
            r = requests.get(f"{self.API_URL}?limit={self.limit}", timeout=20)
            if r.status_code != 200:
                log.warning("Himalayas API returned status %s", r.status_code)
                return []
            data = r.json()
            items = data.get("jobs", [])
            for x in items:
                title = x.get("title", "")
                company = x.get("companyName", "")
                loc_restrictions = x.get("locationRestrictions", [])
                loc_str = ", ".join(loc_restrictions) if loc_restrictions else "Remote Worldwide"
                work_type = x.get("workplaceType") or "Remote"
                remote_type = "Remote" if "remote" in work_type.lower() else ("Hybrid" if "hybrid" in work_type.lower() else "On-site")
                pub_date = x.get("publishedAt")
                url = x.get("applicationLink") or f"https://himalayas.app/companies/{company}/jobs"
                desc = x.get("description") or x.get("excerpt") or ""
                ext_id = str(x.get("id") or url)

                job = Job(
                    source="himalayas",
                    external_id=ext_id,
                    title=title,
                    company=company,
                    location=loc_str,
                    country=loc_str,
                    remote_type=remote_type,
                    posted_at=pub_date,
                    url=url,
                    description=desc,
                    posted_verified=bool(pub_date),
                )
                if x.get("minExperienceYears") is not None:
                    try:
                        job.required_experience_min = float(x["minExperienceYears"])
                    except Exception:
                        pass
                if x.get("maxExperienceYears") is not None:
                    try:
                        job.required_experience_max = float(x["maxExperienceYears"])
                    except Exception:
                        pass
                jobs.append(job)
        except Exception as e:
            log.warning("Himalayas collection failed: %s", e)
        log.info("HimalayasCollector collected %d jobs", len(jobs))
        return jobs
