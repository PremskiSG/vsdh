#!/usr/bin/env python3
"""
Extract business data from known working VSDHOne slugs
"""

import time
import csv
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class WorkingSlugExtractor:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        
        # Known working slugs from your original list
        self.working_slugs = [
            'ad31y', 'mj42f', 'os27m', 'lp56a', 'zb74k', 'ym99l', 
            'yh52b', 'zd20w', 'td32z', 'bo19e', 'bh70s', 'ai04u', 
            'bm49t', 'qu29u', 'tc33l'
        ]
        
        self.results = []
    
    def setup_driver(self):
        """Setup Chrome driver"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        return webdriver.Chrome(options=options)
    
    def extract_business_data(self, slug):
        """Extract detailed business data from a working slug"""
        print(f"\n🔍 Extracting: {slug}")
        
        driver = self.setup_driver()
        
        try:
            url = f"{self.base_url}{slug}"
            driver.get(url)
            
            # Wait for page to load
            time.sleep(8)
            
            business_data = {
                'slug': slug,
                'url': url,
                'final_url': driver.current_url,
                'page_title': driver.title,
                'business_name': '',
                'services': [],
                'pricing': [],
                'description': '',
                'contact_info': '',
                'business_type': '',
                'location': '',
                'extracted_at': datetime.now().isoformat()
            }
            
            # Check if redirected to external site
            if 'vsdigital-bookingwidget-prod.azurewebsites.net' not in driver.current_url:
                print(f"🔗 External redirect to: {driver.current_url}")
                business_data['business_name'] = driver.title
                business_data['external_website'] = driver.current_url
                business_data['business_type'] = 'External Redirect'
                
                # Try to extract contact info from external site
                try:
                    contact_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href^="tel:"], a[href^="mailto:"]')
                    for elem in contact_elements:
                        href = elem.get_attribute('href')
                        if href.startswith('tel:'):
                            business_data['phone'] = href.replace('tel:', '')
                        elif href.startswith('mailto:'):
                            business_data['email'] = href.replace('mailto:', '')
                except:
                    pass
            else:
                # Extract from VSDHOne widget
                print(f"📱 Extracting from VSDHOne widget...")
                
                # Business name (usually in page title or main heading)
                business_data['business_name'] = driver.title
                
                # Look for services and pricing
                try:
                    # Find service items with pricing
                    service_elements = driver.find_elements(By.CSS_SELECTOR, '[class*="service"], [class*="item"], [class*="product"]')
                    services = []
                    pricing = []
                    
                    for elem in service_elements:
                        text = elem.text.strip()
                        if text and len(text) < 200:
                            if '$' in text:
                                pricing.append(text)
                            elif any(word in text.lower() for word in ['injection', 'therapy', 'treatment', 'service']):
                                services.append(text)
                    
                    business_data['services'] = services[:10]  # Limit to 10
                    business_data['pricing'] = pricing[:10]
                    
                    # Try to determine business type
                    all_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
                    if 'semaglutide' in all_text or 'injection' in all_text:
                        business_data['business_type'] = 'Medical/Weight Loss'
                    elif 'drip' in all_text or 'iv' in all_text:
                        business_data['business_type'] = 'IV Therapy'
                    elif 'hotel' in all_text or 'booking' in all_text:
                        business_data['business_type'] = 'Hospitality'
                    else:
                        business_data['business_type'] = 'Healthcare'
                        
                    # Extract description/summary
                    desc_elements = driver.find_elements(By.CSS_SELECTOR, 'p, .description, .summary')
                    descriptions = []
                    for elem in desc_elements:
                        text = elem.text.strip()
                        if text and len(text) > 20 and len(text) < 300:
                            descriptions.append(text)
                    
                    business_data['description'] = ' | '.join(descriptions[:3])
                    
                except Exception as e:
                    print(f"⚠️  Error extracting services: {e}")
            
            print(f"✅ Extracted: {business_data['business_name']}")
            return business_data
            
        except Exception as e:
            print(f"❌ Error extracting {slug}: {e}")
            return {
                'slug': slug,
                'error': str(e),
                'extracted_at': datetime.now().isoformat()
            }
        finally:
            driver.quit()
    
    def extract_all(self):
        """Extract data from all working slugs"""
        print(f"🚀 Extracting business data from {len(self.working_slugs)} known working slugs...")
        
        for i, slug in enumerate(self.working_slugs, 1):
            print(f"\n📍 Processing {i}/{len(self.working_slugs)}: {slug}")
            
            result = self.extract_business_data(slug)
            if result:
                self.results.append(result)
            
            # Rate limiting
            time.sleep(3)
        
        # Save results
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save results to CSV"""
        if not self.results:
            print("No results to save")
            return
        
        filename = f'working_slugs_extracted_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Get all field names
        all_fields = set()
        for result in self.results:
            all_fields.update(result.keys())
        
        fieldnames = sorted(list(all_fields))
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                # Convert lists to strings
                for key, value in result.items():
                    if isinstance(value, list):
                        result[key] = ' | '.join(str(v) for v in value)
                writer.writerow(result)
        
        print(f"💾 Results saved to: {filename}")
    
    def print_summary(self):
        """Print extraction summary"""
        print(f"\n📊 WORKING SLUGS EXTRACTION SUMMARY")
        print(f"=" * 50)
        
        total = len(self.results)
        business_types = {}
        external_redirects = 0
        
        for result in self.results:
            btype = result.get('business_type', 'Unknown')
            business_types[btype] = business_types.get(btype, 0) + 1
            if result.get('external_website'):
                external_redirects += 1
        
        print(f"Total working slugs: {total}")
        print(f"External redirects: {external_redirects}")
        print(f"\nBusiness Types:")
        for btype, count in business_types.items():
            print(f"  {btype}: {count}")
        
        print(f"\n✅ DISCOVERED BUSINESSES:")
        for result in self.results:
            name = result.get('business_name', 'Unknown')[:40]
            btype = result.get('business_type', 'Unknown')
            services_count = len(result.get('services', []))
            print(f"  • {result['slug']}: {name} ({btype}) - {services_count} services")

if __name__ == "__main__":
    extractor = WorkingSlugExtractor()
    extractor.extract_all() 