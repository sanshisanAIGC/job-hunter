"""AI 求职助手 - 配置加载"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()

# 飞书
FEISHU_APP_ID = _env("FEISHU_APP_ID")
FEISHU_APP_SECRET = _env("FEISHU_APP_SECRET")
FEISHU_NOTIFY_OPEN_ID = _env("FEISHU_NOTIFY_OPEN_ID")

# DeepSeek
DEEPSEEK_API_KEY = _env("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = _env("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = _env("DEEPSEEK_MODEL", "deepseek-v4-pro")

# 求职偏好
JOB_KEYWORDS = _env("JOB_KEYWORDS", "Python")
JOB_CITY = _env("JOB_CITY", "深圳")
JOB_SALARY_MIN = int(_env("JOB_SALARY_MIN", "0") or "0")
JOB_WELFARE = _env("JOB_WELFARE", "")

# 投递设置
MATCH_THRESHOLD = int(_env("MATCH_THRESHOLD", "70"))
MAX_DAILY_APPLY = int(_env("MAX_DAILY_APPLY", "50"))
GREET_INTERVAL_MIN = int(_env("GREET_INTERVAL_MIN", "30"))
GREET_INTERVAL_MAX = int(_env("GREET_INTERVAL_MAX", "120"))

# 路径
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RESUME_FILE = DATA_DIR / "resume.json"
APPLIED_FILE = DATA_DIR / "applied_jobs.json"
MESSAGE_FILE = DATA_DIR / "message_history.json"

# 部署
DEPLOY_HOST = _env("DEPLOY_HOST")
DEPLOY_USER = _env("DEPLOY_USER")
DEPLOY_PASSWORD = _env("DEPLOY_PASSWORD")

def validate_config() -> list[str]:
    missing = []
    for key in ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "DEEPSEEK_API_KEY"]:
        if not _env(key):
            missing.append(key)
    return missing
