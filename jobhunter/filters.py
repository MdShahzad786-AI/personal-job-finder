import re
from datetime import datetime, timezone, timedelta
from typing import Optional, Union

RELATIVE = re.compile(r"(?P<num>\d+)\s*(?P<unit>minute|minutes|min|mins|hour|hours|hr|hrs|day|days|week|weeks)\s*ago", re.I)
EXP_RANGE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", re.I)
EXP_PLUS = re.compile(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)", re.I)

def _norm(v): return re.sub(r"\s+"," ",(v or "").lower().strip())

def extract_experience(text: str):
    text=text or ""
    m=EXP_RANGE.search(text)
    if m: return float(m.group(1)),float(m.group(2))
    m=EXP_PLUS.search(text)
    if m: return float(m.group(1)),None
    return None,None

KNOWN_REGIONS = {
    "india": [
        "india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "noida",
        "gurgaon", "gurugram", "delhi", "chennai", "kolkata", "ahmedabad", "coimbatore",
        "kochi", "trivandrum", "thiruvananthapuram", "karnataka", "telangana", "maharashtra",
        "tamil nadu", "kerala", "uttar pradesh", "haryana", "gujarat"
    ],
    "united arab emirates": ["uae", "united arab emirates", "dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah", "fujairah"],
    "saudi arabia": ["saudi arabia", "ksa", "riyadh", "jeddah", "dammam", "khobar", "mecca", "medina", "neom", "dhahran"],
    "qatar": ["qatar", "doha", "al rayyan", "lusail"],
    "kuwait": ["kuwait", "kuwait city", "salmiya", "hawally"],
    "bahrain": ["bahrain", "manama", "muharraq", "riffa"],
    "oman": ["oman", "muscat", "salalah", "sohar"],
    "egypt": ["egypt", "cairo", "giza", "alexandria"],
    "singapore": ["singapore"],
    "united kingdom": ["united kingdom", "uk", "london", "manchester", "birmingham", "edinburgh", "cambridge", "oxford"],
    "germany": ["germany", "berlin", "munich", "frankfurt", "hamburg", "stuttgart", "bielefeld", "cologne"],
    "canada": ["canada", "toronto", "vancouver", "waterloo", "montreal", "ottawa", "calgary"]
}

