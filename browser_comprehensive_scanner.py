#!/usr/bin/env python3
"""
Browser-Based Comprehensive Scanner for VSDHOne
Scans all 60,466,176 combinations using browser automation
Supports parallel execution with range-based distribution
"""

import time
import csv
import json
import random
import string
import itertools
import os
import sys
import signal
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from threading import Lock

class BrowserComprehensiveScanner:
    def __init__(self, instance_id=None, start_range=None, end_range=None):
        # Generate unique instance ID if not provided
        if instance_id is None:
            instance_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        self.instance_id = instance_id
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        
        # Character set: 0-9 + a-z (ASCII order for proper string comparison)
        self.charset = string.digits + string.ascii_lowercase  # 36 characters
        self.total_combinations = 36 ** 5  # 60,466,176
        
        # Range handling for parallel execution
        self.start_range = start_range or 'aaaaa'
        self.end_range = end_range or 'zzzzz'
        
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
        self.requests_per_second = 0.3  # Very conservative for browser automation
        
        # Unique file names for parallel execution
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_file = f"browser_comprehensive_results_{self.instance_id}_{timestamp}.csv"
        self.checkpoint_file = f"browser_comprehensive_checkpoint_{self.instance_id}_{timestamp}.txt"
        self.progress_file = f"browser_comprehensive_progress_{self.instance_id}_{timestamp}.json"
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print(f"🌐 Browser-Based Comprehensive Scanner (Instance: {self.instance_id})")
        print(f"📊 Range: {self.start_range} to {self.end_range}")
        print(f"🔄 Rate limit: {self.requests_per_second} pages/second")
        print(f"📍 Checkpoint every: {self.checkpoint_interval} slugs")
        print(f"💾 Results file: {self.results_file}")
        print(f"📍 Checkpoint file: {self.checkpoint_file}")
        print("")
    
    def signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        print(f"\n🛑 Received signal {signum}. Saving progress...")
        self.save_progress()
        self.save_results()
        print("✅ Progress saved. Exiting...")
        sys.exit(0)
    
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
        options.add_argument('--disable-images')  # Save bandwidth
        options.add_argument('--disable-javascript-harmony-shipping')
        
        # Add unique user data dir for parallel execution
        user_data_dir = f"/tmp/chrome_user_data_{self.instance_id}_{os.getpid()}"
        options.add_argument(f'--user-data-dir={user_data_dir}')
        
        return webdriver.Chrome(options=options)
    
    def generate_range_combinations(self, start_from=None):
        """Generate combinations within specified range"""
        print(f"🔢 Generating combinations from {self.start_range} to {self.end_range}")
        
        started = False
        if start_from:
            print(f"📍 Resuming from: {start_from}")
        
        for combo in itertools.product(self.charset, repeat=5):
            slug = ''.join(combo)
            
            # Check if within range
            if slug < self.start_range:
                continue
            if slug > self.end_range:
                break
            
            # Handle resuming
            if start_from:
                if slug == start_from:
                    started = True
                if not started:
                    continue
            
            yield slug
    
    def test_slug_with_browser(self, slug, current_count):
        """Test a single slug using browser automation"""
        print(f"🔍 [{current_count:,}] Testing: {slug}")
        
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
                'altura health', 'dripbar', 'weight loss', 'injection',
                'semaglutide', 'tirzepatide', 'ozempic', 'mounjaro'
            ]
            
            # Error page indicators
            error_indicators = [
                '401', 'error', 'nothing left to do here', 'go to homepage',
                'not found', 'access denied', 'unauthorized'
            ]
            
            # Count indicators
            business_count = sum(1 for indicator in business_indicators if indicator in page_text_lower)
            error_count = sum(1 for indicator in error_indicators if indicator in page_text_lower)
            
            # Determine page type
            is_error_page = (
                '401' in page_text_lower or 
                'nothing left to do here' in page_text_lower or
                'go to homepage' in page_text_lower or
                error_count > 0
            )
            
            is_business_page = (
                business_count >= 2 and 
                not is_error_page and
                len(page_text) > 100
            )
            
            # Classification and output
            if is_error_page:
                print(f"   🚫 401 ERROR PAGE")
                classification = "401_ERROR"
                return None  # Don't save error pages
            elif is_business_page:
                print(f"   🌟 ACTIVE BUSINESS PAGE - {business_count} indicators!")
                classification = "ACTIVE_BUSINESS"
                
                # This is a find! Return detailed info
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
                    'content_preview': page_text[:300],
                    'tested_at': datetime.now().isoformat()
                }
            else:
                print(f"   ⚠️  UNCLEAR CONTENT - {len(page_text)} chars")
                classification = "UNCLEAR"
                return None  # Don't save unclear results
                
        except Exception as e:
            print(f"   ❌ Browser Error: {str(e)[:100]}")
            return None  # Don't save errors
        finally:
            try:
                driver.quit()
            except:
                pass
    
    def save_progress(self):
        """Save current progress"""
        progress_data = {
            'instance_id': self.instance_id,
            'tested_count': self.tested_count,
            'found_count': len(self.found_slugs),
            'start_time': self.start_time,
            'current_time': datetime.now().isoformat(),
            'range_start': self.start_range,
            'range_end': self.end_range
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def save_results(self):
        """Save found slugs to CSV"""
        if not self.found_slugs:
            print("💾 No active business pages found yet")
            return
        
        fieldnames = ['slug', 'url', 'final_url', 'classification', 'business_indicators', 
                     'error_indicators', 'page_title', 'content_length', 'load_time',
                     'content_preview', 'tested_at']
        
        with open(self.results_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.found_slugs)
        
        print(f"💾 Saved {len(self.found_slugs)} active business pages to {self.results_file}")
    
    def load_checkpoint(self):
        """Load last checkpoint to resume scanning"""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                return f.read().strip()
        return None
    
    def save_checkpoint(self, current_slug):
        """Save current position for resuming"""
        with open(self.checkpoint_file, 'w') as f:
            f.write(current_slug)
    
    def scan_comprehensive_range(self, resume=True):
        """Main scanning function with browser automation"""
        self.start_time = datetime.now().isoformat()
        
        # Check if resuming
        start_from = None
        if resume:
            start_from = self.load_checkpoint()
        
        print(f"🚀 Starting comprehensive browser scan at {self.start_time}")
        print(f"📍 Instance ID: {self.instance_id}")
        print(f"📊 Range: {self.start_range} to {self.end_range}")
        if start_from:
            print(f"📍 Resuming from checkpoint: {start_from}")
        print("")
        
        try:
            for i, slug in enumerate(self.generate_range_combinations(start_from)):
                current_count = i + 1
                self.tested_count = current_count
                
                # Skip known slugs
                if slug in self.known_slugs:
                    print(f"🔍 [{current_count:,}] Testing: {slug}")
                    print(f"   ⏭️  Skipping known working slug")
                else:
                    # Test individual slug with browser
                    result = self.test_slug_with_browser(slug, current_count)
                    if result:
                        self.found_slugs.append(result)
                        print(f"   ✅ SAVED! Total active businesses found: {len(self.found_slugs)}")
                
                # Rate limiting for browser automation
                time.sleep(1.0 / self.requests_per_second)
                
                # Checkpoint every N slugs
                if current_count % self.checkpoint_interval == 0:
                    self.save_checkpoint(slug)
                    
                    elapsed = (datetime.now() - datetime.fromisoformat(self.start_time)).total_seconds()
                    rate = current_count / elapsed if elapsed > 0 else 0
                    
                    print(f"\n📍 CHECKPOINT #{current_count // self.checkpoint_interval}")
                    print(f"📊 Progress: {current_count:,} tested in range")
                    print(f"🌟 Active businesses found: {len(self.found_slugs)}")
                    print(f"⚡ Rate: {rate:.2f} slugs/sec")
                    print(f"💾 Checkpoint saved at: {datetime.now().strftime('%H:%M:%S')}")
                    print("-" * 60)
                    print("")
                    
                    # Save progress and results periodically
                    if current_count % (self.checkpoint_interval * 5) == 0:
                        self.save_progress()
                        self.save_results()
        
        except KeyboardInterrupt:
            print("\n🛑 Scan interrupted by user")
        except Exception as e:
            print(f"❌ Error during scan: {e}")
        finally:
            self.save_progress()
            self.save_results()
            self.print_final_summary()
    
    def print_final_summary(self):
        """Print final scan summary"""
        end_time = datetime.now()
        if self.start_time:
            duration = end_time - datetime.fromisoformat(self.start_time)
        else:
            duration = "Unknown"
        
        print(f"\n🎯 COMPREHENSIVE BROWSER SCAN COMPLETE (Instance: {self.instance_id})")
        print(f"=" * 70)
        print(f"📊 Range scanned: {self.start_range} to {self.end_range}")
        print(f"📊 Total combinations tested: {self.tested_count:,}")
        print(f"🌟 Active business pages found: {len(self.found_slugs)}")
        print(f"⏱️  Scan duration: {duration}")
        print(f"💾 Results saved to: {self.results_file}")
        
        if self.found_slugs:
            print(f"\n🔍 DISCOVERED ACTIVE BUSINESS PAGES:")
            for result in self.found_slugs:
                print(f"  • {result['slug']}: {result['business_indicators']} indicators - {result['content_length']} chars")
        else:
            print(f"\n❌ No active business pages found in range {self.start_range} to {self.end_range}")

def get_range_for_instance(instance_num, total_instances=3):
    """Calculate range for parallel execution"""
    # charset = '0123456789abcdefghijklmnopqrstuvwxyz' (36 chars)
    # Split into 3 logical ranges based on new charset order:
    # Instance 1: 0-9 (all numeric combinations)
    # Instance 2: a-m (first half of letters)
    # Instance 3: n-z (second half of letters)
    
    if instance_num == 1:
        # All numeric combinations: 00000-99999
        start_range = '00000'
        end_range = '99999'
    elif instance_num == 2:
        # First half of letters: a-m
        start_range = 'aaaaa'
        end_range = 'mzzzz'
    else:  # instance 3
        # Second half of letters: n-z
        start_range = 'naaaa'
        end_range = 'zzzzz'
    
    return start_range, end_range

def main():
    print("🌐 VSDHOne Browser-Based Comprehensive Scanner")
    print("=" * 60)
    
    # Get parameters
    instance_id = input("Enter instance ID (default: auto): ").strip()
    if not instance_id:
        instance_id = None
    
    use_predefined_range = input("Use predefined range for parallel execution? (1/2/3 or custom): ").strip()
    
    if use_predefined_range in ['1', '2', '3']:
        instance_num = int(use_predefined_range)
        start_range, end_range = get_range_for_instance(instance_num)
        print(f"📊 Instance {instance_num} will scan: {start_range} to {end_range}")
    else:
        start_range = input("Enter start range (default: aaaaa): ").strip() or 'aaaaa'
        end_range = input("Enter end range (default: zzzzz): ").strip() or 'zzzzz'
    
    print(f"\n⚠️  WARNING: Browser-based scanning is VERY slow!")
    print(f"⚠️  Range {start_range} to {end_range} could take days to complete")
    print(f"✅ Checkpoints saved every 50 slugs for easy resuming")
    
    confirm = input("\n🤔 Are you sure you want to proceed? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("❌ Scan cancelled")
        return
    
    scanner = BrowserComprehensiveScanner(instance_id, start_range, end_range)
    scanner.scan_comprehensive_range()

if __name__ == "__main__":
    main() 