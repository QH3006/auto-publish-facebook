# CHANGELOG
All notable changes to the 24/7 Auto Facebook Book Poster project are documented here.
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

