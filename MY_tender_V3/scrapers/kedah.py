from playwright.sync_api import sync_playwright
import re

def scrape_kedah(keyword):
    results = []
    print(f"Starting scrape for Kedah (Keywords: '{keyword}')...")
    search_terms = [k.strip().lower() for k in keyword.split(",")]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            url = "https://www.kedah.gov.my/index.php/tender-sebut-harga-jabatan-negeri/"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("table.wpr-data-table tbody tr", timeout=20000)
            
            rows = page.query_selector_all("table.wpr-data-table tbody tr.wpr-table-body-row")
            print(f"Found {len(rows)} tender rows in Kedah portal.")
            
            for row in rows:
                cols = row.query_selector_all("td")
                
                if len(cols) >= 6:
                    
                    agency_text = cols[1].text_content().strip()
                    if not agency_text:
                        img = cols[1].query_selector("img")
                        if img:
                            agency_text = img.get_attribute("alt") or "Kerajaan Negeri Kedah"
                        else:
                            agency_text = "Kerajaan Negeri Kedah"
                            
                    title_text = cols[2].text_content().strip()
                    if not title_text:
                        continue
                        
                    closing_date = cols[4].text_content().strip().replace('\n', ' ')
                    
                    clean_title = title_text.replace('\n', ' ')
                    combined_text = (clean_title + " " + agency_text).lower()
                    
                    pdf_link = url 
                    download_btn = cols[5].query_selector("a")
                    if download_btn:
                        extracted_href = download_btn.get_attribute("href")
                        if extracted_href:
                            pdf_link = extracted_href
                    
                    match_found = any(term in combined_text for term in search_terms)
                    
                    if match_found:
                        results.append({
                            "Title": clean_title,
                            "Agency": agency_text,
                            "Closing Date": closing_date,
                            "Source": "Kedah",
                            "Link": pdf_link 
                        })
                        print(f"      ✅ [ADDED] {clean_title[:60]}...")
                        
            print("✅ Finished Kedah.")
            
        except Exception as e: 
            print(f"Kedah Scraping Error: {e}")
            
        finally: 
            browser.close()
            
    return results