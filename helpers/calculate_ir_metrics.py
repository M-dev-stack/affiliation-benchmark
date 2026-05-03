#!/usr/bin/env python3
"""
Calculate Information Retrieval metrics by comparing test results with truth table.

This script compares the ROR IDs from test results with ground truth (truth table)
and calculates standard IR metrics including precision, recall, F1-score, and accuracy.
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
    
    Each paper (identified by 'an') may have multiple affiliations, and each
    affiliation may map to one or more ROR IDs. This function calculates
    precision, recall, and F1-score for each paper by comparing all its
    predicted ROR IDs against the ground truth ROR IDs.
    
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
        # Standard IR convention for undefined cases:
        # - Precision = TP / (TP + FP):
        #   - When pred_set is empty: precision = 1.0 (convention for 0/0, no false positives)
        #   - When pred_set is not empty: precision = TP / |pred_set| (may be 0.0 if TP=0)
        # - Recall = TP / (TP + FN):
        #   - When true_set is empty: recall = 1.0 (convention for 0/0, nothing to miss)
        #   - When true_set is not empty: recall = TP / |true_set| (may be 0.0 if TP=0)
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
    
    Uses micro-averaging (aggregate TP, FP, FN across all papers) and
    macro-averaging (average metrics per paper).
    
    Note: Each 'an' represents a paper that may have multiple affiliations.
    Micro-averaging aggregates counts across all ROR IDs from all papers,
    while macro-averaging treats each paper equally regardless of how many
    ROR IDs it has.
    
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


def print_summary(metrics: Dict[str, float]):
    """
    Print a formatted summary of the metrics.
    
    Args:
        metrics: Dictionary of calculated metrics
    """
    print("\n" + "=" * 60)
    print("INFORMATION RETRIEVAL METRICS SUMMARY")
    print("=" * 60)
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
    print(f"  Total Papers: {metrics['num_papers']}")
    print("=" * 60)


def save_detailed_results(
    per_paper_metrics: Dict[str, Dict[str, float]],
    per_paper_counts: Dict[str, int],
    output_file: str
):
    """
    Save detailed per-paper metrics to a CSV file.
    
    Args:
        per_paper_metrics: Metrics per paper
        per_paper_counts: Counts per paper
        output_file: Path to output CSV file
    """
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = [
                'an', 'precision', 'recall', 'f1', 
                'tp', 'fp', 'fn', 'true_count', 'pred_count'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Sort by paper ID for consistent output
            for an in sorted(per_paper_metrics.keys(), key=lambda x: (int(x) if x.isdigit() else float('inf'), x)):
                metrics = per_paper_metrics[an]
                counts = per_paper_counts[an]
                
                writer.writerow({
                    'an': an,
                    'precision': f"{metrics['precision']:.4f}",
                    'recall': f"{metrics['recall']:.4f}",
                    'f1': f"{metrics['f1']:.4f}",
                    'tp': metrics['tp'],
                    'fp': metrics['fp'],
                    'fn': metrics['fn'],
                    'true_count': counts['true_count'],
                    'pred_count': counts['pred_count']
                })
        
        print(f"\nDetailed per-paper metrics saved to: {output_file}")
    
    except (IOError, csv.Error) as e:
        print(f"Error writing output file '{output_file}': {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 4:
        print("Usage: python calculate_ir_metrics.py <testset.csv> <truth_table.csv> <test_results.csv> [detailed_output.csv]")
        print("\nArguments:")
        print("  testset.csv         - Test set with paper IDs (must have 'an' column)")
        print("  truth_table.csv     - Ground truth ROR IDs (must have 'an' and 'ror_id' columns)")
        print("  test_results.csv    - Predicted ROR IDs (must have 'an' and 'ror_id' columns)")
        print("  detailed_output.csv - Optional: Save per-paper metrics to CSV")
        print("\nOutput:")
        print("  Prints overall metrics summary to stdout")
        print("  Optionally saves detailed per-paper metrics to CSV file")
        sys.exit(1)
    
    testset_file = sys.argv[1]
    truth_file = sys.argv[2]
    predicted_file = sys.argv[3]
    detailed_output = sys.argv[4] if len(sys.argv) > 4 else None
    
    # Load testset paper IDs
    print(f"Loading test set paper IDs from: {testset_file}")
    testset_papers = load_paper_ids(testset_file)
    print(f"Loaded {len(testset_papers)} distinct papers from test set")
    
    # Load data
    print(f"Loading ground truth from: {truth_file}")
    truth = load_ror_data(truth_file)
    
    print(f"Loading test results from: {predicted_file}")
    predicted = load_ror_data(predicted_file)
    
    # Calculate metrics
    print("\nCalculating metrics...")
    overall_metrics = calculate_overall_metrics(truth, predicted, testset_papers)
    
    # Print summary
    print_summary(overall_metrics)
    
    # Save detailed results if requested
    if detailed_output:
        per_paper_metrics, per_paper_counts = calculate_metrics_per_paper(truth, predicted, testset_papers)
        save_detailed_results(per_paper_metrics, per_paper_counts, detailed_output)


if __name__ == "__main__":
    main()
