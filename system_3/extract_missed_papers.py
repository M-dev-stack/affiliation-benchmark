#!/usr/bin/env python3
"""
Extract list of missed papers from System 3 run.log.

This script parses the run.log file to identify papers (AN values) where
the zbMATH API returned 404 errors, indicating unavailable metadata.
These papers could not be processed by System 3.
"""

import csv
import re
import sys


def extract_missed_papers(log_file):
    """
    Extract AN values from log file where zbMATH API returned 404 errors.
    
    Args:
        log_file: Path to the run.log file
        
    Returns:
        List of AN values (as strings) that had 404 errors
    """
    missed_papers = []
    
    # Pattern to match: "Error querying zbMATH API for an=7192482: 404 Client Error"
    pattern = r'Error querying zbMATH API for an=(\d+): 404 Client Error'
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.search(pattern, line)
                if match:
                    an_value = match.group(1)
                    missed_papers.append(an_value)
    except FileNotFoundError:
        print(f"Error: File '{log_file}' not found", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file '{log_file}': {e}", file=sys.stderr)
        sys.exit(1)
    
    return missed_papers


def save_to_csv(missed_papers, output_file):
    """
    Save list of missed papers to CSV file.
    
    Args:
        missed_papers: List of AN values
        output_file: Path to output CSV file
    """
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['an'])
            for an in missed_papers:
                writer.writerow([an])
        
        print(f"Successfully wrote {len(missed_papers)} missed papers to {output_file}")
    except IOError as e:
        print(f"Error writing to file '{output_file}': {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python extract_missed_papers.py <run.log> <output.csv>")
        print("\nArguments:")
        print("  run.log    - System 3 run log file")
        print("  output.csv - Output CSV file with missed paper AN values")
        sys.exit(1)
    
    log_file = sys.argv[1]
    output_file = sys.argv[2]
    
    print(f"Extracting missed papers from: {log_file}")
    missed_papers = extract_missed_papers(log_file)
    
    print(f"Found {len(missed_papers)} papers with 404 errors from zbMATH API")
    print(f"Missed AN values: {', '.join(missed_papers[:10])}{'...' if len(missed_papers) > 10 else ''}")
    
    save_to_csv(missed_papers, output_file)


if __name__ == "__main__":
    main()
