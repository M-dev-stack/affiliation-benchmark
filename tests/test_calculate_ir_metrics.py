#!/usr/bin/env python3
"""
Unit tests for calculate_ir_metrics.py

Run tests with: python3 -m unittest test_calculate_ir_metrics.py
"""

import unittest
import csv
import os
import tempfile
import sys
from unittest.mock import patch
from io import StringIO
from helpers import calculate_ir_metrics


class TestLoadRorData(unittest.TestCase):
    """Test the load_ror_data function."""
    
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
            writer = csv.DictWriter(f, fieldnames=['an', 'ror_id'])
            writer.writeheader()
            writer.writerows(rows)
        return filepath
    
    def test_load_basic_data(self):
        """Test loading basic ROR data."""
        filepath = self._create_test_csv('test.csv', [
            {'an': '1', 'ror_id': 'abc123'},
            {'an': '1', 'ror_id': 'def456'},
            {'an': '2', 'ror_id': 'ghi789'}
        ])
        
        data = calculate_ir_metrics.load_ror_data(filepath)
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data['1'], {'abc123', 'def456'})
        self.assertEqual(data['2'], {'ghi789'})
    
    def test_load_empty_ror_ids(self):
        """Test that empty ROR IDs are ignored."""
        filepath = self._create_test_csv('test.csv', [
            {'an': '1', 'ror_id': 'abc123'},
            {'an': '1', 'ror_id': ''},
            {'an': '2', 'ror_id': 'def456'}
        ])
        
        data = calculate_ir_metrics.load_ror_data(filepath)
        
        self.assertEqual(data['1'], {'abc123'})
        self.assertEqual(data['2'], {'def456'})
    
    def test_load_whitespace_handling(self):
        """Test that whitespace is stripped."""
        filepath = self._create_test_csv('test.csv', [
            {'an': ' 1 ', 'ror_id': ' abc123 '},
            {'an': '1', 'ror_id': 'def456'}
        ])
        
        data = calculate_ir_metrics.load_ror_data(filepath)
        
        self.assertEqual(data['1'], {'abc123', 'def456'})
    
    def test_missing_file(self):
        """Test error handling for missing file."""
        with self.assertRaises(SystemExit):
            calculate_ir_metrics.load_ror_data('nonexistent.csv')
    
    def test_invalid_columns(self):
        """Test error handling for CSV with wrong columns."""
        filepath = os.path.join(self.temp_dir, 'invalid.csv')
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['wrong', 'columns'])
            writer.writeheader()
        
        with self.assertRaises(SystemExit):
            calculate_ir_metrics.load_ror_data(filepath)


class TestLoadPaperIds(unittest.TestCase):
    """Test the load_paper_ids function."""
    
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
    
    def test_load_basic_paper_ids(self):
        """Test loading basic paper IDs."""
        filepath = self._create_test_csv('test.csv', [
            {'an': '1', 'aff_str': 'University A'},
            {'an': '1', 'aff_str': 'University B'},
            {'an': '2', 'aff_str': 'University C'}
        ])
        
        paper_ids = calculate_ir_metrics.load_paper_ids(filepath)
        
        self.assertEqual(len(paper_ids), 2)
        self.assertIn('1', paper_ids)
        self.assertIn('2', paper_ids)
    
    def test_load_empty_paper_ids(self):
        """Test that empty paper IDs are ignored."""
        filepath = self._create_test_csv('test.csv', [
            {'an': '1', 'aff_str': 'University A'},
            {'an': '', 'aff_str': 'University B'},
            {'an': '2', 'aff_str': 'University C'}
        ])
        
        paper_ids = calculate_ir_metrics.load_paper_ids(filepath)
        
        self.assertEqual(len(paper_ids), 2)
        self.assertIn('1', paper_ids)
        self.assertIn('2', paper_ids)
    
    def test_load_whitespace_handling(self):
        """Test that whitespace is stripped."""
        filepath = self._create_test_csv('test.csv', [
            {'an': ' 1 ', 'aff_str': 'University A'},
            {'an': '1', 'aff_str': 'University B'}
        ])
        
        paper_ids = calculate_ir_metrics.load_paper_ids(filepath)
        
        self.assertEqual(len(paper_ids), 1)
        self.assertIn('1', paper_ids)
    
    def test_missing_file(self):
        """Test error handling for missing file."""
        with self.assertRaises(SystemExit):
            calculate_ir_metrics.load_paper_ids('nonexistent.csv')
    
    def test_invalid_columns(self):
        """Test error handling for CSV with wrong columns."""
        filepath = os.path.join(self.temp_dir, 'invalid.csv')
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['wrong', 'columns'])
            writer.writeheader()
        
        with self.assertRaises(SystemExit):
            calculate_ir_metrics.load_paper_ids(filepath)


