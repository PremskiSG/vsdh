# VSDHOne Enterprise Slug Generation System

## Overview
This system generates enterprise slugs for VSDHOne URL format: `https://vsdigital-bookingwidget-prod.azurewebsites.net/b/`

## Working Samples Analysis
- **NzEw** → `710` (RenIVate)
- **NDI2** → `426` (Oh My Olivia)  
- **NzEy** → `712` (Valor Wellness)
- **Pattern**: Enterprise slugs are base64-encoded numbers
- **Key Insight**: All working samples are 3-digit numbers!

## Generated Batches

### Small Initial Batches (1,000 total slugs) - LEGACY
Generated on 20250622_103234:
- `enterprise_batch_1_20250622_103234.txt` - 200 slugs
- `enterprise_batch_2_20250622_103234.txt` - 200 slugs
- `enterprise_batch_3_20250622_103234.txt` - 200 slugs
- `enterprise_batch_4_20250622_103234.txt` - 200 slugs
- `enterprise_batch_5_20250622_103234.txt` - 200 slugs

### Focused Production Batches (8,800 total slugs) - CURRENT
Generated on 20250622_111132 with COMPLETE coverage:

#### 3-Digit Number Batches (800 total slugs)
- `enterprise_3digit_batch_1_20250622_111132.txt` - 300 slugs (numbers 100-399)
- `enterprise_3digit_batch_2_20250622_111132.txt` - 300 slugs (numbers 400-699)  
- `enterprise_3digit_batch_3_20250622_111132.txt` - 200 slugs (numbers 800-999)

#### 4-Digit Number Batches (8,000 total slugs)
- `enterprise_4digit_batch_1_20250622_111132.txt` - 3,000 slugs (numbers 1000-3999)
- `enterprise_4digit_batch_2_20250622_111132.txt` - 3,000 slugs (numbers 4000-6999)
- `enterprise_4digit_batch_3_20250622_111132.txt` - 2,000 slugs (numbers 7000-9999)

**Complete Coverage**: 100% of 3-digit numbers (100-999) and 100% of 4-digit numbers (1000-9999)

## Generation Strategy - Focused Approach
The focused batches provide systematic, complete coverage:

1. **3-Digit Complete Coverage**: All numbers 100-999 (matching working sample pattern)
2. **4-Digit Complete Coverage**: All numbers 1000-9999 (logical extension)
3. **No Duplicates**: Fresh generation with complete coverage
4. **Realistic Ranges**: Based on working samples (all 3-digit numbers)

## Exclusions
- **Nz*** prefixed slugs (tested on other laptop)
- **No other exclusions** - complete coverage within ranges

## Usage with Enterprise Scanner

### Quick Test (3-Digit Batch)
```bash
python3 ../enterprise_level_scanner.py enterprise_3digit_batch_1_20250622_111132.txt
```

### Production Scanning (4-Digit Batch)
```bash
python3 ../enterprise_level_scanner.py enterprise_4digit_batch_1_20250622_111132.txt
```

### Complete Sequential Scanning
```bash
# Scan all 3-digit numbers first (most likely to find matches)
python3 ../enterprise_level_scanner.py enterprise_3digit_batch_1_20250622_111132.txt
python3 ../enterprise_level_scanner.py enterprise_3digit_batch_2_20250622_111132.txt
python3 ../enterprise_level_scanner.py enterprise_3digit_batch_3_20250622_111132.txt

# Then scan 4-digit numbers
python3 ../enterprise_level_scanner.py enterprise_4digit_batch_1_20250622_111132.txt
python3 ../enterprise_level_scanner.py enterprise_4digit_batch_2_20250622_111132.txt
python3 ../enterprise_level_scanner.py enterprise_4digit_batch_3_20250622_111132.txt
```

## File Structure
```
enterprise_slugs/
├── README.md                                          # This documentation
├── enterprise_slug_generator.py                       # Original small batch generator
├── generate_large_enterprise_batches.py              # Large batch generator (DEPRECATED)
├── generate_focused_enterprise_batches.py            # Focused batch generator (CURRENT)
├── test_enterprise_batch.py                          # Batch testing utility
├── enterprise_batch_*_20250622_103234.txt           # Small batches (LEGACY)
├── enterprise_3digit_batch_*_20250622_111132.txt    # 3-digit focused batches (CURRENT)
├── enterprise_4digit_batch_*_20250622_111132.txt    # 4-digit focused batches (CURRENT)
└── FOCUSED_ENTERPRISE_GENERATION_SUMMARY_20250622_111132.json # Current summary
```

## Sample Slug Examples
```
3-digit examples:
MTAw → 100, MTAx → 101, NDI2 → 426, NzEw → 710

4-digit examples:  
MTAwMA → 1000, MTAwMQ → 1001, NDAwMA → 4000
```

## Performance Expectations
- **Enterprise URLs**: ~0.85s response time (much faster than widget URLs)
- **Scanner Rate**: ~10 requests/second with rate limiting
- **Average per URL**: ~3.5 seconds (including processing + rate limiting)
- **3-digit batches**: ~300 slugs = ~17 minutes scanning each
- **4-digit batches**: ~2,500-3,000 slugs = ~2.5-3 hours scanning each

## Known Active Discoveries
- **NjEw** (610) - Discovered as ACTIVE during testing
- **Working samples**: NzEw (710), NDI2 (426), NzEy (712)

## Scanner Integration
All batch files are compatible with:
- `enterprise_level_scanner.py` - Production scanning with full logging
- `enterprise_self_test_scanner.py` - Validation testing
- Both scanners include checkpoint/resume functionality every 10 scans

## Strategy Recommendations

### Priority Order (Highest to Lowest Probability):
1. **3-digit batches first** - All working samples are 3-digit numbers
2. **4-digit batches second** - Logical extension for broader coverage
3. **Focus on 3-digit batch 2** (400-699) - Contains working sample range

### Expected Hit Rate:
- **3-digit numbers**: Higher probability (working samples are all 3-digit)
- **4-digit numbers**: Lower probability but broader coverage
- **Estimated active businesses**: 5-50 across all batches

 