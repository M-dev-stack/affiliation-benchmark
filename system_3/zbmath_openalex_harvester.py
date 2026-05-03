#!/usr/bin/env python3
"""
zbMATH to OpenAlex ROR Harvester

This script:
1. Extracts unique 'an' (article number) values from testset.csv
2. For each 'an', queries zbMATH API to get DOI or arXiv identifier
3. If no DOI, converts arXiv identifier to DOI format
4. Queries OpenAlex API with DOI to get ROR IDs from author affiliations
5. Outputs results to CSV with potentially multiple rows per 'an'

Usage:
    python zbmath_openalex_harvester.py <testset_csv> <output_csv> [--limit N]
    
    --limit N: Process only first N unique 'an' values (for testing)
"""

import csv
import sys
import argparse
import os
from typing import List, Set, Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# API Configuration
ZBMATH_API_BASE = "https://api.zbmath.org/v1/document"
OPENALEX_API_BASE = "https://api.openalex.org/works"
API_TIMEOUT = 30

# Fallback DOIs file path (relative to this script)
FALLBACK_DOIS_FILE = os.path.join(os.path.dirname(__file__), 'fallback_dois.csv')


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
        backoff_factor=1,  # Wait 1, 2, 4, 8, 16 seconds between retries (exponential backoff)
        status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
        allowed_methods=["GET"]  # Only retry GET requests
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def load_fallback_dois() -> Dict[str, str]:
    """
    Load fallback DOIs from CSV file for papers where zbMATH API has no DOI.
    
    Returns:
        Dictionary mapping article numbers (an) to DOIs
    """
    fallback_dois = {}
    
    if not os.path.exists(FALLBACK_DOIS_FILE):
        print(f"Warning: Fallback DOIs file not found at {FALLBACK_DOIS_FILE}", file=sys.stderr)
        return fallback_dois
    
    try:
        with open(FALLBACK_DOIS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if 'an' not in reader.fieldnames or 'doi' not in reader.fieldnames:
                print("Warning: Fallback DOIs CSV must have 'an' and 'doi' columns", file=sys.stderr)
                return fallback_dois
            
            for row in reader:
                an_value = row['an'].strip()
                doi_value = row['doi'].strip()
                if an_value and doi_value:
                    fallback_dois[an_value] = doi_value
        
        print(f"Loaded {len(fallback_dois)} fallback DOI(s) from {FALLBACK_DOIS_FILE}")
        
    except Exception as e:
        print(f"Warning: Error loading fallback DOIs: {e}", file=sys.stderr)
    
    return fallback_dois


def extract_unique_an_values(testset_csv: str, limit: Optional[int] = None) -> List[str]:
    """
    Extract unique 'an' values from the testset CSV.
    
    Args:
        testset_csv: Path to testset CSV file
        limit: Optional limit on number of unique 'an' values to return
        
    Returns:
        List of unique 'an' values (as strings)
    """
    unique_an = []
    seen_an = set()
    
    try:
        with open(testset_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if 'an' not in reader.fieldnames:
                print("Error: testset CSV must have 'an' column", file=sys.stderr)
                sys.exit(1)
            
            for row in reader:
                an_value = row['an'].strip()
                if an_value and an_value not in seen_an:
                    seen_an.add(an_value)
                    unique_an.append(an_value)
                    
                    if limit and len(unique_an) >= limit:
                        break
        
        return unique_an
        
    except FileNotFoundError:
        print(f"Error: File '{testset_csv}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading testset CSV: {e}", file=sys.stderr)
        sys.exit(1)


def try_fallback_doi(an_value: str, fallback_dois: Optional[Dict[str, str]]) -> Optional[str]:
    """
    Try to get a DOI from the fallback dictionary.
    
    Args:
        an_value: The zbMATH article number
        fallback_dois: Optional dictionary mapping article numbers to DOIs
        
    Returns:
        DOI from fallback if found, None otherwise
    """
    if fallback_dois and an_value in fallback_dois:
        doi = fallback_dois[an_value]
        print(f"Using fallback DOI for an={an_value}: {doi}")
        return doi
    return None


def get_doi_from_zbmath(an_value: str, session: requests.Session, fallback_dois: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Query zbMATH API for an article number and extract DOI or arXiv identifier.
    Falls back to a provided dictionary if zbMATH API fails or returns no DOI.
    
    Args:
        an_value: The zbMATH article number (e.g., "7192477")
        session: Requests session with retry configuration
        fallback_dois: Optional dictionary mapping article numbers to DOIs for fallback
        
    Returns:
        DOI string (either from doi link, converted from arxiv, or from fallback)
    """
    try:
        url = f"{ZBMATH_API_BASE}/{an_value}"
        response = session.get(
            url,
            headers={'accept': 'application/json'},
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Check if result has links
        if 'result' not in data or 'links' not in data['result']:
            print(f"Warning: No links found for an={an_value}", file=sys.stderr)
            return try_fallback_doi(an_value, fallback_dois)
        
        links = data['result']['links']
        
        # First, look for DOI link
        for link in links:
            if link.get('type') == 'doi':
                doi = link.get('identifier', '')
                if doi:
                    print(f"Found DOI for an={an_value}: {doi}")
                    return doi
        
        # If no DOI, look for arXiv and convert to DOI
        for link in links:
            if link.get('type') == 'arxiv':
                arxiv_id = link.get('identifier', '')
                if arxiv_id:
                    # Convert arXiv identifier to DOI format
                    # arXiv DOIs follow the pattern: 10.48550/arXiv.{arxiv_id}
                    doi = f"10.48550/arXiv.{arxiv_id}"
                    print(f"Found arXiv for an={an_value}: {arxiv_id}, converted to DOI: {doi}")
                    return doi
        
        print(f"Warning: No DOI or arXiv identifier found for an={an_value}", file=sys.stderr)
        return try_fallback_doi(an_value, fallback_dois)
        
    except requests.exceptions.RequestException as e:
        print(f"Error querying zbMATH API for an={an_value}: {e}", file=sys.stderr)
        return try_fallback_doi(an_value, fallback_dois)
    except Exception as e:
        print(f"Unexpected error processing zbMATH response for an={an_value}: {e}", file=sys.stderr)
        return try_fallback_doi(an_value, fallback_dois)



def get_rors_from_openalex(doi: str, session: requests.Session) -> List[str]:
    """
    Query OpenAlex API with DOI and extract ROR IDs from author affiliations.
    
    Args:
        doi: The DOI to query
        session: Requests session with retry configuration
        
    Returns:
        List of ROR IDs (without the https://ror.org/ prefix)
    """
    try:
        # OpenAlex accepts DOIs in URL format with doi: prefix or just the DOI
        url = f"{OPENALEX_API_BASE}/doi:{doi}"
        response = session.get(
            url,
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        
        ror_ids = []
        
        # Extract RORs from authorships
        if 'authorships' in data:
            for authorship in data['authorships']:
                # Each authorship can have multiple institutions
                if 'institutions' in authorship:
                    for institution in authorship['institutions']:
                        # Extract ROR if present
                        if 'ror' in institution and institution['ror']:
                            ror_url = institution['ror']
                            # Remove the https://ror.org/ prefix
                            if ror_url.startswith('https://ror.org/'):
                                ror_id = ror_url[len('https://ror.org/'):]
                                ror_ids.append(ror_id)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_rors = []
        for ror_id in ror_ids:
            if ror_id not in seen:
                seen.add(ror_id)
                unique_rors.append(ror_id)
        
        if unique_rors:
            print(f"Found {len(unique_rors)} unique ROR(s) for DOI {doi}")
        else:
            print(f"Warning: No RORs found for DOI {doi}", file=sys.stderr)
        
        return unique_rors
        
    except requests.exceptions.RequestException as e:
        print(f"Error querying OpenAlex API for DOI {doi}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected error processing OpenAlex response for DOI {doi}: {e}", file=sys.stderr)
        return []


def process_testset(testset_csv: str, output_csv: str, limit: Optional[int] = None):
    """
    Process the testset CSV and generate ROR IDs via zbMATH and OpenAlex APIs.
    
    Args:
        testset_csv: Path to input testset CSV
        output_csv: Path to output CSV
        limit: Optional limit on number of 'an' values to process
    """
    print("=" * 60)
    print("zbMATH to OpenAlex ROR Harvester")
    print("=" * 60)
    
    # Create session with retry logic
    session = create_session()
    
    # Load fallback DOIs
    print("\nLoading fallback DOIs...")
    fallback_dois = load_fallback_dois()
    
    # Extract unique 'an' values
    print(f"\nExtracting unique 'an' values from {testset_csv}...")
    unique_an_values = extract_unique_an_values(testset_csv, limit)
    
    if limit:
        print(f"Processing first {len(unique_an_values)} unique 'an' value(s) (limit={limit})")
    else:
        print(f"Processing {len(unique_an_values)} unique 'an' value(s)")
    
    # Process each 'an' value
    results = []
    
    for i, an_value in enumerate(unique_an_values, 1):
        print(f"\n[{i}/{len(unique_an_values)}] Processing an={an_value}")
        
        # Get DOI from zbMATH (with fallback)
        doi = get_doi_from_zbmath(an_value, session, fallback_dois)
        
        if not doi:
            print(f"Skipping an={an_value}: No DOI found")
            continue
        
        # Get RORs from OpenAlex
        ror_ids = get_rors_from_openalex(doi, session)
        
        if ror_ids:
            # Add one row per ROR
            for ror_id in ror_ids:
                results.append({
                    'an': an_value,
                    'ror_id': ror_id
                })
        else:
            # If no RORs found, add a row with empty ror_id
            results.append({
                'an': an_value,
                'ror_id': ''
            })
    
    # Write output CSV
    print(f"\nWriting results to {output_csv}...")
    try:
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['an', 'ror_id']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        print(f"Successfully wrote {len(results)} row(s) to {output_csv}")
        
    except Exception as e:
        print(f"Error writing output CSV: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 60)
    print("Processing complete!")
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Harvest ROR IDs from zbMATH via OpenAlex API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process first 3 'an' values (for testing)
  python zbmath_openalex_harvester.py testset.csv output.csv --limit 3
  
  # Process all unique 'an' values
  python zbmath_openalex_harvester.py testset.csv output.csv
        """
    )
    
    parser.add_argument('testset_csv', help='Input testset CSV file (must have "an" column)')
    parser.add_argument('output_csv', help='Output CSV file (will contain "an" and "ror_id" columns)')
    parser.add_argument('--limit', type=int, help='Process only first N unique "an" values (for testing)')
    
    args = parser.parse_args()
    
    # Validate limit
    if args.limit is not None and args.limit < 1:
        print("Error: --limit must be a positive integer", file=sys.stderr)
        sys.exit(1)
    
    process_testset(args.testset_csv, args.output_csv, args.limit)


if __name__ == "__main__":
    main()