class TestCalculateMetricsPerPaper(unittest.TestCase):
    """Test the calculate_metrics_per_paper function."""
    
    def test_perfect_match(self):
        """Test metrics when prediction perfectly matches truth."""
        truth = {'1': {'abc', 'def'}}
        predicted = {'1': {'abc', 'def'}}
        
        metrics, counts = calculate_ir_metrics.calculate_metrics_per_paper(truth, predicted)
        
        self.assertEqual(metrics['1']['precision'], 1.0)
        self.assertEqual(metrics['1']['recall'], 1.0)
        self.assertEqual(metrics['1']['f1'], 1.0)
        self.assertEqual(metrics['1']['tp'], 2)
        self.assertEqual(metrics['1']['fp'], 0)
        self.assertEqual(metrics['1']['fn'], 0)
    
    def test_no_match(self):
        """Test metrics when there's no overlap."""
        truth = {'1': {'abc', 'def'}}
        predicted = {'1': {'ghi', 'jkl'}}
        
        metrics, counts = calculate_ir_metrics.calculate_metrics_per_paper(truth, predicted)
        
        self.assertEqual(metrics['1']['precision'], 0.0)
        self.assertEqual(metrics['1']['recall'], 0.0)
        self.assertEqual(metrics['1']['f1'], 0.0)
        self.assertEqual(metrics['1']['tp'], 0)
        self.assertEqual(metrics['1']['fp'], 2)
        self.assertEqual(metrics['1']['fn'], 2)
    
    def test_partial_match(self):
        """Test metrics with partial overlap."""
        truth = {'1': {'abc', 'def', 'ghi'}}
        predicted = {'1': {'abc', 'def'}}
        
        metrics, counts = calculate_ir_metrics.calculate_metrics_per_paper(truth, predicted)
        
        # Precision: 2/2 = 1.0 (all predicted are correct)
        # Recall: 2/3 = 0.666... (2 out of 3 true items found)
        self.assertEqual(metrics['1']['precision'], 1.0)
        self.assertAlmostEqual(metrics['1']['recall'], 2/3, places=3)
        self.assertAlmostEqual(metrics['1']['f1'], 0.8, places=3)
        self.assertEqual(metrics['1']['tp'], 2)
        self.assertEqual(metrics['1']['fp'], 0)
        self.assertEqual(metrics['1']['fn'], 1)
    
    def test_empty_prediction(self):
        """Test metrics when prediction is empty."""
        truth = {'1': {'abc', 'def'}}
        predicted = {'1': set()}
        
        metrics, counts = calculate_ir_metrics.calculate_metrics_per_paper(truth, predicted)
        
        # When pred_set is empty, precision = 1.0 (no false positives)
        self.assertEqual(metrics['1']['precision'], 1.0)
        self.assertEqual(metrics['1']['recall'], 0.0)
        self.assertEqual(metrics['1']['f1'], 0.0)
        self.assertEqual(metrics['1']['tp'], 0)
        self.assertEqual(metrics['1']['fp'], 0)
        self.assertEqual(metrics['1']['fn'], 2)
    
    def test_empty_truth(self):
        """Test metrics when truth is empty (no ground truth for this paper)."""
        truth = {'1': set()}
        predicted = {'1': {'abc', 'def'}}
        
        metrics, counts = calculate_ir_metrics.calculate_metrics_per_paper(truth, predicted)
        
        # When true_set is empty, recall = 1.0 (nothing to miss)
        self.assertEqual(metrics['1']['precision'], 0.0)
        self.assertEqual(metrics['1']['recall'], 1.0)
        self.assertEqual(metrics['1']['f1'], 0.0)
        self.assertEqual(metrics['1']['tp'], 0)
        self.assertEqual(metrics['1']['fp'], 2)
        self.assertEqual(metrics['1']['fn'], 0)
    
    def test_both_empty(self):
        """Test metrics when both truth and prediction are empty (perfect match)."""
        truth = {'1': set()}
        predicted = {'1': set()}
        
        metrics, counts = calculate_ir_metrics.calculate_metrics_per_paper(truth, predicted)
        
        # Standard IR convention: when both are empty, precision=1.0 and recall=1.0
        # This represents a perfect prediction (no false positives, no false negatives)
        self.assertEqual(metrics['1']['precision'], 1.0)
        self.assertEqual(metrics['1']['recall'], 1.0)
        self.assertEqual(metrics['1']['f1'], 1.0)
        self.assertEqual(metrics['1']['tp'], 0)
        self.assertEqual(metrics['1']['fp'], 0)
        self.assertEqual(metrics['1']['fn'], 0)
    
    def test_multiple_papers(self):
        """Test metrics with multiple papers."""
        truth = {
            '1': {'abc'},
            '2': {'def', 'ghi'}
        }
        predicted = {
            '1': {'abc', 'xyz'},
            '2': {'def'}
        }
        
        metrics, counts = calculate_ir_metrics.calculate_metrics_per_paper(truth, predicted)
        
        # Paper 1: TP=1, FP=1, FN=0
        self.assertEqual(metrics['1']['tp'], 1)
        self.assertEqual(metrics['1']['fp'], 1)
        self.assertEqual(metrics['1']['fn'], 0)
        self.assertAlmostEqual(metrics['1']['precision'], 0.5, places=3)
        self.assertEqual(metrics['1']['recall'], 1.0)
        
        # Paper 2: TP=1, FP=0, FN=1
        self.assertEqual(metrics['2']['tp'], 1)
        self.assertEqual(metrics['2']['fp'], 0)
        self.assertEqual(metrics['2']['fn'], 1)
        self.assertEqual(metrics['2']['precision'], 1.0)
        self.assertAlmostEqual(metrics['2']['recall'], 0.5, places=3)


