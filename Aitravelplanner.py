import streamlit as st
import requests
import pandas as pd
import os
from dotenv import load_dotenv
from openai import OpenAI
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# Load environment variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

st.set_page_config(page_title="AI Travel Planner Pro", layout="wide")
st.title("🎒 AI Travel Planner Pro – Student Edition")

# Chatbot Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar Inputs
st.sidebar.header("Trip Details")

city = st.sidebar.text_input("Enter Destination City")
days = st.sidebar.slider("Number of Days", 1, 7, 2)
budget = st.sidebar.number_input("Total Budget (₹)", min_value=1000, step=500)
interest = st.sidebar.selectbox("Interest Type",
                                 ["tourist attraction", "museum", "park", "amusement park"])
location = st.sidebar.text_input("Enter Your Location (for nearby recommendations)")
route_optimization = st.sidebar.checkbox("Optimize Route")
cost_visualization = st.sidebar.checkbox("Show Cost Visualization")
save_pdf = st.sidebar.checkbox("Save Itinerary as PDF")

# Google Maps Places API
def get_places(city, interest):
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={interest}+in+{city}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    places = []
    if "results" in data:
        for place in data["results"][:5]:
            places.append({
                "name": place["name"],
                "address": place.get("formatted_address", "N/A"),
                "rating": place.get("rating", "N/A")
            })
    return places

# Route Optimization (Directions API)
def get_route(origin, destination):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data.get("routes"):
        leg = data["routes"][0]["legs"][0]
        return leg["distance"]["text"], leg["duration"]["text"]
    return None, None

# Generate Itinerary
if st.sidebar.button("Generate Trip Plan 🚀"):

    places = get_places(city, interest)

    if not places:
        st.error("No places found. Try another city.")
    else:
        st.success("Trip Plan Generated!")

        st.subheader("📍 Recommended Places")

        for place in places:
            st.write(f"**{place['name']}**")
            st.write(f"📌 {place['address']}")
            st.write(f"⭐ Rating: {place['rating']}")
            st.write("---")

        # Route Optimization
        if len(places) >= 2:
            st.subheader("📍 Optimized Route (Between First Two Places)")
            distance, duration = get_route(places[0]["name"], places[1]["name"])

            if distance and duration:
                st.write(f"Distance: {distance}")
                st.write(f"Estimated Travel Time: {duration}")

        # Cost Visualization
        st.subheader("📊 Cost Breakdown")

        attraction_cost = 1000
        stay_cost = 800 * days
        food_cost = 300 * days

        total_cost = attraction_cost + stay_cost + food_cost

        categories = ["Attractions", "Stay", "Food"]
        costs = [attraction_cost, stay_cost, food_cost]

        fig, ax = plt.subplots()
        ax.pie(costs, labels=categories, autopct="%1.1f%%")
        st.pyplot(fig)

        st.write(f"Total Estimated Cost: ₹ {total_cost}")
        st.write(f"Remaining Budget: ₹ {budget - total_cost}")

        # AI Summary Generation   
        prompt = f"""
        Create a student-friendly {days}-day travel itinerary for {city}.
        Recommended places: {[p['name'] for p in places]}.
        Budget: ₹{budget}.
        Make it exciting and budget conscious.
        """

        with st.spinner("Generating AI itinerary..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

        itinerary = response.choices[0].message.content

        st.subheader("🤖 AI Generated Itinerary")
        st.write(itinerary)

        # Save as PDF
        if st.button("💾 Download Itinerary as PDF"):

            pdf = SimpleDocTemplate("TripPlan.pdf")
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("AI Travel Planner - Trip Itinerary", styles["Heading1"]))
            elements.append(Spacer(1, 0.5 * inch))
            elements.append(Paragraph(itinerary, styles["Normal"]))

            pdf.build(elements)

            with open("TripPlan.pdf", "rb") as file:
                st.download_button("Download PDF", file, file_name="TripPlan.pdf")

# Chatbot Interface
st.subheader("💬 Travel Chatbot Assistant")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Ask me anything about your trip..."):
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.messages
    )

    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        st.markdown(reply)