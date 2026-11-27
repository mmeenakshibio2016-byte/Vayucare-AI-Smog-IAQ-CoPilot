# Vayu care-AI-Smog-IAQ-CoPilot
Problem Statement:
Severe air pollution in major metropolitan cities—such as Delhi, Kolkata, and Los Angeles—is increasingly disrupting daily household routines and threatening family health. Current air quality tools provide reactive, real-time readings rather than actionable, forward-looking guidance. To protect households and save lives, VayuCare AI (Smog & IAQ Co-Pilot) bridges this gap by functioning as a predictive, future-focused weather and air quality forecasting application. By combining hyper-local meteorological forecasting with Generative AI, the application predicts upcoming pollution spikes and empowers families with personalized, preventative daily routines, indoor air quality (IAQ) optimizations, and sustainable lifestyle alternatives.
Cause and Effect:
The winter smog is caused due to a combination of seasonal meteorological factors—specifically temperature inversions, low wind speeds, and high humidity—interacting with heavy urban emissions from vehicular traffic, industrial output, construction dust, and seasonal agricultural crop burning. Because cold, dense air gets trapped beneath a layer of warm air, these pollutants cannot disperse into the upper atmosphere, leading to toxic stagnation at ground level. As a result, hazardous particulate matter ($PM_{2.5}$ and $PM_{10}$) infiltrates homes, severely degrading indoor air quality, triggering acute respiratory and cardiovascular illnesses, and forcing families to alter their daily work, school, and outdoor routines without clear guidance on how to mitigate their exposure.
Project Blue Print:
1. Core Application ArchitecturePredictive Weather & AQI Engine: Integrates meteorological APIs (e.g., OpenWeatherMap, AQICN, or Open-Meteo) to fetch 3-to-7-day forecasts for temperature, wind speed, humidity, and atmospheric pressure. The system uses these weather variables to predict "Smog Trap" windows before $PM_{2.5}$ levels peak.
2. GenAI Co-Pilot (LLM Integration): Feeds the localized weather forecast, city profile (e.g., Delhi's winter inversion vs. Los Angeles's photochemical smog), and user household profile (e.g., presence of children, elderly, asthma patients, or gas stoves) into an LLM prompt to generate hyper-personalized daily action plans.
3. Impact Quantifier: Translates abstract AQI numbers and recommended actions into tangible health and environmental metrics (e.g., "Running your exhaust fan and sealing window drafts during tomorrow's 6 AM–10 AM temperature inversion reduces indoor $PM_{2.5}$ exposure by ~40%, equivalent to avoiding 3 passive cigarettes").
2. Key User Features
1.72-Hour Smog & Ventilation Forecast: A timeline showing when outdoor air will be safe enough to open windows for cross-ventilation versus when to seal the home and run air purifiers or DIY box-fan filters.

2.Low-Emission Daily Routine Planner: Suggests optimal times for outdoor exercise, school commutes, and errands based on predicted wind dispersion patterns, alongside low-emission household swaps (e.g., induction cooking over gas during low-ventilation hours, wet-mopping instead of dry-sweeping).

3.DIY Indoor Air Quality (IAQ) Hacks: Cost-effective, accessible solutions tailored to local living conditions, such as building a Corsi-Rosenthal box, strategic placement of indoor air-purifying plants, and natural humidity control to settle airborne dust.
Interactive Dark-Mode City Smog & Wind Map (#smog-leaflet-map) + Google Maps Integration:

Connected New Delhi, Kolkata, Los Angeles, and any searched or GPS-detected city on an interactive dark-mode map with pulsing AQI markers, clickable neighborhood monitoring stations (e.g., Anand Vihar, ITO, RK Puram in Delhi; Ballygunge, Victoria Memorial, Salt Lake in Kolkata; Downtown LA, Burbank, Long Beach in LA), a one-click Google Maps View embed toggle, and a direct Open in Google Maps link.

Global City Search & Live Open-Meteo 72-Hour Weather & Air Quality Engine:

Integrated Open-Meteo's Geocoding, Weather Forecast, and Air Quality APIs so selecting any city marker, searching any city worldwide, or clicking Detect My Weather fetches real-time temperature, humidity, wind vectors, 
PM2.5,PM 2.5 and 72-hour hourly AQI forecasts (with instant fallback data when offline).

## Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run Server.py
```

## Deploy on Streamlit Community Cloud

1. Push this repository, including `Server.py` and `requirements.txt`, to GitHub.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), create an app from this repository and select the branch and `Server.py` as the app entry point.
3. Optionally add a `GOOGLE_API_KEY` secret in the app's settings to enable the personalized Gemini plan. The app works without this secret.

Streamlit Community Cloud installs dependencies from `requirements.txt` automatically.