def relative_to_iso(value):
    if not isinstance(value,str): return None
    val = value.strip().lower()
    if val in ("just now", "moments ago", "few seconds ago"):
        return (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
    if val in ("today",):
        return (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    if val in ("yesterday",):
        return (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    m=RELATIVE.search(value.strip())
    if not m: return None
    n=int(m.group('num')); u=m.group('unit').lower()
    if u.startswith(('minute','min')): d=timedelta(minutes=n)
    elif u.startswith(('hour','hr')): d=timedelta(hours=n)
    elif u.startswith('day'): d=timedelta(days=n)
    elif u.startswith('week'): d=timedelta(weeks=n)
    else: return None
    return (datetime.now(timezone.utc)-d).isoformat()

def parse_dt(value: Optional[Union[str,int,float]]):
    if value is None or value=="": return None
    if isinstance(value,(int,float)):
        try:
            ts=float(value); ts=ts/1000 if ts>10_000_000_000 else ts
            return datetime.fromtimestamp(ts,tz=timezone.utc)
        except Exception: return None
    value=str(value).strip()
    if not value: return None
    if re.fullmatch(r"\d+(?:\.\d+)?",value):
        try:
            ts=float(value); ts=ts/1000 if ts>10_000_000_000 else ts
            return datetime.fromtimestamp(ts,tz=timezone.utc)
        except Exception: pass
    rel=relative_to_iso(value)
    if rel: value=rel
    try:
        dt=datetime.fromisoformat(value.replace('Z','+00:00'))
        if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception: pass
    for fmt in ('%Y-%m-%d','%Y-%m-%d %H:%M:%S','%Y/%m/%d','%d-%m-%Y','%b %d, %Y','%B %d, %Y'):
        try: return datetime.strptime(value,fmt).replace(tzinfo=timezone.utc)
        except ValueError: pass
    return None

def is_fresh(v,hours,reject_unknown=False):
    d=parse_dt(v)
    if not d: return not reject_unknown
    return d>=datetime.now(timezone.utc)-timedelta(hours=hours)

def title_allowed(title, cfg, custom_target_roles=None):
    t = _norm(title)
    if any(m in t for m in cfg['target_roles']['senior_markers']):
        return False

    if custom_target_roles:
        for r in custom_target_roles:
            rn = _norm(r)
            if rn in t or t in rn:
                return True
            tokens = [w for w in rn.split() if len(w) > 2]
            if len(tokens) >= 2 and all(tok in t for tok in tokens):
                return True

    families = cfg['target_roles'].get('role_families', {})
    roles = [r for vals in families.values() for r in vals]
    if any(r in t for r in roles):
        return True

    # Flexible AI/ML/Tech title matching, while still excluding unrelated roles.
    ai_tokens = ('ai', 'artificial intelligence', 'machine learning', 'ml', 'genai', 'generative ai', 'llm', 'rag', 'computer vision', 'nlp', 'data science', 'software', 'python', 'developer')
    engineer_tokens = ('engineer', 'developer', 'scientist', 'research', 'intern', 'analyst')
    return any(a in t for a in ai_tokens) and any(b in t for b in engineer_tokens)

def experience_allowed(job,max_years):
    mn,mx=extract_experience((job.title or '')+' '+(job.description or ''))
    job.required_experience_min=mn; job.required_experience_max=mx
    if mn is None: return True
    return mn<=max_years

NATIONAL_RESTRICTIONS = (
    'uae national', 'uae nationals', 'emirati only', 'emiratisation', 'emiratization',
    'saudi national', 'saudi nationals', 'saudization', 'saudisation', 'saudi only',
    'qatari national', 'kuwaiti national', 'bahraini national', 'omanisation', 'omanization',
    'us citizen', 'us citizenship', 'u.s. citizen', 'green card', 'security clearance',
    'top secret', 'ts/sci', 'dod clearance', 'uk national only', 'singaporean only'
)

LOCAL_ONLY_RESTRICTIONS = (
    'must currently reside in', 'must be currently based in', 'candidates currently in uae',
    'candidates currently in dubai', 'candidates currently residing in dubai', 'locally available candidates only',
    'candidates based in uae only', 'candidates based in saudi only',
    'must have valid uae residence visa', 'valid residence visa required',
    'must have transferable iqama', 'transferable iqama required',
    'no visa sponsorship', 'no sponsorship available', 'unable to sponsor visa',
    'cannot sponsor visa', 'no sponsorship provided', 'own visa only'
)

FOREIGN_REMOTE_RESTRICTIONS = (
    'us only', 'usa only', 'united states only', 'uk only', 'united kingdom only',
    'eu only', 'europe only', 'canada only', 'north america only', 'latam only',
    'must be based in the us', 'must be located in the us', 'remote within us',
    'remote within the us', 'remote within usa', 'remote within uk', 'remote within europe'
)

def is_eligible_for_india_applicant(job):
    """
    Evaluates whether an applicant currently residing in India is eligible to apply for this job.
    Returns: (eligible: bool, reason: str)
    """
    blob = _norm(' '.join([
        getattr(job, 'title', '') or '',
        getattr(job, 'location', '') or '',
        getattr(job, 'country', '') or '',
        getattr(job, 'remote_type', '') or '',
        getattr(job, 'description', '') or ''
    ]))

    # 1. Hard restriction: Local citizens/nationals only
    for term in NATIONAL_RESTRICTIONS:
        if term in blob:
            return False, f"Restricted: {term.title()}"

    # 2. Hard restriction: Local residency only / No visa sponsorship
    for term in LOCAL_ONLY_RESTRICTIONS:
        if term in blob:
            return False, f"Restricted: {term.title()}"

    # 3. Country-restricted remote that excludes India
    is_remote = 'remote' in blob
    if is_remote:
        for term in FOREIGN_REMOTE_RESTRICTIONS:
            if term in blob and not any(x in blob for x in ('india', 'worldwide', 'anywhere', 'global')):
                return False, f"Remote restricted to {term.upper()} (excludes India)"

    # 4. India-based position
    if any(c in blob for c in ('india', 'bengaluru', 'bangalore', 'hyderabad', 'pune', 'mumbai', 'noida', 'gurugram', 'gurgaon', 'delhi', 'chennai', 'kolkata')):
        return True, "India: Domestic hire"

    # 5. Worldwide / Global Remote
    if any(x in blob for x in ('worldwide', 'anywhere', 'work from anywhere', 'global remote', 'all countries')):
        return True, "Worldwide Remote: Open to India"

    # 6. Middle East hubs (UAE, Dubai, Saudi, Qatar, Kuwait, Oman, Bahrain)
    if any(x in blob for x in ('dubai', 'uae', 'abu dhabi', 'sharjah', 'saudi', 'riyadh', 'jeddah', 'dammam', 'qatar', 'doha', 'kuwait', 'oman', 'bahrain')):
        return True, "Middle East: Open to Indian applicants (relocation/visa)"

    # 7. Other Remote roles without country restriction
    if is_remote:
        return True, "Remote: Open to Indian applicants"

    # 8. International positions with explicit visa sponsorship
    if any(x in blob for x in ('visa sponsorship', 'relocation assistance', 'relocation support', 'sponsor visa')):
        return True, "International with Visa Sponsorship"

    return True, "Eligible"

def location_allowed(job, cfg, custom_locations=None):
    # Verify candidate from India is eligible
    eligible, _ = is_eligible_for_india_applicant(job)
    if not eligible:
        return False

    loc = _norm(' '.join([job.location or '', job.country or '', job.remote_type or '']))

    if custom_locations:
        for cl in custom_locations:
            cl_norm = _norm(cl)
            if cl_norm in loc:
                return True
            if cl_norm == 'remote' and 'remote' in loc:
                return True

    allowed_countries = [_norm(x) for x in cfg['locations']['countries']]
    
    # Check configured country names directly
    if any(c in loc for c in allowed_countries): return True
    
    # Check known cities/regions for allowed countries
    for country, cities in KNOWN_REGIONS.items():
        if any(c in allowed_countries for c in [country, country.replace(" ", "")]):
            if any(city in loc for city in cities):
                return True

    # Remote eligibility check
    if cfg['locations'].get('remote_enabled', True) and 'remote' in loc:
        if any(x in loc for x in ['worldwide', 'anywhere', 'global', 'all countries', 'work from anywhere']):
            return cfg['locations']['accept_worldwide_remote']
        if any(x in loc for x in ['india', 'bengaluru', 'bangalore', 'hyderabad', 'pune', 'delhi', 'mumbai']):
            return cfg['locations']['accept_india_remote']
        return cfg['locations'].get('keep_unknown_remote_for_review',True)
    return False

def classify_remote_eligibility(job):
    blob=_norm(' '.join([job.location or '', job.country or '', job.remote_type or '', job.description or '']))
    if 'remote' not in blob:
        return 'not_remote'
    if any(x in blob for x in ['worldwide','anywhere','global remote','work from anywhere']):
        return 'worldwide'
    if 'india' in blob and not any(x in blob for x in ['us only','usa only','uk only','eu only','europe only','canada only']):
        return 'india_eligible'
    restricted=['us only','usa only','united states only','uk only','united kingdom only','eu only','europe only','canada only','must be based in','remote within']
    if any(x in blob for x in restricted):
        return 'country_restricted'
    return 'unknown_remote'
