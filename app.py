import streamlit as st
import pandas as pd
import numpy as np
from catboost import CatBoostClassifier
import json

# ===============================================================
# Page Configuration
# ===============================================================
st.set_page_config(
    page_title="Hawkstone Outlet Performance Predictor",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================================================
# Load Model and UI Configuration
# ===============================================================
@st.cache_resource
def load_model_and_config():
    """Load the trained model and feature configuration."""
    try:
        model = CatBoostClassifier()
        model.load_model('hawkstone_model.cbm')
        with open('feature_config.json', 'r') as f:
            config = json.load(f)
        return model, config
    except FileNotFoundError:
        st.error("Model or configuration file not found. Please run `model_training.py` first.")
        return None, None

model, feature_config = load_model_and_config()

# ===============================================================
# Helper Functions
# ===============================================================
def get_user_inputs(config):
    """Create sidebar widgets and get user inputs."""
    inputs = {}
    for feature, props in config.items():
        label = feature.replace('_', ' ').title()
        if props['type'] == 'categorical':
            inputs[feature] = st.selectbox(label, options=props['values'], index=0)
        else:
            inputs[feature] = st.slider(
                label,
                min_value=props['min'],
                max_value=props['max'],
                value=props['mean']
            )
    return inputs


def calculate_score(probabilities, classes):
    """Calculate weighted performance score for 3-band model."""
    band_weights = {"Low": 30, "Medium": 60, "High": 90}
    score = sum(probabilities[list(classes).index(b)] * band_weights.get(b, 0) for b in classes)
    return score


# ===============================================================
# Main Application UI
# ===============================================================
st.title("🎯 Hawkstone Outlet Performance Predictor (3-Band Model)")
st.markdown("""
This tool predicts an outlet's performance tier — **Low**, **Medium**, or **High** — based on recent activity and location-type levers.
Adjust the sliders and dropdowns on the left to explore how each feature influences the prediction.
""")

if model and feature_config:
    # --- Sidebar for Inputs ---
    with st.sidebar:
        st.header("⚙️ Outlet Levers")
        st.markdown("Adjust the inputs below to generate a prediction.")
        user_inputs = get_user_inputs(feature_config)
        predict_button = st.button("Predict Performance", type="primary", use_container_width=True)

    # --- Main Panel for Outputs ---
    if predict_button:
        with st.spinner('Calculating score...'):
            # Prepare DataFrame for prediction
            input_df = pd.DataFrame([user_inputs])
            for feature, props in feature_config.items():
                if props['type'] == 'categorical':
                    input_df[feature] = input_df[feature].astype('category')

            # --- Model Predictions ---
            probabilities = model.predict_proba(input_df)[0]

            preds = model.predict(input_df)
            if isinstance(preds, np.ndarray) and preds.ndim > 1:
                preds = preds.ravel()
            predicted_score = calculate_score(probabilities, model.classes_)

            predicted_score = calculate_score(probabilities, model.classes_)

            # Derive band directly from observed score distribution
            # Based on: Low ≈ 51.1, Medium ≈ 55.4, High ≈ 58.0
            if predicted_score < 53.0:
                predicted_band = "Low"
            elif predicted_score < 56.7:
                predicted_band = "Medium"
            else:
                predicted_band = "High"



            # --- Display Results ---
            st.subheader("Prediction Results")
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="Predicted Performance Score",
                    value=f"{predicted_score:.1f}",
                    help="Score on a 0–100 scale derived from predicted band probabilities."
                )

                color_map = {
                    "Low": "#E74C3C",        # red
                    "Medium": "#3498DB",     # blue
                    "High": "#27AE60"        # green
                }
                band_color = color_map.get(predicted_band, "grey")
                st.markdown(
                    f"**Predicted Band:** <span style='color: {band_color}; "
                    f"font-weight: bold; font-size: 1.2em; border: 1px solid {band_color}; "
                    f"border-radius: 5px; padding: 5px;'>{predicted_band}</span>",
                    unsafe_allow_html=True
                )

            with col2:
                prob_df = pd.DataFrame({
                    'Band': model.classes_,
                    'Probability': probabilities
                }).set_index('Band')

                st.markdown("**Performance Band Probabilities**")
                st.bar_chart(prob_df)

    else:
        st.info("Use the sidebar to adjust inputs and click **Predict Performance**.")

else:
    st.warning("Model or configuration not found. Please train the model first.")
