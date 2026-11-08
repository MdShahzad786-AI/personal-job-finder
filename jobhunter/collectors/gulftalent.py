import logging
import time
import urllib.parse
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from .base import Collector
from ..models import Job
from ..filters import relative_to_iso

log = logging.getLogger(__name__)

class GulfTalentCollector(Collector):
    DEFAULT_QUERIES = [
        "ai engineer",
        "machine learning engineer",
        "generative ai",
        "ai intern",
        "machine learning intern",
        "data science",
        "computer vision",
    ]

    def __init__(self, queries=None, delay_sec=1.5):
        self.queries = queries or self.DEFAULT_QUERIES
        self.delay_sec = delay_sec

    def collect(self):
        jobs = []
        seen_ids = set()
        try:
            import primp
            client = primp.Client(impersonate="chrome")
        except Exception as e:
            log.warning("Primp client init error for GulfTalent: %s", e)
            return []

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.gulftalent.com/",
        }

        for q in self.queries:
            try:
                # Use search query on GulfTalent
                url = f"https://www.gulftalent.com/jobs/search?pos_ref={urllib.parse.quote(q)}&frmPositionCountry="
                r = client.get(url, headers=headers)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                items = soup.find_all("a", class_="job-results-item")
                for item in items:
                    title_p = item.find("p", class_="title")
                    if not title_p:
                        continue
                    title = title_p.text.strip()
                    comp_div = item.find("div", class_="company-name")
                    company = comp_div.text.strip() if comp_div else "GulfTalent Employer"
                    loc_div = item.find("div", class_="location")
                    location = loc_div.text.strip() if loc_div else "Middle East"
                    date_div = item.find("div", class_="date")
                    date_str = date_div.text.strip() if date_div else ""

                    ext_id = item.get("data-ga-label") or ""
                    country_dim = item.get("data-ga-dimension-three") or ""
                    raw_href = item.get("href") or ""
                    if not raw_href:
                        continue
                    if not ext_id:
                        ext_id = raw_href.strip("/").split("-")[-1]

                    if ext_id in seen_ids:
                        continue
                    seen_ids.add(ext_id)

                    country = country_dim.replace("-", " ").title() if country_dim else location
                    full_url = f"https://www.gulftalent.com{raw_href}" if raw_href.startswith("/") else raw_href

                    loc_lower = (location + " " + title).lower()
                    if "remote" in loc_lower:
                        remote_type = "Remote"
                    elif "hybrid" in loc_lower:
                        remote_type = "Hybrid"
                    else:
                        remote_type = "On-site"

                    # Parse posted date
                    posted_at = relative_to_iso(date_str) or datetime.now(timezone.utc).isoformat()

                    jobs.append(Job(
                        source="gulftalent",
                        external_id=str(ext_id),
                        title=title,
                        company=company,
                        location=f"{location}, {country}" if country and country not in location else location,
                        country=country,
                        remote_type=remote_type,
                        posted_at=posted_at,
                        url=full_url,
                        description=f"{title} at {company} in {location} ({country})",
                        posted_verified=bool(date_str),
                    ))
                time.sleep(self.delay_sec)
            except Exception as e:
                log.warning("GulfTalent scrape error for query '%s': %s", q, e)

        log.info("GulfTalentCollector gathered %d unique jobs", len(jobs))
        return jobs
