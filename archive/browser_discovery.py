#!/usr/bin/env python3
"""
VSDHOne Browser-based Discovery Tool
Uses Selenium to detect valid business slugs by checking if the JavaScript app loads properly
"""

import csv
import time
import random
import string
from itertools import product
from datetime import datetime
import sys
import os

# Try to import selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not available. Install with: pip install selenium")

class BrowserVSDHOneDiscovery:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/"
        self.known_slugs = {
            'ad31y', 'mj42f', 'os27m', 'lp56a', 'zb74k', 'ym99l', 
            'yh52b', 'zd20w', 'td32z', 'bo19e', 'bh70s', 'ai04u', 
            'bm49t', 'qu29u', 'tc33l'
        }
        self.tested_slugs = set()
        self.found_brands = []
        self.driver = None
    
    def setup_browser(self):
        """Setup Chrome browser with headless mode"""
        if not SELENIUM_AVAILABLE:
            raise Exception("Selenium not available")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            return True
        except WebDriverException as e:
            print(f"❌ Failed to setup Chrome browser: {e}")
            print("💡 Make sure Chrome and ChromeDriver are installed")
            return False
    
    def generate_slugs(self):
        """Generate slug combinations based on the observed pattern"""
        letters = string.ascii_lowercase
        digits = string.digits
        
        for combo in product(letters, letters, digits, digits, letters):
            slug = ''.join(combo)
            if slug not in self.known_slugs and slug not in self.tested_slugs:
                yield slug
    
    def test_slug(self, slug):
        """Test if a slug loads a valid business page"""
        url = f"{self.base_url}{slug}"
        
        try:
            print(f"🔍 Testing: {slug}")
            self.driver.get(url)
            
            # Mark as tested
            self.tested_slugs.add(slug)
            
            # Wait for initial load
            time.sleep(3)
            
            # Check for various indicators of a valid business page
            indicators = self.check_page_indicators()
            
            if indicators['is_valid']:
                print(f"✅ Found valid slug: {slug}")
                brand_data = self.extract_brand_data(slug, indicators)
                if brand_data:
                    self.found_brands.append(brand_data)
                    self.save_to_csv()
                return True
            else:
                print(f"❌ {slug} - No valid business content detected")
                return False
                
        except TimeoutException:
            print(f"⏰ {slug} - Page load timeout")
            return False
        except Exception as e:
            print(f"❌ {slug} - Error: {str(e)}")
            return False
    
    def check_page_indicators(self):
        """Check for indicators that the page loaded a valid business"""
        indicators = {
            'is_valid': False,
            'has_booking_widget': False,
            'has_business_name': False,
            'has_error_message': False,
            'page_title': '',
            'business_elements': []
        }
        
        try:
            # Get page title
            indicators['page_title'] = self.driver.title
            
            # Check for error indicators
            error_selectors = [
                "[class*='error']",
                "[class*='Error']",
                "[id*='error']",
                "[data-testid*='error']",
                "div:contains('Error')",
                "div:contains('not found')",
                "div:contains('404')"
            ]
            
            for selector in error_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        indicators['has_error_message'] = True
                        break
                except:
                    pass
            
            # Check for business/booking indicators
            business_selectors = [
                "[class*='booking']",
                "[class*='appointment']",
                "[class*='schedule']",
                "[class*='business']",
                "[class*='clinic']",
                "[class*='service']",
                "input[type='date']",
                "input[type='time']",
                "[class*='calendar']",
                "[class*='time-slot']",
                "button:contains('Book')",
                "button:contains('Schedule')",
                "button:contains('Appointment')"
            ]
            
            for selector in business_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        indicators['has_booking_widget'] = True
                        indicators['business_elements'].extend([elem.get_attribute('outerHTML')[:200] for elem in elements[:3]])
                except:
                    pass
            
            # Look for business name elements
            name_selectors = [
                "h1", "h2", "h3", 
                "[class*='title']", 
                "[class*='name']",
                "[class*='business']",
                "[class*='company']"
            ]
            
            for selector in name_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if len(text) > 3 and len(text) < 100:
                            indicators['has_business_name'] = True
                            indicators['business_elements'].append(f"Title: {text}")
                            break
                except:
                    pass
            
            # Check if page has actually loaded content (not just spinner)
            page_source = self.driver.page_source
            content_indicators = [
                'book', 'appointment', 'schedule', 'service', 'clinic', 
                'treatment', 'therapy', 'consultation', 'wellness', 'health'
            ]
            
            content_score = sum(1 for indicator in content_indicators if indicator in page_source.lower())
            
            # Wait for any dynamic content to load
            time.sleep(2)
            
            # Check if we have moved beyond the loading screen
            try:
                loading_elements = self.driver.find_elements(By.CSS_SELECTOR, "[class*='loading'], [class*='spinner'], [id*='splash']")
                if not loading_elements:
                    # No loading screen visible
                    pass
            except:
                pass
            
            # Determine if this is a valid business page
            indicators['is_valid'] = (
                (indicators['has_booking_widget'] or 
                 indicators['has_business_name'] or 
                 content_score >= 2) and
                not indicators['has_error_message'] and
                len(page_source) > 8000  # More content than just the base template
            )
            
        except Exception as e:
            print(f"Error checking page indicators: {e}")
        
        return indicators
    
    def extract_brand_data(self, slug, indicators):
        """Extract brand information from the loaded page"""
        try:
            brand_data = {
                'slug': slug,
                'url': f"{self.base_url}{slug}",
                'final_url': self.driver.current_url,
                'title': indicators['page_title'],
                'business_name': '',
                'address': '',
                'phone': '',
                'services': '',
                'discovered_at': datetime.now().isoformat(),
                'indicators': str(indicators)
            }
            
            # Try to extract more specific information
            try:
                # Look for business name in various places
                name_selectors = ["h1", "h2", ".business-name", ".clinic-name", ".title"]
                for selector in name_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        text = element.text.strip()
                        if len(text) > 3 and not brand_data['business_name']:
                            brand_data['business_name'] = text
                            break
                    except:
                        pass
                
                # Look for address
                address_selectors = [".address", "[class*='address']", "[class*='location']"]
                for selector in address_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        brand_data['address'] = element.text.strip()
                        break
                    except:
                        pass
                
                # Look for phone
                phone_selectors = ["[href^='tel:']", ".phone", "[class*='phone']"]
                for selector in phone_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        brand_data['phone'] = element.text.strip() or element.get_attribute('href')
                        break
                    except:
                        pass
                
            except Exception as e:
                print(f"Error extracting detailed data: {e}")
            
            return brand_data
            
        except Exception as e:
            print(f"Error extracting brand data for {slug}: {e}")
            return {
                'slug': slug,
                'url': f"{self.base_url}{slug}",
                'error': str(e),
                'discovered_at': datetime.now().isoformat()
            }
    
    def save_to_csv(self):
        """Save found brands to CSV file"""
        if not self.found_brands:
            return
            
        fieldnames = [
            'slug', 'url', 'final_url', 'title', 'business_name', 
            'address', 'phone', 'services', 'discovered_at', 'indicators'
        ]
        
        with open('vsdhone_brands_browser.csv', 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for brand in self.found_brands:
                # Ensure all fields exist
                for field in fieldnames:
                    if field not in brand:
                        brand[field] = ''
                writer.writerow(brand)
        
        print(f"💾 Saved {len(self.found_brands)} brands to vsdhone_brands_browser.csv")
    
    def save_progress(self):
        """Save tested slugs to avoid retesting"""
        with open('tested_slugs_browser.txt', 'w') as f:
            for slug in sorted(self.tested_slugs):
                f.write(f"{slug}\n")
    
    def load_progress(self):
        """Load previously tested slugs"""
        try:
            with open('tested_slugs_browser.txt', 'r') as f:
                self.tested_slugs = set(line.strip() for line in f if line.strip())
            print(f"📁 Loaded {len(self.tested_slugs)} previously tested slugs")
        except FileNotFoundError:
            print("📁 No previous progress found, starting fresh")
    
    def run_discovery(self, max_attempts=100):
        """Run the browser-based discovery process"""
        if not SELENIUM_AVAILABLE:
            print("❌ Selenium not available. Please install: pip install selenium")
            return
        
        print("🚀 Starting browser-based VSDHOne brand discovery...")
        print(f"Known slugs to skip: {len(self.known_slugs)}")
        
        if not self.setup_browser():
            print("❌ Failed to setup browser")
            return
        
        # Load previous progress
        self.load_progress()
        
        attempts = 0
        found_count = 0
        
        try:
            for slug in self.generate_slugs():
                if attempts >= max_attempts:
                    print(f"Reached maximum attempts limit: {max_attempts}")
                    break
                
                attempts += 1
                
                if self.test_slug(slug):
                    found_count += 1
                
                # Add delay to be respectful
                time.sleep(random.uniform(2, 4))
                
                # Save progress periodically
                if attempts % 10 == 0:
                    self.save_progress()
                    print(f"Progress: {attempts} tested, {found_count} found")
        
        except KeyboardInterrupt:
            print("\n🛑 Discovery interrupted by user")
        
        finally:
            if self.driver:
                self.driver.quit()
            self.save_progress()
            self.save_to_csv()
            print(f"\n🎯 Discovery complete!")
            print(f"   • Total tested: {len(self.tested_slugs)}")
            print(f"   • Brands found: {len(self.found_brands)}")
            print(f"   • Results saved to: vsdhone_brands_browser.csv")

if __name__ == "__main__":
    discovery = BrowserVSDHOneDiscovery()
    
    # Allow command line argument for max attempts
    max_attempts = 50
    if len(sys.argv) > 1:
        try:
            max_attempts = int(sys.argv[1])
        except ValueError:
            print("Invalid max_attempts argument, using default 50")
    
    discovery.run_discovery(max_attempts=max_attempts) 