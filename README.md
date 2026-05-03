# Affiliation matching
Supplementary data repository for affiliation matching repo

## Repository Structure

The repository is organized as follows:

- **`system_1/`** - Contains results from System 1 (improved system with better recall)
  - `system_1.csv` - ROR ID predictions with improved performance
  
- **`system_2/`** - Contains baseline system results and code
  - `test_results.csv` - Baseline ROR harvester results
  - `ror_harvester.py` - Script to fetch ROR IDs from affiliation strings

- **`system_3/`** - Contains zbMATH-OpenAlex integration system results and code
  - `result.csv` - System 3 ROR harvester results
  - `zbmath_openalex_harvester.py` - Script that queries zbMATH for DOIs and OpenAlex for ROR IDs
  - `run.log` - Detailed log file from the harvesting process
  - `README.md` - Documentation for the zbMATH-OpenAlex harvester
  
- **`helpers/`** - Helper scripts for evaluation and data processing
  - `calculate_ir_metrics.py` - Calculate precision, recall, and F1-score
  - `filter_csv.py` - Clean CSV files by removing duplicates and empty ROR IDs

- **`tests/`** - Unit tests for all components
  - `test_ror_harvester.py` - Tests for ROR harvester
  - `test_calculate_ir_metrics.py` - Tests for metrics calculation
  - `test_filter_csv.py` - Tests for CSV filtering
  - `README.md` - Testing documentation
  
- **Root directory** - Test data and documentation
  - `testset.csv` - Test set with affiliation strings
  - `truth_table.csv` - Ground truth ROR IDs for evaluation
  - `sample_input.csv` - Sample input file for testing

## Overview

This repository contains tools and results for matching affiliation strings to ROR (Research Organization Registry) IDs. The baseline system queries the ROR API for each affiliation string and extracts ROR IDs from the results.

## Requirements

- Python 3.6 or higher
- `requests` library (install with: `pip install -r requirements.txt`)

## Results

### System 1 Performance

System 1 shows improved recall compared to the baseline:

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

### Baseline System Performance (System 2)

The baseline ROR harvester approach:

```
============================================================
INFORMATION RETRIEVAL METRICS SUMMARY
============================================================

Micro-averaged Metrics (aggregated over all ROR IDs):
  Precision: 0.9328
  Recall:    0.7831
  F1-Score:  0.8514

Macro-averaged Metrics (averaged per paper):
  Precision: 0.9396
  Recall:    0.8015
  F1-Score:  0.8247

Counts:
  True Positives:  1527
  False Positives: 110
  False Negatives: 423
  Total Papers: 1008
============================================================
```

System 1 achieves better recall (0.8826 vs 0.7831 micro-averaged) at the cost of slightly lower precision (0.8710 vs 0.9328 micro-averaged), resulting in a better overall F1-score (0.8767 vs 0.8514 micro-averaged).

### System 3 Performance (zbMATH-OpenAlex Integration)

System 3 uses a different approach by integrating zbMATH and OpenAlex APIs:

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

System 3 demonstrates balanced performance with micro-averaged precision of 0.8225 and recall of 0.8462, achieving an F1-score of 0.8342. This positions it between the baseline System 2 (higher precision, lower recall) and System 1 (lower precision, higher recall).

#### Analysis of Missed Papers

During the harvesting process, System 3 encountered **65 papers (6.44% of the 1009 unique papers)** where the zbMATH API returned 404 errors, indicating that the article metadata was not available.

**Adjusted Performance (Excluding Missed Papers):**

When excluding the 65 papers that couldn't be processed, System 3 achieves:

```
Micro-averaged Metrics (943 papers):
  Precision: 0.8225
  Recall:    0.9011 (improved from 0.8462)
  F1-Score:  0.8600 (improved from 0.8342)

Macro-averaged Metrics:
  Precision: 0.8710
  Recall:    0.9117 (improved from 0.8539)
  F1-Score:  0.8735 (improved from 0.8181)
```

