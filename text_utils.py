import unicodedata
import re
from typing import Tuple
import config
from datetime import datetime, date, timedelta
ENG_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6,
    "jul": 7, "july": 7, "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
def parse_vietnamese_date(text: str) -> str:
    today = date.today()
    if not text:
        return today.strftime("%Y-%m-%d")
    text_lower = normalize_text(text).lower()
    m = re.search(r'(\d{1,2})\s+tháng\s+(\d{1,2})(?:[,\s]+(\d{4}))?', text_lower)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else today.year
        if not m.group(3) and month > today.month:
            year -= 1
        try:
            d = date(year, month, day)
            if not m.group(3) and d > today:
                d = date(year - 1, month, day)
            return d.strftime("%Y-%m-%d")
        except ValueError:
            pass
    m_en1 = re.search(
        r'\b(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\b(?:[,\s]+(\d{4}))?',
        text_lower,
    )
    m_en2 = None if m_en1 else re.search(
        r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)\s+(\d{1,2})\b(?:[,\s]+(\d{4}))?',
        text_lower,
    )
    if m_en1 or m_en2:
        if m_en1:
            day = int(m_en1.group(1))
            month = ENG_MONTHS[m_en1.group(2)]
            yr_str = m_en1.group(3)
        else:
            month = ENG_MONTHS[m_en2.group(1)]
            day = int(m_en2.group(2))
            yr_str = m_en2.group(3)
        year = int(yr_str) if yr_str else today.year
        if not yr_str and month > today.month:
            year -= 1
        try:
            d = date(year, month, day)
            if not yr_str and d > today:
                d = date(year - 1, month, day)
            return d.strftime("%Y-%m-%d")
        except ValueError:
            pass
    m_hour = re.search(r'\b(\d{1,2})\s*(?:giờ|hours?|hrs?|h)\b', text_lower)
    if m_hour:
        hrs = int(m_hour.group(1))
        return (datetime.now() - timedelta(hours=hrs)).strftime("%Y-%m-%d")
    if re.search(r'(?:phút|vừa xong|giây|\bmins?\b|\bminutes?\b|\bjust now\b|\bsecs?\b|\bseconds?\b)', text_lower):
        return today.strftime("%Y-%m-%d")
    m_day = re.search(r'(\d+)\s*(?:ngày|days?|d)\b', text_lower)
    if m_day:
        days_ago = int(m_day.group(1))
        return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    m_week = re.search(r'(\d+)\s*(?:tuần|weeks?|w)\b', text_lower)
    if m_week:
        weeks_ago = int(m_week.group(1))
        return (today - timedelta(days=weeks_ago * 7)).strftime("%Y-%m-%d")
    if "hôm qua" in text_lower or "yesterday" in text_lower:
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
