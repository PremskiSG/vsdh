#!/usr/bin/env python3
"""
Business Details Extraction Tool
Extracts detailed business information from discovered VSDHOne slugs
"""

import requests
import csv
import time
import random
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

class BusinessDetailsExtractor:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        self.api_base = "https://vsdigital-bookingwidget-prod.azurewebsites.net/"
        
        # Load discovered slugs from the CSV
        self.discovered_slugs = []
        self.load_discovered_slugs()
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
        
        self.business_details = []
    
    def load_discovered_slugs(self):
        """Load slugs from the CSV file"""
        try:
            with open('vsdhone_brands_smart.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.discovered_slugs = [row['slug'] for row in reader]
            print(f"📁 Loaded {len(self.discovered_slugs)} discovered slugs")
        except FileNotFoundError:
            print("❌ CSV file not found. Please run discovery first.")
            self.discovered_slugs = []
    
    def try_api_endpoints(self, slug):
        """Try various API endpoints to extract business data"""
        endpoints = [
            f"api/business/{slug}",
            f"api/business/{slug}/details",
            f"api/business/{slug}/info", 
            f"api/business/{slug}/profile",
            f"api/widget/{slug}",
            f"api/widget/{slug}/config",
            f"api/v1/business/{slug}",
            f"api/config/{slug}",
            f"widget-api/business/{slug}",
            f"booking-api/business/{slug}",
        ]
        
        for endpoint in endpoints:
            try:
                url = urljoin(self.api_base, endpoint)
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data and isinstance(data, dict) and len(str(data)) > 200:
                            print(f"✅ {slug}: Found data at {endpoint}")
                            return data, endpoint
                    except json.JSONDecodeError:
                        # Maybe it's useful text content
                        if len(response.text) > 500 and 'business' in response.text.lower():
                            print(f"✅ {slug}: Found text data at {endpoint}")
                            return response.text, endpoint
                            
            except Exception as e:
                continue
        
        return None, None
    
    def extract_from_widget_page(self, slug):
        """Extract data from the widget page by looking for embedded configurations"""
        try:
            url = f"{self.base_url}{slug}"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for JSON configurations in script tags
                patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                    r'window\.CONFIG\s*=\s*({.+?});',
                    r'var\s+config\s*=\s*({.+?});',
                    r'const\s+businessConfig\s*=\s*({.+?});',
                    r'"businessId"\s*:\s*"([^"]+)"',
                    r'"business_id"\s*:\s*"([^"]+)"',
                    r'"name"\s*:\s*"([^"]+)"',
                    r'"address"\s*:\s*"([^"]+)"',
                    r'"phone"\s*:\s*"([^"]+)"',
                ]
                
                extracted_data = {}
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                    if matches:
                        for match in matches:
                            try:
                                if match.startswith('{'):
                                    json_data = json.loads(match)
                                    extracted_data.update(json_data)
                                else:
                                    # Simple string match
                                    if 'business' in pattern.lower():
                                        extracted_data['business_id'] = match
                                    elif 'name' in pattern.lower():
                                        extracted_data['business_name'] = match
                                    elif 'address' in pattern.lower():
                                        extracted_data['address'] = match
                                    elif 'phone' in pattern.lower():
                                        extracted_data['phone'] = match
                            except:
                                continue
                
                if extracted_data:
                    print(f"✅ {slug}: Extracted data from widget page")
                    return extracted_data
                    
        except Exception as e:
            print(f"❌ {slug}: Error extracting from widget page: {e}")
        
        return None
    
    def search_for_business_info(self, slug):
        """Search for business information using various methods"""
        print(f"🔍 Extracting details for: {slug}")
        
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
        
        # Method 1: Try API endpoints
        api_data, api_endpoint = self.try_api_endpoints(slug)
        if api_data:
            business_info['extraction_method'] = f'API: {api_endpoint}'
            business_info['raw_data'] = str(api_data)[:1000]
            
            if isinstance(api_data, dict):
                # Extract common business fields
                business_info['business_name'] = (
                    api_data.get('name', '') or 
                    api_data.get('businessName', '') or 
                    api_data.get('companyName', '') or 
                    api_data.get('title', '')
                )
                
                business_info['address'] = (
                    api_data.get('address', '') or 
                    api_data.get('location', '') or 
                    api_data.get('street', '')
                )
                
                business_info['phone'] = (
                    api_data.get('phone', '') or 
                    api_data.get('phoneNumber', '') or 
                    api_data.get('tel', '')
                )
                
                business_info['email'] = (
                    api_data.get('email', '') or 
                    api_data.get('contactEmail', '')
                )
                
                business_info['website'] = (
                    api_data.get('website', '') or 
                    api_data.get('url', '')
                )
                
                business_info['description'] = (
                    api_data.get('description', '') or 
                    api_data.get('about', '') or 
                    api_data.get('bio', '')
                )
                
                if 'services' in api_data:
                    services = api_data['services']
                    if isinstance(services, list):
                        business_info['services'] = ', '.join([str(s) for s in services[:5]])
                    else:
                        business_info['services'] = str(services)[:200]
        
        # Method 2: Extract from widget page
        if not business_info['business_name']:
            widget_data = self.extract_from_widget_page(slug)
            if widget_data:
                if not business_info['extraction_method']:
                    business_info['extraction_method'] = 'Widget Page'
                else:
                    business_info['extraction_method'] += ' + Widget Page'
                
                business_info['business_name'] = widget_data.get('business_name', business_info['business_name'])
                business_info['address'] = widget_data.get('address', business_info['address'])
                business_info['phone'] = widget_data.get('phone', business_info['phone'])
        
        # Method 3: Try common business lookup APIs (if we had the business name)
        if business_info['business_name']:
            # This could be extended to search Google Places API, Yelp API, etc.
            pass
        
        return business_info
    
    def extract_all_details(self, max_workers=5):
        """Extract details for all discovered slugs"""
        print(f"🚀 Starting business details extraction for {len(self.discovered_slugs)} slugs...")
        
        # Process in smaller batches to be respectful
        batch_size = 20
        
        for i in range(0, len(self.discovered_slugs), batch_size):
            batch = self.discovered_slugs[i:i+batch_size]
            print(f"\n📦 Processing batch {i//batch_size + 1} ({len(batch)} slugs)")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all tasks for this batch
                future_to_slug = {
                    executor.submit(self.search_for_business_info, slug): slug 
                    for slug in batch
                }
                
                # Collect results
                for future in as_completed(future_to_slug):
                    slug = future_to_slug[future]
                    try:
                        business_info = future.result()
                        self.business_details.append(business_info)
                    except Exception as e:
                        print(f"❌ Error processing {slug}: {e}")
            
            # Save progress after each batch
            self.save_results()
            print(f"💾 Saved progress: {len(self.business_details)} businesses processed")
            
            # Add delay between batches
            if i + batch_size < len(self.discovered_slugs):
                print("⏳ Waiting 10 seconds before next batch...")
                time.sleep(10)
    
    def save_results(self):
        """Save business details to CSV"""
        if not self.business_details:
            return
        
        fieldnames = [
            'slug', 'url', 'business_name', 'address', 'phone', 'email', 
            'website', 'services', 'location', 'description', 'extraction_method',
            'raw_data', 'extracted_at'
        ]
        
        with open('vsdhone_business_details.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for business in self.business_details:
                # Ensure all fields exist
                for field in fieldnames:
                    if field not in business:
                        business[field] = ''
                writer.writerow(business)
        
        print(f"💾 Saved {len(self.business_details)} business details to vsdhone_business_details.csv")
    
    def generate_summary_report(self):
        """Generate a summary of the extraction results"""
        if not self.business_details:
            return
        
        total = len(self.business_details)
        with_names = len([b for b in self.business_details if b['business_name']])
        with_addresses = len([b for b in self.business_details if b['address']])
        with_phones = len([b for b in self.business_details if b['phone']])
        
        print(f"\n📊 EXTRACTION SUMMARY")
        print(f"{'='*50}")
        print(f"Total businesses processed: {total}")
        print(f"With business names: {with_names} ({with_names/total*100:.1f}%)")
        print(f"With addresses: {with_addresses} ({with_addresses/total*100:.1f}%)")
        print(f"With phone numbers: {with_phones} ({with_phones/total*100:.1f}%)")
        
        # Show extraction methods used
        methods = {}
        for business in self.business_details:
            method = business['extraction_method'] or 'None'
            methods[method] = methods.get(method, 0) + 1
        
        print(f"\nExtraction methods:")
        for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
            print(f"  {method}: {count}")

if __name__ == "__main__":
    extractor = BusinessDetailsExtractor()
    
    if not extractor.discovered_slugs:
        print("❌ No slugs to process. Run discovery first.")
        exit(1)
    
    extractor.extract_all_details(max_workers=3)  # Be conservative with concurrent requests
    extractor.generate_summary_report()
    print("\n🎯 Business details extraction complete!") 