import logging
import urllib.parse
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from .base import Collector
from ..models import Job

log = logging.getLogger(__name__)

class IndeedCollector(Collector):
    DEFAULT_QUERIES = [
        "AI Engineer",
        "Machine Learning Engineer",
        "Generative AI",
        "AI Intern",
        "Machine Learning Intern",
    ]
    DEFAULT_LOCATIONS = [
        "India",
        "Dubai",
        "Saudi Arabia",
        "Remote",
    ]

    def __init__(self, queries=None, locations=None, delay_sec=1.0):
        self.queries = queries or self.DEFAULT_QUERIES
        self.locations = locations or self.DEFAULT_LOCATIONS
        self.delay_sec = delay_sec

    def collect(self):
        jobs = []
        seen_ids = set()
        try:
            import primp
            client = primp.Client(impersonate="chrome")
        except Exception as e:
            log.warning("Primp client init error for Indeed: %s", e)
            return []

        for q in self.queries:
            for loc in self.locations:
                params = {
                    "q": q,
                    "l": loc,
                    "fromage": "1",  # past 24 hours
                }
                loc_l = loc.lower()
                if any(x in loc_l for x in ("uae", "dubai", "abu dhabi", "sharjah", "emirates")):
                    base_domain = "https://ae.indeed.com"
                elif any(x in loc_l for x in ("saudi", "riyadh", "jeddah", "dammam", "ksa")):
                    base_domain = "https://sa.indeed.com"
                elif any(x in loc_l for x in ("qatar", "doha")):
                    base_domain = "https://qa.indeed.com"
                elif any(x in loc_l for x in ("kuwait",)):
                    base_domain = "https://kw.indeed.com"
                elif any(x in loc_l for x in ("bahrain", "manama")):
                    base_domain = "https://bh.indeed.com"
                elif any(x in loc_l for x in ("oman", "muscat")):
                    base_domain = "https://om.indeed.com"
                elif any(x in loc_l for x in ("egypt", "cairo")):
                    base_domain = "https://eg.indeed.com"
                elif any(x in loc_l for x in ("india", "bengaluru", "bangalore", "delhi", "hyderabad", "pune", "mumbai")):
                    base_domain = "https://in.indeed.com"
                else:
                    base_domain = "https://www.indeed.com"
                url = f"{base_domain}/jobs?{urllib.parse.urlencode(params)}"
                try:
                    r = client.get(url)
                    if r.status_code != 200:
                        continue
                    soup = BeautifulSoup(r.text, "html.parser")
                    beacons = soup.find_all("div", class_="job_seen_beacon")
                    for b in beacons:
                        title_el = b.find("h2", class_="jobTitle") or b.find("a", class_="jcs-JobTitle")
                        if not title_el:
                            continue
                        title = title_el.text.strip()

                        # Extract Job Key (jk)
                        jk = None
                        if title_el.has_attr("data-jk"):
                            jk = title_el.get("data-jk")
                        else:
                            a_tag = b.find("a", {"data-jk": True})
                            if a_tag:
                                jk = a_tag.get("data-jk")
                        if not jk or jk in seen_ids:
                            continue
                        seen_ids.add(jk)

                        comp_el = b.find("span", {"data-testid": "company-name"}) or b.find("span", class_="css-63koeb")
                        company = comp_el.text.strip() if comp_el else "Unknown Company"

                        loc_el = b.find("div", {"data-testid": "text-location"}) or b.find("div", class_="css-1p0sjhy")
                        location_str = loc_el.text.strip() if loc_el else loc

                        loc_lower = (location_str + " " + title).lower()
                        if "remote" in loc_lower or loc.lower() == "remote":
                            remote_type = "Remote"
                        elif "hybrid" in loc_lower:
                            remote_type = "Hybrid"
                        else:
                            remote_type = "On-site"

                        job_url = f"{base_domain}/viewjob?jk={jk}"
                        jobs.append(Job(
                            source="indeed",
                            external_id=str(jk),
                            title=title,
                            company=company,
                            location=location_str,
                            country=location_str,
                            remote_type=remote_type,
                            posted_at=datetime.now(timezone.utc).isoformat(),
                            url=job_url,
                            description=f"{title} at {company} in {location_str}",
                            posted_verified=True,
                        ))
                    time.sleep(self.delay_sec)
                except Exception as e:
                    log.warning("Indeed scrape error for %s in %s: %s", q, loc, e)

        log.info("IndeedCollector gathered %d unique 24h jobs", len(jobs))
        return jobs
