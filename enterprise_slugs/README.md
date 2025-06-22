# Enterprise Slug Generator for VSDHOne

## 🏢 Overview
This directory contains the **Enterprise Slug Generator** for VSDHOne's `/b/` URL format, designed to generate base64-encoded slugs for enterprise booking URLs.

## 🔍 Pattern Analysis
Based on working samples analysis:
- **NzEw** → `710` (RenIVate)
- **NDI2** → `426` (Oh My Olivia) 
- **NzEy** → `712` (Valor Wellness)

**Pattern**: Enterprise slugs are **base64-encoded numbers**

## 🚀 Generation Strategy

### Smart Multi-Strategy Approach:

1. **Around Working Samples** (High Priority)
   - Generates numbers around known working values (±100 range)
   - Targets: 710±100, 426±100, 712±100

2. **Common Patterns**
   - Sequential ranges: 1-99, 100-199, 200-299, etc.
   - Round numbers: 100, 200, 300, 1000, 2000, etc.
   - Random 3-digit and 4-digit numbers

3. **Sequential Fill**
   - Fills remaining quota with systematic ranges
   - Ensures comprehensive coverage

### 🚫 Exclusions
- **Nz*** prefixed slugs (tested on another laptop)
- Duplicate prevention across all strategies

## 📁 Generated Files

### Latest Generation (20250622_103234):
- **Total Slugs**: 1,000 unique enterprise slugs
- **Batches**: 5 files × 200 slugs each
- **Excluded**: 332 Nz* prefixed slugs
- **Success Rate**: Successfully generated 1,000 valid slugs

#### Files:
```
enterprise_batch_1_20250622_103234.txt  (200 slugs)
enterprise_batch_2_20250622_103234.txt  (200 slugs)  
enterprise_batch_3_20250622_103234.txt  (200 slugs)
enterprise_batch_4_20250622_103234.txt  (200 slugs)
enterprise_batch_5_20250622_103234.txt  (200 slugs)
ENTERPRISE_GENERATION_SUMMARY_20250622_103234.json
```

## 🧪 Testing Results

### Quick Test Sample:
- **NjEw** (610) → ✅ **ACTIVE** (Found new business!)
- **NjEx** (611) → ❌ ERROR_PAGE
- **NjEy** (612) → ❌ ERROR_PAGE
- **MQ** (1) → ❌ ERROR_PAGE
- **Mg** (2) → ❌ ERROR_PAGE

**Discovery**: Found at least 1 new active business in generated slugs!

## 🛠️ Usage

### Generate New Slugs:
```bash
cd enterprise_slugs
python3 enterprise_slug_generator.py
```

### Test a Batch:
```bash
cd enterprise_slugs
python3 test_enterprise_batch.py enterprise_batch_1_20250622_103234.txt --max-slugs 10
```

### Full Batch Scan:
```bash
cd enterprise_slugs
python3 test_enterprise_batch.py enterprise_batch_1_20250622_103234.txt
```

## 📊 Generation Statistics

### Strategy Breakdown:
- **Around Working Samples**: 303 slugs
- **Common Patterns**: 641 slugs  
- **Sequential (1000-2000)**: 994 slugs
- **Total Unique**: 1,000 slugs

### Performance:
- **Generation Time**: ~1 second
- **Exclusion Rate**: 332 Nz* slugs filtered out
- **Success Rate**: 100% target achievement

## 🔧 Technical Details

### Base64 Encoding:
```python
number = 710
slug = base64.b64encode(str(number).encode()).decode().rstrip('=')
# Result: "NzEw"
```

### Decoding Verification:
```python
slug = "NjEw"
padded = slug + '=' * (4 - len(slug) % 4) if len(slug) % 4 else slug
number = int(base64.b64decode(padded).decode())
# Result: 610
```

## 🎯 Next Steps

1. **Batch Testing**: Test all 5 batches systematically
2. **Active Business Discovery**: Scan for new enterprise businesses
3. **Pattern Refinement**: Adjust generation based on results
4. **Scale Up**: Generate larger batches if needed

## 📈 Expected Results

Based on the pattern analysis and initial testing, we expect:
- **Hit Rate**: 0.1-1% of generated slugs may be active
- **New Businesses**: Potential to discover 1-10 new enterprise businesses
- **Coverage**: Comprehensive coverage of likely number ranges

---

**🚀 Ready for enterprise discovery scanning!** 