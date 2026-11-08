from pathlib import Path
import os, yaml
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}
def load_config(): return load_yaml(ROOT / 'config.yaml')
def load_candidate(): return load_yaml(ROOT / 'candidate_profile.yaml')
def database_path():
    raw = os.getenv('DATABASE_PATH', 'data/jobs.db')
    p = Path(raw)
    return p if p.is_absolute() else ROOT / p
