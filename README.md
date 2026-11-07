# 24/7 AUTO FACEBOOK BOOK POSTER & GROUP LEAD FINDER
Automated Facebook page crawler, book inventory catalog, daily publisher, and Group Lead Finder.
- Daily Auto-Poster: Posts 3 times daily (06:00, 11:00, 19:00) with 1 image and 3-5 line AI-generated book intro captions.
- Persistent Book Inventory: Retains books permanently in SQLite until marked as sold (`sold_out`).
- Group Lead Scanner: Scans target Facebook Groups for buyer inquiries ("tìm mua", "cần tìm", "ai có cuốn"...), matches with your inventory, and saves clickable leads so you can manually review and comment safely.
- Group Auto-Poster: Automatically posts exactly 1 book post per day to a target Facebook group.
- Persistent Browser Profile: Log in once with `python main.py --login-fb` and session data is remembered permanently in `storage/browser_profile/` without needing to export cookies repeatedly.
- Multi-AI Provider: Supports Google Gemini, OpenAI-compatible (DeepSeek / Groq), or offline Local Ollama.
---
## 1. Project Structure
```text
d:\auto publish facebook\
├── config.py             # Configuration (URLs, Schedule, API Keys, Groups, Keywords)
├── main.py               # Master 24/7 runner and CLI commands
├── login_helper.py       # One-time Facebook login helper with persistent profile
├── group_poster.py       # Automated Facebook Group auto-poster (1 post/day)
├── telegram_bot.py       # Ultra-lightweight Telegram assistant (<15MB RAM) for mobile lookup
├── group_scanner.py      # Automated Facebook Groups buyer lead finder
├── scanner.py            # Playwright crawler that extracts books into inventory
├── ai_engine.py          # Multi-provider AI engine (Gemini, DeepSeek/OpenAI, Local Ollama)
├── database.py           # SQLite database with persistent inventory & matched leads
├── text_utils.py         # Unicode font normalizer & Blacklist filter
├── cleaner.py            # Cleans only sold-out books after retention period
├── fb_poster.py          # Background Playwright browser publisher for Facebook Fanpage
├── requirements.txt      # Python dependencies
├── CHANGELOG.md          # Version history and upgrade notes
├── run_247.bat           # 1-click Windows runner
└── storage/              # Images, database file, logs, and browser profile
```
---
## 2. Quick Setup
1. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   playwright install chromium
   ```
2. Log in to Facebook once (saves session permanently):
   ```powershell
   python main.py --login-fb
   ```
3. Configure `config.py` with your Page URL, API keys, and target group URLs.
---
## 3. Useful Commands
* View inventory status and configuration:
  `python main.py --status`
* Scan Facebook groups immediately for customer inquiries:
  `python main.py --scan-leads`
* View all detected customer leads (with clickable link & matched book):
  `python main.py --leads`
* Mark a customer lead as contacted/done:
  `python main.py --done-lead 1`
* Search available books in stock:
  `python main.py --search "Nhà Giả Kim"`
* Test posting 1 book to Fanpage immediately:
  `python main.py --post-now`
* Test posting 1 book to Facebook Group immediately:
  `python main.py --post-group-now`
* Mark a book as SOLD OUT:
  `python main.py --sold 5`
* Start 24/7 background scheduler:
  `python main.py` (or double-click `run_247.bat`)
