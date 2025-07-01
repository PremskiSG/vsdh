#!/usr/bin/env python3
"""
Merge Combined Scanner Results - Extract Active Businesses Only
============================================================
This script merges all combined scanner CSV results from the logs directory
and extracts only the active businesses, removing duplicates and providing
comprehensive analysis.
"""

import os
import csv
import json
import pandas as pd
from datetime import datetime
from collections import defaultdict
import base64

def decode_base64_slug(slug):
    """Decode base64 slug to original number"""
    try:
        decoded = base64.b64decode(slug).decode('utf-8')
        return decoded
    except:
        return slug

def load_all_combined_results():
    """Load all combined scanner CSV results from logs directory"""
    logs_dir = "logs"
    all_results = []
    processed_files = []
    
    print("🔍 Scanning logs directory for combined scanner results...")
    
    for filename in os.listdir(logs_dir):
        if filename.startswith("SESSION_COMBINED_") and filename.endswith("_results.csv"):
            filepath = os.path.join(logs_dir, filename)
            print(f"📄 Loading: {filename}")
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    file_results = list(reader)
                    all_results.extend(file_results)
                    processed_files.append(filename)
                    print(f"   ✅ Loaded {len(file_results)} records")
            except Exception as e:
                print(f"   ❌ Error loading {filename}: {e}")
    
    print(f"\n📊 Total files processed: {len(processed_files)}")
    print(f"📊 Total records loaded: {len(all_results)}")
    
    return all_results, processed_files

def extract_active_businesses(all_results):
    """Extract only active businesses from all results"""
    active_businesses = []
    
    print("\n🔍 Extracting active businesses...")
    
    for result in all_results:
        slug = result.get('slug', '')
        enterprise_status = result.get('enterprise_status', '')
        hydreight_status = result.get('hydreight_status', '')
        enterprise_business_name = result.get('enterprise_business_name', '')
        hydreight_business_name = result.get('hydreight_business_name', '')
        
        # Check if either platform has an active business
        enterprise_active = enterprise_status == 'ACTIVE'
        hydreight_active = hydreight_status == 'ACTIVE'
        
        if enterprise_active or hydreight_active:
            # Decode the slug to get the original number
            decoded_slug = decode_base64_slug(slug)
            
            active_business = {
                'slug': slug,
                'decoded_slug': decoded_slug,
                'enterprise_active': enterprise_active,
                'hydreight_active': hydreight_active,
                'both_active': enterprise_active and hydreight_active,
                'enterprise_business_name': enterprise_business_name if enterprise_active else '',
                'hydreight_business_name': hydreight_business_name if hydreight_active else '',
                'primary_business_name': enterprise_business_name if enterprise_active else hydreight_business_name,
                'primary_platform': 'Enterprise' if enterprise_active else 'Hydreight',
                'enterprise_status': enterprise_status,
                'hydreight_status': hydreight_status,
                'enterprise_page_title': result.get('enterprise_page_title', ''),
                'hydreight_page_title': result.get('hydreight_page_title', ''),
                'enterprise_url': result.get('enterprise_url', ''),
                'hydreight_url': result.get('hydreight_url', ''),
                'tested_at': result.get('tested_at', '')
            }
            active_businesses.append(active_business)
    
    print(f"✅ Found {len(active_businesses)} active businesses")
    return active_businesses

def remove_duplicates(active_businesses):
    """Remove duplicate businesses based on slug"""
    seen_slugs = set()
    unique_businesses = []
    duplicates_removed = 0
    
    print("\n🔍 Removing duplicates...")
    
    for business in active_businesses:
        slug = business['slug']
        if slug not in seen_slugs:
            seen_slugs.add(slug)
            unique_businesses.append(business)
        else:
            duplicates_removed += 1
    
    print(f"✅ Removed {duplicates_removed} duplicates")
    print(f"✅ {len(unique_businesses)} unique active businesses")
    
    return unique_businesses

