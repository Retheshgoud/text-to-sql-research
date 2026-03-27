"""
Downloads the Chinook SQLite database into data/chinook.db
Run once: python scripts/download_chinook.py
"""
import urllib.request
import os

URL = "https://github.com/lerocha/chinook-database/raw/master/ChinookDatabase/DataSources/Chinook_Sqlite.sqlite"
DEST = "data/chinook.db"

os.makedirs("data", exist_ok=True)

print("Downloading Chinook database...")
urllib.request.urlretrieve(URL, DEST)
print(f"Saved to {DEST}")
