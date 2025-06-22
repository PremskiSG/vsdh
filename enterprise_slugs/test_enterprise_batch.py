#!/usr/bin/env python3
"""
Enterprise Batch Tester
Quick tester for generated enterprise slug batches
"""

import sys
import os
sys.path.append('..')  # Add parent directory to import enterprise scanner

from enterprise_level_scanner import EnterpriseScanner
import argparse

def load_batch_file(filename):
    """Load slugs from a batch file"""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def test_enterprise_batch(batch_file, max_slugs=None):
    """Test a batch of enterprise slugs"""
    print(f"🧪 Testing Enterprise Batch: {batch_file}")
    print("=" * 50)
    
    # Load slugs
    slugs = load_batch_file(batch_file)
    if max_slugs:
        slugs = slugs[:max_slugs]
        print(f"📊 Testing first {max_slugs} slugs from batch")
    else:
        print(f"📊 Testing all {len(slugs)} slugs from batch")
    
    # Initialize scanner
    scanner = EnterpriseScanner(f"BATCH_TEST_{batch_file.split('_')[2]}")
    
    if not scanner.setup_driver():
        print("❌ Failed to setup driver")
        return
    
    try:
        results = scanner.scan_slugs(slugs)
        
        # Print summary
        stats = scanner.session_data['stats']
        print()
        print("📈 BATCH TEST RESULTS")
        print("=" * 50)
        print(f"✅ Active businesses found: {stats['active_found']}")
        print(f"❌ Errors/Invalid: {stats['errors']}")
        print(f"📊 Total tested: {stats['total_tested']}")
        if stats['total_tested'] > 0:
            print(f"🎯 Success rate: {(stats['active_found']/stats['total_tested']*100):.2f}%")
        
        # Save results
        scanner.save_session_data()
        
    finally:
        scanner.driver.quit()

def main():
    parser = argparse.ArgumentParser(description='Test enterprise slug batches')
    parser.add_argument('batch_file', help='Batch file to test')
    parser.add_argument('--max-slugs', type=int, help='Maximum number of slugs to test')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.batch_file):
        print(f"❌ Batch file not found: {args.batch_file}")
        return
    
    test_enterprise_batch(args.batch_file, args.max_slugs)

if __name__ == "__main__":
    main() 