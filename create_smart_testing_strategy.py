#!/usr/bin/env python3
"""
Smart Testing Strategy Generator for VSDHOne
Analyzes patterns in known active slugs and creates optimized testing batches
Creates 15 files with 500K slugs each based on pattern analysis
"""

import itertools
import string
import random
import os
from collections import Counter, defaultdict
from datetime import datetime

class SmartTestingStrategy:
    def __init__(self):
        # Known active business slugs
        self.known_active_slugs = {
            'ad31y', 'mj42f', 'os27m', 'lp56a', 'zb74k', 'ym99l', 
            'yh52b', 'zd20w', 'td32z', 'bo19e', 'bh70s', 'ai04u', 
            'bm49t', 'qu29u', 'tc33l'
        }
        
        # Character set: 0-9 + a-z
        self.charset = string.digits + string.ascii_lowercase
        
        # Target: 15 files × 500K slugs = 7.5M total slugs to test
        self.files_to_create = 15
        self.slugs_per_file = 500000
        self.total_target_slugs = self.files_to_create * self.slugs_per_file
        
        print(f"🎯 Smart Testing Strategy Generator")
        print(f"📊 Target: {self.files_to_create} files × {self.slugs_per_file:,} slugs = {self.total_target_slugs:,} total slugs")
        print("")
        
    def analyze_patterns(self):
        """Analyze patterns in known active slugs"""
        print("🔍 Analyzing patterns in known active slugs...")
        
        # Position-based character frequency analysis
        pos_freq = [Counter() for _ in range(5)]
        
        for slug in self.known_active_slugs:
            for i, char in enumerate(slug):
                pos_freq[i][char] += 1
        
        print("📈 Character frequency by position:")
        for i in range(5):
            print(f"   Position {i+1}: {dict(pos_freq[i].most_common())}")
        
        # Pattern analysis
        patterns = {
            'starts_with_letter': sum(1 for s in self.known_active_slugs if s[0].isalpha()),
            'starts_with_digit': sum(1 for s in self.known_active_slugs if s[0].isdigit()),
            'ends_with_letter': sum(1 for s in self.known_active_slugs if s[4].isalpha()),
            'ends_with_digit': sum(1 for s in self.known_active_slugs if s[4].isdigit()),
            'has_consecutive_letters': sum(1 for s in self.known_active_slugs if any(s[i].isalpha() and s[i+1].isalpha() for i in range(4))),
            'has_consecutive_digits': sum(1 for s in self.known_active_slugs if any(s[i].isdigit() and s[i+1].isdigit() for i in range(4)))
        }
        
        print("🧩 Pattern analysis:")
        for pattern, count in patterns.items():
            percentage = (count / len(self.known_active_slugs)) * 100
            print(f"   {pattern}: {count}/{len(self.known_active_slugs)} ({percentage:.1f}%)")
        
        return pos_freq, patterns
    
    def generate_pattern_based_slugs(self, pos_freq, count):
        """Generate slugs based on character frequency patterns"""
        slugs = set()
        
        # Create weighted character lists for each position
        weighted_chars = []
        for i in range(5):
            chars_weights = []
            for char in self.charset:
                weight = pos_freq[i].get(char, 0) + 1  # +1 to include all chars
                chars_weights.extend([char] * weight)
            weighted_chars.append(chars_weights)
        
        while len(slugs) < count:
            slug = ''.join(random.choice(weighted_chars[i]) for i in range(5))
            slugs.add(slug)
            
            if len(slugs) % 50000 == 0:
                print(f"   Generated {len(slugs):,} pattern-based slugs...")
        
        return list(slugs)
    
    def generate_high_frequency_combinations(self, pos_freq, count):
        """Generate combinations using most frequent characters per position"""
        slugs = set()
        
        # Get top characters for each position
        top_chars = []
        for i in range(5):
            # Get top 50% of characters by frequency
            sorted_chars = [char for char, freq in pos_freq[i].most_common()]
            if not sorted_chars:  # If no frequency data, use all chars
                sorted_chars = list(self.charset)
            
            # Take top half, but at least 6 characters
            top_count = max(6, len(sorted_chars) // 2)
            top_chars.append(sorted_chars[:top_count])
        
        print(f"🎯 High-frequency chars per position: {[len(chars) for chars in top_chars]}")
        
        # Generate combinations from high-frequency characters
        while len(slugs) < count:
            slug = ''.join(random.choice(top_chars[i]) for i in range(5))
            slugs.add(slug)
            
            if len(slugs) % 50000 == 0:
                print(f"   Generated {len(slugs):,} high-frequency slugs...")
        
        return list(slugs)
    
    def generate_similar_to_known(self, count):
        """Generate slugs similar to known active ones (1-2 character variations)"""
        slugs = set()
        
        while len(slugs) < count:
            # Pick a random known slug
            base_slug = random.choice(list(self.known_active_slugs))
            
            # Create variations
            for _ in range(10):  # Try multiple variations per base
                variation = list(base_slug)
                
                # Change 1-2 characters randomly
                positions_to_change = random.sample(range(5), random.choice([1, 2]))
                
                for pos in positions_to_change:
                    variation[pos] = random.choice(self.charset)
                
                new_slug = ''.join(variation)
                if new_slug not in self.known_active_slugs:
                    slugs.add(new_slug)
                
                if len(slugs) >= count:
                    break
            
            if len(slugs) % 50000 == 0:
                print(f"   Generated {len(slugs):,} variation-based slugs...")
        
        return list(slugs)[:count]
    
    def generate_sequential_ranges(self, count):
        """Generate sequential ranges around known active slugs"""
        slugs = set()
        
        for base_slug in self.known_active_slugs:
            # Generate slugs before and after this one
            range_size = count // (len(self.known_active_slugs) * 2)
            
            # Convert slug to number for sequential generation
            base_num = self.slug_to_number(base_slug)
            
            # Generate range before
            for offset in range(-range_size//2, range_size//2):
                try:
                    new_num = base_num + offset
                    if new_num >= 0:
                        new_slug = self.number_to_slug(new_num)
                        if new_slug not in self.known_active_slugs:
                            slugs.add(new_slug)
                except:
                    continue
            
            if len(slugs) >= count:
                break
        
        print(f"   Generated {len(slugs):,} sequential range slugs...")
        return list(slugs)[:count]
    
    def slug_to_number(self, slug):
        """Convert slug to number for sequential operations"""
        number = 0
        base = len(self.charset)
        for char in slug:
            number = number * base + self.charset.index(char)
        return number
    
    def number_to_slug(self, number):
        """Convert number back to slug"""
        if number == 0:
            return '00000'
        
        slug = []
        base = len(self.charset)
        while number > 0:
            slug.append(self.charset[number % base])
            number //= base
        
        # Pad to 5 characters
        while len(slug) < 5:
            slug.append('0')
        
        return ''.join(reversed(slug))
    
    def generate_random_sampling(self, count):
        """Generate completely random slugs for comparison"""
        slugs = set()
        
        while len(slugs) < count:
            slug = ''.join(random.choices(self.charset, k=5))
            if slug not in self.known_active_slugs:
                slugs.add(slug)
            
            if len(slugs) % 50000 == 0:
                print(f"   Generated {len(slugs):,} random slugs...")
        
        return list(slugs)
    
    def create_testing_files(self):
        """Create 15 optimized testing files"""
        print("🚀 Creating smart testing strategy files...")
        
        # Analyze patterns first
        pos_freq, patterns = self.analyze_patterns()
        
        strategies = [
            ("pattern_weighted", "Pattern-weighted based on frequency analysis", 3),
            ("high_frequency", "High-frequency character combinations", 3),
            ("similar_variations", "Variations of known active slugs", 2),
            ("sequential_ranges", "Sequential ranges around known slugs", 2),
            ("random_sampling", "Random sampling for comparison", 2),
            ("mixed_strategy", "Mixed approach combining all strategies", 3)
        ]
        
        file_counter = 1
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for strategy_name, description, file_count in strategies:
            print(f"\n📋 Creating {file_count} files using: {description}")
            
            for i in range(file_count):
                filename = f"SMART_TEST_BATCH_{file_counter:02d}_{strategy_name}_{timestamp}.txt"
                
                print(f"   📝 Generating {filename}...")
                
                if strategy_name == "pattern_weighted":
                    slugs = self.generate_pattern_based_slugs(pos_freq, self.slugs_per_file)
                elif strategy_name == "high_frequency":
                    slugs = self.generate_high_frequency_combinations(pos_freq, self.slugs_per_file)
                elif strategy_name == "similar_variations":
                    slugs = self.generate_similar_to_known(self.slugs_per_file)
                elif strategy_name == "sequential_ranges":
                    slugs = self.generate_sequential_ranges(self.slugs_per_file)
                elif strategy_name == "random_sampling":
                    slugs = self.generate_random_sampling(self.slugs_per_file)
                elif strategy_name == "mixed_strategy":
                    # Mix of all strategies
                    chunk_size = self.slugs_per_file // 4
                    slugs = []
                    slugs.extend(self.generate_pattern_based_slugs(pos_freq, chunk_size))
                    slugs.extend(self.generate_high_frequency_combinations(pos_freq, chunk_size))
                    slugs.extend(self.generate_similar_to_known(chunk_size))
                    slugs.extend(self.generate_random_sampling(chunk_size))
                    
                    # Shuffle the mixed results
                    random.shuffle(slugs)
                    slugs = slugs[:self.slugs_per_file]
                
                # Remove any known active slugs
                slugs = [s for s in slugs if s not in self.known_active_slugs]
                
                # Ensure we have exactly the target count
                while len(slugs) < self.slugs_per_file:
                    new_slug = ''.join(random.choices(self.charset, k=5))
                    if new_slug not in self.known_active_slugs and new_slug not in slugs:
                        slugs.append(new_slug)
                
                slugs = slugs[:self.slugs_per_file]
                
                # Save to file
                with open(filename, 'w') as f:
                    for slug in slugs:
                        f.write(f"{slug}\n")
                
                print(f"   ✅ Created {filename} with {len(slugs):,} slugs")
                file_counter += 1
        
        # Create summary file
        summary_file = f"SMART_TEST_STRATEGY_SUMMARY_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("VSDHOne Smart Testing Strategy Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Created: {datetime.now().isoformat()}\n")
            f.write(f"Total files: {self.files_to_create}\n")
            f.write(f"Slugs per file: {self.slugs_per_file:,}\n")
            f.write(f"Total slugs: {self.total_target_slugs:,}\n\n")
            
            f.write("Strategy Distribution:\n")
            for strategy_name, description, file_count in strategies:
                f.write(f"  {strategy_name}: {file_count} files - {description}\n")
            
            f.write(f"\nKnown Active Slugs ({len(self.known_active_slugs)}):\n")
            for slug in sorted(self.known_active_slugs):
                f.write(f"  {slug}\n")
            
            f.write(f"\nPattern Analysis:\n")
            for pattern, count in patterns.items():
                percentage = (count / len(self.known_active_slugs)) * 100
                f.write(f"  {pattern}: {count}/{len(self.known_active_slugs)} ({percentage:.1f}%)\n")
        
        print(f"\n🎯 SMART TESTING STRATEGY COMPLETE!")
        print(f"📊 Created {self.files_to_create} files with {self.total_target_slugs:,} total slugs")
        print(f"📋 Strategy summary saved to: {summary_file}")
        print(f"\n💡 Usage:")
        print(f"   python3 browser_comprehensive_scanner.py --file SMART_TEST_BATCH_01_pattern_weighted_{timestamp}.txt --instance-id laptop1")

def main():
    strategy_generator = SmartTestingStrategy()
    strategy_generator.create_testing_files()

if __name__ == "__main__":
    main() 