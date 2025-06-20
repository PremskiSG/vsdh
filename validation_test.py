#!/usr/bin/env python3
"""
Validation Test - Test 2 known working slugs + 3 expected 401 slugs
"""

import time
import requests
from datetime import datetime

class ValidationTest:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net"
        self.api_endpoint = "/api/business/"
        self.timeout = 10
        
        # Test slugs
        self.test_slugs = {
            'tc33l': 'Known Working - Altura Health (TX)',
            'ad31y': 'Known Working - The DRIPBaR Direct',
            'aaaaa': 'Expected 401 Error',
            'aaaab': 'Expected 401 Error', 
            'aaaac': 'Expected 401 Error'
        }
        
        print("🧪 VSDHOne Validation Test")
        print("=" * 50)
        print(f"Testing {len(self.test_slugs)} slugs to validate detection logic")
        print("")
    
    def test_slug_detailed(self, slug, description):
        """Test a single slug with detailed output"""
        print(f"🔍 Testing: {slug} ({description})")
        print(f"   URL: {self.base_url}{self.api_endpoint}{slug}")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{self.api_endpoint}{slug}", timeout=self.timeout)
            response_time = time.time() - start_time
            
            # Get response details
            content = response.text
            content_lower = content.lower()
            
            # Business indicators
            business_indicators = [
                'business_name', 'company', 'clinic', 'center', 'health',
                'medical', 'therapy', 'treatment', 'doctor', 'wellness',
                'spa', 'hotel', 'booking', 'appointment', 'schedule',
                'service', 'price', 'location', 'contact', 'phone'
            ]
            
            has_business_content = any(indicator in content_lower for indicator in business_indicators)
            business_indicator_count = sum(1 for indicator in business_indicators if indicator in content_lower)
            
            # Error detection
            has_401 = '401' in content
            has_error = 'error' in content_lower
            has_nothing_left = 'nothing left to do here' in content_lower
            
            # Validation levels
            validation_levels = []
            if response.status_code == 200:
                validation_levels.append("valid_response")
            if len(content) > 1000:
                validation_levels.append("substantial_content")
            if has_business_content:
                validation_levels.append("business_indicators")
            if 'json' in response.headers.get('content-type', ''):
                validation_levels.append("json_content")
            if not any([has_401, has_error, has_nothing_left]):
                validation_levels.append("non_error")
            
            # Results
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📏 Content Length: {len(content):,} chars")
            print(f"   📝 Content Type: {response.headers.get('content-type', 'N/A')}")
            print(f"   ⏱️  Response Time: {response_time:.2f}s")
            print(f"   🏢 Business Indicators: {business_indicator_count}/{len(business_indicators)}")
            print(f"   🎯 Validation Levels: {len(validation_levels)} ({', '.join(validation_levels)})")
            
            # Error analysis
            if has_401:
                print(f"   🚫 Contains '401': YES")
            if has_error:
                print(f"   ❌ Contains 'error': YES")
            if has_nothing_left:
                print(f"   🛑 Contains 'nothing left to do here': YES")
            
            # First 200 characters for inspection
            first_chars = content[:200].replace('\n', ' ').replace('\r', ' ').strip()
            print(f"   📄 First 200 chars: {first_chars}")
            
            # Classification
            if len(validation_levels) >= 3 and not any([has_401, has_error]):
                print(f"   🌟 CLASSIFICATION: PROMISING BUSINESS SLUG")
            elif has_401 or has_nothing_left:
                print(f"   🚫 CLASSIFICATION: 401 ERROR PAGE")  
            elif response.status_code == 200 and len(content) > 1000:
                print(f"   ⚠️  CLASSIFICATION: VALID RESPONSE, NO BUSINESS INDICATORS")
            else:
                print(f"   ❓ CLASSIFICATION: UNKNOWN/ERROR")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print("")
        return True
    
    def run_validation_test(self):
        """Run the validation test"""
        print(f"🚀 Starting validation test at {datetime.now().strftime('%H:%M:%S')}")
        print("")
        
        results = []
        for i, (slug, description) in enumerate(self.test_slugs.items(), 1):
            print(f"[{i}/{len(self.test_slugs)}] " + "="*60)
            success = self.test_slug_detailed(slug, description)
            results.append(success)
            
            # Rate limiting
            if i < len(self.test_slugs):
                print("⏳ Waiting 2 seconds before next test...")
                time.sleep(2)
        
        print("🎯 VALIDATION TEST COMPLETE")
        print("=" * 50)
        print(f"✅ Tests completed: {len(results)}")
        print(f"📊 Success rate: {sum(results)}/{len(results)}")
        print("")
        print("📋 EXPECTED RESULTS:")
        print("   • tc33l & ad31y should show: PROMISING BUSINESS SLUG")
        print("   • aaaaa, aaaab, aaaac should show: 401 ERROR PAGE")

def main():
    tester = ValidationTest()
    tester.run_validation_test()

if __name__ == "__main__":
    main() 