from playwright.sync_api import sync_playwright
import re

def clean_html(raw_html):
    """Removes HTML tags from the JSON data and formats multi-line text."""
    if not raw_html: return ""
    text = re.sub(r'<br\s*/?>', ' | ', str(raw_html), flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    return " ".join(text.split()).replace(" | | ", " | ").strip()

def scrape_selangor(keyword):
    results = []
    print(f"Starting Ultimate API scrape for Selangor (Keywords: '{keyword}')...")
    
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
            print("⏳ Intercepting the main tender database on page load...")
            
            with page.expect_response(lambda r: "json" in r.headers.get("content-type", "").lower() and r.status == 200, timeout=60000) as response_info:
                page.goto("https://tender.selangor.my/?type=tenders", timeout=0)
            
            json_data = response_info.value.json()
            all_tenders = json_data.get('data', [])
            
            print(f"✅ Successfully captured {len(all_tenders)} total tenders from the server.")
            
            for term in search_terms:
                print(f"🔍 Filtering captured data for: '{term}'")
                
                for row in all_tenders:
                    raw_title = row.get('name', '')
                    clean_title = clean_html(raw_title)
                    
                    if term in clean_title.lower() and clean_title not in seen_titles:
                        seen_titles.add(clean_title)
                        
                        raw_date = row.get('submission_datetime', '')
                        closing_date = clean_html(raw_date)
                                                
                        invalid_date_markers = ["", "-", "sila rujuk dokumen iklan", "tiada"]
                        if closing_date.strip().lower() in invalid_date_markers:
                            continue 
                            
                        if "berjaya" in clean_title.lower() or "batal" in clean_title.lower():
                            continue 
                            
                        link_match = re.search(r'href=["\']([^"\']+)["\']', str(raw_title), re.IGNORECASE)
                        
                        if link_match:
                            extracted_url = link_match.group(1)
                            if extracted_url.startswith("http"):
                                direct_link = extracted_url
                            else:
                                direct_link = f"https://tender.selangor.my{extracted_url}" if extracted_url.startswith("/") else f"https://tender.selangor.my/{extracted_url}"
                        else:
                            direct_link = "https://tender.selangor.my/"

                        results.append({
                            "Title": clean_title,
                            "Agency": "Kerajaan Negeri Selangor",
                            "Closing Date": closing_date,
                            "Source": "Selangor",
                            "Link": direct_link
                        })
                        
        except Exception as e:
            print(f"Selangor API Scraping Error: {e}")
            
        finally:
            browser.close()
            
    return results