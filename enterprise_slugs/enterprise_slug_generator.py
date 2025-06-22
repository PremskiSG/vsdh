#!/usr/bin/env python3
"""
Enterprise Slug Generator for VSDHOne
Generates base64-encoded slugs for enterprise booking URLs (/b/ format)

Based on analysis:
- Working samples: NzEw (710), NDI2 (426), NzEy (712)
- Pattern: Base64 encoded numbers
- Strategy: Generate various number ranges and encode them
"""

import base64
import random
import string
from datetime import datetime
import json

class EnterpriseSlugGenerator:
    def __init__(self):
        self.working_samples = {
            'NzEw': '710',  # Known working
            'NDI2': '426',  # Known working  
            'NzEy': '712'   # Known working
        }
        
        # Exclude patterns (tested on another laptop)
        self.exclude_prefixes = ['Nz']  # Exclude Nz* patterns
        
        self.generated_slugs = set()
        self.generation_stats = {
            'total_generated': 0,
            'excluded_count': 0,
            'strategies_used': {}
        }
    
    def encode_number_to_slug(self, number):
        """Convert a number to base64 slug"""
        number_str = str(number)
        encoded = base64.b64encode(number_str.encode('utf-8')).decode('utf-8')
        # Remove padding characters for cleaner slugs
        return encoded.rstrip('=')
    
    def decode_slug_to_number(self, slug):
        """Decode a base64 slug back to number (for verification)"""
        try:
            # Add padding if needed
            padded_slug = slug + '=' * (4 - len(slug) % 4) if len(slug) % 4 else slug
            decoded = base64.b64decode(padded_slug).decode('utf-8')
            return int(decoded) if decoded.isdigit() else None
        except:
            return None
    
    def is_valid_slug(self, slug):
        """Check if slug should be excluded"""
        # Exclude Nz prefixed slugs (tested elsewhere)
        for prefix in self.exclude_prefixes:
            if slug.startswith(prefix):
                self.generation_stats['excluded_count'] += 1
                return False
        return True
    
    def generate_sequential_range(self, start, end, step=1):
        """Generate slugs from sequential number range"""
        strategy = f"sequential_{start}_{end}_{step}"
        slugs = []
        
        for num in range(start, end + 1, step):
            slug = self.encode_number_to_slug(num)
            if self.is_valid_slug(slug) and slug not in self.generated_slugs:
                slugs.append(slug)
                self.generated_slugs.add(slug)
        
        self.generation_stats['strategies_used'][strategy] = len(slugs)
        return slugs
    
    def generate_around_working_samples(self, radius=50):
        """Generate slugs around known working numbers"""
        strategy = "around_working_samples"
        slugs = []
        
        working_numbers = [int(num) for num in self.working_samples.values()]
        
        for base_num in working_numbers:
            # Generate numbers around each working sample
            for offset in range(-radius, radius + 1):
                if offset == 0:  # Skip the exact working number
                    continue
                    
                test_num = base_num + offset
                if test_num > 0:  # Only positive numbers
                    slug = self.encode_number_to_slug(test_num)
                    if self.is_valid_slug(slug) and slug not in self.generated_slugs:
                        slugs.append(slug)
                        self.generated_slugs.add(slug)
        
        self.generation_stats['strategies_used'][strategy] = len(slugs)
        return slugs
    
    def generate_common_patterns(self):
        """Generate slugs from common number patterns"""
        strategy = "common_patterns"
        slugs = []
        
        # Common ID patterns
        patterns = [
            # Round numbers
            list(range(100, 1000, 100)),  # 100, 200, 300...
            list(range(1000, 10000, 1000)),  # 1000, 2000, 3000...
            
            # Sequential ranges
            list(range(1, 100)),      # 1-99
            list(range(100, 200)),    # 100-199
            list(range(200, 300)),    # 200-299
            list(range(300, 500)),    # 300-499
            list(range(500, 800)),    # 500-799
            list(range(800, 1000)),   # 800-999
            
            # Random 3-digit numbers
            [random.randint(100, 999) for _ in range(100)],
            
            # Random 4-digit numbers  
            [random.randint(1000, 9999) for _ in range(50)],
        ]
        
        for pattern in patterns:
            for num in pattern:
                slug = self.encode_number_to_slug(num)
                if self.is_valid_slug(slug) and slug not in self.generated_slugs:
                    slugs.append(slug)
                    self.generated_slugs.add(slug)
        
        self.generation_stats['strategies_used'][strategy] = len(slugs)
        return slugs
    
    def generate_smart_enterprise_slugs(self, total_target=1000):
        """Generate enterprise slugs using multiple smart strategies"""
        print("🏢 Starting Enterprise Slug Generation")
        print("=" * 50)
        print(f"🎯 Target: {total_target} unique slugs")
        print(f"❌ Excluding prefixes: {', '.join(self.exclude_prefixes)}")
        print(f"✅ Known working samples: {len(self.working_samples)}")
        print()
        
        all_slugs = []
        
        # Strategy 1: Around working samples (high priority)
        print("🔍 Strategy 1: Generating around working samples...")
        around_working = self.generate_around_working_samples(radius=100)
        all_slugs.extend(around_working)
        print(f"   Generated: {len(around_working)} slugs")
        
        # Strategy 2: Common patterns
        print("🔍 Strategy 2: Generating common patterns...")
        common_patterns = self.generate_common_patterns()
        all_slugs.extend(common_patterns)
        print(f"   Generated: {len(common_patterns)} slugs")
        
        # Strategy 3: Sequential ranges to fill remaining
        remaining = total_target - len(all_slugs)
        if remaining > 0:
            print(f"🔍 Strategy 3: Filling remaining {remaining} with sequential ranges...")
            
            # Try different ranges until we have enough
            ranges_to_try = [
                (1, 500, 1),
                (1000, 2000, 1), 
                (2000, 3000, 1),
                (3000, 5000, 1),
                (10000, 15000, 1),
            ]
            
            for start, end, step in ranges_to_try:
                if len(all_slugs) >= total_target:
                    break
                    
                sequential = self.generate_sequential_range(start, end, step)
                all_slugs.extend(sequential)
                print(f"   Range {start}-{end}: {len(sequential)} slugs")
                
                if len(all_slugs) >= total_target:
                    all_slugs = all_slugs[:total_target]  # Trim to exact target
                    break
        
        # Final statistics
        self.generation_stats['total_generated'] = len(all_slugs)
        
        print()
        print("📊 GENERATION COMPLETE")
        print("=" * 50)
        print(f"✅ Total unique slugs generated: {len(all_slugs)}")
        print(f"❌ Slugs excluded (Nz* prefix): {self.generation_stats['excluded_count']}")
        print(f"🎯 Target achieved: {len(all_slugs) >= total_target}")
        print()
        print("📈 Strategy breakdown:")
        for strategy, count in self.generation_stats['strategies_used'].items():
            print(f"   {strategy}: {count} slugs")
        
        return all_slugs
    
    def save_slugs_to_files(self, slugs, batch_size=200):
        """Save generated slugs to batch files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create batches
        batches = [slugs[i:i + batch_size] for i in range(0, len(slugs), batch_size)]
        
        batch_files = []
        for i, batch in enumerate(batches, 1):
            filename = f"enterprise_batch_{i}_{timestamp}.txt"
            with open(filename, 'w') as f:
                for slug in batch:
                    f.write(f"{slug}\n")
            batch_files.append(filename)
            print(f"💾 Batch {i}: {len(batch)} slugs → {filename}")
        
        # Save generation summary
        summary_file = f"ENTERPRISE_GENERATION_SUMMARY_{timestamp}.json"
        summary_data = {
            'generation_timestamp': timestamp,
            'total_slugs': len(slugs),
            'batch_count': len(batches),
            'batch_size': batch_size,
            'batch_files': batch_files,
            'working_samples_analyzed': self.working_samples,
            'excluded_prefixes': self.exclude_prefixes,
            'generation_stats': self.generation_stats,
            'sample_slugs': slugs[:10],  # First 10 for preview
            'verification': {
                slug: self.decode_slug_to_number(slug) 
                for slug in slugs[:5]  # Verify first 5 can be decoded
            }
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        print(f"📋 Summary saved: {summary_file}")
        return batch_files, summary_file

def main():
    generator = EnterpriseSlugGenerator()
    
    # Generate enterprise slugs
    slugs = generator.generate_smart_enterprise_slugs(total_target=1000)
    
    # Save to files
    batch_files, summary_file = generator.save_slugs_to_files(slugs, batch_size=200)
    
    print()
    print("🎉 Enterprise slug generation complete!")
    print(f"📁 Files created: {len(batch_files)} batch files + 1 summary")
    print("🚀 Ready for enterprise scanning!")

if __name__ == "__main__":
    main() 