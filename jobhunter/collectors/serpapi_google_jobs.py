import os
import requests
from urllib.parse import quote_plus
from .base import Collector
from ..models import Job
from ..filters import relative_to_iso

COUNTRY_GL = {
    "India": "in", "United Arab Emirates": "ae", "Saudi Arabia": "sa", "Qatar": "qa",
    "Singapore": "sg", "United Kingdom": "uk", "Germany": "de", "Canada": "ca"
}

class SerpApiGoogleJobsCollector(Collector):
    def __init__(self, queries, countries):
        self.queries = queries or []
        self.countries = countries or []
        self.api_key = os.getenv("SERPAPI_API_KEY", "")

    def collect(self):
        if not self.api_key:
            return []
        out = []
        for country in self.countries:
            gl = COUNTRY_GL.get(country, "in")
            for q in self.queries:
                params = {
                    "engine": "google_jobs", "q": q, "gl": gl,
                    "hl": "en", "api_key": self.api_key
                }
                r = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
                r.raise_for_status()
                for x in r.json().get("jobs_results", []):
                    ext = x.get("detected_extensions", {}) or {}
                    posted_text = ext.get("posted_at") or ""
                    apply_options = x.get("apply_options") or []
                    direct = ""
                    if apply_options:
                        direct = apply_options[0].get("link", "")
                    url = direct or x.get("share_link", "")
                    location = x.get("location", "") or country
                    out.append(Job(
                        source="serpapi_google_jobs",
                        external_id=str(x.get("job_id", "")),
                        title=x.get("title", ""),
                        company=x.get("company_name", ""),
                        location=location,
                        country=country,
                        remote_type="Remote" if ext.get("work_from_home") else "Unknown",
                        posted_at=relative_to_iso(posted_text) or posted_text or None,
                        url=url,
                        description=x.get("description", ""),
                        posted_verified=bool(posted_text),
                    ))
        return out
