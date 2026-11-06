# ==============================================================================
# 24/7 AUTOMATIC FACEBOOK POSTER CONFIGURATION
# ==============================================================================
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
IMAGES_DIR = STORAGE_DIR / "images"
DB_PATH = STORAGE_DIR / "database.db"
COOKIES_PATH = BASE_DIR / "cookies.json"
BROWSER_PROFILE_DIR = STORAGE_DIR / "browser_profile"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
# 1. TARGET FACEBOOK PAGE
TARGET_PAGE_URL = "https://www.facebook.com/YOUR_PAGE_URL_HERE"
# 2. SCHEDULE CONFIGURATION
POSTING_HOURS = ["06:00", "11:00", "19:00"]
SCAN_SCHEDULE_HOUR = "04:30"
CLEANUP_SCHEDULE_HOUR = "00:30"
# 3. POST FILTER RULES
REQUIRED_START_PHRASE = "HÔM NAY TIỆM CÓ GÌ?"
REQUIRED_SECOND_PHRASE = "CÓ THẬT NHIỀU SÁCH HAY"
BLACKLIST_KEYWORDS = [
    "truyện tranh",
    "sách tham khảo",
    "sách nuôi dạy con",
    "thiếu nhi",
]
MIN_DAYS_OLD = 7
MAX_DAYS_OLD = 30
PERSISTENT_INVENTORY_MODE = True
SOLD_RETENTION_DAYS = 7
DAILY_POSTS_COUNT = 3
# 4. FACEBOOK GRAPH API CONFIGURATION
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "YOUR_FB_PAGE_ID")
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "YOUR_PAGE_ACCESS_TOKEN")
# 5. MULTI-PROVIDER AI CONFIGURATION (GEMINI / OPENAI-COMPATIBLE / LOCAL OLLAMA)
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.5-flash"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = "gpt-4o-mini"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llava")
# 6. FACEBOOK GROUPS LEAD SCANNER
MONITORED_GROUP_URLS = [
    # "https://www.facebook.com/groups/example_group",
]
BUYER_INTENT_KEYWORDS = [
    "tìm mua",
    "cần tìm",
    "ai có cuốn",
    "ai có sách",
    "pass lại",
    "tìm sách",
    "mua sách",
    "cần mua",
    "pass sách",
    "xin pass",
    "nhượng lại",
]
LEAD_SCAN_INTERVAL_MINUTES = 120