import requests
from .base import Collector
from ..models import Job

class RemoteOKCollector(Collector):
    URL = "https://remoteok.com/api"

    def collect(self):
        headers = {"User-Agent": "AIJobHunter/1.0 (personal job search tool)"}
        r = requests.get(self.URL, headers=headers, timeout=25)
        r.raise_for_status()
        data = r.json()
        jobs = []
        for x in data:
            if not isinstance(x, dict) or not x.get("position"):
                continue
            location = x.get("location") or "Remote"
            jobs.append(Job(
                source="remoteok",
                external_id=str(x.get("id", "")),
                title=x.get("position", ""),
                company=x.get("company", ""),
                location=location,
                country=location,
                remote_type="Remote",
                posted_at=x.get("date") or x.get("epoch"),
                url=x.get("url", "") or x.get("apply_url", ""),
                description=x.get("description", "") or " ".join(x.get("tags", []) or []),
                posted_verified=bool(x.get("date") or x.get("epoch")),
            ))
        return jobs
