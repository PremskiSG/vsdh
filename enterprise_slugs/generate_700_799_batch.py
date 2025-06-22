#!/usr/bin/env python3
"""
700-799 Enterprise Slug Generator for VSDHOne
Generates one batch covering the 700-799 range that was tested on the other laptop
This completes the 3-digit coverage that was missing from the focused batches
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

def generate_700_799_batch():
    """Generate one batch covering ALL numbers 700-799"""
    print("🎯 Generating 700-799 number batch (MISSING RANGE)...")
    print("🔍 Note: This range was tested on other laptop but missing from current batches")
    
    # All 700-799 numbers: 700-799 = 100 numbers total
    all_700_799_numbers = list(range(700, 800))
    batch_slugs = []
    excluded_count = 0
    
    # Note: We're including ALL slugs, even Nz* ones, since this laptop needs to test them
    # The "other laptop" testing was incomplete or we need verification
    
    for num in all_700_799_numbers:
        slug = encode_number(num)
        batch_slugs.append(slug)
        
        # Count how many would be excluded by Nz filter (for info only)
        if slug.startswith('Nz'):
            excluded_count += 1
    
    print(f"  📦 700-799 batch: {len(batch_slugs)} slugs (numbers 700-799)")
    print(f"  🔍 Nz* prefixed slugs included: {excluded_count} (previously excluded)")
    print(f"  ✅ Known working samples in this range: NzEw (710), NzEy (712)")
    
    return batch_slugs

def save_batch(slugs, timestamp):
    """Save the batch to file"""
    filename = f"enterprise_700_799_batch_1_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        for slug in slugs:
            f.write(f"{slug}\n")
    
    print(f"💾 Saved {len(slugs)} slugs to {filename}")
    return filename

def verify_known_samples():
    """Verify the known working samples in this range"""
    known_samples = {
        'NzEw': 710,  # RenIVate
        'NzEy': 712   # Valor Wellness
    }
    
    print("🔍 Verifying known working samples in 700-799 range:")
    for slug, expected_num in known_samples.items():
        decoded = decode_slug(slug)
        status = "✅" if decoded == expected_num else "❌"
        print(f"  {status} {slug} → {decoded} (expected {expected_num})")

def main():
    print("🏢 700-799 Enterprise Slug Generator for VSDHOne")
    print("=" * 60)
    print("🎯 Focus: Complete the MISSING 700-799 range")
    print("🔍 This range was excluded from focused batches due to Nz* filter")
    print("🔥 Includes ALL 700-799 numbers for complete coverage")
    print()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Verify known samples first
    verify_known_samples()
    print()
    
    # Generate 700-799 batch
    batch_slugs = generate_700_799_batch()
    
    # Show samples
    print("\n🔍 Sample slugs from 700-799 range:")
    sample_indices = [0, 10, 20, 50, 90, 99]  # Show spread across range
    for i in sample_indices:
        if i < len(batch_slugs):
            slug = batch_slugs[i]
            num = decode_slug(slug)
            prefix_note = " (Nz* prefix)" if slug.startswith('Nz') else ""
            print(f"  {slug} → {num}{prefix_note}")
    
    # Save batch
    filename = save_batch(batch_slugs, timestamp)
    
    # Create summary
    nz_count = sum(1 for slug in batch_slugs if slug.startswith('Nz'))
    summary = {
        'generation_timestamp': timestamp,
        'type': '700-799',
        'slug_count': len(batch_slugs),
        'number_range': '700-799',
        'filename': filename,
        'nz_prefixed_count': nz_count,
        'non_nz_count': len(batch_slugs) - nz_count,
        'known_working_samples': ['NzEw (710)', 'NzEy (712)'],
        'note': 'This range was missing from focused batches due to Nz* exclusion',
        'sample_slugs': batch_slugs[:5]
    }
    
    summary_file = f"700_799_ENTERPRISE_SUMMARY_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n🎉 700-799 Generation Complete!")
    print(f"📈 Total slugs generated: {len(batch_slugs)}")
    print(f"📊 Coverage: COMPLETE (700-799)")
    print(f"🔍 Nz* prefixed slugs: {nz_count}")
    print(f"🔍 Other prefixed slugs: {len(batch_slugs) - nz_count}")
    print(f"📁 File: {filename}")
    print(f"📋 Summary: {summary_file}")
    print(f"\n⚡ Estimated scanning time: ~6 minutes")
    print(f"💡 Use: python3 ../enterprise_level_scanner.py {filename}")
    print(f"\n🎯 This completes the 3-digit coverage: 100-399, 400-699, 700-799, 800-999")

if __name__ == "__main__":
    main() 