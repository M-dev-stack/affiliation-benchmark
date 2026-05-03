# zbMATH to OpenAlex ROR Harvester

This script harvests ROR (Research Organization Registry) IDs by combining data from zbMATH and OpenAlex APIs.

## Overview

The script performs the following workflow:

1. **Extracts unique 'an' (article number) values** from the testset CSV
2. **Queries zbMATH API** for each 'an' to get DOI or arXiv identifier
3. **Converts arXiv to DOI** if no DOI link is present (format: `10.48550/arXiv.{arxiv_id}`)
4. **Queries OpenAlex API** using the DOI to get author affiliations
5. **Extracts ROR IDs** from author institutions
6. **Outputs to CSV** with potentially multiple rows per 'an' (one row per unique ROR)

## Requirements

```bash
pip install -r requirements.txt
```

Dependencies:
- Python 3.6+
- `requests` library

## Usage

**Note:** Run all commands from the repository root directory.

### Basic Usage

Process all unique 'an' values from the testset:

```bash
python3 system_3/zbmath_openalex_harvester.py testset.csv output.csv
```

### Testing Mode

Process only the first N unique 'an' values (useful for testing):

```bash
python3 system_3/zbmath_openalex_harvester.py testset.csv output.csv --limit 3
```

This will process only the first 3 unique 'an' values from the testset.

### Command-Line Arguments

```
positional arguments:
  testset_csv           Input testset CSV file (must have "an" column)
  output_csv           Output CSV file (will contain "an" and "ror_id" columns)

optional arguments:
  --limit N            Process only first N unique "an" values (for testing)
  -h, --help           Show help message and exit
```

## Input Format

The input CSV must have at least an `an` column:

```csv
an,aff_str
7192470,"CNRS, Univ. Lille, UMR 8524 - Laboratoire Paul Painlevé, F-59000Lille, France"
7192472,"Department of Mathematics, University of Macau, Avenida da Universidade, Taipa, Macau, China"
7192472,"Department of Mathematics and Statistics, Lancaster University, Lancaster, LA14YF, United Kingdom"
```

## Output Format

The output CSV contains two columns: `an` and `ror_id`:

```csv
an,ror_id
7192470,02feahw73
7192472,00mcxsr04
7192472,041bwsv31
```

- Multiple rows per 'an' if multiple RORs are found
- Empty `ror_id` if no ROR was found for that 'an'
- ROR IDs have the `https://ror.org/` prefix removed

## API Details

### zbMATH API

The script queries the zbMATH API to get document metadata:

```bash
curl -X 'GET' 'https://api.zbmath.org/v1/document/7192477' -H 'accept: application/json'
```

From the response, it extracts:
1. **DOI** from links with `type: "doi"`
2. **arXiv identifier** from links with `type: "arxiv"` (if no DOI)

Example zbMATH response:
```json
{
  "result": {
    "links": [
      {
        "identifier": "10.1007/s10851-019-00913-z",
        "type": "doi",
        "url": "https://doi.org/10.1007/s10851-019-00913-z"
      },
      {
        "identifier": "1805.11596",
        "type": "arxiv",
        "url": "https://arxiv.org/abs/1805.11596"
      }
    ]
  }
}
```

### arXiv to DOI Conversion

If no DOI link is found, the script converts arXiv identifiers to DOI format:

```
arXiv: 1805.11596
  ↓
DOI: 10.48550/arXiv.1805.11596
```

### OpenAlex API

The script then queries OpenAlex using the DOI:

```bash
curl 'https://api.openalex.org/works/doi:10.1007/s10851-019-00913-z'
```

It extracts ROR IDs from the `authorships` field:

```json
{
  "authorships": [
    {
      "author_position": "first",
      "author": {
        "id": "https://openalex.org/A5048491430",
        "display_name": "Heather Piwowar"
      },
      "institutions": [
        {
          "id": "https://openalex.org/I4210166736",
          "display_name": "Impact Technology Development",
          "ror": "https://ror.org/05ppvf150",
          "country_code": "US"
        }
      ]
    }
  ]
}
```

The script:
- Extracts all RORs from all authorships
- Removes duplicates
- Removes the `https://ror.org/` prefix

## Testing

A comprehensive test suite is provided to validate the functionality:

```bash
python test_zbmath_harvester.py
```

This runs mock tests for:
1. Extracting unique 'an' values
2. Getting DOI from zbMATH
3. Converting arXiv to DOI
4. Extracting RORs from OpenAlex
5. ROR prefix removal

## Error Handling

The script includes robust error handling:

- **Network errors**: Automatic retry with exponential backoff
- **Missing data**: Warnings printed to stderr
- **Invalid responses**: Gracefully handled with error messages
- **Rate limiting**: HTTP 429 errors automatically retried

## Example Workflow

```bash
# Test with first 3 'an' values
python3 system_3/zbmath_openalex_harvester.py testset.csv test_output.csv --limit 3

# Process complete testset
python3 system_3/zbmath_openalex_harvester.py testset.csv full_output.csv
```

Example output:
```
============================================================
zbMATH to OpenAlex ROR Harvester
============================================================

Extracting unique 'an' values from testset.csv...
Processing first 3 unique 'an' value(s) (limit=3)

[1/3] Processing an=7192470
Found DOI for an=7192470: 10.1234/example-doi
Found 2 unique ROR(s) for DOI 10.1234/example-doi

[2/3] Processing an=7192472
Found arXiv for an=7192472: 1805.11596, converted to DOI: 10.48550/arXiv.1805.11596
Found 1 unique ROR(s) for DOI 10.48550/arXiv.1805.11596

[3/3] Processing an=7192474
Found DOI for an=7192474: 10.5678/another-doi
Found 3 unique ROR(s) for DOI 10.5678/another-doi

Writing results to test_output.csv...
Successfully wrote 6 row(s) to test_output.csv
============================================================
Processing complete!
============================================================
```

## Analyzing Missed Papers

System 3 may encounter papers where zbMATH API returns 404 errors (metadata not available). To analyze these missed papers and calculate adjusted metrics:

### Extract Missed Papers

Extract list of papers that couldn't be processed from the run log:

```bash
python3 system_3/extract_missed_papers.py system_3/run.log system_3/missed_papers.csv
```

This creates a CSV file listing all paper AN values where zbMATH API returned 404 errors.

### Calculate Adjusted Metrics

Calculate recall and other metrics excluding papers that couldn't be processed:

```bash
python3 system_3/calculate_adjusted_metrics.py testset.csv truth_table.csv system_3/result.csv system_3/missed_papers.csv
```

This shows the "true" performance of System 3 for papers it could actually process.

### Analysis Report

For a complete analysis of missed papers and performance comparison with System 1, see:
- **`system_3/ANALYSIS.md`** - Detailed analysis report

Key findings:
- ~6.45% of papers (65 out of 1009) cannot be processed due to missing zbMATH metadata
- When excluding missed papers, System 3 achieves higher recall than System 1 (0.9011 vs 0.8826 micro-averaged)
- System 1 maintains higher precision and better overall F1-score due to complete coverage

## Notes

- The script processes unique 'an' values (not individual rows)
- Duplicate RORs within the same 'an' are automatically removed
- If neither DOI nor arXiv identifier is found, the 'an' is skipped
- Progress messages are printed to stdout
- Error messages are printed to stderr
