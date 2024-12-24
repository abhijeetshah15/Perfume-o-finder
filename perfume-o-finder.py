# Import necessary libraries
import streamlit as st
import requests
import pandas as pd
import os

# Title with emoji for fun
st.title("🌟 Eau What Now? 🌟")

# Initialize session state to store perfume list
if "perfume_list" not in st.session_state:
    st.session_state.perfume_list = []

# Load perfumes from two additional CSV files in the directory
def load_additional_perfumes():
    try:
        # Update paths to your directory if needed
        csv_files = ["mens_perfumes.csv", "womens_perfumes.csv"]  # Replace these with actual file paths if necessary
        combined_perfumes = []

        for file in csv_files:
            if os.path.exists(file):
                df = pd.read_csv(file)
                if "title" in df.columns:
                    combined_perfumes.extend(df["title"].dropna().tolist())
        
        return list(set(combined_perfumes))  # Remove duplicates
    except Exception as e:
        st.error(f"Error loading additional perfume files: {e}")
        return []

additional_perfumes = load_additional_perfumes()

# Add perfumes manually with live dynamic suggestions
st.subheader("📂 Add Perfumes Manually:")
manual_perfume_input = st.text_input("Start typing a perfume name:", placeholder="Type here...")

# Filter suggestions dynamically
if manual_perfume_input:
    suggestions = [
        perfume for perfume in additional_perfumes
        if manual_perfume_input.lower() in perfume.lower()
    ]
else:
    suggestions = additional_perfumes

# Display suggestions in a live-select dropdown
if suggestions:
    selected_perfume = st.selectbox("Suggestions (live):", options=suggestions, key="live_suggestions")
    if st.button("Add Selected Perfume"):
        if selected_perfume not in st.session_state.perfume_list:
            st.session_state.perfume_list.append(selected_perfume)
            st.success(f"Perfume '{selected_perfume}' added!")
        else:
            st.warning(f"Perfume '{selected_perfume}' is already in the list.")
else:
    st.info("No matching suggestions found.")

# Add the perfume manually if user enters one directly
if st.button("Add Perfume Manually"):
    if manual_perfume_input:
        if manual_perfume_input not in st.session_state.perfume_list:
            st.session_state.perfume_list.append(manual_perfume_input)
            st.success(f"Perfume '{manual_perfume_input}' added!")
        else:
            st.warning(f"Perfume '{manual_perfume_input}' is already in the list.")
    else:
        st.warning("Please type a perfume name to add.")

# Display current perfume list
if st.session_state.perfume_list:
    st.markdown("### Current Perfume List:")
    for perfume in st.session_state.perfume_list:
        st.write(f"- {perfume}")
else:
    st.info("No perfumes added yet. Upload a file or add perfumes manually.")

st.markdown("---")

# Event and Recommendation
with st.container():
    st.subheader("🎉 Event Details & Recommendation")
    event = st.text_input(
        "Describe your event (e.g., 'movie at 9:15 PM'):",
        placeholder="e.g., Formal dinner, outdoor in the evening, semi-casual attire"
    )

    if st.button("✨ Get Recommendation ✨"):
        if len(st.session_state.perfume_list) > 0 and event:
            # Formulate the ChatGPT query
            perfume_details = ", ".join(st.session_state.perfume_list)
            message = f"""
            I have these perfumes: {perfume_details}.
            I am going to {event}. The current weather in {city} is {weather_desc} ({temp}°C, {humidity}% humidity).
            For temperatures below 15°C, prefer warm, spicy, or woody perfumes.
            For 15°C–25°C, prefer floral or citrus perfumes.
            For above 25°C, prefer light, fresh, or aquatic perfumes.
            Focus on weather as the primary factor, event type as secondary.
            Provide one recommendation or a tie if necessary, with reasons for your choice.
            But make sure you consider the event as well. Do not only focus on the temperature.
            For example, if it is a formal dinner it could be a nice dark fragrance and not a fresh one even if the temperature is between 15-25.
            Include specific application tips (e.g., pulse points, layering advice, and mixing two fragrances only if necessary, no need to provide every time).
            """

            # ChatGPT API Call
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """
                    You are a professional perfume consultant. 
                    Your job is to analyze a list of perfumes and recommend the most suitable option based on:
                    1. Weather (temperature, humidity, and general description).
                    2. Event type (formal, casual, or outdoor).
                    Avoid repetitive or ambiguous responses and provide consistent recommendations.
                    Also, include a brief explanation of your choice and how to apply the selected perfume for the best effect.
                    """},
                    {"role": "user", "content": message}
                ]
            )

            recommendation = response.choices[0].message.content

            # Display the recommendation
            st.success("🎁 Here's your recommendation:")
            st.write(recommendation)
        else:
            st.error("Please ensure both the perfume list and event details are provided.")