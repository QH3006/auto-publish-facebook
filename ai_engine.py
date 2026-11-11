import os
import time
import base64
import json
import logging
import requests
from typing import Dict, Any, Optional
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
  "category": "Thể loại sách (ví dụ: Văn học, Tiểu thuyết, Trinh thám, Manga, Kỹ năng, Kinh tế, Lịch sử, Thiếu nhi, Thơ ca, Tâm lý)"
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
- Dòng 1: Giới thiệu tên sách và tác giả (nếu có).
- Dòng 2-4: Tóm tắt súc tích, đúng sự thật về nội dung hoặc giá trị cốt lõi của cuốn sách theo nguồn chuẩn (tuyệt đối không phóng đại hay bịa đặt).
- Dòng cuối: Lời nhắn nhẹ nhàng mời bạn đọc quan tâm nhắn tiệm, kèm 2-3 hashtag (#SachHay #TiemSachCuaThuong).
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
def extract_book_info(image_path: str) -> Dict[str, str]:
    provider = config.AI_PROVIDER.lower()
    raw = None
    if provider == "gemini":
        raw = _call_gemini_vision(image_path, BOOK_EXTRACT_PROMPT)
    elif provider == "openai_compatible":
        b64 = image_to_base64(image_path)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": BOOK_EXTRACT_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }
        ]
        raw = _call_openai_compatible(messages)
    elif provider == "ollama":
        raw = _call_ollama_vision(image_path, BOOK_EXTRACT_PROMPT)
    if raw:
        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            if isinstance(data, dict):
                cat = data.get("category", "").strip() or "Khác"
                return {
                    "is_valid_book": data.get("is_valid_book", True),
                    "title": data.get("title", "").strip(),
                    "author": data.get("author", "").strip(),
                    "category": cat
                }
        except Exception:
            pass
    return {"is_valid_book": True, "title": "Sách hay", "author": "", "category": "Khác"}
BUYER_INQUIRY_IMAGE_PROMPT = """
Hãy nhìn vào bức ảnh này. Bức ảnh này do người dùng đăng lên nhóm Facebook với mục đích tìm mua hoặc hỏi xin pass sách cũ.
Bức ảnh có thể là:
1. Ảnh chụp bìa 1 hoặc nhiều cuốn sách họ cần tìm.
2. Ảnh chụp màn hình ứng dụng ghi chú (Notes), danh sách viết tay danh mục các cuốn sách cần mua.
3. Ảnh chụp danh sách giỏ hàng, đơn hàng hoặc wishlist.
Nhiệm vụ của bạn:
Đọc toàn bộ chữ và hình ảnh bìa trong bức ảnh, trích xuất tất cả các tựa đề sách (title) và tên tác giả (author) nếu có.
Trả về định dạng JSON thuần như sau:
{
  "titles": ["Tên sách 1", "Tên sách 2"],
  "authors": ["Tên tác giả 1"]
}
Lưu ý:
- Nếu không có cuốn sách nào hoặc không đọc được, trả về: {"titles": [], "authors": []}
- Chỉ xuất JSON thuần, tuyệt đối không bọc markdown hay thêm lời giải thích nào.
"""
def extract_buyer_inquiry_from_image(image_path: str) -> Dict[str, Any]:
    provider = config.AI_PROVIDER.lower()
    raw = None
    if provider == "gemini":
        raw = _call_gemini_vision(image_path, BUYER_INQUIRY_IMAGE_PROMPT)
    elif provider == "openai_compatible":
        b64 = image_to_base64(image_path)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": BUYER_INQUIRY_IMAGE_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }
        ]
        raw = _call_openai_compatible(messages)
    elif provider == "ollama":
        raw = _call_ollama_vision(image_path, BUYER_INQUIRY_IMAGE_PROMPT)
    if raw:
        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
            if isinstance(data, dict):
                return {
                    "titles": data.get("titles", []),
                    "authors": data.get("authors", [])
                }
        except Exception:
            pass
    return {"titles": [], "authors": []}
def get_fallback_caption() -> str:
    return "Một tựa sách hay cho những ngày thảnh thơi, bạn nhắn tiệm để rước sách về nhà nhé! #SachHay #TiemSachCuaThuong"
