import hashlib
import re
from urllib.parse import urlsplit, urlunsplit

LEGAL = re.compile(r"\b(inc|inc\.|ltd|limited|llc|pvt|private|corp|corporation|gmbh|plc|co\.?|company)\b", re.I)


def clean_text(value: str) -> str:
    value = (value or "").lower().strip()
    value = value.replace("artificial intelligence", "ai")
    value = value.replace("machine-learning", "machine learning")
    value = re.sub(r"[^a-z0-9+#./ -]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_company(value: str) -> str:
    value = LEGAL.sub("", clean_text(value))
    return re.sub(r"\s+", " ", value).strip(" ,-.")


def normalize_title(value: str) -> str:
    t = clean_text(value)
    replacements = {
        "jr.": "junior", "jr ": "junior ", "gen ai": "generative ai",
        "genai": "generative ai", "ai ml": "ai/ml"
    }
    for a, b in replacements.items():
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    try:
        p = urlsplit(url)
        # Remove tracking query/fragment to improve cross-source dedupe.
        return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), "", ""))
    except Exception:
        return url


def fingerprint(title: str, company: str, location: str) -> str:
    # Intentionally excludes source/external id so the same vacancy mirrored across
    # LinkedIn/Indeed/ATS can collapse into one record.
    base = "|".join([normalize_title(title), normalize_company(company), clean_text(location)])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
