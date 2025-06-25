#!/usr/bin/env python3
"""
Fresh Base64 Slug Generator

Generates base64 encoded slugs for two ranges:
1. Numbers 1 to 999
2. Numbers 1000 to 1999

This is a completely fresh generator that ignores any existing databases or previous generations.
"""

import base64
from datetime import datetime
import os

def generate_base64_slug_file(start_num, end_num, filename):
    """
    Generate a file with base64 encoded slugs for the specified number range.
    
    Args:
        start_num (int): Starting number (inclusive)
        end_num (int): Ending number (inclusive)
        filename (str): Output filename
    """
    print(f"Generating slugs for range {start_num} to {end_num}...")
    
    with open(filename, 'w') as f:
        for num in range(start_num, end_num + 1):
            # Convert number to string, then to bytes, then to base64
            num_str = str(num)
            num_bytes = num_str.encode('utf-8')
            base64_slug = base64.b64encode(num_bytes).decode('utf-8')
            
            f.write(base64_slug + '\n')
    
    print(f"✓ Generated {end_num - start_num + 1} slugs in file: {filename}")
    return end_num - start_num + 1

def show_sample_slugs(start_num, count=5):
    """Show sample base64 slugs for verification"""
    print(f"\nSample slugs starting from {start_num}:")
    for i in range(count):
        num = start_num + i
        num_str = str(num)
        num_bytes = num_str.encode('utf-8')
        base64_slug = base64.b64encode(num_bytes).decode('utf-8')
        print(f"  {num} -> {base64_slug}")

def main():
    """
    Generate two files with base64 encoded slugs:
    1. File 1: numbers 1-999
    2. File 2: numbers 1000-1999
    """
    print("=== FRESH BASE64 SLUG GENERATOR ===")
    print("Ignoring any existing databases or previous generations")
    print()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Show samples before generation
    show_sample_slugs(1)
    show_sample_slugs(1000)
    
    print("\nStarting generation...")
    
    # Generate first file: 1-999
    file1 = f"base64_slugs_001_to_999_{timestamp}.txt"
    count1 = generate_base64_slug_file(1, 999, file1)
    
    # Generate second file: 1000-1999
    file2 = f"base64_slugs_1000_to_1999_{timestamp}.txt"
    count2 = generate_base64_slug_file(1000, 1999, file2)
    
    # Verify files exist
    file1_size = os.path.getsize(file1) if os.path.exists(file1) else 0
    file2_size = os.path.getsize(file2) if os.path.exists(file2) else 0
    
    print(f"\n=== GENERATION COMPLETE ===")
    print(f"Created files:")
    print(f"  - {file1} ({file1_size:,} bytes)")
    print(f"  - {file2} ({file2_size:,} bytes)")
    print(f"Total slugs generated: {count1 + count2:,}")
    print()
    print("Files are ready for use!")

if __name__ == "__main__":
    main() 