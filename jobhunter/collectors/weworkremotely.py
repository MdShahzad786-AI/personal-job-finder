import logging
import xml.etree.ElementTree as ET
import requests
from .base import Collector
from ..models import Job

log = logging.getLogger(__name__)

class WeWorkRemotelyCollector(Collector):
    FEED_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"

    def collect(self):
        jobs = []
        try:
            r = requests.get(self.FEED_URL, headers={"User-Agent": "AIJobHunter/1.0"}, timeout=20)
            if r.status_code != 200:
                log.warning("WWR returned status %s", r.status_code)
                return []
            root = ET.fromstring(r.text)
            channel = root.find("channel")
            if channel is None:
                return []
            for item in channel.findall("item"):
                raw_title = (item.findtext("title") or "").strip()
                company = "Remote Company"
                title = raw_title
                if ":" in raw_title:
                    parts = raw_title.split(":", 1)
                    company = parts[0].strip()
                    title = parts[1].strip()

                link = (item.findtext("link") or "").strip()
                pub_date = (item.findtext("pubDate") or "").strip()
                desc = (item.findtext("description") or "").strip()
                guid = (item.findtext("guid") or link).strip()

                jobs.append(Job(
                    source="weworkremotely",
                    external_id=guid,
                    title=title,
                    company=company,
                    location="Remote Worldwide",
                    country="Remote",
                    remote_type="Remote",
                    posted_at=pub_date,
                    url=link,
                    description=desc,
                    posted_verified=bool(pub_date),
                ))
        except Exception as e:
            log.warning("WWR collection failed: %s", e)
        log.info("WeWorkRemotelyCollector collected %d jobs", len(jobs))
        return jobs
