# Build status

## Phase 1: Foundation ✅
Config, SQLite database, dashboard base, logging-ready pipeline, tests.

## Phase 2: Resume profile ✅
Candidate profile integrated; actual PDF included; PDF extraction utility and validation command added.

## Phase 3: Job collection ✅
Remotive, Arbeitnow, RemoteOK, Greenhouse, Lever, optional SerpAPI/Google Jobs collectors.

## Phase 4: Filtering ✅
24-hour freshness, 0–2 year experience, title/seniority filtering, target-country filtering and remote eligibility classification.

## Phase 5: Deduplication ✅
Cross-source fingerprint now ignores portal-specific external IDs and normalizes company/title/location.

## Phase 6: Resume matching ✅
Deterministic weighted scoring, matched/missing skills, project alignment and truthful resume suggestions.

## Phase 7: Email ✅
HTML digest with location summary, score buckets, missing skills, suggestions and direct apply links.

## Phase 8: Scheduling / production workflow ✅
09:15 IST GitHub Actions schedule, automated tests before daily run, cached SQLite history, dashboard application tracking.

## Recommended next production enhancement
For long-term cloud hosting, use managed PostgreSQL/Supabase instead of SQLite cache and deploy the dashboard on a persistent hosting platform.
