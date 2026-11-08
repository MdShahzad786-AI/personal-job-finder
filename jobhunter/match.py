from .normalize import clean_text, normalize_title

SKILL_ALIASES = {
    "python": ["python"], "sql": ["sql"], "machine learning": ["machine learning", " ml "],
    "deep learning": ["deep learning"], "nlp": ["nlp", "natural language processing"],
    "computer vision": ["computer vision"], "generative ai": ["generative ai", "genai", "gen ai"],
    "pandas": ["pandas"], "numpy": ["numpy"], "scikit-learn": ["scikit-learn", "sklearn"],
    "tensorflow": ["tensorflow"], "pytorch": ["pytorch"], "opencv": ["opencv"],
    "langchain": ["langchain"], "langgraph": ["langgraph"], "hugging face": ["hugging face", "huggingface"],
    "docker": ["docker", "containerization"], "flask": ["flask"], "fastapi": ["fastapi"],
    "rest api": ["rest api", "restful api"], "streamlit": ["streamlit"], "git": [" git ", "github"],
    "aws": ["aws", "amazon web services"], "gcp": ["gcp", "google cloud"], "azure": ["azure"],
    "chromadb": ["chromadb", "chroma db"], "rag": ["retrieval augmented generation", "retrieval-augmented generation", " rag "],
    "embeddings": ["embeddings", "embedding model", "vector embedding"], "yolo": ["yolo"],
    "easyocr": ["easyocr"], "lightgbm": ["lightgbm"], "kubernetes": ["kubernetes", "k8s"],
    "mlflow": ["mlflow"], "airflow": ["airflow"], "redis": ["redis"], "postgresql": ["postgresql", "postgres"],
    "transformers": ["transformers"], "faiss": ["faiss"], "pinecone": ["pinecone"], "qdrant": ["qdrant"],
    "llamaindex": ["llamaindex", "llama index"], "spark": ["spark", "pyspark"], "ci/cd": ["ci/cd", "continuous integration"]
}


def contains_alias(skill, padded_text):
    return any(alias in padded_text for alias in SKILL_ALIASES.get(skill, [skill]))


def score_job(job, candidate, cfg):
    text = " " + clean_text(f"{job.title} {job.description}") + " "
    candidate_skills = {clean_text(x) for x in candidate.get("skills", [])}
    required = sorted([skill for skill in SKILL_ALIASES if contains_alias(skill, text)])
    matched = sorted([s for s in required if s in candidate_skills])
    missing = sorted([s for s in required if s not in candidate_skills])
    # A JD with no detected skills should not earn a perfect skills score.
    skill_score = len(matched) / len(required) if required else 0.5

    title = normalize_title(job.title)
    targets = [normalize_title(x) for x in candidate.get("target_roles", [])]
    title_score = 1.0 if any(r in title or title in r for r in targets) else (0.7 if any(k in title for k in ["ai", "machine learning", "ml", "llm", "rag", "computer vision"]) else 0.2)

    mn = job.required_experience_min
    cand_exp = float(candidate.get("experience_years", 0))
    if mn is None:
        exp_score = 0.75
    elif cand_exp >= mn:
        exp_score = 1.0
    elif mn <= 1:
        exp_score = 0.9
    elif mn <= 2:
        exp_score = 0.65
    else:
        exp_score = 0.0

    from .filters import is_eligible_for_india_applicant
    eligible_india, india_reason = is_eligible_for_india_applicant(job)
    eligibility = getattr(job, "remote_eligibility", "unknown")
    blob = clean_text(f"{job.location} {job.country}")
    if not eligible_india:
        location_score = 0.0
    elif "india" in blob or "worldwide" in india_reason.lower():
        location_score = 1.0
    elif "middle east" in india_reason.lower() or "visa sponsorship" in india_reason.lower():
        location_score = 0.95
    elif eligibility == "country_restricted":
        location_score = 0.0
    elif eligibility == "unknown_remote":
        location_score = 0.65
    else:
        location_score = 0.8

    education_score = 1.0 if any(x in text for x in ["bachelor", "bca", "degree", "computer science"]) else 0.8
    project_keywords = ["rag", "llm", "langchain", "computer vision", "yolo", "opencv", "lightgbm", "streamlit", "docker"]
    project_score = min(sum(1 for x in project_keywords if x in text) / 3, 1.0)

    w = cfg["matching"]["weights"]
    score = round(100 * (
        skill_score*w["skills"] + title_score*w["title"] + exp_score*w["experience"] +
        location_score*w["location"] + education_score*w["education"] + project_score*w["projects"]
    ), 1)

    why = []
    if matched:
        why.append("Matched skills: " + ", ".join(matched[:10]))
    if title_score >= 0.7:
        why.append("Target role alignment")
    if exp_score >= 0.65:
        why.append("Experience range is potentially suitable")
    if location_score >= 0.75:
        why.append(f"🇮🇳 India Applicant: {india_reason}")

    highlight = [s for s in matched if s in {"rag", "langchain", "chromadb", "docker", "computer vision", "yolo", "opencv", "lightgbm", "streamlit"}]
    if highlight:
        suggestion = "Highlight existing project evidence for: " + ", ".join(highlight) + "."
    else:
        suggestion = "Tailor your existing project bullets to the JD and quantify outcomes where truthful."
    if missing:
        suggestion += " Learning gaps to consider (do not claim unless true): " + ", ".join(missing[:8]) + "."

    return {
        "score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "why_match": ". ".join(why) or "Partial profile alignment",
        "resume_suggestion": suggestion,
        "suggestion": suggestion,
    }
