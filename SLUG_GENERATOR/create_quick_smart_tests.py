#!/usr/bin/env python3
"""
Smart Slug Generator for VSDHOne
Creates smart test files avoiding only previously tested slugs
"""

import string
import random
import os
import json
import argparse
import glob
from collections import Counter
from datetime import datetime

class SmartSlugGenerator:
    def __init__(self, output_file, num_slugs):
        # Known active business slugs
        self.known_active_slugs = {
            'ad31y', 'mj42f', 'os27m', 'lp56a', 'zb74k', 'ym99l', 
            'yh52b', 'zd20w', 'td32z', 'bo19e', 'bh70s', 'ai04u', 
            'bm49t', 'qu29u', 'tc33l'
        }
        
        # Character set: 0-9 + a-z
        self.charset = string.digits + string.ascii_lowercase
        
        # Configuration
        self.output_file = output_file
        self.num_slugs = num_slugs
        
        # Ensure slugs_to_be_tested directory exists
        os.makedirs('slugs_to_be_tested', exist_ok=True)
        
        # Load previously tested slugs (from scanning results)
        self.previously_tested_slugs = self.load_previously_tested_slugs()
        
        # Load previously generated slugs (to avoid repetition in generation)
        self.previously_generated_slugs = self.load_previously_generated_slugs()
        
        print(f"🧠 Smart Slug Generator")
        print(f"📊 Target: {self.num_slugs:,} new slugs")
        print(f"📂 Output file: {self.output_file}")
        print(f"🧪 Previously tested slugs to avoid: {len(self.previously_tested_slugs):,}")
        print(f"📝 Previously generated slugs to avoid: {len(self.previously_generated_slugs):,}")
        print("")
        
    def load_previously_tested_slugs(self):
        """Load slugs that have been actually tested/scanned"""
        tested_slugs = set()
        
        # Add known active slugs
        tested_slugs.update(self.known_active_slugs)
        
        # Load from MASTER_DATABASE.json if exists (actual scan results)
        if os.path.exists('../MASTER_DATABASE.json'):
            try:
                with open('../MASTER_DATABASE.json', 'r') as f:
                    master_data = json.load(f)
                    for slug_data in master_data.values():
                        tested_slugs.add(slug_data['slug'])
                print(f"📚 Loaded {len(master_data)} tested slugs from MASTER_DATABASE.json")
            except Exception as e:
                print(f"⚠️  Error loading MASTER_DATABASE.json: {e}")
        
        # Load from session logs in logs folder (actual scan results)
        if os.path.exists('../logs'):
            session_files = glob.glob('../logs/*_session.json')
            for session_file in session_files:
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                        for test_result in session_data.get('testing_results', []):
                            slug = test_result.get('slug', '')
                            if len(slug) == 5:
                                tested_slugs.add(slug)
                    print(f"📚 Loaded tested slugs from {session_file}")
                except Exception as e:
                    print(f"⚠️  Error loading {session_file}: {e}")
        
        return tested_slugs
    
    def load_previously_generated_slugs(self):
        """Load slugs that have been generated before (to avoid repetition)"""
        generated_slugs = set()
        
        # Load from any existing generated test files in slugs_to_be_tested
        slugs_dir = 'slugs_to_be_tested'
        if os.path.exists(slugs_dir):
            for filename in os.listdir(slugs_dir):
                if filename.endswith('.txt'):
                    filepath = os.path.join(slugs_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        file_slugs = [line.strip() for line in f if len(line.strip()) == 5]
                        generated_slugs.update(file_slugs)
                    print(f"📝 Loaded {len(file_slugs)} generated slugs from {filename}")
                except Exception as e:
                    print(f"⚠️  Error loading {filename}: {e}")
        
        return generated_slugs
    
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
            top_chars = pos_freq[i].most_common(3)
            print(f"   Position {i+1}: {dict(top_chars)}")
        
        return pos_freq
    
    def generate_smart_slugs(self, pos_freq, count):
        """Generate smart slugs using pattern analysis"""
        slugs = set()
        generated_count = 0
        attempts = 0
        max_attempts = count * 10  # Prevent infinite loops
        
        print(f"🎯 Generating {count:,} smart slugs...")
        
        # Create weighted character lists for each position
        weighted_chars = []
        for i in range(5):
            chars_weights = []
            for char in self.charset:
                # Higher weight for characters that appear in known active slugs
                weight = pos_freq[i].get(char, 0) + 1
                chars_weights.extend([char] * weight)
            weighted_chars.append(chars_weights)
        
        print(f"📊 Weighted character counts per position: {[len(chars) for chars in weighted_chars]}")
        
        while len(slugs) < count and attempts < max_attempts:
            attempts += 1
            
            # Generate slug using weighted random selection
            slug = ''.join(random.choice(weighted_chars[i]) for i in range(5))
            
            # Skip if already tested or already generated
            if (slug in self.previously_tested_slugs or 
                slug in self.previously_generated_slugs or 
                slug in slugs):
                continue
            
            slugs.add(slug)
            generated_count += 1
            
            # Progress update every 1000 slugs
            if generated_count % 1000 == 0:
                print(f"   ✅ Generated {generated_count:,} / {count:,} slugs ({generated_count/count*100:.1f}%)")
        
        if attempts >= max_attempts:
            print(f"⚠️  Reached maximum attempts. Generated {len(slugs):,} unique slugs.")
        else:
            print(f"🎉 Successfully generated {len(slugs):,} unique slugs!")
        
        return list(slugs)
    
    def create_test_file(self):
        """Create a test file with smart slugs"""
        print("🚀 Creating smart test file...")
        
        # Analyze patterns first
        pos_freq = self.analyze_patterns()
        
        # Generate smart slugs
        slugs = self.generate_smart_slugs(pos_freq, self.num_slugs)
        
        if len(slugs) < self.num_slugs:
            print(f"⚠️  Only generated {len(slugs):,} slugs (requested {self.num_slugs:,})")
            print(f"💡 This might happen if too many slugs have already been tested/generated")
        
        # Save to file in slugs_to_be_tested directory
        output_path = os.path.join('slugs_to_be_tested', self.output_file)
        print(f"💾 Saving {len(slugs):,} slugs to {output_path}...")
        with open(output_path, 'w') as f:
            for slug in slugs:
                f.write(f"{slug}\n")
        
        # Create summary
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = f"SMART_GENERATION_SUMMARY_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write(f"Smart Slug Generation Summary\n")
            f.write(f"=" * 40 + "\n\n")
            f.write(f"Created: {datetime.now().isoformat()}\n")
            f.write(f"Output file: {output_path}\n")
            f.write(f"Requested slugs: {self.num_slugs:,}\n")
            f.write(f"Generated slugs: {len(slugs):,}\n")
            f.write(f"Previously tested slugs avoided: {len(self.previously_tested_slugs):,}\n")
            f.write(f"Previously generated slugs avoided: {len(self.previously_generated_slugs):,}\n")
            f.write(f"Known active slugs: {len(self.known_active_slugs)}\n\n")
            
            f.write("Known Active Slugs:\n")
            for slug in sorted(self.known_active_slugs):
                f.write(f"  {slug}\n")
        
        print(f"\n🎯 SMART SLUG GENERATION COMPLETE!")
        print(f"📊 Created {output_path} with {len(slugs):,} slugs")
        print(f"📋 Summary saved to: {summary_file}")
        print(f"🧪 Avoided {len(self.previously_tested_slugs):,} tested slugs")
        print(f"📝 Avoided {len(self.previously_generated_slugs):,} previously generated slugs")
        print(f"\n💡 Usage:")
        print(f"   python3 browser_comprehensive_scanner.py --file {output_path} --instance-id laptop1")

def main():
    parser = argparse.ArgumentParser(description='Smart Slug Generator for VSDHOne')
    parser.add_argument('output_file', help='Output filename for the test slugs (e.g., batch_001.txt)')
    parser.add_argument('-n', '--number', type=int, default=10000, 
                       help='Number of slugs to generate (default: 10000)')
    
    args = parser.parse_args()
    
    # Ensure .txt extension
    if not args.output_file.endswith('.txt'):
        args.output_file += '.txt'
    
    # Check if file already exists in slugs_to_be_tested directory
    output_path = os.path.join('slugs_to_be_tested', args.output_file)
    if os.path.exists(output_path):
        response = input(f"⚠️  File {output_path} already exists. Overwrite? (yes/no): ").lower().strip()
        if response != 'yes':
            print("❌ Operation cancelled")
            return
    
    # Validate number of slugs
    if args.number <= 0:
        print("❌ Number of slugs must be positive")
        return
    
    if args.number > 1000000:
        print("⚠️  Generating more than 1M slugs might take a while...")
        response = input("Continue? (yes/no): ").lower().strip()
        if response != 'yes':
            print("❌ Operation cancelled")
            return
    
    generator = SmartSlugGenerator(args.output_file, args.number)
    generator.create_test_file()

if __name__ == "__main__":
    main() 