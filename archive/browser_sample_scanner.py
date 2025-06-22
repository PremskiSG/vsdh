#!/usr/bin/env python3
"""
Browser-Based Sample Scanner for VSDHOne
Uses Selenium to detect actual business content vs 401 error pages
Supports parallel execution with unique file naming
"""

import time
import csv
import json
import random
import string
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Lock

class BrowserSampleScanner:
    def __init__(self, sample_size=1000, instance_id=None):
        # Generate unique instance ID if not provided
        if instance_id is None:
            instance_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        self.instance_id = instance_id
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        
        # Character set: a-z + 0-9
        self.charset = string.ascii_lowercase + string.digits  # 36 characters
        self.total_possible = 36 ** 5  # 60,466,176
        self.sample_size = sample_size
        
        # Known working slugs to skip
        self.known_slugs = {
            'ad31y', 'mj42f', 'os27m', 'lp56a', 'zb74k', 'ym99l', 
            'yh52b', 'zd20w', 'td32z', 'bo19e', 'bh70s', 'ai04u', 
            'bm49t', 'qu29u', 'tc33l'
        }
        
        # Results tracking
        self.found_slugs = []
        self.tested_count = 0
        self.start_time = None
        self.checkpoint_interval = 50  # Save checkpoint every 50 slugs
        
        # Configuration for browser automation
        self.page_load_timeout = 15  # Seconds to wait for page load
        self.requests_per_second = 0.5  # Very conservative for browser automation
        
        # Unique file names for parallel execution
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_file = f"browser_sample_results_{self.instance_id}_{timestamp}.csv"
        self.checkpoint_file = f"browser_sample_checkpoint_{self.instance_id}_{timestamp}.json"
        self.progress_file = f"browser_sample_progress_{self.instance_id}_{timestamp}.json"
        
        print(f"🌐 Browser-Based Sample Scanner (Instance: {self.instance_id})")
        print(f"📊 Testing {sample_size:,} random combinations ({sample_size/self.total_possible*100:.4f}% of total)")
        print(f"🔄 Rate limit: {self.requests_per_second} pages/second")
        print(f"📍 Checkpoint every: {self.checkpoint_interval} slugs")
        print(f"💾 Results file: {self.results_file}")
        print(f"📍 Checkpoint file: {self.checkpoint_file}")
        print("")
    
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        options = Options()
        options.add_argument('--headless')  # Run in background
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')  # Suppress console logs
        
        # Add unique user data dir for parallel execution
        user_data_dir = f"/tmp/chrome_user_data_{self.instance_id}_{os.getpid()}"
        options.add_argument(f'--user-data-dir={user_data_dir}')
        
        return webdriver.Chrome(options=options)
    
    def generate_random_slug(self):
        """Generate a random 5-character slug"""
        return ''.join(random.choices(self.charset, k=5))
    
    def generate_sample_slugs(self):
        """Generate sample slugs using mixed strategies"""
        sample_slugs = set()
        
        # Strategy 1: Pure random (50% of sample)
        random_count = self.sample_size // 2
        print(f"🎲 Generating {random_count} pure random slugs...")
        while len(sample_slugs) < random_count:
            slug = self.generate_random_slug()
            if slug not in self.known_slugs:
                sample_slugs.add(slug)
        
        # Strategy 2: Pattern-based (25% of sample)
        pattern_count = self.sample_size // 4
        print(f"🔍 Generating {pattern_count} pattern-based slugs...")
        
        # Common patterns from known slugs
        common_first = ['a', 'b', 't', 'y', 'z', 'm', 'o', 'l']
        common_second = ['d', 'h', 'm', 'i', 'o', 'c']
        common_first_digit = ['0', '1', '2', '3', '4', '5', '7']
        common_last_digit = ['0', '1', '2', '4', '9']
        common_last = ['a', 'b', 'e', 'f', 'k', 'l', 'm', 's', 't', 'u', 'w', 'y', 'z']
        
        while len(sample_slugs) < random_count + pattern_count:
            slug = (
                random.choice(common_first) +
                random.choice(common_second) +
                random.choice(common_first_digit) +
                random.choice(common_last_digit) +
                random.choice(common_last)
            )
            if slug not in self.known_slugs:
                sample_slugs.add(slug)
        
        # Strategy 3: Fill remaining with random
        while len(sample_slugs) < self.sample_size:
            slug = self.generate_random_slug()
            if slug not in self.known_slugs:
                sample_slugs.add(slug)
        
        return list(sample_slugs)[:self.sample_size]
    
    def test_slug_with_browser(self, slug, current_index, total_slugs):
        """Test a single slug using browser automation"""
        print(f"🔍 [{current_index:,}/{total_slugs:,}] Testing: {slug} ({current_index/total_slugs*100:.2f}%)")
        
        driver = self.setup_driver()
        
        try:
            url = f"{self.base_url}{slug}"
            print(f"   🌐 Loading: {url}")
            
            start_time = time.time()
            driver.get(url)
            
            # Wait for page to fully load and JavaScript to execute
            time.sleep(8)  # Give React time to load and render
            
            load_time = time.time() - start_time
            final_url = driver.current_url
            page_title = driver.title
            
            # Get page content after JavaScript execution
            try:
                body_element = driver.find_element(By.TAG_NAME, 'body')
                page_text = body_element.text.strip()
            except:
                page_text = ""
            
            # Analyze the content
            page_text_lower = page_text.lower()
            
            # Business content indicators
            business_indicators = [
                'appointment', 'booking', 'schedule', 'clinic', 'medical', 
                'health', 'therapy', 'treatment', 'service', 'price', 
                'location', 'contact', 'phone', 'doctor', 'wellness',
                'altura health', 'dripbar', 'weight loss', 'injection'
            ]
            
            # Error page indicators
            error_indicators = [
                '401', 'error', 'nothing left to do here', 'go to homepage',
                'not found', 'access denied'
            ]
            
            # Count indicators
            business_count = sum(1 for indicator in business_indicators if indicator in page_text_lower)
            error_count = sum(1 for indicator in error_indicators if indicator in page_text_lower)
            
            # Determine page type
            is_error_page = (
                '401' in page_text_lower or 
                'nothing left to do here' in page_text_lower or
                error_count > 0
            )
            
            is_business_page = (
                business_count >= 3 and 
                not is_error_page and
                len(page_text) > 100
            )
            
            # Classification and output
            if is_error_page:
                print(f"   🚫 401 ERROR PAGE - Error indicators: {error_count}")
                classification = "401_ERROR"
            elif is_business_page:
                print(f"   🌟 ACTIVE BUSINESS PAGE - Business indicators: {business_count}")
                classification = "ACTIVE_BUSINESS"
            elif len(page_text) < 50:
                print(f"   ⚠️  MINIMAL CONTENT - {len(page_text)} chars")
                classification = "MINIMAL_CONTENT"
            else:
                print(f"   ❓ UNCLEAR - Business: {business_count}, Error: {error_count}")
                classification = "UNCLEAR"
            
            # Show some content for verification
            preview_text = page_text[:150].replace('\n', ' ').replace('\r', ' ')
            print(f"   📄 Content preview: {preview_text}")
            
            return {
                'slug': slug,
                'url': url,
                'final_url': final_url,
                'classification': classification,
                'business_indicators': business_count,
                'error_indicators': error_count,
                'page_title': page_title,
                'content_length': len(page_text),
                'load_time': load_time,
                'content_preview': page_text[:200],
                'tested_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"   ❌ Browser Error: {str(e)[:100]}")
            return {
                'slug': slug,
                'url': f"{self.base_url}{slug}",
                'classification': 'ERROR',
                'error': str(e),
                'tested_at': datetime.now().isoformat()
            }
        finally:
            try:
                driver.quit()
            except:
                pass
    
    def save_checkpoint(self, current_index, total_slugs, all_results, remaining_slugs):
        """Save checkpoint with current progress"""
        checkpoint_data = {
            'instance_id': self.instance_id,
            'current_index': current_index,
            'total_slugs': total_slugs,
            'results_count': len(all_results),
            'timestamp': datetime.now().isoformat(),
            'remaining_slugs': remaining_slugs,
            'active_business_found': len([r for r in all_results if r.get('classification') == 'ACTIVE_BUSINESS']),
            'error_pages_found': len([r for r in all_results if r.get('classification') == '401_ERROR'])
        }
        
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        print(f"💾 Checkpoint saved: {current_index}/{total_slugs} processed")
    
    def save_results(self, results):
        """Save results to CSV"""
        if not results:
            return
        
        # Get all field names
        all_fields = set()
        for result in results:
            all_fields.update(result.keys())
        
        fieldnames = sorted(list(all_fields))
        
        with open(self.results_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"💾 Saved {len(results)} results to {self.results_file}")
    
    def scan_sample(self):
        """Main sampling function with browser automation"""
        self.start_time = datetime.now()
        print(f"🚀 Starting browser sample scan at {self.start_time}")
        print(f"📍 Instance ID: {self.instance_id}")
        print(f"📊 Will save checkpoint every {self.checkpoint_interval} slugs\n")
        
        # Generate sample slugs
        sample_slugs = self.generate_sample_slugs()
        total_slugs = len(sample_slugs)
        print(f"✅ Generated {total_slugs} unique sample slugs\n")
        
        all_results = []
        active_business_count = 0
        error_page_count = 0
        
        # Process slugs one by one
        for i, slug in enumerate(sample_slugs):
            current_index = i + 1
            
            # Test slug with browser
            result = self.test_slug_with_browser(slug, current_index, total_slugs)
            all_results.append(result)
            
            # Track classifications
            if result.get('classification') == 'ACTIVE_BUSINESS':
                active_business_count += 1
            elif result.get('classification') == '401_ERROR':
                error_page_count += 1
            
            # Rate limiting for browser automation
            time.sleep(1.0 / self.requests_per_second)
            
            # Checkpoint every N slugs
            if current_index % self.checkpoint_interval == 0:
                remaining_slugs = sample_slugs[current_index:] if current_index < len(sample_slugs) else []
                self.save_checkpoint(current_index, total_slugs, all_results, remaining_slugs)
                print(f"📊 CHECKPOINT SUMMARY:")
                print(f"   • Processed: {current_index:,}/{total_slugs:,} ({current_index/total_slugs*100:.1f}%)")
                print(f"   • Active business pages: {active_business_count}")
                print(f"   • 401 error pages: {error_page_count}")
                print(f"   • Time elapsed: {datetime.now() - self.start_time}")
                print("")
            
            # Show progress every 100 slugs
            elif current_index % 100 == 0:
                elapsed = datetime.now() - self.start_time
                rate = current_index / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
                eta = (total_slugs - current_index) / rate if rate > 0 else 0
                print(f"📈 PROGRESS UPDATE:")
                print(f"   • {current_index:,}/{total_slugs:,} ({current_index/total_slugs*100:.1f}%)")
                print(f"   • Rate: {rate:.1f} slugs/sec")
                print(f"   • ETA: {eta/60:.1f} minutes")
                print(f"   • Active businesses: {active_business_count}")
                print("")
        
        # Final save
        self.save_checkpoint(total_slugs, total_slugs, all_results, [])
        self.save_results(all_results)
        self.print_summary(all_results)
    
    def print_summary(self, results):
        """Print final summary"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print(f"\n🎯 BROWSER SAMPLE SCAN COMPLETE (Instance: {self.instance_id})")
        print(f"=" * 60)
        print(f"⏱️  Duration: {duration}")
        print(f"📊 Sample size: {len(results):,}")
        
        # Classification breakdown
        classifications = {}
        for result in results:
            cls = result.get('classification', 'UNKNOWN')
            classifications[cls] = classifications.get(cls, 0) + 1
        
        print(f"\n📋 CLASSIFICATION BREAKDOWN:")
        for cls, count in classifications.items():
            percentage = (count / len(results)) * 100
            print(f"   {cls}: {count} ({percentage:.1f}%)")
        
        # Show active business pages found
        active_businesses = [r for r in results if r.get('classification') == 'ACTIVE_BUSINESS']
        if active_businesses:
            print(f"\n🌟 ACTIVE BUSINESS PAGES FOUND ({len(active_businesses)}):")
            for business in active_businesses:
                print(f"   • {business['slug']}: {business.get('business_indicators', 0)} indicators")
        
        print(f"\n💾 Results saved to: {self.results_file}")

def main():
    print("🌐 VSDHOne Browser-Based Sample Scanner")
    print("=" * 50)
    
    # Get parameters
    sample_size = input("Enter sample size (default 1000): ").strip()
    if not sample_size:
        sample_size = 1000
    else:
        sample_size = int(sample_size)
    
    instance_id = input("Enter instance ID for parallel runs (default: auto): ").strip()
    if not instance_id:
        instance_id = None
    
    scanner = BrowserSampleScanner(sample_size, instance_id)
    scanner.scan_sample()

if __name__ == "__main__":
    main() 