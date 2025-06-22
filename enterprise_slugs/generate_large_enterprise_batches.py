#!/usr/bin/env python3
"""
Large Enterprise Slug Generator for VSDHOne
Generates 5 large batches of ~10,300 enterprise slugs each for 10-hour scanning sessions
Ensures no duplicates from existing batches
"""

import base64
import random
import json
import os
from datetime import datetime
from typing import Set, List, Dict, Any
import glob

class LargeEnterpriseSlugGenerator:
    def __init__(self):
        self.working_samples = {
            'NzEw': 710,  # RenIVate
            'NDI2': 426,  # Oh My Olivia  
            'NzEy': 712   # Valor Wellness
        }
        
        # Load existing slugs to avoid duplicates
        self.existing_slugs = self.load_existing_slugs()
        
        # Excluded prefixes (tested on other laptop)
        self.excluded_prefixes = ['Nz']
        
        # Target slugs per batch for ~10 hours scanning
        self.target_per_batch = 10300
        self.batch_count = 5
        
        print(f"🔍 Loaded {len(self.existing_slugs)} existing slugs to avoid duplicates")
        
    def load_existing_slugs(self) -> Set[str]:
        """Load all existing slugs from previous batches"""
        existing_slugs = set()
        
        # Load from existing batch files
        batch_files = glob.glob("enterprise_batch_*.txt")
        for batch_file in batch_files:
            try:
                with open(batch_file, 'r') as f:
                    slugs = [line.strip() for line in f if line.strip()]
                    existing_slugs.update(slugs)
                    print(f"📁 Loaded {len(slugs)} slugs from {batch_file}")
            except Exception as e:
                print(f"⚠️  Error loading {batch_file}: {e}")
        
        return existing_slugs
    
    def encode_number(self, num: int) -> str:
        """Convert number to base64 encoded slug"""
        return base64.b64encode(str(num).encode()).decode().rstrip('=')
    
    def is_valid_slug(self, slug: str) -> bool:
        """Check if slug is valid (not excluded and not duplicate)"""
        if slug in self.existing_slugs:
            return False
            
        for prefix in self.excluded_prefixes:
            if slug.startswith(prefix):
                return False
                
        return True
    
    def generate_around_working_samples(self, radius: int = 5000) -> List[str]:
        """Generate slugs around working samples with large radius"""
        slugs = []
        
        for sample_slug, sample_num in self.working_samples.items():
            # Generate around each working sample
            start = max(1, sample_num - radius)
            end = sample_num + radius + 1
            
            for num in range(start, end):
                slug = self.encode_number(num)
                if self.is_valid_slug(slug):
                    slugs.append(slug)
        
        return slugs
    
    def generate_sequential_ranges(self) -> List[str]:
        """Generate slugs from various sequential number ranges"""
        slugs = []
        
        # Define ranges for comprehensive coverage
        ranges = [
            (1, 2000),           # Small numbers
            (2000, 5000),        # Medium-small numbers  
            (5000, 10000),       # Medium numbers
            (10000, 25000),      # Large numbers
            (25000, 50000),      # Very large numbers
            (50000, 100000),     # Huge numbers
            (100000, 250000),    # Massive numbers
            (250000, 500000),    # Ultra numbers
            (500000, 750000),    # Mega numbers
            (750000, 999999),    # Maximum 6-digit numbers
        ]
        
        for start, end in ranges:
            # Sample from each range (not all numbers to avoid too many slugs)
            sample_size = min(2000, (end - start) // 10)  # Sample 10% or max 2000
            sampled_numbers = random.sample(range(start, end + 1), sample_size)
            
            for num in sampled_numbers:
                slug = self.encode_number(num)
                if self.is_valid_slug(slug):
                    slugs.append(slug)
        
        return slugs
    
    def generate_random_patterns(self) -> List[str]:
        """Generate random number patterns for diversity"""
        slugs = []
        
        # Generate various random patterns
        patterns = [
            # 7-digit numbers
            lambda: random.randint(1000000, 9999999),
            # 8-digit numbers  
            lambda: random.randint(10000000, 99999999),
            # 9-digit numbers
            lambda: random.randint(100000000, 999999999),
            # Powers of 2 nearby
            lambda: 2**random.randint(10, 25) + random.randint(-100, 100),
            # Powers of 10 nearby
            lambda: 10**random.randint(3, 8) + random.randint(-1000, 1000),
            # Fibonacci-like sequences
            lambda: random.randint(1, 1000) * random.randint(1, 1000),
        ]
        
        for pattern_func in patterns:
            for _ in range(3000):  # Generate 3000 from each pattern
                try:
                    num = pattern_func()
                    if num > 0:  # Ensure positive
                        slug = self.encode_number(num)
                        if self.is_valid_slug(slug):
                            slugs.append(slug)
                except:
                    continue  # Skip invalid numbers
        
        return slugs
    
    def generate_special_patterns(self) -> List[str]:
        """Generate special mathematical patterns"""
        slugs = []
        
        # Prime-like patterns
        for base in [11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]:
            for multiplier in range(1, 1000):
                num = base * multiplier
                slug = self.encode_number(num)
                if self.is_valid_slug(slug):
                    slugs.append(slug)
        
        # Date-based patterns (YYYYMMDD, MMDDYYYY, etc.)
        for year in range(2020, 2030):
            for month in range(1, 13):
                for day in [1, 15, 30]:  # Sample days
                    patterns = [
                        int(f"{year}{month:02d}{day:02d}"),      # YYYYMMDD
                        int(f"{month:02d}{day:02d}{year}"),      # MMDDYYYY
                        int(f"{day:02d}{month:02d}{year}"),      # DDMMYYYY
                    ]
                    
                    for num in patterns:
                        slug = self.encode_number(num)
                        if self.is_valid_slug(slug):
                            slugs.append(slug)
        
        return slugs
    
    def generate_batch(self, batch_number: int) -> List[str]:
        """Generate a single batch of slugs"""
        print(f"\n🎯 Generating batch {batch_number}...")
        
        all_candidates = []
        
        # Strategy 1: Around working samples (large radius)
        print("  📍 Generating around working samples...")
        around_samples = self.generate_around_working_samples(radius=5000)
        all_candidates.extend(around_samples)
        print(f"     Generated {len(around_samples)} candidates")
        
        # Strategy 2: Sequential ranges
        print("  📊 Generating sequential ranges...")
        sequential = self.generate_sequential_ranges()
        all_candidates.extend(sequential)
        print(f"     Generated {len(sequential)} candidates")
        
        # Strategy 3: Random patterns
        print("  🎲 Generating random patterns...")
        random_patterns = self.generate_random_patterns()
        all_candidates.extend(random_patterns)
        print(f"     Generated {len(random_patterns)} candidates")
        
        # Strategy 4: Special patterns
        print("  ✨ Generating special patterns...")
        special_patterns = self.generate_special_patterns()
        all_candidates.extend(special_patterns)
        print(f"     Generated {len(special_patterns)} candidates")
        
        # Remove duplicates and shuffle
        unique_candidates = list(set(all_candidates))
        random.shuffle(unique_candidates)
        
        print(f"  🔄 Total unique candidates: {len(unique_candidates)}")
        
        # Take target amount
        batch_slugs = unique_candidates[:self.target_per_batch]
        
        # Add these to existing slugs to avoid future duplicates
        self.existing_slugs.update(batch_slugs)
        
        print(f"  ✅ Selected {len(batch_slugs)} slugs for batch {batch_number}")
        
        return batch_slugs
    
    def save_batch(self, slugs: List[str], batch_number: int, timestamp: str) -> str:
        """Save a batch to file"""
        filename = f"enterprise_large_batch_{batch_number}_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            for slug in slugs:
                f.write(f"{slug}\n")
        
        print(f"💾 Saved {len(slugs)} slugs to {filename}")
        return filename
    
    def generate_all_batches(self) -> Dict[str, Any]:
        """Generate all large batches"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"🚀 Starting large enterprise batch generation...")
        print(f"📊 Target: {self.batch_count} batches of ~{self.target_per_batch} slugs each")
        print(f"⏱️  Estimated scanning time per batch: ~10 hours")
        print(f"🚫 Avoiding {len(self.existing_slugs)} existing slugs")
        
        batch_files = []
        total_slugs = 0
        generation_stats = {
            'total_batches': self.batch_count,
            'target_per_batch': self.target_per_batch,
            'actual_slugs_per_batch': [],
            'batch_files': [],
            'generation_timestamp': timestamp,
            'existing_slugs_avoided': len(self.existing_slugs)
        }
        
        for batch_num in range(1, self.batch_count + 1):
            batch_slugs = self.generate_batch(batch_num)
            filename = self.save_batch(batch_slugs, batch_num, timestamp)
            
            batch_files.append(filename)
            total_slugs += len(batch_slugs)
            generation_stats['actual_slugs_per_batch'].append(len(batch_slugs))
            generation_stats['batch_files'].append(filename)
        
        generation_stats['total_slugs_generated'] = total_slugs
        generation_stats['average_per_batch'] = total_slugs / self.batch_count
        
        # Save generation summary
        summary_file = f"LARGE_ENTERPRISE_GENERATION_SUMMARY_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(generation_stats, f, indent=2)
        
        print(f"\n🎉 Generation Complete!")
        print(f"📈 Total slugs generated: {total_slugs:,}")
        print(f"📊 Average per batch: {generation_stats['average_per_batch']:.0f}")
        print(f"⏱️  Total estimated scanning time: ~{self.batch_count * 10} hours")
        print(f"📋 Summary saved to: {summary_file}")
        
        return generation_stats

def main():
    """Main execution function"""
    print("🏢 Large Enterprise Slug Generator for VSDHOne")
    print("=" * 60)
    
    generator = LargeEnterpriseSlugGenerator()
    
    # Confirm generation
    print(f"\nReady to generate {generator.batch_count} large batches")
    print(f"Each batch will contain ~{generator.target_per_batch:,} slugs")
    print(f"Total estimated slugs: ~{generator.batch_count * generator.target_per_batch:,}")
    print(f"Total estimated scanning time: ~{generator.batch_count * 10} hours")
    
    response = input("\nProceed with generation? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Generation cancelled")
        return
    
    # Generate all batches
    stats = generator.generate_all_batches()
    
    print(f"\n📁 Generated files:")
    for filename in stats['batch_files']:
        print(f"   • {filename}")
    
    print(f"\n🎯 Ready for enterprise scanning!")
    print(f"💡 Use enterprise_level_scanner.py with these batch files")

if __name__ == "__main__":
    main() 