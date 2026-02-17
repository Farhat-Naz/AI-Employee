# Gmail Watcher Setup Guide

## Step 1 — Install libraries (run once)
```
pip install -r requirements.txt
```

## Step 2 — Get credentials.json
1. Open this link in your browser:
   https://console.cloud.google.com/apis/credentials
2. Sign in with your Google account
3. Click "Create Project" → give any name → Create
4. Go to "APIs & Services" → "Library"
5. Search "Gmail API" → Click it → Click "Enable"
6. Go back to "APIs & Services" → "Credentials"
7. Click "Create Credentials" → "OAuth 2.0 Client ID"
8. Application type = "Desktop app" → Name = anything → Click "Create"
9. Click the download button ⬇ next to your new entry
10. Rename the downloaded file to: credentials.json
11. Move credentials.json to this folder:
    D:\quarterr 4\personalAI\Silver\Watchers\

## Step 3 — Run the watcher
```
python gmail_watcher.py
```
Browser will open once for login → click Allow → done.

## Step 4 — It runs automatically after that
token.json will be saved here. No browser needed again.
