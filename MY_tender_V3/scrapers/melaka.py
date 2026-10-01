from playwright.sync_api import sync_playwright
import time
import re

def scrape_melaka(keyword):
    results = []
    print(f"Starting scrape for Melaka STOM (Keywords: '{keyword}')...")
    search_terms = [k.strip().lower() for k in keyword.split(",")]
    seen_titles = set()

    target_urls = {
        "Notis": "https://stom.melaka.gov.my/",
        "Tender": "https://stom.melaka.gov.my/?type=1",
        "Sebut Harga": "https://stom.melaka.gov.my/?type=2"
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            ignore_https_errors=True
        )
        page = context.new_page()
        
        for category, url in target_urls.items():
            print(f"\n🌐 Accessing Melaka STOM: {category} Tab...")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_selector("input[type='search']", timeout=20000)
                
                for term in search_terms:
                    print(f"🔍 Searching Melaka ({category}) for: '{term}'")
                    search_box = page.locator("input[type='search']")
                    search_box.clear()
                    search_box.fill(term)
                    time.sleep(4) 
                    
                    page_num = 1
                    while True:
                        print(f"📄 Scanning Melaka {category} Page {page_num} for '{term}'...")
                        rows = page.query_selector_all("table#notices-dtb tbody tr")
                        
                        for row in rows:
                            cols = row.query_selector_all("td")
                            row_text = row.inner_text()
                            
                            if len(cols) >= 5 and "No matching records found" not in row_text and "Tiada rekod" not in row_text and "Sedang diproses" not in row_text:
                                title_text = cols[1].inner_text().strip()
                                closing_date = cols[4].inner_text().strip()
                                agency_text = "Kerajaan Negeri Melaka"
                                clean_title = title_text.replace('\n', ' ')
                                
                                detail_link = url 
                                
                                link_el = cols[-1].query_selector("a")
                                if link_el:
                                    href = link_el.get_attribute("href")
                                    if href:
                                        if href.startswith("http"):
                                            detail_link = href
                                        else:
                                            slash = "" if href.startswith("/") else "/"
                                            detail_link = f"https://stom.melaka.gov.my{slash}{href}"
                                
                                if re.search(rf'\b{re.escape(term)}\b', clean_title.lower()) and clean_title not in seen_titles:
                                    seen_titles.add(clean_title)
                                    results.append({
                                        "Title": clean_title,
                                        "Agency": agency_text,
                                        "Closing Date": closing_date,
                                        "Source": f"Melaka STOM ({category})", 
                                        "Link": detail_link 
                                    })
                        
                        next_button = page.locator("li.paginate_button.next:not(.disabled) a")
                        if next_button.count() > 0:
                            print(f"⏳ Clicking Next Page...")
                            next_button.first.click(no_wait_after=True)
                            time.sleep(4)
                            page_num += 1
                        else:
                            print(f"✅ Reached last page for '{term}' in {category}.")
                            break
            
            except Exception as e: 
                print(f"Melaka Scraping Error on {category}: {e}")
        
        browser.close()
        
    return results