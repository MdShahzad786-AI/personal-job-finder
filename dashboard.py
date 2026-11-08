import io
from datetime import datetime, timezone, timedelta
from pathlib import Path
import html
import pandas as pd
import streamlit as st

from jobhunter.config import database_path, load_candidate, load_config
from jobhunter.db import init_db, dashboard_rows, update_job_state, cleanup_old_jobs
from jobhunter.filters import parse_dt, is_eligible_for_india_applicant
from jobhunter.match import score_job
from jobhunter.pipeline import run_pipeline
from jobhunter.resume.parser import extract_resume_text
from jobhunter.resume.ai_agent import AIResumeAgent

# Page configuration
st.set_page_config(
    page_title='AI Job Hunter Pro',
    page_icon='🎯',
    layout='wide',
    initial_sidebar_state='collapsed'
)

# Initialize database & cleanup old jobs
db = database_path()
init_db(db)
cfg = load_config()
retention_days = cfg.get('filters', {}).get('retention_days', 3)
cleanup_old_jobs(db, days=retention_days)

# -------------------------------------------------------------
# Custom Modern SaaS CSS Injection
# -------------------------------------------------------------
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

  html, body, [class*="css"] {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  }

  /* App Background */
  .stApp {
      background: radial-gradient(circle at 12% 10%, rgba(99, 102, 241, 0.09) 0%, transparent 40%),
                  radial-gradient(circle at 88% 90%, rgba(236, 72, 153, 0.07) 0%, transparent 40%),
                  #090d16;
      color: #f8fafc;
  }

  /* Hero Header */
  .hero-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 0.78rem;
      font-weight: 600;
      color: #818cf8;
      background: rgba(99, 102, 241, 0.12);
      border: 1px solid rgba(129, 140, 248, 0.3);
      margin-bottom: 0.8rem;
  }

  .hero-title {
      font-size: 2.6rem;
      font-weight: 800;
      line-height: 1.15;
      background: linear-gradient(135deg, #ffffff 15%, #c7d2fe 55%, #f472b6 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.03em;
      margin-bottom: 0.4rem;
  }

  .hero-sub {
      color: #94a3b8;
      font-size: 1.05rem;
      margin-bottom: 1.8rem;
      line-height: 1.5;
  }

  /* Glassmorphism Card Container */
  .glass-card {
      background: rgba(17, 24, 39, 0.65);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 1.4rem;
      margin-bottom: 1.2rem;
      box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35);
  }

  /* Metric cards */
  div[data-testid="stMetric"] {
      background: rgba(30, 41, 59, 0.4) !important;
      border: 1px solid rgba(255, 255, 255, 0.07) !important;
      border-radius: 14px !important;
      padding: 0.9rem 1.1rem !important;
      box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.25) !important;
  }
  div[data-testid="stMetric"]:hover {
      border-color: rgba(99, 102, 241, 0.4) !important;
  }

  /* Modern Job Card */
  .job-card {
      background: linear-gradient(145deg, rgba(23, 32, 54, 0.65) 0%, rgba(13, 19, 33, 0.85) 100%);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 16px;
      padding: 1.4rem;
      margin-bottom: 1.1rem;
      transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 4px 20px -4px rgba(0, 0, 0, 0.35);
  }
  .job-card:hover {
      transform: translateY(-3px);
      border-color: rgba(129, 140, 248, 0.5);
      box-shadow: 0 16px 36px -8px rgba(99, 102, 241, 0.22);
  }

  .job-title {
      font-size: 1.25rem;
      font-weight: 700;
      color: #ffffff;
      margin-bottom: 0.3rem;
  }
  .job-company {
      font-size: 0.95rem;
      color: #94a3b8;
      font-weight: 500;
      margin-bottom: 0.8rem;
  }

  /* Match Badges */
  .badge-high {
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.3));
      color: #34d399;
      border: 1px solid rgba(52, 211, 153, 0.4);
      padding: 4px 11px;
      border-radius: 9999px;
      font-weight: 700;
      font-size: 0.85rem;
      box-shadow: 0 0 14px rgba(16, 185, 129, 0.2);
  }
  .badge-med {
      background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(14, 165, 233, 0.3));
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.4);
      padding: 4px 11px;
      border-radius: 9999px;
      font-weight: 700;
      font-size: 0.85rem;
      box-shadow: 0 0 14px rgba(56, 189, 248, 0.2);
  }
  .badge-low {
      background: rgba(148, 163, 184, 0.15);
      color: #cbd5e1;
      border: 1px solid rgba(148, 163, 184, 0.3);
      padding: 4px 11px;
      border-radius: 9999px;
      font-weight: 600;
      font-size: 0.85rem;
  }

  /* Tag Pills */
  .tag-pill {
      background: rgba(30, 41, 59, 0.7);
      color: #94a3b8;
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 3px 9px;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 500;
      display: inline-block;
      margin-right: 5px;
      margin-bottom: 5px;
  }
  .skill-match {
      background: rgba(16, 185, 129, 0.12);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 3px 9px;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 600;
      display: inline-block;
      margin-right: 4px;
      margin-bottom: 4px;
  }
  .skill-miss {
      background: rgba(244, 63, 94, 0.1);
      color: #fb7185;
      border: 1px solid rgba(244, 63, 94, 0.25);
      padding: 3px 9px;
      border-radius: 8px;
      font-size: 0.78rem;
      display: inline-block;
      margin-right: 4px;
      margin-bottom: 4px;
  }

  /* Suggestion Tip Box */
  .tip-box {
      background: rgba(99, 102, 241, 0.08);
      border-left: 3px solid #818cf8;
      padding: 9px 13px;
      border-radius: 0 10px 10px 0;
      font-size: 0.82rem;
      color: #c7d2fe;
      margin: 0.7rem 0;
  }

  /* Custom Gradient Apply Button */
  .apply-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
      color: #ffffff !important;
      font-weight: 600;
      font-size: 0.9rem;
      padding: 7px 18px;
      border-radius: 10px;
      text-decoration: none;
      box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
      transition: all 0.2s ease;
  }
  .apply-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(99, 102, 241, 0.55);
      opacity: 0.95;
  }

  /* Primary Button Styling */
  .stButton > button[kind="primary"] {
      background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%) !important;
      color: white !important;
      font-weight: 700 !important;
      border: none !important;
      border-radius: 12px !important;
      padding: 0.65rem 1.4rem !important;
      box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4) !important;
      transition: all 0.2s ease !important;
  }
  .stButton > button[kind="primary"]:hover {
      transform: translateY(-2px) !important;
      box-shadow: 0 8px 25px rgba(99, 102, 241, 0.65) !important;
  }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------
