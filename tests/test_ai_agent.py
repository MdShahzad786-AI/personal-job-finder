import io
import pytest
from jobhunter.resume.parser import extract_resume_text
from jobhunter.resume.ai_agent import AIResumeAgent, extract_skills, infer_target_roles, extract_candidate_name


def test_ai_agent_analysis_basic():
    sample_text = """
    Aman Sharma
    amansharma@example.com | +91-9876543210 | Bengaluru, India
    Summary: Enthusiastic AI/ML Engineer with hands-on experience in PyTorch, Computer Vision and RAG.
    Education: Bachelor of Technology (B.Tech) 2026
    Skills: Python, PyTorch, LangChain, YOLO, OpenCV, Docker, FastApi, SQL
    Projects:
    - Real-time vehicle detection using YOLO and OpenCV
    - Conversational RAG assistant with LangChain and Streamlit
    """
    agent = AIResumeAgent()
    profile = agent.analyze(sample_text)

    assert profile["name"] == "Aman Sharma"
    assert profile["email"] == "amansharma@example.com"
    assert "python" in profile["skills"]
    assert "pytorch" in profile["skills"]
    assert "yolo" in profile["skills"]
    assert "langchain" in profile["skills"]
    assert profile["education"]["degree"] == "Bachelor of Technology (B.Tech)"
    assert profile["education"]["year"] == 2026
    assert any("Computer Vision" in r for r in profile["target_roles"])
    assert any("Generative AI" in r or "LLM" in r or "RAG" in r for r in profile["target_roles"])


def test_ai_agent_skills_and_role_inference():
    skills = extract_skills("Proficient in Python, Machine Learning, Scikit-learn, Pandas, LightGBM")
    assert "python" in skills
    assert "machine learning" in skills
    assert "scikit-learn" in skills
    assert "pandas" in skills

    roles = infer_target_roles(skills, experience_years=0.5)
    assert any("Machine Learning" in r for r in roles)
    assert any("Intern" in r or "Junior" in r for r in roles)


def test_extract_resume_text_string_and_bytes():
    raw_str = "Jane Doe\nAI Developer\nSkills: Python, PyTorch"
    extracted = extract_resume_text(raw_str.encode("utf-8"), filename="test.txt")
    assert "Jane Doe" in extracted
    assert "PyTorch" in extracted
