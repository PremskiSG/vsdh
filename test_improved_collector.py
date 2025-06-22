#!/usr/bin/env python3
"""
Test the improved enterprise business details collector on NzE0
"""

import sys
import os

# Import the collector
from enterprise_business_details_collector import EnterpriseBusinessCollector

def test_nze0_collector():
    print("🧪 Testing Improved Enterprise Business Details Collector on NzE0")
    print("=" * 70)
    
    # Create collector instance
    collector = EnterpriseBusinessCollector(instance_id="TEST_NZE0")
    
    # Test the collection
    collector.collect_business_details("test_nze0_slug.txt")

if __name__ == "__main__":
    test_nze0_collector()