if 'active_candidate' not in st.session_state:
    st.session_state['active_candidate'] = load_candidate()
    st.session_state['resume_filename'] = "Built-in (Mohammed_Shahzad_Resume.pdf)"

if 'freshness_filter' not in st.session_state:
    st.session_state['freshness_filter'] = 'Past 24 Hours (Fresh)'

if 'custom_roles' not in st.session_state:
    st.session_state['custom_roles'] = []

if 'custom_locs' not in st.session_state:
    st.session_state['custom_locs'] = []

if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = '🎴 Modern Cards'

cand = st.session_state['active_candidate']

# -------------------------------------------------------------
# Hero Header
# -------------------------------------------------------------
st.markdown("""
<div style="margin-bottom: 1.5rem;">
  <div class="hero-pill">
    <span>●</span> <span>Live AI Job Engine</span> <span>•</span> <span>15+ Portals Connected</span>
  </div>
  <div class="hero-title">🎯 AI Job Hunter Pro & Intelligent Matcher</div>
  <div class="hero-sub">Upload your resume, customize your target roles and locations, and fetch verified fresh postings under 24 hours with deterministic match scoring.</div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# STEP 1: Upload Resume & AI Agent Analysis
# -------------------------------------------------------------
with st.container():
    st.markdown("### 📄 Step 1: Upload Resume & AI Agent Analysis")

    col_up1, col_up2 = st.columns([3, 1])
    with col_up1:
        uploaded_file = st.file_uploader(
            "Upload candidate resume (PDF, DOCX, TXT):",
            type=["pdf", "docx", "txt"],
            help="Upload any candidate's resume. The AI Agent extracts credentials, skills, and infers matching roles."
        )

    with col_up2:
        st.write("")
        st.write("")
        if st.button("🔄 Use Default Resume (Mohammed Shahzad)"):
            default_path = Path("resume/Mohammed_Shahzad_Resume.pdf")
            if default_path.exists():
                raw_text = extract_resume_text(default_path)
                agent = AIResumeAgent()
                st.session_state['active_candidate'] = agent.analyze(raw_text, filename=default_path.name)
                st.session_state['resume_filename'] = default_path.name
                st.session_state['custom_roles'] = []
                st.session_state['custom_locs'] = []
                st.success("Loaded default resume for Mohammed Shahzad!")
                st.rerun()

    # Process uploaded resume
    if uploaded_file is not None:
        if st.session_state.get('last_uploaded_name') != uploaded_file.name:
            with st.spinner("🤖 AI Agent is parsing resume credentials and skills..."):
                file_bytes = uploaded_file.read()
                raw_text = extract_resume_text(file_bytes, filename=uploaded_file.name)
                agent = AIResumeAgent()
                profile = agent.analyze(raw_text, filename=uploaded_file.name)
                st.session_state['active_candidate'] = profile
                st.session_state['resume_filename'] = uploaded_file.name
                st.session_state['last_uploaded_name'] = uploaded_file.name
                st.session_state['custom_roles'] = []
                st.session_state['custom_locs'] = []
                st.success(f"✅ Analyzed: **{profile.get('name', 'Candidate')}** ({uploaded_file.name})")
                st.rerun()

cand = st.session_state['active_candidate']

# AI Profile Insights Card
with st.expander("🧠 AI Agent Profile Assessment & Extracted Credentials", expanded=True):
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("👤 Candidate", cand.get('name', 'Candidate'))
    exp_val = float(cand.get('experience_years', 0))
    exp_label = "Fresher (0–6 mos)" if exp_val <= 0.5 else f"{exp_val} Years"
    col_b.metric("⏳ Inferred Exp", exp_label)
    edu = cand.get('education', {})
    col_c.metric("🎓 Education", f"{edu.get('degree', 'Degree')} ({edu.get('year', '2026')})")
    col_d.metric("📍 Detected Location", cand.get('location', 'India'))

    if cand.get('summary'):
        st.info(cand['summary'])

    skills_list = cand.get('skills', [])
    if skills_list:
        st.markdown("**🛠️ Extracted Resume Skills:**")
        skills_html = " ".join([f"<span class='skill-match'>{html.escape(s)}</span>" for s in skills_list])
        st.markdown(skills_html, unsafe_allow_html=True)

# -------------------------------------------------------------
# STEP 2: Configure Job Title, Location & Experience
# -------------------------------------------------------------
st.markdown("---")
st.markdown("### ⚙️ Step 2: Target Roles, Location & Experience")

col_r1, col_r2, col_r3 = st.columns([1.5, 1.4, 1.1])

# Combine AI inferred roles + custom added roles
inferred_roles = cand.get('target_roles', [
    "AI Engineer", "Junior AI Engineer", "Machine Learning Engineer", "Generative AI Engineer", "AI Intern"
])
all_role_options = list(dict.fromkeys(st.session_state['custom_roles'] + inferred_roles + [
    "AI Engineer", "Machine Learning Engineer", "Junior AI Engineer",
    "Generative AI Engineer", "LLM Engineer", "RAG Engineer",
    "Computer Vision Engineer", "AI Intern", "Machine Learning Intern",
    "Data Science Intern", "Junior Data Scientist", "Python Developer",
    "Software Engineer", "Full Stack AI Developer"
]))

# Combine AI inferred locations + custom added locations
inferred_locs = cand.get('suggested_locations', [
    "India", "Bengaluru", "Hyderabad", "Pune", "Remote", "Dubai", "Saudi Arabia"
])
all_loc_options = list(dict.fromkeys(st.session_state['custom_locs'] + inferred_locs + [
    "India", "Bengaluru", "Hyderabad", "Pune", "Mumbai", "Delhi-NCR", "Chennai",
    "Remote", "Dubai", "United Arab Emirates", "Saudi Arabia", "Worldwide"
]))

with col_r1:
    st.markdown("**🎯 1. Target Job Title(s):**")
    selected_roles = st.multiselect(
        "Select or customize job titles to search:",
        options=all_role_options,
        default=inferred_roles[:5] if len(inferred_roles) >= 5 else inferred_roles,
        help="The search collectors query live platforms for these job titles."
    )
    with st.expander("➕ Add Custom Job Title"):
        custom_role_input = st.text_input("Type new title (e.g., Python Backend Engineer):", key="new_role_in")
        if st.button("Add Title"):
            if custom_role_input.strip() and custom_role_input.strip() not in st.session_state['custom_roles']:
                st.session_state['custom_roles'].append(custom_role_input.strip())
                st.rerun()

with col_r2:
    st.markdown("**📍 2. Target Location(s):**")
    selected_locs = st.multiselect(
        "Select target locations or work mode:",
        options=all_loc_options,
        default=inferred_locs[:4] if len(inferred_locs) >= 4 else inferred_locs,
        help="Target locations and remote hubs."
    )
    with st.expander("➕ Add Custom Location"):
        custom_loc_input = st.text_input("Type new location (e.g., Singapore, Kolkata):", key="new_loc_in")
        if st.button("Add Location"):
            if custom_loc_input.strip() and custom_loc_input.strip() not in st.session_state['custom_locs']:
                st.session_state['custom_locs'].append(custom_loc_input.strip())
                st.rerun()

with col_r3:
    st.markdown("**⏳ 3. Your Experience:**")
    exp_options = {
        "0.0 Yrs (Fresher / Intern)": 0.0,
        "0.5 Yrs (~6 Months)": 0.5,
        "1.0 Year (Junior)": 1.0,
        "1.5 Years": 1.5,
        "2.0 Years": 2.0,
        "3.0+ Years": 3.0
    }
    curr_exp = float(cand.get('experience_years', 0.5))
    default_idx = 1
    if curr_exp <= 0.2:
        default_idx = 0
    elif curr_exp <= 0.7:
        default_idx = 1
    elif curr_exp <= 1.2:
        default_idx = 2
    elif curr_exp <= 1.7:
        default_idx = 3
    elif curr_exp <= 2.5:
        default_idx = 4
    else:
        default_idx = 5

    selected_exp_label = st.selectbox(
        "Select experience level:",
        options=list(exp_options.keys()),
        index=default_idx
    )
    selected_exp = exp_options[selected_exp_label]

    st.markdown("**⏱️ Freshness Window:**")
    st.success("🔥 Past 24 Hours Only")

# -------------------------------------------------------------
# STEP 3: Fetch Latest Jobs Under 24h Button
# -------------------------------------------------------------
st.markdown("---")
st.markdown("### 🚀 Step 3: Fetch & Match Fresh Under-24h Jobs")

col_btn, col_btn_desc = st.columns([1.6, 2.4])
with col_btn:
    fetch_clicked = st.button(
        "🚀 Fetch Latest Jobs Under 24h & Match My Resume",
        type="primary",
        use_container_width=True
    )

with col_btn_desc:
    st.write(
        f"Searches across **15+ Job Portals** (LinkedIn, Indeed AE/SA/IN, GulfTalent, Bayt, NaukriGulf, Greenhouse, Ashby, Himalayas, RemoteOK) "
        f"for **{len(selected_roles)} role(s)** in **{len(selected_locs)} location(s)** with **{selected_exp_label}**, "
        f"filtering strictly for **postings in the last 24 hours**."
    )

if fetch_clicked:
    if not selected_roles:
        st.error("⚠️ Please select at least one Target Job Title!")
    elif not selected_locs:
        st.error("⚠️ Please select at least one Location!")
    else:
        with st.spinner(f"🔍 Scanning 15+ portals for '{', '.join(selected_roles[:3])}' in '{', '.join(selected_locs[:3])}' (Past 24 Hours)..."):
            cand_to_use = dict(cand)
            cand_to_use['target_roles'] = selected_roles
            cand_to_use['suggested_locations'] = selected_locs
            cand_to_use['experience_years'] = selected_exp

            stats, rows = run_pipeline(
                send_digest=False,
                custom_candidate=cand_to_use,
                custom_queries=selected_roles,
                custom_locations=selected_locs,
                freshness_hours=24,
                min_match_score=40
            )
            st.session_state['active_candidate'] = cand_to_use
            st.session_state['freshness_filter'] = 'Past 24 Hours (Fresh)'
            st.success(f"🎉 Complete! Scanned {stats.get('raw_jobs', 0)} jobs. {stats.get('inserted', 0)} new jobs matched your resume & inserted into database!")
            st.rerun()

# -------------------------------------------------------------
# STEP 4: Best Matched Jobs Dashboard
# -------------------------------------------------------------
st.markdown("---")
st.markdown("### 🎯 Step 4: Best Matched 24-Hour Jobs")

raw_db_rows = [dict(r) for r in dashboard_rows(db)]
if not raw_db_rows:
    st.info('No jobs found in the database yet. Click the **"🚀 Fetch Latest Jobs Under 24h & Match My Resume"** button above to search live platforms.')
    st.stop()

# Helper class for scoring
class RowJob:
    def __init__(self, r):
        self.title = r.get('title', '')
        self.description = r.get('description', '')
        self.location = r.get('location', '')
        self.country = r.get('country', '')
        self.remote_type = r.get('remote_type', '')
        self.required_experience_min = r.get('required_experience_min')
        self.required_experience_max = r.get('required_experience_max')
        self.remote_eligibility = r.get('remote_eligibility', 'unknown')
        self.url = r.get('url', '')

now_utc = datetime.now(timezone.utc)

def get_job_age_hours(r):
    p = r.get('posted_at')
    dt = parse_dt(p)
    if not dt:
        dt = parse_dt(r.get('first_seen_at'))
    if dt:
        return max((now_utc - dt).total_seconds() / 3600.0, 0.0)
    return 999.0

def format_posted_time(r):
    p = r.get('posted_at')
    dt = parse_dt(p)
    if not dt:
        dt = parse_dt(r.get('first_seen_at'))
    if not dt:
        return str(p or '')
    diff_hours = (now_utc - dt).total_seconds() / 3600.0
    if diff_hours < 1:
        return f"{max(int(diff_hours * 60), 1)}m ago"
    elif diff_hours < 24:
        return f"{int(diff_hours)}h ago"
    elif diff_hours < 48:
        return "1 day ago"
    else:
        days = int(diff_hours / 24)
        return f"{days}d ago ({dt.strftime('%b %d')})"

def get_india_status(r):
    eligible, reason = is_eligible_for_india_applicant(RowJob(r))
    return "✅ Eligible" if eligible else f"❌ {reason}"

for r in raw_db_rows:
    m = score_job(RowJob(r), cand, cfg)
    r['match_score'] = m.get('score', 0)
    matched_s = m.get('matched_skills', [])
    r['matched_skills'] = ', '.join(matched_s) if isinstance(matched_s, list) else str(matched_s or '')
    missing_s = m.get('missing_skills', [])
    r['missing_skills'] = ', '.join(missing_s) if isinstance(missing_s, list) else str(missing_s or '')
    r['resume_suggestion'] = m.get('resume_suggestion', m.get('suggestion', ''))
    r['age_hours'] = get_job_age_hours(r)
    r['posted_ago'] = format_posted_time(r)
    r['apply_from_india'] = get_india_status(r)

df = pd.DataFrame(raw_db_rows)

# Overview Metrics (Computed on fresh 24h jobs)
df_24h = df[df.age_hours <= 24.0]
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric('🔥 Past 24h Jobs', len(df_24h))
c2.metric('🎯 80%+ Match', int((df_24h.match_score.fillna(0) >= 80).sum()))
c3.metric('🇮🇳 India Eligible', int((df_24h.apply_from_india.str.startswith('✅')).sum()))
c4.metric('🔄 Hybrid', int(df_24h.remote_type.fillna('').str.contains('hybrid', case=False).sum()))
c5.metric('🏠 Remote', int(df_24h.remote_type.fillna('').str.contains('remote', case=False).sum()))
c6.metric('📦 All Stored Jobs', len(df))

# Filter Controls Expander
with st.expander('🔍 Filter & Search Results', expanded=True):
    col_time, col_loc_f, col_type_f, col_src_f, col_score_f = st.columns([1.8, 1.5, 1.2, 1.3, 1.2])

    time_options = ['Past 24 Hours (Fresh)', 'Past 48 Hours', 'Past 7 Days', 'All Time']
    current_idx = time_options.index(st.session_state['freshness_filter']) if st.session_state['freshness_filter'] in time_options else 0
    selected_time = col_time.selectbox('⏱️ Freshness Window', time_options, index=current_idx)
    st.session_state['freshness_filter'] = selected_time

    countries = sorted([x for x in df.country.dropna().unique().tolist() if x])
    filter_country = col_loc_f.multiselect('Location / Country', countries, placeholder="All locations")

    filter_type = col_type_f.selectbox('Job Type', ['All', 'Remote', 'Hybrid', 'On-site'])

    PORTAL_CONFIG = {
        'All': lambda s: True,
        'LinkedIn': lambda s: 'linkedin' in s.lower(),
        'Indeed (AE / SA / IN / Global)': lambda s: 'indeed' in s.lower(),
        'GulfTalent (Middle East)': lambda s: 'gulftalent' in s.lower(),
        'Bayt (Middle East)': lambda s: 'bayt' in s.lower(),
        'NaukriGulf (UAE / Saudi)': lambda s: 'naukrigulf' in s.lower(),
        'Greenhouse': lambda s: 'greenhouse' in s.lower(),
        'Ashby': lambda s: 'ashby' in s.lower(),
        'Lever': lambda s: 'lever' in s.lower(),
        'Himalayas': lambda s: 'himalayas' in s.lower(),
        'Jobicy': lambda s: 'jobicy' in s.lower(),
        'WeWorkRemotely': lambda s: 'wework' in s.lower(),
        'Arbeitnow': lambda s: 'arbeitnow' in s.lower(),
        'Remotive': lambda s: 'remotive' in s.lower(),
        'RemoteOK': lambda s: 'remoteok' in s.lower(),
    }
    filter_portal = col_src_f.selectbox('Job Portal', list(PORTAL_CONFIG.keys()))
    min_score = col_score_f.slider('Min Match %', 0, 100, 40)

    col_q, col_status, col_india_c = st.columns([2.5, 1.3, 1.2])
    search_query = col_q.text_input('🔎 Search keywords (e.g. Intern, Python, LangChain, TCS, Bengaluru):', '')
    status_filter = col_status.selectbox('Status', ['All', 'Not Applied', 'Applied', 'Interview', 'Rejected', 'Offer'])
    only_india_eligible = col_india_c.checkbox('🇮🇳 Only India Eligible', value=True)

# Apply Time Filter
f = df[df.match_score.fillna(0) >= min_score]

if selected_time == 'Past 24 Hours (Fresh)':
    f = f[f.age_hours <= 24.0]
elif selected_time == 'Past 48 Hours':
    f = f[f.age_hours <= 48.0]
elif selected_time == 'Past 7 Days':
    f = f[f.age_hours <= 168.0]

# Apply India Eligibility Filter
if only_india_eligible:
    f = f[f.apply_from_india.str.startswith('✅')]

# Apply Other Filters
if filter_country:
    f = f[f.country.isin(filter_country)]
if filter_type != 'All':
    if filter_type == 'Remote':
        f = f[f.remote_type.fillna('').str.contains('remote', case=False)]
    elif filter_type == 'Hybrid':
        f = f[f.remote_type.fillna('').str.contains('hybrid', case=False)]
    elif filter_type == 'On-site':
        f = f[f.remote_type.fillna('').str.lower().isin(['on-site', 'onsite'])]
if filter_portal != 'All':
    matcher = PORTAL_CONFIG.get(filter_portal, lambda s: True)
    f = f[f.source.fillna('').apply(matcher)]
if status_filter != 'All':
    f = f[f.application_status.fillna('Not Applied') == status_filter]
if search_query.strip():
    q = search_query.strip().lower()
    mask = (
        f.title.fillna('').str.lower().str.contains(q) |
        f.company.fillna('').str.lower().str.contains(q) |
        f.location.fillna('').str.lower().str.contains(q) |
        f.matched_skills.fillna('').str.lower().str.contains(q)
    )
    f = f[mask]

# Sort by Match Score Descending
f = f.sort_values(by='match_score', ascending=False)

col_view_info, col_view_toggle = st.columns([2.5, 1.5])
with col_view_info:
    st.caption(f"Showing **{len(f)}** best matched jobs for **{cand.get('name', 'Candidate')}** ({selected_time}).")

with col_view_toggle:
    view_mode = st.radio(
        "Display View:",
        options=["🎴 Modern Cards", "📊 Data Table"],
        horizontal=True,
        label_visibility="collapsed"
    )

# -------------------------------------------------------------
# RENDER JOBS: Modern Cards vs Data Table
# -------------------------------------------------------------
if view_mode == "🎴 Modern Cards":
    if len(f) == 0:
        st.info("No jobs match your filter criteria. Try adjusting the Min Match % or Freshness window.")
    else:
        # Display cards
        cards_per_page = 20
        total_matched = len(f)
        
        for idx, row in f.iloc[:cards_per_page].iterrows():
            score = float(row.get('match_score') or 0)
            if score >= 80:
                badge_html = f"<span class='badge-high'>🟢 {score:.1f}% High Match</span>"
            elif score >= 60:
                badge_html = f"<span class='badge-med'>🎯 {score:.1f}% Good Match</span>"
            else:
                badge_html = f"<span class='badge-low'>⚡ {score:.1f}% Match</span>"

            # Parse skills tags
            matched_raw = str(row.get('matched_skills') or '').strip()
            missing_raw = str(row.get('missing_skills') or '').strip()

            matched_tags = ""
            if matched_raw:
                matched_tags = "".join([f"<span class='skill-match'>✓ {html.escape(s.strip())}</span>" for s in matched_raw.split(',') if s.strip()])
            else:
                matched_tags = "<span class='tag-pill'>No specific skills required</span>"

            missing_tags = ""
            if missing_raw:
                missing_tags = "".join([f"<span class='skill-miss'>✗ {html.escape(s.strip())}</span>" for s in missing_raw.split(',')[:5] if s.strip()])

            # Suggestion
            suggestion_txt = html.escape(str(row.get('resume_suggestion') or ''))
            tip_html = f"<div class='tip-box'>💡 <b>Resume Tip:</b> {suggestion_txt}</div>" if suggestion_txt else ""

            # Card HTML
            title = html.escape(str(row.get('title') or 'Untitled Role'))
            company = html.escape(str(row.get('company') or 'Company'))
            location = html.escape(str(row.get('location') or 'Location'))
            posted_ago = html.escape(str(row.get('posted_ago') or ''))
            source = html.escape(str(row.get('source') or '').upper())
            apply_india = html.escape(str(row.get('apply_from_india') or ''))
            remote_type = html.escape(str(row.get('remote_type') or 'On-site'))
            url = str(row.get('url') or '#')
            status = html.escape(str(row.get('application_status') or 'Not Applied'))

            card_html = f"""
            <div class="job-card">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                <div>
                  <div class="job-title">{title}</div>
                  <div class="job-company">🏢 <b>{company}</b> &nbsp;•&nbsp; 📍 {location}</div>
                </div>
                <div>
                  {badge_html}
                </div>
              </div>

              <div style="margin: 0.5rem 0;">
                <span class="tag-pill">⏱️ {posted_ago}</span>
                <span class="tag-pill">🌐 {source}</span>
                <span class="tag-pill">💼 {remote_type}</span>
                <span class="tag-pill">{apply_india}</span>
                <span class="tag-pill" style="color:#818cf8; font-weight:600;">Status: {status}</span>
              </div>

              <div style="margin-top: 0.6rem;">
                <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 3px;"><b>Matched Skills:</b></div>
                <div>{matched_tags}</div>
              </div>

              {f'''<div style="margin-top: 0.5rem;">
                <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 3px;"><b>Missing Skills:</b></div>
                <div>{missing_tags}</div>
              </div>''' if missing_tags else ''}

              {tip_html}

              <div style="margin-top: 0.9rem; display: flex; justify-content: flex-end;">
                <a href="{url}" target="_blank" class="apply-btn">Direct Apply ↗</a>
              </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

        if total_matched > cards_per_page:
            st.caption(f"Showing top **{cards_per_page}** of **{total_matched}** jobs. Use table view to browse all.")

else:
    # Spreadsheet Data Table View
    cols = [
        'id', 'match_score', 'title', 'company', 'location', 'apply_from_india', 'remote_type',
        'posted_ago', 'source', 'matched_skills', 'missing_skills', 'resume_suggestion',
        'application_status', 'url'
    ]

    st.dataframe(
        f[cols],
        hide_index=True,
        column_config={
            'url': st.column_config.LinkColumn('Direct Apply', display_text='Apply ↗'),
            'match_score': st.column_config.ProgressColumn('Match Score %', min_value=0, max_value=100, format="%.1f%%"),
            'apply_from_india': st.column_config.TextColumn('🇮🇳 Apply from India', width='medium'),
            'posted_ago': st.column_config.TextColumn('Posted', width='small'),
            'id': st.column_config.NumberColumn('#ID', width='small'),
        }
    )

# -------------------------------------------------------------
# STEP 5: Quick Application Status Tracker
# -------------------------------------------------------------
st.markdown("---")
st.subheader('📝 Track Application Status')
job_options = {f"#{r['id']} | {r['title']} @ {r['company']} ({r['location']}) [{r['posted_ago']}] - {r['match_score']:.0f}% Match": int(r['id']) for _, r in f.iterrows()}
if job_options:
    label = st.selectbox('Choose job to update status:', list(job_options.keys()))
    x, y, z = st.columns([2, 1, 1])
    new_status = x.selectbox('Application Status:', ['Not Applied', 'Applied', 'Interview', 'Rejected', 'Offer'])
    saved = y.checkbox('⭐ Star / Bookmark Job')
    if z.button('Save Status', type='primary'):
        update_job_state(db, job_options[label], new_status, saved)
        st.success('Status updated successfully! Refreshing...')
        st.rerun()
