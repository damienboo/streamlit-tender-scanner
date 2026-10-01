import pandas as pd
import time
import re

def scrape_live_eperolehan(keyword):
    from playwright.sync_api import sync_playwright
    import streamlit as st
    
    results = []
    search_terms = [k.strip().lower() for k in keyword.split(",")]
    
    try:
        progress_bar = st.progress(0, text="🚀 Launching Secure Browser for Federal ePerolehan...")
    except Exception:
        progress_bar = None 

    def update_status(percent, msg):
        """Updates both the UI progress bar and the background terminal."""
        if progress_bar:
            try:
                progress_bar.progress(percent, text=msg)
            except Exception:
                pass
        print(msg)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            url = "https://www.eperolehan.gov.my/quotation-tender-notice"
            update_status(10, f"🌍 Connecting to {url}...")
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            
            update_status(25, "⏳ Waiting 10 seconds for PrimeFaces table...")
            time.sleep(10)
            
            try:
                page.wait_for_selector("tbody.ui-datatable-data tr", timeout=30000)
            except:
                update_status(100, "❌ Table not found. Website might be loading slowly.")
                browser.close()
                if progress_bar: time.sleep(2); progress_bar.empty()
                return []

            page_num = 1
            while True:
                current_prog = min(25 + (page_num * 5), 95)
                
                rows = page.query_selector_all("tbody.ui-datatable-data tr")
                update_status(current_prog, f"📄 Scanning Page {page_num}... ({len(rows)} rows found)")
                
                for row in rows:
                    cols = row.query_selector_all("td")
                    if len(cols) > 2:
                        link_element = cols[0].query_selector("a")
                        if link_element:
                            title = link_element.inner_text().strip()
                            title_lower = title.lower()
                            
                            match_found = any(term in title_lower for term in search_terms)
                            
                            if match_found:
                                agency = cols[1].inner_text().strip() if len(cols) > 1 else "-"
                                close_date = cols[3].inner_text().strip() if len(cols) > 3 else "-"
                                
                                results.append({
                                    "Title": title,
                                    "Agency": agency,
                                    "Closing Date": close_date,
                                    "Source": "Federal (ePerolehan)",
                                    "Link": "https://www.eperolehan.gov.my/quotation-tender-notice"
                                })

                next_button = page.locator(".ui-paginator-next")
                classes = next_button.get_attribute("class")
                
                if "ui-state-disabled" in classes or not classes:
                    update_status(100, f"✅ Reached end of list at Page {page_num}.")
                    break
                
                # --- NEW: 25-Page Speed Limit Kill Switch ---
                if page_num >= 25:
                    update_status(100, f"🛑 Reached the 25-page limit. Stopping Federal scan.")
                    break
                # --------------------------------------------
                
                try:
                    paginator_text_selector = ".ui-paginator-current"
                    next_button.click(no_wait_after=True)
                    
                    target_text = f"{page_num + 1} /"
                    update_status(current_prog + 2, f"⏳ Clicking Next... Waiting for '{target_text}'")
                    
                    time.sleep(4) 
                    page.wait_for_selector(f"{paginator_text_selector}:has-text('{target_text}')", timeout=15000)
                    page_num += 1
                except Exception as e:
                    print(f"⚠️ Pagination stopped or timed out.")
                    break

            browser.close()
            if progress_bar: time.sleep(1); progress_bar.empty() 
            return results

        except Exception as e:
            print(f"System Error: {e}")
            browser.close()
            if progress_bar: progress_bar.empty()
            return results