import os
import time
import base64
import json
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageFilter, ImageStat, ImageChops
from PIL import Image
import config
import book_lookup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
CAPTION_PROMPT = """
Bạn là người quản lý tiệm sách thân thiện, tinh tế và yêu sách.
Hãy nhìn vào bức ảnh cuốn sách này và viết status giới thiệu thật ngắn gọn:
- Độ dài: Đúng 1 dòng ngắn gọn duy nhất (1 câu tinh tế, tự nhiên, truyền cảm hứng về cuốn sách, không xuống dòng, không viết dài dòng).
- Ở cuối dòng có thể thêm 1-2 hashtag ngắn (ví dụ: #SachHay #TiemSachCuaThuong).
- YÊU CẦU QUAN TRỌNG: Chỉ xuất đúng duy nhất 1 dòng status đó, tuyệt đối không thêm lời chào mở đầu hay câu giải thích nào khác.
"""
BOOK_EXTRACT_PROMPT = """
Bạn là chuyên gia phân tích ảnh bìa sách cho tiệm sách cũ.
Hãy nhìn vào bức ảnh này và trích xuất thông tin theo định dạng JSON:
{
  "is_valid_book": true,
  "title": "Tên cuốn sách chính",
  "author": "Tên tác giả",
  "category": "Thể loại sách (ví dụ: Văn học, Tiểu thuyết, Trinh thám, Manga, Kỹ năng, Kinh tế, Lịch sử, Thiếu nhi, Thơ ca, Tâm lý)",
  "is_clean_photo": true,
  "quality_note": ""
}
QUY TẮC PHÂN TÍCH QUAN TRỌNG:
1. Cuốn sách làm chủ thể chính:
   - Trong tiệm sách cũ, người chụp thường đặt 1 cuốn sách cần bán đứng thẳng ở trung tâm, quay mặt bìa ra trước.
   - Phía sau cuốn sách này có thể có một chồng sách hoặc giá sách được dùng làm điểm tựa (chống lưng).
   - Hãy coi cuốn sách đứng phía trước ở trung tâm là cuốn sách chủ thể. Đọc đúng Tựa sách, Tác giả và phán đoán Thể loại sách.
   - Khi đó: "is_valid_book": true.
2. Trường hợp ảnh KHÔNG hợp lệ (ảnh chồng sách hoặc kệ sách):
   - Nếu ảnh chỉ chụp một chồng/đống nhiều cuốn sách nằm ngang xếp từ dưới lên, hoặc chụp cả một kệ sách mà KHÔNG có cuốn sách nào quay mặt bìa làm chủ thể chính ở giữa.
   - Khi đó: "is_valid_book": false, "title": "", "author": "", "category": "".
3. Đánh giá chất lượng ảnh để đăng Fanpage:
   - Đặt "is_clean_photo": false và ghi lý do ngắn vào "quality_note" nếu ảnh bị mờ nhòe, rung tay, lóa sáng nặng không đọc rõ chữ, hoặc cuốn sách trông bám bụi bẩn, ố mốc, rách nát nặng mất thẩm mỹ.
   - Đặt "is_clean_photo": true nếu ảnh rõ nét và sách trông sạch sẽ, tươm tất.
Chỉ xuất đúng cú pháp JSON thuần, tuyệt đối không bọc markdown hay thêm lời giải thích nào.
"""
def build_grounded_caption_prompt(title: str = "", author: str = "", category: str = "", summary_data: Optional[Dict[str, str]] = None) -> str:
    samples_file = config.STORAGE_DIR / "style_samples.txt"
    style_context = ""
    if samples_file.exists():
        try:
            with open(samples_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    style_context = f"\n--- VĂN PHONG THỰC TẾ CỦA TIỆM ---\n{content}\n-----------------------------------\n"
        except Exception:
            pass
    book_meta = f"Tên sách: {title or 'Chưa rõ'} | Tác giả: {author or 'Chưa rõ'} | Thể loại: {category or 'Chưa rõ'}"
    if summary_data and summary_data.get("summary"):
        fact_rule = (
            f"TÀI LIỆU NGUỒN CHUẨN TỪ [{summary_data['source']}]:\n"
            f"\"\"\"{summary_data['summary']}\"\"\"\n"
            "QUY TẮC BẮT BUỘC: Chỉ tóm tắt nội dung sách DỰA HOÀN TOÀN VÀO TÀI LIỆU NGUỒN CHUẨN Ở TRÊN. "
            "TUYỆT ĐỐI KHÔNG tự bịa thêm chi tiết, nhân vật hay tình tiết không có trong tài liệu."
        )
    else:
        fact_rule = (
            "QUY TẮC BẮT BUỘC: Hãy sử dụng công cụ tìm kiếm Google để tìm thông tin thực tế về cuốn sách này (từ Tiki, Fahasa, Goodreads, NXB, Wikipedia...). "
            "CHỈ giới thiệu dựa trên kết quả tìm được chính xác. Nếu không tìm thấy nguồn xác thực về nội dung bên trong cuốn sách, "
            "TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ BỊA NỘI DUNG — chỉ giới thiệu trung thực tên sách, tác giả, thể loại và lời mời bạn đọc ghé tiệm."
        )
    return f"""
Bạn là người quản lý tiệm sách cũ thân thiện, tinh tế và trung thực.
Thông tin sách: {book_meta}
{fact_rule}
{style_context}
YÊU CẦU ĐỊNH DẠNG BÀI ĐĂNG (3 ĐẾN 5 DÒNG):
- Độ dài: Chính xác từ 3 đến 5 dòng (ngắt dòng rõ ràng, dễ đọc trên Facebook).
- Văn phong: Tự nhiên, gần gũi, xưng "tiệm" / "tiệm mình" và gọi người đọc là "bạn". TUYỆT ĐỐI KHÔNG mở đầu bằng "Dạ chào bạn", "Chào bạn", KHÔNG dùng các cụm sến như "chiếc tiệm nhỏ" hay đuôi câu "nhé ạ".
- Dòng 1: Giới thiệu trực tiếp tên sách, thể loại (nếu có) và tác giả theo mẫu: Tiệm xin giới thiệu cuốn <thể loại> "<Tên sách>" của tác giả <Tác giả>.
- Dòng 2-4: Tóm tắt súc tích, đúng sự thật về nội dung hoặc giá trị cốt lõi của cuốn sách theo nguồn chuẩn (tuyệt đối không phóng đại hay bịa đặt).
- Dòng cuối: Lời nhắn gọn gàng, tự nhiên theo mẫu: Nếu bạn muốn tìm đọc cuốn sách này, hãy nhắn liền cho tiệm mình nhé! kèm 2-3 hashtag (#SachHay #TiemSachCuaThuong).
- CHỈ xuất nội dung bài đăng hoàn chỉnh, không thêm lời chào hay giải thích thừa.
"""
def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
def _call_gemini_vision(image_path: str, prompt: str) -> Optional[str]:
    api_key = config.GEMINI_API_KEY
    if not api_key:
        return None
    try:
        b64_img = image_to_base64(image_path)
        ext = os.path.splitext(image_path)[1].lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent"
        headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": mime, "data": b64_img}}]}]}
        resp = requests.post(url, headers=headers, json=payload, timeout=45)
        if resp.status_code == 200:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        if resp.status_code == 429:
            logging.warning("[Gemini Vision] Đạt giới hạn req/phút, tự động chờ 12s để thử lại...")
            time.sleep(12)
            resp2 = requests.post(url, headers=headers, json=payload, timeout=45)
            if resp2.status_code == 200:
                return resp2.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        logging.error(f"[Gemini Vision] Error {resp.status_code}: {resp.text[:250]}")
        return None
    except Exception as e:
        logging.error(f"[Gemini Vision] Error: {e}")
        return None
def _call_openai_compatible(messages: list, model: str = None) -> Optional[str]:
    api_key = config.OPENAI_API_KEY
    base_url = config.OPENAI_BASE_URL.rstrip("/")
    target_model = model or config.OPENAI_MODEL
    if not api_key:
        return None
    try:
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": 0.7
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=45)
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            logging.error(f"[OpenAI-Compatible] API Error {resp.status_code}: {resp.text}")
            return None
    except Exception as e:
        logging.error(f"[OpenAI-Compatible] Error: {e}")
        return None
