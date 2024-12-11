import streamlit as st
import requests
import pandas as pd
from openai import OpenAI

# OpenWeatherMap API Key
weather_api_key = st.secrets["WEATHER_API_KEY"]

# Title with emoji for fun
st.title("🌟 Eau What Now? 🌟")

# Main Instructions
st.markdown(
    """
    ## 🛠️ How to Use:
    1. **Upload** your perfume list as a **CSV** or **XLSX** file with a column `perfumes`.
    2. Add any missing perfumes manually if needed.
    3. **Enter the city** and let the app fetch weather details for you.
    4. **Describe your event**, and we'll recommend the best perfume for you.
    """
)
st.markdown("---")

# Initialize session state to store perfume list
if "perfume_list" not in st.session_state:
    st.session_state.perfume_list = []

# Layout for Weather Input
with st.container():
    st.subheader("🌦️ Weather Details")
    city = st.text_input("Enter your City:", placeholder="e.g., New York")

    # Initialize variables with default values
    temp, humidity, weather_desc = None, None, ""

    try:
        if city:
            # Fetch weather data
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"
            weather_data = requests.get(weather_url).json()

            if weather_data.get("cod") == 200:
                temp = weather_data["main"]["temp"]
                humidity = weather_data["main"]["humidity"]
                weather_desc = weather_data["weather"][0]["description"]
            else:
                temp, humidity, weather_desc = 25.0, 50, ""  # Reset to default values if error
    except Exception:
        temp, humidity, weather_desc = 25.0, 50, ""  # Reset to default values in case of exception

    col1, col2 = st.columns(2)
    with col1:
        temp = st.number_input("Temperature (°C):", value=temp, step=0.1)
    with col2:
        humidity = st.number_input("Humidity (%):", value=humidity, step=1)

    weather_desc = st.text_input(
        "Weather Description (change if inaccurate):", value=weather_desc if weather_desc else "", placeholder="e.g., warm and sunny"
    )

    if not weather_desc:
        st.warning("Weather description is empty. Consider filling it in for better recommendations.")

st.markdown("---")

# File Upload and Manual Addition Section
with st.container():
    st.subheader("📂 Upload or Add Your Perfume List")
    uploaded_file = st.file_uploader("Upload CSV or XLSX file:")

    # Process uploaded file
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file, engine='openpyxl')

            # Handle case-insensitive column matching for 'perfumes'
            df.columns = df.columns.str.lower()
            if "perfumes" in df.columns:
                file_perfumes = df["perfumes"].dropna().tolist()
                st.session_state.perfume_list.extend(file_perfumes)
                st.session_state.perfume_list = list(set(st.session_state.perfume_list))  # Remove duplicates
                st.success("Perfume list uploaded successfully!")
            else:
                st.error("The uploaded file must contain a column named 'perfumes'.")
        except Exception as e:
            st.error(f"Error reading the file: {e}")

    # Add perfumes manually
    st.markdown("### Or Add Perfumes Manually:")
    manual_perfume = st.text_input("Enter a perfume name:", key="manual_perfume_input")
    if st.button("Add Perfume"):
        if manual_perfume:
            st.session_state.perfume_list.append(manual_perfume)
            st.session_state.perfume_list = list(set(st.session_state.perfume_list))  # Remove duplicates
            st.success(f"Perfume '{manual_perfume}' added!")
            st.session_state.manual_perfume_input = ""  # Clear input
        else:
            st.warning("Please enter a perfume name to add.")

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
