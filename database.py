import sqlite3
import os
from datetime import datetime, date
from typing import List, Dict, Optional
import config
def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                post_id TEXT PRIMARY KEY,
                page_url TEXT,
                post_text TEXT,
                post_date TEXT,
                created_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT,
                image_url TEXT,
                local_path TEXT,
                image_hash TEXT UNIQUE,
                post_date TEXT,
                title TEXT DEFAULT '',
                author TEXT DEFAULT '',
                status TEXT DEFAULT 'available',
                sold_at TEXT,
                is_published INTEGER DEFAULT 0,
                published_at TEXT,
                created_at TEXT,
                FOREIGN KEY (post_id) REFERENCES posts(post_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matched_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_url TEXT,
                post_url TEXT,
                content_snippet TEXT,
                matched_book_id INTEGER,
                matched_book_title TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                UNIQUE(post_url, matched_book_id)
            )
        """)
        cursor.execute("PRAGMA table_info(images)")
        columns = [row[1] for row in cursor.fetchall()]
        if "title" not in columns:
            cursor.execute("ALTER TABLE images ADD COLUMN title TEXT DEFAULT ''")
        if "author" not in columns:
            cursor.execute("ALTER TABLE images ADD COLUMN author TEXT DEFAULT ''")
        if "status" not in columns:
            cursor.execute("ALTER TABLE images ADD COLUMN status TEXT DEFAULT 'available'")
        if "sold_at" not in columns:
            cursor.execute("ALTER TABLE images ADD COLUMN sold_at TEXT")
        conn.commit()
def save_post(post_id: str, page_url: str, post_text: str, post_date: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        cursor.execute("""
            INSERT OR IGNORE INTO posts (post_id, page_url, post_text, post_date, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (post_id, page_url, post_text, post_date, now_str))
        conn.commit()
        return cursor.rowcount > 0
def save_image(post_id: str, image_url: str, local_path: str, image_hash: str, post_date: str, title: str = "", author: str = "") -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        try:
            cursor.execute("""
                INSERT INTO images (
                    post_id, image_url, local_path, image_hash, post_date, 
                    title, author, status, is_published, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 'available', 0, ?)
            """, (post_id, image_url, local_path, image_hash, post_date, title, author, now_str))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
