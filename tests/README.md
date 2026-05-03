# Testing

The project includes comprehensive unit tests using Python's built-in `unittest` framework.

## Running Tests

Run all tests:
```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Run tests with verbose output:
```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Run a specific test file:
```bash
python3 -m unittest tests.test_ror_harvester -v
python3 -m unittest tests.test_calculate_ir_metrics -v
python3 -m unittest tests.test_filter_csv -v
```

## Test Coverage

The test suite includes 52 tests covering:

### ROR Harvester Tests (`test_ror_harvester.py`)

- **Special character encoding** (7 tests)
  - URL encoding of spaces, ampersands, parentheses, plus/minus signs
  - Unicode character handling
  - Empty strings and hyphens

- **ROR API queries** (8 tests)
  - Successful API responses
  - Empty results
  - Network timeouts and HTTP errors
  - Special character handling in queries
  - Empty and whitespace-only inputs

- **CSV processing** (7 tests)
  - Basic CSV reading and writing
  - Multiple ROR IDs per affiliation
  - Empty affiliation strings
  - Missing input files
  - Invalid CSV structure

- **Main function** (3 tests)
  - Argument validation
  - Correct function invocation

### Evaluation Metrics Tests (`test_calculate_ir_metrics.py`)

- **Data loading** (10 tests)
  - Loading ROR data from CSV files
  - Loading paper IDs from test sets
  - Handling missing files and invalid CSV structure
  - Whitespace handling

- **Metrics calculation** (7 tests)
  - Per-paper precision, recall, and F1-score
  - Perfect matches and no matches
  - Partial matches
  - Empty truth and prediction sets
  - Multiple papers

- **Overall metrics** (3 tests)
  - Micro-averaged metrics
  - Macro-averaged metrics
  - Test set filtering

- **I/O and main function** (5 tests)
  - Saving detailed results
  - Printing summaries
  - Argument validation

### CSV Filter Tests (`test_filter_csv.py`)

- **Filtering operations** (7 tests)
  - Duplicate row removal
  - Empty ROR ID filtering
  - Preservation of multiple ROR IDs for the same affiliation
  - Combined filtering operations
  - Empty files

- **Error handling** (2 tests)
  - Missing input files
  - Invalid CSV structure

## Continuous Integration

The repository includes a GitHub Actions workflow that automatically runs all tests on:
- Every push to any branch
- Every pull request

Tests are run across multiple Python versions (3.8, 3.9, 3.10, 3.11, 3.12) to ensure compatibility.
