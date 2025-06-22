#!/usr/bin/env python3
"""
VSDHOne Enterprise Level Scanner - FIXED VERSION
Enhanced enterprise-level scanner for /b/ URL format with comprehensive error handling,
checkpoint/resume functionality, and FIXED CSV fieldnames issue.
"""

import json
import csv
import os
import time
import socket
import argparse
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

class EnterpriseScanner:
    def __init__(self, instance_id="ENT_DEFAULT"):
        self.hostname = socket.gethostname()
        self.session_id = f"{self.hostname}_{instance_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Enterprise-specific configuration - SPEED OPTIMIZED
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/b/"
        self.timeout = 10  # REDUCED from 15s to 10s for faster testing
        self.rate_limit = 10  # INCREASED from 5 to 10 requests/second
        
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
        """Setup Chrome driver with performance optimizations"""
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')
            options.add_argument('--disable-javascript')
            options.add_argument('--disable-css')
            
            # SPEED OPTIMIZATION: Additional performance flags
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-ipc-flooding-protection')
            options.add_argument('--disable-background-networking')
            options.add_argument('--disable-sync')
            options.add_argument('--disable-default-apps')
            options.add_argument('--no-first-run')
            options.add_argument('--fast-start')
            options.add_argument('--disable-logging')
            
            # Use webdriver-manager for automatic ChromeDriver management
            service = Service("/opt/homebrew/bin/chromedriver")
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(self.timeout)
            
            print(f"✅ Chrome driver setup complete (timeout: {self.timeout}s)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup Chrome driver: {e}")
            return False

    def analyze_page_content(self, slug, url):
        """Analyze page content to determine if business is active with comprehensive error handling"""
        result = {
            'slug': slug,
            'url': url,
            'final_url': '',
            'status': 'UNKNOWN',
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
            'tested_at': datetime.now().isoformat(),
            'error_details': ''  # FIXED: Always include error_details field
        }
        
        try:
            start_time = time.time()
            
            # Navigate to the enterprise URL
            self.driver.get(url)
            
            # SPEED OPTIMIZATION: Reduced wait time from 3s to 1s
            time.sleep(1)
            
            # Get page source and basic metrics
            page_source = self.driver.page_source.lower()
            page_title = self.driver.title
            final_url = self.driver.current_url
            content_length = len(page_source)
            load_time = time.time() - start_time
            
            # Update result with basic info
            result.update({
                'final_url': final_url,
                'page_title': page_title,
                'content_length': content_length,
                'load_time': load_time,
                'content_preview': page_source[:200] if page_source else ''
            })
            
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
            
            result.update({
                'error_indicators': len(error_indicators_found),
                'business_indicators': len(business_indicators_found),
                'error_indicators_found': error_indicators_found,
                'indicators_found': business_indicators_found
            })
            
            # ENTERPRISE-SPECIFIC: Empty title is primary indicator of invalid URL
            if not page_title or page_title.strip() == "":
                result.update({
                    'status': 'ERROR_PAGE',
                    'classification': 'EMPTY_TITLE_INVALID_URL',
                    'business_name': ''
                })
            else:
                # Determine status based on indicators with improved logic
                # Check if we have a meaningful business title or substantial content
                has_business_title = page_title and len(page_title) > 3 and page_title.lower() not in ['loading', 'error']
                has_substantial_content = content_length > 20000  # Enterprise pages are typically large
                
                if business_indicators_found or has_business_title or has_substantial_content:
                    # If we have business indicators OR a business title OR substantial content, it's likely active
                    # Only mark as error if we have clear error indicators AND no business signs
                    if error_indicators_found and not business_indicators_found and not has_business_title:
                        result.update({
                            'status': 'ERROR_PAGE',
                            'classification': 'ERROR_INDICATORS_FOUND',
                            'business_name': ''
                        })
                    else:
                        result.update({
                            'status': 'ACTIVE',
                            'classification': 'ACTIVE_BUSINESS',
                            'business_name': self.extract_business_name(page_source, page_title)
                        })
                elif error_indicators_found:
                    result.update({
                        'status': 'ERROR_PAGE',
                        'classification': 'ERROR_INDICATORS_FOUND',
                        'business_name': ''
                    })
                else:
                    result.update({
                        'status': 'INACTIVE_UNKNOWN',
                        'classification': 'NO_INDICATORS',
                        'business_name': ''
                    })
            
            return result
            
        except TimeoutException:
            print(f"⏰ TIMEOUT after {self.timeout}s")
            result.update({
                'status': 'TIMEOUT',
                'classification': 'PAGE_LOAD_TIMEOUT',
                'load_time': self.timeout,
                'error_details': f'Page load timeout after {self.timeout} seconds'
            })
            return result
            
        except WebDriverException as e:
            print(f"🌐 CONNECTION_ERROR: {str(e)[:50]}...")
            result.update({
                'status': 'CONNECTION_ERROR',
                'classification': 'WEBDRIVER_CONNECTION_ERROR',
                'error_details': f'WebDriver error: {str(e)}'
            })
            return result
            
        except Exception as e:
            print(f"❌ BROWSER_ERROR: {str(e)[:50]}...")
            result.update({
                'status': 'BROWSER_ERROR',
                'classification': 'UNEXPECTED_BROWSER_ERROR',
                'error_details': f'Unexpected error: {str(e)}\nTraceback: {traceback.format_exc()}'
            })
            return result

    def extract_business_name(self, page_source, page_title):
        """Extract business name from page content"""
        if page_title and page_title.strip():
            # Clean up the title
            business_name = page_title.strip()
            # Remove common suffixes
            for suffix in [' - Booking', ' | Booking', ' Booking', ' - VSDHOne', ' | VSDHOne']:
                if business_name.endswith(suffix):
                    business_name = business_name[:-len(suffix)].strip()
            return business_name
        return ""

    def save_checkpoint(self, current_slug_index, total_slugs, current_slug):
        """Save checkpoint for resume functionality"""
        checkpoint_data = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'completed_slugs': current_slug_index,
            'total_slugs': total_slugs,
            'current_slug': current_slug,
            'stats': self.session_data['stats'].copy()
        }
        
        # Save checkpoint to file
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        # Also save timestamped checkpoint
        timestamped_checkpoint = f"logs/CHECKPOINT_ENT_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(timestamped_checkpoint, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        print(f"💾 CHECKPOINT [{current_slug_index}/{total_slugs}] - Progress saved")

    def load_checkpoint(self):
        """Load checkpoint data for resume functionality"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)
                print(f"📋 Found checkpoint: {checkpoint_data['completed_slugs']} slugs completed")
                return checkpoint_data
            except Exception as e:
                print(f"⚠️  Could not load checkpoint: {e}")
        return None

    def save_session_data(self):
        """Save session data to files - FIXED VERSION"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save session JSON
        session_filename = f"logs/SESSION_ENT_{self.session_id}_{timestamp}_session.json"
        with open(session_filename, 'w', encoding='utf-8') as f:
            json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        
        # Save results CSV (only if there are results) - FIXED FIELDNAMES
        if self.session_data['results']:
            results_filename = f"logs/SESSION_ENT_{self.session_id}_{timestamp}_results.csv"
            with open(results_filename, 'w', newline='', encoding='utf-8') as f:
                # FIXED: Define consistent fieldnames including error_details
                fieldnames = [
                    'slug', 'url', 'final_url', 'status', 'classification', 'business_name',
                    'business_indicators', 'error_indicators', 'indicators_found', 
                    'error_indicators_found', 'page_title', 'content_length', 'load_time',
                    'content_preview', 'tested_at', 'error_details'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                
                # FIXED: Ensure all results have the error_details field (even if empty)
                for result in self.session_data['results']:
                    if 'error_details' not in result:
                        result['error_details'] = ''
                
                writer.writerows(self.session_data['results'])
        
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
        print(f"🚀 Starting Enterprise Level Scanner {self.session_data['instance_id']}")
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

def main():
    """Main execution function with command line argument support"""
    parser = argparse.ArgumentParser(description='VSDHOne Enterprise Level Scanner')
    parser.add_argument('slug_file', help='Path to file containing slugs to scan (one per line)')
    parser.add_argument('--instance-id', default='ENT_DEFAULT', help='Instance identifier for parallel scanning')
    parser.add_argument('--no-resume', action='store_true', help='Start fresh scan without resume prompt')
    
    args = parser.parse_args()
    
    # Load slugs from file
    try:
        with open(args.slug_file, 'r') as f:
            slugs = [line.strip() for line in f if line.strip()]
        print(f"📁 Loaded {len(slugs)} slugs from {args.slug_file}")
    except FileNotFoundError:
        print(f"❌ Error: Could not find slug file: {args.slug_file}")
        return
    except Exception as e:
        print(f"❌ Error reading slug file: {e}")
        return
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Initialize and run scanner
    scanner = EnterpriseScanner(args.instance_id)
    
    print(f"🏢 Enterprise Level Scanner - FIXED VERSION")
    print(f"🎯 Target: {len(slugs)} enterprise slugs")
    print(f"📍 Instance: {args.instance_id}")
    print(f"🔄 Resume: {'Disabled' if args.no_resume else 'Enabled'}")
    print("=" * 60)
    
    # Determine slugs to scan
    slugs_to_scan = slugs
    
    # Start scanning
    scanner.scan_slugs(slugs_to_scan, resume=not args.no_resume)

if __name__ == "__main__":
    main() 