class TestCalculateOverallMetrics(unittest.TestCase):
    """Test the calculate_overall_metrics function."""
    
    def test_micro_averaging(self):
        """Test micro-averaged metrics calculation."""
        truth = {
            '1': {'abc'},
            '2': {'def', 'ghi'}
        }
        predicted = {
            '1': {'abc', 'xyz'},
            '2': {'def'}
        }
        
        metrics = calculate_ir_metrics.calculate_overall_metrics(truth, predicted)
        
        # Total: TP=2, FP=1, FN=1
        # Micro precision: 2/(2+1) = 0.666...
        # Micro recall: 2/(2+1) = 0.666...
        self.assertAlmostEqual(metrics['micro_precision'], 2/3, places=3)
        self.assertAlmostEqual(metrics['micro_recall'], 2/3, places=3)
        self.assertEqual(metrics['total_tp'], 2)
        self.assertEqual(metrics['total_fp'], 1)
        self.assertEqual(metrics['total_fn'], 1)
    
    def test_macro_averaging(self):
        """Test macro-averaged metrics calculation."""
        truth = {
            '1': {'abc'},
            '2': {'def'}
        }
        predicted = {
            '1': {'abc'},  # Perfect match: P=1.0, R=1.0
            '2': set()     # No predictions: P=1.0 (no FP), R=0.0 (missed all)
        }
        
        metrics = calculate_ir_metrics.calculate_overall_metrics(truth, predicted)
        
        # Macro precision: (1.0 + 1.0) / 2 = 1.0 (with new convention)
        # Macro recall: (1.0 + 0.0) / 2 = 0.5
        self.assertAlmostEqual(metrics['macro_precision'], 1.0, places=3)
        self.assertAlmostEqual(metrics['macro_recall'], 0.5, places=3)
    
    def test_with_testset_papers(self):
        """Test that testset_papers parameter correctly limits evaluation."""
        truth = {
            '1': {'abc'},
            '2': {'def'}
        }
        predicted = {
            '1': {'abc'},
            '2': {'def'},
            '3': {'ghi'}  # Extra paper not in testset
        }
        testset_papers = {'1', '2', '4'}  # Paper 4 has no truth or predictions
        
        metrics = calculate_ir_metrics.calculate_overall_metrics(truth, predicted, testset_papers)
        
        # Should only evaluate papers 1, 2, and 4 (from testset)
        # Paper 3 should be ignored even though it has predictions
        # Paper 4 should be included with TP=0, FP=0, FN=0
        self.assertEqual(metrics['num_papers'], 3)
        self.assertEqual(metrics['total_tp'], 2)  # Papers 1 and 2
        self.assertEqual(metrics['total_fp'], 0)
        self.assertEqual(metrics['total_fn'], 0)


