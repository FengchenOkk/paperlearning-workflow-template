@echo off
cd /d "%~dp0"
node features\F-003-zotero-bridge\scripts\zotero-sync.mjs --sync
pause
