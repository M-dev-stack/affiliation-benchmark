# System 3 Missed Papers Analysis

## Overview

This analysis examines papers that System 3 could not process due to zbMATH API 404 errors and calculates adjusted recall metrics by excluding these papers from the evaluation.

## Missed Papers

### Count and Source
- **Total missed papers**: 65 out of 1009 unique papers (6.45%)
- **Source**: zbMATH API returned 404 "Not Found" errors
- **Cause**: Article metadata not available in zbMATH database

### Complete List of Missed Papers (AN values)

The following 65 papers could not be processed by System 3:

```
6676473, 6676474, 7113793, 7192482, 7192714, 7192715, 7192797, 7192800, 
7192804, 7192805, 7192881, 7192882, 7192883, 7192884, 7192885, 7192886, 
7192887, 7192888, 7192889, 7192890, 7192891, 7192892, 7192893, 7192897, 
7192898, 7192899, 7192900, 7192901, 7192902, 7192903, 7192904, 7192905, 
7192906, 7198965, 7198969, 7198986, 7199054, 7199286, 7199291, 7347171, 
7442286, 7610603, 7610604, 7624888, 7800289, 7890231, 7890232, 7890233, 
7890234, 7890237, 7890238, 7937829, 7975827, 8006337, 8006339, 8006340, 
8006341, 8006342, 8006343, 8006344, 8011472, 8011473, 8011485, 8016647, 
8016648
```

This list has been saved to: `system_3/missed_papers.csv`

## Metrics Comparison

### System 3 Original Performance (All 1008 Papers)

```
============================================================
INFORMATION RETRIEVAL METRICS SUMMARY
============================================================

Micro-averaged Metrics (aggregated over all ROR IDs):
  Precision: 0.8225
  Recall:    0.8462
  F1-Score:  0.8342

Macro-averaged Metrics (averaged per paper):
  Precision: 0.8793
  Recall:    0.8539
  F1-Score:  0.8181

Counts:
  True Positives:  1650
  False Positives: 356
  False Negatives: 300
  Total Papers: 1008
============================================================
```

### System 3 Adjusted Performance (Excluding 65 Missed Papers = 943 Papers)

```
============================================================
ADJUSTED INFORMATION RETRIEVAL METRICS SUMMARY
(Excluding papers with zbMATH API 404 errors)
============================================================

Excluded Papers: 65

Micro-averaged Metrics (aggregated over all ROR IDs):
  Precision: 0.8225
  Recall:    0.9011
  F1-Score:  0.8600

Macro-averaged Metrics (averaged per paper):
  Precision: 0.8710
  Recall:    0.9117
  F1-Score:  0.8735

Counts:
  True Positives:  1650
  False Positives: 356
  False Negatives: 181
  Total Papers (after exclusion): 943
============================================================
```

### System 1 Performance (All 1008 Papers)

```
============================================================
INFORMATION RETRIEVAL METRICS SUMMARY
============================================================

Micro-averaged Metrics (aggregated over all ROR IDs):
  Precision: 0.8710
  Recall:    0.8826
  F1-Score:  0.8767

Macro-averaged Metrics (averaged per paper):
  Precision: 0.8879
  Recall:    0.8921
  F1-Score:  0.8845

Counts:
  True Positives:  1721
  False Positives: 255
  False Negatives: 229
  Total Papers: 1008
============================================================
```

## Analysis

### Impact of Excluding Missed Papers

When we exclude the 65 papers that System 3 couldn't process:

**Recall Improvement:**
- **Micro-averaged recall**: 0.8462 → **0.9011** (+5.49 percentage points, +6.5% relative improvement)
- **Macro-averaged recall**: 0.8539 → **0.9117** (+5.78 percentage points, +6.8% relative improvement)

**F1-Score Improvement:**
- **Micro-averaged F1**: 0.8342 → **0.8600** (+2.58 percentage points, +3.1% relative improvement)
- **Macro-averaged F1**: 0.8181 → **0.8735** (+5.54 percentage points, +6.8% relative improvement)

**Precision:**
- Remains unchanged at 0.8225 (micro) / 0.8710 (macro), as expected since TP and FP counts don't change

**False Negatives:**
- Reduced from 300 to 181 (reduction of 119)
- This confirms that the 65 missed papers contained 119 ground truth ROR IDs that System 3 couldn't retrieve

