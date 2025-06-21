#!/usr/bin/env python3
"""
Update VSDHOne Slug Database
Updates the comprehensive slug database with new scan results
"""

import json
import csv
import os
import glob
from datetime import datetime
from create_slug_database import save_databases

def update_database_with_new_results():
    """Update the database with any new browser scan results"""
    
    print("🔄 Updating slug database with new scan results...")
    
    # Find all browser result files that haven't been processed
    result_files = glob.glob("browser_comprehensive_results_*.csv")
    
    if not result_files:
        print("📭 No new browser scan results found")
        return
    
    print(f"📁 Found {len(result_files)} result files to process")
    
    # Load existing database
    json_files = glob.glob("vsdhone_slug_database_*.json")
    if json_files:
        latest_db = max(json_files, key=os.path.getctime)
        print(f"📖 Loading existing database: {latest_db}")
        
        with open(latest_db, 'r', encoding='utf-8') as f:
            existing_db = json.load(f)
        
        existing_slugs = {slug['slug']: slug for slug in existing_db['all_slugs']}
    else:
        existing_slugs = {}
    
    new_findings = 0
    
    # Process each result file
    for result_file in result_files:
        print(f"📄 Processing: {result_file}")
        
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    slug = row['slug']
                    
                    if slug not in existing_slugs:
                        # This is a new finding!
                        new_findings += 1
                        
                        existing_slugs[slug] = {
                            'slug': slug,
                            'status': 'ACTIVE' if row['classification'] == 'ACTIVE_BUSINESS' else 'INACTIVE_401',
                            'business_name': '',
                            'tested_method': 'Browser_Automation',
                            'last_tested': row['tested_at'][:10],
                            'url': row['url'],
                            'redirects_to': '',
                            'content_length': row['content_length'],
                            'business_indicators': row['business_indicators'],
                            'services': '',
                            'description': f"Found via browser scan - {row['business_indicators']} business indicators"
                        }
                        
                        print(f"   ✨ NEW ACTIVE BUSINESS: {slug}")
        
        except Exception as e:
            print(f"   ⚠️  Error processing {result_file}: {e}")
    
    if new_findings > 0:
        print(f"\n🎉 Found {new_findings} new business(es)! Updating database...")
        
        # Recreate the database with all findings
        save_databases()
        
        print("✅ Database updated successfully!")
    else:
        print("📊 No new active businesses found in scan results")

if __name__ == "__main__":
    update_database_with_new_results() 