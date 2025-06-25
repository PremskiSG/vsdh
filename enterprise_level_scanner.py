#!/usr/bin/env python3
"""
VSDHOne Enterprise Level Scanner
High-performance scanner for enterprise booking URLs (/b/ format)
Based on complete_fast_scanner with optimizations for /b/ endpoint
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
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

class EnterpriseScanner:
    def __init__(self, instance_id="ENT_DEFAULT"):
        self.instance_id = instance_id
        self.hostname = socket.gethostname()
        self.session_id = f"{self.hostname}_{instance_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Enterprise-specific configuration - SPEED OPTIMIZED
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/b/"
        self.rate_limit = 10  # INCREASED from 5 to 10 requests per second
        self.timeout = 10     # REDUCED from 15s to 10s (enterprise URLs are fast)
        
        # Enhanced error indicators for enterprise level
        self.error_indicators = [
            '401', 'error', 'nothing left to do here', 'go to homepage',
            'not found', 'access denied', 'unauthorized',
            "the link you've opened isn't working as expected",
            'page not found', 'invalid request', 'session expired',
            'service unavailable', 'temporarily unavailable'
        ]
        
        # Business indicators optimized for enterprise format
        self.business_indicators = [
            'book', 'appointment', 'schedule', 'service', 'therapy',
            'treatment', 'consultation', 'booking', 'available',
            'select', 'choose', 'weight loss', 'injection', 'iv therapy',
            'dripbar', 'semaglutide', 'tirzepatide', 'hormone',
            'wellness', 'health', 'medical', 'clinic',
            'provider', 'patient', 'visit', 'care'
        ]
        
        # Session tracking
        self.session_data = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'scanner_type': 'Enterprise_Level',
            'base_url': self.base_url,
            'instance_id': instance_id,
            'hostname': self.hostname,
            'results': [],
            'stats': {
                'total_tested': 0,
                'active_found': 0,
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
        self.checkpoint_file = f"logs/CHECKPOINT_ENT_{self.session_id}.txt"
        
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with enterprise optimizations"""
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
        
        # SPEED OPTIMIZATIONS - Additional performance flags
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--fast-start')
        chrome_options.add_argument('--disable-logging')
        
        # Unique user data directory for parallel execution
        user_data_dir = f"/tmp/chrome_enterprise_{self.instance_id}_{random.randint(1000, 9999)}"
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
            print(f"✅ Chrome driver initialized for Enterprise Scanner {self.instance_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            print("💡 Try installing Chrome driver: brew install chromedriver")
            return False
    
    def analyze_page_content(self, slug, url):
        """Analyze page content to determine if business is active"""
        try:
            start_time = time.time()
            
            # Navigate to the enterprise URL
            enterprise_url = f"{self.base_url}{slug}"
            self.driver.get(enterprise_url)
            
            # ACCURACY OPTIMIZATION: Increased wait time to 3s for proper page loading
            # These are dynamic pages that need time for content to fully render
            time.sleep(3)
            
            # Get page source and basic metrics
            page_source = self.driver.page_source.lower()
            page_title = self.driver.title
            final_url = self.driver.current_url
            content_length = len(page_source)
            load_time = time.time() - start_time
            
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
            
            # ENTERPRISE-SPECIFIC: Empty title is primary indicator of invalid URL
            if not page_title or page_title.strip() == "":
                status = "ERROR_PAGE"
                classification = "EMPTY_TITLE_INVALID_URL"
                business_name = ""
            else:
                # Determine status based on indicators with improved logic
                # Check if we have a meaningful business title or substantial content
                has_business_title = page_title and len(page_title) > 3 and page_title.lower() not in ['loading', 'error']
                has_substantial_content = content_length > 20000  # Enterprise pages are typically large
                
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
                        business_name = self.extract_business_name(page_source, page_title)
                elif error_indicators_found:
                    status = "ERROR_PAGE"
                    classification = "ERROR_INDICATORS_FOUND"
                    business_name = ""
                else:
                    status = "INACTIVE_UNKNOWN"
                    classification = "NO_INDICATORS"
                    business_name = ""
            
            # Create comprehensive result
            result = {
                'slug': slug,
                'url': enterprise_url,
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
                'tested_at': datetime.now().isoformat()
            }
            
            return result
            
        except TimeoutException as e:
            print(f"⏰ TIMEOUT after {self.timeout}s")
            return {
                'slug': slug,
                'url': f"{self.base_url}{slug}",
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
                'tested_at': datetime.now().isoformat()
            }
        except WebDriverException as e:
            print(f"🌐 CONNECTION_ERROR: {str(e)[:50]}...")
            return {
                'slug': slug,
                'url': f"{self.base_url}{slug}",
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
                'tested_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ BROWSER_ERROR: {str(e)[:50]}...")
            return {
                'slug': slug,
                'url': f"{self.base_url}{slug}",
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
                'tested_at': datetime.now().isoformat()
            }
    
    def extract_business_name(self, page_source, page_title):
        """Extract business name from page content"""
        # Look for common business name patterns
        if 'dripbar' in page_source:
            # Extract DRIPBaR location info
            if 'direct' in page_source:
                return "The DRIPBaR Direct - Location"
            return "The DRIPBaR"
        elif 'renivate' in page_source:
            return "RenIVate"
        
        # Use page title if available and meaningful
        if page_title and len(page_title) > 3 and page_title.lower() not in ['', 'loading', 'error']:
            return page_title
        
        return ""
    
    def save_checkpoint(self, current_slug_index, total_slugs, current_slug):
        """Save checkpoint for resume functionality"""
        checkpoint_data = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'current_index': current_slug_index,
            'total_slugs': total_slugs,
            'current_slug': current_slug,
            'stats': self.session_data['stats'].copy(),
            'completed_slugs': current_slug_index
        }
        
        # Save to checkpoint file
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        # Also save to timestamped checkpoint
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        timestamped_checkpoint = f"logs/CHECKPOINT_ENT_{self.session_id}_{timestamp}.json"
        with open(timestamped_checkpoint, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        print(f"💾 CHECKPOINT [{current_slug_index}/{total_slugs}] - Progress saved")
        return checkpoint_data
    
    def load_checkpoint(self):
        """Load checkpoint for resume functionality"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)
                print(f"📋 Found checkpoint: {checkpoint_data['completed_slugs']} slugs completed")
                return checkpoint_data
            except Exception as e:
                print(f"⚠️  Could not load checkpoint: {e}")
        return None
    
    def normalize_result_fields(self, result_dict):
        """Ensure all result dictionaries have consistent fields for CSV compatibility"""
        # Define all possible fields that could exist in any result
        all_fields = {
            'slug': '',
            'url': '',
            'final_url': '',
            'status': '',
            'classification': '',
            'business_name': '',
            'business_indicators': 0,
            'error_indicators': 0,
            'indicators_found': [],
            'error_indicators_found': [],
            'page_title': '',
            'content_length': 0,
            'load_time': 0,
            'content_preview': '',
            'error_details': '',  # This field is missing in successful results
            'tested_at': ''
        }
        
        # Merge the result with default fields, keeping existing values
        normalized = all_fields.copy()
        normalized.update(result_dict)
        return normalized

    def save_session_data(self):
        """Save session data to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save session JSON
        session_filename = f"logs/SESSION_ENT_{self.session_id}_{timestamp}_session.json"
        with open(session_filename, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        
        # Save results CSV (only if there are results)
        if self.session_data['results']:
            results_filename = f"logs/SESSION_ENT_{self.session_id}_{timestamp}_results.csv"
            with open(results_filename, 'w', newline='', encoding='utf-8') as f:
                if self.session_data['results']:
                    # Normalize all results to have consistent fields
                    normalized_results = [self.normalize_result_fields(result) for result in self.session_data['results']]
                    
                    # Use predefined fieldnames to ensure consistency
                    fieldnames = [
                        'slug', 'url', 'final_url', 'status', 'classification', 
                        'business_name', 'business_indicators', 'error_indicators', 
                        'indicators_found', 'error_indicators_found', 'page_title', 
                        'content_length', 'load_time', 'content_preview', 
                        'error_details', 'tested_at'
                    ]
                    
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(normalized_results)
        
        # Save progress summary
        progress_filename = f"logs/SESSION_ENT_{self.session_id}_{timestamp}_progress.json"
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
    
    def scan_slugs(self, slugs, resume=True):
        """Scan a list of enterprise slugs with checkpoint/resume functionality"""
        print(f"🚀 Starting Enterprise Level Scanner {self.instance_id}")
        print(f"📍 Base URL: {self.base_url}")
        print(f"🎯 Total slugs to scan: {len(slugs)}")
        print(f"⚡ Rate limit: {self.rate_limit} requests/second")
        print(f"📋 Checkpoint every: {self.session_data['checkpoint_info']['checkpoint_frequency']} scans")
        
        # Check for existing checkpoint
        start_index = 0
        if resume:
            checkpoint = self.load_checkpoint()
            if checkpoint:
                response = input(f"🔄 Resume from slug {checkpoint['completed_slugs']}? (y/n): ").lower()
                if response == 'y':
                    start_index = checkpoint['completed_slugs']
                    self.session_data['stats'] = checkpoint['stats']
                    print(f"🔄 Resuming from index {start_index}")
                else:
                    print("🆕 Starting fresh scan")
        
        if not self.setup_driver():
            print("❌ Failed to setup driver, aborting scan")
            return
        
        slugs_to_process = slugs[start_index:] if start_index > 0 else slugs
        current_global_index = start_index
        
        print(f"🔍 Processing {len(slugs_to_process)} slugs (starting from {start_index+1})")
        print("=" * 70)
        
        try:
            for local_i, slug in enumerate(slugs_to_process, 1):
                current_global_index = start_index + local_i
                
                # Rate limiting (skip for first scan)
                if local_i > 1:
                    time.sleep(1.0 / self.rate_limit)
                
                print(f"🔍 [{current_global_index}/{len(slugs)}] Testing: {slug}", end=" ", flush=True)
                
                # Analyze the page
                result = self.analyze_page_content(slug, f"{self.base_url}{slug}")
                self.session_data['results'].append(result)
                
                # Update statistics
                self.session_data['stats']['total_tested'] += 1
                
                # Enhanced status reporting with proper error tracking
                if result['status'] == 'ACTIVE':
                    self.session_data['stats']['active_found'] += 1
                    print(f"✅ ACTIVE: {result.get('business_name', 'Unknown')}")
                elif result['status'] == 'TIMEOUT':
                    self.session_data['stats']['timeouts'] += 1
                    self.session_data['stats']['errors'] += 1
                    # Already printed in analyze_page_content
                elif result['status'] == 'CONNECTION_ERROR':
                    self.session_data['stats']['connection_errors'] += 1
                    self.session_data['stats']['errors'] += 1
                    # Already printed in analyze_page_content
                elif result['status'] == 'BROWSER_ERROR':
                    self.session_data['stats']['browser_errors'] += 1
                    self.session_data['stats']['errors'] += 1
                    # Already printed in analyze_page_content
                elif result['status'] == 'ERROR_PAGE':
                    print(f"⚪ ERROR_PAGE ({result.get('classification', 'Unknown')})")
                else:
                    print(f"⚪ {result['status']}")
                
                # Checkpoint every N scans (configurable)
                checkpoint_freq = self.session_data['checkpoint_info']['checkpoint_frequency']
                if current_global_index % checkpoint_freq == 0:
                    self.save_checkpoint(current_global_index, len(slugs), slug)
                    
                    # Show detailed progress every checkpoint
                    stats = self.session_data['stats']
                    print(f"📊 Progress Report [{current_global_index}/{len(slugs)}]:")
                    print(f"   ✅ Active: {stats['active_found']}")
                    print(f"   ❌ Errors: {stats['errors']} (Timeouts: {stats['timeouts']}, Connections: {stats['connection_errors']}, Browser: {stats['browser_errors']})")
                    print(f"   🎯 Success Rate: {(stats['active_found']/stats['total_tested']*100):.2f}%")
                    print("   " + "="*50)
                
                # Save full session data every 50 scans
                if current_global_index % 50 == 0:
                    self.save_session_data()
        
        except KeyboardInterrupt:
            print(f"\n⚠️  Scan interrupted by user at {current_global_index}/{len(slugs)}")
            print("💾 Saving final checkpoint...")
            self.save_checkpoint(current_global_index, len(slugs), slug if 'slug' in locals() else 'unknown')
        except Exception as e:
            print(f"\n❌ Unexpected error during scan: {e}")
            print("💾 Saving emergency checkpoint...")
            self.save_checkpoint(current_global_index, len(slugs), slug if 'slug' in locals() else 'unknown')
        finally:
            # Final save and cleanup
            self.session_data['end_time'] = datetime.now().isoformat()
            self.save_session_data()
            
            if self.driver:
                self.driver.quit()
            
            # Print comprehensive final statistics
            stats = self.session_data['stats']
            print(f"\n📊 ENTERPRISE SCAN COMPLETE:")
            print("=" * 50)
            print(f"   🎯 Total Tested: {stats['total_tested']}")
            print(f"   ✅ Active Found: {stats['active_found']}")
            print(f"   ❌ Total Errors: {stats['errors']}")
            print(f"      ⏰ Timeouts: {stats['timeouts']}")
            print(f"      🌐 Connection Errors: {stats['connection_errors']}")
            print(f"      🔧 Browser Errors: {stats['browser_errors']}")
            print(f"   📈 Success Rate: {(stats['active_found']/stats['total_tested']*100):.2f}%" if stats['total_tested'] > 0 else "   📈 Success Rate: 0%")
            print(f"   ⚡ Avg Speed: {stats['total_tested']/(time.time() - time.mktime(datetime.fromisoformat(self.session_data['start_time']).timetuple())):.2f} slugs/second" if stats['total_tested'] > 0 else "")

def determine_business_status(page_source, page_title, url):
    """
    Determine if a page represents an active business based on content analysis.
    Enhanced for enterprise format with empty title detection.
    """
    page_source_lower = page_source.lower()
    page_title_lower = page_title.lower()
    
    # ENTERPRISE-SPECIFIC: Empty title is primary indicator of invalid URL
    if not page_title or page_title.strip() == "":
        return "ERROR_PAGE", "Empty page title indicates invalid enterprise URL"
    
    # Clear error indicators (but only if no business signs)
    error_indicators = [
        "nothing left to do here",
        "go to homepage", 
        "error occurred",
        "page not found",
        "404",
        "401",
        "403",
        "500",
        "internal server error",
        "bad request",
        "unauthorized",
        "forbidden"
    ]
    
    # Business/appointment indicators
    business_indicators = [
        "wellness", "health", "medical", "clinic", "provider", 
        "patient", "visit", "care", "appointment", "schedule", "booking", 
        "select", "calendar", "time", "date", "available"
    ]
    
    # Check for business indicators
    business_signs = any(indicator in page_source_lower or indicator in page_title_lower 
                        for indicator in business_indicators)
    
    # Check for error indicators
    error_signs = any(indicator in page_source_lower for indicator in error_indicators)
    
    # Enterprise logic: Valid title + substantial content + business indicators = ACTIVE
    if page_title.strip() and len(page_source) > 20000 and business_signs:
        return "ACTIVE", f"Valid enterprise business: {page_title}"
    
    # If we have error indicators and no business signs, it's an error
    if error_signs and not business_signs:
        return "ERROR_PAGE", "Error indicators found without business content"
    
    # Enterprise format: If we have a title but no clear business indicators, 
    # it might still be valid but not fully loaded
    if page_title.strip() and len(page_source) > 15000:
        return "ACTIVE", f"Enterprise page with title: {page_title}"
    
    # Default for enterprise: empty title or minimal content = error
    return "ERROR_PAGE", "Insufficient content or empty title for enterprise URL"

def main():
    parser = argparse.ArgumentParser(description='VSDHOne Enterprise Level Scanner')
    parser.add_argument('--slugs', nargs='+', help='Enterprise slugs to test (space-separated)')
    parser.add_argument('--file', help='File containing enterprise slugs (one per line)')
    parser.add_argument('--instance-id', default='ENT_DEFAULT', help='Instance identifier for parallel execution')
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
        print("❌ No slugs provided. Use --slugs or --file")
        return
    
    if not slugs_to_scan:
        print("❌ No valid slugs found to scan")
        return
    
    # Create and run scanner
    scanner = EnterpriseScanner(instance_id=args.instance_id)
    scanner.scan_slugs(slugs_to_scan, resume=not args.no_resume)

if __name__ == "__main__":
    main() 