def update_book_metadata(image_id: int, title: str, author: str = ""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE images SET title = ?, author = ? WHERE id = ?", (title, author, image_id))
        conn.commit()
def mark_book_sold(image_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        cursor.execute("UPDATE images SET status = 'sold_out', sold_at = ? WHERE id = ?", (now_str, image_id))
        conn.commit()
def mark_book_available(image_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE images SET status = 'available', sold_at = NULL WHERE id = ?", (image_id,))
        conn.commit()
def search_available_books(keyword: str) -> List[Dict]:
    results = []
    cleaned_query = keyword.strip().lower()
    kw_pattern = f"%{cleaned_query}%"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.id, i.post_id, i.local_path, i.title, i.author, i.status, 
                   i.post_date, p.post_text
            FROM images i
            LEFT JOIN posts p ON i.post_id = p.post_id
            WHERE i.status = 'available'
              AND (
                  LOWER(i.title) LIKE ?
                  OR LOWER(i.author) LIKE ?
                  OR LOWER(p.post_text) LIKE ?
              )
            ORDER BY i.id DESC
        """, (kw_pattern, kw_pattern, kw_pattern))
        rows = cursor.fetchall()
        if not rows:
            cursor.execute("""
                SELECT i.id, i.post_id, i.local_path, i.title, i.author, i.status, 
                       i.post_date, p.post_text
                FROM images i
                LEFT JOIN posts p ON i.post_id = p.post_id
                WHERE i.status = 'available'
            """)
            all_available = cursor.fetchall()
            matched_rows = []
            for item in all_available:
                title = (item["title"] or "").strip().lower()
                author = (item["author"] or "").strip().lower()
                if (title and len(title) >= 3 and title in cleaned_query) or (author and len(author) >= 3 and author in cleaned_query):
                    matched_rows.append(item)
            rows = matched_rows
        for row in rows:
            if os.path.exists(row["local_path"]):
                results.append(dict(row))
    return results
def get_unposted_eligible_images(min_days: int = 7, max_days: int = 30) -> List[Dict]:
    today = date.today()
    results = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, post_id, local_path, post_date, image_url, title, author 
            FROM images 
            WHERE is_published = 0 AND status = 'available'
            ORDER BY RANDOM()
        """)
        rows = cursor.fetchall()
        for row in rows:
            post_date_str = row["post_date"]
            try:
                p_date = datetime.strptime(post_date_str, "%Y-%m-%d").date()
                age_days = (today - p_date).days
            except Exception:
                continue
            if min_days <= age_days <= max_days:
                if os.path.exists(row["local_path"]):
                    results.append({
                        "id": row["id"],
                        "post_id": row["post_id"],
                        "local_path": row["local_path"],
                        "post_date": row["post_date"],
                        "title": row["title"],
                        "author": row["author"],
                        "age_days": age_days,
                        "image_url": row["image_url"]
                    })
    return results
def mark_image_published(image_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        cursor.execute("UPDATE images SET is_published = 1, published_at = ? WHERE id = ?", (now_str, image_id))
        conn.commit()
def get_expired_images() -> List[Dict]:
    today = date.today()
    expired = []
    with get_connection() as conn:
        cursor = conn.cursor()
        if config.PERSISTENT_INVENTORY_MODE:
            cursor.execute("SELECT id, local_path, status, sold_at FROM images WHERE status = 'sold_out'")
            rows = cursor.fetchall()
            for row in rows:
                sold_at_str = row["sold_at"]
                if not sold_at_str:
                    continue
                try:
                    s_date = datetime.fromisoformat(sold_at_str).date()
                    if (today - s_date).days >= config.SOLD_RETENTION_DAYS:
                        expired.append({
                            "id": row["id"],
                            "local_path": row["local_path"],
                            "reason": f"Sold out for {(today - s_date).days} days"
                        })
                except Exception:
                    pass
        else:
            cursor.execute("SELECT id, local_path, post_date FROM images")
            rows = cursor.fetchall()
            for row in rows:
                try:
                    p_date = datetime.strptime(row["post_date"], "%Y-%m-%d").date()
                    age_days = (today - p_date).days
                    if age_days > config.MAX_DAYS_OLD:
                        expired.append({
                            "id": row["id"],
                            "local_path": row["local_path"],
                            "reason": f"Post age {age_days} days > {config.MAX_DAYS_OLD} days"
                        })
                except Exception:
                    pass
    return expired
def delete_image_record(image_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
        conn.commit()
def save_lead(group_url: str, post_url: str, content_snippet: str, matched_book_id: int, matched_book_title: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        try:
            cursor.execute("""
                INSERT INTO matched_leads (
                    group_url, post_url, content_snippet, 
                    matched_book_id, matched_book_title, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, 'pending', ?)
            """, (group_url, post_url, content_snippet, matched_book_id, matched_book_title, now_str))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
def get_leads(status: str = "pending") -> List[Dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        if status == "all":
            cursor.execute("SELECT * FROM matched_leads ORDER BY id DESC")
        else:
            cursor.execute("SELECT * FROM matched_leads WHERE status = ? ORDER BY id DESC", (status,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
def mark_lead_done(lead_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE matched_leads SET status = 'contacted' WHERE id = ?", (lead_id,))
        conn.commit()
def get_stats() -> Dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM images")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM images WHERE status = 'available'")
        available = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM images WHERE status = 'sold_out'")
        sold = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM images WHERE is_published = 1")
        published = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM posts")
        total_posts = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM matched_leads WHERE status = 'pending'")
        pending_leads = cursor.fetchone()[0]
    eligible = len(get_unposted_eligible_images(config.MIN_DAYS_OLD, config.MAX_DAYS_OLD))
    return {
        "total_posts": total_posts,
        "total_images": total,
        "available_in_stock": available,
        "sold_out": sold,
        "published_images": published,
        "eligible_ready_to_post": eligible,
        "pending_leads": pending_leads
    }
init_db()