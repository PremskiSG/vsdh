#!/usr/bin/env python3
"""
Focused Enterprise Slug Generator for VSDHOne
Generates focused batches covering 3-digit and 4-digit numbers systematically
Based on working samples: 426, 710, 712 (all 3-digit numbers)
FRESH GENERATION - ignores previous batches
"""

import base64
import json
import os
from datetime import datetime
from typing import Set, List, Dict, Any
import glob
import math

class FocusedEnterpriseSlugGenerator:
    def __init__(self):
        self.working_samples = {
            'NzEw': 710,  # RenIVate
            'NDI2': 426,  # Oh My Olivia  
            'NzEy': 712   # Valor Wellness
        }
        
        # Excluded prefixes (tested on other laptop)
        self.excluded_prefixes = ['Nz']
        
        print(f"🎯 Working samples are all 3-digit numbers: {list(self.working_samples.values())}")
        print(f"🔥 FRESH GENERATION - ignoring previous batches for complete coverage")
        
    def encode_number(self, num: int) -> str:
        """Convert number to base64 encoded slug"""
        return base64.b64encode(str(num).encode()).decode().rstrip('=')
    
    def decode_slug(self, slug: str) -> int:
        """Convert base64 slug back to number (for verification)"""
        padded = slug + '=' * (4 - len(slug) % 4) if len(slug) % 4 else slug
        return int(base64.b64decode(padded).decode())
    
    def is_valid_slug(self, slug: str) -> bool:
        """Check if slug is valid (only check excluded prefixes, ignore duplicates)"""
        for prefix in self.excluded_prefixes:
            if slug.startswith(prefix):
                return False
        return True
    
    def generate_3_digit_batches(self) -> List[List[str]]:
        """Generate 3 batches covering ALL 3-digit numbers (100-999)"""
        print("🎯 Generating 3-digit number batches (100-999)...")
        
        # All 3-digit numbers: 100-999 = 900 numbers total
        all_3_digit_numbers = list(range(100, 1000))
        
        # Split into 3 equal batches
        batch_size = len(all_3_digit_numbers) // 3
        batches = []
        
        for i in range(3):
            start_idx = i * batch_size
            if i == 2:  # Last batch gets any remainder
                end_idx = len(all_3_digit_numbers)
            else:
                end_idx = (i + 1) * batch_size
            
            batch_numbers = all_3_digit_numbers[start_idx:end_idx]
            batch_slugs = []
            
            for num in batch_numbers:
                slug = self.encode_number(num)
                if self.is_valid_slug(slug):
                    batch_slugs.append(slug)
            
            batches.append(batch_slugs)
            print(f"  📦 3-digit batch {i+1}: {len(batch_slugs)} slugs (numbers {batch_numbers[0]}-{batch_numbers[-1]})")
        
        return batches
    
    def generate_4_digit_batches(self) -> List[List[str]]:
        """Generate 3 batches covering ALL 4-digit numbers (1000-9999)"""
        print("🎯 Generating 4-digit number batches (1000-9999)...")
        
        # 4-digit numbers: 1000-9999 = 9000 numbers total
        # Split into 3 strategic batches
        
        batch_ranges = [
            (1000, 3999),  # Lower 4-digit: 1000-3999 (3000 numbers)
            (4000, 6999),  # Middle 4-digit: 4000-6999 (3000 numbers)  
            (7000, 9999),  # Upper 4-digit: 7000-9999 (3000 numbers)
        ]
        
        batches = []
        
        for i, (start, end) in enumerate(batch_ranges):
            batch_numbers = list(range(start, end + 1))
            batch_slugs = []
            
            for num in batch_numbers:
                slug = self.encode_number(num)
                if self.is_valid_slug(slug):
                    batch_slugs.append(slug)
            
            batches.append(batch_slugs)
            print(f"  📦 4-digit batch {i+1}: {len(batch_slugs)} slugs (numbers {start}-{end})")
        
        return batches
    
    def save_batch(self, slugs: List[str], batch_type: str, batch_number: int, timestamp: str) -> str:
        """Save a batch to file"""
        filename = f"enterprise_{batch_type}_batch_{batch_number}_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            for slug in slugs:
                f.write(f"{slug}\n")
        
        print(f"💾 Saved {len(slugs)} slugs to {filename}")
        return filename
    
    def verify_samples(self):
        """Verify our working samples decode correctly"""
        print("🔍 Verifying working samples:")
        for slug, expected_num in self.working_samples.items():
            decoded = self.decode_slug(slug)
            status = "✅" if decoded == expected_num else "❌"
            print(f"  {status} {slug} → {decoded} (expected {expected_num})")
    
    def show_sample_slugs(self, batches_3digit, batches_4digit):
        """Show sample slugs from each batch"""
        print("🔍 Sample slugs from each batch:")
        
        for i, batch in enumerate(batches_3digit, 1):
            if batch:
                sample_slugs = batch[:5]  # First 5 slugs
                sample_numbers = [self.decode_slug(slug) for slug in sample_slugs]
                print(f"  3-digit batch {i}: {sample_slugs} → {sample_numbers}")
        
        for i, batch in enumerate(batches_4digit, 1):
            if batch:
                sample_slugs = batch[:5]  # First 5 slugs
                sample_numbers = [self.decode_slug(slug) for slug in sample_slugs]
                print(f"  4-digit batch {i}: {sample_slugs} → {sample_numbers}")
    
    def generate_all_focused_batches(self) -> Dict[str, Any]:
        """Generate all focused batches"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"🚀 Starting FRESH focused enterprise batch generation...")
        print(f"📊 Plan: 3 batches for 3-digit numbers + 3 batches for 4-digit numbers")
        print(f"🔥 Complete coverage: 100-999 (3-digit) + 1000-9999 (4-digit)")
        print()
        
        # Verify working samples first
        self.verify_samples()
        print()
        
        all_batch_files = []
        total_slugs = 0
        generation_stats = {
            'generation_timestamp': timestamp,
            'fresh_generation': True,
            'excluded_prefixes': self.excluded_prefixes,
            'batches': []
        }
        
        # Generate 3-digit batches
        digit3_batches = self.generate_3_digit_batches()
        for i, batch_slugs in enumerate(digit3_batches, 1):
            filename = self.save_batch(batch_slugs, "3digit", i, timestamp)
            all_batch_files.append(filename)
            total_slugs += len(batch_slugs)
            
            generation_stats['batches'].append({
                'type': '3-digit',
                'batch_number': i,
                'filename': filename,
                'slug_count': len(batch_slugs),
                'number_range': f"{self.decode_slug(batch_slugs[0])}-{self.decode_slug(batch_slugs[-1])}" if batch_slugs else "empty"
            })
        
        print()
        
        # Generate 4-digit batches  
        digit4_batches = self.generate_4_digit_batches()
        for i, batch_slugs in enumerate(digit4_batches, 1):
            filename = self.save_batch(batch_slugs, "4digit", i, timestamp)
            all_batch_files.append(filename)
            total_slugs += len(batch_slugs)
            
            generation_stats['batches'].append({
                'type': '4-digit',
                'batch_number': i,
                'filename': filename,
                'slug_count': len(batch_slugs),
                'number_range': f"{self.decode_slug(batch_slugs[0])}-{self.decode_slug(batch_slugs[-1])}" if batch_slugs else "empty"
            })
        
        print()
        self.show_sample_slugs(digit3_batches, digit4_batches)
        
        generation_stats['total_batches'] = len(all_batch_files)
        generation_stats['total_slugs_generated'] = total_slugs
        generation_stats['batch_files'] = all_batch_files
        
        # Save generation summary
        summary_file = f"FOCUSED_ENTERPRISE_GENERATION_SUMMARY_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(generation_stats, f, indent=2)
        
        print(f"\n🎉 Fresh Focused Generation Complete!")
        print(f"📈 Total slugs generated: {total_slugs:,}")
        print(f"📊 3-digit coverage: COMPLETE (100-999)")
        print(f"📊 4-digit coverage: COMPLETE (1000-9999)")
        print(f"🚫 Excluded Nz* prefixes: {len([s for batch in digit3_batches + digit4_batches for s in batch if any(s.startswith(p) for p in self.excluded_prefixes)])}")
        print(f"📋 Summary saved to: {summary_file}")
        
        return generation_stats

def main():
    """Main execution function"""
    print("🏢 Focused Enterprise Slug Generator for VSDHOne")
    print("=" * 60)
    print("🎯 Focus: COMPLETE 3-digit and 4-digit number coverage")
    print("🔥 FRESH generation - ignoring previous batches")
    print()
    
    generator = FocusedEnterpriseSlugGenerator()
    
    # Show the plan
    print("📋 Generation Plan:")
    print("  • 3-digit numbers (100-999): 3 batches, ~300 slugs each = ~900 total")
    print("  • 4-digit numbers (1000-9999): 3 batches, ~3000 slugs each = ~9000 total")
    print("  • Total estimated: ~9,900 focused slugs")
    print("  • Excludes only Nz* prefixes (tested on other laptop)")
    print()
    
    response = input("Proceed with FRESH focused generation? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Generation cancelled")
        return
    
    # Generate all batches
    stats = generator.generate_all_focused_batches()
    
    print(f"\n📁 Generated files:")
    for batch in stats['batches']:
        print(f"   • {batch['filename']} ({batch['slug_count']} slugs, {batch['type']}, range: {batch['number_range']})")
    
    print(f"\n🎯 Ready for focused enterprise scanning!")
    print(f"💡 Use enterprise_level_scanner.py with these batch files")
    print(f"🔥 Complete coverage of realistic number ranges!")

if __name__ == "__main__":
    main() 