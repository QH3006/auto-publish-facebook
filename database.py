import sqlite3
import os
import hashlib
from datetime import datetime, date, timedelta
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
                category TEXT DEFAULT '',
                price TEXT DEFAULT '',
                status TEXT DEFAULT 'available',
                sold_at TEXT,
                is_published INTEGER DEFAULT 0,
                published_at TEXT,
                created_at TEXT,
                FOREIGN KEY (post_id) REFERENCES posts(post_id)
            )
        """)
        cursor.execute("PRAGMA table_info(images)")
        cols = [c[1] for c in cursor.fetchall()]
        for col_name, col_def in [("category", "TEXT DEFAULT ''"), ("price", "TEXT DEFAULT ''"), ("is_single_book", "INTEGER DEFAULT 1"), ("is_reviewed", "INTEGER DEFAULT 1"), ("title", "TEXT DEFAULT ''"), ("author", "TEXT DEFAULT ''"), ("status", "TEXT DEFAULT 'available'"), ("sold_at", "TEXT"), ("last_attempted_at", "TEXT"), ("is_group_published", "INTEGER DEFAULT 0")]:
            if col_name not in cols:
                cursor.execute(f"ALTER TABLE images ADD COLUMN {col_name} {col_def}")
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
        cursor.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, created_at TEXT)")
        conn.commit()
    normalize_image_paths()
def normalize_image_paths():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, local_path FROM images WHERE local_path IS NOT NULL AND local_path != ''")
            for r in cursor.fetchall():
                fname = os.path.basename(r[1])
                new_p = str(config.IMAGES_DIR / fname)
                if r[1] != new_p and os.path.exists(new_p):
                    cursor.execute("UPDATE images SET local_path = ? WHERE id = ?", (new_p, r[0]))
            conn.commit()
    except Exception:
        pass
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
def is_image_hash_saved(image_hash: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM images WHERE image_hash = ?", (image_hash,))
        return cursor.fetchone() is not None
def is_duplicate_book(title: str, price: str) -> bool:
    if not title or not title.strip() or not price or not str(price).strip():
        return False
    with get_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM images WHERE LOWER(TRIM(title)) = ? AND price = ? AND status = 'available'", (title.strip().lower(), str(price).strip()))
        return c.fetchone() is not None
def is_post_saved(post_id: str) -> bool:
    with get_connection() as conn:
        return conn.execute("SELECT post_id FROM posts WHERE post_id = ?", (post_id,)).fetchone() is not None
def get_next_available_id() -> int:
    with get_connection() as conn:
        existing = {r[0] for r in conn.execute("SELECT id FROM images").fetchall()}
        c = 1
        while c in existing: c += 1
        return c
def save_image(post_id: str, image_url: str, local_path: str, image_hash: str, post_date: str, title: str = "", author: str = "", category: str = "", price: str = "", is_single_book: int = 1, is_reviewed: int = 0) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        next_id = get_next_available_id()
        try:
            cursor.execute("""
                INSERT INTO images (
                    id, post_id, image_url, local_path, image_hash, post_date, 
                    title, author, category, price, is_single_book, is_reviewed, status, is_published, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'available', 0, ?)
            """, (next_id, post_id, image_url, local_path, image_hash, post_date, title, author, category, price, is_single_book, is_reviewed, now_str))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
def add_book_manually(title: str, author: str = "", category: str = "", price: str = "", status: str = "available", local_path: str = "", is_reviewed: int = 1) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        today_str = date.today().isoformat()
        dummy_hash = hashlib.sha256(f"manual_{now_str}_{title}".encode()).hexdigest()
        next_id = get_next_available_id()
        cursor.execute("""
            INSERT INTO images (
                id, post_id, image_url, local_path, image_hash, post_date,
                title, author, category, price, is_single_book, is_reviewed, status, is_published, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 0, ?)
        """, (next_id, "manual_entry", "", local_path, dummy_hash, today_str, title, author, category, price, is_reviewed, status, now_str))
        conn.commit()
        return next_id
def update_book_details(book_id: int, title: str, author: str = "", price: str = "", is_single_book: int = 1, status: str = "available", is_reviewed: int = 1, category: str = ""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE images 
            SET title = ?, author = ?, category = ?, price = ?, is_single_book = ?, status = ?, is_reviewed = ?
            WHERE id = ?
        """, (title, author, category, price, is_single_book, status, is_reviewed, book_id))
        conn.commit()
