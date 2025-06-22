#!/usr/bin/env python3
"""
Enterprise Business Details Collector for VSDHOne - Simplified Version
Visits only ACTIVE enterprise slugs and collects comprehensive business information
Saves data in both CSV and JSON formats without readiness assessment
"""

import json
import csv
import os
import time
import re
import base64
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

class EnterpriseBusinessCollector:
    def __init__(self, instance_id="BIZ_SIMPLE"):
        self.instance_id = instance_id
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/b/"
        self.driver = None
        self.timeout = 15
        self.rate_limit = 5  # requests per second
        
        # Initialize session data
        self.session_data = {
            'session_id': f"{instance_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'total_collected': 0,
                'successful_collections': 0,
                'failed_collections': 0
            },
            'businesses': []
        }
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
    def setup_driver(self):
        """Setup Chrome driver with optimized settings"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--fast-start')
            chrome_options.add_argument('--disable-logging')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            print(f"✅ Chrome driver setup successful")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup Chrome driver: {e}")
            return False
            
    def decode_slug(self, slug):
        """Decode base64 slug to get the number"""
        try:
            padded = slug + '=' * (4 - len(slug) % 4) if len(slug) % 4 else slug
            return int(base64.b64decode(padded).decode())
        except:
            return None
            
    def extract_business_details(self, slug, url):
        """Extract comprehensive business details from a page"""
        try:
            start_time = time.time()
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            load_time = time.time() - start_time
            
            # Get page source and basic info
            page_source = self.driver.page_source.lower()
            original_page_source = self.driver.page_source  # Keep original case for extraction
            page_title = self.driver.title
            final_url = self.driver.current_url
            content_length = len(page_source)
            
            # Extract business details
            business_details = {
                'slug': slug,
                'slug_number': self.decode_slug(slug),
                'original_url': url,
                'final_url': final_url,
                'page_title': page_title,
                'load_time': round(load_time, 2),
                'content_length': content_length,
                'collected_at': datetime.now().isoformat(),
                
                # Business Information
                'business_name': self.extract_business_name(page_source, page_title, original_page_source),
                'business_type': self.extract_business_type(page_source),
                'location_info': self.extract_location_info(original_page_source),
                'contact_info': self.extract_contact_info(original_page_source),
                'services': self.extract_services(page_source),
                'specializations': self.extract_specializations(page_source),
                'business_description': self.extract_business_description(original_page_source),
                'operating_hours': self.extract_operating_hours(original_page_source),
                'pricing_info': self.extract_pricing_info(original_page_source),
                
                # Technical Details
                'redirect_info': self.analyze_redirect(url, final_url),
                'widget_business_slug': self.extract_widget_slug(final_url),
                'page_structure': self.analyze_page_structure(page_source),
                'meta_data': self.extract_meta_data(original_page_source),
                
                # Content Analysis
                'business_indicators': self.count_business_indicators(page_source),
                'error_indicators': self.count_error_indicators(page_source),
                'content_quality': self.assess_content_quality(page_source, page_title),
                'social_media': self.extract_social_media(original_page_source),
                'images_count': self.count_images(original_page_source)
            }
            
            return business_details
            
        except TimeoutException:
            print(f"⏰ TIMEOUT after {self.timeout}s")
            return self.create_error_result(slug, url, "TIMEOUT", f"Page load timeout after {self.timeout}s")
            
        except WebDriverException as e:
            print(f"🌐 CONNECTION_ERROR: {str(e)[:50]}...")
            return self.create_error_result(slug, url, "CONNECTION_ERROR", str(e))
            
        except Exception as e:
            print(f"❌ UNEXPECTED_ERROR: {str(e)[:50]}...")
            return self.create_error_result(slug, url, "UNEXPECTED_ERROR", str(e))
            
    def extract_business_name(self, page_source, page_title, original_source):
        """Extract business name with multiple strategies"""
        # Strategy 1: Use page title if meaningful
        if page_title and len(page_title) > 3 and page_title.lower() not in ['', 'loading', 'error', 'undefined']:
            return page_title
            
        # Strategy 2: Look for specific business patterns
        if 'dripbar' in page_source:
            if 'direct' in page_source:
                return "The DRIPBaR Direct - Location"
            return "The DRIPBaR"
        elif 'renivate' in page_source:
            return "RenIVate"
        elif 'hydrafacial' in page_source:
            return "Hydrafacial at Home"
            
        # Strategy 3: Look for business name in meta tags and headers
        name_patterns = [
            r'<meta[^>]*name=["\']?business[^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']?og:site_name[^>]*content=["\']([^"\']+)["\']',
            r'<h1[^>]*>([^<]{3,100})</h1>',
            r'<h2[^>]*class=[^>]*business[^>]*>([^<]{3,100})</h2>'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, original_source, re.IGNORECASE)
            if matches:
                return matches[0].strip()
                
        return ""
        
    def extract_business_type(self, page_source):
        """Determine business type based on content"""
        if any(term in page_source for term in ['iv', 'drip', 'vitamin', 'therapy', 'wellness']):
            return "IV Therapy/Wellness"
        elif any(term in page_source for term in ['weight loss', 'nutrition', 'diet']):
            return "Weight Loss/Nutrition"
        elif any(term in page_source for term in ['medical', 'health', 'clinic']):
            return "Medical/Health"
        elif any(term in page_source for term in ['beauty', 'spa', 'aesthetic']):
            return "Beauty/Spa"
        elif any(term in page_source for term in ['fitness', 'gym', 'training']):
            return "Fitness/Training"
        else:
            return "Unknown"
            
    def extract_location_info(self, page_source):
        """Extract location information"""
        locations = []
        
        # Look for common location patterns
        location_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\([A-Z]{2}\)',  # City (STATE)
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})',   # City, STATE
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([A-Z]{2})',     # City STATE
            r'(\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln))',  # Street addresses
            r'(\d{5}(?:-\d{4})?)'  # ZIP codes
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, page_source)
            if isinstance(matches[0], tuple) if matches else False:
                locations.extend([' '.join(match) for match in matches])
            else:
                locations.extend(matches)
            
        return list(set(locations))[:10]  # Return up to 10 unique locations
        
    def extract_contact_info(self, page_source):
        """Extract contact information"""
        contact = {}
        
        # Phone numbers
        phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, page_source))
        if phones:
            contact['phones'] = list(set(phones))[:5]
            
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_source)
        if emails:
            contact['emails'] = list(set(emails))[:5]
            
        # Website URLs
        url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        urls = re.findall(url_pattern, page_source)
        if urls:
            # Filter out common CDN/library URLs
            filtered_urls = [url for url in urls if not any(cdn in url for cdn in ['googleapis', 'gstatic', 'jsdelivr', 'unpkg'])]
            contact['websites'] = list(set(filtered_urls))[:5]
            
        return contact
        
    def extract_services(self, page_source):
        """Extract services offered"""
        service_keywords = [
            'iv therapy', 'vitamin drip', 'hydration', 'wellness', 'weight loss',
            'semaglutide', 'tirzepatide', 'injection', 'consultation', 'treatment',
            'therapy', 'massage', 'facial', 'aesthetic', 'medical', 'health',
            'botox', 'filler', 'laser', 'microneedling', 'chemical peel',
            'nutrition', 'diet', 'fitness', 'coaching', 'training'
        ]
        
        found_services = []
        for service in service_keywords:
            if service in page_source:
                found_services.append(service)
                
        return found_services
        
    def extract_specializations(self, page_source):
        """Extract business specializations"""
        specializations = []
        
        if 'weight loss' in page_source and any(drug in page_source for drug in ['semaglutide', 'tirzepatide']):
            specializations.append('GLP-1 Weight Loss')
        if 'iv' in page_source and 'vitamin' in page_source:
            specializations.append('IV Vitamin Therapy')
        if 'hydrafacial' in page_source:
            specializations.append('HydraFacial Treatments')
        if 'dripbar' in page_source:
            specializations.append('DRIPBaR Franchise')
        if 'botox' in page_source or 'filler' in page_source:
            specializations.append('Cosmetic Injections')
        if 'laser' in page_source:
            specializations.append('Laser Treatments')
            
        return specializations
        
    def extract_business_description(self, page_source):
        """Extract business description"""
        description_patterns = [
            r'<meta[^>]*name=["\']?description[^>]*content=["\']([^"\']{20,500})["\']',
            r'<meta[^>]*property=["\']?og:description[^>]*content=["\']([^"\']{20,500})["\']',
            r'<p[^>]*class=[^>]*description[^>]*>([^<]{20,500})</p>'
        ]
        
        for pattern in description_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                return matches[0].strip()
                
        return ""
        
    def extract_operating_hours(self, page_source):
        """Extract operating hours"""
        hours_patterns = [
            r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)[^<\n]*(\d{1,2}:\d{2}[^<\n]*\d{1,2}:\d{2})',
            r'Hours?[^<\n]*(\d{1,2}:\d{2}[^<\n]*\d{1,2}:\d{2})',
            r'Open[^<\n]*(\d{1,2}:\d{2}[^<\n]*\d{1,2}:\d{2})'
        ]
        
        hours = []
        for pattern in hours_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            hours.extend([' '.join(match) if isinstance(match, tuple) else match for match in matches])
            
        return list(set(hours))[:7]  # Max 7 days
        
    def extract_pricing_info(self, page_source):
        """Extract pricing information"""
        price_patterns = [
            r'\$\d+(?:\.\d{2})?',
            r'\d+\s*dollars?',
            r'Price[^<\n]*\$?\d+',
            r'Cost[^<\n]*\$?\d+'
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            prices.extend(matches)
            
        return list(set(prices))[:10]  # Max 10 price mentions
        
    def analyze_redirect(self, original_url, final_url):
        """Analyze URL redirect information"""
        if original_url == final_url:
            return "No redirect"
        elif '/widget-business/' in final_url:
            return f"Redirects to widget-business: {final_url.split('/')[-1]}"
        elif '/widget' in final_url:
            return "Redirects to generic widget"
        else:
            return f"Redirects to: {final_url}"
            
    def extract_widget_slug(self, final_url):
        """Extract widget-business slug if present"""
        if '/widget-business/' in final_url:
            return final_url.split('/')[-1]
        return None
        
    def analyze_page_structure(self, page_source):
        """Analyze page structure and components"""
        structure = {}
        
        structure['has_forms'] = 'form' in page_source
        structure['has_booking'] = any(term in page_source for term in ['book', 'appointment', 'schedule'])
        structure['has_services'] = 'service' in page_source
        structure['has_pricing'] = any(term in page_source for term in ['price', 'cost', '$'])
        structure['has_contact'] = any(term in page_source for term in ['contact', 'phone', 'email'])
        structure['has_location'] = any(term in page_source for term in ['address', 'location', 'directions'])
        structure['script_count'] = page_source.count('<script')
        structure['style_count'] = page_source.count('<style')
        structure['image_count'] = page_source.count('<img')
        structure['link_count'] = page_source.count('<a')
        
        return structure
        
    def extract_meta_data(self, page_source):
        """Extract meta data from page"""
        meta_data = {}
        
        meta_patterns = {
            'keywords': r'<meta[^>]*name=["\']?keywords[^>]*content=["\']([^"\']+)["\']',
            'author': r'<meta[^>]*name=["\']?author[^>]*content=["\']([^"\']+)["\']',
            'viewport': r'<meta[^>]*name=["\']?viewport[^>]*content=["\']([^"\']+)["\']',
            'robots': r'<meta[^>]*name=["\']?robots[^>]*content=["\']([^"\']+)["\']'
        }
        
        for key, pattern in meta_patterns.items():
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                meta_data[key] = matches[0]
                
        return meta_data
        
    def extract_social_media(self, page_source):
        """Extract social media links"""
        social_patterns = {
            'facebook': r'https?://(?:www\.)?facebook\.com/[^"\s<>]+',
            'instagram': r'https?://(?:www\.)?instagram\.com/[^"\s<>]+',
            'twitter': r'https?://(?:www\.)?twitter\.com/[^"\s<>]+',
            'linkedin': r'https?://(?:www\.)?linkedin\.com/[^"\s<>]+',
            'youtube': r'https?://(?:www\.)?youtube\.com/[^"\s<>]+'
        }
        
        social_media = {}
        for platform, pattern in social_patterns.items():
            matches = re.findall(pattern, page_source, re.IGNORECASE)
            if matches:
                social_media[platform] = matches[0]
                
        return social_media
        
    def count_images(self, page_source):
        """Count images on the page"""
        return len(re.findall(r'<img[^>]*>', page_source, re.IGNORECASE))
        
    def count_business_indicators(self, page_source):
        """Count business-related indicators"""
        indicators = [
            'service', 'appointment', 'book', 'schedule', 'consultation',
            'treatment', 'therapy', 'wellness', 'health', 'medical',
            'contact', 'phone', 'email', 'address', 'location'
        ]
        return sum(1 for indicator in indicators if indicator in page_source)
        
    def count_error_indicators(self, page_source):
        """Count error-related indicators"""
        indicators = ['error', 'not found', '404', '500', 'unavailable', 'maintenance']
        return sum(1 for indicator in indicators if indicator in page_source)
        
    def assess_content_quality(self, page_source, page_title):
        """Assess overall content quality"""
        if len(page_source) > 50000 and page_title and self.count_business_indicators(page_source) > 5:
            return "High"
        elif len(page_source) > 30000 and page_title:
            return "Medium"
        else:
            return "Low"
            
    def create_error_result(self, slug, url, error_type, error_message):
        """Create error result structure"""
        return {
            'slug': slug,
            'slug_number': self.decode_slug(slug),
            'original_url': url,
            'final_url': '',
            'page_title': '',
            'load_time': 0,
            'content_length': 0,
            'collected_at': datetime.now().isoformat(),
            'business_name': '',
            'business_type': '',
            'location_info': [],
            'contact_info': {},
            'services': [],
            'specializations': [],
            'business_description': '',
            'operating_hours': [],
            'pricing_info': [],
            'redirect_info': '',
            'widget_business_slug': None,
            'page_structure': {},
            'meta_data': {},
            'business_indicators': 0,
            'error_indicators': 1,
            'content_quality': 'Error',
            'social_media': {},
            'images_count': 0,
            'error_type': error_type,
            'error_message': error_message
        }
        
    def save_results(self):
        """Save results in both CSV and JSON formats"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON
        json_filename = f"logs/ENTERPRISE_BUSINESS_SIMPLE_{self.session_data['session_id']}_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)
            
        # Save CSV
        if self.session_data['businesses']:
            csv_filename = f"logs/ENTERPRISE_BUSINESS_SIMPLE_{self.session_data['session_id']}_{timestamp}.csv"
            
            # Define CSV fieldnames
            fieldnames = [
                'slug', 'slug_number', 'original_url', 'final_url', 'page_title',
                'business_name', 'business_type', 'location_info', 'contact_info',
                'services', 'specializations', 'business_description', 'operating_hours',
                'pricing_info', 'redirect_info', 'widget_business_slug', 'page_structure',
                'meta_data', 'business_indicators', 'error_indicators', 'content_quality',
                'social_media', 'images_count', 'load_time', 'content_length',
                'collected_at', 'error_type', 'error_message'
            ]
            
            with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for business in self.session_data['businesses']:
                    # Convert lists and dicts to strings for CSV
                    row = business.copy()
                    for key in ['location_info', 'contact_info', 'services', 'specializations', 
                               'operating_hours', 'pricing_info', 'page_structure', 'meta_data', 'social_media']:
                        if key in row:
                            row[key] = str(row[key]) if row[key] else ''
                    writer.writerow(row)
                    
        print(f"📊 Results saved:")
        print(f"   JSON: {json_filename}")
        if self.session_data['businesses']:
            print(f"   CSV: {csv_filename}")
            
    def collect_business_details(self, slugs_file):
        """Collect business details for all active slugs"""
        # Load active slugs
        with open(slugs_file, 'r') as f:
            slugs = [line.strip() for line in f if line.strip()]
            
        print(f"🚀 Starting Enterprise Business Details Collection (Simplified)")
        print(f"📍 Base URL: {self.base_url}")
        print(f"🎯 Total active slugs to collect: {len(slugs)}")
        print(f"⚡ Rate limit: {self.rate_limit} requests/second")
        print("=" * 70)
        
        if not self.setup_driver():
            print("❌ Failed to setup driver, aborting collection")
            return
            
        try:
            for i, slug in enumerate(slugs, 1):
                # Rate limiting
                if i > 1:
                    time.sleep(1.0 / self.rate_limit)
                    
                print(f"🔍 [{i}/{len(slugs)}] Collecting: {slug}", end=" ", flush=True)
                
                # Collect business details
                url = f"{self.base_url}{slug}"
                details = self.extract_business_details(slug, url)
                self.session_data['businesses'].append(details)
                
                # Update statistics
                self.session_data['stats']['total_collected'] += 1
                
                if 'error_type' in details:
                    self.session_data['stats']['failed_collections'] += 1
                    print(f"❌ {details['error_type']}")
                else:
                    self.session_data['stats']['successful_collections'] += 1
                    business_name = details['business_name'] or 'Unknown'
                    business_type = details['business_type'] or 'Unknown'
                    print(f"✅ {business_name} ({business_type})")
                        
                # Save progress every 25 collections
                if i % 25 == 0:
                    self.save_results()
                    stats = self.session_data['stats']
                    print(f"\n📊 Progress Report [{i}/{len(slugs)}]:")
                    print(f"   ✅ Successful: {stats['successful_collections']}")
                    print(f"   ❌ Failed: {stats['failed_collections']}")
                    print(f"   📈 Success Rate: {(stats['successful_collections']/stats['total_collected']*100):.1f}%")
                    print("   " + "="*50)
                    
        except KeyboardInterrupt:
            print(f"\n⚠️  Collection interrupted by user at {i}/{len(slugs)}")
            
        finally:
            # Final save and cleanup
            self.save_results()
            if self.driver:
                self.driver.quit()
                
            # Print final statistics
            stats = self.session_data['stats']
            print(f"\n🎯 FINAL RESULTS:")
            print(f"   📊 Total Collected: {stats['total_collected']}")
            print(f"   ✅ Successful: {stats['successful_collections']}")
            print(f"   ❌ Failed: {stats['failed_collections']}")
            print(f"   📈 Success Rate: {(stats['successful_collections']/stats['total_collected']*100):.1f}%")

def main():
    collector = EnterpriseBusinessCollector()
    slugs_file = "enterprise_active_slugs_for_collection.txt"
    
    if not os.path.exists(slugs_file):
        print(f"❌ Slugs file not found: {slugs_file}")
        print("Please run the active slugs extraction first.")
        return
        
    collector.collect_business_details(slugs_file)

if __name__ == "__main__":
    main() 