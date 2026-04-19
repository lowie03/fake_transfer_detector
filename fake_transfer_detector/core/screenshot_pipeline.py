"""
Screenshot Forgery Detection Pipeline.
Extracts image features + text structural features from bank transfer screenshots.
"""

import cv2
import numpy as np
import os
import joblib
import pytesseract
from scipy import ndimage

from .text_cleaning import extract_text_structural_features


def extract_image_features(image_path):
    """
    Extract visual forensic features from a screenshot image.
    Detects manipulation through sharpness, noise, edge, and compression analysis.
    """
    features = {}

    try:
        img = cv2.imread(image_path)
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Image metadata
        features['img_height'] = h
        features['img_width'] = w
        features['img_aspect_ratio'] = w / h if h > 0 else 0
        features['img_total_pixels'] = h * w
        file_size = os.path.getsize(image_path)
        features['img_file_size'] = file_size
        features['img_bytes_per_pixel'] = file_size / (h * w) if h * w > 0 else 0

        # Sharpness analysis
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        features['img_sharpness_mean'] = np.mean(np.abs(laplacian))
        features['img_sharpness_std'] = np.std(laplacian)
        features['img_sharpness_var'] = laplacian.var()

        # Regional sharpness (detects inconsistent editing)
        third_h = h // 3
        if third_h > 0:
            lap_top = cv2.Laplacian(gray[:third_h, :], cv2.CV_64F)
            lap_mid = cv2.Laplacian(gray[third_h:2*third_h, :], cv2.CV_64F)
            lap_bot = cv2.Laplacian(gray[2*third_h:, :], cv2.CV_64F)
            features['img_sharpness_top'] = lap_top.var()
            features['img_sharpness_mid'] = lap_mid.var()
            features['img_sharpness_bot'] = lap_bot.var()
            features['img_sharpness_region_var'] = np.var([lap_top.var(), lap_mid.var(), lap_bot.var()])
        else:
            features['img_sharpness_top'] = features['img_sharpness_mid'] = features['img_sharpness_bot'] = 0
            features['img_sharpness_region_var'] = 0

        # Noise analysis
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        noise = gray.astype(float) - blurred.astype(float)
        features['img_noise_mean'] = np.mean(np.abs(noise))
        features['img_noise_std'] = np.std(noise)

        if third_h > 0:
            features['img_noise_region_var'] = np.var([
                np.std(noise[:third_h, :]),
                np.std(noise[third_h:2*third_h, :]),
                np.std(noise[2*third_h:, :])
            ])
        else:
            features['img_noise_region_var'] = 0

        # Edge analysis
        edges = cv2.Canny(gray, 50, 150)
        features['img_edge_density'] = np.sum(edges > 0) / (h * w) if h * w > 0 else 0

        if third_h > 0:
            edge_top = np.sum(edges[:third_h, :] > 0) / (third_h * w)
            edge_mid = np.sum(edges[third_h:2*third_h, :] > 0) / (third_h * w)
            edge_bot = np.sum(edges[2*third_h:, :] > 0) / ((h - 2*third_h) * w)
            features['img_edge_region_var'] = np.var([edge_top, edge_mid, edge_bot])
        else:
            features['img_edge_region_var'] = 0

        # Color/contrast
        features['img_brightness_mean'] = np.mean(gray)
        features['img_brightness_std'] = np.std(gray)
        features['img_contrast'] = gray.max() - gray.min()

        b, g, r = cv2.split(img)
        features['img_channel_b_mean'] = np.mean(b)
        features['img_channel_g_mean'] = np.mean(g)
        features['img_channel_r_mean'] = np.mean(r)
        features['img_channel_std_var'] = np.var([np.std(b), np.std(g), np.std(r)])

        # Histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        hist_norm = hist / hist.sum()
        features['img_hist_entropy'] = -np.sum(hist_norm[hist_norm > 0] * np.log2(hist_norm[hist_norm > 0]))
        features['img_hist_peak_count'] = np.sum((hist[1:-1] > hist[:-2]) & (hist[1:-1] > hist[2:]))
        features['img_hist_uniformity'] = np.sum(hist_norm ** 2)

        # Texture (Sobel)
        sobelx = ndimage.sobel(gray.astype(float), axis=1)
        sobely = ndimage.sobel(gray.astype(float), axis=0)
        texture = np.sqrt(sobelx**2 + sobely**2)
        features['img_texture_mean'] = np.mean(texture)
        features['img_texture_std'] = np.std(texture)

        # JPEG blockiness (fixed for odd dimensions)
        if h >= 16 and w >= 16:
            col_7 = gray[:, 7::8].astype(float)
            col_8 = gray[:, 8::8].astype(float)
            mc = min(col_7.shape[1], col_8.shape[1])
            row_7 = gray[7::8, :].astype(float)
            row_8 = gray[8::8, :].astype(float)
            mr = min(row_7.shape[0], row_8.shape[0])

            if mc > 0 and mr > 0:
                h_diff = np.mean(np.abs(col_7[:, :mc] - col_8[:, :mc]))
                v_diff = np.mean(np.abs(row_7[:mr, :] - row_8[:mr, :]))
                col_3 = gray[:, 3::8].astype(float)
                col_4 = gray[:, 4::8].astype(float)
                mc_nb = min(col_3.shape[1], col_4.shape[1])
                row_3 = gray[3::8, :].astype(float)
                row_4 = gray[4::8, :].astype(float)
                mr_nb = min(row_3.shape[0], row_4.shape[0])
                h_diff_nb = np.mean(np.abs(col_3[:, :mc_nb] - col_4[:, :mc_nb])) if mc_nb > 0 else 0
                v_diff_nb = np.mean(np.abs(row_3[:mr_nb, :] - row_4[:mr_nb, :])) if mr_nb > 0 else 0
                features['img_jpeg_blockiness_h'] = h_diff - h_diff_nb
                features['img_jpeg_blockiness_v'] = v_diff - v_diff_nb
            else:
                features['img_jpeg_blockiness_h'] = features['img_jpeg_blockiness_v'] = 0
        else:
            features['img_jpeg_blockiness_h'] = features['img_jpeg_blockiness_v'] = 0

    except Exception as e:
        print(f"Error extracting image features: {e}")
        return None

    return features