def _call_ollama_vision(image_path: str, prompt: str) -> Optional[str]:
    try:
        url = f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        b64 = image_to_base64(image_path)
        payload = {
            "model": config.OLLAMA_VISION_MODEL,
            "prompt": prompt,
            "images": [b64],
            "stream": False
        }
        resp = requests.post(url, json=payload, timeout=90)
        if resp.status_code == 200:
            return resp.json().get("response", "").strip()
        return None
    except Exception as e:
        logging.error(f"[Ollama Vision] Error: {e}")
        return None
def _call_gemini_grounded(prompt: str, use_google_search: bool = False) -> Optional[str]:
    api_key = config.GEMINI_API_KEY
    if not api_key:
        return None
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.GEMINI_MODEL}:generateContent"
        headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
        payload: Dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}
        if use_google_search:
            payload["tools"] = [{"google_search": {}}]
        resp = requests.post(url, headers=headers, json=payload, timeout=45)
        if resp.status_code == 200:
            parts = resp.json()["candidates"][0]["content"]["parts"]
            text = "\n".join(p.get("text", "") for p in parts if p.get("text")).strip()
            return text or None
        logging.error(f"[Gemini Grounded] Error {resp.status_code}: {resp.text[:250]}")
    except Exception as e:
        logging.error(f"[Gemini Grounded] Error: {e}")
    return None
