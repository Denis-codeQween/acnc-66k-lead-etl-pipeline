import pandas as pd
import urllib.parse
import re
import time
import random
import os
from playwright.sync_api import sync_playwright

INPUT_EXCEL = "extracted_charities_info.xlsx"
OUTPUT_EXCEL = "all_charities_emails.xlsx"
NOT_FOUND_EXCEL = "charities_not_found.xlsx"

# Smart loading: if results file already exists, resume from it!
if os.path.exists(OUTPUT_EXCEL):
    print(f"1. Loading previously saved progress from {OUTPUT_EXCEL}...")
    df = pd.read_excel(OUTPUT_EXCEL)
elif os.path.exists(INPUT_EXCEL):
    print(f"1. Loading source file {INPUT_EXCEL}...")
    df = pd.read_excel(INPUT_EXCEL)
else:
    print(f"[ERROR] No data files found in the script directory!")
    exit()

total_records = len(df)
print(f"Total records in database: {total_records}")

# Manual mapping dictionary for known exceptions
MANUAL_MAP = {
    "SHINE PROJECT AUSTRALIA": "alison@marktrovato.com.au",
    "The Dale Family Foundation": "chrisdale@iinet.net.au",
    "The SJD Homes Foundation": "andrewe@primefinancial.com.au",
}

# Prepare the Email column if it doesn't exist yet
if 'Email' not in df.columns:
    df['Email'] = None

not_found_indices = []
# Restore "Not found" indices from current dataframe if they are already present
for idx, row_val in df.iterrows():
    val = row_val.get('Email')
    if pd.notna(val) and str(val).strip() == "Not found":
        not_found_indices.append(idx)

print("2. Starting email extraction pipeline with auto-save every 50 records...")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    page = context.new_page()

    for index, row in df.iterrows():
        name = str(row.get('Charity_Legal_Name', '')).strip()
        abn = str(row.get('ABN', '')).strip()
        
        # Skip immediately if email is already filled or marked as "Not found"
        current_email = row.get('Email')
        if pd.notna(current_email) and str(current_email).strip() and str(current_email) != "nan":
            continue

        found_email = None
        
        # 1. Manual mapping lookup
        for key, mapped_email in MANUAL_MAP.items():
            if key.lower() in name.lower():
                found_email = mapped_email
                break
                
        # 2. Google Search extraction fallback
        if not found_email:
            try:
                query = f"acnc ABN: {abn} | {name} email"
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                page.goto(search_url, timeout=10000)
                
                if "sorry/index" in page.url or "recaptcha" in page.content().lower():
                    print(f"\n[WARNING] Google reCAPTCHA triggered at record {index+1}. Please solve it in the browser...")
                    time.sleep(40)
                
                page_text = page.inner_text('body')
                found_emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', page_text)
                
                ignore_list = ['google.com', 'schema.org', 'w3.org', 'example.com', 'png', 'jpg', 'acnc.gov.au', 'finance.gov.au']
                valid_emails = [e.strip() for e in found_emails if not any(bad in e.lower() for bad in ignore_list) and len(e.strip()) > 5]
                
                if valid_emails:
                    found_email = valid_emails[0]
            except Exception:
                pass

        if found_email:
            df.at[index, 'Email'] = found_email
            status_str = f"Email: {found_email}"
        else:
            df.at[index, 'Email'] = "Not found"
            status_str = "Not found"
            if index not in not_found_indices:
                not_found_indices.append(index)

        if (index + 1) % 10 == 0 or index == 0:
            print(f"[{index+1}/{total_records}] {name[:25]}... -> {status_str}")

        # Auto-save every 50 records
        if (index + 1) % 50 == 0:
            try:
                df.to_excel(OUTPUT_EXCEL, index=False)
                not_found_df = df.iloc[not_found_indices]
                not_found_df.to_excel(NOT_FOUND_EXCEL, index=False)
                print(f"--- [Auto-save] Files updated at record {index + 1} ---")
            except Exception as e:
                print(f"--- [Auto-save Warning] Please close the file in Excel: {e} ---")
        
        # Randomized cyclical delay to mimic human behavior (2 to 5 seconds)
        delay_cycle = [2.0, 3.0, 4.0, 5.0, 2.5, 3.5]
        sleep_time = delay_cycle[index % len(delay_cycle)] + random.uniform(0.1, 0.8)
        time.sleep(sleep_time)

    browser.close()

print("\n3. Performing final save of results...")
df.to_excel(OUTPUT_EXCEL, index=False)
not_found_df = df.iloc[not_found_indices]
not_found_df.to_excel(NOT_FOUND_EXCEL, index=False)
print("Done! All data successfully written to files.")
