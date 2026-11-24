# ==============================================================================
# 24/7 AUTOMATIC FACEBOOK POSTER CONFIGURATION
# ==============================================================================
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
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
TARGET_PAGE_URL = "https://www.facebook.com/tiemsachcuathuong/"
# 2. SCHEDULE CONFIGURATION
POSTING_HOURS = ["11:00", "19:00"]
SCAN_SCHEDULE_HOUR = "04:30"
CLEANUP_SCHEDULE_HOUR = "00:30"
WEEKLY_BACKUP_HOUR = os.getenv("WEEKLY_BACKUP_HOUR", "07:00")
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
MAX_DAYS_OLD = 90
PERSISTENT_INVENTORY_MODE = True
SOLD_RETENTION_DAYS = 7
DAILY_POSTS_COUNT = 3
# 4. MY FANPAGE PUBLISHING CONFIGURATION (PLAYWRIGHT BROWSER AUTOMATION)
# Any Facebook account with Admin/Editor access to this page will work!
MY_FANPAGE_URL = os.getenv("MY_FANPAGE_URL", "https://www.facebook.com/104950864827739")
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "104950864827739")
# 5. MULTI-PROVIDER AI CONFIGURATION (GEMINI / OPENAI-COMPATIBLE / LOCAL OLLAMA)
AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.5-flash-lite"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = "gpt-4o-mini"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llava")
# 6. FACEBOOK GROUPS LEAD SCANNER
# Browser channel: None (Playwright engine) | "msedge" (Windows built-in Edge) | "chrome" (System Chrome)
BROWSER_CHANNEL = "msedge"
MONITORED_GROUP_URLS = [
    # "https://www.facebook.com/groups/example_group",
    "https://www.facebook.com/groups/225413611557113/",
    "https://www.facebook.com/groups/1572146076366815/",
    "https://www.facebook.com/groups/979050155491747/",
    "https://www.facebook.com/groups/477952032340642/",
    "https://www.facebook.com/groups/3440463649349254/",
    "https://www.facebook.com/groups/703844251801628/",
    "https://www.facebook.com/groups/1374822839964696/",
]
BUYER_INTENT_KEYWORDS = [
    "tìm mua", "cần mua", "hỏi mua", "mua lại", "muốn mua", "tìm sách", "cần tìm",
    "mình cần sách", "em cần sách", "đang cần sách", "cần mua sách", "cần tìm sách", "đang tìm sách",
    "tìm cuốn", "tìm quyển", "tìm bộ", "tìm tập", "mình tìm cuốn", "em tìm cuốn",
    "mình tìm quyển", "em tìm quyển", "mình tìm bộ", "em tìm bộ", "đang tìm cuốn",
    "ai có cuốn", "ai có quyển", "ai có sách", "ai có bộ", "ai còn sách",
    "ai pass", "ai pass lại", "ai có pass", "bạn nào pass", "bác nào pass",
    "pass cho mình", "pass cho em", "pass lại cho mình", "pass lại cho em", "để lại cho mình", "nhượng lại cho mình",
    "tìm người pass", "có ai pass", "hóng pass", "tìm pass", "ai bán", "có ai bán",
    "bác nào có", "bạn nào có", "ai có không", "ai có ko", "ai có ib", "ai có inbox", "ai còn cuốn", "ai còn quyển",
    "tìm như hình", "tìm như ảnh", "mua như hình", "mua như ảnh"
]
SELLER_EXCLUDE_KEYWORDS = [
    "#pass", "pass nhanh", "pass gấp", "pass all", "mình pass", "em pass", "e pass", "pass bớt",
    "pass sách", "pass rẻ", "giá pass", "thanh lý", "xả kho", "xả tủ", "dọn nhà", "dọn kệ", "dọn tủ", "dọn phòng",
    "lấy all", "lấy cả", "lấy hết", "nhận all ptgd", "ptgd", "ship cod", "ck full", "bank full",
    "giá trên ảnh", "giá trong ảnh", "giá như hình", "đồng giá", "pass lại cho", "mình pass lại", "em pass lại",
    "cần pass lại", "muốn pass lại", "pass lại giá", "pass lại rẻ", "bạn nào cần", "ai cần ib", "ai cần nhắn",
    "xả sách", "chủ mới", "tìm chủ mới", "tìm chủ", "nhà mới", "tìm nhà mới",
    "độ mới", "mới 99%", "mới 98%", "mới 95%", "new seal", "nguyên seal", "lên kệ",
    "còn mấy cuốn", "còn vài cuốn", "mình có mấy cuốn", "em có mấy cuốn", "giá chỉ", "freeship", "free ship", "không cod", "ko cod",
    "xin pass", "mình xin pass", "em xin pass", "e xin pass", "xin phép pass", "xin phép ad", "xin phép admin",
    "pass các", "pass mấy", "pass vài", "pass ít", "pass thu hồi", "cần pass", "muốn pass",
    "mình bán", "em bán", "cần bán", "muốn bán", "nhượng lại"
]
LEAD_SCAN_INTERVAL_MINUTES = 120
LEAD_SCAN_QUIET_START_HOUR = 22
LEAD_SCAN_QUIET_END_HOUR = 6
# 7. TELEGRAM BOT ASSISTANT (REMOTE MOBILE LOOKUP & LEAD ALERTS)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
# 8. FACEBOOK GROUP AUTO-POSTER (1 POST PER DAY AT 18:00 WITH 10 IMAGES)
TARGET_POST_GROUP_URLS = [
    # "https://www.facebook.com/groups/example_group",
    "https://www.facebook.com/groups/1374822839964696",
    "https://www.facebook.com/groups/1572146076366815",
    "https://www.facebook.com/groups/979050155491747",
    "https://www.facebook.com/groups/225413611557113",
    "https://www.facebook.com/groups/703844251801628",
    "https://www.facebook.com/groups/477952032340642",
    "https://www.facebook.com/groups/3440463649349254",
]
GROUP_POSTING_HOUR = "18:00"
GROUP_POST_IMAGES_COUNT = 10