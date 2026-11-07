# CHANGELOG
All notable changes to the 24/7 Auto Facebook Book Poster project are documented here.
## [v1.8.0] - 2026-11-07
### Added
- Database Web Inventory Dashboard (`web_admin.py`): Built-in visual book inventory table on port 8080 (`http://localhost:8080`). Displays live book cover thumbnails, title, author, price, availability status, real-time live search filter, and instant one-click `[Đánh dấu ĐÃ BÁN]` button.
- Book Price Tracking (`database.py`): Added `price` column to `images` table to store price extracted from photo captions or labels.
- Single vs Multi-Book Detection (`ai_engine.py`): AI Gemini inspects photos to distinguish between single-book photos (`is_single_book: true`) and book collections/piles. Database rotator strictly prioritizes single-book photos for daily posts.
- Bookstore Tone & Style Mimicry (`storage/style_samples.txt`): AI reads real bookstore sample posts to match exact line breaks, warm tone, vocabulary, and hashtag habits.
## [v1.7.0] - 2026-11-07
### Changed
- Removed all Facebook Graph API and Access Token dependencies: Eliminated Meta Developer App review requirements, expiring access tokens, and Business Manager asset linking deadlocks.
- Upgraded Fanpage Publisher (`fb_poster.py`): Now operates 100% via Playwright browser automation using the persistent profile/cookies of any Facebook account with Admin/Editor access to the Page.
- Automatic Profile Switching: Automatically detects and handles Facebook New Pages Experience "Chuyển ngay" (Switch Profile) prompt before publishing.
- Dual Session Persistence (`login_helper.py`): Saves authentication state to both `storage/browser_profile/` and `cookies.json`.
- Automatic Error Diagnostics: Automatically captures debug screenshot to `storage/fb_post_error.png` if any UI step encounters an issue.
## [v1.6.0] - 2026-11-07
### Added
- Headless Server Remote Management (`web_admin.py`): Built-in web dashboard (port 8080) for headless operation.
- System Resource Monitoring: Real-time tracking of CPU (%), RAM (GB/used/percent), Disk storage, and uptime. Accessible from anywhere or via Telegram `/system` command.
- LAN Security Enforcement: Changes to system configuration (adding/removing monitored groups, changing AI providers, updating API keys) are strictly allowed ONLY from within the local network (LAN / private IP). Remote requests outside LAN are restricted to view-only mode.
- Persistent Settings Manager (`settings_manager.py`): Saves overrides to `storage/settings.json` without modifying source code files directly.
## [v1.5.0] - 2026-11-07
### Added
- Facebook Group Auto-Poster (`group_poster.py`): Posts exactly 1 book post per day to a target Facebook group using the persistent browser profile, complete with image attachment and AI-generated caption.
- Deep Comment Scanning: Enhanced `group_scanner.py` to automatically click and expand hidden comments ("Xem thêm bình luận") to capture buyer requests in comment threads.
- CLI flag `--post-group-now`: Test posting 1 book to target group immediately.
## [v1.4.0] - 2026-11-07
### Added
- Telegram Bot Assistant (`telegram_bot.py`): Zero-bloat, pure requests-based bot consuming < 15MB RAM. Allows bookseller to look up inventory by texting book names, receive photo of cover with status, and tap one-click inline buttons to mark books as SOLD OUT from mobile devices anywhere (4G/Wi-Fi).
- Lead Alert Integration: Automatically dispatches new Facebook group buyer inquiry notifications with direct post links to Telegram.
- CLI flag `--bot`: Run standalone Telegram Bot listener.
## [v1.3.1] - 2026-11-07
### Added
- Multi-Browser Support: Added `BROWSER_CHANNEL` in `config.py`. You can now use Windows built-in Microsoft Edge (`channel="msedge"`), system Chrome (`channel="chrome"`), or Playwright bundled Chromium engine (`None`), meaning you never need to install Google Chrome.
## [v1.3.0] - 2026-11-07
### Added
- Persistent Browser Profile: Added `login_helper.py` and CLI flag `--login-fb` allowing one-time manual Facebook login in visible browser. Profile is stored in `storage/browser_profile/` so subsequent background scans never expire or require manual cookie exporting.
- Lead Scanner CLI commands: Added `--scan-leads`, `--leads`, and `--done-lead` to manage group buyer leads.
- Requirements file: Created `requirements.txt` with tested package versions.
### Changed
- Scanner modules (`scanner.py`, `group_scanner.py`) upgraded to use `launch_persistent_context` with stored browser profile.
- Codebase style refactoring: Eliminated unnecessary blank lines across all modules to optimize vertical screen space.
- Character standardization: Removed non-standard symbols and emojis from logs and console outputs, standardizing on ASCII tags (`[INFO]`, `[OK]`, `*`).
## [v1.2.0] - 2026-11-07
### Added
- Group Lead Scanner (`group_scanner.py`): Scans Facebook groups for buyer intent keywords ("tìm mua", "cần tìm", "ai có cuốn"...), matches against available inventory, and captures post URLs.
- Table `matched_leads`: Database schema for storing buyer leads with status tracking (`pending`, `contacted`).
## [v1.1.0] - 2026-11-07
### Added
- Persistent Book Inventory: Books remain in database indefinitely under `status='available'` until explicitly marked as sold via `--sold <ID>`.
- Multi-Provider AI Engine (`ai_engine.py`): Support for Google Gemini, OpenAI-compatible APIs (DeepSeek, Groq), and offline local Ollama.
- Inventory Search CLI: Added `--search` command for fast stock verification.
### Changed
- Scope restriction: AI generation strictly restricted to daily book introduction posts. Lead replies and customer communications remain 100% human-managed.
## [v1.0.0] - 2026-11-05
### Added
- Initial project release: 24/7 automated scheduler for 3 daily posts (06:00, 11:00, 19:00).
- Post filter: Mathematical Unicode bold normalizer (NFKC), 7-30 day age window, and blacklist exclusion keywords ("Truyện tranh", "Sách tham khảo", etc.).
- Facebook Graph API publisher (`fb_poster.py`) with dry-run simulation mode.
- Playwright page crawler (`scanner.py`) and SQLite storage (`database.py`).

