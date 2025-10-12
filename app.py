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
        else: # numerical
            inputs[feature] = st.slider(
                label,
                min_value=props['min'],
                max_value=props['max'],
                value=props['mean']
            )
    return inputs

def calculate_score(probabilities, classes):
    """Calculate the weighted performance score."""
    band_weights = {"Very Low": 10, "Low": 30, "Medium": 50, "High": 70, "Very High": 90}
    score = sum(probabilities[list(classes).index(b)] * band_weights[b] for b in classes)
    return score

# ===============================================================
# Main Application UI
# ===============================================================
st.title("🎯 Hawkstone Outlet Performance Predictor")
st.markdown("""
This tool uses a machine learning model to predict the performance score of an outlet based on key characteristics.
Adjust the levers in the sidebar to see how they impact the potential score.
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
            # Create a DataFrame from inputs
            input_df = pd.DataFrame([user_inputs])

            # Ensure correct data types
            for feature, props in feature_config.items():
                if props['type'] == 'categorical':
                    input_df[feature] = input_df[feature].astype('category')

            # Get predictions
            probabilities = model.predict_proba(input_df)[0]
            predicted_band = model.predict(input_df)[0][0]
            predicted_score = calculate_score(probabilities, model.classes_)

            # Display results
            st.subheader("Prediction Results")
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="Predicted Performance Score",
                    value=f"{predicted_score:.1f}",
                    help="Score is on a 0-100 scale, calculated from band probabilities."
                )
                
                # Dynamic styling for the predicted band
                color_map = {"Very Low": "red", "Low": "orange", "Medium": "blue", "High": "green", "Very High": "violet"}
                band_color = color_map.get(predicted_band, "grey")
                st.markdown(f"**Predicted Band:** <span style='color: {band_color}; font-weight: bold; font-size: 1.2em; border: 1px solid {band_color}; border-radius: 5px; padding: 5px;'>{predicted_band}</span>", unsafe_allow_html=True)


            with col2:
                # Create a DataFrame for the probability chart
                prob_df = pd.DataFrame({
                    'Band': model.classes_,
                    'Probability': probabilities
                }).set_index('Band')

                st.markdown("**Performance Band Probabilities**")
                st.bar_chart(prob_df)

    else:
        st.info("Adjust the levers in the sidebar and click 'Predict Performance' to see the results.")

else:
    st.warning("Application is not configured. Please run the training script.")