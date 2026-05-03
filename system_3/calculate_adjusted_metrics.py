#!/usr/bin/env python3
"""
Calculate adjusted Information Retrieval metrics excluding missed papers.

This script is similar to helpers/calculate_ir_metrics.py but excludes
papers that were missed (e.g., due to 404 errors from zbMATH API).
This allows us to calculate the "true" recall rate for papers that
System 3 could actually process.
"""

import csv
import sys
from typing import Dict, Set, Tuple
from collections import defaultdict


def load_ror_data(filepath: str) -> Dict[str, Set[str]]:
    """
    Load ROR ID data from CSV file.
    
    Args:
        filepath: Path to CSV file with 'an' and 'ror_id' columns
        
    Returns:
        Dictionary mapping 'an' values to sets of ROR IDs
    """
    data = defaultdict(set)
    
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Validate required columns
            if 'an' not in reader.fieldnames or 'ror_id' not in reader.fieldnames:
                print(f"Error: CSV file '{filepath}' must have 'an' and 'ror_id' columns", 
                      file=sys.stderr)
                sys.exit(1)
            
            for row in reader:
                an = row['an'].strip()
                ror_id = row['ror_id'].strip()
                
                # Only add non-empty ROR IDs
                if an and ror_id:
                    data[an].add(ror_id)
    
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        sys.exit(1)
    except (IOError, csv.Error) as e:
        print(f"Error reading CSV file '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)
    
    return data


def load_paper_ids(filepath: str) -> Set[str]:
    """
    Load paper IDs (an values) from CSV file.
    
    Args:
        filepath: Path to CSV file with 'an' column
        
    Returns:
        Set of paper IDs (an values)
    """
    paper_ids = set()
    
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            # Validate required column
            if 'an' not in reader.fieldnames:
                print(f"Error: CSV file '{filepath}' must have 'an' column", 
                      file=sys.stderr)
                sys.exit(1)
            
            for row in reader:
                an = row['an'].strip()
                if an:
                    paper_ids.add(an)
    
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found", file=sys.stderr)
        sys.exit(1)
    except (IOError, csv.Error) as e:
        print(f"Error reading CSV file '{filepath}': {e}", file=sys.stderr)
        sys.exit(1)
    
    return paper_ids


def calculate_metrics_per_paper(
    truth: Dict[str, Set[str]], 
    predicted: Dict[str, Set[str]],
    testset_papers: Set[str] = None
) -> Tuple[Dict[str, Dict[str, float]], Dict[str, int]]:
    """
    Calculate metrics for each paper.
    
    Args:
        truth: Ground truth ROR IDs per paper (keyed by 'an')
        predicted: Predicted ROR IDs per paper (keyed by 'an')
        testset_papers: Optional set of paper IDs to evaluate. If provided,
                        only these papers will be included in the evaluation.
        
    Returns:
        Tuple of (per-paper metrics dict, per-paper counts dict)
    """
    per_paper_metrics = {}
    per_paper_counts = {}
    
    # Get all paper IDs - use testset_papers if provided, otherwise union of truth and predicted
    if testset_papers is not None:
        all_ans = testset_papers
    else:
        all_ans = set(truth.keys()) | set(predicted.keys())
    
    for an in all_ans:
        true_set = truth.get(an, set())
        pred_set = predicted.get(an, set())
        
        # Calculate TP, FP, FN
        true_positives = len(true_set & pred_set)
        false_positives = len(pred_set - true_set)
        false_negatives = len(true_set - pred_set)
        
        # Calculate precision and recall for this paper
        precision = true_positives / len(pred_set) if pred_set else 1.0
        recall = true_positives / len(true_set) if true_set else 1.0
        
        # Calculate F1-score
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        
        per_paper_metrics[an] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': true_positives,
            'fp': false_positives,
            'fn': false_negatives
        }
        
        per_paper_counts[an] = {
            'true_count': len(true_set),
            'pred_count': len(pred_set)
        }
    
    return per_paper_metrics, per_paper_counts


