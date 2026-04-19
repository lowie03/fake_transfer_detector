"""
Fake Transfer Detection System — Streamlit App
A tool for SMEs to verify mobile money transfer screenshots and SMS alerts.
"""

import streamlit as st
import os
import tempfile
from core.detector import FakeTransferDetector

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Fake Transfer Detector",
    page_icon="🔍",
    layout="centered"
)

# =============================================================================
# LOAD MODELS (cached so they only load once)
# =============================================================================

@st.cache_resource
def load_detector():
    """Load both detection pipelines."""
    return FakeTransferDetector(models_dir='models')

detector = load_detector()

# =============================================================================
# CUSTOM STYLING
# =============================================================================

st.markdown("""
<style>
    .result-fake {
        background-color: #2d2d2d;
        color: #ffb3b3;
        border-left: 5px solid #e74c3c;
        padding: 20px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .result-genuine {
        background-color: #f4fff4;
        color: #218838;
        border-left: 5px solid #2ecc71;
        padding: 20px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .result-error {
        background-color: #fff8e1;
        color: #b26a00;
        border-left: 5px solid #f39c12;
        padding: 20px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .metric-box {
        text-align: center;
        padding: 15px;
        border-radius: 8px;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# HEADER
# =============================================================================

st.title("🔍 Fake Transfer Detection System")
st.markdown("*Explainable AI-powered verification for mobile money transfers*")
st.markdown("---")

# =============================================================================
# INPUT SELECTION
# =============================================================================

input_mode = st.radio(
    "Select input type:",
    ["📸 Upload Screenshot", "📝 Enter SMS / Transaction Details"],
    horizontal=True
)

# =============================================================================
# SCREENSHOT INPUT MODE
# =============================================================================

if input_mode == "📸 Upload Screenshot":
    st.subheader("Upload Transfer Screenshot")
    st.caption("Upload a screenshot of a bank transfer confirmation to verify its authenticity.")

    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['png', 'jpg', 'jpeg'],
        help="Supported formats: PNG, JPG, JPEG"
    )

    if uploaded_file is not None:
        # Display the uploaded image
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(uploaded_file, caption="Uploaded Screenshot", use_container_width=True)

        # Verify button
        if st.button("🔍 Verify Screenshot", type="primary", use_container_width=True):
            with st.spinner("Analyzing screenshot..."):
                # Save to temp file for processing
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                # Run detection
                result = detector.verify_transaction(tmp_path, input_type='image')

                # Cleanup temp file
                os.unlink(tmp_path)

            # Display results
            display_result(result) if 'display_result' in dir() else None

            prediction = result['prediction']
            confidence = result['confidence']
            reason = result['reason']
            action = result['action']

            st.markdown("### Result")

            if prediction == "FAKE":
                st.markdown(f"""
                <div class="result-fake">
                    <h2>⚠️ FAKE TRANSFER DETECTED</h2>
                    <p><strong>Confidence:</strong> {confidence}</p>
                    <p><strong>Why:</strong> {reason}</p>
                    <p><strong>Action:</strong> {action}</p>
                </div>
                """, unsafe_allow_html=True)
            elif prediction == "GENUINE":
                st.markdown(f"""
                <div class="result-genuine">
                    <h2>✅ GENUINE TRANSFER</h2>
                    <p><strong>Confidence:</strong> {confidence}</p>
                    <p><strong>Why:</strong> {reason}</p>
                    <p><strong>Action:</strong> {action}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="result-error">
                    <h2>⚠️ ANALYSIS ERROR</h2>
                    <p><strong>Reason:</strong> {reason}</p>
                    <p><strong>Action:</strong> {action}</p>
                </div>
                """, unsafe_allow_html=True)

            # Show pipeline info
            st.caption(f"Pipeline: {result.get('pipeline_used', 'N/A')} | Time: {result.get('timestamp', 'N/A')}")

# =============================================================================
# SMS / TEXT INPUT MODE
# =============================================================================

else:
    st.subheader("Enter Transaction Details")
    st.caption("Paste the SMS alert text or enter the transaction details manually.")

    # Option A: Quick text input
    tab1, tab2 = st.tabs(["Quick Text Input", "Full Transaction Details"])

    with tab1:
        sms_text = st.text_area(
            "Paste SMS / Alert Message:",
            height=100,
            placeholder="e.g., VIA GTWORLD FROM JOHN DOE"
        )

        if st.button("🔍 Verify Message", type="primary", key="verify_text", use_container_width=True):
            if sms_text.strip():
                with st.spinner("Analyzing message..."):
                    result = detector.verify_transaction(sms_text.strip(), input_type='text')

                prediction = result['prediction']
                confidence = result['confidence']
                reason = result['reason']
                action = result['action']

                st.markdown("### Result")

                if prediction == "FAKE":
                    st.markdown(f"""
                    <div class="result-fake">
                        <h2>⚠️ FAKE TRANSFER DETECTED</h2>
                        <p><strong>Confidence:</strong> {confidence}</p>
                        <p><strong>Why:</strong> {reason}</p>
                        <p><strong>Action:</strong> {action}</p>
                    </div>
                    """, unsafe_allow_html=True)
                elif prediction == "GENUINE":
                    st.markdown(f"""
                    <div class="result-genuine">
                        <h2>✅ GENUINE TRANSFER</h2>
                        <p><strong>Confidence:</strong> {confidence}</p>
                        <p><strong>Why:</strong> {reason}</p>
                        <p><strong>Action:</strong> {action}</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.caption(f"Pipeline: {result.get('pipeline_used', 'N/A')} | Time: {result.get('timestamp', 'N/A')}")
            else:
                st.warning("Please enter a message to verify.")

    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            bank = st.selectbox("Bank", ["GTBank", "Zenith", "Moniepoint", "Other"])
            amount = st.number_input("Amount (NGN)", min_value=0, value=0, step=1000)
            date = st.text_input("Date", placeholder="e.g., 24/09/2025 or Fri, 28 November 2025")

        with col2:
            account = st.text_input("Account (masked)", placeholder="e.g., ******0586")
            balance = st.number_input("Balance (NGN)", min_value=0.0, value=0.0, step=1000.0)
            time_val = st.text_input("Time", placeholder="e.g., 19:19 or 4:25 pm")

        description = st.text_input(
            "Description / Alert Text",
            placeholder="e.g., VIA GTWORLD FROM JOHN DOE"
        )

        if st.button("🔍 Verify Transaction", type="primary", key="verify_full", use_container_width=True):
            if description.strip():
                transaction = {
                    'bank': bank,
                    'account_masked': account,
                    'amount_ngn': amount,
                    'balance_ngn': balance,
                    'date': date,
                    'time': time_val,
                    'description': description
                }

                with st.spinner("Analyzing transaction..."):
                    result = detector.verify_transaction(transaction, input_type='text')

                prediction = result['prediction']
                confidence = result['confidence']
                reason = result['reason']
                action = result['action']

                st.markdown("### Result")

                if prediction == "FAKE":
                    st.markdown(f"""
                    <div class="result-fake">
                        <h2>⚠️ FAKE TRANSFER DETECTED</h2>
                        <p><strong>Confidence:</strong> {confidence}</p>
                        <p><strong>Why:</strong> {reason}</p>
                        <p><strong>Action:</strong> {action}</p>
                    </div>
                    """, unsafe_allow_html=True)
                elif prediction == "GENUINE":
                    st.markdown(f"""
                    <div class="result-genuine">
                        <h2>✅ GENUINE TRANSFER</h2>
                        <p><strong>Confidence:</strong> {confidence}</p>
                        <p><strong>Why:</strong> {reason}</p>
                        <p><strong>Action:</strong> {action}</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.caption(f"Pipeline: {result.get('pipeline_used', 'N/A')} | Time: {result.get('timestamp', 'N/A')}")
            else:
                st.warning("Please enter a description to verify.")

# =============================================================================
# SIDEBAR — MODEL INFO
# =============================================================================

with st.sidebar:
    st.markdown("### 📊 Model Information")

    model_info = detector.get_model_info()

    if 'screenshot' in model_info:
        st.markdown("**Pipeline 1: Screenshot**")
        metrics = model_info['screenshot'].get('metrics', {})
        st.markdown(f"- Accuracy: {metrics.get('accuracy', 'N/A'):.1%}" if isinstance(metrics.get('accuracy'), float) else "- Accuracy: N/A")
        st.markdown(f"- Recall: {metrics.get('recall', 'N/A'):.1%}" if isinstance(metrics.get('recall'), float) else "- Recall: N/A")

    if 'sms' in model_info:
        st.markdown("**Pipeline 2: SMS/Text**")
        metrics = model_info['sms'].get('metrics', {})
        st.markdown(f"- Accuracy: {metrics.get('accuracy', 'N/A'):.1%}" if isinstance(metrics.get('accuracy'), float) else "- Accuracy: N/A")
        st.markdown(f"- Recall: {metrics.get('recall', 'N/A'):.1%}" if isinstance(metrics.get('recall'), float) else "- Recall: N/A")

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    This system uses **Explainable AI** to detect 
    fake mobile money transfers.
    
    It analyzes:
    - 📸 Screenshot visual forensics
    - 📝 SMS structural patterns
    - 💰 Transaction data consistency
    
    Built for SME vendors in Nigeria.
    """)

    st.markdown("---")
    st.caption("Final Year Project — 2026")