class TestSaveDetailedResults(unittest.TestCase):
    """Test the save_detailed_results function."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_save_results(self):
        """Test saving detailed results to CSV."""
        per_paper_metrics = {
            '1': {'precision': 0.5, 'recall': 1.0, 'f1': 0.667, 'tp': 1, 'fp': 1, 'fn': 0},
            '2': {'precision': 1.0, 'recall': 0.5, 'f1': 0.667, 'tp': 1, 'fp': 0, 'fn': 1}
        }
        per_paper_counts = {
            '1': {'true_count': 1, 'pred_count': 2},
            '2': {'true_count': 2, 'pred_count': 1}
        }
        
        output_file = os.path.join(self.temp_dir, 'output.csv')
        calculate_ir_metrics.save_detailed_results(per_paper_metrics, per_paper_counts, output_file)
        
        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['an'], '1')
        self.assertEqual(rows[0]['tp'], '1')
        self.assertEqual(rows[1]['an'], '2')
        self.assertEqual(rows[1]['tp'], '1')


class TestMain(unittest.TestCase):
    """Test the main function."""
    
    def test_no_arguments(self):
        """Test main function with no arguments."""
        with patch('sys.argv', ['calculate_ir_metrics.py']):
            with self.assertRaises(SystemExit):
                calculate_ir_metrics.main()
    
    def test_insufficient_arguments(self):
        """Test main function with insufficient arguments."""
        with patch('sys.argv', ['calculate_ir_metrics.py', 'truth.csv']):
            with self.assertRaises(SystemExit):
                calculate_ir_metrics.main()
    
    @patch('helpers.calculate_ir_metrics.load_paper_ids')
    @patch('helpers.calculate_ir_metrics.load_ror_data')
    @patch('helpers.calculate_ir_metrics.calculate_overall_metrics')
    @patch('helpers.calculate_ir_metrics.print_summary')
    def test_basic_execution(self, mock_print, mock_calc, mock_load, mock_load_papers):
        """Test basic execution flow."""
        mock_load_papers.return_value = {'1'}  # testset papers
        mock_load.side_effect = [
            {'1': {'abc'}},  # truth
            {'1': {'abc'}}   # predicted
        ]
        mock_calc.return_value = {
            'micro_precision': 1.0,
            'micro_recall': 1.0,
            'micro_f1': 1.0,
            'macro_precision': 1.0,
            'macro_recall': 1.0,
            'macro_f1': 1.0,
            'total_tp': 1,
            'total_fp': 0,
            'total_fn': 0,
            'num_papers': 1
        }
        
        with patch('sys.argv', ['calculate_ir_metrics.py', 'testset.csv', 'truth.csv', 'pred.csv']):
            calculate_ir_metrics.main()
        
        mock_load_papers.assert_called_once()
        self.assertEqual(mock_load.call_count, 2)
        mock_calc.assert_called_once()
        mock_print.assert_called_once()


class TestPrintSummary(unittest.TestCase):
    """Test the print_summary function."""
    
    def test_print_output(self):
        """Test that summary is printed correctly."""
        metrics = {
            'micro_precision': 0.75,
            'micro_recall': 0.80,
            'micro_f1': 0.77,
            'macro_precision': 0.70,
            'macro_recall': 0.65,
            'macro_f1': 0.67,
            'total_tp': 100,
            'total_fp': 25,
            'total_fn': 20,
            'num_papers': 50
        }
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            calculate_ir_metrics.print_summary(metrics)
        
        output = captured_output.getvalue()
        
        # Verify key information is in output
        self.assertIn('INFORMATION RETRIEVAL METRICS', output)
        self.assertIn('0.7500', output)  # micro precision
        self.assertIn('0.8000', output)  # micro recall
        self.assertIn('100', output)     # TP
        self.assertIn('50', output)      # num papers


if __name__ == '__main__':
    unittest.main()
