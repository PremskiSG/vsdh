#!/usr/bin/env python3
"""
Improved Business Details Extraction Tool for VSDHOne Platform
Handles React SPA and dynamic data loading using multiple extraction methods
"""

import requests
import csv
import time
import random
import json
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging

class ImprovedBusinessExtractor:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        self.api_base = "https://vsdigital-bookingwidget-prod.azurewebsites.net/"
        
        # Load discovered slugs
        self.discovered_slugs = []
        self.load_discovered_slugs()
        
        # Setup session with realistic headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })
        
        self.business_data = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_discovered_slugs(self):
        """Load slugs from the discovery CSV file"""
        try:
            with open('vsdhone_brands_smart.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.discovered_slugs = [row['slug'] for row in reader]
            print(f"📁 Loaded {len(self.discovered_slugs)} discovered slugs")
        except FileNotFoundError:
            print("❌ Discovery CSV file not found. Please run discovery first.")
            self.discovered_slugs = []
    
    def setup_selenium_driver(self):
        """Setup Selenium driver with appropriate options"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e:
            self.logger.error(f"Failed to setup Chrome driver: {e}")
            return None
    
    def extract_with_browser_automation(self, slug):
        """Extract business data using browser automation to handle dynamic content"""
        driver = None
        try:
            driver = self.setup_selenium_driver()
            if not driver:
                return None
            
            url = f"{self.base_url}{slug}"
            self.logger.info(f"🌐 Loading {slug} with browser automation...")
            
            driver.get(url)
            
            # Wait for potential React content to load
            time.sleep(5)
            
            # Try to find business data in various ways
            business_info = {
                'extraction_method': 'Browser Automation',
                'business_name': '',
                'address': '',
                'phone': '',
                'email': '',
                'website': '',
                'services': '',
                'description': '',
                'location': '',
            }
            
            # Look for common business info selectors
            business_selectors = [
                # Business name selectors
                ('business_name', ['h1', 'h2', '.business-name', '.company-name', '.title', '[data-testid*="name"]']),
                # Address selectors  
                ('address', ['.address', '.location', '[data-testid*="address"]', '.contact-info']),
                # Phone selectors
                ('phone', ['.phone', '.telephone', '[href^="tel:"]', '[data-testid*="phone"]']),
                # Email selectors
                ('email', ['.email', '[href^="mailto:"]', '[data-testid*="email"]']),
            ]
            
            for field, selectors in business_selectors:
                for selector in selectors:
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            text = element.get_attribute('textContent') or element.text
                            if text and len(text.strip()) > 2:
                                business_info[field] = text.strip()[:200]  # Limit length
                                break
                        if business_info[field]:
                            break
                    except Exception:
                        continue
            
            # Check for network requests that might contain business data
            logs = driver.get_log('performance')
            for log in logs:
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    url_log = message['message']['params']['response']['url']
                    if 'business' in url_log or 'api' in url_log:
                        self.logger.info(f"Found API call: {url_log}")
            
            # Look for JavaScript variables containing business data
            business_data_script = """
            var businessData = {};
            
            // Check common global variables
            if (window.businessConfig) businessData.config = window.businessConfig;
            if (window.__INITIAL_STATE__) businessData.initialState = window.__INITIAL_STATE__;
            if (window.appConfig) businessData.appConfig = window.appConfig;
            
            // Check for React component data
            var reactElements = document.querySelectorAll('[data-reactroot] *');
            for (var i = 0; i < reactElements.length; i++) {
                var elem = reactElements[i];
                for (var prop in elem) {
                    if (prop.startsWith('__reactInternalInstance') || prop.startsWith('_reactInternalFiber')) {
                        try {
                            var reactData = elem[prop];
                            if (reactData && reactData.memoizedProps) {
                                businessData.reactProps = reactData.memoizedProps;
                                break;
                            }
                        } catch(e) {}
                    }
                }
                if (businessData.reactProps) break;
            }
            
            return JSON.stringify(businessData);
            """
            
            try:
                js_data = driver.execute_script(business_data_script)
                if js_data and js_data != '{}':
                    business_info['raw_js_data'] = js_data[:1000]  # Limit size
                    
                    # Try to parse useful info from JS data
                    parsed_data = json.loads(js_data)
                    for key, value in parsed_data.items():
                        if isinstance(value, dict):
                            # Look for business info in nested objects
                            for nested_key, nested_value in value.items():
                                if 'name' in nested_key.lower() and isinstance(nested_value, str):
                                    business_info['business_name'] = business_info['business_name'] or nested_value
                                elif 'address' in nested_key.lower() and isinstance(nested_value, str):
                                    business_info['address'] = business_info['address'] or nested_value
                                elif 'phone' in nested_key.lower() and isinstance(nested_value, str):
                                    business_info['phone'] = business_info['phone'] or nested_value
            except Exception as e:
                self.logger.debug(f"JS extraction failed: {e}")
            
            # Return data if we found anything useful
            if any(business_info[field] for field in ['business_name', 'address', 'phone', 'email']):
                return business_info
            
            return None
            
        except Exception as e:
            self.logger.error(f"Browser automation failed for {slug}: {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def try_api_discovery(self, slug):
        """Try to discover and call business-specific API endpoints"""
        # Extended list of potential API endpoints
        api_endpoints = [
            f"api/business/{slug}",
            f"api/business/{slug}/details", 
            f"api/business/{slug}/info",
            f"api/business/{slug}/profile",
            f"api/business/{slug}/config",
            f"api/business/{slug}/settings",
            f"api/widget/{slug}",
            f"api/widget/{slug}/config",
            f"api/widget/{slug}/business",
            f"api/v1/business/{slug}",
            f"api/v2/business/{slug}",
            f"business-api/{slug}",
            f"widget-api/{slug}",
            f"booking-api/business/{slug}",
            f"config/{slug}",
            f"businesses/{slug}",
            f"data/business/{slug}",
            f"api/businesses/{slug}/data",
        ]
        
        for endpoint in api_endpoints:
            try:
                url = f"{self.api_base}{endpoint}"
                
                # Try different request methods
                for method in ['GET', 'POST']:
                    try:
                        if method == 'GET':
                            response = self.session.get(url, timeout=10)
                        else:
                            response = self.session.post(url, json={'businessId': slug}, timeout=10)
                        
                        if response.status_code == 200:
                            try:
                                # Try JSON first
                                data = response.json()
                                if isinstance(data, dict) and len(str(data)) > 100:
                                    # Check if it's actually business data, not error/empty response
                                    if any(key in str(data).lower() for key in ['name', 'address', 'phone', 'business', 'contact']):
                                        self.logger.info(f"✅ Found business data at {endpoint}")
                                        return {'endpoint': endpoint, 'method': method, 'data': data}
                            except json.JSONDecodeError:
                                # Maybe it's useful HTML/text content
                                content = response.text
                                if len(content) > 500 and any(term in content.lower() for term in ['business', 'address', 'phone', 'contact']):
                                    self.logger.info(f"✅ Found business content at {endpoint}")
                                    return {'endpoint': endpoint, 'method': method, 'data': content}
                    except Exception:
                        continue
                        
            except Exception:
                continue
        
        return None
    
    def extract_business_details(self, slug):
        """Extract business details using multiple methods"""
        self.logger.info(f"🔍 Extracting details for: {slug}")
        
        business_info = {
            'slug': slug,
            'url': f"{self.base_url}{slug}",
            'business_name': '',
            'address': '',
            'phone': '',
            'email': '',
            'website': '',
            'services': '',
            'location': '',
            'description': '',
            'extraction_method': '',
            'raw_data': '',
            'extracted_at': datetime.now().isoformat()
        }
        
        extraction_methods = []
        
        # Method 1: API Discovery
        api_result = self.try_api_discovery(slug)
        if api_result:
            extraction_methods.append('API Discovery')
            business_info['extraction_method'] = f"API: {api_result['endpoint']}"
            business_info['raw_data'] = str(api_result['data'])[:1000]
            
            # Extract business info from API data
            data = api_result['data']
            if isinstance(data, dict):
                # Common field mappings
                field_mappings = {
                    'business_name': ['name', 'businessName', 'companyName', 'title', 'business_name'],
                    'address': ['address', 'location', 'street', 'full_address', 'business_address'],
                    'phone': ['phone', 'phoneNumber', 'tel', 'telephone', 'contact_phone'],
                    'email': ['email', 'contactEmail', 'business_email', 'contact_email'],
                    'website': ['website', 'url', 'homepage', 'web_url'],
                    'description': ['description', 'about', 'bio', 'summary', 'details']
                }
                
                for field, possible_keys in field_mappings.items():
                    for key in possible_keys:
                        if key in data and data[key]:
                            business_info[field] = str(data[key])[:200]
                            break
        
        # Method 2: Browser Automation (if API didn't work)
        if not extraction_methods:
            browser_result = self.extract_with_browser_automation(slug)
            if browser_result:
                extraction_methods.append('Browser Automation')
                business_info['extraction_method'] = 'Browser Automation'
                for key, value in browser_result.items():
                    if key in business_info and value:
                        business_info[key] = value
        
        # Method 3: Network traffic analysis during page load
        if not extraction_methods:
            # This would require more advanced network monitoring
            # For now, mark as attempted
            extraction_methods.append('Network Analysis (placeholder)')
            business_info['extraction_method'] = 'Network Analysis - No data found'
        
        # If we got any useful data, consider it successful
        if any(business_info[field] for field in ['business_name', 'address', 'phone', 'email']):
            self.logger.info(f"✅ Successfully extracted data for {slug}")
            return business_info
        else:
            self.logger.warning(f"⚠️  No business data found for {slug}")
            return business_info  # Return anyway for record-keeping
    
    def extract_all_details(self, max_workers=3, max_slugs=None):
        """Extract details for all discovered slugs with threading"""
        slugs_to_process = self.discovered_slugs[:max_slugs] if max_slugs else self.discovered_slugs
        
        print(f"🚀 Starting improved extraction for {len(slugs_to_process)} slugs...")
        print(f"Using {max_workers} concurrent workers")
        
        successful_extractions = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all extraction tasks
            future_to_slug = {
                executor.submit(self.extract_business_details, slug): slug 
                for slug in slugs_to_process
            }
            
            # Process completed tasks
            for i, future in enumerate(as_completed(future_to_slug), 1):
                slug = future_to_slug[future]
                try:
                    result = future.result(timeout=60)  # 60 second timeout per slug
                    if result:
                        self.business_data.append(result)
                        
                        # Check if we got useful data
                        if any(result[field] for field in ['business_name', 'address', 'phone', 'email']):
                            successful_extractions += 1
                            print(f"✅ {i}/{len(slugs_to_process)}: {slug} - Data found!")
                        else:
                            print(f"⚠️  {i}/{len(slugs_to_process)}: {slug} - No data")
                    
                    # Save progress periodically
                    if i % 10 == 0:
                        self.save_results()
                        print(f"💾 Progress saved - {successful_extractions}/{i} successful")
                    
                    # Rate limiting
                    time.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    self.logger.error(f"Error processing {slug}: {e}")
                    # Add failed entry
                    self.business_data.append({
                        'slug': slug,
                        'url': f"{self.base_url}{slug}",
                        'extraction_method': 'Failed',
                        'raw_data': f'Error: {str(e)}',
                        'extracted_at': datetime.now().isoformat()
                    })
        
        print(f"\n🎯 Extraction complete!")
        print(f"   • Total processed: {len(slugs_to_process)}")
        print(f"   • Successful extractions: {successful_extractions}")
        print(f"   • Success rate: {successful_extractions/len(slugs_to_process)*100:.1f}%")
        
        # Final save
        self.save_results()
    
    def save_results(self):
        """Save extracted business data to CSV"""
        if not self.business_data:
            return
        
        fieldnames = [
            'slug', 'url', 'business_name', 'address', 'phone', 'email', 
            'website', 'services', 'location', 'description', 'extraction_method', 
            'raw_data', 'extracted_at'
        ]
        
        filename = f'improved_business_details_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in self.business_data:
                # Ensure all fields exist
                for field in fieldnames:
                    if field not in entry:
                        entry[field] = ''
                writer.writerow(entry)
        
        print(f"💾 Results saved to: {filename}")
    
    def generate_summary_report(self):
        """Generate a summary report of extraction results"""
        if not self.business_data:
            print("No data to summarize")
            return
        
        total = len(self.business_data)
        with_names = sum(1 for entry in self.business_data if entry.get('business_name', '').strip())
        with_addresses = sum(1 for entry in self.business_data if entry.get('address', '').strip())
        with_phones = sum(1 for entry in self.business_data if entry.get('phone', '').strip())
        with_emails = sum(1 for entry in self.business_data if entry.get('email', '').strip())
        
        print(f"\n📊 EXTRACTION SUMMARY REPORT")
        print(f"=" * 50)
        print(f"Total slugs processed: {total}")
        print(f"Business names found: {with_names} ({with_names/total*100:.1f}%)")
        print(f"Addresses found: {with_addresses} ({with_addresses/total*100:.1f}%)")
        print(f"Phone numbers found: {with_phones} ({with_phones/total*100:.1f}%)")
        print(f"Email addresses found: {with_emails} ({with_emails/total*100:.1f}%)")
        
        # Show successful extractions
        successful = [entry for entry in self.business_data 
                     if any(entry.get(field, '').strip() for field in ['business_name', 'address', 'phone', 'email'])]
        
        print(f"\n✅ SUCCESSFUL EXTRACTIONS ({len(successful)}):")
        for entry in successful:
            name = entry.get('business_name', 'Unknown')
            address = entry.get('address', 'No address')
            phone = entry.get('phone', 'No phone')
            print(f"  • {entry['slug']}: {name} | {address} | {phone}")

if __name__ == "__main__":
    extractor = ImprovedBusinessExtractor()
    
    # Test on a small sample first
    print("🧪 Starting with a small test sample...")
    extractor.extract_all_details(max_workers=2, max_slugs=5)
    extractor.generate_summary_report()
    
    # Ask user if they want to continue with full extraction
    if input("\nContinue with full extraction? (y/n): ").lower() == 'y':
        extractor.extract_all_details(max_workers=3)
        extractor.generate_summary_report() 