def mark_book_reviewed(book_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE images SET is_reviewed = 1 WHERE id = ?", (book_id,))
        conn.commit()
def approve_all_books():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE images SET is_reviewed = 1 WHERE is_reviewed = 0")
        conn.commit()
def get_pending_review_books(limit: int = 50) -> List[Dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, post_id, local_path, title, author, category, price, status, is_single_book, is_reviewed, post_date 
            FROM images 
            WHERE is_reviewed = 0
            ORDER BY id DESC 
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]
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
    clean_id = cleaned_query.lstrip("#")
    kw_pattern = f"%{cleaned_query}%"
    with get_connection() as conn:
        cursor = conn.cursor()
        if clean_id.isdigit():
            cursor.execute("""
                SELECT i.id, i.post_id, i.local_path, i.title, i.author, i.category, i.price, i.status, 
                       i.post_date, p.post_text
                FROM images i
                LEFT JOIN posts p ON i.post_id = p.post_id
                WHERE i.status = 'available'
                  AND (
                      i.id = ?
                      OR LOWER(i.title) LIKE ?
                      OR LOWER(i.author) LIKE ?
                      OR LOWER(i.category) LIKE ?
                      OR LOWER(p.post_text) LIKE ?
                  )
                ORDER BY i.id DESC
            """, (int(clean_id), kw_pattern, kw_pattern, kw_pattern, kw_pattern))
        else:
            cursor.execute("""
                SELECT i.id, i.post_id, i.local_path, i.title, i.author, i.category, i.price, i.status, 
                       i.post_date, p.post_text
                FROM images i
                LEFT JOIN posts p ON i.post_id = p.post_id
                WHERE i.status = 'available'
                  AND (
                      CAST(i.id AS TEXT) LIKE ?
                      OR LOWER(i.title) LIKE ?
                      OR LOWER(i.author) LIKE ?
                      OR LOWER(i.category) LIKE ?
                      OR LOWER(p.post_text) LIKE ?
                  )
                ORDER BY i.id DESC
            """, (kw_pattern, kw_pattern, kw_pattern, kw_pattern, kw_pattern))
        rows = cursor.fetchall()
        if not rows:
            cursor.execute("""
                SELECT i.id, i.post_id, i.local_path, i.title, i.author, i.category, i.price, i.status, 
                       i.post_date, p.post_text
                FROM images i
                LEFT JOIN posts p ON i.post_id = p.post_id
                WHERE i.status = 'available'
            """)
            all_available = cursor.fetchall()
            matched_rows = []
            generic_skip = {"sách hay", "sách cũ", "sách mới", "sách", "truyện", "tiểu thuyết"}
            for item in all_available:
                title = (item["title"] or "").strip().lower()
                author = (item["author"] or "").strip().lower()
                if title in generic_skip:
                    continue
                if (title and len(title) >= 4 and title in cleaned_query) or (author and len(author) >= 4 and author in cleaned_query):
                    matched_rows.append(item)
            rows = matched_rows
        for row in rows:
            if not row["local_path"] or os.path.exists(row["local_path"]):
                results.append(dict(row))
    return results
def get_unposted_eligible_images(min_days: int = 7, max_days: int = 30) -> List[Dict]:
    today = date.today()
    results = []
    cutoff_20h = (datetime.now() - timedelta(hours=20)).isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, post_id, local_path, post_date, image_url, title, author, category, price, is_reviewed 
            FROM images 
            WHERE is_published = 0 AND status = 'available' AND (is_single_book = 1 OR is_single_book IS NULL)
              AND (last_attempted_at IS NULL OR last_attempted_at = '' OR last_attempted_at < ?)
              AND (image_hash IS NULL OR image_hash = '' OR image_hash NOT IN (SELECT image_hash FROM images WHERE is_published = 1 AND image_hash IS NOT NULL AND image_hash != ''))
              AND (title IS NULL OR TRIM(title) = '' OR LOWER(TRIM(title)) NOT IN (SELECT LOWER(TRIM(title)) FROM images WHERE is_published = 1 AND title IS NOT NULL AND TRIM(title) != ''))
            ORDER BY is_reviewed DESC, RANDOM()
        """, (cutoff_20h,))
        rows = cursor.fetchall()
        for row in rows:
            post_date_str = row["post_date"]
            try:
                p_date = datetime.strptime(post_date_str, "%Y-%m-%d").date()
                age_days = (today - p_date).days
            except Exception:
                continue
            if min_days <= age_days <= max_days:
                lp = row["local_path"]
                if lp and not os.path.exists(lp):
                    cand = str(config.IMAGES_DIR / os.path.basename(lp))
                    if os.path.exists(cand): lp = cand
                if not lp or os.path.exists(lp):
                    results.append({
                        "id": row["id"], "post_id": row["post_id"], "local_path": lp,
                        "post_date": row["post_date"], "title": row["title"], "author": row["author"],
                        "category": row["category"], "price": row["price"], "age_days": age_days, "image_url": row["image_url"]
                    })
    return results
def mark_image_attempted(image_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        cursor.execute("SELECT image_hash, title FROM images WHERE id = ?", (image_id,))
        row = cursor.fetchone()
        cursor.execute("UPDATE images SET last_attempted_at = ? WHERE id = ?", (now_str, image_id))
        if row and (row["image_hash"] or (row["title"] and row["title"].strip())):
            cursor.execute(
                "UPDATE images SET last_attempted_at = ? WHERE (image_hash IS NOT NULL AND image_hash != '' AND image_hash = ?) OR (title IS NOT NULL AND TRIM(title) != '' AND LOWER(TRIM(title)) = LOWER(TRIM(?)))",
                (now_str, row["image_hash"] or "", row["title"] or "")
            )
        conn.commit()
def mark_image_group_published(image_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE images SET is_group_published = 1 WHERE id = ?", (image_id,))
        conn.commit()
def mark_image_published(image_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        now_str = datetime.now().isoformat()
        cursor.execute("SELECT image_hash, title FROM images WHERE id = ?", (image_id,))
        row = cursor.fetchone()
        cursor.execute("UPDATE images SET is_published = 1, published_at = ? WHERE id = ?", (now_str, image_id))
        if row and (row["image_hash"] or (row["title"] and row["title"].strip())):
            cursor.execute(
                "UPDATE images SET is_published = 1, published_at = COALESCE(published_at, ?) WHERE is_published = 0 AND ((image_hash IS NOT NULL AND image_hash != '' AND image_hash = ?) OR (title IS NOT NULL AND TRIM(title) != '' AND LOWER(TRIM(title)) = LOWER(TRIM(?))))",
                (now_str, row["image_hash"] or "", row["title"] or "")
            )
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
def query_books(keyword: str = "", category: str = "", min_price: int = None, max_price: int = None, status: str = "", is_reviewed: int = None, sort_by: str = "id_desc", limit: int = 500) -> List[Dict]:
    conditions = []
    params = []
    if keyword:
        kw_raw = keyword.strip()
        clean_id = kw_raw.lstrip("#")
        kw = f"%{kw_raw.lower()}%"
        if clean_id.isdigit():
            conditions.append("(id = ? OR CAST(id AS TEXT) LIKE ? OR LOWER(title) LIKE ? OR LOWER(author) LIKE ?)")
            params.extend([int(clean_id), kw, kw, kw])
        else:
            conditions.append("(CAST(id AS TEXT) LIKE ? OR LOWER(title) LIKE ? OR LOWER(author) LIKE ?)")
            params.extend([kw, kw, kw])
    if category:
        conditions.append("LOWER(category) = ?")
        params.append(category.strip().lower())
    if min_price is not None:
        conditions.append("CAST(REPLACE(REPLACE(price, '.', ''), ',', '') AS INTEGER) >= ?")
        params.append(int(min_price))
    if max_price is not None:
        conditions.append("CAST(REPLACE(REPLACE(price, '.', ''), ',', '') AS INTEGER) <= ?")
        params.append(int(max_price))
    if status:
        conditions.append("status = ?")
        params.append(status.strip())
    if is_reviewed is not None:
        conditions.append("is_reviewed = ?")
        params.append(int(is_reviewed))
    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    order_clause = "ORDER BY id DESC"
    if sort_by == "id_asc":
        order_clause = "ORDER BY id ASC"
    elif sort_by == "price_asc":
        order_clause = "ORDER BY CAST(REPLACE(REPLACE(price, '.', ''), ',', '') AS INTEGER) ASC"
    elif sort_by == "price_desc":
        order_clause = "ORDER BY CAST(REPLACE(REPLACE(price, '.', ''), ',', '') AS INTEGER) DESC"
    elif sort_by == "title_asc":
        order_clause = "ORDER BY title COLLATE NOCASE ASC"
    query = f"SELECT id, post_id, local_path, title, author, category, price, status, is_published, is_single_book, is_reviewed, post_date, created_at FROM images {where_clause} {order_clause} LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        return [dict(r) for r in cursor.fetchall()]
def get_all_books(limit: int = 100) -> List[Dict]:
    return query_books(limit=limit)
def delete_image_record(image_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT local_path FROM images WHERE id = ?", (image_id,))
        row = cursor.fetchone()
        if not row:
            return False
        local_path = row[0]
        cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
        conn.commit()
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass
        return True
def save_lead(group_url: str, post_url: str, content_snippet: str, matched_book_id: int, matched_book_title: str) -> bool:
    with get_connection() as conn:
        try:
            conn.cursor().execute("INSERT INTO matched_leads (group_url, post_url, content_snippet, matched_book_id, matched_book_title, status, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?)", (group_url, post_url, content_snippet, matched_book_id, matched_book_title, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
def get_leads(status: str = "pending") -> List[Dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT l.*, i.price as book_price, i.category as book_category, i.local_path as book_image FROM matched_leads l LEFT JOIN images i ON l.matched_book_id = i.id"
        if status == "all":
            cursor.execute(query + " ORDER BY l.id DESC")
        else:
            cursor.execute(query + " WHERE l.status = ? ORDER BY l.id DESC", (status,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
def update_lead_status(lead_id: int, status: str) -> bool:
    with get_connection() as conn:
        conn.cursor().execute("UPDATE matched_leads SET status = ? WHERE id = ?", (status, lead_id))
        conn.commit()
        return True
def delete_lead(lead_id: int) -> bool:
    with get_connection() as conn:
        conn.cursor().execute("DELETE FROM matched_leads WHERE id = ?", (lead_id,))
        conn.commit()
        return True
def mark_lead_done(lead_id: int):
    return update_lead_status(lead_id, "contacted")
def get_stats() -> Dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        total = cursor.execute("SELECT COUNT(*) FROM images").fetchone()[0]
        available = cursor.execute("SELECT COUNT(*) FROM images WHERE status = 'available'").fetchone()[0]
        sold = cursor.execute("SELECT COUNT(*) FROM images WHERE status = 'sold_out'").fetchone()[0]
        published = cursor.execute("SELECT COUNT(*) FROM images WHERE is_published = 1").fetchone()[0]
        total_posts = cursor.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
        pending_leads = cursor.execute("SELECT COUNT(*) FROM matched_leads WHERE status = 'pending'").fetchone()[0]
    eligible = len(get_unposted_eligible_images(config.MIN_DAYS_OLD, config.MAX_DAYS_OLD))
    return {
        "total_posts": total_posts, "total_images": total, "available_in_stock": available,
        "sold_out": sold, "published_images": published, "eligible_ready_to_post": eligible, "pending_leads": pending_leads
    }
DEFAULT_CATEGORIES = [
    "Văn học Việt Nam", "Văn học phương Tây", "Văn học Trung Quốc", "Văn học Nhật Bản",
    "Kỹ năng sống / Tâm lý", "Kinh tế / Kinh doanh", "Lịch sử / Văn hóa", "Manga / Light Novel",
    "Thiếu nhi", "Trinh thám / Kinh dị", "Tản văn", "Ngôn tình", "Âm nhạc / Nghệ thuật", "Ngoại văn"
]
def get_all_categories() -> List[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY name ASC")
        rows = [r[0] for r in cursor.fetchall()]
        if not rows:
            for cat in DEFAULT_CATEGORIES:
                cursor.execute("INSERT OR IGNORE INTO categories (name, created_at) VALUES (?, ?)", (cat, datetime.now().isoformat()))
            conn.commit()
            return sorted(DEFAULT_CATEGORIES)
        return rows
def add_category(name: str) -> bool:
    clean = name.strip()
    if not clean:
        return False
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO categories (name, created_at) VALUES (?, ?)", (clean, datetime.now().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
def delete_category(name: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE name = ?", (name.strip(),))
        conn.commit()
        return True
init_db()