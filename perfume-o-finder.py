import streamlit as st
import requests
import pandas as pd
from openai import OpenAI

# OpenWeatherMap API Key
weather_api_key = st.secrets["WEATHER_API_KEY"]

# Title with emoji for fun
st.title("🌟 Eau What Now? 🌟")

# Sidebar for navigation
st.sidebar.title("Navigation")
st.sidebar.markdown("Use the sections below to navigate:")
st.sidebar.markdown("- Weather Input")
st.sidebar.markdown("- Upload Perfume List")
st.sidebar.markdown("- Get Recommendation")

# Main Instructions
st.markdown(
    """
    ## 🛠️ How to Use:
    1. **Upload** your perfume list as a **CSV** or **XLSX** file.
    2. Ensure the file has a column named **'Perfumes'**.
    3. **Enter the city** and let the app fetch weather details for you.
    4. **Describe your event**, and we'll recommend the best perfume for you.
    """
)
st.markdown("---")

# Layout for Weather Input
with st.container():
    st.subheader("🌦️ Weather Details")
    city = st.text_input("Enter your City:", placeholder="e.g., New York")
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
                temp, humidity, weather_desc = None, None, None
    except Exception:
        temp, humidity, weather_desc = None, None, None

    col1, col2 = st.columns(2)
    with col1:
        temp = st.number_input("Temperature (°C):", value=temp if temp else 25.0, step=0.1)
    with col2:
        humidity = st.number_input("Humidity (%):", value=humidity if humidity else 50, step=1)

    weather_desc = st.text_input(
        "Weather Description:", value=weather_desc if weather_desc else "", placeholder="e.g., warm and sunny"
    )

    if not weather_desc:
        st.warning("Weather description is empty. Consider filling it in for better recommendations.")

st.markdown("---")

# File Upload Section
with st.container():
    st.subheader("📂 Upload Your Perfume List")
    uploaded_file = st.file_uploader("Upload CSV or XLSX file:")
    perfume_list = []

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file, engine='openpyxl')

            # Handle case-insensitive column matching for 'perfumes'
            df.columns = df.columns.str.lower()
            if "perfumes" in df.columns:
                perfume_list = df["perfumes"].dropna().tolist()
                st.success("Perfume list uploaded successfully!")
                with st.expander("Click to view your uploaded perfumes list"):
                    for perfume in perfume_list:
                        st.write(f"- {perfume}")
            else:
                st.error("The uploaded file must contain a column named 'perfumes'.")
        except Exception as e:
            st.error(f"Error reading the file: {e}")
    else:
        st.info("Please upload a file to proceed.")

st.markdown("---")

# Event and Recommendation
with st.container():
    st.subheader("🎉 Event Details & Recommendation")
    event = st.text_input("Describe your event (e.g., 'movie at 9:15 PM'):", placeholder="e.g., Dinner with friends")

    if st.button("✨ Get Recommendation ✨"):
        if len(perfume_list) > 0 and event:
            # Formulate the ChatGPT query
            message = f"""
            I have these perfumes: {', '.join(perfume_list)}. I am going to {event}. 
            The current weather in {city} is {weather_desc} ({temp}°C, {humidity}% humidity). 
            Based on this information, recommend the best perfume to wear and explain briefly why. 
            Also, include instructions on how to apply the selected perfume.
            """

            # ChatGPT API Call
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a perfume expert. Provide concise, personalized recommendations with application instructions."},
                    {"role": "user", "content": message}
                ]
            )

            recommendation = response.choices[0].message.content

            # Display the recommendation
            st.success("🎁 Here's your recommendation:")
            st.write(recommendation)
        else:
            st.error("Please ensure both the perfume list and event details are provided.")
