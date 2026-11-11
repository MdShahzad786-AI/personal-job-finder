# 🎯 AI Job Hunter Pro & Intelligent Resume Matcher

An autonomous, production-grade job discovery and resume-matching system designed for entry-level AI/ML candidates. It aggregates postings across 5+ job boards and company ATS portals, applies strict 24-hour freshness and experience filters, extracts credentials from resumes via an AI Agent, and calculates deterministic 0–100% match scores in real time.

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B?logo=streamlit)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Key Features

1. **📄 Multi-Format Resume Ingestion**:
   - Upload any resume in `.pdf`, `.docx`, or `.txt`.
   - Built-in fallback profile for Mohammed Shahzad (BCA 2026, AI/ML focus).

2. **🤖 AI Resume Agent (`jobhunter/resume/ai_agent.py`)**:
   - Parses candidate name, contact, education, passing year, and calculates exact experience.
   - Detects 150+ categorized modern technical skills (PyTorch, LangChain, YOLO, RAG, Docker, OpenCV, LightGBM, SQL, etc.).
   - Automatically infers best target job titles and suggests high-opportunity locations.
   - Generates an executive profile assessment summary.

3. **🌐 15+ Multi-Source Job Ingestion (100% Free / Zero API Keys Required)**:
   - **Job Aggregators:** LinkedIn (Guest API), Indeed (India, UAE, Saudi Arabia via browser impersonation).
   - **Regional Middle East Portals:** GulfTalent, Bayt, NaukriGulf.
   - **Direct Tech Company ATS:** Greenhouse, Ashby, Lever (OpenAI, Scale AI, Databricks, Anthropic, Careem, Cursor, ElevenLabs, etc.).
   - **Remote Job Boards:** Himalayas, Jobicy, WeWorkRemotely, Remotive, RemoteOK, Arbeitnow.
   - **Optional Search APIs:** SerpAPI Google Jobs, Adzuna (disabled by default).

4. **🛡️ Strict Production-Grade Filters**:
   - **24-Hour Freshness:** Filters strictly for postings published within the last 24 hours.
   - **Senior Exclusion:** Automatically rejects `Senior`, `Lead`, `Manager`, `Director`, `Staff`, `Architect`.
   - **Experience Enforcement:** Keeps 0–2 years / fresher / junior / internship roles.
   - **India & Remote Eligibility:** Flags country-restricted roles, local residency requirements, and visa restrictions.

5. **🎯 Deterministic Resume Match Engine (0–100%)**:
   - Weighted multi-factor scoring (Skills 40%, Title 20%, Experience 15%, Location 10%, Projects 10%, Education 5%).
   - Lists exact **Matched Skills** and **Missing Skills**.
   - Provides truthful resume tailoring tips without skill hallucination.

6. **💻 Interactive Streamlit Dashboard**:
   - Upload resume & inspect AI Agent extracted credentials.
   - Customize target job titles, locations, and experience level.
   - One-click live scan & matching across 15+ portals.
   - Direct `Apply ↗` links and real-time Application Status Tracker (*Applied*, *Interview*, *Offer*, *Saved*).

7. **⏰ Daily Automation**:
   - GitHub Actions workflow (`.github/workflows/daily-jobs.yml`) runs daily at 09:15 IST and dispatches an HTML email digest via SMTP.

---

## 🛠️ Project Structure

```
AI job hunter/
├── dashboard.py               # Streamlit interactive UI application
├── main.py                    # CLI pipeline runner (scraping, filtering, scoring, email)
├── config.yaml                # Master configuration (filters, roles, hubs, ATS companies)
├── candidate_profile.yaml      # Candidate profile & skills definition
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
│
├── jobhunter/                 # Core engine package
│   ├── collectors/            # 16 multi-source job board scrapers and ATS collectors
│   ├── resume/
│   │   ├── ai_agent.py        # AI Resume Agent (entity extraction & role inference)
│   │   └── parser.py          # Multi-format PDF / DOCX / TXT parser
│   ├── db.py                  # SQLite database interface & status management
│   ├── filters.py             # 24h freshness, experience, senior exclusion, location
│   ├── match.py               # Deterministic 0-100% resume match scoring algorithm
│   ├── models.py              # Normalized Job dataclass
│   ├── normalize.py           # Deduplication fingerprints & canonical URLs
│   ├── pipeline.py            # End-to-end ingestion and scoring pipeline coordinator
│   └── emailer.py             # SMTP HTML email digest generator
│
├── scripts/                   # Validation & utility scripts
├── tests/                     # 27 automated unit tests (All passing)
└── data/                      # SQLite database storage (jobs.db)
```

---

## ⚡ Quick Start

### 1. Clone & Setup Virtual Environment

```bash
git clone https://github.com/<your-username>/ai-job-hunter.git
cd ai-job-hunter

python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
```

### 2. Initialize Database & Run Dashboard

```bash
python scripts/init_db.py
streamlit run dashboard.py
```

Open **`http://localhost:8501`** in your browser!

### 3. Run Automated Unit Tests

```bash
pytest -v
```

---

## 📧 Email Digest Setup (Optional)

Configure your `.env` file:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=your_email@gmail.com
```

Test sending an email digest:
```bash
python scripts/send_test_email.py
python main.py --send-email
```

---

## 📜 License

MIT License. Free to use, adapt, and build upon.