**Key Findings:**
- When excluding missed papers, **System 3 achieves higher recall than System 1** (0.9011 vs 0.8826 micro-averaged)
- System 1 maintains higher precision (0.8710 vs 0.8225) and better overall F1-score (0.8767 vs 0.8600)
- The 65 missed papers contained 119 ground truth ROR IDs that System 3 couldn't retrieve

**Tools for Analysis:**

To analyze missed papers and calculate adjusted metrics:

```bash
# Extract missed papers from run log
python3 system_3/extract_missed_papers.py system_3/run.log system_3/missed_papers.csv

# Calculate adjusted metrics excluding missed papers
python3 system_3/calculate_adjusted_metrics.py testset.csv truth_table.csv system_3/result.csv system_3/missed_papers.csv
```

For detailed analysis, see **`system_3/ANALYSIS.md`**.

## Testing

The project includes comprehensive unit tests. See [tests/README.md](tests/README.md) for detailed testing documentation.

Quick start:
```bash
# Run all tests
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Helper Scripts

### CSV Filter Script (`helpers/filter_csv.py`)

The `filter_csv.py` script cleans up CSV files by removing duplicate rows and rows with empty ROR IDs:

```bash
python helpers/filter_csv.py <input_csv> <output_csv>
```

This script:
- **Removes duplicate rows**: Identical rows (same `an` and `ror_id`) are removed
- **Removes rows with empty ROR IDs**: Rows that have an `an` value but an empty `ror_id` are removed

**Example Usage:**
```bash
python helpers/filter_csv.py results.csv filtered_results.csv
```

**Example**: Given an input file with duplicates and empty ROR IDs:
```csv
an,ror_id
1,052gg0110
1,052gg0110
2,
3,042nb2s44
```

The filter will produce:
```csv
an,ror_id
1,052gg0110
3,042nb2s44
```

The duplicate row for `an=1` is removed, and the row `an=2` with empty `ror_id` is filtered out.

### Calculating Information Retrieval Metrics (`helpers/calculate_ir_metrics.py`)

The `calculate_ir_metrics.py` script compares predicted ROR IDs against ground truth and calculates standard Information Retrieval metrics.

**Important Note on Terminology:**
- Each row in the CSV files has an `an` (author number) identifier representing a **paper/publication**
- Each paper may have multiple affiliations (affiliation strings)
- The ROR harvester processes all affiliations for a paper and returns a set of ROR IDs
- Metrics are calculated **per paper** (per `an`), comparing all predicted ROR IDs for that paper against the ground truth

#### Usage

```bash
python helpers/calculate_ir_metrics.py <testset.csv> <truth_table.csv> <test_results.csv> [detailed_output.csv]
```

**Arguments:**
- `testset.csv` - Test set with paper IDs (CSV with 'an' column) - defines the papers to evaluate
- `truth_table.csv` - Ground truth ROR IDs (CSV with 'an' and 'ror_id' columns)
- `test_results.csv` - Predicted ROR IDs (CSV with 'an' and 'ror_id' columns)
- `detailed_output.csv` - Optional: Save per-paper metrics to CSV file

**Example:**
```bash
python helpers/calculate_ir_metrics.py testset.csv truth_table.csv system_1/system_1.csv detailed_metrics.csv
```

#### Metrics Calculated

The script calculates both **micro-averaged** and **macro-averaged** metrics:

**Micro-averaged metrics** (aggregated over all ROR IDs):
- Aggregates True Positives, False Positives, and False Negatives across all papers
- Then calculates precision, recall, and F1-score from the aggregated counts
- Gives more weight to papers with many ROR IDs
- **Precision**: What fraction of all predicted ROR IDs (across all papers) are correct?
- **Recall**: What fraction of all true ROR IDs (across all papers) were found?
- **F1-Score**: Harmonic mean of micro-precision and micro-recall

**Macro-averaged metrics** (averaged per paper):
- Calculates precision, recall, and F1-score for each paper individually
- Then averages these metrics across all papers
- Treats each paper equally regardless of how many ROR IDs it has
- **Precision**: Average precision across all papers
- **Recall**: Average recall across all papers
- **F1-Score**: Average F1-score across all papers

**Counts:**
- True Positives (TP): Correct ROR ID predictions
- False Positives (FP): Incorrect ROR ID predictions
- False Negatives (FN): Missed ROR IDs from ground truth

#### Handling Papers with No Ground Truth

**Important:** The evaluation includes all papers from the test set, ensuring consistent evaluation across the entire dataset. The script now requires `testset.csv` as input to define the exact set of papers to evaluate.

**How these papers are handled in metrics calculation:**

1. **Papers with predictions but no ground truth**:
   - Ground truth: empty set `{}`
   - Predictions: whatever ROR IDs were predicted, e.g., `{ror1, ror2}`
   - Metrics calculation:
     - TP = 0 (no true positives possible without ground truth)
     - FP = number of predicted ROR IDs (all predictions are false positives)
     - FN = 0 (no ground truth to miss)
     - Precision = 0.0 (no predictions are correct)
     - Recall = 1.0 (standard IR convention: nothing to miss when ground truth is empty)

2. **Papers with ground truth but no predictions**:
   - Ground truth: e.g., `{ror1, ror2}`
   - Predictions: empty set `{}`
   - Metrics calculation:
     - TP = 0 (nothing predicted)
     - FP = 0 (no false predictions)
     - FN = number of ground truth ROR IDs (all missed)
     - Precision = 1.0 (standard IR convention: no false positives when predictions are empty)
     - Recall = 0.0 (nothing found)

3. **Papers with no ground truth and no predictions** (perfect match):
   - Ground truth: empty set `{}`
   - Predictions: empty set `{}`
   - Metrics calculation:
     - TP = 0, FP = 0, FN = 0 (perfect agreement)
     - Precision = 1.0 (no false positives)
     - Recall = 1.0 (nothing to miss)
   - Interpretation: A system that correctly predicts nothing when there's nothing to predict is performing perfectly

**Impact on overall metrics:**
- **Micro-averaging**: Papers with no ground truth contribute to the total false positives count, which lowers the overall precision. This is intentional - the system is penalized for predicting ROR IDs when there should be none.
- **Macro-averaging**: With standard IR conventions:
  - Papers with predictions but no ground truth contribute P=0.0, R=1.0 (nothing to miss)
  - Papers with ground truth but no predictions contribute P=1.0 (no false positives), R=0.0

**Example from dataset:**
```
Paper 7199025:
  Ground truth: {} (0 affiliations)
  Predicted: {03kw9gc02} (1 ROR ID)
  Result: TP=0, FP=1, FN=0, Precision=0.0, Recall=1.0 (nothing to miss)
