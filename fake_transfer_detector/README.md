# Fake Transfer Detection System

**Explainable AI Model for Detecting Fake Mobile Money Transfers for SMEs**

Final Year Project — 2026

## Overview

This system uses two AI pipelines to detect forged mobile money transfers:

- **Pipeline 1 (Screenshot):** Analyzes bank transfer screenshot images using image forensic features (sharpness, noise, compression artifacts). Accuracy: 96.6%
- **Pipeline 2 (SMS/Text):** Analyzes SMS alerts and transaction data using structural patterns, TF-IDF, and transaction metadata. Accuracy: 95.7% (internal), 77.6% (external)

Both pipelines provide **explainable predictions** — telling users *why* a transfer was flagged, not just the result.

## Setup

### Prerequisites

- Python 3.9+
- Tesseract OCR installed on your system

#### Install Tesseract

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from: https://github.com/tesseract-ocr/tesseract

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Add Model Files

Copy your trained model files to the `models/` folder:
- `pipeline1_screenshot_model.pkl`
- `pipeline2_full_feature.pkl`

## Usage

### Run the Web App

```bash
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

### Use in Python

```python
from core.detector import FakeTransferDetector

detector = FakeTransferDetector(models_dir='models')

# Verify a screenshot
result = detector.verify_transaction('path/to/screenshot.png', input_type='image')

# Verify SMS text
result = detector.verify_transaction('VIA GTWORLD FROM JOHN DOE', input_type='text')

# Verify with full transaction data
result = detector.verify_transaction({
    'bank': 'GTBank',
    'amount_ngn': 50000,
    'balance_ngn': 75000,
    'date': '24/09/2025 19:19',
    'time': '',
    'description': 'VIA GTWORLD FROM JOHN DOE'
}, input_type='text')

print(result['prediction'])   # FAKE or GENUINE
print(result['confidence'])   # e.g., "87.5%"
print(result['reason'])       # Human-readable explanation
print(result['action'])       # Recommended action
```

### Batch Testing

```bash
python test/test_system.py path/to/test_data.csv
```

## Project Structure

```
fake_transfer_detector/
├── app.py                    ← Streamlit web app
├── requirements.txt          ← Python dependencies
├── README.md                 ← This file
├── models/                   ← Trained model files (.pkl)
├── core/                     ← Core detection logic
│   ├── detector.py           ← Unified verify_transaction()
│   ├── screenshot_pipeline.py ← Image forensic analysis
│   ├── sms_pipeline.py       ← SMS/text structural analysis
│   └── text_cleaning.py      ← Text preprocessing utilities
├── test/                     ← Testing scripts
│   └── test_system.py        ← Batch testing
└── logs/                     ← Auto-generated prediction logs
    └── detection_log.csv
```

## How It Works

### Screenshot Detection
1. Extracts image features: sharpness, noise levels, compression artifacts, edge patterns
2. Extracts OCR text structural features from the screenshot
3. Uses a trained Logistic Regression model to classify
4. Explains: "Flagged because inconsistent image sharpness, unusual compression ratio"

### SMS/Text Detection  
1. Extracts structural features from the message text
2. Extracts TF-IDF features from cleaned text
3. Analyzes transaction metadata (amount, balance, date format, bank)
4. Uses a trained model to classify
5. Explains: "Flagged because uses GTBANK instead of GTWORLD, suspicious sender name"

## Limitations

- Screenshot model trained on 29 images (preliminary results)
- SMS model performance varies by forgery sophistication
- Limited to Nigerian banks in training data (GTBank, Zenith, Moniepoint)
- Highly sophisticated forgeries may evade detection