def generate_caption_for_image(image_path: str, book_info: Optional[Dict[str, Any]] = None) -> str:
    title = (book_info or {}).get("title", "").strip()
    author = (book_info or {}).get("author", "").strip()
    category = (book_info or {}).get("category", "").strip()
    if not title or book_lookup.norm_words(title) in book_lookup.GENERIC_TITLES:
        extracted = extract_book_info(image_path)
        title = title or extracted.get("title", "")
        author = author or extracted.get("author", "")
        category = category or extracted.get("category", "")
    summary_data = book_lookup.lookup_verified_book_summary(title, author)
    prompt = build_grounded_caption_prompt(title, author, category, summary_data)
    provider = config.AI_PROVIDER.lower()
    result = None
    if provider == "gemini":
        use_search = summary_data is None
        result = _call_gemini_grounded(prompt, use_google_search=use_search)
    elif provider == "openai_compatible":
        result = _call_openai_compatible([{"role": "user", "content": prompt}])
    elif provider == "ollama":
        result = _call_ollama_vision(image_path, prompt)
    if result:
        return result
    return book_lookup.format_factual_post_without_ai(title, author, category, summary_data)
def _call_vision_provider(image_path: str, prompt: str) -> Optional[str]:
    provider = config.AI_PROVIDER.lower()
    if provider == "gemini":
        return _call_gemini_vision(image_path, prompt)
    if provider == "openai_compatible":
        b64 = image_to_base64(image_path)
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]
        }]
        return _call_openai_compatible(messages)
    if provider == "ollama":
        return _call_ollama_vision(image_path, prompt)
    return None
