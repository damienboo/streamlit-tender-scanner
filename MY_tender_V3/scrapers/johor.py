from playwright.sync_api import sync_playwright
import re

def scrape_johor(keyword):
    results = []
    print(f"Starting scrape for Johor MBIP (Keywords: '{keyword}')...")
    
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
            for term in search_terms:
                print(f"\n🔍 Searching MBIP directly for: '{term}'")
                
                current_url = f"https://eperolehan2.mbip.gov.my/tender?search={term}"
                page_num = 1
                
                while current_url:
                    print(f"📄 Scanning Page {page_num}...")
                    page.goto(current_url, wait_until="domcontentloaded", timeout=60000)
                    
                    try:
                        page.wait_for_selector(".card-tender", timeout=15000)
                    except Exception:
                        print(f"ℹ️ No active tenders found or page empty for '{term}'.")
                        break
                        
                    cards = page.query_selector_all(".card-tender")
                    
                    for card in cards:
                        title_el = card.query_selector("a.tender-title")
                        if not title_el:
                            continue
                            
                        raw_title = title_el.text_content().strip()
                        clean_title = " ".join(raw_title.split())
                        
                        href = title_el.get_attribute("href")
                        if href:
                            detail_link = href if href.startswith("http") else f"https://eperolehan2.mbip.gov.my{href}"
                        else:
                            detail_link = current_url 
                        
                        badges = card.query_selector_all(".badge")
                        badge_texts = [b.text_content().strip().lower() for b in badges]
                        
                        if "buka" not in badge_texts and "diumumkan" not in badge_texts:
                            status_reason = badge_texts[-1].upper() if badges else "UNKNOWN"
                            print(f"      ❌ [SKIPPED - {status_reason}] {clean_title[:60]}...")
                            continue 
                        else:
                            print(f"      ✅ [ADDED - ACTIVE] {clean_title[:60]}...")
                        
                        if clean_title and clean_title not in seen_titles:
                            seen_titles.add(clean_title)
                            
                            date_el = card.query_selector(".close-date")
                            closing_date = date_el.text_content().replace("Tarikh Tutup:", "").strip() if date_el else "Sila Rujuk Dokumen"
                            
                            results.append({
                                "Title": clean_title,
                                "Agency": "Majlis Bandaraya Iskandar Puteri (MBIP)",
                                "Closing Date": closing_date,
                                "Source": "Johor (MBIP)",
                                "Link": detail_link 
                            })
                    
                    next_button = page.query_selector("a.page-link[rel='next']")
                    if next_button:
                        next_href = next_button.get_attribute("href")
                        if next_href.startswith("http"):
                            current_url = next_href
                        else:
                            current_url = "https://eperolehan2.mbip.gov.my" + next_href
                            
                        page_num += 1
                        print(f"⏳ Flipping to the next page...")
                    else:
                        print(f"✅ Reached end of MBIP list for '{term}'.")
                        current_url = None 

        except Exception as e:
            print(f"Johor MBIP Scraping Error: {e}")
            
        finally:
            browser.close()
            
    return results