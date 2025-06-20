#!/usr/bin/env python3
"""
Quick API Endpoint Tester for VSDHOne Platform
Tests various API endpoints to find where business data is actually served
"""

import requests
import json
import csv
from datetime import datetime

class QuickAPITester:
    def __init__(self):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net/"
        
        # Load a few sample slugs
        self.sample_slugs = []
        self.load_sample_slugs(5)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://vsdigital-bookingwidget-prod.azurewebsites.net/',
            'Origin': 'https://vsdigital-bookingwidget-prod.azurewebsites.net',
        })
    
    def load_sample_slugs(self, count=5):
        """Load a few sample slugs for testing"""
        try:
            with open('vsdhone_brands_smart.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.sample_slugs = [row['slug'] for row in list(reader)[:count]]
            print(f"📁 Loaded {len(self.sample_slugs)} sample slugs: {self.sample_slugs}")
        except FileNotFoundError:
            self.sample_slugs = ['yc92e', 'od74i', 'cp94s']  # Fallback
    
    def test_api_endpoints(self, slug):
        """Test various API endpoints for a given slug"""
        print(f"\n🔍 Testing API endpoints for slug: {slug}")
        
        # Extended list of potential API endpoints
        endpoints_to_test = [
            # Business-specific endpoints
            f"api/business/{slug}",
            f"api/businesses/{slug}",
            f"api/widget/business/{slug}",
            f"api/widget/{slug}/business",
            f"api/widget/{slug}",
            f"widget-api/business/{slug}",
            f"widget-api/{slug}",
            f"business-api/{slug}",
            f"booking-api/business/{slug}",
            
            # Config/settings endpoints
            f"api/config/{slug}",
            f"api/settings/{slug}",
            f"api/widget/{slug}/config",
            f"api/business/{slug}/config",
            f"config/{slug}",
            f"settings/{slug}",
            
            # Data endpoints
            f"api/data/{slug}",
            f"api/business/{slug}/data",
            f"api/business/{slug}/details",
            f"api/business/{slug}/info",
            f"api/business/{slug}/profile",
            f"data/{slug}",
            
            # Versioned endpoints
            f"api/v1/business/{slug}",
            f"api/v2/business/{slug}",
            f"api/v1/widget/{slug}",
            f"api/v2/widget/{slug}",
            
            # Alternative patterns
            f"business/{slug}/api",
            f"widget/{slug}/api",
            f"api/{slug}/business",
            f"api/{slug}/widget",
            f"api/{slug}",
            
            # With different query parameters
            f"api/business?id={slug}",
            f"api/widget?business={slug}",
            f"api/data?slug={slug}",
        ]
        
        results = []
        
        for endpoint in endpoints_to_test:
            try:
                url = f"{self.base_url}{endpoint}"
                
                # Test both GET and POST
                for method in ['GET', 'POST']:
                    try:
                        if method == 'GET':
                            response = self.session.get(url, timeout=5)
                        else:
                            # Try different POST payloads
                            payloads = [
                                {'slug': slug},
                                {'businessId': slug},
                                {'id': slug},
                                {'business': slug},
                            ]
                            
                            for payload in payloads:
                                response = self.session.post(url, json=payload, timeout=5)
                                if response.status_code != 404:
                                    break
                        
                        status = response.status_code
                        content_type = response.headers.get('content-type', '')
                        content_length = len(response.content)
                        
                        result = {
                            'slug': slug,
                            'endpoint': endpoint,
                            'method': method,
                            'status_code': status,
                            'content_type': content_type,
                            'content_length': content_length,
                            'response_preview': '',
                            'is_json': False,
                            'contains_business_data': False,
                        }
                        
                        if status == 200 and content_length > 0:
                            # Get response preview
                            try:
                                if 'json' in content_type:
                                    data = response.json()
                                    result['is_json'] = True
                                    result['response_preview'] = json.dumps(data, indent=2)[:500]
                                    
                                    # Check if it contains business-like data
                                    data_str = str(data).lower()
                                    business_indicators = [
                                        'name', 'address', 'phone', 'email', 'business', 
                                        'contact', 'location', 'company', 'service'
                                    ]
                                    if any(indicator in data_str for indicator in business_indicators):
                                        result['contains_business_data'] = True
                                        print(f"🎯 POTENTIAL MATCH: {method} {endpoint}")
                                        print(f"   Status: {status}, Content-Type: {content_type}")
                                        print(f"   Preview: {result['response_preview'][:200]}...")
                                else:
                                    result['response_preview'] = response.text[:300]
                                    
                                    # Check text content for business data
                                    text_lower = response.text.lower()
                                    if any(indicator in text_lower for indicator in ['name', 'address', 'phone', 'business']):
                                        result['contains_business_data'] = True
                                        print(f"🎯 POTENTIAL TEXT MATCH: {method} {endpoint}")
                                        
                            except Exception as e:
                                result['response_preview'] = f"Error parsing response: {e}"
                        
                        results.append(result)
                        
                        # Print interesting responses
                        if status not in [404, 500] and content_length > 100:
                            print(f"📡 {status} {method} {endpoint} ({content_length} bytes)")
                            
                    except requests.exceptions.Timeout:
                        print(f"⏱️  Timeout: {method} {endpoint}")
                    except Exception as e:
                        print(f"❌ Error: {method} {endpoint} - {e}")
                        
            except Exception as e:
                print(f"❌ General error for {endpoint}: {e}")
        
        return results
    
    def run_comprehensive_test(self):
        """Run comprehensive API testing on sample slugs"""
        print("🚀 Starting comprehensive API endpoint testing...")
        
        all_results = []
        
        for slug in self.sample_slugs:
            results = self.test_api_endpoints(slug)
            all_results.extend(results)
        
        # Save results
        self.save_results(all_results)
        
        # Analyze results
        self.analyze_results(all_results)
    
    def save_results(self, results):
        """Save API test results to CSV"""
        filename = f'api_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        fieldnames = [
            'slug', 'endpoint', 'method', 'status_code', 'content_type', 
            'content_length', 'is_json', 'contains_business_data', 'response_preview'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"💾 API test results saved to: {filename}")
    
    def analyze_results(self, results):
        """Analyze API test results and show promising endpoints"""
        print(f"\n📊 API TEST ANALYSIS")
        print(f"=" * 50)
        
        total_tests = len(results)
        successful_200 = [r for r in results if r['status_code'] == 200]
        json_responses = [r for r in results if r['is_json']]
        business_data = [r for r in results if r['contains_business_data']]
        
        print(f"Total API calls tested: {total_tests}")
        print(f"Successful (200) responses: {len(successful_200)}")
        print(f"JSON responses: {len(json_responses)}")
        print(f"Responses with business data: {len(business_data)}")
        
        if business_data:
            print(f"\n🎯 PROMISING ENDPOINTS:")
            for result in business_data:
                print(f"  • {result['method']} {result['endpoint']}")
                print(f"    Status: {result['status_code']}, Type: {result['content_type']}")
                print(f"    Preview: {result['response_preview'][:100]}...")
                print()
        
        # Show unique status codes
        status_codes = {}
        for result in results:
            status = result['status_code']
            status_codes[status] = status_codes.get(status, 0) + 1
        
        print(f"\n📈 STATUS CODE DISTRIBUTION:")
        for status, count in sorted(status_codes.items()):
            print(f"  {status}: {count} responses")
        
        # Show endpoints with non-404 responses
        interesting_endpoints = {}
        for result in results:
            if result['status_code'] not in [404, 500]:
                endpoint = result['endpoint']
                if endpoint not in interesting_endpoints:
                    interesting_endpoints[endpoint] = []
                interesting_endpoints[endpoint].append(result['status_code'])
        
        if interesting_endpoints:
            print(f"\n🔍 NON-404 ENDPOINTS:")
            for endpoint, statuses in interesting_endpoints.items():
                print(f"  {endpoint}: {list(set(statuses))}")

if __name__ == "__main__":
    tester = QuickAPITester()
    tester.run_comprehensive_test() 