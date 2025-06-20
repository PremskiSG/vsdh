#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import json

def analyze_url(url, slug_name):
    print(f"\n{'='*60}")
    print(f"Analyzing: {slug_name} - {url}")
    print(f"{'='*60}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    try:
        response = session.get(url, timeout=15, allow_redirects=True)
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for script tags
        scripts = soup.find_all('script')
        print(f"Found {len(scripts)} script tags")
        
        # Look for any embedded data or configuration
        for i, script in enumerate(scripts):
            if script.string and len(script.string.strip()) > 100:
                content = script.string.strip()
                print(f"\nScript {i+1} (first 500 chars):")
                print(content[:500])
                
                # Look for JSON-like structures
                json_matches = re.findall(r'\{[^{}]*"[^"]*"[^{}]*\}', content)
                if json_matches:
                    print(f"Found {len(json_matches)} potential JSON objects")
                    for j, match in enumerate(json_matches[:3]):  # Show first 3
                        print(f"  JSON {j+1}: {match}")
        
        # Look for any meta tags or data attributes
        metas = soup.find_all('meta')
        for meta in metas:
            if meta.get('name') or meta.get('property'):
                print(f"Meta: {meta}")
        
        # Check if there are any API calls or fetch requests in the JS
        if 'fetch(' in response.text or 'XMLHttpRequest' in response.text or 'axios' in response.text:
            print("✅ Found AJAX/API call patterns")
        
        # Look for error-specific content
        if 'error' in response.text.lower():
            error_contexts = []
            lines = response.text.split('\n')
            for i, line in enumerate(lines):
                if 'error' in line.lower():
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    context = '\n'.join(lines[start:end])
                    error_contexts.append(context)
            
            print(f"\nFound {len(error_contexts)} error contexts:")
            for i, context in enumerate(error_contexts[:3]):  # Show first 3
                print(f"\nError Context {i+1}:")
                print(context)
        
    except Exception as e:
        print(f"Error: {e}")

# Test known good and potentially invalid slugs
test_cases = [
    ("https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/tc33l", "tc33l (known good)"),
    ("https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/aa00a", "aa00a (likely invalid)"),
    ("https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/zz99z", "zz99z (likely invalid)"),
]

for url, slug_name in test_cases:
    analyze_url(url, slug_name) 