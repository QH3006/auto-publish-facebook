import os
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
Hãy nhìn vào bức ảnh bìa cuốn sách này và trích xuất thông tin dưới dạng JSON:
{
  "title": "Tên cuốn sách (nếu không đọc được rõ thì ghi 'Sách hay')",
  "author": "Tên tác giả (nếu có, không có thì để trống '')"
}
Chỉ xuất đúng cú pháp JSON thuần, không kèm markdown hay lời dẫn.
"""
def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
def _call_gemini_vision(image_path: str, prompt: str) -> Optional[str]:
    api_key = config.GEMINI_API_KEY
    if not api_key or api_key == "YOUR_GEMINI_API_KEY":
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        img = Image.open(image_path)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        response = model.generate_content([prompt, img])
        return response.text.strip()
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
def generate_caption_for_image(image_path: str) -> str:
    provider = config.AI_PROVIDER.lower()
    result = None
    if provider == "gemini":
        result = _call_gemini_vision(image_path, CAPTION_PROMPT)
    elif provider == "openai_compatible":
        b64 = image_to_base64(image_path)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": CAPTION_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }
        ]
        result = _call_openai_compatible(messages)
    elif provider == "ollama":
        result = _call_ollama_vision(image_path, CAPTION_PROMPT)
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
            return json.loads(clean)
        except Exception:
            pass
    return {"title": "Sách hay", "author": ""}
def get_fallback_caption() -> str:
    return (
        "Mỗi trang sách mở ra là một hành trình tĩnh lặng đưa tâm hồn ta tìm về an yên.\n"
        "Gửi đến bạn một tựa sách hay cho những ngày cần chút khoảng lặng suy ngẫm.\n"
        "Ghé tiệm hôm nay để chọn cho mình một người bạn đồng hành nhé!\n"
        "#SachHay #MoiNgayMotCuonSach #Tiemsach"
    )