#!/usr/bin/env python3
"""
Fast Hybrid Scanner for VSDHOne Platform
Combines HTTP pre-filtering with selective browser automation for maximum speed

Strategy:
1. HTTP Request (0.1s): Quick check for response patterns
2. Content Analysis: Look for business vs error indicators
3. Browser Verification (5s): Only for promising candidates

Speed: ~10x faster than pure browser approach
"""

import time
import csv
import json
import requests
import random
import string
import os
import sys
import signal
import socket
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

class FastHybridScanner:
    def __init__(self, instance_id=None, start_range=None, end_range=None, slug_file=None):
        # Generate unique instance ID if not provided
        if instance_id is None:
            instance_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        self.instance_id = instance_id
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        
        # Character set for slug generation
        self.charset = string.digits + string.ascii_lowercase  # 36 characters
        
        # Handle slug file or range-based scanning
        self.slug_file = slug_file
        self.slugs_to_test = []
        
        if slug_file and os.path.exists(slug_file):
            self.load_slugs_from_file()
            self.start_range = "FILE_BASED"
            self.end_range = "FILE_BASED"
        else:
            self.start_range = start_range or 'aaaaa'
            self.end_range = end_range or 'zzzzz'
        
        # Load tested slugs from database
        self.tested_slugs = self.load_tested_slugs_database()
        print(f"📚 Loaded {len(self.tested_slugs)} previously tested slugs from database")
        
        # Known working slugs to skip
        self.known_slugs = {
            'ad31y', 'mj42f', 'os27m', 'lp56a', 'zb74k', 'ym99l', 
            'yh52b', 'zd20w', 'td32z', 'bo19e', 'bh70s', 'ai04u', 
            'bm49t', 'qu29u', 'tc33l'
        }
        
        # Results tracking
        self.found_slugs = []
        self.tested_count = 0
        self.skipped_count = 0
        self.http_filtered_count = 0
        self.browser_verified_count = 0
        self.start_time = None
        
        # Performance settings
        self.http_timeout = 3.0  # Fast HTTP timeout
        self.browser_timeout = 10  # Browser page load timeout
        self.requests_per_second = 20.0  # Much faster than browser-only (20 vs 5)
        
        # HTTP session for speed
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
        
        # Business content patterns (from known active businesses)
        self.business_patterns = [
            # Business names and types
            'altura health', 'dripbar', 'wellness', 'clinic', 'medical', 'health',
            'therapy', 'treatment', 'spa', 'center', 'institute', 'practice',
            
            # Services
            'weight loss', 'injection', 'iv therapy', 'hydration', 'vitamin',
            'consultation', 'appointment', 'booking', 'schedule', 'service',
            
            # Business indicators
            'contact', 'location', 'address', 'phone', 'email', 'hours',
            'pricing', 'cost', 'package', 'membership', 'doctor', 'nurse',
            
            # Booking/widget specific
            'book now', 'schedule appointment', 'select service', 'choose time',
            'available', 'calendar', 'date', 'time slot'
        ]
        
        # Error patterns (from known inactive slugs)
        self.error_patterns = [
            '401', 'error', 'nothing left to do here', 'go to homepage',
            'unauthorized', 'access denied', 'not found', 'invalid',
            'expired', 'disabled', 'suspended'
        ]
        
        # Create logs folder
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Create session files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        hostname = socket.gethostname().replace('.', '_')
        
        if self.slug_file:
            file_base = os.path.splitext(os.path.basename(self.slug_file))[0]
            session_prefix = f"SESSION_HYBRID_{hostname}_{file_base}_{timestamp}"
        else:
            session_prefix = f"SESSION_HYBRID_{hostname}_{self.instance_id}_{timestamp}"
        
        self.results_file = f"logs/{session_prefix}_results.csv"
        self.session_log_file = f"logs/{session_prefix}_session.json"
        
        # Session data tracking
        self.session_data = {
            'session_info': {
                'session_id': session_prefix,
                'hostname': hostname,
                'instance_id': self.instance_id,
                'start_time': None,
                'end_time': None,
                'session_type': 'HYBRID_SCAN',
                'range_start': self.start_range,
                'range_end': self.end_range,
                'scanner_version': '3.0_hybrid_fast'
            },
            'performance_stats': {
                'total_tested': 0,
                'http_filtered': 0,
                'browser_verified': 0,
                'active_found': 0,
                'inactive_found': 0,
                'errors': 0,
                'avg_http_time': 0,
                'avg_browser_time': 0,
                'speed_improvement': 0
            },
            'testing_results': []
        }
        
        print(f"🚀 Fast Hybrid Scanner (Instance: {self.instance_id})")
        print(f"📊 Range: {self.start_range} to {self.end_range}")
        print(f"⚡ Rate limit: {self.requests_per_second} tests/second")
        print(f"🔄 Strategy: HTTP pre-filter → Browser verify")
        print(f"💾 Results file: {self.results_file}")
        print("")
    
    def load_tested_slugs_database(self):
        """Load previously tested slugs from the MASTER_DATABASE"""
        tested_slugs = set()
        
        if os.path.exists('MASTER_DATABASE.json'):
            try:
                with open('MASTER_DATABASE.json', 'r', encoding='utf-8') as f:
                    database = json.load(f)
                
                for slug_data in database.get('all_slugs', []):
                    tested_slugs.add(slug_data['slug'])
                
                print(f"✅ Successfully loaded {len(tested_slugs)} tested slugs")
            except Exception as e:
                print(f"⚠️  Error loading database: {e}")
        
        return tested_slugs
    
    def load_slugs_from_file(self):
        """Load slugs from a text file (one slug per line)"""
        try:
            with open(self.slug_file, 'r') as f:
                self.slugs_to_test = [line.strip() for line in f if len(line.strip()) == 5]
            print(f"📂 Loaded {len(self.slugs_to_test)} slugs from {self.slug_file}")
        except Exception as e:
            print(f"⚠️  Error loading slug file: {e}")
            self.slugs_to_test = []
    
    def http_pre_filter(self, slug):
        """Fast HTTP check to filter out obvious inactive slugs"""
        start_time = time.time()
        
        try:
            url = f"{self.base_url}{slug}"
            response = self.session.get(url, timeout=self.http_timeout, allow_redirects=True)
            
            http_time = time.time() - start_time
            content = response.text.lower()
            content_length = len(content)
            final_url = response.url
            
            # Quick content analysis
            business_score = sum(1 for pattern in self.business_patterns if pattern in content)
            error_score = sum(1 for pattern in self.error_patterns if pattern in content)
            
            # Decision logic
            is_promising = False
            reason = ""
            
            if error_score > 0:
                reason = f"error_indicators:{error_score}"
            elif business_score >= 2:  # At least 2 business indicators
                is_promising = True
                reason = f"business_indicators:{business_score}"
            elif content_length > 15000:  # Unusually large content (might be dynamic)
                is_promising = True
                reason = f"large_content:{content_length}"
            elif 'react' in content and 'app' in content and business_score > 0:
                is_promising = True
                reason = f"react_app_with_business:{business_score}"
            else:
                reason = f"standard_spa:business={business_score},error={error_score}"
            
            result = {
                'http_time': http_time,
                'status_code': response.status_code,
                'content_length': content_length,
                'final_url': final_url,
                'business_score': business_score,
                'error_score': error_score,
                'is_promising': is_promising,
                'filter_reason': reason
            }
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                'http_time': self.http_timeout,
                'status_code': 0,
                'content_length': 0,
                'final_url': '',
                'business_score': 0,
                'error_score': 0,
                'is_promising': False,
                'filter_reason': 'timeout'
            }
        except Exception as e:
            return {
                'http_time': time.time() - start_time,
                'status_code': 0,
                'content_length': 0,
                'final_url': '',
                'business_score': 0,
                'error_score': 0,
                'is_promising': False,
                'filter_reason': f'error:{str(e)[:50]}'
            }
    
    def browser_verify(self, slug, http_result):
        """Detailed browser verification for promising candidates"""
        start_time = time.time()
        driver = None
        
        try:
            # Setup browser
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-images')  # Save bandwidth
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.browser_timeout)
            
            # Load page
            url = f"{self.base_url}{slug}"
            driver.get(url)
            
            # Wait for React to load
            time.sleep(3)
            
            # Get page content after JS execution
            final_url = driver.current_url
            page_title = driver.title
            
            try:
                body_element = driver.find_element(By.TAG_NAME, 'body')
                page_text = body_element.text.strip()
            except:
                page_text = ""
            
            browser_time = time.time() - start_time
            
            # Enhanced analysis
            page_text_lower = page_text.lower()
            title_lower = page_title.lower()
            
            # Business indicators
            business_indicators = sum(1 for pattern in self.business_patterns if pattern in page_text_lower)
            error_indicators = sum(1 for pattern in self.error_patterns if pattern in page_text_lower)
            
            # Determine status
            if error_indicators > 0 or '401' in page_text or 'nothing left to do here' in page_text_lower:
                status = 'INACTIVE_401'
            elif business_indicators >= 3 or any(name in page_text_lower for name in ['altura health', 'dripbar']):
                status = 'ACTIVE'
            elif len(page_text) > 500 and business_indicators > 0:
                status = 'POTENTIALLY_ACTIVE'
            else:
                status = 'INACTIVE_UNKNOWN'
            
            # Extract business name
            business_name = self.extract_business_name(page_text, page_title)
            
            result = {
                'status': status,
                'browser_time': browser_time,
                'final_url': final_url,
                'page_title': page_title,
                'content_length': len(page_text),
                'business_indicators': business_indicators,
                'error_indicators': error_indicators,
                'business_name': business_name,
                'page_text_preview': page_text[:200]
            }
            
            return result
            
        except TimeoutException:
            return {
                'status': 'TIMEOUT',
                'browser_time': time.time() - start_time,
                'final_url': url,
                'page_title': '',
                'content_length': 0,
                'business_indicators': 0,
                'error_indicators': 0,
                'business_name': '',
                'page_text_preview': 'Timeout during page load'
            }
        except Exception as e:
            return {
                'status': 'ERROR',
                'browser_time': time.time() - start_time,
                'final_url': url,
                'page_title': '',
                'content_length': 0,
                'business_indicators': 0,
                'error_indicators': 0,
                'business_name': '',
                'page_text_preview': f'Error: {str(e)[:100]}'
            }
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def extract_business_name(self, page_text, page_title):
        """Extract business name from page content"""
        # Simple business name extraction
        if 'altura health' in page_text.lower():
            return 'Altura Health'
        elif 'dripbar' in page_text.lower():
            return 'The DRIPBaR'
        elif page_title and page_title != 'VSDHOne':
            return page_title
        else:
            # Look for patterns like "Welcome to [Business Name]"
            import re
            patterns = [
                r'welcome to ([^.!?\n]+)',
                r'([^.!?\n]+) - book now',
                r'book your appointment at ([^.!?\n]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text.lower())
                if match:
                    return match.group(1).title()
        
        return ''
    
    def test_slug_hybrid(self, slug, current_count):
        """Test a single slug using hybrid approach"""
        print(f"🔍 [{current_count:,}] Testing: {slug}")
        
        # Step 1: HTTP pre-filter
        http_result = self.http_pre_filter(slug)
        self.http_filtered_count += 1
        
        print(f"   📡 HTTP: {http_result['filter_reason']} ({http_result['http_time']:.2f}s)")
        
        # Step 2: Browser verification (only if promising)
        if http_result['is_promising']:
            print(f"   🌐 Browser verification needed...")
            browser_result = self.browser_verify(slug, http_result)
            self.browser_verified_count += 1
            
            # Combine results
            final_result = {
                'slug': slug,
                'method': 'HYBRID',
                'status': browser_result['status'],
                'business_name': browser_result['business_name'],
                'http_time': http_result['http_time'],
                'browser_time': browser_result['browser_time'],
                'total_time': http_result['http_time'] + browser_result['browser_time'],
                'content_length': browser_result['content_length'],
                'business_indicators': browser_result['business_indicators'],
                'error_indicators': browser_result['error_indicators'],
                'final_url': browser_result['final_url'],
                'http_filter_reason': http_result['filter_reason']
            }
            
            status_emoji = "✅" if browser_result['status'] == 'ACTIVE' else "❌"
            print(f"   {status_emoji} {browser_result['status']}: {browser_result['business_name']}")
            
        else:
            # HTTP filter determined it's not promising
            final_result = {
                'slug': slug,
                'method': 'HTTP_ONLY',
                'status': 'INACTIVE_FILTERED',
                'business_name': '',
                'http_time': http_result['http_time'],
                'browser_time': 0,
                'total_time': http_result['http_time'],
                'content_length': http_result['content_length'],
                'business_indicators': http_result['business_score'],
                'error_indicators': http_result['error_score'],
                'final_url': http_result['final_url'],
                'http_filter_reason': http_result['filter_reason']
            }
            
            print(f"   ⚡ Filtered out (saved browser time)")
        
        return final_result
    
    def generate_file_based_slugs(self):
        """Generate slugs from loaded file"""
        print(f"🔢 Processing {len(self.slugs_to_test)} slugs from file: {self.slug_file}")
        
        for slug in self.slugs_to_test:
            yield slug
    
    def scan_hybrid_range(self):
        """Main hybrid scanning function"""
        self.start_time = datetime.now().isoformat()
        self.session_data['session_info']['start_time'] = self.start_time
        
        print(f"🚀 Starting hybrid scan at {self.start_time}")
        print(f"📍 Instance ID: {self.instance_id}")
        print(f"📊 Range: {self.start_range} to {self.end_range}")
        print("")
        
        try:
            # Choose generator based on scanning mode
            if self.slug_file:
                slug_generator = self.generate_file_based_slugs()
            else:
                # For test, use predefined list
                slug_generator = iter(self.slugs_to_test)
            
            for i, slug in enumerate(slug_generator):
                current_count = i + 1
                self.tested_count = current_count
                
                # Test individual slug with hybrid approach
                result = self.test_slug_hybrid(slug, current_count)
                
                # Log the result
                self.session_data['testing_results'].append({
                    'slug': slug,
                    'timestamp': datetime.now().isoformat(),
                    'result': result
                })
                
                # Track active businesses
                if result['status'] == 'ACTIVE':
                    self.found_slugs.append(result)
                    print(f"   🎯 ACTIVE BUSINESS FOUND! Total: {len(self.found_slugs)}")
                
                # Rate limiting (much faster than browser-only)
                time.sleep(1.0 / self.requests_per_second)
                
                print("")  # Add spacing between tests
        
        except KeyboardInterrupt:
            print("\n🛑 Scan interrupted by user")
        except Exception as e:
            print(f"❌ Error during scan: {e}")
        finally:
            self.save_session_log()
            self.print_final_summary()
    
    def save_session_log(self):
        """Save session log with performance stats"""
        # Update performance stats
        self.session_data['performance_stats'].update({
            'total_tested': self.tested_count,
            'http_filtered': self.http_filtered_count,
            'browser_verified': self.browser_verified_count,
            'active_found': len(self.found_slugs),
            'speed_improvement': round(self.http_filtered_count / max(self.browser_verified_count, 1), 1)
        })
        
        # Update session end time
        if self.session_data['session_info']['start_time']:
            end_time = datetime.now()
            self.session_data['session_info']['end_time'] = end_time.isoformat()
            duration = (end_time - datetime.fromisoformat(self.session_data['session_info']['start_time'])).total_seconds()
            self.session_data['performance_stats']['session_duration_seconds'] = duration
        
        try:
            with open(self.session_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
            print(f"📋 Session log saved to: {self.session_log_file}")
        except Exception as e:
            print(f"⚠️  Error saving session log: {e}")
    
    def print_final_summary(self):
        """Print final scan summary with performance metrics"""
        end_time = datetime.now()
        if self.start_time:
            duration = end_time - datetime.fromisoformat(self.start_time)
        else:
            duration = "Unknown"
        
        print(f"\n🎯 HYBRID SCAN COMPLETE (Instance: {self.instance_id})")
        print(f"=" * 70)
        print(f"📊 Test slugs processed: {self.tested_count:,}")
        
        print(f"\n⚡ PERFORMANCE BREAKDOWN:")
        print(f"📡 HTTP pre-filtered: {self.http_filtered_count:,}")
        print(f"🌐 Browser verified: {self.browser_verified_count:,}")
        
        if self.browser_verified_count > 0:
            browser_percentage = (self.browser_verified_count / self.http_filtered_count) * 100
            speed_improvement = self.http_filtered_count / self.browser_verified_count
            print(f"🚀 Browser usage: {browser_percentage:.1f}% (saved {speed_improvement:.1f}x time)")
        
        print(f"🌟 Active businesses found: {len(self.found_slugs)}")
        print(f"⏱️  Total duration: {duration}")
        
        # Show accuracy analysis
        print(f"\n📊 ACCURACY ANALYSIS:")
        active_slugs = ['ad31y', 'mj42f', 'os27m', 'lp56a', 'zb74k', 'ym99l', 'yh52b', 'zd20w', 'td32z', 'bo19e']
        inactive_slugs = ['aaaaa', 'aaaab', 'aaaac', 'aaaad', 'aaaae', 'aaaaf', 'aaaag', 'aaaah', 'aaaai', 'aaaaj']
        
        correct_predictions = 0
        total_predictions = 0
        
        for result_entry in self.session_data['testing_results']:
            slug = result_entry['slug']
            predicted_status = result_entry['result']['status']
            
            if slug in active_slugs:
                expected = 'ACTIVE'
                correct = predicted_status == 'ACTIVE'
            elif slug in inactive_slugs:
                expected = 'INACTIVE'
                correct = predicted_status in ['INACTIVE_401', 'INACTIVE_FILTERED', 'INACTIVE_UNKNOWN']
            else:
                continue
            
            if correct:
                correct_predictions += 1
            total_predictions += 1
            
            status_icon = "✅" if correct else "❌"
            print(f"  {status_icon} {slug}: Expected {expected}, Got {predicted_status}")
        
        if total_predictions > 0:
            accuracy = (correct_predictions / total_predictions) * 100
            print(f"\n🎯 Overall Accuracy: {accuracy:.1f}% ({correct_predictions}/{total_predictions})")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='VSDHOne Fast Hybrid Scanner')
    parser.add_argument('--test', action='store_true', help='Run test with 20 known slugs')
    parser.add_argument('--file', '-f', help='File containing slugs to test (one per line)')
    parser.add_argument('--instance-id', '-i', help='Instance ID for parallel execution')
    
    args = parser.parse_args()
    
    print("⚡ VSDHOne Fast Hybrid Scanner")
    print("=" * 60)
    print("🚀 Strategy: HTTP pre-filter → Browser verify promising candidates")
    print("")
    
    if args.test:
        print("🧪 Running test with 20 known slugs (10 active + 10 inactive)")
        
        # Create scanner for test
        scanner = FastHybridScanner(instance_id="test20")
        
        # Set test slugs manually
        scanner.slugs_to_test = [
            # 10 known active slugs
            'ad31y', 'mj42f', 'os27m', 'lp56a', 'zb74k', 
            'ym99l', 'yh52b', 'zd20w', 'td32z', 'bo19e',
            # 10 known inactive slugs
            'aaaaa', 'aaaab', 'aaaac', 'aaaad', 'aaaae',
            'aaaaf', 'aaaag', 'aaaah', 'aaaai', 'aaaaj'
        ]
        
        print(f"📋 Test slugs: {len(scanner.slugs_to_test)}")
        print(f"✅ Active (expected): {scanner.slugs_to_test[:10]}")
        print(f"❌ Inactive (expected): {scanner.slugs_to_test[10:]}")
        print("")
        
        scanner.scan_hybrid_range()
        
    elif args.file:
        if not os.path.exists(args.file):
            print(f"❌ Error: File {args.file} not found")
            return
        
        print(f"📂 File-based scanning mode: {args.file}")
        scanner = FastHybridScanner(args.instance_id, slug_file=args.file)
        scanner.scan_hybrid_range()
    else:
        print("❌ Please specify --test or --file")
        print("Usage: python3 fast_hybrid_scanner.py --test")
        print("       python3 fast_hybrid_scanner.py --file slugs.txt")

if __name__ == "__main__":
    main()
