#!/usr/bin/env python3
"""
Widget Validation Test - Test the actual widget endpoints
"""

import time
import requests
from datetime import datetime

class WidgetValidationTest:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net"
        self.widget_endpoint = "/widget-business/"
        self.timeout = 10
        
        # Test slugs
        self.test_slugs = {
            'tc33l': 'Known Working - Altura Health (TX)',
            'ad31y': 'Known Working - The DRIPBaR Direct',  
            'aaaaa': 'Expected 401 Error',
            'aaaab': 'Expected 401 Error',
            'aaaac': 'Expected 401 Error'
        }
        
        print("🌐 VSDHOne Widget Validation Test")
        print("=" * 50)
        print(f"Testing {len(self.test_slugs)} slugs at WIDGET endpoint")
        print(f"Endpoint: {self.base_url}{self.widget_endpoint}")
        print("")
    
    def test_widget_slug(self, slug, description):
        """Test a single slug at the widget endpoint"""
        print(f"🔍 Testing: {slug} ({description})")
        widget_url = f"{self.base_url}{self.widget_endpoint}{slug}"
        print(f"   URL: {widget_url}")
        
        try:
            start_time = time.time()
            response = requests.get(widget_url, timeout=self.timeout, allow_redirects=True)
            response_time = time.time() - start_time
            
            # Track redirects
            final_url = response.url
            was_redirected = final_url != widget_url
            
            # Get response details
            content = response.text
            content_lower = content.lower()
            
            # Business indicators
            business_indicators = [
                'altura health', 'dripbar', 'business', 'appointment', 'booking',
                'schedule', 'clinic', 'medical', 'health', 'therapy', 'treatment',
                'service', 'price', 'location', 'contact', 'phone', 'doctor'
            ]
            
            # Error indicators
            error_indicators = ['401', 'error', 'nothing left to do here', 'go to homepage']
            
            # Analysis
            has_business_content = any(indicator in content_lower for indicator in business_indicators)
            business_indicator_count = sum(1 for indicator in business_indicators if indicator in content_lower)
            
            has_error_content = any(indicator in content_lower for indicator in error_indicators)
            error_indicator_count = sum(1 for indicator in error_indicators if indicator in content_lower)
            
            # Results
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📏 Content Length: {len(content):,} chars")
            print(f"   📝 Content Type: {response.headers.get('content-type', 'N/A')}")
            print(f"   ⏱️  Response Time: {response_time:.2f}s")
            print(f"   🔄 Redirected: {was_redirected}")
            if was_redirected:
                print(f"   🎯 Final URL: {final_url}")
            
            print(f"   🏢 Business Indicators: {business_indicator_count} found")
            print(f"   🚫 Error Indicators: {error_indicator_count} found")
            
            # Show found indicators
            if has_business_content:
                found_business = [ind for ind in business_indicators if ind in content_lower]
                print(f"   ✅ Business terms found: {', '.join(found_business)}")
            
            if has_error_content:
                found_errors = [ind for ind in error_indicators if ind in content_lower]
                print(f"   ❌ Error terms found: {', '.join(found_errors)}")
            
            # First 300 characters for inspection
            first_chars = content[:300].replace('\n', ' ').replace('\r', ' ').strip()
            print(f"   📄 First 300 chars: {first_chars}")
            
            # Classification
            if has_error_content and '401' in content_lower:
                print(f"   🚫 CLASSIFICATION: 401 ERROR PAGE")
            elif has_business_content and not has_error_content:
                print(f"   🌟 CLASSIFICATION: ACTIVE BUSINESS PAGE")
            elif response.status_code == 200 and len(content) > 1000:
                print(f"   ⚠️  CLASSIFICATION: VALID RESPONSE, CONTENT UNCLEAR")
            else:
                print(f"   ❓ CLASSIFICATION: UNKNOWN/ERROR")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
        
        print("")
        return True
    
    def run_widget_validation(self):
        """Run the widget validation test"""
        print(f"🚀 Starting widget validation at {datetime.now().strftime('%H:%M:%S')}")
        print("")
        
        results = []
        for i, (slug, description) in enumerate(self.test_slugs.items(), 1):
            print(f"[{i}/{len(self.test_slugs)}] " + "="*70)
            success = self.test_widget_slug(slug, description)
            results.append(success)
            
            # Rate limiting
            if i < len(self.test_slugs):
                print("⏳ Waiting 3 seconds before next test...")
                time.sleep(3)
        
        print("🎯 WIDGET VALIDATION TEST COMPLETE")
        print("=" * 50)
        print(f"✅ Tests completed: {len(results)}")
        print("")
        print("📋 EXPECTED RESULTS:")
        print("   • tc33l & ad31y should show: ACTIVE BUSINESS PAGE")
        print("   • aaaaa, aaaab, aaaac should show: 401 ERROR PAGE")

def main():
    tester = WidgetValidationTest()
    tester.run_widget_validation()

if __name__ == "__main__":
    main() 