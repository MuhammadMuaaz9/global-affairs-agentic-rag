import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import calendar
import os
import time

API_KEY = "b1f0989fc71dd0e8333d3e7d23da4fb4"

# Step 1: Get previous month/year
today = datetime.now()
first_day_this_month = today.replace(day=1)
last_month_date = first_day_this_month - timedelta(days=1)
year = last_month_date.year
month = last_month_date.month

# Step 2: Regex for date in format YYYY-MM-DD
date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")

# Step 3: Get number of days in that month
days_in_month = calendar.monthrange(year, month)[1]

# Step 4: Output file (overwrite)
with open("urls.txt", "w", encoding="utf-8") as f:
    pass  # Clear file

# Step 5: Loop days & pages
for day in range(1, days_in_month + 1):
    for page in range(1, 21):  # 1 → 20
        sitemap_url = f"https://www.reuters.com/sitemap/{year}-{month:02d}/{day:02d}/{page}/"
        print(f"Fetching: {sitemap_url}")

        payload = {"api_key": API_KEY, "url": sitemap_url}
        try:
            resp = requests.get("https://api.scraperapi.com/", params=payload, timeout=30)
            if resp.status_code != 200:
                print(f"Skipping {sitemap_url} (status {resp.status_code})")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            links = [a["href"] for a in soup.find_all("a", href=True)]

            filtered_links = [
                "https://www.reuters.com" + link if link.startswith("/") else link
                for link in links
                if "/world/" in link and date_pattern.search(link)
            ]

            if filtered_links:
                with open("urls.txt", "a", encoding="utf-8") as f:
                    for link in filtered_links:
                        f.write(link + "\n")

                print(f"Found {len(filtered_links)} world news links on {sitemap_url}")

        except Exception as e:
            print(f"Error fetching {sitemap_url}: {e}")

print("Completed! All links saved to urls.txt")

# --- Remove duplicate URLs from file ---
URLS_FILE = "urls.txt"
if os.path.exists(URLS_FILE):
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        unique_urls = sorted(set(line.strip() for line in f if line.strip()))

    with open(URLS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(unique_urls))

    print(f"🧹 Removed duplicates — {len(unique_urls)} unique URLs remain in {URLS_FILE}")
