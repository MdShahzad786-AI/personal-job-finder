from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jobhunter.config import load_config
from jobhunter.resume.parser import extract_pdf_text, resume_summary

if __name__ == "__main__":
    cfg = load_config()
    p = ROOT / cfg["candidate"]["resume_path"]
    text = extract_pdf_text(p)
    summary = resume_summary(text)
    print(f"Resume: {p}")
    print(f"Characters extracted: {summary['characters']}")
    print("Skills detected:", ", ".join(summary["skills_detected"]))
