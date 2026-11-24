import json
import time
import threading
from datetime import date, datetime
from typing import Dict, Any, Optional
import config
_LOCK = threading.Lock()
_STATUS_FILE = config.STORAGE_DIR / "ai_status.json"
ALERT_COOLDOWN_SECONDS = 1800
def _default_state() -> Dict[str, Any]:
    return {
        "date": date.today().isoformat(),
        "provider": config.AI_PROVIDER,
        "model": config.GEMINI_MODEL if config.AI_PROVIDER.lower() == "gemini" else config.OPENAI_MODEL,
        "status": "ok",
        "last_error": "",
        "last_error_at": "",
        "last_success_at": "",
        "last_alert_at": 0.0,
        "requests_today": 0,
        "prompt_tokens_today": 0,
        "output_tokens_today": 0,
        "total_tokens_today": 0,
    }
def _load_state() -> Dict[str, Any]:
    today_str = date.today().isoformat()
    state = _default_state()
    if _STATUS_FILE.exists():
        try:
            with open(_STATUS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                if saved.get("date") == today_str:
                    state.update(saved)
                else:
                    state["status"] = saved.get("status", "ok")
                    state["last_error"] = saved.get("last_error", "")
                    state["last_error_at"] = saved.get("last_error_at", "")
                    state["last_alert_at"] = saved.get("last_alert_at", 0.0)
        except Exception:
            pass
    return state
def _save_state(state: Dict[str, Any]) -> None:
    try:
        with open(_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
def record_success(provider: str, model: str, usage: Optional[Dict[str, Any]] = None) -> None:
    with _LOCK:
        state = _load_state()
        state["provider"] = provider
        state["model"] = model
        state["status"] = "ok"
        state["last_error"] = ""
        state["last_success_at"] = datetime.now().strftime("%H:%M:%S %d/%m")
        state["requests_today"] = int(state.get("requests_today", 0)) + 1
        if isinstance(usage, dict):
            p_tok = int(usage.get("promptTokenCount") or usage.get("prompt_tokens") or 0)
            o_tok = int(usage.get("candidatesTokenCount") or usage.get("completion_tokens") or 0)
            t_tok = int(usage.get("totalTokenCount") or usage.get("total_tokens") or (p_tok + o_tok))
            state["prompt_tokens_today"] = int(state.get("prompt_tokens_today", 0)) + p_tok
            state["output_tokens_today"] = int(state.get("output_tokens_today", 0)) + o_tok
            state["total_tokens_today"] = int(state.get("total_tokens_today", 0)) + t_tok
        _save_state(state)
def record_error(provider: str, model: str, status_code: int, detail: str = "") -> None:
    d_lower = (detail or "").lower()
    is_quota = status_code == 429 or any(k in d_lower for k in ("resource_exhausted", "quota", "insufficient_quota", "rate_limit"))
    is_auth = status_code in (401, 403)
    new_status = "quota_exceeded" if is_quota else ("auth_error" if is_auth else "error")
    now_str = datetime.now().strftime("%H:%M:%S %d/%m")
    should_alert = False
    snapshot: Dict[str, Any] = {}
    with _LOCK:
        state = _load_state()
        state["provider"] = provider
        state["model"] = model
        state["status"] = new_status
        state["last_error"] = f"HTTP {status_code}: {(detail or '')[:160]}"
        state["last_error_at"] = now_str
        if is_quota or is_auth:
            now_ep = time.time()
            if (now_ep - float(state.get("last_alert_at", 0.0))) >= ALERT_COOLDOWN_SECONDS:
                state["last_alert_at"] = now_ep
                should_alert = True
        _save_state(state)
        snapshot = dict(state)
    if should_alert:
        try:
            import telegram_bot
            title = "🚨 [HẾT HẠN MỨC TOKEN AI]" if is_quota else "🔑 [LỖI API KEY AI]"
            tok_fmt = f"{snapshot.get('total_tokens_today', 0):,}".replace(",", ".")
            msg = (
                f"{title}\n\n"
                f"• Provider: {provider} ({model})\n"
                f"• Mã lỗi: HTTP {status_code}\n"
                f"• Đã dùng hôm nay: {tok_fmt} token ({snapshot.get('requests_today', 0)} lượt)\n"
                f"• Chi tiết: {(detail or '')[:180]}\n\n"
                f"👉 Vui lòng kiểm tra hạn mức hoặc thay API key mới trong file .env!"
            )
            telegram_bot.send_alert_to_all(msg)
        except Exception:
            pass
def get_status() -> Dict[str, Any]:
    with _LOCK:
        state = _load_state()
    prov = config.AI_PROVIDER.lower()
    if prov == "gemini" and not config.GEMINI_API_KEY and state.get("status") == "ok" and state.get("requests_today", 0) == 0:
        state["status"] = "unconfigured"
    elif prov == "openai_compatible" and not config.OPENAI_API_KEY and state.get("status") == "ok" and state.get("requests_today", 0) == 0:
        state["status"] = "unconfigured"
    return state
