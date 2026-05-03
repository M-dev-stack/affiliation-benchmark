#!/usr/bin/env python3
"""
CSV Filter - Remove duplicate rows and rows with only 'an' and empty 'ror_id'.

This script reads a CSV file, removes duplicate rows, and removes rows that
only have the 'an' field defined with an empty 'ror_id' field.
"""

import csv
import sys


def filter_csv(input_file: str, output_file: str):
    """
    Filter CSV file by removing duplicates and rows with only 'an' and empty 'ror_id'.
    
    Args:
        input_file: Path to input CSV file (must have 'an' and 'ror_id' columns)
        output_file: Path to output CSV file
    """
    try:
        # Read the CSV file
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            # Validate required columns
            if 'an' not in reader.fieldnames or 'ror_id' not in reader.fieldnames:
                print("Error: Input CSV must have 'an' and 'ror_id' columns", file=sys.stderr)
                sys.exit(1)
            
            # Process rows: remove duplicates and filter out rows with only 'an' and empty 'ror_id'
            # Use dict to deduplicate - keys are (an, ror_id) tuples, values are row dicts
            unique_rows = {}
            
            for row in reader:
                an_value = row['an']
                ror_id_value = row['ror_id']
                
                # Skip rows with only 'an' defined and empty 'ror_id'
                if an_value.strip() and not ror_id_value.strip():
                    continue
                
                # Create a tuple for duplicate detection
                row_tuple = (an_value, ror_id_value)
                
                # Dict automatically handles deduplication - last occurrence wins
                unique_rows[row_tuple] = row
        
        # Write the filtered output
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            fieldnames = ['an', 'ror_id']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_rows.values())
        
        print(f"Filtered {len(unique_rows)} rows to {output_file}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except (IOError, csv.Error) as e:
        print(f"Error processing CSV: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python filter_csv.py <input_csv> <output_csv>")
        print("\nInput CSV must have columns: 'an', 'ror_id'")
        print("Output CSV will have the same columns with:")
        print("  - Duplicate rows removed")
        print("  - Rows with only 'an' and empty 'ror_id' removed")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    filter_csv(input_file, output_file)


if __name__ == "__main__":
    main()
