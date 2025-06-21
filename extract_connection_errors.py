#!/usr/bin/env python3
"""
Extract Error Slugs from Session Logs
Finds all slugs that had errors (CONNECTION_ERROR, BROWSER_ERROR, ERROR) for retry
"""

import json
import os
import glob
import argparse
from datetime import datetime

def extract_connection_error_slugs(log_files, output_file):
    """Extract slugs with errors from session log files"""
    connection_error_slugs = set()
    browser_error_slugs = set()
    other_error_slugs = set()
    
    total_logs_processed = 0
    
    for log_file in log_files:
        print(f"📖 Processing: {log_file}")
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Extract slugs with errors
            for test_result in session_data.get('testing_results', []):
                status = test_result.get('status', '')
                slug = test_result.get('slug', '')
                
                if status == 'CONNECTION_ERROR':
                    connection_error_slugs.add(slug)
                elif status == 'BROWSER_ERROR':
                    browser_error_slugs.add(slug)
                elif status == 'ERROR':
                    other_error_slugs.add(slug)
                # Also handle legacy SITE_UNAVAILABLE status
                elif status == 'SITE_UNAVAILABLE':
                    connection_error_slugs.add(slug)
            
            total_logs_processed += 1
            
        except Exception as e:
            print(f"⚠️  Error processing {log_file}: {e}")
    
    # Combine all error slugs
    all_error_slugs = connection_error_slugs.union(browser_error_slugs).union(other_error_slugs)
    
    print(f"\n📊 EXTRACTION SUMMARY:")
    print(f"📂 Session logs processed: {total_logs_processed}")
    print(f"🌐 Connection error slugs: {len(connection_error_slugs)}")
    print(f"🔧 Browser error slugs: {len(browser_error_slugs)}")
    print(f"❌ Other error slugs: {len(other_error_slugs)}")
    print(f"📝 Total slugs to retry: {len(all_error_slugs)}")
    
    if all_error_slugs:
        # Save to output file
        with open(output_file, 'w') as f:
            for slug in sorted(all_error_slugs):
                f.write(f"{slug}\n")
        
        print(f"💾 Saved retry slugs to: {output_file}")
        
        # Create summary file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = f"connection_errors_summary_{timestamp}.txt"
        
        with open(summary_file, 'w') as f:
            f.write("Error Slugs Extraction Summary\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Extraction date: {datetime.now().isoformat()}\n")
            f.write(f"Session logs processed: {total_logs_processed}\n")
            f.write(f"Connection error slugs: {len(connection_error_slugs)}\n")
            f.write(f"Browser error slugs: {len(browser_error_slugs)}\n")
            f.write(f"Other error slugs: {len(other_error_slugs)}\n")
            f.write(f"Total slugs to retry: {len(all_error_slugs)}\n")
            f.write(f"Output file: {output_file}\n\n")
            
            f.write("Processed log files:\n")
            for log_file in log_files:
                f.write(f"  {log_file}\n")
        
        print(f"📋 Summary saved to: {summary_file}")
        
        print(f"\n💡 Usage:")
        print(f"   python3 browser_comprehensive_scanner.py --file {output_file} --instance-id retry1")
        
    else:
        print(f"\n✅ No connection errors found in the processed session logs!")
    
    return len(all_error_slugs)

def main():
    parser = argparse.ArgumentParser(description='Extract Error Slugs from Session Logs')
    parser.add_argument('--logs-dir', '-d', default='logs', help='Directory containing session log files')
    parser.add_argument('--output', '-o', default='connection_errors_retry.txt', help='Output file for retry slugs')
    parser.add_argument('--pattern', '-p', default='*_session.json', help='Pattern to match session log files')
    
    args = parser.parse_args()
    
    print("🔍 Error Slug Extractor")
    print("=" * 40)
    
    # Find session log files
    if args.logs_dir and os.path.exists(args.logs_dir):
        pattern = os.path.join(args.logs_dir, args.pattern)
        log_files = glob.glob(pattern)
    else:
        # Also check current directory
        log_files = glob.glob(args.pattern)
    
    if not log_files:
        print(f"❌ No session log files found matching pattern: {args.pattern}")
        print(f"📂 Searched in: {args.logs_dir if args.logs_dir else 'current directory'}")
        return
    
    print(f"📂 Found {len(log_files)} session log files:")
    for log_file in log_files:
        print(f"  • {log_file}")
    print("")
    
    # Extract connection error slugs
    error_count = extract_connection_error_slugs(log_files, args.output)
    
    if error_count > 0:
        print(f"\n🎯 Ready to retry {error_count} slugs with connection issues!")
    else:
        print(f"\n✅ All slugs were tested successfully - no connection issues found!")

if __name__ == "__main__":
    main() 