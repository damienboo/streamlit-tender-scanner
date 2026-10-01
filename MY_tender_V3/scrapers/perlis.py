from playwright.sync_api import sync_playwright
import time

def scrape_perlis(keyword):
    results = []
    print(f"Starting scrape for Perlis JKR (Keywords: '{keyword}')...")
    search_terms = [k.strip().lower() for k in keyword.split(",")]
    seen_titles = set()
    matched_tenders = [] 

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            url = "https://jkrperlis.gov.my/arkib-tender-sebutharga/"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            page_num = 1
            while True:
                print(f"📄 Scanning Perlis Page {page_num}...")
                try:
                    page.wait_for_selector("table.ninja_footable tbody tr", timeout=15000)
                except Exception:
                    break
                    
                rows = page.query_selector_all("table.ninja_footable tbody tr")
                for row in rows:
                    link_el = row.query_selector("td.ninja_column_1 a")
                    if not link_el: continue
                        
                    title_text = link_el.text_content().strip()
                    clean_title = " ".join(title_text.split())
                    href = link_el.get_attribute("href")
                    
                    if any(term in clean_title.lower() for term in search_terms):
                        if clean_title not in seen_titles:
                            seen_titles.add(clean_title)
                            matched_tenders.append({"Title": clean_title, "Link": href})
                
                next_button = page.locator("li.footable-page-arrow.next:not(.disabled) a")
                if next_button.count() > 0:
                    next_button.first.click()
                    page.wait_for_timeout(2000) 
                    page_num += 1
                else:
                    break
                    
            if matched_tenders:
                print(f"\n🔍 Found {len(matched_tenders)} matching tenders. Fetching closing dates...")
                for tender in matched_tenders:
                    clean_title = tender["Title"]
                    href = tender["Link"]
                    closing_date = "Sila Rujuk Dokumen" 
                    
                    if href:
                        try:
                            page.goto(href, wait_until="domcontentloaded", timeout=30000)
                            
                            try:
                                page.wait_for_selector("table#ntb_table tr td", timeout=15000)
                            except Exception as e:
                                print(f"⚠️ Timeout waiting for details table or table not found: {e}")

                            detail_rows = page.query_selector_all("table#ntb_table tr")
                            for d_row in detail_rows:
                                cells = d_row.query_selector_all("td")
                                if len(cells) >= 2:
                                    label = cells[0].text_content().strip().lower()
                                    
                                    if label == "tarikh tutup":
                                        closing_date = cells[1].text_content().strip().replace('\n', ' ')
                                        break
                                        
                        except Exception as e:
                            print(f"⚠️ Could not fetch details for: {clean_title} ({e})")
                    
                    if href:
                        if href.startswith("http"):
                            detail_link = href
                        else:
                            slash = "" if href.startswith("/") else "/"
                            detail_link = f"https://jkrperlis.gov.my{slash}{href}"
                    else:
                        detail_link = "https://jkrperlis.gov.my/arkib-tender-sebutharga/"
                    
                    results.append({
                        "Title": clean_title,
                        "Agency": "Jabatan Kerja Raya Negeri Perlis (JKR)",
                        "Closing Date": closing_date,
                        "Source": "Perlis (JKR)",
                        "Link": detail_link 
                    })
                    print(f"      ✅ [ADDED] {clean_title[:50]}... (Tutup: {closing_date})")

        except Exception as e: 
            print(f"Perlis Scraping Error: {e}")
        finally: 
            browser.close()
            
    return results