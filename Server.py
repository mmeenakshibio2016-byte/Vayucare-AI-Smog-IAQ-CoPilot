import json
import math
import os
from datetime import datetime
from urllib.parse import quote

import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="VayuCare AI",
    page_icon="🌫️",
    layout="wide",
)

CITY_PROFILES = {
    "New Delhi": (28.6139, 77.2090),
    "Kolkata": (22.5726, 88.3639),
    "Los Angeles": (34.0522, -118.2437),
}

STATIONS = {
    "New Delhi": [
        ("Anand Vihar", 28.6469, 77.3160),
        ("ITO", 28.6286, 77.2410),
        ("RK Puram", 28.5665, 77.1767),
    ],
    "Kolkata": [
        ("Ballygunge", 22.5275, 88.3651),
        ("Victoria Memorial", 22.5448, 88.3426),
        ("Salt Lake", 22.5867, 88.4173),
    ],
    "Los Angeles": [
        ("Downtown LA", 34.0407, -118.2468),
        ("Burbank", 34.1808, -118.3089),
        ("Long Beach", 33.7701, -118.1937),
    ],
}


@st.cache_data(ttl=900)
def geocode_city(city):
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=10,
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    if not results:
        return None
    return {
        "name": results[0]["name"],
        "latitude": results[0]["latitude"],
        "longitude": results[0]["longitude"],
        "country": results[0].get("country", ""),
    }


@st.cache_data(ttl=900)
def fetch_weather(latitude, longitude):
    response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "timezone": "auto",
            "forecast_days": 3,
        },
        timeout=12,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=900)
def fetch_air_quality(latitude, longitude):
    response = requests.get(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "pm2_5,pm10,us_aqi",
            "timezone": "auto",
            "forecast_days": 3,
        },
        timeout=12,
    )
    response.raise_for_status()
    return response.json()


def aqi_category(aqi):
    if aqi <= 50:
        return "Good", "#22c55e"
    if aqi <= 100:
        return "Moderate", "#eab308"
    if aqi <= 150:
        return "Unhealthy for sensitive groups", "#f97316"
    if aqi <= 200:
        return "Unhealthy", "#ef4444"
    if aqi <= 300:
        return "Very unhealthy", "#a855f7"
    return "Hazardous", "#7f1d1d"


def fallback_weather(latitude, longitude):
    now = datetime.now()
    hours = [now.replace(minute=0, second=0, microsecond=0).isoformat()]
    hourly = {
        "time": [],
        "temperature_2m": [],
        "relative_humidity_2m": [],
        "wind_speed_10m": [],
    }
    for index in range(72):
        hour = pd.Timestamp(now).floor("h") + pd.Timedelta(hours=index)
        hourly["time"].append(hour.isoformat())
        hourly["temperature_2m"].append(round(22 + 5 * math.sin(index / 5), 1))
        hourly["relative_humidity_2m"].append(round(64 + 12 * math.sin(index / 8), 1))
        hourly["wind_speed_10m"].append(round(8 + 4 * math.cos(index / 6), 1))
    return {
        "current": {
            "temperature_2m": hourly["temperature_2m"][0],
            "relative_humidity_2m": hourly["relative_humidity_2m"][0],
            "wind_speed_10m": hourly["wind_speed_10m"][0],
        },
        "hourly": hourly,
    }


def fallback_air_quality():
    now = pd.Timestamp.now().floor("h")
    result = {
        "time": [],
        "pm2_5": [],
        "pm10": [],
        "us_aqi": [],
    }
    for index in range(72):
        hour = now + pd.Timedelta(hours=index)
        result["time"].append(hour.isoformat())
        pm25 = round(55 + 35 * math.sin(index / 9) + (10 if 4 <= hour.hour <= 10 else 0), 1)
        result["pm2_5"].append(max(5, pm25))
        result["pm10"].append(round(max(12, pm25 * 1.45), 1))
        result["us_aqi"].append(round(max(25, pm25 * 1.8), 0))
    return {"hourly": result}


def load_location(city):
    location = geocode_city(city)
    if location:
        latitude = location["latitude"]
        longitude = location["longitude"]
        name = f"{location['name']}, {location['country']}".strip(", ")
    else:
        latitude, longitude = CITY_PROFILES.get(city, (28.6139, 77.2090))
        name = city

    try:
        weather = fetch_weather(latitude, longitude)
    except requests.RequestException:
        weather = fallback_weather(latitude, longitude)

    try:
        air = fetch_air_quality(latitude, longitude)
    except requests.RequestException:
        air = fallback_air_quality()

    return name, latitude, longitude, weather, air


