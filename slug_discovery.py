#!/usr/bin/env python3
"""
VSDHOne Slug Discovery Tool
Discovers live brands on Hydreight's VSDHOne platform by brute-force testing slug combinations
"""

import requests
import csv
import time
import random
import string
from itertools import product
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import json
import sys
from datetime import datetime

class VSDHOneDiscovery:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
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
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def generate_slugs(self, pattern='[a-z][a-z][0-9][0-9][a-z]'):
        """Generate slug combinations based on the observed pattern"""
        # Pattern: 2 letters + 2 digits + 1 letter
        letters = string.ascii_lowercase
        digits = string.digits
        
        for combo in product(letters, letters, digits, digits, letters):
            slug = ''.join(combo)
            if slug not in self.known_slugs and slug not in self.tested_slugs:
                yield slug
    
    def test_slug(self, slug):
        """Test if a slug is live and extract data if it is"""
        url = urljoin(self.base_url, slug)
        
        try:
            print(f"Testing: {slug}")
            response = self.session.get(url, timeout=10, allow_redirects=True)
            
            # Mark as tested
            self.tested_slugs.add(slug)
            
            # Check if it's a valid response
            if response.status_code == 200 and not self.is_error_page(response):
                print(f"✅ Found live slug: {slug}")
                brand_data = self.extract_brand_data(slug, response)
                if brand_data:
                    self.found_brands.append(brand_data)
                    self.save_to_csv()  # Save after each find
                return True
            else:
                print(f"❌ {slug} - Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ {slug} - Error: {str(e)}")
            return False
    
    def is_error_page(self, response):
        """Check if the response is an error page"""
        content = response.text.lower()
        error_indicators = [
            '401', 'unauthorized', 'access denied', 
            'not found', '404', 'error', 
            'does not work as expected',
            'invalid request'
        ]
        return any(indicator in content for indicator in error_indicators)
    
    def extract_brand_data(self, slug, response):
        """Extract brand information from the response"""
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Initialize data structure
            brand_data = {
                'slug': slug,
                'url': urljoin(self.base_url, slug),
                'final_url': response.url,
                'title': '',
                'business_name': '',
                'address': '',
                'phone': '',
                'location': '',
                'discovered_at': datetime.now().isoformat(),
                'raw_content_sample': ''
            }
            
            # Extract title
            title_tag = soup.find('title')
            if title_tag:
                brand_data['title'] = title_tag.get_text().strip()
            
            # Try to extract business information from various possible locations
            # Look for business name patterns
            for tag in soup.find_all(['h1', 'h2', 'h3', 'div', 'span']):
                text = tag.get_text().strip()
                if len(text) > 3 and len(text) < 100:
                    if any(keyword in text.lower() for keyword in ['hotel', 'clinic', 'center', 'spa', 'wellness', 'medical']):
                        if not brand_data['business_name']:
                            brand_data['business_name'] = text
            
            # Look for address patterns
            for tag in soup.find_all(['div', 'span', 'p']):
                text = tag.get_text().strip()
                if any(keyword in text.lower() for keyword in ['street', 'avenue', 'road', 'blvd', 'suite', 'floor']):
                    if not brand_data['address']:
                        brand_data['address'] = text
            
            # Look for phone numbers
            for tag in soup.find_all(['div', 'span', 'a']):
                text = tag.get_text().strip()
                if 'phone' in tag.get('class', []) or 'tel' in tag.get('href', ''):
                    brand_data['phone'] = text
                elif any(char.isdigit() for char in text) and len(text) > 7 and len(text) < 20:
                    if '+' in text or '(' in text or '-' in text:
                        if not brand_data['phone']:
                            brand_data['phone'] = text
            
            # Get a sample of the content for manual review
            body_text = soup.get_text()
            brand_data['raw_content_sample'] = body_text[:500] if body_text else ''
            
            return brand_data
            
        except Exception as e:
            print(f"Error extracting data for {slug}: {str(e)}")
            return {
                'slug': slug,
                'url': urljoin(self.base_url, slug),
                'final_url': response.url,
                'error': str(e),
                'discovered_at': datetime.now().isoformat()
            }
    
    def save_to_csv(self):
        """Save found brands to CSV file"""
        if not self.found_brands:
            return
            
        fieldnames = [
            'slug', 'url', 'final_url', 'title', 'business_name', 
            'address', 'phone', 'location', 'discovered_at', 
            'raw_content_sample'
        ]
        
        with open('vsdhone_brands.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for brand in self.found_brands:
                # Ensure all fields exist
                for field in fieldnames:
                    if field not in brand:
                        brand[field] = ''
                writer.writerow(brand)
        
        print(f"💾 Saved {len(self.found_brands)} brands to vsdhone_brands.csv")
    
    def save_progress(self):
        """Save tested slugs to avoid retesting"""
        with open('tested_slugs.txt', 'w') as f:
            for slug in sorted(self.tested_slugs):
                f.write(f"{slug}\n")
    
    def load_progress(self):
        """Load previously tested slugs"""
        try:
            with open('tested_slugs.txt', 'r') as f:
                self.tested_slugs = set(line.strip() for line in f if line.strip())
            print(f"📁 Loaded {len(self.tested_slugs)} previously tested slugs")
        except FileNotFoundError:
            print("📁 No previous progress found, starting fresh")
    
    def run_discovery(self, max_attempts=1000):
        """Run the discovery process"""
        print("🔍 Starting VSDHOne brand discovery...")
        print(f"Known slugs to skip: {len(self.known_slugs)}")
        
        # Load previous progress
        self.load_progress()
        
        attempts = 0
        found_count = 0
        
        try:
            for slug in self.generate_slugs():
                if attempts >= max_attempts:
                    print(f"Reached maximum attempts limit: {max_attempts}")
                    break
                
                attempts += 1
                
                if self.test_slug(slug):
                    found_count += 1
                
                # Add random delay to be respectful
                time.sleep(random.uniform(1, 3))
                
                # Save progress periodically
                if attempts % 50 == 0:
                    self.save_progress()
                    print(f"Progress: {attempts} tested, {found_count} found")
        
        except KeyboardInterrupt:
            print("\n🛑 Discovery interrupted by user")
        
        finally:
            self.save_progress()
            self.save_to_csv()
            print(f"\n🎯 Discovery complete!")
            print(f"   • Total tested: {len(self.tested_slugs)}")
            print(f"   • Brands found: {len(self.found_brands)}")
            print(f"   • Results saved to: vsdhone_brands.csv")

if __name__ == "__main__":
    discovery = VSDHOneDiscovery()
    
    # Allow command line argument for max attempts
    max_attempts = 1000
    if len(sys.argv) > 1:
        try:
            max_attempts = int(sys.argv[1])
        except ValueError:
            print("Invalid max_attempts argument, using default 1000")
    
    discovery.run_discovery(max_attempts=max_attempts) 