import streamlit as st
import requests
import pandas as pd
from openai import OpenAI

# OpenWeatherMap API Key
weather_api_key = st.secrets["WEATHER_API_KEY"]

# Title
st.title("Perfume-o-finder")

# Get Current Weather
def get_weather():
    try:
        city = st.text_input("Enter your City:")

        # Fetch weather data from API
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"
        weather_data = requests.get(weather_url).json()

        if weather_data.get("cod") == 200:
            temp = weather_data["main"]["temp"]
            humidity = weather_data["main"]["humidity"]
            weather_desc = weather_data["weather"][0]["description"]
        else:
            # Default fallback if API fails
            temp, humidity, weather_desc = None, None, None
    except Exception as e:
        st.error("Unable to fetch weather data. Using default values.")
        temp, humidity, weather_desc = None, None, None

    # Editable fields for temperature, humidity, and weather description
    temp = st.number_input("Temperature (°C):", value=temp if temp else 25.0, step=0.1)
    humidity = st.number_input("Humidity (%):", value=humidity if humidity else 50, step=1)
    weather_desc = st.text_input("Weather Description:", value=weather_desc if weather_desc else "")

    # Generate weather description dynamically if left empty
    if not weather_desc:
        weather_desc = generate_weather_description(temp, humidity)

    return city, temp, humidity, weather_desc

# Helper function to generate weather description
def generate_weather_description(temp, humidity):
    if temp > 30:
        if humidity > 60:
            return "hot and humid"
        else:
            return "hot and dry"
    elif 20 <= temp <= 30:
        if humidity > 60:
            return "warm and humid"
        else:
            return "pleasant"
    elif temp < 20:
        if humidity > 60:
            return "cold and damp"
        else:
            return "cold and dry"
    else:
        return "mild weather"

# Get and display weather information
city, temperature, humidity, weather_desc = get_weather()
st.write(f"Weather in {city}: {temperature}°C, {humidity}% humidity, {weather_desc}")

# File Upload
uploaded_file = st.file_uploader("Upload your perfume list (CSV,XLSX format):")
perfume_list = []
if uploaded_file:
    try:
        # Determine the file type and read accordingly
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)

        # Assuming the file has a column named 'perfumes'
        if "perfumes" in df.columns:
            perfume_list = df["perfumes"].dropna().tolist()
            st.write("Your perfumes:")
            st.write(perfume_list)
        else:
            st.error("The uploaded file must contain a column named 'perfumes'.")
    except Exception as e:
        st.error(f"Error reading the file: {e}")
else:
    st.write("No file uploaded. Please upload a file containing your perfume list.")

# Event/Context
event = st.text_input("Describe your event (e.g., 'movie at 9:15 PM'):")

# Get Recommendation
if st.button("Get Recommendation"):
    if len(perfume_list) > 0:
        # Formulate the ChatGPT query
        message = f"""
        I have these perfumes: {', '.join(perfume_list)}. I am going to {event}. 
        The current weather in {city} is {weather_desc} ({temperature}°C, {humidity}% humidity). 
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

        # New way to extract the response text:
        recommendation = response.choices[0].message.content

        # Display the recommendation
        st.write("Recommendation:")
        st.write(recommendation)
    else:
        st.error("No perfumes available for recommendation.")
