#!/usr/bin/env python3
"""
Unit tests for System 3 analysis scripts.

Tests extract_missed_papers.py and calculate_adjusted_metrics.py

Run tests with: python3 -m unittest tests.test_system3_analysis
"""

import unittest
import csv
import os
import tempfile
import sys
from io import StringIO

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from system_3 import extract_missed_papers
from system_3 import calculate_adjusted_metrics


class TestExtractMissedPapers(unittest.TestCase):
    """Test the extract_missed_papers module."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_test_log(self, filename, content):
        """Helper to create test log files."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def test_extract_404_errors(self):
        """Test extraction of AN values from 404 error lines."""
        log_content = """[1/1008] Processing an=7192470
Found DOI for an=7192470: 10.1515/conop-2019-0009
[2/1008] Processing an=7192482
Error querying zbMATH API for an=7192482: 404 Client Error: Not Found for url: https://api.zbmath.org/v1/document/7192482
Skipping an=7192482: No DOI found
[3/1008] Processing an=7192483
Found DOI for an=7192483: 10.1007/s10851-019-00926-8
[4/1008] Processing an=7192714
Error querying zbMATH API for an=7192714: 404 Client Error: Not Found for url: https://api.zbmath.org/v1/document/7192714
Skipping an=7192714: No DOI found
"""
        log_file = self._create_test_log('test.log', log_content)
        
        missed_papers = extract_missed_papers.extract_missed_papers(log_file)
        
        self.assertEqual(len(missed_papers), 2)
        self.assertIn('7192482', missed_papers)
        self.assertIn('7192714', missed_papers)
    
    def test_no_errors(self):
        """Test log file with no 404 errors."""
        log_content = """[1/1008] Processing an=7192470
Found DOI for an=7192470: 10.1515/conop-2019-0009
[2/1008] Processing an=7192483
Found DOI for an=7192483: 10.1007/s10851-019-00926-8
"""
        log_file = self._create_test_log('test.log', log_content)
        
        missed_papers = extract_missed_papers.extract_missed_papers(log_file)
        
        self.assertEqual(len(missed_papers), 0)
    
    def test_save_to_csv(self):
        """Test saving missed papers to CSV."""
        missed_papers = ['7192482', '7192714', '7192715']
        output_file = os.path.join(self.temp_dir, 'missed.csv')
        
        extract_missed_papers.save_to_csv(missed_papers, output_file)
        
        # Read back the CSV
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]['an'], '7192482')
        self.assertEqual(rows[1]['an'], '7192714')
        self.assertEqual(rows[2]['an'], '7192715')


