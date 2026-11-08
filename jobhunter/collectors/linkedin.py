import logging
import time
import urllib.parse
import requests
# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup
from .base import Collector
from ..models import Job
from ..filters import relative_to_iso

log = logging.getLogger(__name__)

class LinkedInCollector(Collector):
    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    DEFAULT_QUERIES = [
        "AI Engineer",
        "Machine Learning Engineer",
        "Generative AI Engineer",
        "Junior AI Engineer",
        "LLM Engineer",
        "Computer Vision Engineer",
    ]
    DEFAULT_LOCATIONS = [
        "India",
        "Remote",
        "Bengaluru",
        "Hyderabad",
        "United Arab Emirates",
        "Saudi Arabia",
        "Australia",
        "New Zealand",
        "UK",
        "Canada",
        "USA",
        "Europe",
        "Asia",
        "Africa",
        "South America",
        "North America",
        "Germany",
        "Singapore",
        "Switzerland",
    ]

    def __init__(self, queries=None, locations=None, work_types=None, max_pages_per_combo=1, delay_sec=0.5):
        self.queries = queries or self.DEFAULT_QUERIES
        self.locations = locations or self.DEFAULT_LOCATIONS
        # 1: On-site, 2: Remote, 3: Hybrid. If None, fetch all
        self.work_types = work_types if work_types is not None else [None]
        self.max_pages_per_combo = max_pages_per_combo
        self.delay_sec = delay_sec
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def collect(self):
        jobs = []
        seen_ids = set()

        for q in self.queries:
            for loc in self.locations:
                for wt in self.work_types:
                    for page in range(self.max_pages_per_combo):
                        start = page * 10
                        params = {
                            "keywords": q,
                            "location": loc,
                            "f_TPR": "r86400",  # past 24 hours
                            "start": start,
                        }
                        if wt is not None:
                            params["f_WT"] = str(wt)

                        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
                        try:
                            r = requests.get(url, headers=self.headers, timeout=15)
                            if r.status_code == 429:
                                log.warning("LinkedIn rate limited (429), pausing...")
                                time.sleep(2)
                                break
                            if r.status_code != 200:
                                break

                            soup = BeautifulSoup(r.text, "html.parser")
                            cards = soup.find_all("div", class_="base-search-card")
                            if not cards:
                                break

                            for card in cards:
                                urn = card.get("data-entity-urn") or ""
                                ext_id = urn.split(":")[-1] if urn else ""
                                if not ext_id or ext_id in seen_ids:
                                    continue
                                seen_ids.add(ext_id)

                                title_el = card.find("h3", class_="base-search-card__title")
                                title = title_el.text.strip() if title_el else ""
                                comp_el = card.find("h4", class_="base-search-card__subtitle")
                                company = comp_el.text.strip() if comp_el else ""
                                loc_el = card.find("span", class_="job-search-card__location")
                                location_str = loc_el.text.strip() if loc_el else loc

                                link_el = card.find("a", class_="base-card__full-link")
                                raw_url = link_el.get("href") if link_el else ""
                                clean_url = raw_url.split("?")[0] if raw_url else ""

                                time_el = card.find("time")
                                posted_at = None
                                if time_el:
                                    txt = time_el.text.strip()
                                    dt_attr = time_el.get("datetime")
                                    if txt and "ago" in txt.lower():
                                        posted_at = relative_to_iso(txt) or dt_attr
                                    else:
                                        posted_at = dt_attr or txt

                                # Accurately determine remote type
                                loc_lower = location_str.lower()
                                if wt == 2 or "remote" in loc_lower or loc.lower() == "remote":
                                    remote_type = "Remote"
                                elif wt == 3 or "hybrid" in loc_lower:
                                    remote_type = "Hybrid"
                                elif wt == 1:
                                    remote_type = "On-site"
                                elif "remote" in loc_lower:
                                    remote_type = "Remote"
                                elif "hybrid" in loc_lower:
                                    remote_type = "Hybrid"
                                else:
                                    remote_type = "On-site"

                                jobs.append(Job(
                                    source="linkedin",
                                    external_id=ext_id,
                                    title=title,
                                    company=company,
                                    location=location_str,
                                    country=location_str,
                                    remote_type=remote_type,
                                    posted_at=posted_at,
                                    url=clean_url or raw_url,
                                    description=f"{title} at {company} in {location_str}",
                                    posted_verified=True,
                                ))

                            time.sleep(self.delay_sec)
                        except Exception as e:
                            log.warning("LinkedIn fetch error for %s in %s: %s", q, loc, e)
                            break

        log.info("LinkedInCollector gathered %d unique 24h jobs", len(jobs))
        return jobs
