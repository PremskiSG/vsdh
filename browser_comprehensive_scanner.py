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
import socket
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from threading import Lock
from selenium.common.exceptions import TimeoutException, WebDriverException
import glob

class BrowserComprehensiveScanner:
    def __init__(self, instance_id=None, start_range=None, end_range=None, slug_file=None):
        # Generate unique instance ID if not provided
        if instance_id is None:
            instance_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        self.instance_id = instance_id
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        
        # Character set: 0-9 + a-z (ASCII order for proper string comparison)
        self.charset = string.digits + string.ascii_lowercase  # 36 characters
        self.total_combinations = 36 ** 5  # 60,466,176
        
        # Handle slug file or range-based scanning
        self.slug_file = slug_file
        self.slugs_to_test = []
        
        if slug_file and os.path.exists(slug_file):
            self.load_slugs_from_file()
            self.start_range = "FILE_BASED"
            self.end_range = "FILE_BASED"
        else:
            # Range handling for parallel execution
            self.start_range = start_range or 'aaaaa'
            self.end_range = end_range or 'zzzzz'
        
        # Load tested slugs from database to avoid retesting
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
        self.start_time = None
        self.checkpoint_interval = 50  # Save checkpoint every 50 slugs
        
        # Configuration for browser automation
        self.page_load_timeout = 15  # Seconds to wait for page load
        self.requests_per_second = 5.0  # 0.2s between tests = 5 tests per second
        
        # Create logs folder if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            print("📁 Created logs folder")
        
        # Create unique session files for each run
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        hostname = socket.gethostname().replace('.', '_')  # Get laptop identifier
        
        # Generate file prefix based on input file or range
        if self.slug_file:
            # Use input filename (without extension) as part of the prefix
            file_base = os.path.splitext(os.path.basename(self.slug_file))[0]
            session_prefix = f"SESSION_FILE_{hostname}_{file_base}_{timestamp}"
        else:
            session_prefix = f"SESSION_RANGE_{hostname}_{self.instance_id}_{timestamp}"
        
        # Store all files in logs folder
        self.results_file = f"logs/{session_prefix}_results.csv"
        self.progress_file = f"logs/{session_prefix}_progress.json"
        self.session_log_file = f"logs/{session_prefix}_session.json"
        
        # Create persistent checkpoint file (no timestamp for resume capability)
        if self.slug_file:
            file_base = os.path.splitext(os.path.basename(self.slug_file))[0]
            self.checkpoint_file = f"logs/CHECKPOINT_FILE_{hostname}_{file_base}.txt"
        else:
            self.checkpoint_file = f"logs/CHECKPOINT_RANGE_{hostname}_{self.instance_id}.txt"
        
        # Initialize session log data
        self.session_data = {
            'session_info': {
                'session_id': session_prefix,
                'hostname': hostname,
                'instance_id': self.instance_id,
                'start_time': None,
                'end_time': None,
                'session_type': 'COMPREHENSIVE_SCAN',
                'range_start': self.start_range,
                'range_end': self.end_range,
                'scanner_version': '2.1_session_logging'
            },
            'testing_results': [],
            'session_summary': {
                'total_tested': 0,
                'active_found': 0,
                'inactive_found': 0,
                'connection_errors': 0,
                'browser_errors': 0,
                'other_errors': 0,
                'session_duration_seconds': 0,
                'average_test_time': 0
            }
        }
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print(f"🌐 Browser-Based Comprehensive Scanner (Instance: {self.instance_id})")
        print(f"📊 Range: {self.start_range} to {self.end_range}")
        print(f"🔄 Rate limit: {self.requests_per_second} pages/second")
        print(f"📍 Checkpoint every: {self.checkpoint_interval} slugs")
        print(f"💾 Results file: {self.results_file}")
        print(f"📍 Checkpoint file: {self.checkpoint_file}")
        print(f"📋 Session log file: {self.session_log_file}")
        print("")
    
    def load_tested_slugs_database(self):
        """Load previously tested slugs from the MASTER_DATABASE"""
        tested_slugs = set()
        
        # Check for MASTER_DATABASE first
        if os.path.exists('MASTER_DATABASE.json'):
            latest_file = 'MASTER_DATABASE.json'
            print(f"📖 Loading tested slugs from: {latest_file}")
        else:
            # Fallback to old database files
            json_files = glob.glob("vsdhone_slug_database_*.json")
            if not json_files:
                print("📭 No existing slug database found - will test all slugs")
                return tested_slugs
            
            # Get the most recent file
            latest_file = max(json_files, key=os.path.getctime)
            print(f"📖 Loading tested slugs from: {latest_file}")
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                database = json.load(f)
            
            # Extract all tested slugs
            for slug_data in database.get('all_slugs', []):
                tested_slugs.add(slug_data['slug'])
            
            print(f"✅ Successfully loaded {len(tested_slugs)} tested slugs")
            
        except Exception as e:
            print(f"⚠️  Error loading database: {e}")
            print("📭 Will proceed without database - may retest some slugs")
        
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
    
    def generate_file_based_slugs(self, start_from=None):
        """Generate slugs from loaded file"""
        print(f"🔢 Processing {len(self.slugs_to_test)} slugs from file: {self.slug_file}")
        
        started = False
        if start_from:
            print(f"📍 Resuming from: {start_from}")
        
        for slug in self.slugs_to_test:
            # Handle resuming
            if start_from:
                if slug == start_from:
                    started = True
                if not started:
                    continue
            
            yield slug
    
    def log_test_result(self, slug, result, test_type="COMPREHENSIVE_SCAN"):
        """Log individual test result to session data"""
        test_entry = {
            'slug': slug,
            'timestamp': datetime.now().isoformat(),
            'test_type': test_type,
            'status': result.get('status', 'ERROR') if result else 'ERROR',
            'business_name': result.get('business_name', '') if result else '',
            'load_time': result.get('load_time', 0) if result else 0,
            'content_length': result.get('content_length', 0) if result else 0,
            'business_indicators': result.get('business_indicators', 0) if result else 0,
            'error_indicators': result.get('error_indicators', 0) if result else 0,
            'final_url': result.get('final_url', '') if result else '',
            'error': result.get('error', '') if result and 'error' in result else ''
        }
        
        self.session_data['testing_results'].append(test_entry)
        
        # Update session summary
        self.session_data['session_summary']['total_tested'] += 1
        if result and result.get('status') == 'ACTIVE':
            self.session_data['session_summary']['active_found'] += 1
        elif result and result.get('status') == 'INACTIVE_401':
            self.session_data['session_summary']['inactive_found'] += 1
        else:
            self.session_data['session_summary']['errors_encountered'] += 1
    
    def save_session_log(self):
        """Save complete session log to JSON file"""
        # Update session end time and duration
        if self.session_data['session_info']['start_time']:
            start_time = datetime.fromisoformat(self.session_data['session_info']['start_time'])
            end_time = datetime.now()
            self.session_data['session_info']['end_time'] = end_time.isoformat()
            duration = (end_time - start_time).total_seconds()
            self.session_data['session_summary']['session_duration_seconds'] = duration
            
            # Calculate average test time
            total_tests = self.session_data['session_summary']['total_tested']
            if total_tests > 0:
                self.session_data['session_summary']['average_test_time'] = duration / total_tests
        
        # Save to file
        try:
            with open(self.session_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
            print(f"📋 Session log saved to: {self.session_log_file}")
        except Exception as e:
            print(f"⚠️  Error saving session log: {e}")

    def signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        print(f"\n🛑 Received signal {signum}. Saving progress...")
        self.save_progress()
        self.save_results()
        self.save_session_log()
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
                'semaglutide', 'tirzepatide', 'ozempic', 'mounjaro',
                'iv therapy', 'vitamin', 'consultation', 'appointment'
            ]
            
            # Error page indicators
            error_indicators = [
                '401', 'error', 'nothing left to do here', 'go to homepage',
                'not found', 'access denied', 'unauthorized'
            ]
            
            # Count indicators
            business_count = sum(1 for indicator in business_indicators if indicator in page_text_lower)
            error_count = sum(1 for indicator in error_indicators if indicator in page_text_lower)
            
            # Get indicators found for detailed reporting
            indicators_found = [indicator for indicator in business_indicators if indicator in page_text_lower]
            error_indicators_found = [indicator for indicator in error_indicators if indicator in page_text_lower]
            
            # Determine page type
            is_error_page = (
                '401' in page_text_lower or 
                'nothing left to do here' in page_text_lower or
                'go to homepage' in page_text_lower or
                error_count > 0 or
                len(page_text) < 100
            )
            
            is_business_page = (
                business_count >= 2 and 
                not is_error_page and
                len(page_text) > 200
            )
            
            # Classification and detailed output
            if is_error_page:
                print(f"   🚫 INACTIVE_401 - Error Page")
                print(f"   📏 Content Length: {len(page_text)} chars")
                print(f"   🔗 Final URL: {final_url}")
                if error_indicators_found:
                    print(f"   🔍 Error Indicators Found: {', '.join(error_indicators_found)}")
                classification = "INACTIVE_401"
                
                return {
                    'slug': slug,
                    'url': url,
                    'final_url': final_url,
                    'status': 'INACTIVE_401',
                    'classification': classification,
                    'business_name': '',
                    'business_indicators': business_count,
                    'error_indicators': error_count,
                    'indicators_found': indicators_found,
                    'error_indicators_found': error_indicators_found,
                    'page_title': page_title,
                    'content_length': len(page_text),
                    'load_time': load_time,
                    'content_preview': page_text[:500] + "..." if len(page_text) > 500 else page_text,
                    'tested_at': datetime.now().isoformat()
                }
            elif is_business_page:
                # Extract business name
                business_name = self.extract_business_name_enhanced(page_text, page_title)
                
                print(f"   🌟 ACTIVE BUSINESS PAGE - {business_name}")
                print(f"   📊 Business Indicators: {business_count}")
                print(f"   📄 Page Title: {page_title}")
                print(f"   📏 Content Length: {len(page_text)} chars")
                print(f"   ⏱️  Load Time: {load_time:.2f} seconds")
                print(f"   🔍 Business Indicators Found: {', '.join(indicators_found)}")
                
                # Extract and show services/pricing if available
                services = self.extract_services_from_content(page_text)
                if services:
                    print(f"   💰 Services Found: {', '.join(services[:3])}")
                
                classification = "ACTIVE_BUSINESS"
                
                # This is a find! Return detailed info
                return {
                    'slug': slug,
                    'url': url,
                    'final_url': final_url,
                    'status': 'ACTIVE',
                    'classification': classification,
                    'business_name': business_name,
                    'business_indicators': business_count,
                    'error_indicators': error_count,
                    'indicators_found': indicators_found,
                    'error_indicators_found': error_indicators_found,
                    'page_title': page_title,
                    'content_length': len(page_text),
                    'load_time': load_time,
                    'content_preview': page_text[:500] + "..." if len(page_text) > 500 else page_text,
                    'tested_at': datetime.now().isoformat()
                }
            else:
                print(f"   ⚠️  UNCLEAR CONTENT")
                print(f"   📏 Content Length: {len(page_text)} chars")
                print(f"   📊 Business Indicators: {business_count}")
                print(f"   🚫 Error Indicators: {error_count}")
                if indicators_found:
                    print(f"   🔍 Some Business Indicators: {', '.join(indicators_found[:3])}")
                classification = "UNCLEAR"
                
                return {
                    'slug': slug,
                    'url': url,
                    'final_url': final_url,
                    'status': 'UNCLEAR',
                    'classification': classification,
                    'business_name': '',
                    'business_indicators': business_count,
                    'error_indicators': error_count,
                    'indicators_found': indicators_found,
                    'error_indicators_found': error_indicators_found,
                    'page_title': page_title,
                    'content_length': len(page_text),
                    'load_time': load_time,
                    'content_preview': page_text[:500] + "..." if len(page_text) > 500 else page_text,
                    'tested_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            error_str = str(e).lower()
            
            # Categorize different types of errors
            if any(keyword in error_str for keyword in ['timeout', 'connection', 'network', 'dns', 'resolve']):
                print(f"   🌐 CONNECTION ERROR - Logging for retry: {str(e)[:100]}")
                status = 'CONNECTION_ERROR'
                classification = 'CONNECTION_ERROR'
            elif any(keyword in error_str for keyword in ['chrome', 'driver', 'session']):
                print(f"   🔧 BROWSER ERROR - Logging for retry: {str(e)[:100]}")
                status = 'BROWSER_ERROR'
                classification = 'BROWSER_ERROR'
            else:
                print(f"   ❌ UNKNOWN ERROR - Logging for retry: {str(e)[:100]}")
                status = 'ERROR'
                classification = 'ERROR'
            
            return {
                'slug': slug,
                'url': f"{self.base_url}{slug}",
                'final_url': '',
                'status': status,
                'classification': classification,
                'business_name': '',
                'business_indicators': 0,
                'error_indicators': 0,
                'indicators_found': [],
                'error_indicators_found': [],
                'page_title': '',
                'content_length': 0,
                'load_time': 0,
                'content_preview': '',
                'error': str(e),
                'tested_at': datetime.now().isoformat()
            }
        finally:
            try:
                driver.quit()
            except:
                pass

    def extract_business_name_enhanced(self, page_text, page_title):
        """Enhanced business name extraction"""
        # Try page title first
        if page_title and len(page_title) > 3 and 'widget' not in page_title.lower():
            return page_title.strip()
        
        # Try to find business name in content
        lines = page_text.split('\n')
        for line in lines[:15]:  # Check first 15 lines
            line = line.strip()
            if len(line) > 5 and len(line) < 100:
                # Look for lines that might be business names
                if any(word in line.lower() for word in ['clinic', 'health', 'medical', 'wellness', 'center', 'bar', 'drip', 'altura']):
                    return line
                # Look for lines with business-like patterns
                if '(' in line and ')' in line and any(state in line for state in ['TX', 'FL', 'CA', 'NY']):
                    return line
        
        return "Business name not found"

    def extract_services_from_content(self, content):
        """Extract services and prices from page content"""
        if not content:
            return []
        
        services = []
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if '$' in line:
                # Look for service lines with prices
                if any(service in line.lower() for service in ['injection', 'iv', 'vitamin', 'semaglutide', 'tirzepatide', 'consultation']):
                    # Clean up the line
                    clean_line = ' '.join(line.split())
                    if len(clean_line) < 100:  # Avoid very long lines
                        services.append(clean_line)
        
        return services[:5]  # Return max 5 services
    
    def save_progress(self):
        """Save current progress"""
        progress_data = {
            'instance_id': self.instance_id,
            'tested_count': self.tested_count,
            'found_count': len(self.found_slugs),
            'skipped_count': self.skipped_count,
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
        
        fieldnames = ['slug', 'url', 'final_url', 'status', 'classification', 'business_name',
                     'business_indicators', 'error_indicators', 'indicators_found', 
                     'error_indicators_found', 'page_title', 'content_length', 
                     'load_time', 'content_preview', 'tested_at']
        
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
    
    def cleanup_checkpoint(self):
        """Remove checkpoint file when scan completes successfully"""
        try:
            if os.path.exists(self.checkpoint_file):
                os.remove(self.checkpoint_file)
                print(f"🗑️  Checkpoint file cleaned up: {self.checkpoint_file}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up checkpoint file: {e}")
    
    def scan_comprehensive_range(self, resume=True):
        """Main scanning function with browser automation"""
        self.start_time = datetime.now().isoformat()
        
        # Set session start time
        self.session_data['session_info']['start_time'] = self.start_time
        
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
        
        scan_completed_successfully = False
        
        try:
            # Choose generator based on scanning mode
            if self.slug_file:
                slug_generator = self.generate_file_based_slugs(start_from)
            else:
                slug_generator = self.generate_range_combinations(start_from)
            
            for i, slug in enumerate(slug_generator):
                current_count = i + 1
                self.tested_count = current_count
                
                # Skip known slugs
                if slug in self.known_slugs:
                    print(f"🔍 [{current_count:,}] Testing: {slug}")
                    print(f"   ⏭️  Skipping known working slug")
                elif slug in self.tested_slugs:
                    print(f"🔍 [{current_count:,}] Testing: {slug}")
                    print(f"   ⏭️  Skipping previously tested slug")
                    self.skipped_count += 1
                else:
                    # Test individual slug with browser
                    result = self.test_slug_with_browser(slug, current_count)
                    
                    # Log the result (always log, regardless of type)
                    self.log_test_result(slug, result, "COMPREHENSIVE_SCAN")
                    
                    # Update session summary based on result
                    if result:
                        if result.get('status') == 'ACTIVE':
                            self.found_slugs.append(result)
                            self.session_data['session_summary']['active_found'] += 1
                            print(f"   ✅ SAVED! Total active businesses found: {len(self.found_slugs)}")
                        elif result.get('status') == 'CONNECTION_ERROR':
                            self.session_data['session_summary']['connection_errors'] += 1
                        elif result.get('status') == 'BROWSER_ERROR':
                            self.session_data['session_summary']['browser_errors'] += 1
                        elif result.get('status') == 'INACTIVE_401':
                            self.session_data['session_summary']['inactive_found'] += 1
                        elif result.get('status') == 'ERROR':
                            self.session_data['session_summary']['other_errors'] += 1
                    
                    # Update total tested count
                    self.session_data['session_summary']['total_tested'] += 1
                
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
            
            # If we reach here, the scan completed successfully
            scan_completed_successfully = True
        
        except KeyboardInterrupt:
            print("\n🛑 Scan interrupted by user")
        except Exception as e:
            print(f"❌ Error during scan: {e}")
        finally:
            self.save_progress()
            self.save_results()
            self.save_session_log()
            
            # Clean up checkpoint file if scan completed successfully
            if scan_completed_successfully:
                self.cleanup_checkpoint()
            
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
        print(f"�� Total combinations processed: {self.tested_count:,}")
        print(f"⏭️  Previously tested (skipped): {self.skipped_count:,}")
        print(f"🔍 New combinations tested: {self.tested_count - self.skipped_count:,}")
        print(f"🌟 Active business pages found: {len(self.found_slugs)}")
        
        # Show error summary
        connection_errors = self.session_data['session_summary']['connection_errors']
        browser_errors = self.session_data['session_summary']['browser_errors']
        other_errors = self.session_data['session_summary']['other_errors']
        
        if connection_errors > 0 or browser_errors > 0 or other_errors > 0:
            print(f"🔧 Errors logged for retry: {connection_errors} connection, {browser_errors} browser, {other_errors} other")
        
        print(f"⏱️  Scan duration: {duration}")
        print(f"💾 Results saved to: {self.results_file}")
        print(f"📋 Session log saved to: {self.session_log_file}")
        
        if self.found_slugs:
            print(f"\n🔍 DISCOVERED ACTIVE BUSINESS PAGES:")
            for result in self.found_slugs:
                print(f"  • {result['slug']}: {result['business_indicators']} indicators - {result['content_length']} chars")
        else:
            print(f"\n❌ No new active business pages found in range {self.start_range} to {self.end_range}")
            if self.skipped_count > 0:
                print(f"💡 Note: {self.skipped_count:,} slugs were skipped as already tested")

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
    import argparse
    
    parser = argparse.ArgumentParser(description='VSDHOne Browser-Based Comprehensive Scanner')
    parser.add_argument('--file', '-f', help='File containing slugs to test (one per line)')
    parser.add_argument('--instance-id', '-i', help='Instance ID for parallel execution')
    parser.add_argument('--start-range', '-s', help='Start range for range-based scanning')
    parser.add_argument('--end-range', '-e', help='End range for range-based scanning')
    parser.add_argument('--predefined', '-p', choices=['1', '2', '3'], help='Use predefined range (1/2/3)')
    
    args = parser.parse_args()
    
    print("🌐 VSDHOne Browser-Based Comprehensive Scanner")
    print("=" * 60)
    
    instance_id = args.instance_id
    slug_file = args.file
    
    if slug_file:
        if not os.path.exists(slug_file):
            print(f"❌ Error: File {slug_file} not found")
            return
        
        print(f"📂 File-based scanning mode: {slug_file}")
        scanner = BrowserComprehensiveScanner(instance_id, slug_file=slug_file)
        
    else:
        # Range-based scanning
        if args.predefined:
            instance_num = int(args.predefined)
            start_range, end_range = get_range_for_instance(instance_num)
            print(f"📊 Instance {instance_num} will scan: {start_range} to {end_range}")
        else:
            start_range = args.start_range or 'aaaaa'
            end_range = args.end_range or 'zzzzz'
        
        print(f"📊 Range-based scanning mode: {start_range} to {end_range}")
        scanner = BrowserComprehensiveScanner(instance_id, start_range, end_range)
    
    print(f"\n⚠️  WARNING: Browser-based scanning is VERY slow!")
    print(f"✅ Checkpoints saved every 50 slugs for easy resuming")
    print(f"🚀 Starting scan automatically...")
    
    scanner.scan_comprehensive_range()

if __name__ == "__main__":
    main() 