#!/usr/bin/env python3
"""
Combined Scanner - Enterprise + Hydreight
Tests both vsdigital-bookingwidget-prod.azurewebsites.net/b/ and booking.hydreight.com/b/ URLs
Scans slugs 100-999, tries enterprise first, then Hydreight if enterprise fails
Comprehensive logging with one line per slug showing results from both platforms
"""

import asyncio
import json
import csv
import os
import time
import socket
import argparse
import random
import string
import base64
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

class CombinedScanner:
    def __init__(self, instance_id="COMBINED_DEFAULT"):
        self.instance_id = instance_id
        self.hostname = socket.gethostname()
        self.session_id = f"{self.hostname}_{instance_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Dual URL configuration - SAFETY OPTIMIZED
        self.enterprise_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/b/"
        self.hydreight_url = "https://booking.hydreight.com/b/"
        self.rate_limit = 8   # REDUCED for safety - 8 requests per second
        self.timeout = 15     # INCREASED for safety - 15 seconds timeout
        
        # Enterprise-specific configuration - SPEED OPTIMIZED
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/b/"
        self.rate_limit = 10  # INCREASED from 5 to 10 requests per second
        self.timeout = 10     # REDUCED from 15s to 10s (enterprise URLs are fast)
        
        # Enhanced error indicators for both platforms
        self.error_indicators = [
            '401', 'error', 'nothing left to do here', 'go to homepage',
            'not found', 'access denied', 'unauthorized',
            "the link you've opened isn't working as expected",
            'page not found', 'invalid request', 'session expired',
            'service unavailable', 'temporarily unavailable'
        ]
        
        # Business indicators optimized for both platforms
        self.business_indicators = [
            'book', 'appointment', 'schedule', 'service', 'therapy',
            'treatment', 'consultation', 'booking', 'available',
            'select', 'choose', 'weight loss', 'injection', 'iv therapy',
            'dripbar', 'hydreight', 'semaglutide', 'tirzepatide', 'hormone',
            'wellness', 'health', 'medical', 'clinic',
            'provider', 'patient', 'visit', 'care'
        ]
        
        # Session tracking
        self.session_data = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'scanner_type': 'Combined_Enterprise_Hydreight',
            'enterprise_url': self.enterprise_url,
            'hydreight_url': self.hydreight_url,
            'instance_id': instance_id,
            'hostname': self.hostname,
            'results': [],
            'stats': {
                'total_tested': 0,
                'enterprise_active': 0,
                'hydreight_active': 0,
                'both_active': 0,
                'neither_active': 0,
                'errors': 0,
                'connection_errors': 0,
                'browser_errors': 0,
                'timeouts': 0
            },
            'checkpoint_info': {
                'last_checkpoint': 0,
                'checkpoint_frequency': 10,
                'resume_from_slug': None
            }
        }
        
        # Checkpoint file for resume functionality
        self.checkpoint_file = f"logs/CHECKPOINT_COMBINED_{self.session_id}.txt"
        
        self.driver = None
        
    def generate_base64_slugs(self, start=100, end=999):
        """Generate base64 encoded slugs for the specified range"""
        slugs = []
        for i in range(start, end + 1):
            # Convert number to string and encode to base64
            base64_slug = base64.b64encode(str(i).encode()).decode('utf-8')
            slugs.append(base64_slug)
        return slugs
        
    def setup_driver(self):
        """Setup Chrome driver with safety optimizations"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript-harmony')
        chrome_options.add_argument('--aggressive-cache-discard')
        chrome_options.add_argument('--memory-pressure-off')
        
        # SAFETY OPTIMIZATIONS - Additional performance flags
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--fast-start')
        chrome_options.add_argument('--disable-logging')
        
        # Cache and cookie management for clean sessions
        chrome_options.add_argument('--disable-application-cache')
        chrome_options.add_argument('--disable-offline-load-stale-cache')
        chrome_options.add_argument('--disk-cache-size=0')
        chrome_options.add_argument('--media-cache-size=0')
        
        # Unique user data directory for parallel execution
        user_data_dir = f"/tmp/chrome_combined_{self.instance_id}_{random.randint(1000, 9999)}"
        chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        
        # Performance optimizations
        chrome_options.add_argument('--max_old_space_size=4096')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        
        try:
            # Try multiple approaches for Chrome driver
            try:
                # First try: Use webdriver_manager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception as e1:
                print(f"⚠️  WebDriver Manager failed: {e1}")
                try:
                    # Second try: Use system Chrome driver
                    self.driver = webdriver.Chrome(options=chrome_options)
                except Exception as e2:
                    print(f"⚠️  System Chrome driver failed: {e2}")
                    # Third try: Use explicit path (common locations)
                    chrome_paths = [
                        '/usr/local/bin/chromedriver',
                        '/opt/homebrew/bin/chromedriver',
                        '/usr/bin/chromedriver'
                    ]
                    driver_found = False
                    for path in chrome_paths:
                        if os.path.exists(path):
                            service = Service(path)
                            self.driver = webdriver.Chrome(service=service, options=chrome_options)
                            driver_found = True
                            break
                    if not driver_found:
                        raise Exception("No Chrome driver found in common locations")
            
            self.driver.set_page_load_timeout(self.timeout)
            print(f"✅ Chrome driver initialized for Combined Scanner {self.instance_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            print("💡 Try installing Chrome driver: brew install chromedriver")
            return False
    
    def clear_browser_cache(self):
        """Clear browser cache and cookies between requests for clean sessions"""
        try:
            # Clear cookies
            self.driver.delete_all_cookies()
            
            # Clear local storage and session storage
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            
            # Clear cache via Chrome DevTools Protocol if available
            try:
                self.driver.execute_cdp_cmd('Network.clearBrowserCache', {})
                self.driver.execute_cdp_cmd('Network.clearBrowserCookies', {})
            except:
                pass  # CDP commands might not be available in all setups
                
        except Exception as e:
            # If clearing fails, it's not critical - continue scanning
            pass
    
    def analyze_page_content(self, slug, url, platform_name):
        """Analyze page content to determine if business is active"""
        try:
            start_time = time.time()
            
            # Clear cache before each request for clean session
            self.clear_browser_cache()
            
            # Navigate to the URL
            print(f"   🌐 Testing {platform_name}: {url}")
            self.driver.get(url)
            
            # SAFETY OPTIMIZATION: Increased wait time to 5s for proper page loading
            # We prioritize data accuracy over speed
            time.sleep(5)
            
            # Get page source and basic metrics
            page_source = self.driver.page_source.lower()
            page_title = self.driver.title
            final_url = self.driver.current_url
            content_length = len(page_source)
            load_time = time.time() - start_time
            
            print(f"   📄 {platform_name} Title: '{page_title}'")
            print(f"   📏 {platform_name} Content: {content_length:,} chars, {load_time:.2f}s")
            
            # Check for error indicators first
            error_indicators_found = []
            for indicator in self.error_indicators:
                if indicator.lower() in page_source:
                    error_indicators_found.append(indicator)
            
            # Check for business indicators
            business_indicators_found = []
            for indicator in self.business_indicators:
                if indicator.lower() in page_source:
                    business_indicators_found.append(indicator)
            
            # Determine status based on platform-specific logic
            if not page_title or page_title.strip() == "":
                status = "ERROR_PAGE"
                classification = "EMPTY_TITLE_INVALID_URL"
                business_name = ""
            else:
                # Check if we have a meaningful business title or substantial content
                has_business_title = page_title and len(page_title) > 3 and page_title.lower() not in ['loading', 'error']
                has_substantial_content = content_length > 20000  # Both platforms have large pages when active
                
                if business_indicators_found or has_business_title or has_substantial_content:
                    # If we have business indicators OR a business title OR substantial content, it's likely active
                    # Only mark as error if we have clear error indicators AND no business signs
                    if error_indicators_found and not business_indicators_found and not has_business_title:
                        status = "ERROR_PAGE"
                        classification = "ERROR_INDICATORS_FOUND"
                        business_name = ""
                    else:
                        status = "ACTIVE"
                        classification = "ACTIVE_BUSINESS"
                        business_name = self.extract_business_name(page_source, page_title, platform_name)
                elif error_indicators_found:
                    status = "ERROR_PAGE"
                    classification = "ERROR_INDICATORS_FOUND"
                    business_name = ""
                else:
                    status = "INACTIVE_UNKNOWN"
                    classification = "NO_INDICATORS"
                    business_name = ""
            
            print(f"   🤖 {platform_name} Result: {status} - {business_name}")
            
            # Create comprehensive result
            result = {
                'slug': slug,
                'url': url,
                'final_url': final_url,
                'status': status,
                'classification': classification,
                'business_name': business_name,
                'business_indicators': len(business_indicators_found),
                'error_indicators': len(error_indicators_found),
                'indicators_found': business_indicators_found,
                'error_indicators_found': error_indicators_found,
                'page_title': page_title,
                'content_length': content_length,
                'load_time': load_time,
                'content_preview': page_source[:500] if page_source else '',
                'tested_at': datetime.now().isoformat(),
                'platform': platform_name
            }
            
            return result
            
        except TimeoutException as e:
            print(f"⏰ TIMEOUT after {self.timeout}s")
            return {
                'slug': slug,
                'url': url,
                'final_url': '',
                'status': 'TIMEOUT',
                'classification': 'TIMEOUT_ERROR',
                'business_name': '',
                'business_indicators': 0,
                'error_indicators': 0,
                'indicators_found': [],
                'error_indicators_found': ['timeout'],
                'page_title': '',
                'content_length': 0,
                'load_time': self.timeout,
                'content_preview': '',
                'error_details': f"Timeout after {self.timeout}s: {str(e)}",
                'tested_at': datetime.now().isoformat(),
                'platform': platform_name
            }
        except WebDriverException as e:
            print(f"🌐 CONNECTION_ERROR: {str(e)[:50]}...")
            return {
                'slug': slug,
                'url': url,
                'final_url': '',
                'status': 'CONNECTION_ERROR',
                'classification': 'CONNECTION_ERROR',
                'business_name': '',
                'business_indicators': 0,
                'error_indicators': 1,
                'indicators_found': [],
                'error_indicators_found': ['connection_error'],
                'page_title': '',
                'content_length': 0,
                'load_time': 0,
                'content_preview': '',
                'error_details': f"WebDriver error: {str(e)}",
                'tested_at': datetime.now().isoformat(),
                'platform': platform_name
            }
        except Exception as e:
            print(f"❌ BROWSER_ERROR: {str(e)[:50]}...")
            return {
                'slug': slug,
                'url': url,
                'final_url': '',
                'status': 'BROWSER_ERROR',
                'classification': 'BROWSER_ERROR',
                'business_name': '',
                'business_indicators': 0,
                'error_indicators': 1,
                'indicators_found': [],
                'error_indicators_found': [str(e)],
                'page_title': '',
                'content_length': 0,
                'load_time': 0,
                'content_preview': '',
                'error_details': f"Unexpected error: {str(e)}",
                'tested_at': datetime.now().isoformat(),
                'platform': platform_name
            }
    
    def extract_business_name(self, page_source, page_title, platform_name):
        """Extract business name from page content - PRIORITIZE PAGE TITLE"""
        # PRIORITY 1: Use page title if available and meaningful (contains actual business name)
        if page_title and len(page_title) > 3 and page_title.lower() not in ['', 'loading', 'error']:
            return page_title
        
        # PRIORITY 2: Look for platform-specific business name patterns only if no meaningful title
        if platform_name == "Enterprise":
            if 'dripbar' in page_source:
                if 'direct' in page_source:
                    return "The DRIPBaR Direct - Location"
                return "The DRIPBaR"
            elif 'renivate' in page_source:
                return "RenIVate"
        elif platform_name == "Hydreight":
            if 'hydreight' in page_source:
                if 'location' in page_source:
                    return "Hydreight - Location"
                return "Hydreight"
        
        # PRIORITY 3: Generic patterns
        if 'iv therapy' in page_source:
            return "IV Therapy Center"
        
        return ""

    def save_session_data(self):
        """Save comprehensive session data to multiple formats"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON session data
        session_filename = f"logs/SESSION_COMBINED_{self.session_id}_{timestamp}_session.json"
        with open(session_filename, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        
        # Save CSV results (combined format - one line per slug)
        results_filename = f"logs/SESSION_COMBINED_{self.session_id}_{timestamp}_results.csv"
        if self.session_data['results']:
            fieldnames = [
                'slug', 'tested_at',
                # Enterprise columns
                'enterprise_status', 'enterprise_business_name', 'enterprise_classification',
                'enterprise_page_title', 'enterprise_content_length', 'enterprise_load_time',
                'enterprise_url', 'enterprise_final_url', 'enterprise_business_indicators', 'enterprise_error_indicators',
                # Hydreight columns  
                'hydreight_status', 'hydreight_business_name', 'hydreight_classification',
                'hydreight_page_title', 'hydreight_content_length', 'hydreight_load_time',
                'hydreight_url', 'hydreight_final_url', 'hydreight_business_indicators', 'hydreight_error_indicators',
                # Summary columns
                'enterprise_active', 'hydreight_active', 'both_active', 'either_active',
                'primary_business_name', 'primary_platform'
            ]
            
            with open(results_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.session_data['results'])
        
        # Save progress summary
        progress_filename = f"logs/SESSION_COMBINED_{self.session_id}_{timestamp}_progress.json"
        progress_data = {
            'session_id': self.session_id,
            'timestamp': timestamp,
            'stats': self.session_data['stats'],
            'last_update': datetime.now().isoformat()
        }
        with open(progress_filename, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2)
        
        print(f"📊 Session data saved:")
        print(f"   Session: {session_filename}")
        if self.session_data['results']:
            print(f"   Results: {results_filename}")
        print(f"   Progress: {progress_filename}")
    
    def scan_slugs(self, slugs=None, resume=True):
        """Scan a list of slugs with checkpoint/resume functionality"""
        if slugs is None:
            # Generate slugs 100-999 by default
            slugs = self.generate_base64_slugs(100, 999)
            print(f"🎯 Generated {len(slugs)} base64 slugs (100-999)")
        
        print(f"🚀 Starting Combined Scanner {self.instance_id}")
        print(f"📍 Enterprise URL: {self.enterprise_url}")
        print(f"📍 Hydreight URL: {self.hydreight_url}")
        print(f"🎯 Total slugs to scan: {len(slugs)}")
        print(f"⚡ Rate limit: {self.rate_limit} requests/second")
        print(f"📋 Checkpoint every: {self.session_data['checkpoint_info']['checkpoint_frequency']} scans")
        
        if not self.setup_driver():
            print("❌ Failed to setup driver, aborting scan")
            return
        
        print("=" * 80)
        
        try:
            for i, slug in enumerate(slugs, 1):
                # Rate limiting
                if i > 1:
                    time.sleep(1.0 / self.rate_limit)
                
                print(f"\n🔍 [{i}/{len(slugs)}] Processing slug: {slug}")
                
                # Scan both platforms
                combined_result, enterprise_result, hydreight_result = self.scan_combined_slug(slug)
                
                # Store results
                self.session_data['results'].append(combined_result)
                
                # Update statistics
                self.session_data['stats']['total_tested'] += 1
                if enterprise_result['status'] == 'ACTIVE':
                    self.session_data['stats']['enterprise_active'] += 1
                if hydreight_result['status'] == 'ACTIVE':
                    self.session_data['stats']['hydreight_active'] += 1
                if combined_result['both_active']:
                    self.session_data['stats']['both_active'] += 1
                if not combined_result['either_active']:
                    self.session_data['stats']['neither_active'] += 1
                
                # Track errors
                for result in [enterprise_result, hydreight_result]:
                    if result['status'] == 'TIMEOUT':
                        self.session_data['stats']['timeouts'] += 1
                    elif result['status'] == 'CONNECTION_ERROR':
                        self.session_data['stats']['connection_errors'] += 1
                    elif result['status'] == 'BROWSER_ERROR':
                        self.session_data['stats']['browser_errors'] += 1
                    if result['status'] in ['TIMEOUT', 'CONNECTION_ERROR', 'BROWSER_ERROR']:
                        self.session_data['stats']['errors'] += 1
                
                # Checkpoint every N scans
                checkpoint_freq = self.session_data['checkpoint_info']['checkpoint_frequency']
                if i % checkpoint_freq == 0:
                    stats = self.session_data['stats']
                    print(f"\n📊 Progress Report [{i}/{len(slugs)}]:")
                    print(f"   ✅ Enterprise Active: {stats['enterprise_active']}")
                    print(f"   ✅ Hydreight Active: {stats['hydreight_active']}")
                    print(f"   🎯 Both Active: {stats['both_active']}")
                    print(f"   ❌ Neither Active: {stats['neither_active']}")
                    print(f"   ⚠️  Total Errors: {stats['errors']}")
                    print("   " + "="*60)
                
                # Save full session data every 25 scans
                if i % 25 == 0:
                    self.save_session_data()
        
        except KeyboardInterrupt:
            print(f"\n⚠️  Scan interrupted by user at {i}/{len(slugs)}")
        except Exception as e:
            print(f"\n❌ Unexpected error during scan: {e}")
        finally:
            # Final save and cleanup
            self.session_data['end_time'] = datetime.now().isoformat()
            self.save_session_data()
            
            if self.driver:
                self.driver.quit()
            
            # Print comprehensive final statistics
            stats = self.session_data['stats']
            print(f"\n📊 COMBINED SCAN COMPLETE:")
            print("=" * 60)
            print(f"   🎯 Total Tested: {stats['total_tested']}")
            print(f"   ✅ Enterprise Active: {stats['enterprise_active']}")
            print(f"   ✅ Hydreight Active: {stats['hydreight_active']}")
            print(f"   🎯 Both Active: {stats['both_active']}")
            print(f"   ❌ Neither Active: {stats['neither_active']}")
            print(f"   ⚠️  Total Errors: {stats['errors']}")
            print(f"      ⏰ Timeouts: {stats['timeouts']}")
            print(f"      🌐 Connection Errors: {stats['connection_errors']}")
            print(f"      🔧 Browser Errors: {stats['browser_errors']}")
            if stats['total_tested'] > 0:
                print(f"   📈 Enterprise Success Rate: {(stats['enterprise_active']/stats['total_tested']*100):.2f}%")
                print(f"   📈 Hydreight Success Rate: {(stats['hydreight_active']/stats['total_tested']*100):.2f}%")
                print(f"   📈 Combined Success Rate: {((stats['enterprise_active'] + stats['hydreight_active'])/stats['total_tested']*100):.2f}%")

    def scan_combined_slug(self, slug):
        """Scan a single slug on both platforms with fallback logic"""
        print(f"🔍 Testing slug: {slug}")
        
        # Step 1: Try Enterprise first
        enterprise_url = f"{self.enterprise_url}{slug}"
        enterprise_result = self.analyze_page_content(slug, enterprise_url, "Enterprise")
        
        # Step 2: Try Hydreight (always test both for comprehensive data)
        hydreight_url = f"{self.hydreight_url}{slug}"
        hydreight_result = self.analyze_page_content(slug, hydreight_url, "Hydreight")
        
        # Create combined result for CSV logging
        combined_result = {
            'slug': slug,
            'tested_at': datetime.now().isoformat(),
            
            # Enterprise results
            'enterprise_status': enterprise_result['status'],
            'enterprise_business_name': enterprise_result['business_name'],
            'enterprise_classification': enterprise_result['classification'],
            'enterprise_page_title': enterprise_result['page_title'],
            'enterprise_content_length': enterprise_result['content_length'],
            'enterprise_load_time': enterprise_result['load_time'],
            'enterprise_url': enterprise_result['url'],
            'enterprise_final_url': enterprise_result['final_url'],
            'enterprise_business_indicators': enterprise_result['business_indicators'],
            'enterprise_error_indicators': enterprise_result['error_indicators'],
            
            # Hydreight results
            'hydreight_status': hydreight_result['status'],
            'hydreight_business_name': hydreight_result['business_name'],
            'hydreight_classification': hydreight_result['classification'],
            'hydreight_page_title': hydreight_result['page_title'],
            'hydreight_content_length': hydreight_result['content_length'],
            'hydreight_load_time': hydreight_result['load_time'],
            'hydreight_url': hydreight_result['url'],
            'hydreight_final_url': hydreight_result['final_url'],
            'hydreight_business_indicators': hydreight_result['business_indicators'],
            'hydreight_error_indicators': hydreight_result['error_indicators'],
            
            # Summary analysis
            'enterprise_active': enterprise_result['status'] == 'ACTIVE',
            'hydreight_active': hydreight_result['status'] == 'ACTIVE',
            'both_active': enterprise_result['status'] == 'ACTIVE' and hydreight_result['status'] == 'ACTIVE',
            'either_active': enterprise_result['status'] == 'ACTIVE' or hydreight_result['status'] == 'ACTIVE',
            'primary_business_name': enterprise_result['business_name'] if enterprise_result['status'] == 'ACTIVE' else hydreight_result['business_name'],
            'primary_platform': 'Enterprise' if enterprise_result['status'] == 'ACTIVE' else ('Hydreight' if hydreight_result['status'] == 'ACTIVE' else 'None')
        }
        
        # Print summary
        ent_status = "✅" if enterprise_result['status'] == 'ACTIVE' else "❌"
        hyd_status = "✅" if hydreight_result['status'] == 'ACTIVE' else "❌"
        print(f"📊 Summary: Enterprise {ent_status} | Hydreight {hyd_status} | Primary: {combined_result['primary_platform']}")
        
        return combined_result, enterprise_result, hydreight_result

def main():
    parser = argparse.ArgumentParser(description='Combined Enterprise + Hydreight Scanner')
    parser.add_argument('--start', type=int, default=100, help='Start number for slug generation (default: 100)')
    parser.add_argument('--end', type=int, default=999, help='End number for slug generation (default: 999)')
    parser.add_argument('--slugs', nargs='+', help='Specific slugs to test (space-separated)')
    parser.add_argument('--file', help='File containing slugs (one per line)')
    parser.add_argument('--instance-id', default='COMBINED_DEFAULT', help='Instance identifier for parallel execution')
    parser.add_argument('--no-resume', action='store_true', help='Start fresh scan (ignore checkpoints)')
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Determine slugs to scan
    slugs_to_scan = []
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                slugs_to_scan = [line.strip() for line in f if line.strip()]
            print(f"📁 Loaded {len(slugs_to_scan)} slugs from {args.file}")
        except Exception as e:
            print(f"❌ Error reading file {args.file}: {e}")
            return
    elif args.slugs:
        slugs_to_scan = args.slugs
        print(f"📝 Using {len(slugs_to_scan)} slugs from command line")
    else:
        # Use default range
        scanner = CombinedScanner(instance_id=args.instance_id)
        slugs_to_scan = scanner.generate_base64_slugs(args.start, args.end)
        print(f"🎯 Generated {len(slugs_to_scan)} base64 slugs ({args.start}-{args.end})")
    
    if not slugs_to_scan:
        print("❌ No valid slugs found to scan")
        return
    
    # Create and run scanner
    scanner = CombinedScanner(instance_id=args.instance_id)
    scanner.scan_slugs(slugs_to_scan, resume=not args.no_resume)

if __name__ == "__main__":
    main() 