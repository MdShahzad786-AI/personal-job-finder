import logging
from .config import load_config, load_candidate, database_path
from .db import init_db, upsert_job, get_unemailed_jobs, mark_emailed, record_collection_run, record_email_run, cleanup_old_jobs
from .normalize import fingerprint, canonicalize_url
from .filters import is_fresh, title_allowed, experience_allowed, location_allowed
from .match import score_job
from .collectors.remotive import RemotiveCollector
from .collectors.arbeitnow import ArbeitnowCollector
from .collectors.remoteok import RemoteOKCollector
from .collectors.greenhouse import GreenhouseCollector
from .collectors.lever import LeverCollector
from .collectors.ashby import AshbyCollector
from .collectors.adzuna import AdzunaCollector
from .collectors.serpapi_google_jobs import SerpApiGoogleJobsCollector
from .collectors.linkedin import LinkedInCollector
from .collectors.indeed import IndeedCollector
from .collectors.bayt import BaytCollector
from .collectors.gulftalent import GulfTalentCollector
from .collectors.naukrigulf import NaukriGulfCollector
from .collectors.himalayas import HimalayasCollector
from .collectors.jobicy import JobicyCollector
from .collectors.weworkremotely import WeWorkRemotelyCollector

log = logging.getLogger(__name__)


def build_collectors(cfg, custom_queries=None, custom_locations=None):
    s = cfg['sources']
    out = []
    
    queries = list(custom_queries) if custom_queries else None
    locations = list(custom_locations) if custom_locations else None

    if s.get('linkedin', {}).get('enabled', True):
        lk = s.get('linkedin', {})
        out.append(LinkedInCollector(
            queries=queries or lk.get('queries'),
            locations=locations or lk.get('locations'),
            work_types=lk.get('work_types'),
            max_pages_per_combo=lk.get('max_pages_per_combo', 1),
            delay_sec=lk.get('delay_sec', 0.5)
        ))
    if s.get('indeed', {}).get('enabled', True):
        ind = s.get('indeed', {})
        out.append(IndeedCollector(
            queries=queries or ind.get('queries'),
            locations=locations or ind.get('locations'),
            delay_sec=ind.get('delay_sec', 0.8)
        ))
    if s.get('bayt', {}).get('enabled', True):
        out.append(BaytCollector())
    if s.get('gulftalent', {}).get('enabled', True):
        gt = s.get('gulftalent', {})
        out.append(GulfTalentCollector(
            queries=queries or gt.get('queries'),
            delay_sec=gt.get('delay_sec', 1.0)
        ))
    if s.get('naukrigulf', {}).get('enabled', True):
        ng = s.get('naukrigulf', {})
        out.append(NaukriGulfCollector(
            target_paths=ng.get('target_paths'),
            delay_sec=ng.get('delay_sec', 1.5)
        ))
    if s.get('himalayas', {}).get('enabled', True):
        out.append(HimalayasCollector())
    if s.get('jobicy', {}).get('enabled', True):
        out.append(JobicyCollector())
    if s.get('weworkremotely', {}).get('enabled', True):
        out.append(WeWorkRemotelyCollector())
    if s.get('remotive', {}).get('enabled'):
        out.append(RemotiveCollector())
    if s.get('arbeitnow', {}).get('enabled'):
        out.append(ArbeitnowCollector())
    if s.get('remoteok', {}).get('enabled'):
        out.append(RemoteOKCollector())
    if s.get('greenhouse', {}).get('enabled'):
        out.append(GreenhouseCollector(s['greenhouse'].get('companies', [])))
    if s.get('lever', {}).get('enabled'):
        out.append(LeverCollector(s['lever'].get('companies', [])))
    if s.get('ashby', {}).get('enabled'):
        out.append(AshbyCollector(s['ashby'].get('companies', [])))
    if s.get('adzuna', {}).get('enabled'):
        out.append(AdzunaCollector(s['adzuna'].get('countries', []), queries or s['adzuna'].get('queries', [])))
    if s.get('serpapi_google_jobs', {}).get('enabled'):
        x = s['serpapi_google_jobs']
        out.append(SerpApiGoogleJobsCollector(queries or x.get('queries', []), locations or x.get('countries', [])))
    return out


