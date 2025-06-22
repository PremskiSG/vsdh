#!/usr/bin/env python3
"""
Merge VSDHOne Data from Other Laptop
Merges session logs and database from other laptop with current data
"""

import json
import csv
import os
import glob
import shutil
from datetime import datetime
from collections import defaultdict

def load_master_database(db_path):
    """Load master database from JSON file"""
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {db_path}: {e}")
        return None

def extract_active_businesses_from_sessions(logs_dir):
    """Extract active businesses from session files"""
    active_businesses = {}
    
    # Process all session JSON files
    session_files = glob.glob(os.path.join(logs_dir, "SESSION_*.json"))
    
    for session_file in session_files:
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Check if this is a results array
                if isinstance(data, list):
                    for result in data:
                        if isinstance(result, dict) and result.get('status') == 'ACTIVE':
                            slug = result.get('slug')
                            if slug:
                                active_businesses[slug] = result
                
                # Check if this is a single result object
                elif isinstance(data, dict) and data.get('status') == 'ACTIVE':
                    slug = data.get('slug')
                    if slug:
                        active_businesses[slug] = data
                        
        except Exception as e:
            print(f"Error processing {session_file}: {e}")
    
    return active_businesses

def extract_active_businesses_from_csvs(logs_dir):
    """Extract active businesses from CSV result files"""
    active_businesses = {}
    
    # Process all CSV result files
    csv_files = glob.glob(os.path.join(logs_dir, "SESSION_*_results.csv"))
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    if row.get('status') == 'ACTIVE':
                        slug = row.get('slug')
                        if slug:
                            active_businesses[slug] = {
                                'slug': slug,
                                'status': 'ACTIVE',
                                'business_name': row.get('business_name', ''),
                                'url': row.get('url', ''),
                                'final_url': row.get('final_url', ''),
                                'classification': row.get('classification', ''),
                                'business_indicators': row.get('business_indicators', ''),
                                'page_title': row.get('page_title', ''),
                                'content_length': row.get('content_length', ''),
                                'load_time': row.get('load_time', ''),
                                'content_preview': row.get('content_preview', ''),
                                'tested_at': row.get('tested_at', '')
                            }
                            
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
    
    return active_businesses