def analyze_active_businesses(unique_businesses):
    """Analyze the active businesses and provide statistics"""
    print("\n📊 ACTIVE BUSINESSES ANALYSIS:")
    print("=" * 60)
    
    # Basic stats
    total_active = len(unique_businesses)
    enterprise_only = sum(1 for b in unique_businesses if b['enterprise_active'] and not b['hydreight_active'])
    hydreight_only = sum(1 for b in unique_businesses if b['hydreight_active'] and not b['enterprise_active'])
    both_platforms = sum(1 for b in unique_businesses if b['both_active'])
    
    print(f"📈 Total Active Businesses: {total_active}")
    print(f"🏢 Enterprise Only: {enterprise_only}")
    print(f"💧 Hydreight Only: {hydreight_only}")
    print(f"🎯 Both Platforms: {both_platforms}")
    
    # Business name analysis
    business_name_counts = defaultdict(int)
    for business in unique_businesses:
        name = business['primary_business_name']
        if name:
            business_name_counts[name] += 1
    
    print(f"\n🏪 Business Name Distribution:")
    print("-" * 40)
    for name, count in sorted(business_name_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {name}: {count}")
    
    # Platform distribution
    platform_counts = defaultdict(int)
    for business in unique_businesses:
        platform_counts[business['primary_platform']] += 1
    
    print(f"\n🌐 Platform Distribution:")
    print("-" * 40)
    for platform, count in platform_counts.items():
        print(f"   {platform}: {count}")
    
    return {
        'total_active': total_active,
        'enterprise_only': enterprise_only,
        'hydreight_only': hydreight_only,
        'both_platforms': both_platforms,
        'business_name_counts': dict(business_name_counts),
        'platform_counts': dict(platform_counts)
    }

def save_active_businesses(unique_businesses, stats):
    """Save active businesses to multiple formats"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save as CSV
    csv_filename = f"COMBINED_ACTIVE_BUSINESSES_{timestamp}.csv"
    fieldnames = [
        'slug', 'decoded_slug', 'primary_business_name', 'primary_platform',
        'enterprise_active', 'hydreight_active', 'both_active',
        'enterprise_business_name', 'hydreight_business_name',
        'enterprise_status', 'hydreight_status',
        'enterprise_page_title', 'hydreight_page_title',
        'enterprise_url', 'hydreight_url', 'tested_at'
    ]
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_businesses)
    
    print(f"💾 Active businesses saved to: {csv_filename}")
    
    # Save summary report
    summary_filename = f"COMBINED_ACTIVE_BUSINESSES_SUMMARY_{timestamp}.md"
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write("# Combined Scanner - Active Businesses Summary\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Overview\n\n")
        f.write(f"- **Total Active Businesses:** {stats['total_active']}\n")
        f.write(f"- **Enterprise Only:** {stats['enterprise_only']}\n")
        f.write(f"- **Hydreight Only:** {stats['hydreight_only']}\n")
        f.write(f"- **Both Platforms:** {stats['both_platforms']}\n\n")
        
        f.write("## Business Name Distribution\n\n")
        f.write("| Business Name | Count |\n")
        f.write("|---------------|-------|\n")
        for name, count in sorted(stats['business_name_counts'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"| {name} | {count} |\n")
        
        f.write("\n## Platform Distribution\n\n")
        f.write("| Platform | Count |\n")
        f.write("|----------|-------|\n")
        for platform, count in stats['platform_counts'].items():
            f.write(f"| {platform} | {count} |\n")
        
        f.write("\n## Active Businesses List\n\n")
        f.write("| Slug | Decoded | Business Name | Platform | Enterprise | Hydreight |\n")
        f.write("|------|---------|---------------|----------|------------|----------|\n")
        
        for business in sorted(unique_businesses, key=lambda x: int(x['decoded_slug']) if x['decoded_slug'].isdigit() else 999999):
            enterprise_status = "✅" if business['enterprise_active'] else "❌"
            hydreight_status = "✅" if business['hydreight_active'] else "❌"
            f.write(f"| {business['slug']} | {business['decoded_slug']} | {business['primary_business_name']} | {business['primary_platform']} | {enterprise_status} | {hydreight_status} |\n")
    
    print(f"📄 Summary report saved to: {summary_filename}")
    
    # Save as JSON for programmatic access
    json_filename = f"COMBINED_ACTIVE_BUSINESSES_{timestamp}.json"
    output_data = {
        'generated_at': datetime.now().isoformat(),
        'statistics': stats,
        'active_businesses': unique_businesses
    }
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"🔧 JSON data saved to: {json_filename}")
    
    return csv_filename, summary_filename, json_filename

def main():
    """Main function to merge and analyze combined scanner results"""
    print("🚀 Combined Scanner Results Merger")
    print("=" * 50)
    
    # Load all results
    all_results, processed_files = load_all_combined_results()
    
    if not all_results:
        print("❌ No combined scanner results found in logs directory!")
        return
    
    # Extract active businesses
    active_businesses = extract_active_businesses(all_results)
    
    if not active_businesses:
        print("❌ No active businesses found in the results!")
        return
    
    # Remove duplicates
    unique_businesses = remove_duplicates(active_businesses)
    
    # Analyze businesses
    stats = analyze_active_businesses(unique_businesses)
    
    # Save results
    csv_file, summary_file, json_file = save_active_businesses(unique_businesses, stats)
    
    print(f"\n🎉 MERGE COMPLETE!")
    print("=" * 50)
    print(f"📊 Processed {len(processed_files)} log files")
    print(f"📊 Found {len(unique_businesses)} unique active businesses")
    print(f"💾 Results saved to:")
    print(f"   - CSV: {csv_file}")
    print(f"   - Summary: {summary_file}")
    print(f"   - JSON: {json_file}")

if __name__ == "__main__":
    main() 