def calculate_overall_metrics(
    truth: Dict[str, Set[str]], 
    predicted: Dict[str, Set[str]],
    testset_papers: Set[str] = None
) -> Dict[str, float]:
    """
    Calculate overall IR metrics.
    
    Args:
        truth: Ground truth ROR IDs per paper (keyed by 'an')
        predicted: Predicted ROR IDs per paper (keyed by 'an')
        testset_papers: Optional set of paper IDs to evaluate. If provided,
                        only these papers will be included in the evaluation.
        
    Returns:
        Dictionary with overall metrics
    """
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    # Get all paper IDs - use testset_papers if provided, otherwise union of truth and predicted
    if testset_papers is not None:
        all_ans = testset_papers
    else:
        all_ans = set(truth.keys()) | set(predicted.keys())
    
    for an in all_ans:
        true_set = truth.get(an, set())
        pred_set = predicted.get(an, set())
        
        tp = len(true_set & pred_set)
        fp = len(pred_set - true_set)
        fn = len(true_set - pred_set)
        
        total_tp += tp
        total_fp += fp
        total_fn += fn
    
    # Calculate micro-averaged metrics
    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    
    # Calculate macro-averaged metrics (average of per-paper metrics)
    per_paper_metrics, _ = calculate_metrics_per_paper(truth, predicted, testset_papers)
    
    if per_paper_metrics:
        macro_precision = sum(m['precision'] for m in per_paper_metrics.values()) / len(per_paper_metrics)
        macro_recall = sum(m['recall'] for m in per_paper_metrics.values()) / len(per_paper_metrics)
        macro_f1 = sum(m['f1'] for m in per_paper_metrics.values()) / len(per_paper_metrics)
    else:
        macro_precision = macro_recall = macro_f1 = 0.0
    
    return {
        'micro_precision': precision,
        'micro_recall': recall,
        'micro_f1': f1,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1,
        'total_tp': total_tp,
        'total_fp': total_fp,
        'total_fn': total_fn,
        'num_papers': len(all_ans)
    }


def print_summary(metrics: Dict[str, float], excluded_papers: int = 0):
    """
    Print a formatted summary of the metrics.
    
    Args:
        metrics: Dictionary of calculated metrics
        excluded_papers: Number of papers excluded from evaluation
    """
    print("\n" + "=" * 60)
    print("ADJUSTED INFORMATION RETRIEVAL METRICS SUMMARY")
    print("(Excluding papers with zbMATH API 404 errors)")
    print("=" * 60)
    
    if excluded_papers > 0:
        print(f"\nExcluded Papers: {excluded_papers}")
    
    print("\nMicro-averaged Metrics (aggregated over all ROR IDs):")
    print(f"  Precision: {metrics['micro_precision']:.4f}")
    print(f"  Recall:    {metrics['micro_recall']:.4f}")
    print(f"  F1-Score:  {metrics['micro_f1']:.4f}")
    
    print("\nMacro-averaged Metrics (averaged per paper):")
    print(f"  Precision: {metrics['macro_precision']:.4f}")
    print(f"  Recall:    {metrics['macro_recall']:.4f}")
    print(f"  F1-Score:  {metrics['macro_f1']:.4f}")
    
    print("\nCounts:")
    print(f"  True Positives:  {metrics['total_tp']}")
    print(f"  False Positives: {metrics['total_fp']}")
    print(f"  False Negatives: {metrics['total_fn']}")
    print(f"  Total Papers (after exclusion): {metrics['num_papers']}")
    print("=" * 60)


def main():
    """Main entry point."""
    if len(sys.argv) < 5:
        print("Usage: python calculate_adjusted_metrics.py <testset.csv> <truth_table.csv> <test_results.csv> <missed_papers.csv>")
        print("\nArguments:")
        print("  testset.csv         - Test set with paper IDs (must have 'an' column)")
        print("  truth_table.csv     - Ground truth ROR IDs (must have 'an' and 'ror_id' columns)")
        print("  test_results.csv    - Predicted ROR IDs (must have 'an' and 'ror_id' columns)")
        print("  missed_papers.csv   - Papers to exclude from evaluation (must have 'an' column)")
        print("\nOutput:")
        print("  Prints adjusted metrics summary to stdout")
        sys.exit(1)
    
    testset_file = sys.argv[1]
    truth_file = sys.argv[2]
    predicted_file = sys.argv[3]
    missed_papers_file = sys.argv[4]
    
    # Load testset paper IDs
    print(f"Loading test set paper IDs from: {testset_file}")
    testset_papers = load_paper_ids(testset_file)
    print(f"Loaded {len(testset_papers)} distinct papers from test set")
    
    # Load missed papers
    print(f"Loading missed papers from: {missed_papers_file}")
    missed_papers = load_paper_ids(missed_papers_file)
    print(f"Loaded {len(missed_papers)} missed papers to exclude")
    
    # Exclude missed papers from testset
    adjusted_testset = testset_papers - missed_papers
    print(f"Adjusted test set contains {len(adjusted_testset)} papers (excluded {len(missed_papers)} papers)")
    
    # Load data
    print(f"Loading ground truth from: {truth_file}")
    truth = load_ror_data(truth_file)
    
    print(f"Loading test results from: {predicted_file}")
    predicted = load_ror_data(predicted_file)
    
    # Calculate metrics
    print("\nCalculating adjusted metrics...")
    overall_metrics = calculate_overall_metrics(truth, predicted, adjusted_testset)
    
    # Print summary
    print_summary(overall_metrics, len(missed_papers))


if __name__ == "__main__":
    main()
