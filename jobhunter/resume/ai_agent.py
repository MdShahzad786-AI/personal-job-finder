import re
import os
import logging
from typing import Dict, Any, List, Optional

log = logging.getLogger(__name__)

# Comprehensive Skill Taxonomy
SKILL_TAXONOMY = {
    # AI / ML Core
    "python": ["python", "py"],
    "machine learning": ["machine learning", " ml "],
    "deep learning": ["deep learning", " dl "],
    "natural language processing": ["natural language processing", "nlp"],
    "computer vision": ["computer vision", " cv "],
    "generative ai": ["generative ai", "genai", "gen ai"],
    "large language models": ["large language models", "llm", "llms"],
    "retrieval augmented generation": ["retrieval augmented generation", "retrieval-augmented generation", " rag "],
    "transformers": ["transformer", "transformers"],
    "embeddings": ["embedding", "embeddings", "vector embedding"],
    
    # Frameworks & Libraries
    "pytorch": ["pytorch", "torch"],
    "tensorflow": ["tensorflow", "tf"],
    "keras": ["keras"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "opencv": ["opencv", "cv2"],
    "yolo": ["yolo", "yolov8", "yolov5", "yolov11"],
    "easyocr": ["easyocr"],
    "lightgbm": ["lightgbm", "lgb"],
    "xgboost": ["xgboost", "xgb"],
    "langchain": ["langchain"],
    "langgraph": ["langgraph"],
    "llamaindex": ["llamaindex", "llama-index"],
    "hugging face": ["hugging face", "huggingface", "hf"],
    
    # Vector DBs & Search
    "chromadb": ["chromadb", "chroma db", "chroma"],
    "faiss": ["faiss"],
    "pinecone": ["pinecone"],
    "qdrant": ["qdrant"],
    
    # Data & Analytics
    "sql": ["sql", "mysql", "postgresql", "postgres", "sqlite"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "statistics": ["statistics", "statistical analysis", "probability"],
    "spark": ["spark", "pyspark"],
    
    # Backend & Deployment
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "django": ["django"],
    "streamlit": ["streamlit"],
    "rest api": ["rest api", "restful api", "apis"],
    "docker": ["docker", "containerization"],
    "kubernetes": ["kubernetes", "k8s"],
    
    # Cloud & Tools
    "aws": ["aws", "amazon web services"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "azure": ["azure", "microsoft azure"],
    "git": [" git ", "git/", "version control"],
    "github": ["github"],
    "ci/cd": ["ci/cd", "continuous integration"]
}


def clean_text_for_search(text: str) -> str:
    cleaned = re.sub(r'[\r\n\t]+', ' ', text)
    cleaned = re.sub(r'[^a-zA-Z0-9\s/+#.-]', ' ', cleaned)
    return f" {cleaned.lower()} "


def extract_contact_info(text: str) -> Dict[str, Any]:
    # Email
    email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    email = email_match.group(0) if email_match else ""

    # Phone (+91-XXXXX XXXXX or standard international)
    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}', text)
    phone = phone_match.group(0).strip() if phone_match else ""

    # Social links
    github = ""
    linkedin = ""
    for line in text.splitlines():
        if "github.com" in line.lower() and not github:
            m = re.search(r'github\.com/[a-zA-Z0-9_.-]+', line, re.I)
            if m: github = f"https://{m.group(0)}"
        if "linkedin.com" in line.lower() and not linkedin:
            m = re.search(r'linkedin\.com/in/[a-zA-Z0-9_.-]+', line, re.I)
            if m: linkedin = f"https://{m.group(0)}"

    return {
        "email": email,
        "phone": phone,
        "github": github,
        "linkedin": linkedin
    }


def extract_candidate_name(text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    ignore_words = {
        "resume", "curriculum", "vitae", "cv", "page", "phone", "email",
        "objective", "profile", "contact", "summary", "experience", "education",
        "skills", "projects", "certifications"
    }
    for line in lines[:10]:
        words = line.split()
        if 1 <= len(words) <= 4:
            lower = line.lower()
            if not any(w in lower for w in ignore_words) and "@" not in lower and "http" not in lower and not any(ch.isdigit() for ch in line):
                # Clean punctuation
                cleaned = re.sub(r'[^a-zA-Z\s]', '', line).strip()
                if len(cleaned) >= 3:
                    return cleaned.title()
    return "Candidate"


def extract_education(text: str) -> Dict[str, Any]:
    lower = text.lower()
    degrees = [
        ("Bachelor of Computer Applications (BCA)", ["bca", "bachelor of computer applications", "bachelor in computer application"]),
        ("Bachelor of Technology (B.Tech)", ["b.tech", "btech", "bachelor of technology"]),
        ("Bachelor of Engineering (B.E.)", ["b.e.", "bachelor of engineering"]),
        ("Master of Computer Applications (MCA)", ["mca", "master of computer applications"]),
        ("Master of Technology (M.Tech)", ["m.tech", "mtech", "master of technology"]),
        ("Master of Science (M.S. / M.Sc)", ["m.sc", "msc", "master of science"]),
        ("Bachelor of Science (B.Sc)", ["b.sc", "bsc", "bachelor of science"]),
        ("Diploma in Engineering / CS", ["diploma in computer", "polytechnic"]),
    ]

    degree_name = "Bachelor's Degree"
    for name, aliases in degrees:
        if any(a in lower for a in aliases):
            degree_name = name
            break

    # Look for graduation year
    year_match = re.search(r'\b(20[12]\d)\b', text)
    year = int(year_match.group(1)) if year_match else 2026

    return {
        "degree": degree_name,
        "year": year
    }


def extract_experience_years(text: str) -> float:
    lower = text.lower()
    # Check for fresher terms
    if any(k in lower for k in ["fresher", "entry-level", "entry level", "new grad", "graduate 202", "bca 2026", "btech 2026", "student"]):
        # Check for months of experience
        m_match = re.search(r'(\d+)\s*(?:\+|-)?\s*months?\s*(?:of)?\s*(?:internship|experience|work)', lower)
        if m_match:
            months = float(m_match.group(1))
            return round(months / 12.0, 2)
        return 0.5

    # Check for direct year statements e.g. "1.5 years experience", "2 years of experience"
    exp_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:\+|-)?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:relevant)?\s*experience', lower)
    if exp_match:
        return float(exp_match.group(1))

    return 0.5


def extract_skills(text: str) -> List[str]:
    searchable = clean_text_for_search(text)
    detected = []
    for skill_name, aliases in SKILL_TAXONOMY.items():
        if any(alias in searchable for alias in aliases):
            detected.append(skill_name)
    return detected


def extract_projects(text: str) -> List[str]:
    lines = text.splitlines()
    projects = []
    in_project_section = False

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if any(h in lower for h in ["projects", "academic projects", "key projects", "personal projects"]):
            in_project_section = True
            continue
        if in_project_section and any(h in lower for h in ["education", "experience", "work history", "certifications", "skills", "achievements"]):
            in_project_section = False
            break

        if in_project_section and stripped:
            if stripped.startswith(("-", "•", "*", "1.", "2.", "3.", "4.", "5.")):
                p_text = re.sub(r'^[-•*\d.]+\s*', '', stripped)
                if len(p_text) > 15:
                    projects.append(p_text)
            elif len(stripped) > 20 and not stripped.endswith(":"):
                projects.append(stripped)

    # Fallback to key phrases if none parsed
    if not projects:
        for line in lines:
            if any(term in line.lower() for term in ["rag", "yolo", "chatbot", "prediction", "detection", "recommendation", "pipeline"]):
                if len(line.strip()) > 20:
                    projects.append(line.strip())
                    if len(projects) >= 4:
                        break

    return projects[:5]


def infer_target_roles(skills: List[str], experience_years: float) -> List[str]:
    roles = []
    s_set = set(s.lower() for s in skills)

    is_junior = experience_years <= 2.0

    # GenAI / LLM roles
    if any(k in s_set for k in ["generative ai", "large language models", "retrieval augmented generation", "langchain", "llamaindex", "transformers"]):
        roles.append("Generative AI Engineer")
        roles.append("LLM Engineer")
        roles.append("RAG Engineer")
        roles.append("Applied AI Engineer")
        if is_junior:
            roles.append("Generative AI Intern")
            roles.append("Generative AI Developer")

    # Computer Vision roles
    if any(k in s_set for k in ["computer vision", "opencv", "yolo", "easyocr"]):
        roles.append("Computer Vision Engineer")
        if is_junior:
            roles.append("Junior Computer Vision Engineer")
            roles.append("Computer Vision Intern")

    # ML / AI General roles
    if any(k in s_set for k in ["machine learning", "deep learning", "pytorch", "tensorflow", "scikit-learn"]):
        roles.append("AI Engineer")
        roles.append("Machine Learning Engineer")
        if is_junior:
            roles.append("Junior AI Engineer")
            roles.append("Junior Machine Learning Engineer")
            roles.append("AI/ML Engineer")
            roles.append("Machine Learning Intern")
            roles.append("AI Intern")

    # Data Science roles
    if any(k in s_set for k in ["pandas", "numpy", "sql", "statistics", "lightgbm", "xgboost"]):
        if is_junior:
            roles.append("Junior Data Scientist")
            roles.append("Data Science Intern")

    # Fallbacks if none matched
    if not roles:
        roles = [
            "AI Engineer",
            "Junior AI Engineer",
            "Machine Learning Engineer",
            "AI Intern",
            "Generative AI Engineer"
        ]

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for r in roles:
        if r.lower() not in seen:
            seen.add(r.lower())
            deduped.append(r)
    return deduped


def suggest_locations(text: str) -> List[str]:
    lower = text.lower()
    default_hubs = ["India", "Bengaluru", "Hyderabad", "Pune", "Remote", "Dubai", "Saudi Arabia"]
    detected = []

    location_keywords = {
        "India": ["india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "delhi", "noida", "gurgaon", "gurugram", "chennai", "kolkata", "jharkhand", "bihar"],
        "Bengaluru": ["bengaluru", "bangalore"],
        "Hyderabad": ["hyderabad"],
        "Pune": ["pune"],
        "Delhi-NCR": ["delhi", "noida", "gurgaon", "gurugram"],
        "Remote": ["remote", "work from home", "wfh"],
        "Dubai": ["dubai", "uae", "abu dhabi", "united arab emirates"],
        "Saudi Arabia": ["saudi", "riyadh", "jeddah"]
    }

    for hub, keywords in location_keywords.items():
        if any(k in lower for k in keywords):
            detected.append(hub)

    for h in default_hubs:
        if h not in detected:
            detected.append(h)

    return detected[:6]


def generate_ai_summary(name: str, exp_years: float, skills: List[str], target_roles: List[str], education: Dict[str, Any]) -> str:
    top_skills = ", ".join([s.title() for s in skills[:6]]) if skills else "Modern AI/ML Technologies"
    top_roles = ", ".join(target_roles[:3]) if target_roles else "AI/ML Engineer"
    exp_str = f"~{int(exp_years * 12)} months of practical experience" if exp_years < 1 else f"{exp_years} years of experience"
    if exp_years == 0:
        exp_str = "Fresher / Entry-Level readiness"

    deg = education.get("degree", "Bachelor's Degree")
    yr = education.get("year", 2026)

    return (
        f"**{name}** is an emerging technical talent ({deg}, Class of {yr}) with {exp_str}. "
        f"Demonstrates strong hands-on capabilities across **{top_skills}**. "
        f"Prime fit for **{top_roles}** roles with high adaptability for fast-moving AI & GenAI teams."
    )


class AIResumeAgent:
    """
    Intelligent AI Agent for analyzing candidate resumes, extracting core credentials,
    inferring target roles, and preparing candidate profiles for real-time 24h job matching.
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")

    def analyze(self, raw_text: str, filename: str = "") -> Dict[str, Any]:
        if not raw_text or not raw_text.strip():
            return {
                "name": "Candidate",
                "email": "",
                "phone": "",
                "location": "India",
                "experience_years": 0.5,
                "education": {"degree": "BCA", "year": 2026},
                "skills": ["python", "machine learning", "deep learning", "nlp", "generative ai"],
                "projects": [],
                "target_roles": ["Junior AI Engineer", "AI/ML Engineer", "AI Intern"],
                "suggested_locations": ["India", "Bengaluru", "Remote", "Dubai"],
                "summary": "No resume text provided."
            }

        contact = extract_contact_info(raw_text)
        name = extract_candidate_name(raw_text)
        education = extract_education(raw_text)
        experience_years = extract_experience_years(raw_text)
        skills = extract_skills(raw_text)
        projects = extract_projects(raw_text)
        target_roles = infer_target_roles(skills, experience_years)
        suggested_locations = suggest_locations(raw_text)
        summary = generate_ai_summary(name, experience_years, skills, target_roles, education)

        # Build candidate profile dictionary compatible with job matching engine
        profile = {
            "name": name,
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
            "github": contact.get("github", ""),
            "linkedin": contact.get("linkedin", ""),
            "location": suggested_locations[0] if suggested_locations else "India",
            "experience_years": experience_years,
            "education": education,
            "skills": skills,
            "projects": projects,
            "target_roles": target_roles,
            "suggested_locations": suggested_locations,
            "summary": summary,
            "raw_text_length": len(raw_text)
        }

        # Optional Gemini API enhancement if key is configured
        if self.gemini_api_key:
            try:
                profile = self._enrich_with_gemini(raw_text, profile)
            except Exception as e:
                log.warning("Gemini enhancement skipped: %s", e)

        return profile

    def _enrich_with_gemini(self, text: str, current_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Optional LLM pass if user provides Gemini API key in environment."""
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        prompt = (
            f"Analyze this resume and return a concise JSON with fields: 'summary' (2 sentences), "
            f"'top_skills' (list of strings), 'recommended_roles' (list of 5 roles). "
            f"Resume text:\n{text[:4000]}"
        )
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10)
        if res.status_code == 200:
            import json
            data = res.json()
            out_text = data['candidates'][0]['content']['parts'][0]['text']
            m = re.search(r'\{.*\}', out_text, re.DOTALL)
            if m:
                parsed = json.loads(m.group(0))
                if 'summary' in parsed and parsed['summary']:
                    current_profile['summary'] = parsed['summary']
                if 'recommended_roles' in parsed and parsed['recommended_roles']:
                    current_profile['target_roles'] = parsed['recommended_roles']
        return current_profile


def analyze_resume(raw_text: str, filename: str = "") -> Dict[str, Any]:
    agent = AIResumeAgent()
    return agent.analyze(raw_text, filename)
