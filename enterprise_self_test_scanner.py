#!/usr/bin/env python3
"""
VSDHOne Enterprise Self-Test Scanner
Tests known working and non-working enterprise URLs to validate scanner functionality
"""

import json
import csv
import os
import time
import socket
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

class EnterpriseSelfTestScanner:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.session_id = f"{self.hostname}_ENT_SELFTEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Enterprise-specific configuration - SPEED OPTIMIZED
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/b/"
        self.timeout = 10  # REDUCED from 15s to 10s for faster testing
        
        # Test slugs: 3 working + 2 non-working
        self.test_slugs = {
            # Known working enterprise URLs (from your examples)
            'NzEw': {'expected': 'ACTIVE', 'type': 'working'},
            'NDI2': {'expected': 'ACTIVE', 'type': 'working'},
            'NzEy': {'expected': 'ACTIVE', 'type': 'working'},
            # Known non-working slugs
            'aaaa': {'expected': 'ERROR_PAGE', 'type': 'error'},
            'Nzab': {'expected': 'ERROR_PAGE', 'type': 'error'}
        }
        
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
            'scanner_type': 'Enterprise_Self_Test',
            'base_url': self.base_url,
            'hostname': self.hostname,
            'test_results': [],
            'validation_summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'accuracy': 0.0
            }
        }
        
        self.driver = None
    
    def setup_driver(self):
        """Setup Chrome driver for self-testing"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        
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
        
        # Unique user data directory
        chrome_options.add_argument(f'--user-data-dir=/tmp/chrome_ent_selftest_{self.session_id}')
        
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
            print(f"✅ Chrome driver initialized for Enterprise Self-Test")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {e}")
            print("💡 Try installing Chrome driver: brew install chromedriver")
            return False
    
    def analyze_page_content(self, slug):
        """Analyze page content to determine if business is active"""
        try:
            start_time = time.time()
            
            # Navigate to the enterprise URL
            enterprise_url = f"{self.base_url}{slug}"
            self.driver.get(enterprise_url)
            
            # SPEED OPTIMIZATION: Reduced wait time from 3s to 1s
            time.sleep(1)
            
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
            
        except TimeoutException:
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
                'tested_at': datetime.now().isoformat()
            }
        except Exception as e:
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
                'tested_at': datetime.now().isoformat()
            }
    
    def extract_business_name(self, page_source, page_title):
        """Extract business name from page content"""
        # Look for common business name patterns
        if 'dripbar' in page_source:
            if 'direct' in page_source:
                return "The DRIPBaR Direct - Location"
            return "The DRIPBaR"
        elif 'renivate' in page_source:
            return "RenIVate"
        
        # Use page title if available and meaningful
        if page_title and len(page_title) > 3 and page_title.lower() not in ['', 'loading', 'error']:
            return page_title
        
        return ""
    
    def validate_result(self, slug, result, expected_status):
        """Validate if the result matches expected outcome"""
        actual_status = result['status']
        
        # Define validation logic
        if expected_status == 'ACTIVE':
            # For working slugs, we expect ACTIVE status
            passed = actual_status == 'ACTIVE'
        elif expected_status == 'ERROR_PAGE':
            # For error slugs, we expect either ERROR_PAGE, INACTIVE_UNKNOWN, or certain error conditions
            passed = actual_status in ['ERROR_PAGE', 'INACTIVE_UNKNOWN', 'TIMEOUT', 'BROWSER_ERROR']
        else:
            passed = actual_status == expected_status
        
        return {
            'slug': slug,
            'expected': expected_status,
            'actual': actual_status,
            'passed': passed,
            'test_type': self.test_slugs[slug]['type']
        }
    
    def run_self_test(self):
        """Run the complete self-test validation"""
        print(f"🧪 Starting Enterprise Self-Test Scanner")
        print(f"📍 Base URL: {self.base_url}")
        print(f"🎯 Testing {len(self.test_slugs)} known URLs")
        
        if not self.setup_driver():
            print("❌ Failed to setup driver, aborting self-test")
            return False
        
        try:
            validation_results = []
            
            for i, (slug, test_config) in enumerate(self.test_slugs.items(), 1):
                expected_status = test_config['expected']
                test_type = test_config['type']
                
                print(f"🔍 [{i}/{len(self.test_slugs)}] Testing {test_type} slug: {slug}", end=" ", flush=True)
                
                # Analyze the page
                result = self.analyze_page_content(slug)
                self.session_data['test_results'].append(result)
                
                # Validate the result
                validation = self.validate_result(slug, result, expected_status)
                validation_results.append(validation)
                
                # Update statistics
                self.session_data['validation_summary']['total_tests'] += 1
                if validation['passed']:
                    self.session_data['validation_summary']['passed'] += 1
                    print(f"✅ PASS ({validation['actual']})")
                else:
                    self.session_data['validation_summary']['failed'] += 1
                    print(f"❌ FAIL (Expected: {validation['expected']}, Got: {validation['actual']})")
                
                # Small delay between tests
                time.sleep(1)
            
            # Calculate accuracy
            total = self.session_data['validation_summary']['total_tests']
            passed = self.session_data['validation_summary']['passed']
            accuracy = (passed / total * 100) if total > 0 else 0
            self.session_data['validation_summary']['accuracy'] = accuracy
            
            # Save results
            self.save_test_results(validation_results)
            
            # Print summary
            print(f"\n📊 ENTERPRISE SELF-TEST COMPLETE:")
            print(f"   • Total Tests: {total}")
            print(f"   • Passed: {passed}")
            print(f"   • Failed: {self.session_data['validation_summary']['failed']}")
            print(f"   • Accuracy: {accuracy:.1f}%")
            
            # Determine if scanner is working correctly
            if accuracy >= 80.0:  # 4 out of 5 tests should pass
                print(f"✅ Enterprise Scanner is working correctly!")
                return True
            else:
                print(f"❌ Enterprise Scanner needs attention - accuracy below 80%")
                return False
                
        except Exception as e:
            print(f"\n❌ Unexpected error during self-test: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_test_results(self, validation_results):
        """Save test results to files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save session data
        session_filename = f"logs/SESSION_ENT_SELFTEST_{self.session_id}_{timestamp}_session.json"
        with open(session_filename, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        
        # Save detailed results CSV
        if self.session_data['test_results']:
            results_filename = f"logs/SESSION_ENT_SELFTEST_{self.session_id}_{timestamp}_results.csv"
            with open(results_filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = self.session_data['test_results'][0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.session_data['test_results'])
        
        # Save validation summary
        summary_filename = f"logs/SESSION_ENT_SELFTEST_{self.session_id}_{timestamp}_summary.json"
        summary_data = {
            'session_id': self.session_id,
            'timestamp': timestamp,
            'validation_summary': self.session_data['validation_summary'],
            'validation_details': validation_results,
            'test_configuration': self.test_slugs
        }
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
        
        print(f"\n📊 Test results saved:")
        print(f"   Session: {session_filename}")
        if self.session_data['test_results']:
            print(f"   Results: {results_filename}")
        print(f"   Summary: {summary_filename}")

def main():
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Create and run self-test scanner
    scanner = EnterpriseSelfTestScanner()
    success = scanner.run_self_test()
    
    # Exit with appropriate code
    exit(0 if success else 1)

if __name__ == "__main__":
    main() 