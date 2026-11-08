import logging
import time
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from .base import Collector
from ..models import Job

log = logging.getLogger(__name__)

class BaytCollector(Collector):
    TARGET_PATHS = [
        ("UAE", "/en/uae/jobs/ai-jobs/"),
        ("UAE", "/en/uae/jobs/machine-learning-jobs/"),
        ("UAE", "/en/uae/jobs/data-science-jobs/"),
        ("UAE", "/en/uae/jobs/intern-jobs/"),
        ("Saudi Arabia", "/en/saudi-arabia/jobs/ai-jobs/"),
        ("Saudi Arabia", "/en/saudi-arabia/jobs/machine-learning-jobs/"),
        ("Saudi Arabia", "/en/saudi-arabia/jobs/intern-jobs/"),
        ("Qatar", "/en/qatar/jobs/ai-jobs/"),
        ("Qatar", "/en/qatar/jobs/intern-jobs/"),
        ("Kuwait", "/en/kuwait/jobs/ai-jobs/"),
        ("Egypt", "/en/egypt/jobs/ai-jobs/"),
        ("International", "/en/international/jobs/ai-engineer-jobs/"),
        ("International", "/en/international/jobs/ai-intern-jobs/"),
    ]

    def __init__(self, target_paths=None, delay_sec=1.0):
        self.target_paths = target_paths or self.TARGET_PATHS
        self.delay_sec = delay_sec

    def collect(self):
        jobs = []
        seen_ids = set()
        try:
            import primp
            client = primp.Client(impersonate="chrome")
        except Exception as e:
            log.warning("Primp client init error for Bayt: %s", e)
            return []

        for country_label, path in self.target_paths:
            url = f"https://www.bayt.com{path}"
            try:
                r = client.get(url)
                if r.status_code != 200:
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                cards = soup.find_all("li", class_="has-pointer-d")
                for cd in cards:
                    h2 = cd.find("h2")
                    if not h2:
                        continue
                    a_tag = h2.find("a")
                    title = h2.text.strip()
                    raw_link = a_tag.get("href") if a_tag else ""
                    if not raw_link or raw_link in seen_ids:
                        continue
                    seen_ids.add(raw_link)

                    # Extract Job ID from link (e.g. -5486409/)
                    ext_id = raw_link.strip("/").split("-")[-1]

                    comp_el = cd.find("b")
                    company = comp_el.text.strip() if comp_el and comp_el.text.strip() else "Bayt Employer"

                    loc_el = cd.find("span", class_="t-mute")
                    loc_text = loc_el.text.strip() if loc_el else country_label

                    loc_lower = (loc_text + " " + title).lower()
                    if "remote" in loc_lower:
                        remote_type = "Remote"
                    elif "hybrid" in loc_lower:
                        remote_type = "Hybrid"
                    else:
                        remote_type = "On-site"

                    full_url = f"https://www.bayt.com{raw_link}" if raw_link.startswith("/") else raw_link
                    jobs.append(Job(
                        source="bayt",
                        external_id=str(ext_id),
                        title=title,
                        company=company,
                        location=f"{loc_text}, {country_label}",
                        country=country_label,
                        remote_type=remote_type,
                        posted_at=datetime.now(timezone.utc).isoformat(),
                        url=full_url,
                        description=f"{title} at {company} in {country_label}",
                        posted_verified=True,
                    ))
                time.sleep(self.delay_sec)
            except Exception as e:
                log.warning("Bayt scrape error for %s: %s", path, e)

        log.info("BaytCollector gathered %d unique jobs", len(jobs))
        return jobs