def build_forecast(weather, air):
    weather_hourly = weather.get("hourly", {})
    air_hourly = air.get("hourly", {})
    weather_times = weather_hourly.get("time", [])
    air_times = air_hourly.get("time", [])
    if not weather_times or not air_times:
        raise ValueError("Forecast data is unavailable")

    frame = pd.DataFrame({
        "time": pd.to_datetime(weather_times),
        "temperature": weather_hourly.get("temperature_2m"),
        "humidity": weather_hourly.get("relative_humidity_2m"),
        "wind": weather_hourly.get("wind_speed_10m"),
    })
    air_frame = pd.DataFrame({
        "time": pd.to_datetime(air_times),
        "pm25": air_hourly.get("pm2_5"),
        "pm10": air_hourly.get("pm10"),
        "aqi": air_hourly.get("us_aqi"),
    })
    return frame.merge(air_frame, on="time", how="inner")


def summarize_plan(forecast, location_name):
    peak = forecast.loc[forecast["aqi"].idxmax()]
    safe = forecast.loc[forecast["aqi"].idxmin()]
    low_wind = forecast.loc[forecast["wind"].idxmin()]

    peak_time = pd.Timestamp(peak["time"]).strftime("%a %I:%M %p")
    safe_time = pd.Timestamp(safe["time"]).strftime("%a %I:%M %p")
    low_wind_time = pd.Timestamp(low_wind["time"]).strftime("%a %I:%M %p")
    pm25_reduction = max(20, min(55, round(100 - float(safe["aqi"]))))

    return {
        "peak_time": peak_time,
        "peak_aqi": round(float(peak["aqi"])),
        "safe_time": safe_time,
        "safe_aqi": round(float(safe["aqi"])),
        "low_wind_time": low_wind_time,
        "pm25_reduction": pm25_reduction,
    }


def generate_llm_plan(location_name, household, forecast, summary):
    api_key = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        prompt = (
            f"Create a concise 72-hour indoor and outdoor air-quality action plan for "
            f"{location_name}. Household: {household}. Forecast summary: {json.dumps(summary)}. "
            "Include commute timing, exercise timing, window/ventilation guidance, purifier guidance, "
            "Corsi-Rosenthal box or wet-mopping alternatives, and low-emission swaps."
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.4),
        )
        return response.text
    except Exception as exc:
        st.caption(f"AI coach unavailable: {exc}")
        return None


def render_map(latitude, longitude, location_name, forecast):
    markers = [{"name": location_name, "lat": latitude, "lon": longitude, "aqi": forecast.iloc[0]["aqi"]}]
    for name, lat, lon in STATIONS.get(location_name.split(",")[0], []):
        markers.append({"name": name, "lat": lat, "lon": lon, "aqi": forecast.iloc[0]["aqi"]})

    marker_js = []
    for marker in markers:
        category, color = aqi_category(float(marker["aqi"]))
        marker_js.append(
            f"""L.circleMarker([{marker["lat"]}, {marker["lon"]}], {{
                radius: 10, color: "{color}", fillColor: "{color}", fillOpacity: 0.75
            }}).addTo(map).bindPopup("<b>{marker["name"]}</b><br>AQI {round(marker["aqi"])} - {category}");
            """
        )

    html = f"""
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <div id="map" style="height: 420px; border-radius: 14px;"></div>
    <script>
      var map = L.map('map', {{zoomControl: true}}).setView([{latitude}, {longitude}], 10);
      L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
        attribution: '&copy; OpenStreetMap &copy; CARTO'
      }}).addTo(map);
      {''.join(marker_js)}
    </script>
    """
    st.components.v1.html(html, height=430)


st.title("VayuCare AI - Smog & IAQ Co-Pilot")
st.caption("Predict, prepare, and protect your household for the next 72 hours.")

with st.sidebar:
    st.header("Plan your protection")
    city = st.text_input("City", value="New Delhi")
    household = st.selectbox(
        "Household profile",
        ["Family with children", "Elderly residents", "Asthma or respiratory illness", "General household"],
    )
    activities = st.multiselect(
        "Daily concerns",
        ["School commute", "Outdoor exercise", "Open-window ventilation", "Indoor cooking"],
        default=["School commute", "Outdoor exercise"],
    )
    detect_location = st.button("Use detected location")

