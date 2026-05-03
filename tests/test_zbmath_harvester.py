#!/usr/bin/env python3
"""
Test script for zbmath_openalex_harvester with mock data.

This script demonstrates the functionality of the zbMATH to OpenAlex harvester
by simulating API responses with mock data.
"""

import json
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path to import the harvester from system_3
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from system_3.zbmath_openalex_harvester import (
    get_doi_from_zbmath,
    get_rors_from_openalex,
    extract_unique_an_values,
    create_session,
    load_fallback_dois
)


def test_extract_unique_an_values():
    """Test extraction of unique 'an' values."""
    print("=" * 60)
    print("Test 1: Extract unique 'an' values")
    print("=" * 60)
    
    # Extract first 3 unique 'an' values
    unique_an = extract_unique_an_values('testset.csv', limit=3)
    
    print(f"Extracted {len(unique_an)} unique 'an' values:")
    for an in unique_an:
        print(f"  - {an}")
    
    assert len(unique_an) == 3, f"Expected 3 unique 'an' values, got {len(unique_an)}"
    assert unique_an[0] == '7192470', f"Expected first 'an' to be 7192470, got {unique_an[0]}"
    
    print("\n✓ Test passed!\n")


def test_get_doi_from_zbmath_with_doi():
    """Test zbMATH API parsing with DOI link."""
    print("=" * 60)
    print("Test 2: Get DOI from zbMATH (with DOI link)")
    print("=" * 60)
    
    # Mock zbMATH API response with DOI
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
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
    mock_response.raise_for_status = Mock()
    
    session = create_session()
    
    with patch.object(session, 'get', return_value=mock_response):
        doi = get_doi_from_zbmath('7192477', session)
    
    print(f"Input: an=7192477")
    print(f"Output DOI: {doi}")
    
    assert doi == "10.1007/s10851-019-00913-z", f"Expected DOI 10.1007/s10851-019-00913-z, got {doi}"
    
    print("\n✓ Test passed!\n")


def test_get_doi_from_zbmath_with_arxiv():
    """Test zbMATH API parsing with only arXiv identifier."""
    print("=" * 60)
    print("Test 3: Get DOI from zbMATH (arXiv to DOI conversion)")
    print("=" * 60)
    
    # Mock zbMATH API response with only arXiv
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": {
            "links": [
                {
                    "identifier": "1805.11596",
                    "type": "arxiv",
                    "url": "https://arxiv.org/abs/1805.11596"
                }
            ]
        }
    }
    mock_response.raise_for_status = Mock()
    
    session = create_session()
    
    with patch.object(session, 'get', return_value=mock_response):
        doi = get_doi_from_zbmath('7192478', session)
    
    print(f"Input: an=7192478 (with arXiv 1805.11596)")
    print(f"Output DOI: {doi}")
    print(f"Note: arXiv identifier converted to DOI format")
    
    assert doi == "10.48550/arXiv.1805.11596", f"Expected DOI 10.48550/arXiv.1805.11596, got {doi}"
    
    print("\n✓ Test passed!\n")


def test_get_rors_from_openalex():
    """Test OpenAlex API parsing to extract RORs."""
    print("=" * 60)
    print("Test 4: Get RORs from OpenAlex")
    print("=" * 60)
    
    # Mock OpenAlex API response with RORs
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "authorships": [
            {
                "author_position": "first",
                "author": {
                    "id": "https://openalex.org/A5048491430",
                    "display_name": "Heather Piwowar",
                    "orcid": "https://orcid.org/0000-0003-1613-5981"
                },
                "institutions": [
                    {
                        "id": "https://openalex.org/I4210166736",
                        "display_name": "Impact Technology Development (United States)",
                        "ror": "https://ror.org/05ppvf150",
                        "country_code": "US"
                    }
                ]
            },
            {
                "author_position": "middle",
                "author": {
                    "id": "https://openalex.org/A5012345678",
                    "display_name": "John Doe"
                },
                "institutions": [
                    {
                        "id": "https://openalex.org/I4210166737",
                        "display_name": "Example University",
                        "ror": "https://ror.org/01234abcd",
                        "country_code": "UK"
                    }
                ]
            },
            {
                "author_position": "last",
                "author": {
                    "id": "https://openalex.org/A5098765432",
                    "display_name": "Jane Smith"
                },
                "institutions": [
                    {
                        "id": "https://openalex.org/I4210166736",
                        "display_name": "Impact Technology Development (United States)",
                        "ror": "https://ror.org/05ppvf150",  # Duplicate ROR
                        "country_code": "US"
                    }
                ]
            }
        ]
    }
    mock_response.raise_for_status = Mock()
    
    session = create_session()
    
    with patch.object(session, 'get', return_value=mock_response):
        rors = get_rors_from_openalex('10.1007/s10851-019-00913-z', session)
    
    print(f"Input: DOI 10.1007/s10851-019-00913-z")
    print(f"Output RORs: {rors}")
    print(f"Note: Duplicate ROR '05ppvf150' appears only once in output")
    
    assert len(rors) == 2, f"Expected 2 unique RORs, got {len(rors)}"
    assert '05ppvf150' in rors, "Expected ROR '05ppvf150' in results"
    assert '01234abcd' in rors, "Expected ROR '01234abcd' in results"
    
    print("\n✓ Test passed!\n")


