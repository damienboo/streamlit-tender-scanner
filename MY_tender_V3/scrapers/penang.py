from playwright.sync_api import sync_playwright
import re

def scrape_penang(keyword):
    results = []
    print(f"Starting scrape for Penang sysP (Keywords: '{keyword}')...")
    search_terms = [k.strip().lower() for k in keyword.split(",")]
    seen_titles = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            url = "https://ep.penang.gov.my/index.php"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            page_num = 1
            while True:
                print(f"📄 Scanning Penang Page {page_num}...")
                
                try:
                    page.wait_for_selector("table.perolehan", timeout=15000)
                except Exception:
                    print("ℹ️ No tender table found or page timed out.")
                    break
                    
                rows = page.query_selector_all("table.perolehan tr")
                
                for row in rows:
                    cols = row.query_selector_all("td")
                    
                    if len(cols) == 6:
                        raw_cell = cols[0]
                        
                        raw_agency = raw_cell.query_selector("div.view_title_content")
                        raw_number = raw_cell.query_selector("div.view_title_kecil")
                        raw_title = raw_cell.query_selector("a.a2")
                        
                        if raw_title and raw_agency:
                            full_cell_text = raw_cell.text_content().lower()
                            match_found = any(term in full_cell_text for term in search_terms)
                            
                            if match_found:
                                title_text = raw_title.text_content().strip()
                                clean_title = " ".join(title_text.split())
                                
                                if clean_title not in seen_titles:
                                    seen_titles.add(clean_title)
                                    
                                    agency_text = raw_agency.text_content().strip()
                                    tender_number = raw_number.text_content().strip() if raw_number else ""
                                    
                                    display_title = f"{tender_number} | {clean_title}" if tender_number else clean_title
                                    
                                    closing_date = cols[4].text_content().strip().replace('\n', ' ')
                                    
                                    href = raw_title.get_attribute("href")
                                    if href:
                                        if href.startswith("http"):
                                            detail_link = href
                                        else:
                                            slash = "" if href.startswith("/") else "/"
                                            detail_link = f"https://ep.penang.gov.my{slash}{href}"
                                    else:
                                        detail_link = "https://ep.penang.gov.my/index.php"
                                    
                                    results.append({
                                        "Title": display_title,
                                        "Agency": agency_text,
                                        "Closing Date": closing_date,
                                        "Source": "Penang (sysP)",
                                        "Link": detail_link 
                                    })
                                    print(f"      ✅ [ADDED] {display_title[:60]}...")
                
                next_button = page.locator("a:has(img[src='img/right.gif'])")
                
                if next_button.count() > 0:
                    print(f"⏳ Flipping to the next page...")
                    with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                        next_button.first.click()
                    page_num += 1
                else:
                    print("✅ Reached end of Penang list.")
                    break
                    
        except Exception as e: 
            print(f"Penang Scraping Error: {e}")
            
        finally: 
            browser.close()
            
    return results