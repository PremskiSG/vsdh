#!/usr/bin/env python3
"""
Quick sample test - runs immediately with 1000 samples
"""

import sys
import os
sys.path.append('.')

from sample_slug_scanner import SampleSlugScanner

def main():
    print("🧪 Quick Sample Test - Testing 1000 random slugs")
    print("=" * 50)
    
    scanner = SampleSlugScanner(sample_size=1000)
    scanner.scan_sample()

if __name__ == "__main__":
    main() 