def test_ror_prefix_removal():
    """Test that ROR URLs are correctly cleaned."""
    print("=" * 60)
    print("Test 5: ROR prefix removal")
    print("=" * 60)
    
    # Mock OpenAlex API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "authorships": [
            {
                "author": {},
                "institutions": [
                    {
                        "ror": "https://ror.org/05ppvf150"
                    }
                ]
            }
        ]
    }
    mock_response.raise_for_status = Mock()
    
    session = create_session()
    
    with patch.object(session, 'get', return_value=mock_response):
        rors = get_rors_from_openalex('10.1234/test', session)
    
    print(f"Input: ROR URL 'https://ror.org/05ppvf150'")
    print(f"Output: ROR ID '{rors[0]}'")
    
    assert rors[0] == '05ppvf150', f"Expected cleaned ROR '05ppvf150', got '{rors[0]}'"
    assert not rors[0].startswith('https://'), "ROR should not contain 'https://' prefix"
    assert not rors[0].startswith('ror.org/'), "ROR should not contain 'ror.org/' prefix"
    
    print("\n✓ Test passed!\n")


def test_fallback_doi():
    """Test fallback DOI functionality when zbMATH API fails."""
    print("=" * 60)
    print("Test 6: Fallback DOI on API failure")
    print("=" * 60)
    
    # Mock zbMATH API response that returns 404
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = Exception("404 Not Found")
    
    session = create_session()
    
    # Create fallback DOIs dictionary
    fallback_dois = {
        '6676473': '10.1142/S0217732317300014',
        '7192482': '10.1007/s10851-019-00927-7'
    }
    
    with patch.object(session, 'get', return_value=mock_response):
        doi = get_doi_from_zbmath('6676473', session, fallback_dois)
    
    print(f"Input: an=6676473 (zbMATH API fails)")
    print(f"Output DOI from fallback: {doi}")
    
    assert doi == "10.1142/S0217732317300014", f"Expected fallback DOI 10.1142/S0217732317300014, got {doi}"
    
    print("\n✓ Test passed!\n")


def test_load_fallback_dois():
    """Test loading fallback DOIs from CSV file."""
    print("=" * 60)
    print("Test 7: Load fallback DOIs from CSV")
    print("=" * 60)
    
    # Load fallback DOIs
    fallback_dois = load_fallback_dois()
    
    print(f"Loaded {len(fallback_dois)} fallback DOIs")
    
    # Check that we have the expected DOIs
    assert len(fallback_dois) == 65, f"Expected 65 fallback DOIs, got {len(fallback_dois)}"
    assert '6676473' in fallback_dois, "Expected an=6676473 in fallback DOIs"
    assert fallback_dois['6676473'] == '10.1142/S0217732317300014', \
        f"Expected DOI 10.1142/S0217732317300014 for an=6676473, got {fallback_dois['6676473']}"
    assert '7347171' in fallback_dois, "Expected an=7347171 in fallback DOIs"
    assert fallback_dois['7347171'] == '10.1017/jfm.2021.280', \
        f"Expected DOI 10.1017/jfm.2021.280 for an=7347171, got {fallback_dois['7347171']}"
    # Check some of the newly added entries
    assert '8016648' in fallback_dois, "Expected an=8016648 in fallback DOIs"
    assert fallback_dois['8016648'] == '10.1007/978-3-031-78241-1', \
        f"Expected DOI 10.1007/978-3-031-78241-1 for an=8016648, got {fallback_dois['8016648']}"
    
    print("\n✓ Test passed!\n")


def main():
    """Run all tests."""
    print("\n")
    print("#" * 60)
    print("# zbMATH to OpenAlex Harvester - Mock Tests")
    print("#" * 60)
    print("\n")
    
    try:
        test_extract_unique_an_values()
        test_get_doi_from_zbmath_with_doi()
        test_get_doi_from_zbmath_with_arxiv()
        test_get_rors_from_openalex()
        test_ror_prefix_removal()
        test_fallback_doi()
        test_load_fallback_dois()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        print("\nThe script successfully:")
        print("  1. Extracts unique 'an' values from testset")
        print("  2. Queries zbMATH API and extracts DOI")
        print("  3. Converts arXiv identifiers to DOI format")
        print("  4. Queries OpenAlex API and extracts ROR IDs")
        print("  5. Removes 'https://ror.org/' prefix from RORs")
        print("  6. Handles duplicate RORs correctly")
        print("  7. Uses fallback DOIs when zbMATH API fails")
        print("  8. Loads fallback DOIs from CSV file")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