class ScreenshotDetector:
    """Screenshot forgery detection using image + text structural features."""

    def __init__(self, model_path):
        """Load the trained model package."""
        package = joblib.load(model_path)
        self.model = package['model_object']
        self.scaler = package.get('scaler')
        self.selector = package['feature_selector']
        self.selected_features = package['selected_features']
        self.all_feature_names = package['all_feature_names']
        self.model_name = package['model_name']
        self.metrics = package.get('metrics_loocv', {})

    def predict(self, image_path):
        """
        Predict whether a screenshot is forged and explain why.

        Args:
            image_path: Path to screenshot image file

        Returns:
            dict with prediction, confidence, reason, action
        """
        # Extract image features
        img_feats = extract_image_features(image_path)
        if img_feats is None:
            return {
                'prediction': 'ERROR',
                'confidence': '0%',
                'reason': 'Could not process image file.',
                'action': '⚠️ Manual review required — image could not be analyzed.'
            }

        # Extract OCR text + structural features
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            raw_text = pytesseract.image_to_string(gray)
            raw_text = raw_text.encode('utf-8', errors='replace').decode('utf-8')
        except:
            raw_text = ""

        txt_feats = extract_text_structural_features(raw_text)

        # Build feature vector
        all_feats = {**img_feats, **txt_feats}
        vec = np.array([[all_feats.get(f, 0) for f in self.all_feature_names]])
        vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)

        # Select features and scale
        vec_selected = self.selector.transform(vec)
        if self.scaler is not None:
            vec_selected = self.scaler.transform(vec_selected)

        # Predict
        prob = self.model.predict_proba(vec_selected)[0][1]
        prediction = "FAKE" if prob >= 0.5 else "GENUINE"

        # Build explanation
        reasons = []
        for feat in self.selected_features:
            val = all_feats.get(feat, 0)
            if 'sharpness_region_var' in feat and val > 100:
                reasons.append(f"Inconsistent image sharpness ({val:.0f})")
            elif 'noise_region_var' in feat and val > 5:
                reasons.append(f"Uneven noise levels suggest editing ({val:.1f})")
            elif 'edge_region_var' in feat and val > 0.001:
                reasons.append(f"Edge pattern inconsistency ({val:.4f})")
            elif 'jpeg_blockiness' in feat and abs(val) > 1:
                reasons.append(f"Compression artifacts detected ({val:.2f})")
            elif 'garbled_ratio' in feat and val > 0.05:
                reasons.append(f"High OCR error rate ({val:.0%})")
            elif 'bytes_per_pixel' in feat:
                reasons.append(f"Image compression: {val:.3f} bytes/pixel")
            elif 'brightness_std' in feat:
                reasons.append(f"Brightness variation: {val:.1f}")

        if not reasons:
            reasons.append("Based on visual and structural pattern analysis")

        return {
            'prediction': prediction,
            'confidence': f"{prob*100:.1f}%" if prediction == "FAKE" else f"{(1-prob)*100:.1f}%",
            'probability_fake': float(prob),
            'reason': f"{prediction}: " + "; ".join(reasons[:4]),
            'action': "⚠️ This screenshot shows signs of forgery. Do not accept as proof of payment."
                      if prediction == "FAKE"
                      else "✅ Screenshot appears authentic. Standard verification applies."
        }
