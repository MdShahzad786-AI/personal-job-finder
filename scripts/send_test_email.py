from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jobhunter.emailer import send_email

if __name__ == '__main__':
    sample=[{
        'title':'Junior AI Engineer','company':'Test Company','country':'Remote','location':'Worldwide',
        'remote_type':'Remote','remote_eligibility':'worldwide','posted_at':'test','match_score':88,
        'matched_skills':'python, rag, langchain','missing_skills':'fastapi',
        'resume_suggestion':'Highlight your existing RAG deployment work if relevant.','url':'https://example.com'
    }]
    send_email(sample,'AI Job Hunter - Test Email'); print('Test email sent.')
