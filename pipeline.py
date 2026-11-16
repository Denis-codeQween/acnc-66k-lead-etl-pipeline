import asyncio
import json
import os
import time
from curl_cffi.requests import AsyncSession
import pandas as pd

# Files for saving data and progress
OUTPUT_JSONL = "acnc_results.jsonl"
PROGRESS_FILE = "progress.json"
OUTPUT_EXCEL = "acnc_full_database.xlsx"

# Scraping settings
MAX_CONCURRENT_REQUESTS = 5  # Concurrent threads for downloading profiles
CHECKPOINT_INTERVAL = 100    # Save checkpoint every 100 processed companies

async def load_progress():
    """Load the set of already processed UUIDs from the progress file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_progress(completed_set):
    """Save current progress to disk."""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(completed_set), f)

def save_result_jsonl(data: dict):
    """Instantly append a single record to JSON Lines."""
    with open(OUTPUT_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

async def fetch_all_charity_uuids():
    """Stage 1: Collect all UUIDs with periodic session recreation to protect against HTTP/2 stream reset."""
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.acnc.gov.au/charity/search",
        "X-Requested-With": "XMLHttpRequest"
    }
    url = "https://www.acnc.gov.au/api/dynamics/search/charity"
    working_params = {"page": 0, "query": "the"}
    
    all_uuids = []
    page = 0
    
    print("[*] Starting mass collection of organization UUIDs with stream reset protection...", flush=True)
    
    while True:
        # Recreate session every 200 pages to bypass Cloudflare HTTP/2 multiplexing limits
        async with AsyncSession(impersonate="chrome124") as session:
            try:
                await session.get("https://www.acnc.gov.au/charity/search", timeout=15)
            except Exception:
                pass
            
            for _ in range(200):
                current_params = working_params.copy()
                current_params["page"] = page
                
                print(f"[*] Fetching list: page (index) {page}...", flush=True)
                success = False
                results = []
                
                for attempt in range(3):
                    try:
                        response = await session.get(url, params=current_params, headers=headers, timeout=20)
                        if response.status_code == 200:
                            data = response.json()
                            results = data.get("results", [])
                            success = True
                            break
                        elif response.status_code in [403, 429, 502, 503]:
                            print(f"[!] Rate limit (status code {response.status_code}), pausing...", flush=True)
                            await asyncio.sleep(5 * (attempt + 1))
                        else:
                            await asyncio.sleep(2)
                    except Exception as e:
                        print(f"[-] Network error on page {page} (attempt {attempt+1}/3): {e}", flush=True)
                        await asyncio.sleep(2 * (attempt + 1))
                        
                if not success:
                    print(f"[-] Failure on page {page}, reconnecting session...", flush=True)
                    break  
                    
                if not results:
                    print(f"[*] UUID collection complete. No more data on page {page}.", flush=True)
                    return all_uuids
                    
                for item in results:
                    charity_id = item.get("uuid") or item.get("id")
                    if charity_id:
                        all_uuids.append(charity_id)
                        
                print(f"    • UUIDs collected on page: {len(results)}. Total accumulated: {len(all_uuids)}", flush=True)
                page += 1
                await asyncio.sleep(0.3)

async def fetch_charity_details(session: AsyncSession, uuid: str, semaphore: asyncio.Semaphore):
    """Stage 2: Directly fetch the structured JSON company profile via API."""
    async with semaphore:
        ts = 60000 * int(time.time() * 1000 // 60000)
        api_url = f"https://www.acnc.gov.au/api/dynamics/entity/{uuid}?ts={ts}"
        
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Referer": f"https://www.acnc.gov.au/charity/charities/{uuid}/profile"
        }
        
        for attempt in range(3):
            try:
                response = await session.get(api_url, headers=headers, impersonate="chrome124", timeout=20)
                
                if response.status_code == 200:
                    res_data = response.json()
                    entity_data = res_data.get("data", {})
                    
                    org_data = {
                        "uuid": uuid,
                        "url": f"https://www.acnc.gov.au/charity/charities/{uuid}/profile",
                        **(entity_data if isinstance(entity_data, dict) else {"raw_data": entity_data}),
                        "status": "success"
                    }
                    return org_data, True
                    
                elif response.status_code in [403, 429]:
                    await asyncio.sleep(10)
                else:
                    return {"uuid": uuid, "status": f"http_error_{response.status_code}"}, False
                    
            except Exception:
                if attempt == 2:
                    return {"uuid": uuid, "status": "failed_retries"}, False
                await asyncio.sleep(2)
                
        return {"uuid": uuid, "status": "failed_retries"}, False

def convert_to_excel():
    """Convert collected JSONL into the final normalized Excel file."""
    print("\n[*] Converting all data to Excel (.xlsx)...", flush=True)
    data_list = []
    
    if os.path.exists(OUTPUT_JSONL):
        with open(OUTPUT_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data_list.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
                    
        if data_list:
            df = pd.json_normalize(data_list)
            df.to_excel(OUTPUT_EXCEL, index=False, engine="openpyxl")
            print(f"[+] Successfully saved to file: {OUTPUT_EXCEL} (Total records: {len(df)})", flush=True)
        else:
            print("[-] Results are empty, nothing to convert.")
    else:
        print("[-] Results file not found.")

async def main():
    print("[*] Starting ACNC data collection pipeline via internal API...", flush=True)
    
    uuids = await fetch_all_charity_uuids()
    
    if not uuids:
        print("[-] Failed to retrieve UUID list from API.")
        return
        
    # Deduplicate UUID list just in case
    uuids = list(dict.fromkeys(uuids))
    print(f"[+] Total unique organization UUIDs retrieved: {len(uuids)}", flush=True)
    
    completed_uuids = await load_progress()
    remaining_uuids = [u for u in uuids if u not in completed_uuids]
    
    print(f"[+] Already downloaded previously: {len(completed_uuids)}. Remaining to download: {len(remaining_uuids)}", flush=True)
    
    if not remaining_uuids:
        print("[*] All data is already collected!")
        convert_to_excel()
        return

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    # Stage 2: Reopen session for each batch (guaranteeing protection against CURLE_HTTP2_STREAM)
    for i in range(0, len(remaining_uuids), CHECKPOINT_INTERVAL):
        batch = remaining_uuids[i:i + CHECKPOINT_INTERVAL]
        print(f"\n[---] Processing batch: items {i+1} to {i+len(batch)} of {len(remaining_uuids)}", flush=True)
        
        async with AsyncSession(impersonate="chrome124") as session:
            tasks = [fetch_charity_details(session, uuid, semaphore) for uuid in batch]
            results = await asyncio.gather(*tasks)
        
        for uuid, (org_data, success) in zip(batch, results):
            if success:
                save_result_jsonl(org_data)
                completed_uuids.add(uuid)
        
        save_progress(completed_uuids)
        print(f"[checkpoint] Progress saved. Successfully downloaded: {len(completed_uuids)}/{len(uuids)}", flush=True)
        await asyncio.sleep(0.5)
        
    print("\n[+] Data collection fully completed!")
    convert_to_excel()

if __name__ == "__main__":
    asyncio.run(main())