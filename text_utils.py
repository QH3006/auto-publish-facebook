import unicodedata
import re
from typing import Tuple
import config
def normalize_text(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = re.sub(r"[ \t]+", " ", normalized).strip()
    return normalized
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