def run_pipeline(
    send_digest: bool = False,
    custom_candidate: dict = None,
    custom_queries: list = None,
    custom_locations: list = None,
    freshness_hours: int = None,
    min_match_score: int = None
):
    from .emailer import send_email
    cfg = load_config()
    cand = custom_candidate if custom_candidate else load_candidate()
    db = database_path()
    init_db(db)

    f = cfg['filters']
    actual_freshness = freshness_hours if freshness_hours is not None else f.get('freshness_hours', 24)
    actual_min_score = min_match_score if min_match_score is not None else f.get('min_match_score', 50)
    
    # Calculate candidate experience allowance
    cand_exp = float(cand.get('experience_years', 0))
    max_exp = max(2.0, cand_exp + 1.0)

    retention_days = f.get('retention_days', 3)
    purged = cleanup_old_jobs(db, days=retention_days)
    if purged > 0:
        log.info('Automatically deleted %d jobs older than %d days from database', purged, retention_days)

    stats = {
        'sources_attempted': 0, 'sources_failed': 0, 'raw_jobs': 0, 'title_passed': 0,
        'freshness_passed': 0, 'experience_passed': 0, 'location_passed': 0,
        'score_passed': 0, 'inserted': 0, 'duplicates': 0
    }
    errors = []
    jobs = []
    source_counts = {}

    target_roles = list(custom_queries) if custom_queries else cand.get('target_roles', [])
    locations = list(custom_locations) if custom_locations else None

    collectors = build_collectors(cfg, custom_queries=target_roles, custom_locations=locations)
    for col in collectors:
        stats['sources_attempted'] += 1
        name = col.__class__.__name__
        try:
            got = col.collect()
            jobs.extend(got)
            source_counts[name] = len(got)
            log.info('%s collected %s jobs', name, len(got))
        except Exception as e:
            stats['sources_failed'] += 1
            errors.append(f'{name}: {e}')
            source_counts[name] = 'FAILED'
            log.exception('Collector failed: %s', e)

    stats['raw_jobs'] = len(jobs)

    for job in jobs:
        if not title_allowed(job.title, cfg, custom_target_roles=target_roles):
            continue
        stats['title_passed'] += 1

        if not is_fresh(job.posted_at, actual_freshness, f.get('reject_unknown_freshness', False)):
            continue
        stats['freshness_passed'] += 1

        if not experience_allowed(job, max_exp):
            continue
        stats['experience_passed'] += 1

        if not location_allowed(job, cfg, custom_locations=locations):
            continue
        stats['location_passed'] += 1

        job.canonical_url = canonicalize_url(job.url)
        m = score_job(job, cand, cfg)
        if m['score'] < actual_min_score:
            continue
        stats['score_passed'] += 1

        fp = fingerprint(job.title, job.company, job.location)
        if upsert_job(db, job, fp, m):
            stats['inserted'] += 1
        else:
            stats['duplicates'] += 1

    stats['source_counts'] = source_counts
    record_collection_run(db, {k: v for k, v in stats.items() if k != 'source_counts'}, '\n'.join(errors))

    rows = get_unemailed_jobs(db, actual_min_score)
    if send_digest and (rows or cfg['email'].get('send_when_zero_jobs', False)):
        chosen = rows[:cfg['email']['top_jobs_limit']]
        try:
            recipient = send_email(chosen, cfg['email']['subject_prefix'])
            mark_emailed(db, [r['id'] for r in chosen])
            record_email_run(db, recipient, len(chosen), True)
        except Exception as e:
            record_email_run(db, '', len(chosen), False, str(e))
            raise

    return stats, rows
