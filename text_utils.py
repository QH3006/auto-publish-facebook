import unicodedata
import re
from typing import Tuple
import config
from datetime import datetime, date, timedelta
def parse_vietnamese_date(text: str) -> str:
    today = date.today()
    if not text:
        return today.strftime("%Y-%m-%d")
    text_lower = text.lower().strip()
    m = re.search(r'(\d{1,2})\s+tháng\s+(\d{1,2})', text_lower)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = today.year
        if month > today.month:
            year -= 1
        try:
            return date(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            pass
    m_day = re.search(r'(\d+)\s*ngày', text_lower)
    if m_day:
        days_ago = int(m_day.group(1))
        return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    m_week = re.search(r'(\d+)\s*tuần', text_lower)
    if m_week:
        weeks_ago = int(m_week.group(1))
        return (today - timedelta(days=weeks_ago * 7)).strftime("%Y-%m-%d")
    if "hôm qua" in text_lower:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    return today.strftime("%Y-%m-%d")
def normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = re.sub(r"[ \t]+", " ", normalized).strip()
    return normalized
def extract_category_from_post(post_text: str) -> str:
    if not post_text:
        return ""
    norm = normalize_text(post_text)
    lines = [l.strip() for l in norm.split("\n") if l.strip()]
    skip_keywords = ["hôm nay tiệm có gì", "có thật nhiều sách hay", "giá sách", "tiệm", "xem thêm", "ship", "inbox", "liên hệ", "địa chỉ", "pass"]
    for line in lines:
        l_lower = line.lower()
        if any(kw in l_lower for kw in skip_keywords):
            continue
        if 2 <= len(line) <= 50 and not line.startswith("#"):
            cleaned_cat = re.sub(r"\s+(ạ|nha|nhé|nè|ạ\.*|\.+)$", "", line, flags=re.IGNORECASE).strip()
            return cleaned_cat
    return ""
def check_post_eligibility(post_text: str) -> Tuple[bool, str]:
    if not post_text:
        return False, "Post text is empty."
    norm_text = normalize_text(post_text)
    norm_lower = norm_text.lower()
    for bad_word in config.BLACKLIST_KEYWORDS:
        bad_word_norm = normalize_text(bad_word).lower()
        if bad_word_norm in norm_lower:
            return False, f"Excluded by blacklist keyword: '{bad_word}'"
    start_phrase_norm = normalize_text(config.REQUIRED_START_PHRASE).lower()
    second_phrase_norm = normalize_text(config.REQUIRED_SECOND_PHRASE).lower()
    if start_phrase_norm not in norm_lower:
        return False, f"Missing required start phrase: '{config.REQUIRED_START_PHRASE}'"
    if second_phrase_norm not in norm_lower:
        return False, f"Missing required secondary phrase: '{config.REQUIRED_SECOND_PHRASE}'"
    return True, "Eligible"