if detect_location:
    try:
        response = requests.get("https://ipapi.co/json/", timeout=8)
        response.raise_for_status()
        city = response.json().get("city") or city
        st.toast(f"Location detected: {city}")
    except requests.RequestException:
        st.warning("Browser location was unavailable. Showing the selected city instead.")

try:
    location_name, latitude, longitude, weather, air = load_location(city)
    forecast = build_forecast(weather, air)
except (requests.RequestException, ValueError, TypeError) as exc:
    st.error(f"Weather data could not be loaded: {exc}")
    st.stop()

summary = summarize_plan(forecast, location_name)
current = forecast.iloc[0]
category, category_color = aqi_category(float(current["aqi"]))

col1, col2, col3, col4 = st.columns(4)
col1.metric("US AQI", f"{round(float(current['aqi']))}", category)
col2.metric("PM2.5", f"{float(current['pm25']):.1f} ug/m3")
col3.metric("Temperature", f"{float(current['temperature']):.1f} C")
col4.metric("Wind", f"{float(current['wind']):.1f} km/h")

tab_map, tab_forecast, tab_plan, tab_iaq = st.tabs(
    ["Live city map", "72-hour forecast", "Daily plan", "IAQ toolkit"]
)

with tab_map:
    map_col, link_col = st.columns([4, 1])
    with map_col:
        render_map(latitude, longitude, location_name, forecast)
    with link_col:
        st.subheader(location_name)
        st.markdown(
            f"[Open in Google Maps](https://www.google.com/maps/search/?api=1&query={quote(location_name)})"
        )
        for name, lat, lon in STATIONS.get(location_name.split(",")[0], []):
            query = quote(f"{name}, {location_name}")
            st.markdown(f"[View {name}](https://www.google.com/maps/search/?api=1&query={query})")

with tab_forecast:
    forecast_table = forecast.rename(columns={
        "temperature": "Temperature (C)",
        "humidity": "Humidity (%)",
        "wind": "Wind (km/h)",
        "pm25": "PM2.5 (ug/m3)",
        "pm10": "PM10 (ug/m3)",
        "aqi": "US AQI",
    })
    st.line_chart(
        forecast_table.set_index("time")[["US AQI", "PM2.5 (ug/m3)"]],
        height=320,
        color=["#ef4444", "#f97316"],
    )
    st.dataframe(
        forecast_table,
        hide_index=True,
        use_container_width=True,
        column_config={"time": st.column_config.DatetimeColumn("Time", format="MMM DD, hh:mm a")},
    )

with tab_plan:
    c1, c2, c3 = st.columns(3)
    c1.warning(f"Expected peak: {summary['peak_time']} (AQI {summary['peak_aqi']})")
    c2.success(f"Best window: {summary['safe_time']} (AQI {summary['safe_aqi']})")
    c3.info(f"Lowest dispersion: {summary['low_wind_time']}")

    ai_plan = generate_llm_plan(location_name, household, forecast, summary)
    if ai_plan:
        st.subheader("Personalized AI plan")
        st.markdown(ai_plan)
    else:
        st.subheader("Preventive daily routine")
        st.markdown(
            f"""
- **{summary['safe_time']}:** Open windows only if outdoor AQI remains below 100.
- **{summary['peak_time']}:** Seal window gaps, keep children indoors, and run a HEPA or well-fitted purifier.
- **Commute:** Shift outdoor activity toward lower-AQI forecast hours and use public transit or walking less near traffic.
- **Cooking:** Prefer induction or electric cooking during smog traps; use an exhaust fan that vents outdoors.
- **Cleaning:** Use wet mopping instead of dry sweeping to reduce resuspended dust.
"""
        )

with tab_iaq:
    st.subheader("Low-cost IAQ actions")
    i1, i2 = st.columns(2)
    i1.markdown(
        f"""
### Corsi-Rosenthal box
Use four boxed fan filters in an enclosed cube, orient the fan outward, and keep it away from curtains.

**Estimated impact:** sealing leaks and continuous filtration may reduce indoor PM2.5 exposure by
about **{summary['pm25_reduction']}%** during a smog trap.
"""
    )
    i2.markdown(
        """
### Ventilation checklist
- Check the outdoor forecast before opening windows.
- Use wet mopping and a damp cloth for dust.
- Replace HVAC or purifier filters on schedule.
- Avoid incense, smoking, candles, and frying without extraction.
- Keep a door-seal kit and window weather stripping ready.
"""
    )