def merge_databases():
    """Main function to merge data from other laptop"""
    
    print("🔄 Merging data from other laptop...")
    
    # Load current master database
    current_db = load_master_database("MASTER_DATABASE.json")
    if not current_db:
        print("❌ Could not load current master database")
        return
    
    # Load other laptop's master database
    other_db = load_master_database("other_laptop/MASTER_DATABASE.json")
    if not other_db:
        print("❌ Could not load other laptop's master database")
        return
    
    print(f"📊 Current database: {len(current_db)} entries")
    print(f"📊 Other laptop database: {len(other_db)} entries")
    
    # Extract active businesses from other laptop's session logs
    other_active_sessions = extract_active_businesses_from_sessions("other_laptop/logs/")
    other_active_csvs = extract_active_businesses_from_csvs("other_laptop/logs/")
    
    print(f"🔍 Found {len(other_active_sessions)} active businesses in other laptop's session files")
    print(f"🔍 Found {len(other_active_csvs)} active businesses in other laptop's CSV files")
    
    # Combine all active businesses from other laptop
    all_other_active = {}
    all_other_active.update(other_active_sessions)
    all_other_active.update(other_active_csvs)
    
    print(f"📈 Total unique active businesses from other laptop: {len(all_other_active)}")
    
    # Check which ones are new
    current_slugs = set()
    if isinstance(current_db, dict):
        if 'all_slugs' in current_db:
            for entry in current_db['all_slugs']:
                if isinstance(entry, dict) and 'slug' in entry:
                    current_slugs.add(entry['slug'])
        else:
            # If it's a flat dict, use keys as slugs
            current_slugs = set(current_db.keys())
    else:
        for entry in current_db:
            if isinstance(entry, dict) and 'slug' in entry:
                current_slugs.add(entry['slug'])
    
    new_businesses = {}
    for slug, business in all_other_active.items():
        if slug not in current_slugs:
            new_businesses[slug] = business
    
    print(f"✨ New businesses to add: {len(new_businesses)}")
    
    # Display new businesses
    if new_businesses:
        print("\n🎉 NEW ACTIVE BUSINESSES FOUND:")
        for slug, business in new_businesses.items():
            business_name = business.get('business_name', business.get('page_title', 'Unknown'))
            print(f"   • {slug}: {business_name}")
    
    # Create updated database
    if new_businesses:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Convert current database to list if it's a dict
        if isinstance(current_db, dict):
            if 'all_slugs' in current_db:
                updated_db = current_db['all_slugs'].copy()
            else:
                updated_db = list(current_db.values()) if current_db else []
        else:
            updated_db = current_db.copy()
        
        for slug, business in new_businesses.items():
            # Convert to standard format
            new_entry = {
                'slug': slug,
                'status': 'ACTIVE',
                'business_name': business.get('business_name', business.get('page_title', '')),
                'tested_method': 'Browser_Automation_OtherLaptop',
                'last_tested': business.get('tested_at', '')[:10] if business.get('tested_at') else '',
                'url': business.get('url', f"https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/{slug}"),
                'redirects_to': '',
                'content_length': business.get('content_length', ''),
                'business_indicators': business.get('business_indicators', ''),
                'services': 'Weight Loss, IV Therapy, Hormone Therapy',
                'description': f"Active DRIPBaR business found via other laptop scan"
            }
            updated_db.append(new_entry)
        
        # Save updated database
        backup_filename = f"MASTER_DATABASE_backup_{timestamp}.json"
        shutil.copy("MASTER_DATABASE.json", backup_filename)
        print(f"💾 Backed up current database to: {backup_filename}")
        
        with open("MASTER_DATABASE.json", 'w', encoding='utf-8') as f:
            json.dump(updated_db, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated MASTER_DATABASE.json with {len(new_businesses)} new businesses!")
        print(f"📊 Total database size: {len(updated_db)} entries")
        
        # Also save as CSV
        csv_filename = f"MASTER_DATABASE_merged_{timestamp}.csv"
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            if updated_db:
                fieldnames = updated_db[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(updated_db)
        
        print(f"💾 Also saved as CSV: {csv_filename}")
        
    else:
        print("📊 No new businesses to add - databases are already synchronized")
    
    # Copy session logs for backup
    print("\n📁 Copying session logs from other laptop...")
    os.makedirs("logs/other_laptop_backup", exist_ok=True)
    
    other_logs = glob.glob("other_laptop/logs/*")
    copied_count = 0
    
    for log_file in other_logs:
        if os.path.isfile(log_file):
            filename = os.path.basename(log_file)
            dest_path = f"logs/other_laptop_backup/{filename}"
            shutil.copy2(log_file, dest_path)
            copied_count += 1
    
    print(f"📁 Copied {copied_count} log files to logs/other_laptop_backup/")
    
    print("\n🎯 MERGE SUMMARY:")
    print(f"   • Current database entries: {len(current_db)}")
    print(f"   • Other laptop active businesses: {len(all_other_active)}")
    print(f"   • New businesses added: {len(new_businesses)}")
    print(f"   • Final database size: {len(current_db) + len(new_businesses)}")
    
    if new_businesses:
        print(f"\n🏆 SUCCESS RATE UPDATE:")
        total_tested = len(updated_db)  # Use the final database size
        
        # Count active businesses in updated database
        total_active = 0
        for entry in updated_db:
            if isinstance(entry, dict) and entry.get('status') == 'ACTIVE':
                total_active += 1
        
        success_rate = (total_active / 60466176) * 100  # Against total possible combinations
        print(f"   • Total Active Businesses: {total_active}")
        print(f"   • Total Database Entries: {total_tested}")
        print(f"   • Success Rate vs Total Space: {success_rate:.8f}%")

def generate_comprehensive_summary():
    """Generate comprehensive summary of all active businesses"""
    
    print("\n" + "="*80)
    print("📋 GENERATING COMPREHENSIVE ACTIVE BUSINESS SUMMARY")
    print("="*80)
    
    # Load the updated database
    db = load_master_database("MASTER_DATABASE.json")
    if not db:
        print("❌ Could not load master database for summary")
        return
    
    # Filter active businesses
    active_businesses = [entry for entry in db if entry.get('status') == 'ACTIVE']
    
    print(f"🏢 TOTAL ACTIVE BUSINESSES: {len(active_businesses)}")
    print(f"📊 Total Database Entries: {len(db)}")
    
    # Group by business name pattern
    business_groups = defaultdict(list)
    for business in active_businesses:
        name = business.get('business_name', '')
        if 'DRIPBaR' in name:
            business_groups['DRIPBaR'].append(business)
        else:
            business_groups['Other'].append(business)
    
    print(f"\n📈 BUSINESS BREAKDOWN:")
    for group, businesses in business_groups.items():
        print(f"   • {group}: {len(businesses)} locations")
    
    # Create detailed summary file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_filename = f"COMPREHENSIVE_ACTIVE_BUSINESSES_SUMMARY_{timestamp}.md"
    
    with open(summary_filename, 'w', encoding='utf-8') as f:
        f.write("# VSDHOne Active Businesses - Comprehensive Summary\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Active Businesses:** {len(active_businesses)}\n")
        f.write(f"**Total Database Entries:** {len(db)}\n\n")
        
        f.write("## Active Business Directory\n\n")
        f.write("| Slug | Business Name | Services | Last Tested | Method |\n")
        f.write("|------|---------------|----------|-------------|--------|\n")
        
        # Sort by slug for consistent ordering
        sorted_businesses = sorted(active_businesses, key=lambda x: x.get('slug', ''))
        
        for business in sorted_businesses:
            slug = business.get('slug', '')
            name = business.get('business_name', '')
            services = business.get('services', 'Weight Loss, IV Therapy')
            last_tested = business.get('last_tested', '')
            method = business.get('tested_method', '')
            
            f.write(f"| {slug} | {name} | {services} | {last_tested} | {method} |\n")
        
        f.write("\n## Business Patterns\n\n")
        f.write("### DRIPBaR Locations\n")
        dripbar_businesses = [b for b in active_businesses if 'DRIPBaR' in b.get('business_name', '')]
        
        for business in sorted(dripbar_businesses, key=lambda x: x.get('business_name', '')):
            name = business.get('business_name', '')
            slug = business.get('slug', '')
            f.write(f"- **{slug}**: {name}\n")
        
        f.write("\n### Services Offered\n")
        f.write("All active businesses primarily offer:\n")
        f.write("- Weight Loss Injections (Semaglutide, Tirzepatide)\n")
        f.write("- IV Therapy and Hydration\n")
        f.write("- Hormone Replacement Therapy\n")
        f.write("- Wellness and Recovery Services\n")
        
        f.write("\n### Technical Details\n")
        f.write(f"- **Platform**: VSDHOne (Azure-hosted telehealth widget)\n")
        f.write(f"- **Base URL**: https://vsdigital-bookingwidget-prod.azurewebsites.net/widget-business/\n")
        f.write(f"- **Slug Pattern**: [a-z][a-z][0-9][0-9][a-z] (5 characters)\n")
        f.write(f"- **Total Search Space**: 60,466,176 possible combinations\n")
        
        success_rate = (len(active_businesses) / 60466176) * 100
        f.write(f"- **Current Success Rate**: {success_rate:.8f}%\n")
        
        f.write("\n### Discovery Timeline\n")
        f.write("- **Original Known Slugs**: 15 businesses\n")
        f.write("- **First Discovery Phase**: +30 businesses\n")
        f.write("- **Other Laptop Phase**: +5 businesses\n")
        f.write(f"- **Current Total**: {len(active_businesses)} businesses\n")
        
        f.write("\n### Next Steps\n")
        f.write("1. Continue systematic scanning with smart pattern-based slug generation\n")
        f.write("2. Focus on high-probability character combinations based on found patterns\n")
        f.write("3. Implement parallel scanning across multiple instances\n")
        f.write("4. Monitor for new business registrations and pattern changes\n")
    
    print(f"📄 Comprehensive summary saved to: {summary_filename}")
    
    # Also create a simple CSV export of just active businesses
    active_csv_filename = f"ACTIVE_BUSINESSES_ONLY_{timestamp}.csv"
    with open(active_csv_filename, 'w', newline='', encoding='utf-8') as f:
        if active_businesses:
            fieldnames = active_businesses[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(active_businesses)
    
    print(f"📊 Active businesses CSV saved to: {active_csv_filename}")
    
    return len(active_businesses)

if __name__ == "__main__":
    merge_databases()
    generate_comprehensive_summary() 