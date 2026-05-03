#!/usr/bin/env python3
"""
ROR Harvester - Query ROR API for affiliation strings and extract ROR IDs.

This script reads a CSV file with affiliation strings, queries the ROR API,
and outputs a CSV file with ROR IDs.
"""

import csv
import sys
from typing import List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Constants
ROR_API_TIMEOUT = 30  # Timeout in seconds for ROR API requests
ROR_API_BASE_URL = "https://api.ror.org/organizations"


def create_session() -> requests.Session:
    """
    Create a requests session with retry logic for handling rate limits.
    
    Automatically retries on:
    - HTTP 429 (Too Many Requests)
    - HTTP 500, 502, 503, 504 (Server errors)
    
    Returns:
        Configured requests.Session with retry logic
    """
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=5,  # Maximum number of retries
        backoff_factor=1,  # Wait 0, 2, 4, 8, 16 seconds between retries (exponential backoff)
        status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
        allowed_methods=["GET"]  # Only retry GET requests
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def query_ror_api(affiliation_string: str, session: requests.Session) -> List[str]:
    """
    Query the ROR API for an affiliation string and extract ROR IDs.
    
    Uses the affiliation endpoint with chosen=true filtering to get
    high-precision matches. Extracts IDs from organization.id field.
    
    Args:
        affiliation_string: The affiliation string to search for
        session: Requests session with retry configuration
        
    Returns:
        List of ROR IDs (without the https://ror.org/ prefix) where chosen=true
    """
    if not affiliation_string or not affiliation_string.strip():
        return []
    
    try:
        # Make the API request with affiliation parameter for better precision
        response = session.get(
            ROR_API_BASE_URL,
            params={
                "affiliation": affiliation_string.strip(),
                "single_search": True
            },
            timeout=ROR_API_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Extract ROR IDs from the response
        # For affiliation endpoint: only use items where chosen=true
        # and extract from organization.id
        ror_ids = []
        if 'items' in data:
            for item in data['items']:
                # Only include results where chosen is true
                if item.get('chosen', False):
                    # Extract ROR ID from organization.id
                    if 'organization' in item and 'id' in item['organization']:
                        ror_id = item['organization']['id']
                        # Remove the https://ror.org/ prefix
                        if ror_id.startswith('https://ror.org/'):
                            ror_id = ror_id[len('https://ror.org/'):]
                        ror_ids.append(ror_id)
        
        return ror_ids
        
    except requests.exceptions.RequestException as e:
        # Include exception type for better diagnostics
        error_msg = f"Error querying ROR API for '{affiliation_string}' ({type(e).__name__}): {str(e)}"
        try:
            print(error_msg, file=sys.stderr)
        except UnicodeEncodeError:
            # Fallback: write directly to stderr.buffer for environments with encoding issues
            sys.stderr.buffer.write(error_msg.encode('utf-8', errors='replace') + b'\n')
        return []


def process_csv(input_file: str, output_file: str):
    """
    Process CSV file, query ROR API, and write results.
    
    Args:
        input_file: Path to input CSV file (must have 'an' and 'aff_str' columns)
        output_file: Path to output CSV file
    """
    # Create session with retry logic
    session = create_session()
    
    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            
            # Validate required columns
            if 'an' not in reader.fieldnames or 'aff_str' not in reader.fieldnames:
                print("Error: Input CSV must have 'an' and 'aff_str' columns", file=sys.stderr)
                sys.exit(1)
            
            # Process each row
            results = []
            for row in reader:
                an_value = row['an']
                aff_str = row['aff_str']
                
                # Query ROR API
                ror_ids = query_ror_api(aff_str, session)
                
                # Create one result entry per ROR ID
                if ror_ids:
                    for ror_id in ror_ids:
                        results.append({
                            'an': an_value,
                            'ror_id': ror_id
                        })
                else:
                    # If no ROR IDs found, create a row with empty ror_id
                    results.append({
                        'an': an_value,
                        'ror_id': ''
                    })
                
                # Print progress
                print(f"Processed: {an_value} -> {len(ror_ids)} ROR ID(s) found")
        
        # Write output CSV
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            fieldnames = ['an', 'ror_id']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"\nResults written to {output_file}")
        
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except (IOError, csv.Error) as e:
        print(f"Error processing CSV: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: python ror_harvester.py <input_csv> <output_csv>")
        print("\nInput CSV must have columns: 'an', 'aff_str'")
        print("Output CSV will have columns: 'an', 'ror_id'")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    process_csv(input_file, output_file)


if __name__ == "__main__":
    main()
