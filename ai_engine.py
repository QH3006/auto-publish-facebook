import os
import time
import base64
import json
import logging
import requests
from typing import Dict, Any, Optional
from PIL import Image
import config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
CAPTION_PROMPT = """
Bạn là người quản lý tiệm sách thân thiện, tinh tế và yêu sách.
Hãy nhìn vào bức ảnh cuốn sách này và viết một đoạn status giới thiệu thật cuốn hút:
- Độ dài: Đúng từ 3 đến 5 dòng (không viết dài dòng, không lan man).
- Nội dung: Giới thiệu ngắn gọn tinh thần hoặc thông điệp ý nghĩa của cuốn sách trong ảnh, khơi gợi cảm hứng đọc cho bạn đọc.
- Văn phong: Nhẹ nhàng, ấm áp, sâu lắng và tự nhiên.
- Ở cuối có thể thêm 1-2 hashtag liên quan (ví dụ: #SachHay #GocDocSach #MoiNgayMotCuonSach).
- YÊU CẦU QUAN TRỌNG: Chỉ xuất đúng nội dung đoạn status đó, tuyệt đối không thêm lời chào mở đầu hay câu giải thích nào khác.
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
def get_caption_prompt() -> str:
    samples_file = config.STORAGE_DIR / "style_samples.txt"
    style_context = ""
    if samples_file.exists():
        try:
            with open(samples_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    style_context = (
                        "\n--- CÁC BÀI VIẾT MẪU VĂN PHONG THỰC TẾ CỦA TIỆM ĐỂ BẠN HỌC THEO ---\n"
                        f"{content}\n"
                        "--------------------------------------------------------------------\n"
                        "Hãy viết bài giới thiệu cuốn sách trong ảnh theo đúng văn phong tự nhiên, ấm áp, cách ngắt dòng và dùng từ như các bài mẫu trên.\n"
                    )
        except Exception:
            pass
    return f"""
Bạn là người quản lý tiệm sách thân thiện, tinh tế và yêu sách.
Hãy nhìn vào bức ảnh cuốn sách này và viết một đoạn status giới thiệu thật cuốn hút:
- Độ dài: Đúng từ 3 đến 5 dòng (không viết dài dòng, không lan man).
- Nội dung: Giới thiệu ngắn gọn tinh thần hoặc thông điệp ý nghĩa của cuốn sách trong ảnh, khơi gợi cảm hứng đọc cho bạn đọc.
- Văn phong: Nhẹ nhàng, ấm áp, sâu lắng và tự nhiên.
- Ở cuối có thể thêm 1-2 hashtag liên quan (ví dụ: #SachHay #GocDocSach #MoiNgayMotCuonSach).
{style_context}
- YÊU CẦU QUAN TRỌNG: Chỉ xuất đúng nội dung đoạn status đó, tuyệt đối không thêm lời chào mở đầu hay câu giải thích nào khác.
"""
def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
def _call_gemini_vision(image_path: str, prompt: str) -> Optional[str]:
    api_key = config.GEMINI_API_KEY
    if not api_key:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        img = Image.open(image_path)
        response = model.generate_content([prompt, img])
        return response.text.strip()
    except Exception as e:
        if "429" in str(e):
            logging.warning("[Gemini Vision] Đạt giới hạn 15 req/phút, tự động chờ 12s để thử lại...")
            time.sleep(12)
            try:
                response = model.generate_content([prompt, img])
                return response.text.strip()
            except Exception:
                pass
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
def generate_caption_for_image(image_path: str) -> str:
    provider = config.AI_PROVIDER.lower()
    result = None
    prompt = get_caption_prompt()
    if provider == "gemini":
        result = _call_gemini_vision(image_path, prompt)
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
        result = _call_openai_compatible(messages)
    elif provider == "ollama":
        result = _call_ollama_vision(image_path, prompt)
    if result:
        return result
    return get_fallback_caption()
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
    return (
        "Mỗi trang sách mở ra là một hành trình tĩnh lặng đưa tâm hồn ta tìm về an yên.\n"
        "Gửi đến bạn một tựa sách hay cho những ngày cần chút khoảng lặng suy ngẫm.\n"
        "Ghé tiệm hôm nay để chọn cho mình một người bạn đồng hành nhé!\n"
        "#SachHay #MoiNgayMotCuonSach #Tiemsach"
    )