def check_local_image_sharpness(image_path: str) -> Tuple[bool, str]:
    if not image_path or not os.path.exists(image_path):
        return False, "Không tìm thấy file ảnh"
    try:
        with Image.open(image_path) as img:
            w, h = img.size
            if w < 320 or h < 320:
                return False, f"Ảnh độ phân giải quá thấp ({w}x{h})"
            g = img.convert("L")
            if max(w, h) > 1000:
                scale = 1000.0 / max(w, h)
                g = g.resize((int(w * scale), int(h * scale)))
            diff = ImageChops.difference(g, g.filter(ImageFilter.GaussianBlur(radius=2)))
            gw, gh = diff.size
            diff = diff.crop((4, 4, max(5, gw - 4), max(5, gh - 4)))
            hf_std = ImageStat.Stat(diff).stddev[0]
            if hf_std < 3.0:
                return False, f"Ảnh bị mờ/out nét (độ nét {hf_std:.1f})"
        return True, "OK"
    except Exception as e:
        return False, f"Lỗi kiểm tra ảnh: {e}"
def check_book_image_quality(image_path: str) -> Tuple[bool, str]:
    sharp_ok, sharp_reason = check_local_image_sharpness(image_path)
    if not sharp_ok:
        return False, sharp_reason
    prompt = """Hãy kiểm tra chất lượng bức ảnh sách này để đăng bán Fanpage tiệm sách cũ.
Đặt "is_good": false nếu gặp một trong các lỗi sau:
(a) Ảnh bị mờ, out nét, rung tay, quá tối hoặc lóa sáng nặng không nhìn rõ bìa.
(b) Cuốn sách trong ảnh trông bám bụi bẩn rõ rệt, ố mốc, bẩn thỉu hoặc rách nát nặng mất thẩm mỹ.
Đặt "is_good": true nếu ảnh rõ nét và cuốn sách trông sạch sẽ, lịch sự để đăng bán.
Chỉ xuất JSON thuần: {"is_good": true, "reason": ""}"""
    raw = _call_vision_provider(image_path, prompt)
    if raw:
        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            s, e = clean.find("{"), clean.rfind("}")
            data = json.loads(clean[s:e+1] if s != -1 and e > s else clean)
            if isinstance(data, dict) and data.get("is_good") is False:
                reason = (data.get("reason") or "").strip() or "Ảnh mờ hoặc sách bụi bẩn"
                return False, reason
        except Exception:
            pass
    return True, "OK"
def extract_book_info(image_path: str) -> Dict[str, Any]:
    sharp_ok, sharp_reason = check_local_image_sharpness(image_path)
    raw = _call_vision_provider(image_path, BOOK_EXTRACT_PROMPT)
    if raw:
        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            s, e = clean.find("{"), clean.rfind("}")
            data = json.loads(clean[s:e+1] if s != -1 and e > s else clean)
            if isinstance(data, dict):
                cat = data.get("category", "").strip() or "Khác"
                ai_clean = bool(data.get("is_clean_photo", True))
                q_note = sharp_reason if not sharp_ok else (data.get("quality_note", "") or "").strip()
                return {
                    "is_valid_book": data.get("is_valid_book", True),
                    "title": data.get("title", "").strip(),
                    "author": data.get("author", "").strip(),
                    "category": cat,
                    "is_clean_photo": bool(sharp_ok and ai_clean),
                    "quality_note": q_note
                }
        except Exception:
            pass
    return {
        "is_valid_book": True,
        "title": "Sách hay",
        "author": "",
        "category": "Khác",
        "is_clean_photo": sharp_ok,
        "quality_note": "" if sharp_ok else sharp_reason
    }
