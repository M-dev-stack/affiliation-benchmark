# Usage Examples for zbMATH to OpenAlex ROR Harvester

**Note:** Run all commands from the repository root directory.

## Quick Start

### Test with First 3 Articles

To test the script with just the first 3 unique 'an' values:

```bash
python3 system_3/zbmath_openalex_harvester.py testset.csv test_output.csv --limit 3
```

### Process Full Testset

To process all unique 'an' values from the testset:

```bash
python3 system_3/zbmath_openalex_harvester.py testset.csv full_output.csv
```

## Run Tests

To verify the script works correctly with mock data:

```bash
python3 tests/test_zbmath_harvester.py
```

Expected output:
```
############################################################
# zbMATH to OpenAlex Harvester - Mock Tests
############################################################

============================================================
Test 1: Extract unique 'an' values
============================================================
Extracted 3 unique 'an' values:
  - 7192470
  - 7192472
  - 7192474

✓ Test passed!

[... more tests ...]

============================================================
All tests passed! ✓
============================================================
```

## Example Output

### Input (testset.csv)
```csv
an,aff_str
7192470,"CNRS, Univ. Lille, France"
7192472,"Department of Mathematics, University of Macau"
7192472,"Department of Mathematics, Lancaster University"
```

### Output (output.csv)
```csv
an,ror_id
7192470,02feahw73
7192470,041bwsv31
7192472,00mcxsr04
7192472,041231x45
```

Note: Multiple rows per 'an' value, one for each unique ROR found.

## Workflow

The script performs these steps for each unique 'an':

1. **Query zbMATH API**
   ```
   GET https://api.zbmath.org/v1/document/7192477
   ```
   → Extract DOI: `10.1007/s10851-019-00913-z`
   → Or arXiv: `1805.11596` → Convert to DOI: `10.48550/arXiv.1805.11596`

2. **Query OpenAlex API**
   ```
   GET https://api.openalex.org/works/doi:10.1007/s10851-019-00913-z
   ```
   → Extract RORs from author institutions

3. **Clean and Output**
   - Remove `https://ror.org/` prefix
   - Remove duplicates
   - Write to CSV (one row per ROR)

## Command Line Options

```
python3 system_3/zbmath_openalex_harvester.py [-h] [--limit LIMIT] testset_csv output_csv

positional arguments:
  testset_csv    Input CSV file with 'an' column
  output_csv     Output CSV file with 'an' and 'ror_id' columns

optional arguments:
  -h, --help     Show help message
  --limit LIMIT  Process only first N unique 'an' values
```

## Error Handling

The script handles various error conditions:

- **Network errors:** Automatic retry with exponential backoff (1, 2, 4, 8, 16 seconds)
- **Missing data:** Warnings printed to stderr, processing continues
- **Invalid responses:** Graceful error handling, processing continues
- **Rate limiting:** HTTP 429 errors automatically retried

## Performance Notes

- Processing time depends on API response times
- Typical API response time: 0.5-2 seconds per request
- For 1000 unique 'an' values: approximately 15-40 minutes
- Use `--limit` for quick testing

## Troubleshooting

### No RORs Found

If the script finds DOIs but no RORs:
- Check if the DOI exists in OpenAlex
- Some papers may not have ROR IDs in OpenAlex
- Output will contain rows with empty `ror_id` values

### Network Errors

If you encounter connection errors:
- Check internet connectivity
- Verify API endpoints are accessible
- The script will retry automatically up to 5 times

### Empty Output

If no results are produced:
- Verify the testset.csv has an 'an' column
- Check if zbMATH API returns DOIs for the articles
- Look for error messages in stderr

## Integration with Existing Tools

After generating ROR IDs, you can use the existing helper scripts:

### Filter Results
```bash
python3 helpers/filter_csv.py output.csv filtered_output.csv
```

This removes:
- Duplicate rows (same 'an' and 'ror_id')
- Rows with empty ROR IDs

### Calculate Metrics
```bash
python3 helpers/calculate_ir_metrics.py testset.csv truth_table.csv output.csv
```

This calculates precision, recall, and F1-score by comparing your results against ground truth.
