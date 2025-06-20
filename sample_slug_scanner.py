#!/usr/bin/env python3
"""
Sample VSDHOne Slug Scanner
Tests a smaller sample to validate approach before full comprehensive scan
"""

import time
import csv
import json
import requests
import string
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

class SampleSlugScanner:
    def __init__(self, sample_size=10000):
        self.base_url = "https://vsdigital-bookingwidget-prod.azurewebsites.net"
        self.api_endpoint = "/api/business/"
        
        # Character set: a-z + 0-9
        self.charset = string.ascii_lowercase + string.digits  # 36 characters
        self.total_possible = 36 ** 5  # 60,466,176
        self.sample_size = sample_size
        
        # Known working slugs to skip
        self.known_slugs = {
            'ad31y', 'mj42f', 'os27m', 'lp56a', 'zb74k', 'ym99l', 
            'yh52b', 'zd20w', 'td32z', 'bo19e', 'bh70s', 'ai04u', 
            'bm49t', 'qu29u', 'tc33l'
        }
        
        # Results tracking
        self.found_slugs = []
        self.tested_count = 0
        self.start_time = None
        self.lock = Lock()
        
        # Configuration
        self.max_workers = 5  # Reduce threads for better progress visibility
        self.requests_per_second = 3  # Conservative rate limiting for sampling
        self.timeout = 10  # Request timeout
        self.checkpoint_interval = 50  # Save checkpoint every 50 slugs
        
        # Results file
        self.results_file = f"sample_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.checkpoint_file = f"sample_checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        print(f"🧪 Sample VSDHOne Slug Scanner")
        print(f"📊 Testing {sample_size:,} random combinations ({sample_size/self.total_possible*100:.4f}% of total)")
        print(f"⚡ Concurrent workers: {self.max_workers}")
        print(f"🔄 Rate limit: {self.requests_per_second} requests/second")
        print(f"💾 Results file: {self.results_file}")
    
    def generate_random_slug(self):
        """Generate a random 5-character slug"""
        return ''.join(random.choices(self.charset, k=5))
    
    def generate_sample_slugs(self):
        """Generate sample slugs using different strategies"""
        sample_slugs = set()
        
        # Strategy 1: Pure random (50% of sample)
        random_count = self.sample_size // 2
        print(f"🎲 Generating {random_count} pure random slugs...")
        while len(sample_slugs) < random_count:
            slug = self.generate_random_slug()
            if slug not in self.known_slugs:
                sample_slugs.add(slug)
        
        # Strategy 2: Pattern-based (25% of sample) - similar to known working patterns
        pattern_count = self.sample_size // 4
        print(f"🔍 Generating {pattern_count} pattern-based slugs...")
        
        # Common patterns from known slugs
        common_first = ['a', 'b', 't', 'y', 'z', 'm', 'o', 'l']
        common_second = ['d', 'h', 'm', 'i', 'o', 'c']
        common_first_digit = ['0', '1', '2', '3', '4', '5', '7']
        common_last_digit = ['0', '1', '2', '4', '9']
        common_last = ['a', 'b', 'e', 'f', 'k', 'l', 'm', 's', 't', 'u', 'w', 'y', 'z']
        
        while len(sample_slugs) < random_count + pattern_count:
            slug = (
                random.choice(common_first) +
                random.choice(common_second) +
                random.choice(common_first_digit) +
                random.choice(common_last_digit) +
                random.choice(common_last)
            )
            if slug not in self.known_slugs:
                sample_slugs.add(slug)
        
        # Strategy 3: Sequential ranges (25% of sample) - test specific ranges
        sequential_count = self.sample_size - len(sample_slugs)
        print(f"📈 Generating {sequential_count} sequential range slugs...")
        
        # Test some specific ranges
        ranges = [
            ('aaaaa', 'abzzz'),  # Start of alphabet
            ('ma000', 'mazzz'),  # Medical/Med prefix
            ('ha000', 'hazzz'),  # Health prefix
            ('ba000', 'bazzz'),  # Business prefix
            ('ca000', 'cazzz'),  # Care/Clinic prefix
            ('wa000', 'wazzz'),  # Wellness prefix
            ('za000', 'zazzz'),  # End ranges
        ]
        
        for start_range, end_range in ranges:
            if len(sample_slugs) >= self.sample_size:
                break
            
            # Generate some slugs in this range
            for _ in range(sequential_count // len(ranges)):
                if len(sample_slugs) >= self.sample_size:
                    break
                
                # Generate within range
                slug = self.generate_random_slug()  # For now, just random
                if slug not in self.known_slugs:
                    sample_slugs.add(slug)
        
        return list(sample_slugs)[:self.sample_size]
    
    def test_slug_api(self, slug):
        """Test a single slug via API endpoint"""
        try:
            url = f"{self.base_url}{self.api_endpoint}{slug}"
            response = requests.get(url, timeout=self.timeout)
            
            # Check if it's a real business (not just HTML shell)
            content = response.text.lower()
            
            # Look for business indicators in the response  
            business_indicators = [
                'business_name', 'company', 'clinic', 'center', 'health',
                'medical', 'therapy', 'treatment', 'doctor', 'wellness',
                'spa', 'hotel', 'booking', 'appointment', 'schedule',
                'service', 'price', 'location', 'contact', 'phone'
            ]
            
            # Check for JSON-like structure or business content
            has_business_content = any(indicator in content for indicator in business_indicators)
            
            # Different validation levels
            validation_levels = []
            
            # Level 1: Basic response
            if response.status_code == 200:
                validation_levels.append("valid_response")
            
            # Level 2: Substantial content
            if len(content) > 1000:
                validation_levels.append("substantial_content")
            
            # Level 3: Business indicators
            if has_business_content:
                validation_levels.append("business_indicators")
            
            # Level 4: JSON content type
            if 'json' in response.headers.get('content-type', ''):
                validation_levels.append("json_content")
            
            # Level 5: Non-error page
            if not any(error in content for error in ['401', 'error', 'not found', 'nothing left']):
                validation_levels.append("non_error")
                
            # Return detailed result for analysis
            return {
                'slug': slug,
                'url': url,
                'status_code': response.status_code,
                'content_length': len(content),
                'content_type': response.headers.get('content-type', ''),
                'validation_levels': '|'.join(validation_levels),
                'validation_count': len(validation_levels),
                'has_business_indicators': has_business_content,
                'business_indicator_count': sum(1 for indicator in business_indicators if indicator in content),
                'first_100_chars': content[:100].replace('\n', ' ').replace('\r', ' '),
                'contains_401': '401' in content,
                'contains_error': 'error' in content.lower(),
                'found_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'slug': slug,
                'error': str(e),
                'found_at': datetime.now().isoformat()
            }
    
    def test_single_slug_with_progress(self, slug, current_index, total_slugs):
        """Test a single slug with detailed progress output"""
        print(f"🔍 [{current_index:,}/{total_slugs:,}] Testing: {slug} ({(current_index/total_slugs)*100:.2f}%)")
        
        result = self.test_slug_api(slug)
        
        # Show result immediately
        if result.get('error'):
            print(f"   ❌ Error: {result['error']}")
        elif result.get('validation_count', 0) >= 3:
            print(f"   ⭐ PROMISING: {result['validation_count']} validation levels - {result.get('content_length', 0)} chars")
        elif result.get('validation_count', 0) >= 2:
            print(f"   🔍 Interesting: {result['validation_count']} validation levels")
        elif result.get('contains_401'):
            print(f"   🚫 401 Error page")
        else:
            print(f"   ✅ Response: {result.get('status_code', 'N/A')} - {result.get('content_length', 0)} chars")
        
        return result
    
    def save_checkpoint(self, current_index, total_slugs, all_results, sample_slugs):
        """Save checkpoint with current progress"""
        checkpoint_data = {
            'current_index': current_index,
            'total_slugs': total_slugs,
            'results_count': len(all_results),
            'timestamp': datetime.now().isoformat(),
            'remaining_slugs': sample_slugs[current_index:] if current_index < len(sample_slugs) else [],
            'found_promising': len([r for r in all_results if r.get('validation_count', 0) >= 3])
        }
        
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        print(f"💾 Checkpoint saved: {current_index}/{total_slugs} processed")
    
    def scan_sample(self):
        """Main sampling function with detailed progress"""
        self.start_time = datetime.now()
        print(f"🚀 Starting sample scan at {self.start_time}")
        print(f"📍 Checkpoint file: {self.checkpoint_file}")
        print(f"📊 Will save checkpoint every {self.checkpoint_interval} slugs\n")
        
        # Generate sample slugs
        sample_slugs = self.generate_sample_slugs()
        total_slugs = len(sample_slugs)
        print(f"✅ Generated {total_slugs} unique sample slugs\n")
        
        all_results = []
        promising_count = 0
        
        # Process slugs one by one for maximum visibility
        for i, slug in enumerate(sample_slugs):
            current_index = i + 1
            
            # Test slug with progress output
            result = self.test_single_slug_with_progress(slug, current_index, total_slugs)
            all_results.append(result)
            
            # Track promising results
            if result.get('validation_count', 0) >= 3:
                promising_count += 1
            
            # Rate limiting
            time.sleep(1.0 / self.requests_per_second)
            
            # Checkpoint every N slugs
            if current_index % self.checkpoint_interval == 0:
                self.save_checkpoint(current_index, total_slugs, all_results, sample_slugs)
                print(f"📊 CHECKPOINT SUMMARY:")
                print(f"   • Processed: {current_index:,}/{total_slugs:,} ({current_index/total_slugs*100:.1f}%)")
                print(f"   • Promising results: {promising_count}")
                print(f"   • Errors: {len([r for r in all_results if 'error' in r])}")
                print(f"   • Time elapsed: {datetime.now() - self.start_time}")
                print("")
            
            # Show mini-summary every 100 slugs
            elif current_index % 100 == 0:
                elapsed = datetime.now() - self.start_time
                rate = current_index / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
                eta = (total_slugs - current_index) / rate if rate > 0 else 0
                print(f"📈 PROGRESS UPDATE:")
                print(f"   • {current_index:,}/{total_slugs:,} ({current_index/total_slugs*100:.1f}%)")
                print(f"   • Rate: {rate:.1f} slugs/sec")
                print(f"   • ETA: {eta/60:.1f} minutes")
                print(f"   • Promising: {promising_count}")
                print("")
        
        # Final checkpoint
        self.save_checkpoint(total_slugs, total_slugs, all_results, sample_slugs)
        
        # Analyze results
        print(f"\n🔬 FINAL ANALYSIS")
        print(f"=" * 50)
        self.analyze_results(all_results)
        
        # Save results
        self.save_results(all_results)
        self.print_summary(all_results)
    
    def analyze_results(self, results):
        """Analyze sample results"""
        print(f"\n🔬 ANALYZING SAMPLE RESULTS")
        print(f"=" * 40)
        
        total = len(results)
        errors = len([r for r in results if 'error' in r])
        valid_responses = len([r for r in results if r.get('status_code') == 200])
        
        # Validation level analysis
        validation_stats = {}
        for i in range(6):
            count = len([r for r in results if r.get('validation_count', 0) >= i])
            validation_stats[i] = count
        
        print(f"📊 Total tested: {total}")
        print(f"❌ Errors: {errors}")
        print(f"✅ Valid HTTP responses: {valid_responses}")
        print(f"\n🎯 Validation Level Analysis:")
        for level, count in validation_stats.items():
            percentage = (count / total) * 100 if total > 0 else 0
            print(f"  Level {level}+: {count} ({percentage:.2f}%)")
        
        # Find most promising results
        promising = [r for r in results if r.get('validation_count', 0) >= 3]
        if promising:
            print(f"\n🌟 Most Promising Results ({len(promising)} found):")
            for result in promising[:10]:  # Show top 10
                print(f"  • {result['slug']}: {result['validation_levels']} - {result.get('content_length', 0)} chars")
    
    def save_results(self, results):
        """Save results to CSV"""
        if not results:
            return
        
        # Get all field names
        all_fields = set()
        for result in results:
            all_fields.update(result.keys())
        
        fieldnames = sorted(list(all_fields))
        
        with open(self.results_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"💾 Saved {len(results)} results to {self.results_file}")
    
    def print_summary(self, results):
        """Print final summary"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print(f"\n🎯 SAMPLE SCAN COMPLETE")
        print(f"=" * 40)
        print(f"⏱️  Duration: {duration}")
        print(f"📊 Sample size: {len(results):,}")
        print(f"📈 Estimated total hits: {len([r for r in results if r.get('validation_count', 0) >= 3]) * (self.total_possible / len(results)):,.0f}")
        print(f"💾 Results saved to: {self.results_file}")

def main():
    print("🧪 VSDHOne Sample Slug Scanner")
    print("=" * 40)
    
    sample_size = input("Enter sample size (default 10000): ").strip()
    if not sample_size:
        sample_size = 10000
    else:
        sample_size = int(sample_size)
    
    scanner = SampleSlugScanner(sample_size)
    scanner.scan_sample()

if __name__ == "__main__":
    main() 