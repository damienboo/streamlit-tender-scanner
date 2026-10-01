import time
import os
import logging
import re
import warnings
import asyncio
import sys
from plyer import notification
import database

# --- WINDOWS PLAYWRIGHT FIX ---
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
# ------------------------------

os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)
logging.getLogger("streamlit").setLevel(logging.ERROR)

from scrapers.eperolehan import scrape_live_eperolehan
from scrapers.selangor import scrape_selangor
from scrapers.johor import scrape_johor
from scrapers.kedah import scrape_kedah
from scrapers.melaka import scrape_melaka
from scrapers.pahang import scrape_pahang
from scrapers.kelantan import scrape_kelantan
from scrapers.negerisembilan import scrape_negeri_sembilan
from scrapers.penang import scrape_penang
from scrapers.perak import scrape_perak
from scrapers.perlis import scrape_perlis
from scrapers.terengganu import scrape_terengganu
from scrapers.sabah import scrape_sabah
from scrapers.sarawak import scrape_sarawak

MONITOR_KEYWORDS = "ict, tmk, rangkaian, network, server, storage, security, penyelenggaraan, maintenance" 

NOTIFICATION_KEYWORDS = [
    "network", "rangkaian", 
    "server", "pelayan",
    "storage", "storan", 
    "security", "keselamatan", 
    "ict", "tmk"
]

def filter_exact_matches(tenders, keyword_string):
    if not tenders: return []
    search_terms = [k.strip().lower() for k in keyword_string.split(",")]
    valid_tenders = []
    for tender in tenders:
        title = tender.get('Title', tender.get('Tender Title', '')).lower()
        is_valid = False
        for term in search_terms:
            pattern = rf"(^|[^a-z0-9]){re.escape(term)}([^a-z0-9]|$)"
            if re.search(pattern, title):
                is_valid = True
                break
        if is_valid:
            valid_tenders.append(tender)
    return valid_tenders

def send_windows_push_notification(title, agency):
    try:
        notification.notify(
            title="🚨 H3C Tender Drop!",
            message=f"🏛 {agency}\n📄 {title}",
            app_name="MY-Tender Tracker",
            timeout=10 
        )
    except Exception as e:
        print(f"Notification failed: {e}")

def run_monitor():
    print("🚀 Starting MY-Tender Background Monitor (Windows Edition)...")
    print(f"Searching websites for: {MONITOR_KEYWORDS}")
    print(f"Alerting ONLY for exact H3C Keywords: {', '.join(NOTIFICATION_KEYWORDS)}")
    
    while True:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Waking up to scan for drops...")
        
        live_results = []
        
        try:
            print("Scanning Federal (ePerolehan)...")
            fed_data = scrape_live_eperolehan(MONITOR_KEYWORDS)
            if fed_data: live_results.extend(fed_data)

            print("🚀 Launching State Scrapers (Sequential Mode for Stability)...")
            state_scrapers = [
                ("Selangor", scrape_selangor), ("Johor", scrape_johor), 
                ("Kedah", scrape_kedah), ("Melaka", scrape_melaka),
                ("Pahang", scrape_pahang), ("Kelantan", scrape_kelantan), 
                ("Negeri Sembilan", scrape_negeri_sembilan), ("Penang", scrape_penang), 
                ("Perak", scrape_perak), ("Perlis", scrape_perlis), 
                ("Terengganu", scrape_terengganu), ("Sabah", scrape_sabah), 
                ("Sarawak", scrape_sarawak)
            ]
            
            for state_name, scraper in state_scrapers:
                print(f"  -> Scanning {state_name}...")
                try:
                    data = scraper(MONITOR_KEYWORDS)
                    if data: live_results.extend(data)
                except Exception as e:
                    print(f"     [!] Skipped {state_name} due to error: {e}")
                    
        except Exception as e:
            print(f"Scan interrupted: {e}")

        # Filter the massive list down to exact matches
        live_results = filter_exact_matches(live_results, MONITOR_KEYWORDS)

        new_tenders_found = False
        for tender in live_results:
            title = tender.get('Title', tender.get('Tender Title', 'Unknown'))
            agency = tender.get('Agency', 'Unknown Agency')
            
            is_new = database.insert_tender(tender)
            
            if is_new:
                new_tenders_found = True
                title_lower = title.lower()
                
                # Check if it matches our high-priority notification list
                match_found = any(re.search(rf'(^|[^a-z0-9]){re.escape(kw)}([^a-z0-9]|$)', title_lower) for kw in NOTIFICATION_KEYWORDS)
                
                if match_found:
                    send_windows_push_notification(title, agency)
                    print(f"🚨 H3C DROP DETECTED: {title}")
                    time.sleep(2) 
                else:
                    print(f"🤫 Saved silently to SQL: {title}")

        if new_tenders_found:
            database.export_to_excel_team_report()
            print("✅ SQL Database updated and Team Excel Report generated.")
        else:
            print("💤 No new data found.")

        print("⏳ Monitor going to sleep. Will check again in 1 hour...")
        time.sleep(3600)

if __name__ == "__main__":
    run_monitor()