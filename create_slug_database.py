#!/usr/bin/env python3
"""
VSDHOne Slug Database Creator
Creates comprehensive JSON and CSV files with all tested slugs and their results
"""

import json
import csv
import os
from datetime import datetime
from collections import defaultdict

def extract_slugs_from_files():
    """Extract all tested slugs from various result files"""
    all_slugs = {}
    
    # Known active business slugs
    known_active = {
        'ad31y': {'business_name': 'The DRIPBaR Direct - Sebring (FL)', 'status': 'ACTIVE'},
        'tc33l': {'business_name': 'Altura Health (TX)', 'status': 'ACTIVE'},
        'mj42f': {'status': 'ACTIVE'},
        'os27m': {'status': 'ACTIVE'},
        'lp56a': {'status': 'ACTIVE'},
        'zb74k': {'status': 'ACTIVE'},
        'ym99l': {'status': 'ACTIVE'},
        'yh52b': {'status': 'ACTIVE'},
        'zd20w': {'status': 'ACTIVE'},
        'td32z': {'status': 'ACTIVE'},
        'bo19e': {'status': 'ACTIVE'},
        'bh70s': {'status': 'ACTIVE'},
        'ai04u': {'status': 'ACTIVE'},
        'bm49t': {'status': 'ACTIVE'},
        'qu29u': {'status': 'ACTIVE'}
    }
    
    # Add known active slugs
    for slug, info in known_active.items():
        all_slugs[slug] = {
            'slug': slug,
            'status': info['status'],
            'business_name': info.get('business_name', ''),
            'tested_method': 'Known_Working',
            'last_tested': '2025-06-20',
            'url': f'https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/{slug}',
            'redirects_to': '',
            'content_length': '',
            'business_indicators': '',
            'services': '',
            'description': ''
        }
    
    # Extract from tested_slugs_smart.txt (API tested)
    if os.path.exists('tested_slugs_smart.txt'):
        with open('tested_slugs_smart.txt', 'r') as f:
            for line in f:
                slug = line.strip()
                if len(slug) == 5 and slug not in all_slugs:
                    all_slugs[slug] = {
                        'slug': slug,
                        'status': 'INACTIVE_401',
                        'business_name': '',
                        'tested_method': 'API_HTTP',
                        'last_tested': '2025-06-20',
                        'url': f'https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/{slug}',
                        'redirects_to': '/widget/401',
                        'content_length': '7537',
                        'business_indicators': '0',
                        'services': '',
                        'description': 'Returns identical React SPA HTML - likely inactive account'
                    }
    
    # Extract from browser extraction results
    if os.path.exists('browser_extraction_results_20250620_132138.csv'):
        with open('browser_extraction_results_20250620_132138.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                slug = row['slug']
                if len(slug) == 5:
                    all_slugs[slug] = {
                        'slug': slug,
                        'status': 'INACTIVE_401',
                        'business_name': row.get('business_name', ''),
                        'tested_method': 'Browser_Automation',
                        'last_tested': row.get('extracted_at', '2025-06-20')[:10],
                        'url': row.get('original_url', f'https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/{slug}'),
                        'redirects_to': '/widget/401',
                        'content_length': '49',
                        'business_indicators': '0',
                        'services': '',
                        'description': '401 ERROR Nothing left to do here. Go To HomePage'
                    }
    
    # Extract from API test results
    if os.path.exists('api_test_results_20250620_131821.csv'):
        with open('api_test_results_20250620_131821.csv', 'r') as f:
            reader = csv.DictReader(f)
            tested_slugs = set()
            for row in reader:
                slug = row['slug']
                if len(slug) == 5:
                    tested_slugs.add(slug)
            
            # Add any new slugs from API results
            for slug in tested_slugs:
                if slug not in all_slugs:
                    all_slugs[slug] = {
                        'slug': slug,
                        'status': 'INACTIVE_401',
                        'business_name': '',
                        'tested_method': 'API_HTTP',
                        'last_tested': '2025-06-20',
                        'url': f'https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/{slug}',
                        'redirects_to': '/widget/401',
                        'content_length': '7537',
                        'business_indicators': '0',
                        'services': '',
                        'description': 'Returns identical React SPA HTML - likely inactive account'
                    }
    
    # Add ranges from other laptop (as individual entries)
    other_laptop_ranges = [
        ('faaaa', 'fabon', 'Range tested on other laptop - all inactive'),
        ('yaaaa', 'yabny', 'Range tested on other laptop - all inactive'),
        ('paaaa', 'pabhs', 'Range tested on other laptop - all inactive')
    ]
    
    for start, end, description in other_laptop_ranges:
        # Generate individual slugs for these ranges
        import string
        charset = string.digits + string.ascii_lowercase
        
        # For now, just add the start and end of each range as examples
        for slug in [start, end]:
            if slug not in all_slugs:
                all_slugs[slug] = {
                    'slug': slug,
                    'status': 'INACTIVE_401',
                    'business_name': '',
                    'tested_method': 'Other_Laptop_Range',
                    'last_tested': '2025-06-20',
                    'url': f'https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/{slug}',
                    'redirects_to': '/widget/401',
                    'content_length': '',
                    'business_indicators': '0',
                    'services': '',
                    'description': description
                }
    
    return all_slugs

def create_json_database(all_slugs):
    """Create comprehensive JSON database"""
    
    # Separate active and inactive
    active_slugs = {k: v for k, v in all_slugs.items() if v['status'] == 'ACTIVE'}
    inactive_slugs = {k: v for k, v in all_slugs.items() if v['status'] != 'ACTIVE'}
    
    # Group by testing method
    by_method = defaultdict(list)
    for slug_data in all_slugs.values():
        by_method[slug_data['tested_method']].append(slug_data)
    
    database = {
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'total_slugs_tested': len(all_slugs),
            'active_businesses_found': len(active_slugs),
            'inactive_slugs_found': len(inactive_slugs),
            'testing_methods': list(by_method.keys()),
            'platform_url': 'https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/',
            'slug_pattern': '[0-9a-z]{5}',
            'total_possible_combinations': 36**5,
            'percentage_tested': f"{(len(all_slugs) / (36**5)) * 100:.6f}%"
        },
        'active_businesses': {
            'count': len(active_slugs),
            'slugs': list(active_slugs.values())
        },
        'inactive_slugs': {
            'count': len(inactive_slugs),
            'slugs': list(inactive_slugs.values())
        },
        'by_testing_method': {
            method: {
                'count': len(slugs),
                'slugs': slugs
            } for method, slugs in by_method.items()
        },
        'all_slugs': list(all_slugs.values())
    }
    
    return database

