import re
import html
import logging
import unicodedata
from typing import Optional, Dict
import requests
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
GENERIC_TITLES = {"sach hay", "sach cu", "sach moi", "sach", "untitled", "chua ro", "nhieu cuon sach"}
def strip_accents(text: str) -> str:
    s = unicodedata.normalize("NFD", text or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D")
def norm_words(text: str) -> str:
    s = strip_accents((text or "").lower())
    return " ".join(re.sub(r"[^\w\s]", " ", s).split())
def is_exact_title_match(query_title: str, candidate_title: str) -> bool:
    qt = norm_words(query_title)
    ct = norm_words(candidate_title)
    if not qt or qt in GENERIC_TITLES:
        return False
    if len(qt.split()) < 2 and len(qt) < 5:
        return False
    return qt in ct
def clean_html_text(raw: str) -> str:
    t = html.unescape(raw or "")
    t = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</h[1-6]>", ". ", t, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\.\s*\.", ".", t)
    for stop_phrase in ["Giá sản phẩm trên Tiki", "Sản phẩm này là tài sản cá nhân", "Chính sách đổi trả"]:
        if stop_phrase in t:
            t = t.split(stop_phrase)[0].strip()
    return t
def _is_json_resp(resp) -> bool:
    return resp.status_code == 200 and "application/json" in resp.headers.get("Content-Type", "").lower() and bool(resp.text.strip())
def _lookup_goodreads(title: str, author: str = "") -> Optional[Dict[str, str]]:
    try:
        q = f"{title} {author}".strip()
        resp = requests.get("https://www.goodreads.com/search", params={"q": q}, headers=HEADERS, timeout=8)
        if resp.status_code != 200 or "bookTitle" not in resp.text:
            return None
        matches = re.findall(r'class="bookTitle"[^>]*href="([^"]+)"[^>]*>.*?<span[^>]*>(.*?)</span>', resp.text, re.S)
        for href, raw_name in matches[:5]:
            name = clean_html_text(raw_name)
            if is_exact_title_match(title, name):
                book_url = "https://www.goodreads.com" + href.split("?")[0]
                bp = requests.get(book_url, headers=HEADERS, timeout=8)
                if bp.status_code == 200:
                    m = re.search(r'data-testid="description"[^>]*>(.*?)</div>', bp.text, re.S)
                    if not m:
                        m = re.search(r'name="description"\s+content="([^"]+)"', bp.text, re.I)
                    if m:
                        desc = clean_html_text(m.group(1))
                        if len(desc) >= 60:
                            return {"summary": desc[:1400], "source": "Goodreads"}
    except Exception as e:
        logging.debug(f"[BookLookup Goodreads] Skip: {e}")
    return None
def _lookup_tiki(title: str, author: str = "") -> Optional[Dict[str, str]]:
    try:
        q = f"{title} {author}".strip()
        resp = requests.get("https://tiki.vn/api/v2/products", params={"limit": 8, "q": q, "category": "8322"}, headers=HEADERS, timeout=8)
        if not _is_json_resp(resp):
            return None
        for item in resp.json().get("data", []):
            if is_exact_title_match(title, item.get("name", "")):
                pid = item.get("id")
                detail_resp = requests.get(f"https://tiki.vn/api/v2/products/{pid}", headers=HEADERS, timeout=8)
                if _is_json_resp(detail_resp):
                    d = detail_resp.json()
                    desc = clean_html_text(d.get("description") or d.get("short_description") or "")
                    if len(desc) >= 60:
                        return {"summary": desc[:1400], "source": "Tiki Sách"}
    except Exception as e:
        logging.debug(f"[BookLookup Tiki] Skip: {e}")
    return None
