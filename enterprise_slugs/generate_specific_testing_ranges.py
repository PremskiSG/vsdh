#!/usr/bin/env python3
"""
Specific Testing Ranges Enterprise Slug Generator for VSDHOne
Generates slugs for specific number ranges requested for testing:
- 371 to 400 (30 numbers)
- 493 to 545 (53 numbers)  
- 583 to 636 (54 numbers)
- 643 to 698 (56 numbers)
Total: 193 slugs for focused testing
"""

import base64
import json
from datetime import datetime

def encode_number(num: int) -> str:
    """Convert number to base64 encoded slug"""
    return base64.b64encode(str(num).encode()).decode().rstrip('=')

def decode_slug(slug: str) -> int:
    """Convert base64 slug back to number (for verification)"""
    padded = slug + '=' * (4 - len(slug) % 4) if len(slug) % 4 else slug
    return int(base64.b64decode(padded).decode())

def generate_specific_testing_ranges():
    """Generate slugs for specific testing ranges"""
    print("🎯 Generating specific testing ranges...")
    
    # Define the specific ranges
    ranges = [
        (371, 400, "371-400"),
        (493, 545, "493-545"),
        (583, 636, "583-636"), 
        (643, 698, "643-698")
    ]
    
    all_batch_slugs = []
    range_details = []
    
    for start, end, range_name in ranges:
        range_numbers = list(range(start, end + 1))
        range_slugs = []
        
        for num in range_numbers:
            slug = encode_number(num)
            range_slugs.append(slug)
            all_batch_slugs.append(slug)
        
        range_details.append({
            'range': range_name,
            'start': start,
            'end': end,
            'count': len(range_slugs),
            'sample_slugs': range_slugs[:3]  # First 3 as samples
        })
        
        print(f"  📦 Range {range_name}: {len(range_slugs)} slugs")
    
    print(f"\n📊 Total slugs generated: {len(all_batch_slugs)}")
    return all_batch_slugs, range_details

def save_batch(slugs, timestamp):
    """Save the batch to file"""
    filename = f"enterprise_specific_testing_ranges_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        for slug in slugs:
            f.write(f"{slug}\n")
    
    print(f"💾 Saved {len(slugs)} slugs to {filename}")
    return filename

def verify_sample_slugs(range_details):
    """Verify sample slugs from each range"""
    print("🔍 Verifying sample slugs from each range:")
    
    for range_info in range_details:
        print(f"\n  📋 Range {range_info['range']}:")
        for slug in range_info['sample_slugs']:
            decoded = decode_slug(slug)
            print(f"    {slug} → {decoded}")

def main():
    print("🏢 Specific Testing Ranges Enterprise Slug Generator for VSDHOne")
    print("=" * 70)
    print("🎯 Focus: Generate slugs for specific number ranges")
    print("🔍 Ranges: 371-400, 493-545, 583-636, 643-698")
    print("📊 Total expected: 193 slugs")
    print()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate specific testing ranges
    batch_slugs, range_details = generate_specific_testing_ranges()
    
    # Verify samples
    verify_sample_slugs(range_details)
    
    # Show detailed breakdown
    print(f"\n🔍 Detailed breakdown:")
    total_expected = 0
    for range_info in range_details:
        expected_count = range_info['end'] - range_info['start'] + 1
        actual_count = range_info['count']
        total_expected += expected_count
        print(f"  {range_info['range']}: {actual_count}/{expected_count} slugs")
    
    print(f"\n📊 Total: {len(batch_slugs)}/{total_expected} slugs")
    
    # Save batch
    filename = save_batch(batch_slugs, timestamp)
    
    # Create summary
    summary = {
        'generation_timestamp': timestamp,
        'type': 'specific-testing-ranges',
        'slug_count': len(batch_slugs),
        'filename': filename,
        'ranges': range_details,
        'total_expected': total_expected,
        'note': 'Generated for specific testing ranges: 371-400, 493-545, 583-636, 643-698'
    }
    
    summary_file = f"SPECIFIC_TESTING_RANGES_SUMMARY_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n🎉 Specific Testing Ranges Generation Complete!")
    print(f"📈 Total slugs generated: {len(batch_slugs)}")
    print(f"📊 Coverage: {len(batch_slugs)}/{total_expected} expected slugs")
    print(f"📁 File: {filename}")
    print(f"📋 Summary: {summary_file}")
    print(f"\n⚡ Estimated scanning time: ~11 minutes (193 slugs × 3.5s each)")
    print(f"💡 Use: python3 ../enterprise_level_scanner_fixed.py {filename}")
    print(f"\n🎯 These ranges are for investigating the 'Akshay Health Center' mystery")

if __name__ == "__main__":
    main()
