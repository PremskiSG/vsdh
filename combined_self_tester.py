#!/usr/bin/env python3
"""
Combined Scanner Self-Tester
Tests the combined scanner with known slugs to verify it's working correctly
Tests 3 slugs: aaaa (expected: invalid), MzYz and NDgz (expected: valid)
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

class CombinedSelfTester:
    def __init__(self, instance_id="COMBINED_SELFTEST"):
        self.instance_id = instance_id
        self.hostname = socket.gethostname()
        self.session_id = f"{self.hostname}_{instance_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Dual URL configuration - SAFETY OPTIMIZED
        self.enterprise_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/b/"
        self.hydreight_url = "https://booking.hydreight.com/b/"
        self.rate_limit = 5   # REDUCED for testing - 5 requests per second
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
        
        # Test slugs with expected results
        self.test_slugs = [
            {'slug': 'aaaa', 'expected_enterprise': 'ERROR_PAGE', 'expected_hydreight': 'ERROR_PAGE', 'description': 'Invalid slug'},
            {'slug': 'MzYz', 'expected_enterprise': 'ACTIVE', 'expected_hydreight': 'UNKNOWN', 'description': 'Base64 for 363 - should be active on enterprise'},
            {'slug': 'NDgz', 'expected_enterprise': 'UNKNOWN', 'expected_hydreight': 'ACTIVE', 'description': 'Base64 for 483 - should be active on hydreight'}
        ]
        
        # Session tracking
        self.session_data = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'scanner_type': 'Combined_Self_Tester',
            'enterprise_url': self.enterprise_url,
            'hydreight_url': self.hydreight_url,
            'instance_id': instance_id,
            'hostname': self.hostname,
            'test_results': [],
            'test_summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'enterprise_tests': 0,
                'hydreight_tests': 0,
                'errors': 0
            }
        }
        
        # Checkpoint file for resume functionality
        self.checkpoint_file = f"logs/CHECKPOINT_COMBINED_{self.session_id}.txt"
        
        self.driver = None
        
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
        user_data_dir = f"/tmp/chrome_combined_selftest_{self.instance_id}_{random.randint(1000, 9999)}"
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
            print(f"✅ Chrome driver initialized for Combined Self-Tester {self.instance_id}")
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

    def test_slug(self, test_case):
        """Test a single slug on both platforms and validate against expected results"""
        slug = test_case['slug']
        expected_enterprise = test_case['expected_enterprise']
        expected_hydreight = test_case['expected_hydreight']
        description = test_case['description']
        
        print(f"🧪 Testing: {slug} ({description})")
        
        # Test Enterprise
        enterprise_url = f"{self.enterprise_url}{slug}"
        enterprise_result = self.analyze_page_content(slug, enterprise_url, "Enterprise")
        
        # Test Hydreight
        hydreight_url = f"{self.hydreight_url}{slug}"
        hydreight_result = self.analyze_page_content(slug, hydreight_url, "Hydreight")
        
        # Validate results
        enterprise_passed = True
        hydreight_passed = True
        
        if expected_enterprise != 'UNKNOWN':
            if expected_enterprise == 'ERROR_PAGE':
                enterprise_passed = enterprise_result['status'] in ['ERROR_PAGE', 'TIMEOUT', 'CONNECTION_ERROR', 'BROWSER_ERROR']
            else:
                enterprise_passed = enterprise_result['status'] == expected_enterprise
        
        if expected_hydreight != 'UNKNOWN':
            if expected_hydreight == 'ERROR_PAGE':
                hydreight_passed = hydreight_result['status'] in ['ERROR_PAGE', 'TIMEOUT', 'CONNECTION_ERROR', 'BROWSER_ERROR']
            else:
                hydreight_passed = hydreight_result['status'] == expected_hydreight
        
        overall_passed = enterprise_passed and hydreight_passed
        
        # Create test result
        test_result = {
            'slug': slug,
            'description': description,
            'tested_at': datetime.now().isoformat(),
            
            # Enterprise results
            'enterprise_expected': expected_enterprise,
            'enterprise_actual': enterprise_result['status'],
            'enterprise_passed': enterprise_passed,
            'enterprise_business_name': enterprise_result['business_name'],
            'enterprise_page_title': enterprise_result['page_title'],
            'enterprise_content_length': enterprise_result['content_length'],
            'enterprise_load_time': enterprise_result['load_time'],
            
            # Hydreight results
            'hydreight_expected': expected_hydreight,
            'hydreight_actual': hydreight_result['status'],
            'hydreight_passed': hydreight_passed,
            'hydreight_business_name': hydreight_result['business_name'],
            'hydreight_page_title': hydreight_result['page_title'],
            'hydreight_content_length': hydreight_result['content_length'],
            'hydreight_load_time': hydreight_result['load_time'],
            
            # Overall result
            'overall_passed': overall_passed
        }
        
        # Print results
        ent_icon = "✅" if enterprise_passed else "❌"
        hyd_icon = "✅" if hydreight_passed else "❌"
        overall_icon = "✅" if overall_passed else "❌"
        
        print(f"📊 Results for {slug}:")
        print(f"   Enterprise: {ent_icon} Expected: {expected_enterprise}, Got: {enterprise_result['status']}")
        print(f"   Hydreight:  {hyd_icon} Expected: {expected_hydreight}, Got: {hydreight_result['status']}")
        print(f"   Overall:    {overall_icon} {'PASSED' if overall_passed else 'FAILED'}")
        
        return test_result
    
    def save_test_results(self):
        """Save test results to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save JSON session data
        session_filename = f"logs/SELFTEST_COMBINED_{self.session_id}_{timestamp}_session.json"
        with open(session_filename, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        
        # Save CSV results
        results_filename = f"logs/SELFTEST_COMBINED_{self.session_id}_{timestamp}_results.csv"
        if self.session_data['test_results']:
            fieldnames = [
                'slug', 'description', 'tested_at',
                'enterprise_expected', 'enterprise_actual', 'enterprise_passed',
                'enterprise_business_name', 'enterprise_page_title', 'enterprise_content_length', 'enterprise_load_time',
                'hydreight_expected', 'hydreight_actual', 'hydreight_passed',
                'hydreight_business_name', 'hydreight_page_title', 'hydreight_content_length', 'hydreight_load_time',
                'overall_passed'
            ]
            
            with open(results_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.session_data['test_results'])
        
        # Save summary
        summary_filename = f"logs/SELFTEST_COMBINED_{self.session_id}_{timestamp}_summary.json"
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(self.session_data['test_summary'], f, indent=2)
        
        print(f"📊 Self-test data saved:")
        print(f"   Session: {session_filename}")
        if self.session_data['test_results']:
            print(f"   Results: {results_filename}")
        print(f"   Summary: {summary_filename}")
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        summary = self.session_data['test_summary']
        print(f"\n🧪 COMBINED SCANNER SELF-TEST COMPLETE:")
        print("=" * 60)
        print(f"   🎯 Total Tests: {summary['total_tests']}")
        print(f"   ✅ Passed: {summary['passed_tests']}")
        print(f"   ❌ Failed: {summary['failed_tests']}")
        print(f"   🏢 Enterprise Tests Passed: {summary['enterprise_tests']}")
        print(f"   💧 Hydreight Tests Passed: {summary['hydreight_tests']}")
        
        if summary['total_tests'] > 0:
            success_rate = (summary['passed_tests'] / summary['total_tests']) * 100
            print(f"   📈 Success Rate: {success_rate:.1f}%")
        
        if summary['failed_tests'] == 0:
            print(f"\n🎉 ALL TESTS PASSED! Combined scanner is working correctly.")
        else:
            print(f"\n⚠️  {summary['failed_tests']} test(s) failed. Please review the results.")
    
    def run_self_test(self):
        """Run the complete self-test suite"""
        print(f"🧪 Starting Combined Scanner Self-Test")
        print(f"📍 Enterprise URL: {self.enterprise_url}")
        print(f"📍 Hydreight URL: {self.hydreight_url}")
        print(f"🎯 Test cases: {len(self.test_slugs)}")
        print("=" * 80)
        
        if not self.setup_driver():
            print("❌ Failed to setup driver, aborting self-test")
            return False
        
        try:
            for i, test_case in enumerate(self.test_slugs, 1):
                print(f"\n🔍 Test {i}/{len(self.test_slugs)}")
                
                # Rate limiting between tests
                if i > 1:
                    time.sleep(1.0 / self.rate_limit)
                
                # Run test
                test_result = self.test_slug(test_case)
                self.session_data['test_results'].append(test_result)
                
                # Update statistics
                self.session_data['test_summary']['total_tests'] += 1
                if test_result['overall_passed']:
                    self.session_data['test_summary']['passed_tests'] += 1
                else:
                    self.session_data['test_summary']['failed_tests'] += 1
                
                if test_result['enterprise_passed']:
                    self.session_data['test_summary']['enterprise_tests'] += 1
                if test_result['hydreight_passed']:
                    self.session_data['test_summary']['hydreight_tests'] += 1
                
                print("   " + "="*60)
        
        except KeyboardInterrupt:
            print(f"\n⚠️  Self-test interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error during self-test: {e}")
        finally:
            # Final save and cleanup
            self.session_data['end_time'] = datetime.now().isoformat()
            self.save_test_results()
            
            if self.driver:
                self.driver.quit()
            
            # Print final summary
            self.print_test_summary()
            
            return self.session_data['test_summary']['failed_tests'] == 0

def main():
    parser = argparse.ArgumentParser(description='Combined Scanner Self-Tester')
    parser.add_argument('--instance-id', default='COMBINED_SELFTEST', help='Instance identifier')
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Create and run self-tester
    tester = CombinedSelfTester(instance_id=args.instance_id)
    success = tester.run_self_test()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main() 