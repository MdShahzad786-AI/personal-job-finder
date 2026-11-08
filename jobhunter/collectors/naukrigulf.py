import logging
import time
import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from .base import Collector
from ..models import Job
from ..filters import relative_to_iso

log = logging.getLogger(__name__)

class NaukriGulfCollector(Collector):
    TARGET_PATHS = [
        "ai-engineer-jobs",
        "machine-learning-jobs",
        "generative-ai-jobs",
        "data-science-jobs",
        "artificial-intelligence-jobs",
        "ai-jobs-in-dubai",
        "ai-jobs-in-uae",
        "ai-jobs-in-saudi-arabia",
    ]

    def __init__(self, target_paths=None, delay_sec=2.0):
        self.target_paths = target_paths or self.TARGET_PATHS
        self.delay_sec = delay_sec

    def collect(self):
        jobs = []
        seen_ids = set()

        try:
            from curl_cffi import requests as cffi_requests
            use_cffi = True
        except ImportError:
            use_cffi = False

        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "sec-ch-ua": '"Google Chrome";v="130", "Chromium";v="130", "Not?A_Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        }

        for path in self.target_paths:
            url = f"https://www.naukrigulf.com/{path}"
            try:
                if use_cffi:
                    r = cffi_requests.get(url, headers=headers, impersonate="chrome120", timeout=12)
                else:
                    import primp
                    client = primp.Client(impersonate="chrome")
                    r = client.get(url, headers=headers)

                if r.status_code != 200:
                    continue

                soup = BeautifulSoup(r.text, "html.parser")
                # Look for job links
                job_links = soup.find_all("a", class_=lambda c: c and "info-position" in c)
                for a_tag in job_links:
                    raw_href = a_tag.get("href") or ""
                    if not raw_href or raw_href in seen_ids:
                        continue
                    seen_ids.add(raw_href)

                    p_title = a_tag.find("p") or a_tag
                    title = p_title.text.strip()
                    if not title:
                        continue

                    # Extract Job ID from URL (e.g. -jid-123456)
                    m = re.search(r"jid[=-]?(\d+)", raw_href)
                    ext_id = m.group(1) if m else raw_href.strip("/").split("/")[-1]

                    parent = a_tag.find_parent("article") or a_tag.find_parent("div")
                    company = "NaukriGulf Employer"
                    location = "Middle East"
                    exp_text = ""

                    if parent:
                        comp_el = parent.find("a", class_=lambda c: c and "info-org" in c) or parent.find("span", class_="org-name")
                        if comp_el:
                            company = comp_el.text.strip()

                        # Extract details from list items
                        li_items = parent.find_all("li")
                        for li in li_items:
                            text = li.text.strip()
                            if any(k in text.lower() for k in ("dubai", "uae", "emirates", "saudi", "riyadh", "qatar", "kuwait", "egypt", "oman", "bahrain")):
                                location = text
                            elif any(k in text.lower() for k in ("year", "yr", "exp")):
                                exp_text = text

                    full_url = f"https://www.naukrigulf.com{raw_href}" if raw_href.startswith("/") else raw_href

                    loc_lower = (location + " " + title).lower()
                    if "remote" in loc_lower:
                        remote_type = "Remote"
                    elif "hybrid" in loc_lower:
                        remote_type = "Hybrid"
                    else:
                        remote_type = "On-site"

                    jobs.append(Job(
                        source="naukrigulf",
                        external_id=str(ext_id),
                        title=title,
                        company=company,
                        location=location,
                        country=location,
                        remote_type=remote_type,
                        posted_at=datetime.now(timezone.utc).isoformat(),
                        url=full_url,
                        description=f"{title} at {company} in {location}. Experience: {exp_text}",
                        posted_verified=True,
                    ))

                time.sleep(self.delay_sec)
            except Exception as e:
                log.warning("NaukriGulf scrape warning for %s: %s", path, e)

        log.info("NaukriGulfCollector gathered %d unique jobs", len(jobs))
        return jobs
