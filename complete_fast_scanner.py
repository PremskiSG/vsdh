#!/usr/bin/env python3
"""
Complete Fast Scanner for VSDHOne Platform
All features of comprehensive scanner + optimized speed

Features:
✅ Checkpoint/Resume capability
✅ Range-based and file-based scanning  
✅ Skip previously tested slugs
✅ Progress saving every 50 slugs
✅ Graceful signal handling
✅ Parallel execution safety
✅ CSV and JSON output
✅ Predefined ranges for easy parallel setup
✅ 2x faster than comprehensive scanner
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
import glob
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

class CompleteFastScanner:
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
        
        # OPTIMIZED performance settings (2x faster than comprehensive)
        self.page_load_timeout = 8   # Reduced from 15s
        self.js_wait_time = 2        # Reduced from 3s  
        self.requests_per_second = 10.0  # Doubled from 5 (0.1s between tests)
        
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
            session_prefix = f"SESSION_FAST_{hostname}_{file_base}_{timestamp}"
        else:
            session_prefix = f"SESSION_FAST_{hostname}_{self.instance_id}_{timestamp}"
        
        # Store all files in logs folder
        self.results_file = f"logs/{session_prefix}_results.csv"
        self.progress_file = f"logs/{session_prefix}_progress.json"
        self.session_log_file = f"logs/{session_prefix}_session.json"
        
        # Create persistent checkpoint file (no timestamp for resume capability)
        if self.slug_file:
            file_base = os.path.splitext(os.path.basename(self.slug_file))[0]
            self.checkpoint_file = f"logs/CHECKPOINT_FAST_{hostname}_{file_base}.txt"
        else:
            self.checkpoint_file = f"logs/CHECKPOINT_FAST_{hostname}_{self.instance_id}.txt"
        
        # Initialize session log data
        self.session_data = {
            'session_info': {
                'session_id': session_prefix,
                'hostname': hostname,
                'instance_id': self.instance_id,
                'start_time': None,
                'end_time': None,
                'session_type': 'FAST_COMPREHENSIVE_SCAN',
                'range_start': self.start_range,
                'range_end': self.end_range,
                'scanner_version': '3.0_complete_fast'
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
        
        print(f"🚀 Complete Fast Scanner (Instance: {self.instance_id})")
        print(f"📊 Range: {self.start_range} to {self.end_range}")
        print(f"⚡ Rate limit: {self.requests_per_second} pages/second (2x faster)")
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
    
    def generate_range_combinations(self, start_from=None):
        """Generate combinations within specified range"""
        print(f"🔢 Generating combinations from {self.start_range} to {self.end_range}")
        
        def slug_to_number(slug):
            """Convert slug to number for comparison"""
            result = 0
            for char in slug:
                if char.isdigit():
                    result = result * 36 + int(char)
                else:
                    result = result * 36 + (ord(char) - ord('a') + 10)
            return result
        
        start_num = slug_to_number(self.start_range)
        end_num = slug_to_number(self.end_range)
        
        # Handle resume from checkpoint
        if start_from:
            resume_num = slug_to_number(start_from)
            start_num = max(start_num, resume_num)
            print(f"📍 Resuming from: {start_from} (number: {resume_num})")
        
        def number_to_slug(num):
            """Convert number back to slug"""
            slug = ""
            for _ in range(5):
                remainder = num % 36
                if remainder < 10:
                    slug = str(remainder) + slug
                else:
                    slug = chr(ord('a') + remainder - 10) + slug
                num //= 36
            return slug
        
        for num in range(start_num, end_num + 1):
            yield number_to_slug(num)
    
    def setup_optimized_driver(self):
        """Setup optimized Chrome driver for maximum speed"""
        options = Options()
        
        # Basic headless setup
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # SPEED OPTIMIZATIONS
        options.add_argument('--disable-images')           # Don't load images
        options.add_argument('--disable-extensions')       # No extensions
        options.add_argument('--disable-plugins')          # No plugins
        options.add_argument('--disable-web-security')     # Skip security checks
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        
        # Memory optimizations
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        
        # Network optimizations
        options.add_argument('--aggressive-cache-discard')
        options.add_argument('--disable-background-networking')
        
        # Logging
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')
        
        # Unique user data directory for parallel execution
        user_data_dir = f"/tmp/chrome_fast_{self.instance_id}_{os.getpid()}"
        options.add_argument(f'--user-data-dir={user_data_dir}')
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(self.page_load_timeout)
        
        return driver
    
    def test_slug_with_browser(self, slug, current_count):
        """Test a single slug using optimized browser automation"""
        driver = None
        start_test_time = time.time()
        
        try:
            driver = self.setup_optimized_driver()
            url = f"{self.base_url}{slug}"
            
            print(f"🔍 [{current_count:,}] Testing: {slug}")
            print(f"   🌐 Loading: {url}")
            
            # Navigate to the page
            driver.get(url)
            
            # OPTIMIZED: Reduced wait time for React
            time.sleep(self.js_wait_time)
            
            # Get final URL after any redirects
            final_url = driver.current_url
            
            # Get page source and title
            page_title = driver.title
            
            try:
                body_element = driver.find_element(By.TAG_NAME, 'body')
                page_text = body_element.text.strip()
            except:
                page_text = ""
            
            # Analyze the content
            result = self.analyze_page_content(page_text, page_title, final_url, slug)
            result['load_time'] = time.time() - start_test_time
            result['slug'] = slug  # Ensure slug is stored in result
            
            # Print result in comprehensive scanner format
            if result['status'] == 'ACTIVE':
                print(f"   🌟 ACTIVE BUSINESS PAGE - {result.get('business_name', '')}")
                print(f"   📊 Business Indicators: {result.get('business_indicators', 0)}")
                print(f"   📄 Page Title: {result.get('page_title', '')}")
                print(f"   📏 Content Length: {result.get('content_length', 0)} chars")
                print(f"   ⏱️  Load Time: {result['load_time']:.2f} seconds")
                if final_url != url:
                    print(f"   🔗 Final URL: {final_url}")
                if result.get('services'):
                    print(f"   💰 Services Found: {', '.join(result['services'][:3])}")
            elif result['status'] == 'INACTIVE_401':
                print(f"   🚫 INACTIVE_401 - Error Page")
                print(f"   📏 Content Length: {result.get('content_length', 0)} chars")
                print(f"   🔗 Final URL: {result.get('final_url', '')}")
                if result.get('error_indicators', 0) > 0:
                    print(f"   🔍 Error Indicators Found: {result.get('error_indicators', 0)} detected")
            else:
                print(f"   ⚠️  {result['status']}")
                print(f"   📏 Content Length: {result.get('content_length', 0)} chars")
                if final_url != url:
                    print(f"   🔗 Final URL: {final_url}")
                if result.get('business_indicators', 0) > 0:
                    print(f"   📊 Business Indicators: {result.get('business_indicators', 0)}")
            
            return result
            
        except TimeoutException:
            error_msg = f"BROWSER_ERROR: Page load timeout for {slug}"
            print(f"   🌐 CONNECTION ERROR - Logging for retry: Page load timeout")
            return {
                'status': 'TIMEOUT',
                'error': error_msg,
                'load_time': time.time() - start_test_time,
                'final_url': url,
                'slug': slug
            }
            
        except WebDriverException as e:
            error_msg = f"BROWSER_ERROR: WebDriver error for {slug}: {str(e)}"
            print(f"   🔧 BROWSER ERROR - Logging for retry: {str(e)[:100]}")
            return {
                'status': 'BROWSER_ERROR',
                'error': error_msg,
                'load_time': time.time() - start_test_time,
                'final_url': url,
                'slug': slug
            }
            
        except Exception as e:
            error_msg = f"ERROR: Unexpected error for {slug}: {str(e)}"
            print(f"   ❌ UNKNOWN ERROR - Logging for retry: {str(e)[:100]}")
            return {
                'status': 'ERROR',
                'error': error_msg,
                'load_time': time.time() - start_test_time,
                'final_url': url,
                'slug': slug
            }
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def analyze_page_content(self, page_text, page_title, final_url, slug):
        """Analyze page content to determine if business is active"""
        content_lower = page_text.lower()
        title_lower = page_title.lower()
        
        # Check for error indicators first
        error_indicators = 0
        business_indicators = 0
        
        # Strong error indicators
        error_patterns = [
            '401', 'error', 'nothing left to do here', 'go to homepage',
            'unauthorized', 'access denied', 'not found'
        ]
        
        # Business content indicators
        business_patterns = [
            'altura health', 'dripbar', 'wellness', 'clinic', 'medical', 'health',
            'therapy', 'treatment', 'spa', 'center', 'institute', 'practice',
            'weight loss', 'injection', 'iv therapy', 'hydration', 'vitamin',
            'consultation', 'appointment', 'booking', 'schedule', 'service',
            'contact', 'location', 'address', 'phone', 'email', 'hours',
            'book now', 'schedule appointment', 'select service', 'choose time'
        ]
        
        # Count indicators
        for pattern in error_patterns:
            if pattern in content_lower:
                error_indicators += 1
        
        for pattern in business_patterns:
            if pattern in content_lower:
                business_indicators += 1
        
        # Determine status
        if error_indicators > 0 or '401' in page_text or 'nothing left to do here' in content_lower:
            status = 'INACTIVE_401'
        elif business_indicators >= 3 or any(name in content_lower for name in ['altura health', 'dripbar']):
            status = 'ACTIVE'
        elif len(page_text) > 500 and business_indicators > 0:
            status = 'POTENTIALLY_ACTIVE'
        else:
            status = 'INACTIVE_UNKNOWN'
        
        # Extract business name
        business_name = self.extract_business_name_enhanced(page_text, page_title)
        
        # Extract services
        services = self.extract_services_from_content(page_text)
        
        return {
            'status': status,
            'business_name': business_name,
            'services': services,
            'content_length': len(page_text),
            'business_indicators': business_indicators,
            'error_indicators': error_indicators,
            'final_url': final_url,
            'page_title': page_title
        }
    
    def extract_business_name_enhanced(self, page_text, page_title):
        """Extract business name from page content"""
        # Known business patterns
        if 'altura health' in page_text.lower():
            return 'Altura Health'
        elif 'dripbar' in page_text.lower():
            return 'The DRIPBaR'
        elif page_title and page_title != 'VSDHOne' and page_title.strip():
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
    
    def extract_services_from_content(self, content):
        """Extract services from page content"""
        services = []
        service_keywords = [
            'weight loss', 'iv therapy', 'hydration', 'vitamin injection',
            'consultation', 'wellness', 'treatment', 'therapy'
        ]
        
        content_lower = content.lower()
        for service in service_keywords:
            if service in content_lower:
                services.append(service.title())
        
        return services[:5]  # Limit to first 5 services
    
    def log_test_result(self, slug, result, test_type="FAST_COMPREHENSIVE_SCAN"):
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
    
    def save_progress(self):
        """Save current progress to JSON file"""
        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'tested_count': self.tested_count,
            'skipped_count': self.skipped_count,
            'found_slugs_count': len(self.found_slugs),
            'session_info': self.session_data['session_info'],
            'found_businesses': [
                {
                    'slug': result.get('slug', ''),
                    'business_name': result.get('business_name', ''),
                    'status': result.get('status', '')
                }
                for result in self.found_slugs
            ]
        }
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Error saving progress: {e}")
    
    def save_results(self):
        """Save results to CSV file"""
        try:
            with open(self.results_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'slug', 'status', 'business_name', 'services', 'load_time',
                    'content_length', 'business_indicators', 'error_indicators',
                    'final_url', 'page_title', 'timestamp'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in self.found_slugs:
                    writer.writerow({
                        'slug': result.get('slug', ''),
                        'status': result.get('status', ''),
                        'business_name': result.get('business_name', ''),
                        'services': ', '.join(result.get('services', [])),
                        'load_time': result.get('load_time', 0),
                        'content_length': result.get('content_length', 0),
                        'business_indicators': result.get('business_indicators', 0),
                        'error_indicators': result.get('error_indicators', 0),
                        'final_url': result.get('final_url', ''),
                        'page_title': result.get('page_title', ''),
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"⚠️  Error saving results: {e}")
    
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
        """Main scanning function with all comprehensive features + speed optimizations"""
        self.start_time = datetime.now().isoformat()
        
        # Set session start time
        self.session_data['session_info']['start_time'] = self.start_time
        
        # Check if resuming
        start_from = None
        if resume:
            start_from = self.load_checkpoint()
        
        print(f"🚀 Starting complete fast scan at {self.start_time}")
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
                    self.skipped_count += 1
                elif slug in self.tested_slugs:
                    print(f"🔍 [{current_count:,}] Testing: {slug}")
                    print(f"   ⏭️  Skipping previously tested slug")
                    self.skipped_count += 1
                else:
                    # Test individual slug with OPTIMIZED browser
                    result = self.test_slug_with_browser(slug, current_count)
                    
                    # Log the result (always log, regardless of type)
                    self.log_test_result(slug, result, "FAST_COMPREHENSIVE_SCAN")
                    
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
                
                # OPTIMIZED: Faster rate limiting (0.1s vs 0.2s)
                time.sleep(1.0 / self.requests_per_second)
                
                # Checkpoint every N slugs
                if current_count % self.checkpoint_interval == 0:
                    self.save_checkpoint(slug)
                    
                    elapsed = (datetime.now() - datetime.fromisoformat(self.start_time)).total_seconds()
                    rate = current_count / elapsed if elapsed > 0 else 0
                    
                    print(f"\n📍 CHECKPOINT #{current_count // self.checkpoint_interval}")
                    print(f"📊 Progress: {current_count:,} tested in range")
                    print(f"🌟 Active businesses found: {len(self.found_slugs)}")
                    print(f"⚡ Rate: {rate:.2f} slugs/sec (FAST)")
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
        
        print(f"\n🎯 COMPLETE FAST SCAN COMPLETE (Instance: {self.instance_id})")
        print(f"=" * 70)
        print(f"📊 Range scanned: {self.start_range} to {self.end_range}")
        print(f"🧮 Total combinations processed: {self.tested_count:,}")
        print(f"⏭️  Previously tested (skipped): {self.skipped_count:,}")
        print(f"🔍 New combinations tested: {self.tested_count - self.skipped_count:,}")
        print(f"🌟 Active business pages found: {len(self.found_slugs)}")
        
        # Show error summary
        connection_errors = self.session_data['session_summary']['connection_errors']
        browser_errors = self.session_data['session_summary']['browser_errors']
        other_errors = self.session_data['session_summary']['other_errors']
        
        if connection_errors > 0 or browser_errors > 0 or other_errors > 0:
            print(f"🔧 Errors logged for retry: {connection_errors} connection, {browser_errors} browser, {other_errors} other")
        
        # Calculate performance metrics
        if self.session_data['testing_results']:
            total_time = sum(r['load_time'] for r in self.session_data['testing_results'])
            avg_time = total_time / len(self.session_data['testing_results'])
            print(f"⚡ Average test time: {avg_time:.2f}s per slug (OPTIMIZED)")
            print(f"🚀 Theoretical max rate: {3600/avg_time:.0f} slugs/hour")
        
        print(f"⏱️  Scan duration: {duration}")
        print(f"💾 Results saved to: {self.results_file}")
        print(f"📋 Session log saved to: {self.session_log_file}")
        
        if self.found_slugs:
            print(f"\n🔍 DISCOVERED ACTIVE BUSINESS PAGES:")
            for result in self.found_slugs:
                services_str = ', '.join(result.get('services', [])[:3])
                print(f"  • {result['slug']}: {result.get('business_name', 'Unknown')} - {services_str}")
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
    
    parser = argparse.ArgumentParser(description='VSDHOne Complete Fast Scanner')
    parser.add_argument('--file', '-f', help='File containing slugs to test (one per line)')
    parser.add_argument('--instance-id', '-i', help='Instance ID for parallel execution')
    parser.add_argument('--start-range', '-s', help='Start range for range-based scanning')
    parser.add_argument('--end-range', '-e', help='End range for range-based scanning')
    parser.add_argument('--predefined', '-p', choices=['1', '2', '3'], help='Use predefined range (1/2/3)')
    parser.add_argument('--force-test', action='store_true', help='Force test all slugs (ignore known/tested lists)')
    
    args = parser.parse_args()
    
    print("🚀 VSDHOne Complete Fast Scanner")
    print("=" * 60)
    print("⚡ All comprehensive features + 2x speed optimization")
    print("")
    
    instance_id = args.instance_id
    slug_file = args.file
    
    if slug_file:
        if not os.path.exists(slug_file):
            print(f"❌ Error: File {slug_file} not found")
            return
        
        print(f"📂 File-based scanning mode: {slug_file}")
        scanner = CompleteFastScanner(instance_id, slug_file=slug_file)
        
        # Handle force test mode
        if args.force_test:
            print("🔥 FORCE TEST MODE: Will test all slugs regardless of known/tested status")
            scanner.known_slugs = set()  # Clear known slugs
            scanner.tested_slugs = set()  # Clear tested slugs
        
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
        scanner = CompleteFastScanner(instance_id, start_range, end_range)
        
        # Handle force test mode
        if args.force_test:
            print("🔥 FORCE TEST MODE: Will test all slugs regardless of known/tested status")
            scanner.known_slugs = set()  # Clear known slugs
            scanner.tested_slugs = set()  # Clear tested slugs
    
    print(f"\n✅ All comprehensive features included:")
    print(f"   📍 Checkpoint/Resume capability")
    print(f"   📊 Range-based and file-based scanning")
    print(f"   ⏭️  Skip previously tested slugs")
    print(f"   💾 Progress saving every 50 slugs")
    print(f"   🛑 Graceful signal handling")
    print(f"   🔄 Parallel execution safety")
    print(f"   📄 CSV and JSON output")
    print(f"   ⚡ 2x speed optimization")
    print(f"\n🚀 Starting scan automatically...")
    
    scanner.scan_comprehensive_range()

if __name__ == "__main__":
    main()