```

**Key changes:**
- The script now requires `testset.csv` to define the papers to evaluate
- All 1008 distinct papers from the test set are evaluated
- Papers only in `truth_table.csv` but not in `testset.csv` are excluded from evaluation
- This ensures consistent micro-averaging across the complete test set

This approach ensures that:
- The system is evaluated on all papers in the test set (1008 papers)
- Predicting ROR IDs for papers with no affiliations is counted as an error
- The evaluation reflects real-world performance where some papers may have no affiliations
- Micro-averaging considers the complete test set for accurate metrics

#### Output

The script prints a summary to stdout. Example output format (using baseline `test_results.csv`):
```
============================================================
INFORMATION RETRIEVAL METRICS SUMMARY
============================================================

Micro-averaged Metrics (aggregated over all ROR IDs):
  Precision: 0.9328
  Recall:    0.7823
  F1-Score:  0.8509

Macro-averaged Metrics (averaged per paper):
  Precision: 0.9393
  Recall:    0.7985
  F1-Score:  0.8218

Counts:
  True Positives:  1527
  False Positives: 110
  False Negatives: 423
  Total Papers: 1008
============================================================
```

If a detailed output file is specified, per-paper metrics are saved as CSV with columns:
- `an`: Paper identifier
- `precision`, `recall`, `f1`: Per-paper metrics
- `tp`, `fp`, `fn`: Counts for this paper
- `true_count`, `pred_count`: Number of ROR IDs in truth and prediction
