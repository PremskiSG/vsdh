#!/usr/bin/env python3
"""
Hydreight Self Tester Scanner
Self-testing scanner for booking.hydreight.com/b/ URLs
Tests two specific slugs: 'aaaa' (invalid) and 'NDgz' (valid)
Based on bookinghydreight_level_scanner.py
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

class HydrightSelfTester:
    def __init__(self, instance_id="SELF_TEST"):
        self.instance_id = instance_id
        self.hostname = socket.gethostname()
        self.session_id = f"{self.hostname}_{instance_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Hydreight-specific configuration - SPEED OPTIMIZED
        self.base_url = "https://booking.hydreight.com/b/"
        self.rate_limit = 10  # INCREASED from 5 to 10 requests per second
        self.timeout = 15     # Increased timeout for testing
        
        # Test slugs - predefined for self testing
        self.test_slugs = [
            {"slug": "aaaa", "expected": "INVALID", "description": "Invalid test slug"},
            {"slug": "NDgz", "expected": "VALID", "description": "Valid Hydreight booking page"}
        ]
        
        # Enhanced error indicators for hydreight level
        self.error_indicators = [
            '401', 'error', 'nothing left to do here', 'go to homepage',
            'not found', 'access denied', 'unauthorized',
            "the link you've opened isn't working as expected",
            'page not found', 'invalid request', 'session expired',
            'service unavailable', 'temporarily unavailable'
        ]
        
        # Business indicators optimized for hydreight format
        self.business_indicators = [
            'book', 'appointment', 'schedule', 'service', 'therapy',
            'treatment', 'consultation', 'booking', 'available',
            'select', 'choose', 'weight loss', 'injection', 'iv therapy',
            'hydreight', 'semaglutide', 'tirzepatide', 'hormone',
            'wellness', 'health', 'medical', 'clinic',
            'provider', 'patient', 'visit', 'care'
        ]
        
        # Session tracking
        self.session_data = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'scanner_type': 'Hydreight_Self_Test',
            'base_url': self.base_url,
            'instance_id': instance_id,
            'hostname': self.hostname,
            'test_slugs': self.test_slugs,
            'results': [],
            'test_summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'active_found': 0,
                'errors': 0
            }
        }
        
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with hydreight optimizations"""
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
        user_data_dir = f"/tmp/chrome_hydreight_test_{self.instance_id}_{random.randint(1000, 9999)}"
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
            print(f"✅ Chrome driver initialized for Hydreight Self Tester {self.instance_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            print("💡 Try installing Chrome driver: brew install chromedriver")
            return False
    
    def analyze_page_content(self, slug, url):
        """Analyze page content to determine if business is active"""
        try:
            start_time = time.time()
            
            # Navigate to the hydreight URL
            hydreight_url = f"{self.base_url}{slug}"
            print(f"🌐 Testing URL: {hydreight_url}")
            self.driver.get(hydreight_url)
            
            # ACCURACY OPTIMIZATION: Increased wait time to 3s for proper page loading
            # These are dynamic pages that need time for content to fully render
            time.sleep(3)
            
            # Get page source and basic metrics
            page_source = self.driver.page_source.lower()
            page_title = self.driver.title
            final_url = self.driver.current_url
            content_length = len(page_source)
            load_time = time.time() - start_time
            
            print(f"📄 Page Title: '{page_title}'")
            print(f"🔗 Final URL: {final_url}")
            print(f"📏 Content Length: {content_length:,} characters")
            print(f"⏱️  Load Time: {load_time:.2f}s")
            
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
            
            print(f"❌ Error Indicators Found: {error_indicators_found}")
            print(f"✅ Business Indicators Found: {business_indicators_found}")
            
            # HYDREIGHT-SPECIFIC: Empty title is primary indicator of invalid URL
            if not page_title or page_title.strip() == "":
                status = "ERROR_PAGE"
                classification = "EMPTY_TITLE_INVALID_URL"
                business_name = ""
            else:
                # Determine status based on indicators with improved logic
                # Check if we have a meaningful business title or substantial content
                has_business_title = page_title and len(page_title) > 3 and page_title.lower() not in ['loading', 'error']
                has_substantial_content = content_length > 20000  # Hydreight pages are typically large
                
                print(f"🏷️  Has Business Title: {has_business_title}")
                print(f"📊 Has Substantial Content (>20k): {has_substantial_content}")
                
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
            
            print(f"🤖 Scanner Result: {status} ({classification})")
            print(f"🏢 Business Name: {business_name}")
            
            # Create comprehensive result
            result = {
                'slug': slug,
                'url': hydreight_url,
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
        """Extract business name from page content - PRIORITIZE PAGE TITLE"""
        # PRIORITY 1: Use page title if available and meaningful (contains actual business name)
        if page_title and len(page_title) > 3 and page_title.lower() not in ['', 'loading', 'error']:
            return page_title
        
        # PRIORITY 2: Look for common business name patterns only if no meaningful title
        if 'hydreight' in page_source:
            # Extract Hydreight location info
            if 'location' in page_source:
                return "Hydreight - Location"
            return "Hydreight"
        elif 'iv therapy' in page_source:
            return "IV Therapy Center"
        
        return ""
    
    def evaluate_test_result(self, test_case, result):
        """Evaluate if the test result matches expectations"""
        expected = test_case['expected']
        actual_status = result['status']
        
        # Define what constitutes a valid/invalid result
        valid_statuses = ['ACTIVE']
        invalid_statuses = ['ERROR_PAGE', 'TIMEOUT', 'CONNECTION_ERROR', 'BROWSER_ERROR', 'INACTIVE_UNKNOWN']
        
        if expected == "VALID":
            test_passed = actual_status in valid_statuses
        elif expected == "INVALID":
            test_passed = actual_status in invalid_statuses
        else:
            test_passed = False
        
        return test_passed
    
    def save_test_results(self):
        """Save test results to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save test results JSON
        results_filename = f"logs/SELF_TEST_HYD_{self.session_id}_{timestamp}_results.json"
        with open(results_filename, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Test results saved to: {results_filename}")
        return results_filename
    
    def run_self_test(self):
        """Run self-test with predefined test cases"""
        print("🧪 HYDREIGHT SELF TESTER")
        print("=" * 50)
        print(f"📍 Base URL: {self.base_url}")
        print(f"🎯 Test Cases: {len(self.test_slugs)}")
        print()
        
        if not self.setup_driver():
            print("❌ Failed to setup driver, aborting test")
            return False
        
        try:
            for i, test_case in enumerate(self.test_slugs, 1):
                slug = test_case['slug']
                expected = test_case['expected']
                description = test_case['description']
                
                print(f"🔍 TEST {i}/{len(self.test_slugs)}: {slug}")
                print(f"📝 Description: {description}")
                print(f"🎯 Expected: {expected}")
                print("-" * 40)
                
                # Run the test
                result = self.analyze_page_content(slug, f"{self.base_url}{slug}")
                
                # Evaluate the result
                test_passed = self.evaluate_test_result(test_case, result)
                
                # Add test evaluation to result
                result['test_case'] = test_case
                result['test_passed'] = test_passed
                result['expected_result'] = expected
                
                self.session_data['results'].append(result)
                
                # Update test summary
                self.session_data['test_summary']['total_tests'] += 1
                if test_passed:
                    self.session_data['test_summary']['passed'] += 1
                    print(f"✅ TEST PASSED: Expected {expected}, Got {result['status']}")
                else:
                    self.session_data['test_summary']['failed'] += 1
                    print(f"❌ TEST FAILED: Expected {expected}, Got {result['status']}")
                
                if result['status'] == 'ACTIVE':
                    self.session_data['test_summary']['active_found'] += 1
                elif result['status'] in ['TIMEOUT', 'CONNECTION_ERROR', 'BROWSER_ERROR']:
                    self.session_data['test_summary']['errors'] += 1
                
                print("=" * 50)
                print()
                
                # Small delay between tests
                time.sleep(2)
            
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 Browser closed")
        
        # Save results and print summary
        self.save_test_results()
        self.print_test_summary()
        
        return self.session_data['test_summary']['failed'] == 0
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        summary = self.session_data['test_summary']
        
        print("\n🏁 SELF TEST SUMMARY")
        print("=" * 50)
        print(f"📊 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"🎯 Success Rate: {(summary['passed']/summary['total_tests']*100):.1f}%" if summary['total_tests'] > 0 else "0%")
        print()
        print(f"🔍 Scanner Results:")
        print(f"   ✅ Active Found: {summary['active_found']}")
        print(f"   ❌ Errors: {summary['errors']}")
        print()
        
        # Print individual test results
        print("📋 Test Details:")
        for i, result in enumerate(self.session_data['results'], 1):
            status_icon = "✅" if result['test_passed'] else "❌"
            print(f"   {status_icon} Test {i}: {result['slug']} -> {result['status']} (Expected: {result['expected_result']})")
        
        print("=" * 50)
        
        if summary['failed'] == 0:
            print("🎉 ALL TESTS PASSED! Scanner is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the results.")

    def scan_slugs(self, slugs, resume=True):
        """Legacy method - use run_self_test() instead"""
        print("⚠️  This is a self-tester. Use run_self_test() method instead.")
        return self.run_self_test()

def determine_business_status(page_source, page_title, url):
    """
    Determine if a page represents an active business based on content analysis.
    Enhanced for hydreight format with empty title detection.
    """
    page_source_lower = page_source.lower()
    page_title_lower = page_title.lower()
    
    # HYDREIGHT-SPECIFIC: Empty title is primary indicator of invalid URL
    if not page_title or page_title.strip() == "":
        return "ERROR_PAGE", "Empty page title indicates invalid hydreight URL"
    
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
        "select", "calendar", "time", "date", "available", "hydreight"
    ]
    
    # Check for business indicators
    business_signs = any(indicator in page_source_lower or indicator in page_title_lower 
                        for indicator in business_indicators)
    
    # Check for error indicators
    error_signs = any(indicator in page_source_lower for indicator in error_indicators)
    
    # Hydreight logic: Valid title + substantial content + business indicators = ACTIVE
    if page_title.strip() and len(page_source) > 20000 and business_signs:
        return "ACTIVE", f"Valid hydreight business: {page_title}"
    
    # If we have error indicators and no business signs, it's an error
    if error_signs and not business_signs:
        return "ERROR_PAGE", "Error indicators found without business content"
    
    # Hydreight format: If we have a title but no clear business indicators, 
    # it might still be valid but not fully loaded
    if page_title.strip() and len(page_source) > 15000:
        return "ACTIVE", f"Hydreight page with title: {page_title}"
    
    # Default for hydreight: empty title or minimal content = error
    return "ERROR_PAGE", "Insufficient content or empty title for hydreight URL"

def main():
    parser = argparse.ArgumentParser(description='Hydreight Self Tester Scanner')
    parser.add_argument('--instance-id', default='SELF_TEST', help='Instance identifier for testing')
    
    args = parser.parse_args()
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Create and run self tester
    tester = HydrightSelfTester(instance_id=args.instance_id)
    success = tester.run_self_test()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main() 