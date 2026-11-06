import os
import logging
import requests
from typing import Dict, Any
import config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
GRAPH_API_VERSION = "v21.0"
def publish_photo_to_facebook(image_path: str, caption: str) -> Dict[str, Any]:
    page_id = config.FB_PAGE_ID
    access_token = config.FB_PAGE_ACCESS_TOKEN
    if (not access_token or access_token == "YOUR_PAGE_ACCESS_TOKEN" or not page_id or page_id == "YOUR_FB_PAGE_ID"):
        logging.warning("DRY-RUN MODE: FB_PAGE_ID or FB_PAGE_ACCESS_TOKEN not configured in config.py.")
        logging.info(f"[SIMULATED POST] Image: {os.path.basename(image_path)}")
        logging.info(f"[SIMULATED CAPTION]:\n{caption}")
        return {
            "success": True,
            "simulated": True,
            "post_id": "simulated_fb_post_id_123456",
            "message": "Simulation successful (real token not configured yet)."
        }
    if not os.path.exists(image_path):
        logging.error(f"Image file to post does not exist: {image_path}")
        return {"success": False, "error": "Image file not found"}
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/photos"
    data = {
        "caption": caption,
        "access_token": access_token
    }
    try:
        with open(image_path, "rb") as image_file:
            files = {
                "source": image_file
            }
            logging.info(f"Sending photo {os.path.basename(image_path)} to Facebook via Graph API...")
            response = requests.post(url, data=data, files=files, timeout=30)
            result = response.json()
            if response.status_code == 200 and "id" in result:
                post_id = result.get("post_id", result.get("id"))
                logging.info(f"SUCCESS: Post published. Post ID: {post_id}")
                return {
                    "success": True,
                    "simulated": False,
                    "post_id": post_id,
                    "response": result
                }
            else:
                error_msg = result.get("error", {}).get("message", str(result))
                logging.error(f"Facebook API error: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "response": result
                }
    except Exception as e:
        logging.error(f"Connection error while posting to Facebook: {e}")
        return {"success": False, "error": str(e)}
if __name__ == "__main__":
    res = publish_photo_to_facebook("test.jpg", "Test bookstore status...")
    print(res)