class TestCalculateAdjustedMetrics(unittest.TestCase):
    """Test the calculate_adjusted_metrics module."""
    
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
            if rows and 'ror_id' in rows[0]:
                fieldnames = ['an', 'ror_id']
            else:
                fieldnames = ['an']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return filepath
    
    def test_load_paper_ids(self):
        """Test loading paper IDs from CSV."""
        filepath = self._create_test_csv('papers.csv', [
            {'an': '1'},
            {'an': '2'},
            {'an': '3'}
        ])
        
        paper_ids = calculate_adjusted_metrics.load_paper_ids(filepath)
        
        self.assertEqual(len(paper_ids), 3)
        self.assertIn('1', paper_ids)
        self.assertIn('2', paper_ids)
        self.assertIn('3', paper_ids)
    
    def test_calculate_metrics_with_exclusions(self):
        """Test metric calculation excluding certain papers."""
        # Create test data
        truth_data = {
            '1': {'ror_a', 'ror_b'},
            '2': {'ror_c'},
            '3': {'ror_d', 'ror_e'},  # This will be excluded
        }
        predicted_data = {
            '1': {'ror_a', 'ror_b'},
            '2': {'ror_c', 'ror_x'},  # Has false positive
            '3': {'ror_x'},  # This will be excluded
        }
        testset_papers = {'1', '2'}  # Exclude paper 3
        
        metrics = calculate_adjusted_metrics.calculate_overall_metrics(
            truth_data, predicted_data, testset_papers
        )
        
        # Check that paper 3 is excluded
        self.assertEqual(metrics['num_papers'], 2)
        
        # Paper 1: TP=2, FP=0, FN=0
        # Paper 2: TP=1, FP=1, FN=0
        # Total: TP=3, FP=1, FN=0
        self.assertEqual(metrics['total_tp'], 3)
        self.assertEqual(metrics['total_fp'], 1)
        self.assertEqual(metrics['total_fn'], 0)
        
        # Micro precision = 3/(3+1) = 0.75
        # Micro recall = 3/(3+0) = 1.0
        self.assertAlmostEqual(metrics['micro_precision'], 0.75)
        self.assertAlmostEqual(metrics['micro_recall'], 1.0)
    
    def test_metrics_all_papers_processed(self):
        """Test metrics when no papers are excluded."""
        truth_data = {
            '1': {'ror_a'},
            '2': {'ror_b'},
        }
        predicted_data = {
            '1': {'ror_a'},
            '2': {'ror_b'},
        }
        testset_papers = {'1', '2'}
        
        metrics = calculate_adjusted_metrics.calculate_overall_metrics(
            truth_data, predicted_data, testset_papers
        )
        
        # Perfect predictions
        self.assertEqual(metrics['total_tp'], 2)
        self.assertEqual(metrics['total_fp'], 0)
        self.assertEqual(metrics['total_fn'], 0)
        self.assertAlmostEqual(metrics['micro_precision'], 1.0)
        self.assertAlmostEqual(metrics['micro_recall'], 1.0)
        self.assertAlmostEqual(metrics['micro_f1'], 1.0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the full workflow."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_full_workflow(self):
        """Test extracting missed papers and calculating adjusted metrics."""
        # Create test log with 404 errors
        log_content = """[1/3] Processing an=1
Found DOI for an=1: 10.1234/example1
[2/3] Processing an=2
Error querying zbMATH API for an=2: 404 Client Error: Not Found for url: https://api.zbmath.org/v1/document/2
[3/3] Processing an=3
Found DOI for an=3: 10.1234/example3
"""
        log_file = os.path.join(self.temp_dir, 'run.log')
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        # Extract missed papers
        missed_papers = extract_missed_papers.extract_missed_papers(log_file)
        self.assertEqual(missed_papers, ['2'])
        
        # Create test data files
        testset_file = os.path.join(self.temp_dir, 'testset.csv')
        with open(testset_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['an'])
            writer.writeheader()
            writer.writerows([{'an': '1'}, {'an': '2'}, {'an': '3'}])
        
        truth_file = os.path.join(self.temp_dir, 'truth.csv')
        with open(truth_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['an', 'ror_id'])
            writer.writeheader()
            writer.writerows([
                {'an': '1', 'ror_id': 'ror_a'},
                {'an': '2', 'ror_id': 'ror_b'},  # This paper was missed
                {'an': '3', 'ror_id': 'ror_c'},
            ])
        
        predicted_file = os.path.join(self.temp_dir, 'predicted.csv')
        with open(predicted_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['an', 'ror_id'])
            writer.writeheader()
            writer.writerows([
                {'an': '1', 'ror_id': 'ror_a'},
                # Paper 2 has no predictions (was missed)
                {'an': '3', 'ror_id': 'ror_c'},
            ])
        
        # Load data
        testset_papers = calculate_adjusted_metrics.load_paper_ids(testset_file)
        missed_paper_set = set(missed_papers)
        adjusted_testset = testset_papers - missed_paper_set
        
        truth = calculate_adjusted_metrics.load_ror_data(truth_file)
        predicted = calculate_adjusted_metrics.load_ror_data(predicted_file)
        
        # Calculate metrics
        metrics = calculate_adjusted_metrics.calculate_overall_metrics(
            truth, predicted, adjusted_testset
        )
        
        # Should only evaluate papers 1 and 3 (paper 2 excluded)
        self.assertEqual(metrics['num_papers'], 2)
        self.assertEqual(metrics['total_tp'], 2)  # Both papers correctly predicted
        self.assertEqual(metrics['total_fp'], 0)
        self.assertEqual(metrics['total_fn'], 0)
        self.assertAlmostEqual(metrics['micro_recall'], 1.0)


if __name__ == '__main__':
    unittest.main()
