#!/usr/bin/env python3
"""
Unit tests for ror_harvester.py

Run tests with: python3 -m unittest test_ror_harvester.py
"""

import unittest
import csv
import os
import sys
import tempfile
from unittest.mock import patch, Mock
from system_2 import ror_harvester


class TestCreateSession(unittest.TestCase):
    """Test the create_session function."""
    
    def test_session_created(self):
        """Test that a session is created."""
        session = ror_harvester.create_session()
        self.assertIsNotNone(session)
        # Check that adapters are mounted
        self.assertIn('http://', session.adapters)
        self.assertIn('https://', session.adapters)


class TestQueryRorApi(unittest.TestCase):
    """Test the query_ror_api function."""
    
    @patch('requests.Session.get')
    def test_successful_query(self, mock_get):
        """Test successful API query returns ROR IDs."""
        # Mock API response for affiliation endpoint
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {
                    'chosen': True,
                    'organization': {'id': 'https://ror.org/052gg0110', 'name': 'University of Oxford'}
                },
                {
                    'chosen': True,
                    'organization': {'id': 'https://ror.org/123456789', 'name': 'Oxford College'}
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        session = ror_harvester.create_session()
        result = ror_harvester.query_ror_api("University of Oxford", session)
        
        self.assertEqual(len(result), 2)
        self.assertIn('052gg0110', result)
        self.assertIn('123456789', result)
    
    @patch('requests.Session.get')
    def test_successful_query_filters_unchosen(self, mock_get):
        """Test that only items with chosen=true are included."""
        # Mock API response with mixed chosen values
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [
                {
                    'chosen': True,
                    'organization': {'id': 'https://ror.org/052gg0110', 'name': 'University of Oxford'}
                },
                {
                    'chosen': False,
                    'organization': {'id': 'https://ror.org/999999999', 'name': 'Wrong Match'}
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        session = ror_harvester.create_session()
        result = ror_harvester.query_ror_api("University of Oxford", session)
        
        # Should only include the one with chosen=True
        self.assertEqual(len(result), 1)
        self.assertIn('052gg0110', result)
        self.assertNotIn('999999999', result)
    
    @patch('requests.Session.get')
    def test_no_results(self, mock_get):
        """Test API query with no results."""
        mock_response = Mock()
        mock_response.json.return_value = {'items': []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        session = ror_harvester.create_session()
        result = ror_harvester.query_ror_api("Nonexistent University", session)
        
        self.assertEqual(result, [])
    
    @patch('requests.Session.get')
    def test_api_timeout(self, mock_get):
        """Test API query handles timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("timeout")
        
        session = ror_harvester.create_session()
        result = ror_harvester.query_ror_api("Test University", session)
        
        self.assertEqual(result, [])
    
    @patch('requests.Session.get')
    def test_api_http_error(self, mock_get):
        """Test API query handles HTTP errors."""
        import requests
        mock_get.side_effect = requests.exceptions.HTTPError("500 Server Error")
        
        session = ror_harvester.create_session()
        result = ror_harvester.query_ror_api("Test University", session)
        
        self.assertEqual(result, [])
    
    def test_empty_affiliation_string(self):
        """Test that empty affiliation string returns empty list."""
        session = ror_harvester.create_session()
        result = ror_harvester.query_ror_api("", session)
        self.assertEqual(result, [])
    
    def test_whitespace_only(self):
        """Test that whitespace-only string returns empty list."""
        session = ror_harvester.create_session()
        result = ror_harvester.query_ror_api("   ", session)
        self.assertEqual(result, [])
    
    @patch('requests.Session.get')
    def test_special_characters_in_query(self, mock_get):
        """Test that special characters are properly handled in queries."""
        mock_response = Mock()
        mock_response.json.return_value = {'items': []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        session = ror_harvester.create_session()
        ror_harvester.query_ror_api("University & College", session)
        
        # Verify the request was made with proper params
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['params']['affiliation'], "University & College")


class TestProcessCsv(unittest.TestCase):
    """Test the process_csv function."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_csv(self, filename, rows):
        """Helper to create test CSV files."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['an', 'aff_str'])
            writer.writeheader()
            writer.writerows(rows)
        return filepath
    
    @patch('system_2.ror_harvester.query_ror_api')
    def test_basic_processing(self, mock_query):
        """Test basic CSV processing."""
        # Mock API responses (without https://ror.org/ prefix)
        mock_query.side_effect = [
            ['052gg0110'],
            ['042nb2s44']
        ]
        
        # Create input CSV
        input_file = self._create_test_csv('input.csv', [
            {'an': '1', 'aff_str': 'University of Oxford'},
            {'an': '2', 'aff_str': 'MIT'}
        ])
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        # Process CSV
        ror_harvester.process_csv(input_file, output_file)
        
        # Verify output
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['an'], '1')
        self.assertEqual(rows[0]['ror_id'], '052gg0110')
        self.assertEqual(rows[1]['an'], '2')
        self.assertEqual(rows[1]['ror_id'], '042nb2s44')
    
    @patch('system_2.ror_harvester.query_ror_api')
    def test_multiple_ror_ids(self, mock_query):
        """Test handling multiple ROR IDs for one affiliation - creates multiple rows."""
        # Mock API returning multiple IDs (without prefix)
        mock_query.return_value = [
            '111111111',
            '222222222'
        ]
        
        input_file = self._create_test_csv('input.csv', [
            {'an': '1', 'aff_str': 'Test University'}
        ])
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        ror_harvester.process_csv(input_file, output_file)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Should have 2 rows, one for each ROR ID
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['an'], '1')
        self.assertEqual(rows[0]['ror_id'], '111111111')
        self.assertEqual(rows[1]['an'], '1')
        self.assertEqual(rows[1]['ror_id'], '222222222')
    
    @patch('system_2.ror_harvester.query_ror_api')
    def test_no_ror_ids_found(self, mock_query):
        """Test handling when no ROR IDs are found."""
        mock_query.return_value = []
        
        input_file = self._create_test_csv('input.csv', [
            {'an': '1', 'aff_str': 'Unknown University'}
        ])
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        ror_harvester.process_csv(input_file, output_file)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(rows[0]['ror_id'], '')
    
    @patch('system_2.ror_harvester.query_ror_api')
    def test_empty_affiliation_string(self, mock_query):
        """Test handling empty affiliation strings."""
        mock_query.return_value = []
        
        input_file = self._create_test_csv('input.csv', [
            {'an': '1', 'aff_str': ''}
        ])
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        ror_harvester.process_csv(input_file, output_file)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(rows[0]['an'], '1')
        self.assertEqual(rows[0]['ror_id'], '')
    
    def test_missing_input_file(self):
        """Test error handling for missing input file."""
        with self.assertRaises(SystemExit):
            ror_harvester.process_csv('nonexistent.csv', 'output.csv')
    
    def test_invalid_csv_missing_columns(self):
        """Test error handling for CSV with missing required columns."""
        # Create CSV with wrong columns
        filepath = os.path.join(self.temp_dir, 'invalid.csv')
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['wrong', 'columns'])
            writer.writeheader()
        
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        with self.assertRaises(SystemExit):
            ror_harvester.process_csv(filepath, output_file)


class TestMain(unittest.TestCase):
    """Test the main function."""
    
    def test_no_arguments(self):
        """Test main function with no arguments."""
        with patch('sys.argv', ['ror_harvester.py']):
            with self.assertRaises(SystemExit):
                ror_harvester.main()
    
    def test_insufficient_arguments(self):
        """Test main function with insufficient arguments."""
        with patch('sys.argv', ['ror_harvester.py', 'input.csv']):
            with self.assertRaises(SystemExit):
                ror_harvester.main()
    
    @patch('system_2.ror_harvester.process_csv')
    def test_correct_arguments(self, mock_process):
        """Test main function with correct arguments."""
        with patch('sys.argv', ['ror_harvester.py', 'input.csv', 'output.csv']):
            ror_harvester.main()
            mock_process.assert_called_once_with('input.csv', 'output.csv')


if __name__ == '__main__':
    unittest.main()
