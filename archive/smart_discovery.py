#!/usr/bin/env python3
"""
Smart VSDHOne Discovery Tool
Uses targeted patterns and API monitoring to find valid business slugs more efficiently
"""

import requests
import csv
import time
import random
import string
from itertools import product
from datetime import datetime
import sys
import re

class SmartVSDHOneDiscovery:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        self.api_base = "https://vsdigital-bookingwidget-prod.azurewebsites.net/api/"
        self.known_slugs = {
            'ad31y', 'mj42f', 'os27m', 'lp56a', 'zb74k', 'ym99l', 
            'yh52b', 'zd20w', 'td32z', 'bo19e', 'bh70s', 'ai04u', 
            'bm49t', 'qu29u', 'tc33l'
        }
        self.tested_slugs = set()
        self.found_brands = []
        self.session = requests.Session()
        
        # Add headers to look like a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def analyze_known_patterns(self):
        """Analyze known slugs to find patterns and likely character distributions"""
        print("🔍 Analyzing known slug patterns...")
        
        patterns = {
            'first_letters': {},
            'second_letters': {},
            'first_digits': {},
            'second_digits': {},
            'last_letters': {}
        }
        
        for slug in self.known_slugs:
            if len(slug) == 5:
                patterns['first_letters'][slug[0]] = patterns['first_letters'].get(slug[0], 0) + 1
                patterns['second_letters'][slug[1]] = patterns['second_letters'].get(slug[1], 0) + 1
                patterns['first_digits'][slug[2]] = patterns['first_digits'].get(slug[2], 0) + 1
                patterns['second_digits'][slug[3]] = patterns['second_digits'].get(slug[3], 0) + 1
                patterns['last_letters'][slug[4]] = patterns['last_letters'].get(slug[4], 0) + 1
        
        print("📊 Character frequency analysis:")
        for pos, freq in patterns.items():
            sorted_chars = sorted(freq.items(), key=lambda x: x[1], reverse=True)
            print(f"  {pos}: {sorted_chars}")
        
        return patterns
    
    def generate_smart_slugs(self, patterns, max_slugs=1000):
        """Generate slugs using weighted probability based on known patterns"""
        print(f"🎯 Generating {max_slugs} smart slug candidates...")
        
        # Create weighted character lists
        def get_weighted_chars(char_freq, default_chars):
            if not char_freq:
                return list(default_chars)
            
            # Create a weighted list where more frequent chars appear more often
            weighted = []
            for char, freq in char_freq.items():
                weighted.extend([char] * (freq * 3))  # Multiply by 3 for stronger weighting
            
            # Add all possible characters but with lower frequency
            for char in default_chars:
                if char not in weighted:
                    weighted.append(char)
            
            return weighted
        
        letters = string.ascii_lowercase
        digits = string.digits
        
        first_letters = get_weighted_chars(patterns['first_letters'], letters)
        second_letters = get_weighted_chars(patterns['second_letters'], letters)
        first_digits = get_weighted_chars(patterns['first_digits'], digits)
        second_digits = get_weighted_chars(patterns['second_digits'], digits)
        last_letters = get_weighted_chars(patterns['last_letters'], letters)
        
        generated = set()
        
        # Generate weighted random combinations
        while len(generated) < max_slugs:
            slug = (
                random.choice(first_letters) +
                random.choice(second_letters) +
                random.choice(first_digits) +
                random.choice(second_digits) +
                random.choice(last_letters)
            )
            
            if slug not in self.known_slugs and slug not in self.tested_slugs:
                generated.add(slug)
        
        return list(generated)
    
    def test_api_endpoints(self, slug):
        """Test various API endpoints that might reveal if a slug is valid"""
        api_endpoints = [
            f"business/{slug}",
            f"business/{slug}/info",
            f"business/{slug}/config",
            f"business/{slug}/settings",
            f"booking/{slug}",
            f"widget/{slug}",
            f"config/{slug}",
            f"v1/business/{slug}",
            f"v1/widget/{slug}",
        ]
        
        for endpoint in api_endpoints:
            try:
                url = f"{self.api_base}{endpoint}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data and isinstance(data, dict):
                            print(f"📡 API hit: {endpoint} returned data")
                            return True, data
                    except:
                        # Not JSON, but 200 response might still be valid
                        if len(response.text) > 100:
                            print(f"📡 API hit: {endpoint} returned content")
                            return True, response.text
                
            except Exception as e:
                continue
        
        return False, None
    
    def test_slug_comprehensive(self, slug):
        """Comprehensive test using multiple methods"""
        print(f"🔍 Testing: {slug}")
        
        # Mark as tested
        self.tested_slugs.add(slug)
        
        # Method 1: API endpoint testing
        api_valid, api_data = self.test_api_endpoints(slug)
        if api_valid:
            print(f"✅ Found via API: {slug}")
            brand_data = self.extract_api_data(slug, api_data)
            if brand_data:
                self.found_brands.append(brand_data)
                self.save_to_csv()
            return True
        
        # Method 2: Direct URL analysis (look for different response patterns)
        try:
            url = f"{self.base_url}{slug}"
            response = self.session.get(url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                # Look for subtle differences in the response
                indicators = self.analyze_response_deeply(response, slug)
                
                if indicators['likely_valid']:
                    print(f"✅ Found via deep analysis: {slug}")
                    brand_data = self.extract_response_data(slug, response, indicators)
                    if brand_data:
                        self.found_brands.append(brand_data)
                        self.save_to_csv()
                    return True
        
        except Exception as e:
            print(f"❌ {slug} - Error: {str(e)}")
        
        print(f"❌ {slug} - No valid indicators found")
        return False
    
    def analyze_response_deeply(self, response, slug):
        """Deep analysis of response to find subtle differences"""
        indicators = {
            'likely_valid': False,
            'reasons': []
        }
        
        # Check response headers for differences
        headers = response.headers
        if 'X-Business-Id' in headers or 'X-Widget-Config' in headers:
            indicators['likely_valid'] = True
            indicators['reasons'].append('Business headers found')
        
        # Check for different JavaScript bundle hashes or configurations
        content = response.text
        
        # Look for business-specific configuration in JavaScript
        business_config_patterns = [
            r'businessId["\']?\s*:\s*["\']([^"\']+)["\']',
            r'business_id["\']?\s*:\s*["\']([^"\']+)["\']',
            r'widgetConfig["\']?\s*:\s*\{[^}]+\}',
            r'config["\']?\s*:\s*\{[^}]*business[^}]*\}',
        ]
        
        for pattern in business_config_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                indicators['likely_valid'] = True
                indicators['reasons'].append(f'Config pattern found: {pattern}')
                break
        
        # Check for different bundle URLs or hashes
        bundle_pattern = r'/static/js/([a-f0-9]+)\.chunk\.js'
        bundles = re.findall(bundle_pattern, content)
        
        # Compare with a known invalid response
        if hasattr(self, '_base_bundles'):
            if set(bundles) != self._base_bundles:
                indicators['likely_valid'] = True
                indicators['reasons'].append('Different JS bundles loaded')
        else:
            self._base_bundles = set(bundles)
        
        # Look for business-specific CSS or assets
        if f'business/{slug}' in content or f'widget/{slug}' in content:
            indicators['likely_valid'] = True
            indicators['reasons'].append('Slug-specific references found')
        
        return indicators
    
    def extract_api_data(self, slug, api_data):
        """Extract business data from API response"""
        brand_data = {
            'slug': slug,
            'url': f"{self.base_url}{slug}",
            'discovery_method': 'API',
            'business_name': '',
            'address': '',
            'phone': '',
            'services': '',
            'discovered_at': datetime.now().isoformat(),
            'api_data': str(api_data)[:500]  # Truncate for CSV
        }
        
        # Extract information from API data
        if isinstance(api_data, dict):
            brand_data['business_name'] = api_data.get('name', '') or api_data.get('businessName', '')
            brand_data['address'] = api_data.get('address', '') or api_data.get('location', '')
            brand_data['phone'] = api_data.get('phone', '') or api_data.get('phoneNumber', '')
            
            if 'services' in api_data:
                services = api_data['services']
                if isinstance(services, list):
                    brand_data['services'] = ', '.join([str(s) for s in services[:5]])
                else:
                    brand_data['services'] = str(services)[:100]
        
        return brand_data
    
    def extract_response_data(self, slug, response, indicators):
        """Extract data from response analysis"""
        return {
            'slug': slug,
            'url': f"{self.base_url}{slug}",
            'final_url': response.url,
            'discovery_method': 'Response Analysis',
            'business_name': '',
            'address': '',
            'phone': '',
            'services': '',
            'discovered_at': datetime.now().isoformat(),
            'indicators': str(indicators)
        }
    
    def save_to_csv(self):
        """Save found brands to CSV file"""
        if not self.found_brands:
            return
            
        fieldnames = [
            'slug', 'url', 'final_url', 'discovery_method', 'business_name', 
            'address', 'phone', 'services', 'discovered_at', 'api_data', 'indicators'
        ]
        
        with open('vsdhone_brands_smart.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for brand in self.found_brands:
                # Ensure all fields exist
                for field in fieldnames:
                    if field not in brand:
                        brand[field] = ''
                writer.writerow(brand)
        
        print(f"💾 Saved {len(self.found_brands)} brands to vsdhone_brands_smart.csv")
    
    def save_progress(self):
        """Save tested slugs to avoid retesting"""
        with open('tested_slugs_smart.txt', 'w') as f:
            for slug in sorted(self.tested_slugs):
                f.write(f"{slug}\n")
    
    def load_progress(self):
        """Load previously tested slugs"""
        try:
            with open('tested_slugs_smart.txt', 'r') as f:
                self.tested_slugs = set(line.strip() for line in f if line.strip())
            print(f"📁 Loaded {len(self.tested_slugs)} previously tested slugs")
        except FileNotFoundError:
            print("📁 No previous progress found, starting fresh")
    
    def run_discovery(self, max_attempts=200):
        """Run the smart discovery process"""
        print("🧠 Starting smart VSDHOne brand discovery...")
        print(f"Known slugs to skip: {len(self.known_slugs)}")
        
        # Load previous progress
        self.load_progress()
        
        # Analyze patterns from known slugs
        patterns = self.analyze_known_patterns()
        
        # Generate smart slug candidates
        candidates = self.generate_smart_slugs(patterns, max_attempts)
        
        attempts = 0
        found_count = 0
        
        try:
            for slug in candidates:
                if attempts >= max_attempts:
                    print(f"Reached maximum attempts limit: {max_attempts}")
                    break
                
                attempts += 1
                
                if self.test_slug_comprehensive(slug):
                    found_count += 1
                
                # Add random delay to be respectful
                time.sleep(random.uniform(1, 2))
                
                # Save progress periodically
                if attempts % 20 == 0:
                    self.save_progress()
                    print(f"Progress: {attempts} tested, {found_count} found")
        
        except KeyboardInterrupt:
            print("\n🛑 Discovery interrupted by user")
        
        finally:
            self.save_progress()
            self.save_to_csv()
            print(f"\n🎯 Smart discovery complete!")
            print(f"   • Total tested: {len(self.tested_slugs)}")
            print(f"   • Brands found: {len(self.found_brands)}")
            print(f"   • Results saved to: vsdhone_brands_smart.csv")

if __name__ == "__main__":
    discovery = SmartVSDHOneDiscovery()
    
    # Allow command line argument for max attempts
    max_attempts = 200
    if len(sys.argv) > 1:
        try:
            max_attempts = int(sys.argv[1])
        except ValueError:
            print("Invalid max_attempts argument, using default 200")
    
    discovery.run_discovery(max_attempts=max_attempts) 