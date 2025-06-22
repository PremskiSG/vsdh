#!/usr/bin/env python3
"""
2-Digit Enterprise Slug Generator for VSDHOne
Generates one batch covering all 2-digit numbers (10-99)
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

def generate_2digit_batch():
    """Generate one batch covering ALL 2-digit numbers (10-99)"""
    print("🎯 Generating 2-digit number batch (10-99)...")
    
    # All 2-digit numbers: 10-99 = 90 numbers total
    all_2_digit_numbers = list(range(10, 100))
    batch_slugs = []
    
    excluded_prefixes = ['Nz']  # Same exclusion as other batches
    
    for num in all_2_digit_numbers:
        slug = encode_number(num)
        # Check if slug is valid (not excluded)
        valid = True
        for prefix in excluded_prefixes:
            if slug.startswith(prefix):
                valid = False
                break
        
        if valid:
            batch_slugs.append(slug)
    
    print(f"  📦 2-digit batch: {len(batch_slugs)} slugs (numbers 10-99)")
    return batch_slugs

def save_batch(slugs, timestamp):
    """Save the batch to file"""
    filename = f"enterprise_2digit_batch_1_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        for slug in slugs:
            f.write(f"{slug}\n")
    
    print(f"💾 Saved {len(slugs)} slugs to {filename}")
    return filename

def main():
    print("🏢 2-Digit Enterprise Slug Generator for VSDHOne")
    print("=" * 60)
    print("🎯 Focus: Complete 2-digit number coverage (10-99)")
    print()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate 2-digit batch
    batch_slugs = generate_2digit_batch()
    
    # Show samples
    print("\n🔍 Sample slugs:")
    for i in range(min(10, len(batch_slugs))):
        slug = batch_slugs[i]
        num = decode_slug(slug)
        print(f"  {slug} → {num}")
    
    # Save batch
    filename = save_batch(batch_slugs, timestamp)
    
    # Create summary
    summary = {
        'generation_timestamp': timestamp,
        'type': '2-digit',
        'slug_count': len(batch_slugs),
        'number_range': '10-99',
        'filename': filename,
        'excluded_prefixes': ['Nz'],
        'sample_slugs': batch_slugs[:5]
    }
    
    summary_file = f"2DIGIT_ENTERPRISE_SUMMARY_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n🎉 2-Digit Generation Complete!")
    print(f"📈 Total slugs generated: {len(batch_slugs)}")
    print(f"📊 Coverage: COMPLETE (10-99)")
    print(f"📁 File: {filename}")
    print(f"📋 Summary: {summary_file}")
    print(f"\n⚡ Estimated scanning time: ~5 minutes (FASTEST!)")
    print(f"💡 Use: python3 ../enterprise_level_scanner.py {filename}")

if __name__ == "__main__":
    main()
