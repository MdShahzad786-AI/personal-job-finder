from dataclasses import dataclass
from typing import Optional

@dataclass
class Job:
    source: str
    external_id: str
    title: str
    company: str
    location: str
    country: str
    remote_type: str
    posted_at: Optional[str]
    url: str
    description: str
    required_experience_min: Optional[float] = None
    required_experience_max: Optional[float] = None
    remote_eligibility: str = "unknown"
    posted_verified: bool = False
    canonical_url: str = ""