def create_csv_database(all_slugs):
    """Create CSV database with all slug information"""
    
    fieldnames = [
        'slug', 'status', 'business_name', 'tested_method', 'last_tested',
        'url', 'redirects_to', 'content_length', 'business_indicators',
        'services', 'description'
    ]
    
    # Sort slugs alphabetically
    sorted_slugs = sorted(all_slugs.values(), key=lambda x: x['slug'])
    
    return fieldnames, sorted_slugs

def save_databases():
    """Main function to create and save both databases"""
    
    print("🔍 Extracting all tested slugs from result files...")
    all_slugs = extract_slugs_from_files()
    
    print(f"📊 Found {len(all_slugs)} unique tested slugs")
    
    # Create JSON database
    print("📝 Creating JSON database...")
    json_db = create_json_database(all_slugs)
    
    json_filename = f"vsdhone_slug_database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(json_db, f, indent=2, ensure_ascii=False)
    
    print(f"💾 JSON database saved: {json_filename}")
    
    # Create CSV database
    print("📝 Creating CSV database...")
    fieldnames, csv_data = create_csv_database(all_slugs)
    
    csv_filename = f"vsdhone_slug_database_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
    
    print(f"💾 CSV database saved: {csv_filename}")
    
    # Print summary
    active_count = len([s for s in all_slugs.values() if s['status'] == 'ACTIVE'])
    inactive_count = len(all_slugs) - active_count
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total slugs tested: {len(all_slugs):,}")
    print(f"   Active businesses: {active_count}")
    print(f"   Inactive slugs: {inactive_count:,}")
    print(f"   Success rate: {(active_count/len(all_slugs)*100):.4f}%")
    
    # Return filenames for updating scanner
    return json_filename, csv_filename, all_slugs

if __name__ == "__main__":
    save_databases() 