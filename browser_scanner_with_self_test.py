#!/usr/bin/env python3
"""
Browser-Based Comprehensive Scanner for VSDHOne with Self-Testing
Scans all 60,466,176 combinations using browser automation
Supports parallel execution with range-based distribution
Now includes self-testing mode for validation
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
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from threading import Lock
from selenium.common.exceptions import TimeoutException, WebDriverException
import glob

class BrowserComprehensiveScanner:
    def __init__(self, instance_id=None, start_range=None, end_range=None, self_test=False):
        # Generate unique instance ID if not provided
        if instance_id is None:
            instance_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        self.instance_id = instance_id
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        self.self_test = self_test
        
        # Character set: 0-9 + a-z (ASCII order for proper string comparison)
        self.charset = string.digits + string.ascii_lowercase  # 36 characters
        self.total_combinations = 36 ** 5  # 60,466,176
        
        # Range handling for parallel execution
        self.start_range = start_range or 'aaaaa'
        self.end_range = end_range or 'zzzzz'
        
        # Load tested slugs from database to avoid retesting (skip in self-test mode)
        if not self_test:
            self.tested_slugs = self.load_tested_slugs_database()
            print(f"📚 Loaded {len(self.tested_slugs)} previously tested slugs from database")
        else:
            self.tested_slugs = set()
            print("🧪 Self-test mode: Will test validation slugs regardless of database")
        
        # Known working slugs
        self.known_active_slugs = {
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
        self.requests_per_second = 0.3  # Very conservative for browser automation
        
        # Unique file names for parallel execution
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if self_test:
            self.results_file = f"browser_self_test_results_{timestamp}.csv"
            self.checkpoint_file = f"browser_self_test_checkpoint_{timestamp}.txt"
            self.progress_file = f"browser_self_test_progress_{timestamp}.json"
        else:
            self.results_file = f"browser_comprehensive_results_{self.instance_id}_{timestamp}.csv"
            self.checkpoint_file = f"browser_comprehensive_checkpoint_{self.instance_id}_{timestamp}.txt"
            self.progress_file = f"browser_comprehensive_progress_{self.instance_id}_{timestamp}.json"
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        if self_test:
            print(f"🧪 Browser Self-Test Mode")
            print(f"📊 Will test 30 validation slugs (15 active + 15 inactive)")
        else:
            print(f"🌐 Browser-Based Comprehensive Scanner (Instance: {self.instance_id})")
            print(f"📊 Range: {self.start_range} to {self.end_range}")
        
        print(f"🔄 Rate limit: {self.requests_per_second} pages/second")
        print(f"📍 Checkpoint every: {self.checkpoint_interval} slugs")
        print(f"💾 Results file: {self.results_file}")
        print(f"📍 Checkpoint file: {self.checkpoint_file}")
        print("")
    
    def load_tested_slugs_database(self):
        """Load previously tested slugs from the most recent database file"""
        tested_slugs = set()
        
        # Find the most recent slug database JSON file
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
    
    def signal_handler(self, signum, frame):
        """Handle graceful shutdown"""
        print(f"\n🛑 Received signal {signum}. Saving progress...")
        self.save_progress()
        self.save_results()
        print("✅ Progress saved. Exiting...")
        sys.exit(0)
    
    def get_self_test_slugs(self):
        """Get 10 slugs for self-testing: 5 known active + 5 known inactive (randomly selected)"""
        test_slugs = []
        
        # Randomly select 5 from the 15 known active businesses
        active_slugs = list(self.known_active_slugs)
        selected_active = random.sample(active_slugs, min(5, len(active_slugs)))
        test_slugs.extend(selected_active)
        
        # Get inactive slugs from database
        inactive_slugs = []
        
        # Try to load from database
        json_files = glob.glob("vsdhone_*database*.json")
        if json_files:
            latest_file = max(json_files, key=os.path.getctime)
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    database = json.load(f)
                
                # Get inactive slugs
                for slug_data in database.get('all_slugs', []):
                    if (slug_data['status'] == 'INACTIVE_401' and 
                        slug_data['slug'] not in self.known_active_slugs):
                        inactive_slugs.append(slug_data['slug'])
                            
            except Exception as e:
                print(f"⚠️  Error loading database for self-test: {e}")
        
        # If we don't have enough inactive slugs, add some known 401 slugs
        if len(inactive_slugs) < 20:
            known_inactive = [
                'aaaaa', 'aaaab', 'aaaac', 'aaaad', 'aaaae',
                'zzzzz', 'zzzzy', 'zzzzx', 'zzzzw', 'zzzzv',
                '00000', '00001', '00002', '00003', '00004',
                'bbbbb', 'ccccc', 'ddddd', 'eeeee', 'fffff'
            ]
            
            for slug in known_inactive:
                if slug not in self.known_active_slugs and slug not in inactive_slugs:
                    inactive_slugs.append(slug)
        
        # Randomly select 5 inactive slugs
        if len(inactive_slugs) >= 5:
            selected_inactive = random.sample(inactive_slugs, 5)
        else:
            selected_inactive = inactive_slugs[:5]
        
        test_slugs.extend(selected_inactive)
        
        # Shuffle for random order
        random.shuffle(test_slugs)
        
        print(f"🧪 Self-test will validate {len(test_slugs)} slugs:")
        print(f"   ✅ Expected active: {len([s for s in test_slugs if s in self.known_active_slugs])}")
        print(f"   ❌ Expected inactive: {len([s for s in test_slugs if s not in self.known_active_slugs])}")
        print(f"   🎲 Active slugs selected: {', '.join(selected_active)}")
        print(f"   🎲 Inactive slugs selected: {', '.join(selected_inactive)}")
        print("")
        
        return test_slugs

    def run_self_test(self):
        """Run self-test mode to validate scanner accuracy"""
        print("🧪 Starting Self-Test Mode...")
        print("=" * 60)
        
        test_slugs = self.get_self_test_slugs()
        
        correct_predictions = 0
        total_tests = len(test_slugs)
        
        results = []
        
        for i, slug in enumerate(test_slugs, 1):
            expected_status = "ACTIVE" if slug in self.known_active_slugs else "INACTIVE_401"
            
            print(f"\n🔍 [{i}/{total_tests}] Testing: {slug}")
            print(f"   📋 Expected: {expected_status}")
            
            # Test the slug using modified browser test for self-test
            result = self.test_slug_for_self_test(slug, i)
            
            if result and result['status'] != 'ERROR':
                actual_status = result['status']
                is_correct = (actual_status == expected_status)
                
                if is_correct:
                    correct_predictions += 1
                    print(f"   ✅ CORRECT: {actual_status}")
                else:
                    print(f"   ❌ INCORRECT: Expected {expected_status}, got {actual_status}")
                
                # Print detailed results
                if actual_status == "ACTIVE":
                    print(f"   🏢 Business Name: {result.get('business_name', 'Not found')}")
                    print(f"   📊 Business Indicators: {result.get('business_indicators', 0)}")
                    print(f"   📄 Page Title: {result.get('page_title', 'No title')}")
                    print(f"   📏 Content Length: {result.get('content_length', 0)} chars")
                    print(f"   ⏱️  Load Time: {result.get('load_time', 0):.2f} seconds")
                    
                    # Show all business indicators found
                    indicators_found = result.get('indicators_found', [])
                    if indicators_found:
                        print(f"   🔍 Business Indicators Found: {', '.join(indicators_found)}")
                    
                    # Extract and show services/pricing if available
                    services = self.extract_services_from_content(result.get('content_preview', ''))
                    if services:
                        print(f"   💰 Services Found: {', '.join(services[:3])}")
                elif actual_status == "INACTIVE_401":
                    print(f"   🚫 Error Indicators: {result.get('error_indicators', 0)}")
                    print(f"   📏 Content Length: {result.get('content_length', 0)} chars")
                    print(f"   🔗 Final URL: {result.get('final_url', 'Unknown')}")
                    
                    # Show all error indicators found
                    error_indicators_found = result.get('error_indicators_found', [])
                    if error_indicators_found:
                        print(f"   🔍 Error Indicators Found: {', '.join(error_indicators_found)}")
                
                # Add to results
                result['expected_status'] = expected_status
                result['is_correct'] = is_correct
                results.append(result)
            else:
                print(f"   ⚠️  ERROR: Could not test slug - {result.get('error', 'Unknown error') if result else 'No result'}")
                results.append({
                    'slug': slug,
                    'expected_status': expected_status,
                    'status': 'ERROR',
                    'is_correct': False,
                    'error': result.get('error', 'Unknown error') if result else 'No result returned'
                })
            
            # Small delay between tests
            if i < total_tests:  # Don't delay after the last test
                print(f"   ⏳ Waiting 1.5 seconds before next test...")
                time.sleep(1.5)
        
        # Calculate accuracy
        accuracy = (correct_predictions / total_tests) * 100
        
        print(f"\n🎯 SELF-TEST RESULTS:")
        print(f"=" * 60)
        print(f"📊 Total tests: {total_tests}")
        print(f"✅ Correct predictions: {correct_predictions}")
        print(f"❌ Incorrect predictions: {total_tests - correct_predictions}")
        print(f"🎯 Accuracy: {accuracy:.1f}%")
        
        # Show breakdown by type
        active_tests = [r for r in results if r['expected_status'] == 'ACTIVE']
        inactive_tests = [r for r in results if r['expected_status'] == 'INACTIVE_401']
        
        active_correct = sum(1 for r in active_tests if r.get('is_correct', False))
        inactive_correct = sum(1 for r in inactive_tests if r.get('is_correct', False))
        
        print(f"\n📈 BREAKDOWN BY TYPE:")
        print(f"   🟢 Active Business Detection: {active_correct}/{len(active_tests)} correct ({(active_correct/len(active_tests)*100):.1f}%)")
        print(f"   🔴 Inactive Page Detection: {inactive_correct}/{len(inactive_tests)} correct ({(inactive_correct/len(inactive_tests)*100):.1f}%)")
        
        # Save detailed results
        self.save_self_test_results(results, accuracy)
        
        if accuracy >= 95:
            print(f"\n🎉 EXCELLENT: Scanner is working correctly!")
        elif accuracy >= 85:
            print(f"\n✅ GOOD: Scanner is mostly accurate")
        else:
            print(f"\n⚠️  WARNING: Scanner accuracy is below 85%")
        
        return accuracy

    def test_slug_for_self_test(self, slug, current_count):
        """Test a single slug for self-testing (returns status regardless of result)"""
        driver = self.setup_driver()
        
        try:
            url = f"{self.base_url}{slug}"
            
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
            
            # Determine status
            if is_error_page:
                status = "INACTIVE_401"
                classification = "401_ERROR"
            elif is_business_page:
                status = "ACTIVE"
                classification = "ACTIVE_BUSINESS"
            else:
                status = "UNKNOWN"
                classification = "UNCLEAR"
            
            # Extract business name with better logic
            business_name = ""
            if is_business_page:
                business_name = self.extract_business_name_enhanced(page_text, page_title)
            
            return {
                'slug': slug,
                'status': status,
                'url': url,
                'final_url': final_url,
                'classification': classification,
                'business_name': business_name,
                'page_title': page_title,
                'business_indicators': business_count,
                'error_indicators': error_count,
                'indicators_found': [indicator for indicator in business_indicators if indicator in page_text_lower],
                'error_indicators_found': [indicator for indicator in error_indicators if indicator in page_text_lower],
                'content_length': len(page_text),
                'load_time': load_time,
                'content_preview': page_text[:500] + "..." if len(page_text) > 500 else page_text,
                'tested_at': datetime.now().isoformat()
            }
                
        except Exception as e:
            return {
                'slug': slug,
                'status': 'ERROR',
                'error': str(e)
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

    def save_self_test_results(self, results, accuracy):
        """Save self-test results to CSV"""
        fieldnames = [
            'slug', 'expected_status', 'status', 'is_correct', 'business_name',
            'url', 'final_url', 'page_title', 'content_length', 'business_indicators',
            'error_indicators', 'classification', 'indicators_found', 'error_indicators_found',
            'content_preview', 'load_time', 'tested_at'
        ]
        
        with open(self.results_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                # Fill in missing fields
                for field in fieldnames:
                    if field not in result:
                        result[field] = ''
                
                writer.writerow(result)
        
        print(f"💾 Self-test results saved to: {self.results_file}")
        
        # Also save summary
        summary_file = f"browser_self_test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        summary = {
            'test_date': datetime.now().isoformat(),
            'total_tests': len(results),
            'correct_predictions': sum(1 for r in results if r.get('is_correct', False)),
            'accuracy_percentage': accuracy,
            'active_slugs_tested': len([r for r in results if r['expected_status'] == 'ACTIVE']),
            'inactive_slugs_tested': len([r for r in results if r['expected_status'] == 'INACTIVE_401']),
            'detailed_results': results
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Self-test summary saved to: {summary_file}")
    
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
                if slug in self.known_active_slugs:
                    print(f"🔍 [{current_count:,}] Testing: {slug}")
                    print(f"   ⏭️  Skipping known working slug")
                elif slug in self.tested_slugs:
                    print(f"🔍 [{current_count:,}] Testing: {slug}")
                    print(f"   ⏭️  Skipping previously tested slug")
                    self.skipped_count += 1
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
        print(f"📊 Total combinations processed: {self.tested_count:,}")
        print(f"⏭️  Previously tested (skipped): {self.skipped_count:,}")
        print(f"🔍 New combinations tested: {self.tested_count - self.skipped_count:,}")
        print(f"🌟 Active business pages found: {len(self.found_slugs)}")
        print(f"⏱️  Scan duration: {duration}")
        print(f"💾 Results saved to: {self.results_file}")
        
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
    parser = argparse.ArgumentParser(description='VSDHOne Browser-Based Comprehensive Scanner')
    parser.add_argument('--self-test', action='store_true', 
                       help='Run self-test mode to validate scanner accuracy')
    parser.add_argument('--instance-id', type=str, 
                       help='Instance ID for parallel execution')
    parser.add_argument('--range', type=str, 
                       help='Range in format start-end (e.g., aaaaa-bbbbb)')
    
    args = parser.parse_args()
    
    if args.self_test:
        print("🧪 VSDHOne Browser Scanner - Self-Test Mode")
        print("=" * 60)
        scanner = BrowserComprehensiveScanner(self_test=True)
        accuracy = scanner.run_self_test()
        return
    
    print("🌐 VSDHOne Browser-Based Comprehensive Scanner")
    print("=" * 60)
    
    # Get parameters
    instance_id = args.instance_id
    if not instance_id:
        instance_id = input("Enter instance ID (default: auto): ").strip()
        if not instance_id:
            instance_id = None
    
    if args.range:
        try:
            start_range, end_range = args.range.split('-')
        except ValueError:
            print("❌ Invalid range format. Use: start-end (e.g., aaaaa-bbbbb)")
            return
    else:
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