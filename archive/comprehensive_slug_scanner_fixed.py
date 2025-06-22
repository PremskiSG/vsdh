#!/usr/bin/env python3
"""
Comprehensive VSDHOne Slug Scanner - Fixed Version
Scans all possible 5-character combinations (aaaaa to zzzzz including numbers)
Total combinations: 36^5 = 60,466,176
"""

import time
import csv
import json
import requests
import string
import itertools
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import os
import signal
import sys

class ComprehensiveSlugScanner:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net"
        self.api_endpoint = "/api/business/"
        
        # Character set: a-z + 0-9
        self.charset = string.ascii_lowercase + string.digits  # 36 characters
        self.total_combinations = 36 ** 5  # 60,466,176
        
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
        self.lock = Lock()
        
        # Configuration
        self.max_workers = 5  # Reduce for better progress visibility
        self.requests_per_second = 3  # Conservative rate limiting
        self.batch_size = 50  # Progress save interval - checkpoint every 50
        self.timeout = 10  # Request timeout
        
        # Progress tracking files
        self.progress_file = "scan_progress.json"
        self.results_file = f"comprehensive_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.checkpoint_file = "scan_checkpoint.txt"
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print(f"🚀 Comprehensive VSDHOne Slug Scanner")
        print(f"📊 Total combinations to test: {self.total_combinations:,}")
        print(f"⚡ Concurrent workers: {self.max_workers}")
        print(f"🔄 Rate limit: {self.requests_per_second} requests/second")
        print(f"📍 Checkpoint every: {self.batch_size} slugs")
        print(f"💾 Results file: {self.results_file}")
        print(f"📍 Checkpoint file: {self.checkpoint_file}")
    
    def signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        print(f"\n🛑 Received signal {signum}. Saving progress...")
        self.save_progress()
        self.save_results()
        print("✅ Progress saved. Exiting...")
        sys.exit(0)
    
    def generate_all_combinations(self, start_from=None):
        """Generate all possible 5-character combinations"""
        print(f"🔢 Generating combinations from charset: {self.charset}")
        
        # If resuming, skip to start position
        if start_from:
            print(f"📍 Resuming from: {start_from}")
            started = False
            for combo in itertools.product(self.charset, repeat=5):
                slug = ''.join(combo)
                if slug == start_from:
                    started = True
                if started:
                    yield slug
        else:
            # Generate all combinations
            for combo in itertools.product(self.charset, repeat=5):
                yield ''.join(combo)
    
    def test_slug_with_progress(self, slug, current_count):
        """Test a single slug with progress output"""
        print(f"🔍 [{current_count:,}/{self.total_combinations:,}] Testing: {slug} ({current_count/self.total_combinations*100:.4f}%)")
        
        if slug in self.known_slugs:
            print(f"   ⏭️  Skipping known slug")
            return None  # Skip known slugs
        
        try:
            url = f"{self.base_url}{self.api_endpoint}{slug}"
            response = requests.get(url, timeout=self.timeout)
            
            # Check if it's a real business (not just HTML shell)
            content = response.text.lower()
            
            # Look for business indicators in the response
            business_indicators = [
                'business_name', 'company', 'clinic', 'center', 'health',
                'medical', 'therapy', 'treatment', 'doctor', 'wellness',
                'spa', 'hotel', 'booking', 'appointment', 'schedule'
            ]
            
            # Check for JSON-like structure or business content
            has_business_content = any(indicator in content for indicator in business_indicators)
            
            # Additional checks for valid business pages
            is_valid = (
                response.status_code == 200 and
                len(content) > 1000 and  # Substantial content
                (has_business_content or 'json' in response.headers.get('content-type', ''))
            )
            
            if is_valid:
                print(f"   ✅ FOUND VALID SLUG: {slug} - {len(content)} chars")
                return {
                    'slug': slug,
                    'url': url,
                    'status_code': response.status_code,
                    'content_length': len(content),
                    'content_type': response.headers.get('content-type', ''),
                    'has_business_indicators': has_business_content,
                    'first_100_chars': content[:100].replace('\n', ' ').replace('\r', ' '),
                    'found_at': datetime.now().isoformat()
                }
            else:
                # Show what we got
                if '401' in content:
                    print(f"   🚫 401 Error page")
                elif response.status_code != 200:
                    print(f"   ❌ HTTP {response.status_code}")
                else:
                    print(f"   ✅ Response: {len(content)} chars, no business indicators")
                    
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")
        
        return None
    
    def save_progress(self):
        """Save current progress"""
        progress_data = {
            'tested_count': self.tested_count,
            'found_count': len(self.found_slugs),
            'start_time': self.start_time,
            'current_time': datetime.now().isoformat(),
            'total_combinations': self.total_combinations
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
    
    def save_results(self):
        """Save found slugs to CSV"""
        if not self.found_slugs:
            return
        
        fieldnames = ['slug', 'url', 'status_code', 'content_length', 'content_type', 
                     'has_business_indicators', 'first_100_chars', 'found_at']
        
        with open(self.results_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.found_slugs)
        
        print(f"💾 Saved {len(self.found_slugs)} results to {self.results_file}")
    
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
    
    def scan_all_combinations(self, resume=True):
        """Main scanning function with detailed progress"""
        self.start_time = datetime.now().isoformat()
        
        # Check if resuming
        start_from = None
        if resume:
            start_from = self.load_checkpoint()
        
        print(f"🚀 Starting comprehensive scan at {self.start_time}")
        if start_from:
            print(f"📍 Resuming from checkpoint: {start_from}")
        print("")
        
        try:
            for i, slug in enumerate(self.generate_all_combinations(start_from)):
                current_count = i + 1
                
                # Test individual slug with progress
                result = self.test_slug_with_progress(slug, current_count)
                if result:
                    self.found_slugs.append(result)
                
                # Rate limiting
                time.sleep(1.0 / self.requests_per_second)
                
                # Checkpoint every batch_size slugs
                if current_count % self.batch_size == 0:
                    self.tested_count = current_count
                    self.save_checkpoint(slug)
                    
                    # Progress update with current slug info
                    progress = (current_count / self.total_combinations) * 100
                    elapsed = (datetime.now() - datetime.fromisoformat(self.start_time)).total_seconds()
                    rate = current_count / elapsed if elapsed > 0 else 0
                    eta = (self.total_combinations - current_count) / rate if rate > 0 else 0
                    
                    print(f"\n📍 CHECKPOINT #{current_count // self.batch_size}")
                    print(f"📊 Progress: {current_count:,}/{self.total_combinations:,} ({progress:.4f}%)")
                    print(f"✅ Valid slugs found: {len(self.found_slugs)}")
                    print(f"⚡ Rate: {rate:.1f} slugs/sec")
                    print(f"⏰ ETA: {eta/3600:.1f} hours")
                    print(f"💾 Checkpoint saved at: {datetime.now().strftime('%H:%M:%S')}")
                    print("-" * 60)
                    print("")
                    
                    # Save progress periodically
                    if current_count % (self.batch_size * 10) == 0:
                        self.save_progress()
                        self.save_results()
        
        except KeyboardInterrupt:
            print("\n🛑 Scan interrupted by user")
        except Exception as e:
            print(f"❌ Error during scan: {e}")
        finally:
            self.tested_count = current_count if 'current_count' in locals() else 0
            self.save_progress()
            self.save_results()
            self.print_final_summary()
    
    def print_final_summary(self):
        """Print final scan summary"""
        print(f"\n🎯 COMPREHENSIVE SCAN COMPLETE")
        print(f"=" * 50)
        print(f"📊 Total combinations tested: {self.tested_count:,}")
        print(f"✅ Valid slugs found: {len(self.found_slugs)}")
        print(f"⏱️  Scan duration: {datetime.now().isoformat()}")
        print(f"💾 Results saved to: {self.results_file}")
        
        if self.found_slugs:
            print(f"\n🔍 DISCOVERED VALID SLUGS:")
            for result in self.found_slugs:
                print(f"  • {result['slug']}: {result['content_length']} chars")
        else:
            print("\n❌ No valid slugs found in scanned range")

def main():
    print("🌟 VSDHOne Comprehensive Slug Scanner")
    print("=" * 50)
    print("⚠️  WARNING: This will test 60,466,176 combinations!")
    print("⚠️  Estimated time: 24-48 hours at conservative rate")
    print("⚠️  Use Ctrl+C to stop gracefully and save progress")
    print("✅ Checkpoints saved every 50 slugs for easy resuming")
    
    confirm = input("\n🤔 Are you sure you want to proceed? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("❌ Scan cancelled")
        return
    
    scanner = ComprehensiveSlugScanner()
    scanner.scan_all_combinations()

if __name__ == "__main__":
    main() 