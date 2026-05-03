#!/usr/bin/env python3
"""
Unit tests for filter_csv.py

Run tests with: python3 -m unittest test_filter_csv.py
"""

import unittest
import csv
import os
import sys
import tempfile
import shutil
from unittest.mock import patch
from helpers import filter_csv


class TestFilterCsv(unittest.TestCase):
    """Test the filter_csv function."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_csv(self, filename, rows):
        """Helper to create test CSV files."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['an', 'ror_id'])
            writer.writeheader()
            writer.writerows(rows)
        return filepath
    
    def _read_csv(self, filepath):
        """Helper to read CSV file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def test_removes_duplicate_rows(self):
        """Test that duplicate rows are removed."""
        input_file = self._create_test_csv('input.csv', [
            {'an': '1', 'ror_id': '052gg0110'},
            {'an': '1', 'ror_id': '052gg0110'},  # Duplicate
            {'an': '2', 'ror_id': '042nb2s44'}
        ])
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        filter_csv.filter_csv(input_file, output_file)
        
        rows = self._read_csv(output_file)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['an'], '1')
        self.assertEqual(rows[0]['ror_id'], '052gg0110')
        self.assertEqual(rows[1]['an'], '2')
        self.assertEqual(rows[1]['ror_id'], '042nb2s44')
    
    def test_removes_rows_with_empty_ror_id(self):
        """Test that rows with only 'an' and empty 'ror_id' are removed."""
        input_file = self._create_test_csv('input.csv', [
            {'an': '1', 'ror_id': '052gg0110'},
            {'an': '2', 'ror_id': ''},  # Should be removed
            {'an': '3', 'ror_id': '042nb2s44'}
        ])
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        filter_csv.filter_csv(input_file, output_file)
        
        rows = self._read_csv(output_file)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['an'], '1')
        self.assertEqual(rows[1]['an'], '3')
    
    def test_removes_both_duplicates_and_empty_ror_id(self):
        """Test that both duplicates and empty ror_id rows are removed."""
        input_file = self._create_test_csv('input.csv', [
            {'an': '1', 'ror_id': '052gg0110'},
            {'an': '1', 'ror_id': '052gg0110'},  # Duplicate
            {'an': '2', 'ror_id': ''},  # Empty ror_id
            {'an': '3', 'ror_id': '042nb2s44'},
            {'an': '3', 'ror_id': '042nb2s44'},  # Duplicate
        ])
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        filter_csv.filter_csv(input_file, output_file)
        
        rows = self._read_csv(output_file)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['an'], '1')
        self.assertEqual(rows[0]['ror_id'], '052gg0110')
        self.assertEqual(rows[1]['an'], '3')
        self.assertEqual(rows[1]['ror_id'], '042nb2s44')
    
    def test_keeps_multiple_ror_ids_for_same_an(self):
        """Test that different ror_ids for the same 'an' are kept."""
        input_file = self._create_test_csv('input.csv', [
            {'an': '1', 'ror_id': '052gg0110'},
            {'an': '1', 'ror_id': '042nb2s44'},  # Different ror_id, should be kept
            {'an': '1', 'ror_id': '052gg0110'},  # Duplicate of first row
        ])
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        filter_csv.filter_csv(input_file, output_file)
        
        rows = self._read_csv(output_file)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['an'], '1')
        self.assertEqual(rows[0]['ror_id'], '052gg0110')
        self.assertEqual(rows[1]['an'], '1')
        self.assertEqual(rows[1]['ror_id'], '042nb2s44')
    
    def test_empty_file(self):
        """Test handling of empty CSV file."""
        input_file = self._create_test_csv('input.csv', [])
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        filter_csv.filter_csv(input_file, output_file)
        
        rows = self._read_csv(output_file)
        self.assertEqual(len(rows), 0)
    
    def test_missing_input_file(self):
        """Test error handling for missing input file."""
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        with self.assertRaises(SystemExit):
            filter_csv.filter_csv('nonexistent.csv', output_file)
    
    def test_invalid_csv_missing_columns(self):
        """Test error handling for CSV with missing required columns."""
        # Create CSV with wrong columns
        filepath = os.path.join(self.temp_dir, 'invalid.csv')
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['wrong', 'columns'])
            writer.writeheader()
        
        output_file = os.path.join(self.temp_dir, 'output.csv')
        
        with self.assertRaises(SystemExit):
            filter_csv.filter_csv(filepath, output_file)


class TestMain(unittest.TestCase):
    """Test the main function."""
    
    def test_no_arguments(self):
        """Test main function with no arguments."""
        with patch('sys.argv', ['filter_csv.py']):
            with self.assertRaises(SystemExit):
                filter_csv.main()
    
    def test_insufficient_arguments(self):
        """Test main function with insufficient arguments."""
        with patch('sys.argv', ['filter_csv.py', 'input.csv']):
            with self.assertRaises(SystemExit):
                filter_csv.main()


if __name__ == '__main__':
    unittest.main()