def _lookup_google_books(title: str, author: str = "") -> Optional[Dict[str, str]]:
    try:
        q = f"{title} {author}".strip()
        resp = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": q, "maxResults": 5}, timeout=8)
        if not _is_json_resp(resp):
            return None
        for item in resp.json().get("items", []):
            vi = item.get("volumeInfo", {})
            if is_exact_title_match(title, vi.get("title", "")):
                desc = clean_html_text(vi.get("description") or "")
                if len(desc) >= 50:
                    return {"summary": desc[:1400], "source": "Google Books"}
    except Exception as e:
        logging.debug(f"[BookLookup GoogleBooks] Skip: {e}")
    return None
def _lookup_wikipedia_vi(title: str, author: str = "") -> Optional[Dict[str, str]]:
    try:
        q = f'"{title}" sách {author}'.strip()
        resp = requests.get("https://vi.wikipedia.org/w/api.php", params={"action": "query", "list": "search", "srsearch": q, "format": "json"}, headers=HEADERS, timeout=8)
        if not _is_json_resp(resp):
            return None
        for hit in resp.json().get("query", {}).get("search", [])[:3]:
            w_title = hit.get("title", "")
            if is_exact_title_match(title, w_title):
                r2 = requests.get("https://vi.wikipedia.org/w/api.php", params={"action": "query", "prop": "extracts", "exintro": True, "explaintext": True, "titles": w_title, "format": "json"}, headers=HEADERS, timeout=8)
                if _is_json_resp(r2):
                    for page in r2.json().get("query", {}).get("pages", {}).values():
                        ext = clean_html_text(re.sub(r"\([^)]*tiếng[^)]*\)", "", page.get("extract") or ""))
                        if len(ext) >= 50:
                            return {"summary": ext[:1400], "source": "Wikipedia"}
    except Exception as e:
        logging.debug(f"[BookLookup Wiki] Skip: {e}")
    return None
def lookup_verified_book_summary(title: str, author: str = "") -> Optional[Dict[str, str]]:
    if not title or norm_words(title) in GENERIC_TITLES:
        return None
    for fn in (_lookup_goodreads, _lookup_tiki, _lookup_google_books, _lookup_wikipedia_vi):
        res = fn(title, author)
        if res:
            logging.info(f"[BookLookup] Tìm thấy nội dung chuẩn cho '{title}' từ nguồn [{res['source']}]")
            return res
    logging.info(f"[BookLookup] Không tìm thấy nguồn chuẩn bên ngoài cho '{title}'.")
    return None
def format_factual_post_without_ai(title: str = "", author: str = "", category: str = "", summary_data: Optional[Dict[str, str]] = None) -> str:
    clean_title = (title or "").strip()
    clean_author = (author or "").strip()
    clean_cat = (category or "").strip()
    header = f"📖 {clean_title}" if clean_title and norm_words(clean_title) not in GENERIC_TITLES else "📖 Một tựa sách hay vừa lên kệ tiệm hôm nay"
    if clean_author and clean_author.lower() not in {"chưa rõ", "unknown", ""}:
        header += f" — {clean_author}"
    lines = [header]
    if summary_data and summary_data.get("summary"):
        raw = summary_data["summary"]
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw) if len(s.strip()) > 18]
        picked = []
        total_len = 0
        for s in sentences:
            if total_len + len(s) > 320 and picked:
                break
            picked.append(s)
            total_len += len(s)
            if len(picked) >= 3:
                break
        if picked:
            lines.extend(picked[:3])
        else:
            lines.append(raw[:260].rstrip() + "...")
    else:
        if clean_cat and clean_cat.lower() not in {"khác", "chưa rõ", ""}:
            lines.append(f"🏷️ Thể loại: {clean_cat} — Sách đang có sẵn tại kệ tiệm, bản đẹp giữ gìn cẩn thận.")
        else:
            lines.append("Sách đang có sẵn tại kệ tiệm, bản đẹp giữ gìn cẩn thận chờ bạn hữu duyên.")
    lines.append("Bạn ưng cuốn này cứ nhắn tiệm để xem thêm chi tiết và rước sách về nhé! #SachHay #TiemSachCuaThuong")
    return "\n".join(lines[:5])