def verify_buyer_post_with_ai(post_text: str) -> bool:
    if not post_text or not post_text.strip():
        return False
    prompt = f"""Phân loại bài đăng trong nhóm mua bán sách cũ Facebook sau đây thành JSON duy nhất:
Nội dung bài đăng:
\"\"\"{post_text[:1000]}\"\"\"
QUY TẮC PHÂN LOẠI NGHIÊM NGẶT:
- Trả về {{"is_buyer": false}} nếu người đăng ĐANG CÓ SÁCH và muốn BÁN / PASS / THANH LÝ / NHƯỢNG LẠI (ví dụ: "Mình xin pass các đầu sách này ạ", "Em xin phép ad pass lại ít sách", liệt kê giá bán, tình trạng sách, mời người khác nhắn tin mua).
- CHỈ trả về {{"is_buyer": true}} nếu người đăng THỰC SỰ CHƯA CÓ SÁCH và đang hỏi TÌM MUA / CẦN MUA / TÌM NGƯỜI BÁN LẠI cho mình.
Chỉ xuất duy nhất JSON thuần {{"is_buyer": true}} hoặc {{"is_buyer": false}}, không giải thích."""
    provider = config.AI_PROVIDER.lower()
    raw = None
    if provider == "gemini":
        raw = _call_gemini_grounded(prompt, use_google_search=False)
    elif provider == "openai_compatible":
        raw = _call_openai_compatible([{"role": "user", "content": prompt}])
    if raw:
        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            s, e = clean.find("{"), clean.rfind("}")
            if s != -1 and e > s:
                data = json.loads(clean[s:e+1])
                if isinstance(data, dict) and "is_buyer" in data:
                    return bool(data["is_buyer"])
        except Exception:
            pass
    return True
def _build_buyer_inquiry_prompt(post_text: str = "") -> str:
    ctx = post_text[:600].strip() if post_text else "Không có"
    return f"""Hãy nhìn bức ảnh này kèm nội dung bài viết đi kèm trong nhóm sách cũ Facebook:
Nội dung bài viết đi kèm: \"\"\"{ctx}\"\"\"
Nhiệm vụ 1 - Xác định vai trò người đăng:
- Nếu bài viết hoặc bức ảnh là của NGƯỜI BÁN / ĐĂNG PASS / THANH LÝ SÁCH (ví dụ: "Mình xin pass...", "Em xin phép pass...", chụp chồng sách hoặc nhiều cuốn bày ra kèm giá/trạng thái để bán) -> đặt "is_buyer": false, "titles": [], "authors": [].
- Chỉ khi thực sự là NGƯỜI ĐANG TÌM MUA / CẦN MUA sách (chụp bìa sách cần tìm, ghi chú wishlist, giỏ hàng) -> đặt "is_buyer": true và trích xuất tất cả tựa sách ("titles"), tác giả ("authors").
Trả về JSON thuần theo đúng mẫu:
{{"is_buyer": true, "titles": ["Tên sách 1"], "authors": ["Tên tác giả 1"]}}
Không bọc markdown, không thêm lời giải thích."""
def extract_buyer_inquiry_from_image(image_path: str, post_text: str = "") -> Dict[str, Any]:
    provider = config.AI_PROVIDER.lower()
    prompt = _build_buyer_inquiry_prompt(post_text)
    raw = None
    if provider == "gemini":
        raw = _call_gemini_vision(image_path, prompt)
    elif provider == "openai_compatible":
        b64 = image_to_base64(image_path)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }
        ]
        raw = _call_openai_compatible(messages)
    elif provider == "ollama":
        raw = _call_ollama_vision(image_path, prompt)
    if raw:
        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            s, e = clean.find("{"), clean.rfind("}")
            data = json.loads(clean[s:e+1] if s != -1 and e > s else clean)
            if isinstance(data, dict):
                is_buyer = bool(data.get("is_buyer", True))
                if not is_buyer:
                    return {"is_buyer": False, "titles": [], "authors": []}
                return {
                    "is_buyer": True,
                    "titles": data.get("titles", []),
                    "authors": data.get("authors", [])
                }
        except Exception:
            pass
    return {"is_buyer": True, "titles": [], "authors": []}
def get_fallback_caption() -> str:
    return "Một tựa sách hay cho những ngày thảnh thơi, bạn nhắn tiệm để rước sách về nhà nhé! #SachHay #TiemSachCuaThuong"
