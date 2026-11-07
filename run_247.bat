@echo off
title Auto FB Poster & Headless Server 24/7
echo ========================================================
echo   24/7 AUTO BOOK POSTER, LEAD SCANNER & WEB ADMIN
echo   * Fanpage Posting: 06:00 - 11:00 - 19:00 (3 posts/day)
echo   * Group Posting:   09:30 (1 post/day)
echo   * Telegram Bot:    Active in background
echo   * Web Admin (LAN): http://localhost:8080
echo ========================================================
cd /d "d:\auto publish facebook"
python main.py
pause
