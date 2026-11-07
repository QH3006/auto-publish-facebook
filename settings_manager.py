import os
import json
import logging
from typing import Dict, Any
import config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
SETTINGS_FILE = config.STORAGE_DIR / "settings.json"
def get_current_settings() -> Dict[str, Any]:
    return {
        "TARGET_PAGE_URL": config.TARGET_PAGE_URL,
        "POSTING_HOURS": config.POSTING_HOURS,
        "AI_PROVIDER": config.AI_PROVIDER,
        "GEMINI_API_KEY": config.GEMINI_API_KEY,
        "GEMINI_MODEL": config.GEMINI_MODEL,
        "OPENAI_API_KEY": config.OPENAI_API_KEY,
        "OPENAI_BASE_URL": config.OPENAI_BASE_URL,
        "OPENAI_MODEL": config.OPENAI_MODEL,
        "OLLAMA_BASE_URL": config.OLLAMA_BASE_URL,
        "OLLAMA_VISION_MODEL": config.OLLAMA_VISION_MODEL,
        "BROWSER_CHANNEL": config.BROWSER_CHANNEL,
        "MONITORED_GROUP_URLS": config.MONITORED_GROUP_URLS,
        "TARGET_POST_GROUP_URLS": config.TARGET_POST_GROUP_URLS,
        "GROUP_POSTING_HOUR": config.GROUP_POSTING_HOUR,
        "TELEGRAM_BOT_TOKEN": config.TELEGRAM_BOT_TOKEN,
        "TELEGRAM_CHAT_ID": config.TELEGRAM_CHAT_ID,
    }
def save_settings(new_settings: Dict[str, Any]) -> bool:
    try:
        current = get_current_settings()
        current.update(new_settings)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
        apply_settings_to_config(current)
        logging.info("[OK] Settings saved and applied successfully.")
        return True
    except Exception as e:
        logging.error(f"Error saving settings: {e}")
        return False
def apply_settings_to_config(settings: Dict[str, Any]):
    for key, val in settings.items():
        if hasattr(config, key):
            setattr(config, key, val)
def load_and_apply_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                apply_settings_to_config(saved)
                logging.info("[INFO] Custom settings loaded from storage/settings.json")
        except Exception as e:
            logging.error(f"Error loading settings.json: {e}")