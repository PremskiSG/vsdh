#!/usr/bin/env python3
"""
Browser-Based Self-Test Scanner for VSDHOne
Tests 6 specific slugs (4 active + 2 known errors) to validate scanner functionality
Based on the comprehensive scanner with identical logic
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

class BrowserSelfTestScanner:
    def __init__(self, instance_id=None):
        # Generate unique instance ID if not provided
        if instance_id is None:
            instance_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        self.instance_id = instance_id
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        
        # Character set: 0-9 + a-z (ASCII order for proper string comparison)
        self.charset = string.digits + string.ascii_lowercase  # 36 characters
        self.total_combinations = 36 ** 5  # 60,466,176
        
        # Self-test specific slugs: 4 active + 2 known errors
        self.test_slugs = [
            # 4 known active slugs
            'ad31y', 'mj42f', 'os27m', 'lp56a',
            # 2 known error/inactive slugs (these should return 401 or similar)
            'aaaaa', 'zzzzz'
        ]
        
        # Known working slugs (all 15 for reference)
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
        
        session_prefix = f"SESSION_SELFTEST_{hostname}_{self.instance_id}_{timestamp}"
        
        # Store all files in logs folder
        self.results_file = f"logs/{session_prefix}_results.csv"
        self.checkpoint_file = f"logs/{session_prefix}_checkpoint.txt"
        self.progress_file = f"logs/{session_prefix}_progress.json"
        self.session_log_file = f"logs/{session_prefix}_session.json"
        
        # Initialize session log data
        self.session_data = {
            'session_info': {
                'session_id': session_prefix,
                'hostname': hostname,
                'instance_id': self.instance_id,
                'start_time': None,
                'end_time': None,
                'session_type': 'SELF_TEST',
                'range_start': 'SELF_TEST_6_SLUGS',
                'range_end': 'SELF_TEST_6_SLUGS',
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
        
        print(f"🧪 Browser-Based Self-Test Scanner (Instance: {self.instance_id})")
        print(f"📊 Testing 6 slugs: 4 active + 2 known errors")
        print(f"🔄 Rate limit: {self.requests_per_second} pages/second")
        print(f"💾 Results file: {self.results_file}")
        print(f"📋 Session log file: {self.session_log_file}")
        print("")
    
    def log_test_result(self, slug, result, test_type="SELF_TEST"):
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
        elif result and 'CONNECTION_ERROR' in result.get('error', ''):
            self.session_data['session_summary']['connection_errors'] += 1
        elif result and 'BROWSER_ERROR' in result.get('error', ''):
            self.session_data['session_summary']['browser_errors'] += 1
        else:
            self.session_data['session_summary']['other_errors'] += 1
    
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
        
        try:
            with open(self.session_log_file, 'w') as f:
                json.dump(self.session_data, f, indent=2)
            print(f"💾 Session log saved to: {self.session_log_file}")
        except Exception as e:
            print(f"⚠️  Error saving session log: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {signum}. Shutting down gracefully...")
        self.save_session_log()
        sys.exit(0)
    
    def setup_driver(self):
        """Set up Chrome WebDriver with proper options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")  # Disable JS for faster loading
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(self.page_load_timeout)
        return driver
    
    def test_slug_with_browser(self, slug, current_count):
        """Test a single slug using browser automation - identical to comprehensive scanner"""
        driver = None
        start_test_time = time.time()
        
        try:
            driver = self.setup_driver()
            url = f"{self.base_url}{slug}"
            
            print(f"🔍 [{current_count}/6] Testing: {slug} -> {url}")
            
            # Navigate to the page
            driver.get(url)
            
            # Wait a moment for any redirects or dynamic content
            time.sleep(2)
            
            # Get final URL after any redirects
            final_url = driver.current_url
            
            # Get page source and title
            page_source = driver.page_source
            page_title = driver.title
            
            # Analyze the content
            result = self.analyze_page_content(page_source, page_title, final_url, slug)
            result['load_time'] = time.time() - start_test_time
            
            # Print result
            status_emoji = "✅" if result['status'] == 'ACTIVE' else "❌" if result['status'] == 'INACTIVE_401' else "⚠️"
            print(f"   {status_emoji} {result['status']}: {result.get('business_name', 'No business name')}")
            if result.get('services'):
                print(f"      Services: {', '.join(result['services'][:3])}")
            
            return result
            
        except TimeoutException:
            error_msg = f"BROWSER_ERROR: Page load timeout for {slug}"
            print(f"   ⏰ Timeout: {slug}")
            return {
                'status': 'TIMEOUT',
                'error': error_msg,
                'load_time': time.time() - start_test_time,
                'final_url': url
            }
            
        except WebDriverException as e:
            error_msg = f"BROWSER_ERROR: WebDriver error for {slug}: {str(e)}"
            print(f"   🔧 Browser Error: {slug} - {str(e)[:100]}")
            return {
                'status': 'BROWSER_ERROR',
                'error': error_msg,
                'load_time': time.time() - start_test_time,
                'final_url': url
            }
            
        except Exception as e:
            error_msg = f"ERROR: Unexpected error for {slug}: {str(e)}"
            print(f"   💥 Error: {slug} - {str(e)[:100]}")
            return {
                'status': 'ERROR',
                'error': error_msg,
                'load_time': time.time() - start_test_time,
                'final_url': url
            }
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def analyze_page_content(self, page_source, page_title, final_url, slug):
        """Analyze page content to determine if business is active - identical to comprehensive scanner"""
        content_lower = page_source.lower()
        title_lower = page_title.lower()
        
        # Check for error indicators first
        error_indicators = 0
        business_indicators = 0
        
        # Strong error indicators
        error_patterns = [
            'widget/401', '/401', 'unauthorized', 'not found', '404', 'error',
            'access denied', 'forbidden', 'invalid', 'expired', 'suspended'
        ]
        
        for pattern in error_patterns:
            if pattern in content_lower or pattern in title_lower or pattern in final_url.lower():
                error_indicators += 1
        
        # Strong business indicators
        business_patterns = [
            'book now', 'schedule', 'appointment', 'consultation', 'treatment',
            'service', 'clinic', 'medical', 'health', 'therapy', 'wellness',
            'patient', 'doctor', 'nurse', 'provider', 'practice', 'care',
            'injection', 'vitamin', 'iv therapy', 'weight loss', 'aesthetic'
        ]
        
        for pattern in business_patterns:
            if pattern in content_lower or pattern in title_lower:
                business_indicators += 1
        
        # Extract business name
        business_name = self.extract_business_name_enhanced(page_source, page_title)
        
        # Extract services
        services = self.extract_services_from_content(content_lower)
        
        # Decision logic
        if error_indicators > 0 and business_indicators == 0:
            status = 'INACTIVE_401'
        elif business_indicators >= 2 or (business_indicators >= 1 and business_name):
            status = 'ACTIVE'
        elif 'react' in content_lower and len(page_source) > 5000:
            # Large React app with some content - likely active
            status = 'ACTIVE'
        else:
            status = 'INACTIVE_401'
        
        return {
            'status': status,
            'business_name': business_name,
            'services': services,
            'business_indicators': business_indicators,
            'error_indicators': error_indicators,
            'content_length': len(page_source),
            'final_url': final_url
        }
    
    def extract_business_name_enhanced(self, page_text, page_title):
        """Extract business name from page content - identical to comprehensive scanner"""
        # Try page title first
        if page_title and page_title.strip() and page_title.lower() not in ['', 'loading', 'error', 'untitled']:
            # Clean up the title
            title = page_title.strip()
            if len(title) > 3 and not title.lower().startswith('error'):
                return title
        
        # Look for business name patterns in content
        import re
        patterns = [
            r'"businessName":\s*"([^"]+)"',
            r'"name":\s*"([^"]+)"',
            r'<title[^>]*>([^<]+)</title>',
            r'business[_\s]name["\s]*:[\s"]*([^"<>\n]+)',
            r'company[_\s]name["\s]*:[\s"]*([^"<>\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            for match in matches:
                name = match.strip()
                if len(name) > 2 and name.lower() not in ['loading', 'error', 'null', 'undefined']:
                    return name
        
        return ""
    
    def extract_services_from_content(self, content):
        """Extract services from page content - identical to comprehensive scanner"""
        services = []
        service_keywords = [
            'iv therapy', 'vitamin injection', 'weight loss', 'botox', 'filler',
            'aesthetic', 'wellness', 'hydration', 'beauty', 'anti-aging',
            'consultation', 'treatment', 'therapy', 'injection', 'infusion'
        ]
        
        for keyword in service_keywords:
            if keyword in content:
                services.append(keyword.title())
        
        return list(set(services))  # Remove duplicates
    
    def run_self_test(self):
        """Run the self-test on 6 specific slugs"""
        print("🚀 Starting Self-Test...")
        print(f"📊 Testing {len(self.test_slugs)} slugs:")
        for i, slug in enumerate(self.test_slugs, 1):
            expected = "ACTIVE" if slug in self.known_slugs else "INACTIVE/ERROR"
            print(f"   {i}. {slug} (expected: {expected})")
        print("")
        
        self.start_time = datetime.now()
        self.session_data['session_info']['start_time'] = self.start_time.isoformat()
        
        results = []
        
        for i, slug in enumerate(self.test_slugs, 1):
            try:
                # Test the slug
                result = self.test_slug_with_browser(slug, i)
                
                # Log the result
                self.log_test_result(slug, result, "SELF_TEST")
                
                # Store result for analysis
                results.append({
                    'slug': slug,
                    'expected': 'ACTIVE' if slug in self.known_slugs else 'INACTIVE',
                    'actual': result.get('status', 'ERROR'),
                    'business_name': result.get('business_name', ''),
                    'load_time': result.get('load_time', 0),
                    'correct': (result.get('status') == 'ACTIVE') == (slug in self.known_slugs)
                })
                
                self.tested_count += 1
                
                # Rate limiting
                if i < len(self.test_slugs):  # Don't sleep after last test
                    sleep_time = 1.0 / self.requests_per_second
                    time.sleep(sleep_time)
                    
            except Exception as e:
                print(f"   💥 Unexpected error testing {slug}: {e}")
                results.append({
                    'slug': slug,
                    'expected': 'ACTIVE' if slug in self.known_slugs else 'INACTIVE',
                    'actual': 'ERROR',
                    'business_name': '',
                    'load_time': 0,
                    'correct': False
                })
        
        # Calculate accuracy
        correct_results = sum(1 for r in results if r['correct'])
        accuracy = (correct_results / len(results)) * 100 if results else 0
        
        # Save results
        self.save_self_test_results(results, accuracy)
        self.save_session_log()
        
        # Print summary
        self.print_self_test_summary(results, accuracy)
        
        return results, accuracy
    
    def save_self_test_results(self, results, accuracy):
        """Save self-test results to CSV file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        try:
            with open(self.results_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['slug', 'expected', 'actual', 'correct', 'business_name', 'load_time']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in results:
                    writer.writerow(result)
            
            print(f"💾 Self-test results saved to: {self.results_file}")
            
            # Also save summary
            summary_file = f"logs/browser_self_test_summary_{timestamp}.json"
            summary_data = {
                'timestamp': timestamp,
                'total_tests': len(results),
                'correct_predictions': sum(1 for r in results if r['correct']),
                'accuracy_percentage': accuracy,
                'results': results
            }
            
            with open(summary_file, 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            print(f"📋 Self-test summary saved to: {summary_file}")
            
        except Exception as e:
            print(f"⚠️  Error saving results: {e}")
    
    def print_self_test_summary(self, results, accuracy):
        """Print comprehensive self-test summary"""
        print("\n" + "="*60)
        print("🧪 SELF-TEST RESULTS SUMMARY")
        print("="*60)
        
        print(f"📊 Total Tests: {len(results)}")
        print(f"✅ Correct Predictions: {sum(1 for r in results if r['correct'])}")
        print(f"❌ Incorrect Predictions: {sum(1 for r in results if not r['correct'])}")
        print(f"🎯 Accuracy: {accuracy:.1f}%")
        print("")
        
        print("📋 Detailed Results:")
        print("-" * 80)
        print(f"{'Slug':<8} {'Expected':<10} {'Actual':<12} {'Correct':<8} {'Business Name':<25} {'Time':<6}")
        print("-" * 80)
        
        for result in results:
            status_icon = "✅" if result['correct'] else "❌"
            business_name = result['business_name'][:24] if result['business_name'] else 'N/A'
            print(f"{result['slug']:<8} {result['expected']:<10} {result['actual']:<12} "
                  f"{status_icon:<8} {business_name:<25} {result['load_time']:.2f}s")
        
        print("-" * 80)
        
        # Performance assessment
        if accuracy >= 90:
            print("🎉 EXCELLENT: Scanner is working perfectly!")
        elif accuracy >= 75:
            print("👍 GOOD: Scanner is working well with minor issues")
        elif accuracy >= 50:
            print("⚠️  MODERATE: Scanner has some issues that need attention")
        else:
            print("🚨 POOR: Scanner has significant issues and needs debugging")
        
        print(f"\n⏱️  Total test duration: {time.time() - self.start_time.timestamp():.1f}s")
        print(f"⚡ Average test time: {sum(r['load_time'] for r in results) / len(results):.2f}s per slug")
        print("="*60)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Browser Self-Test Scanner for VSDHOne')
    parser.add_argument('--instance-id', help='Unique instance identifier')
    
    args = parser.parse_args()
    
    try:
        scanner = BrowserSelfTestScanner(instance_id=args.instance_id)
        results, accuracy = scanner.run_self_test()
        
        # Exit with appropriate code
        if accuracy >= 75:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
            
    except KeyboardInterrupt:
        print("\n🛑 Self-test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 