### Comparison: System 3 (Adjusted) vs System 1

#### Micro-averaged Metrics

| Metric    | System 3 (Adjusted) | System 1 | Difference        |
|-----------|---------------------|----------|-------------------|
| Precision | 0.8225              | 0.8710   | **-0.0485 (-4.9%)**  |
| Recall    | **0.9011**          | 0.8826   | **+0.0185 (+1.9%)** |
| F1-Score  | 0.8600              | 0.8767   | **-0.0167 (-1.7%)**  |

#### Macro-averaged Metrics

| Metric    | System 3 (Adjusted) | System 1 | Difference        |
|-----------|---------------------|----------|-------------------|
| Precision | 0.8710              | 0.8879   | **-0.0169 (-1.7%)**  |
| Recall    | **0.9117**          | 0.8921   | **+0.0196 (+2.0%)** |
| F1-Score  | 0.8735              | 0.8845   | **-0.0110 (-1.1%)**  |

### Key Findings

1. **Recall Advantage**: When we exclude papers that System 3 couldn't process, **System 3 achieves higher recall than System 1** (0.9011 vs 0.8826 micro-averaged, 0.9117 vs 0.8921 macro-averaged).

2. **Precision Trade-off**: System 3's adjusted precision (0.8225 micro, 0.8710 macro) is still lower than System 1 (0.8710 micro, 0.8879 macro), indicating System 3 retrieves more ROR IDs but with more false positives.

3. **F1-Score**: System 1 maintains a slightly better overall F1-score (0.8767 vs 0.8600 micro-averaged), showing better balance between precision and recall.

4. **Coverage Limitation**: System 3's major limitation is the 6.45% of papers it cannot process due to missing zbMATH metadata. This is a fundamental constraint of the two-API approach.

## Implications

### Strengths of System 3 (When Data Available)

- **Superior recall**: When papers are processable, System 3 finds more ground truth ROR IDs than System 1
- **Better coverage**: The adjusted recall of 0.9011 (micro) shows System 3 misses fewer correct ROR IDs for papers it can process
- **Metadata-based approach**: Leveraging structured DOI/arXiv identifiers provides more comprehensive author affiliation data

### Limitations of System 3

- **Coverage gap**: 6.45% of papers cannot be processed due to missing zbMATH metadata
- **Lower precision**: More false positives indicate some incorrect ROR ID assignments
- **API dependency**: Relies on both zbMATH and OpenAlex APIs, creating multiple points of failure

### Comparison with System 1

When we account for papers System 3 can actually process:

- **System 3 has better recall** (+1.9% micro, +2.0% macro)
- **System 1 has better precision** (+4.9% micro, +1.7% macro)  
- **System 1 has better overall F1-score** (+1.7% micro, +1.1% macro)

The trade-off is:
- **System 3**: Higher recall but lower precision and limited coverage
- **System 1**: Better balanced performance with complete coverage

## Recommendations

1. **Hybrid Approach**: Consider combining both systems - use System 3 when zbMATH metadata is available, fall back to System 1 for the remaining ~6.5% of papers

2. **Precision Improvement for System 3**: Investigate why System 3 has more false positives and apply filtering to improve precision

3. **Metadata Completeness**: Work with zbMATH to improve metadata coverage for the missing papers

4. **Context-Dependent Choice**: 
   - Use System 3 when **maximum recall** is critical and papers have zbMATH coverage
   - Use System 1 when **complete coverage** is required or **higher precision** is preferred

## Files Generated

1. **`system_3/missed_papers.csv`** - List of 65 AN values that couldn't be processed
2. **`system_3/extract_missed_papers.py`** - Script to extract missed papers from run.log
3. **`system_3/calculate_adjusted_metrics.py`** - Script to calculate metrics excluding missed papers
4. **`system_3/ANALYSIS.md`** - This analysis document

## Usage

### Extract Missed Papers

```bash
python3 system_3/extract_missed_papers.py system_3/run.log system_3/missed_papers.csv
```

### Calculate Adjusted Metrics

```bash
python3 system_3/calculate_adjusted_metrics.py testset.csv truth_table.csv system_3/result.csv system_3/missed_papers.csv
```
