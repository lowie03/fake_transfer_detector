"""
Batch testing script for the Fake Transfer Detection System.
Tests multiple inputs and logs results to CSV.
"""

import pandas as pd
import os
import sys
from core.detector import FakeTransferDetector


def test_sms_csv(detector, csv_path, output_path='logs/batch_test_results.csv'):
    """
    Test the SMS pipeline on a CSV file of transactions.

    Args:
        detector: FakeTransferDetector instance
        csv_path: Path to test CSV with columns: description, is_legit (and optionally bank, amount, etc.)
        output_path: Path to save results
    """
    print(f"\n{'='*60}")
    print(f"BATCH TEST: SMS/CSV Pipeline")
    print(f"{'='*60}")

    df = pd.read_csv(csv_path)

    # Standardize column names
    if 'is_legit' in df.columns:
        df = df.rename(columns={'is_legit': 'label'})
    if 'sms_text' in df.columns:
        df = df.rename(columns={'sms_text': 'description'})

    print(f"Loaded: {len(df)} samples")
    print(f"Genuine: {sum(df['label']==0)}, Fake: {sum(df['label']==1)}")

    results = []
    correct = 0
    total = len(df)

    for idx, row in df.iterrows():
        # Pass full row if available, otherwise just text
        if 'bank' in df.columns:
            result = detector.verify_transaction(row.to_dict(), input_type='text')
        else:
            result = detector.verify_transaction(str(row['description']), input_type='text')

        pred_label = 1 if result['prediction'] == 'FAKE' else 0
        true_label = row['label']
        is_correct = pred_label == true_label

        if is_correct:
            correct += 1

        results.append({
            'input_text': str(row.get('description', ''))[:100],
            'true_label': 'FAKE' if true_label == 1 else 'GENUINE',
            'predicted_label': result['prediction'],
            'confidence': result['confidence'],
            'correct': '✅' if is_correct else '❌',
            'explanation': result['reason'],
            'pipeline': result['pipeline_used']
        })

        # Progress
        if (idx + 1) % 10 == 0:
            print(f"  Processed {idx+1}/{total}...")

    # Save results
    results_df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False)

    # Print summary
    accuracy = correct / total
    tp = sum(1 for r in results if r['true_label'] == 'FAKE' and r['predicted_label'] == 'FAKE')
    fp = sum(1 for r in results if r['true_label'] == 'GENUINE' and r['predicted_label'] == 'FAKE')
    fn = sum(1 for r in results if r['true_label'] == 'FAKE' and r['predicted_label'] == 'GENUINE')
    tn = sum(1 for r in results if r['true_label'] == 'GENUINE' and r['predicted_label'] == 'GENUINE')

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"{'='*60}")
    print(f"  Accuracy:  {accuracy:.4f} ({accuracy*100:.1f}%)")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1-Score:  {f1:.4f}")
    print(f"  TP={tp}, FP={fp}, FN={fn}, TN={tn}")
    print(f"\n  Results saved to: {output_path}")

    return results_df


def test_screenshots(detector, image_dir, output_path='logs/screenshot_test_results.csv'):
    """
    Test the screenshot pipeline on a directory of images.

    Args:
        detector: FakeTransferDetector instance
        image_dir: Directory with subfolders 'Fake/' and 'Genuine/'
        output_path: Path to save results
    """
    print(f"\n{'='*60}")
    print(f"BATCH TEST: Screenshot Pipeline")
    print(f"{'='*60}")

    results = []

    for label_folder in ['Genuine', 'Fake', 'genuine', 'fake', 'Real', 'real']:
        folder_path = os.path.join(image_dir, label_folder)
        if not os.path.exists(folder_path):
            continue

        true_label = 'FAKE' if 'fake' in label_folder.lower() else 'GENUINE'

        for filename in sorted(os.listdir(folder_path)):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue

            img_path = os.path.join(folder_path, filename)
            result = detector.verify_transaction(img_path, input_type='image')

            is_correct = result['prediction'] == true_label

            results.append({
                'image_name': filename,
                'true_label': true_label,
                'predicted_label': result['prediction'],
                'confidence': result['confidence'],
                'correct': '✅' if is_correct else '❌',
                'explanation': result['reason'],
                'pipeline': result['pipeline_used']
            })

    if results:
        results_df = pd.DataFrame(results)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        results_df.to_csv(output_path, index=False)

        correct = sum(1 for r in results if r['correct'] == '✅')
        print(f"  Tested: {len(results)} images")
        print(f"  Accuracy: {correct/len(results):.4f} ({correct}/{len(results)})")
        print(f"  Results saved to: {output_path}")

        return results_df
    else:
        print("  No images found in directory.")
        return pd.DataFrame()


if __name__ == '__main__':
    # Initialize detector
    detector = FakeTransferDetector(models_dir='models')

    # Test SMS if CSV path provided
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
        if os.path.exists(csv_path):
            test_sms_csv(detector, csv_path)
        else:
            print(f"File not found: {csv_path}")
    else:
        print("Usage:")
        print("  python test/test_system.py path/to/test.csv")
        print("  python test/test_system.py path/to/image_dir/")

        # Quick self-test
        print("\n--- Quick Self-Test ---")

        # Test SMS with text
        result = detector.verify_transaction("VIA GTWORLD FROM AMAKA NWOSU", input_type='text')
        print(f"\n  Text: 'VIA GTWORLD FROM AMAKA NWOSU'")
        print(f"  Result: {result['prediction']} ({result['confidence']})")
        print(f"  Reason: {result['reason']}")

        # Test SMS with suspicious text
        result = detector.verify_transaction("CREDIT/ CASH PRIZE/Payment", input_type='text')
        print(f"\n  Text: 'CREDIT/ CASH PRIZE/Payment'")
        print(f"  Result: {result['prediction']} ({result['confidence']})")
        print(f"  Reason: {result['reason']}")

        # Test with full transaction
        transaction = {
            'bank': 'GTBank', 'account_masked': '******0586',
            'amount_ngn': 50000, 'balance_ngn': 75000,
            'date': '24/09/2025 19:19', 'time': '',
            'description': 'VIA GTWORLD FROM CHIDI OKORO'
        }
        result = detector.verify_transaction(transaction, input_type='text')
        print(f"\n  Transaction: {transaction['description']}")
        print(f"  Result: {result['prediction']} ({result['confidence']})")
        print(f"  Reason: {result['reason']}")
