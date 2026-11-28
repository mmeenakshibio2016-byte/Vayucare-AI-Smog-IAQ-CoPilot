import os
import unittest
from unittest.mock import patch

import pandas as pd
import requests
from streamlit.testing.v1 import AppTest


class MockResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class ServerAppTests(unittest.TestCase):
    def setUp(self):
        import streamlit as st

        st.cache_data.clear()
        self.times = pd.date_range(
            pd.Timestamp.now().floor("h"),
            periods=72,
            freq="h",
        ).strftime("%Y-%m-%dT%H:00").tolist()

    def tearDown(self):
        import streamlit as st

        st.cache_data.clear()

    def live_api_response(self, url, **kwargs):
        if "geocoding-api" in url:
            return MockResponse({
                "results": [{
                    "name": "New Delhi",
                    "latitude": 28.6139,
                    "longitude": 77.209,
                    "country": "India",
                }]
            })
        if "air-quality" in url:
            return MockResponse({
                "hourly": {
                    "time": self.times,
                    "pm2_5": [45.0] * 72,
                    "pm10": [70.0] * 72,
                    "us_aqi": [90.0] * 72,
                }
            })
        return MockResponse({
            "hourly": {
                "time": self.times,
                "temperature_2m": [20.0] * 72,
                "relative_humidity_2m": [60.0] * 72,
                "wind_speed_10m": [8.0] * 72,
            }
        })

    def run_without_genai_key(self, app, request_mock):
        with (
            patch("requests.get", side_effect=request_mock),
            patch.dict(os.environ, {"GOOGLE_API_KEY": ""}),
            patch("streamlit.secrets", {}),
        ):
            app.run()

    @staticmethod
    def offline_api_request(*args, **kwargs):
        raise requests.Timeout("offline")

    def test_plan_tracks_selected_activities(self):
        app = AppTest.from_file("Server.py", default_timeout=30)
        with (
            patch("requests.get", side_effect=self.live_api_response),
            patch.dict(os.environ, {"GOOGLE_API_KEY": ""}),
            patch("streamlit.secrets", {}),
        ):
            app.run()
            self.assertFalse(app.exception, app.exception)
            self.assertTrue(any("School commute" in item.value for item in app.markdown))
            self.assertTrue(any("Exercise" in item.value for item in app.markdown))

            app.multiselect[0].set_value(["Indoor cooking"])
            app.run()

        self.assertFalse(app.exception, app.exception)
        self.assertTrue(any("Cooking" in item.value for item in app.markdown))
        self.assertFalse(any("School commute:" in item.value for item in app.markdown))

    def test_offline_forecast_is_disclosed(self):
        app = AppTest.from_file("Server.py", default_timeout=30)
        self.run_without_genai_key(
            app,
            self.offline_api_request,
        )

        self.assertFalse(app.exception, app.exception)
        self.assertTrue(any("Estimated offline values" in item.value for item in app.warning))

    def test_unknown_city_does_not_use_default_city_coordinates(self):
        app = AppTest.from_file("Server.py", default_timeout=30)

        def city_lookup(url, **kwargs):
            if "geocoding-api" in url:
                city = kwargs["params"]["name"]
                if city == "Atlantis":
                    return MockResponse({"results": []})
            return self.live_api_response(url, **kwargs)

        with (
            patch("requests.get", side_effect=city_lookup),
            patch.dict(os.environ, {"GOOGLE_API_KEY": ""}),
            patch("streamlit.secrets", {}),
        ):
            app.run()
            app.text_input[0].set_value("Atlantis")
            app.run()

        self.assertFalse(app.exception, app.exception)
        self.assertTrue(any("Could not find coordinates" in item.value for item in app.error))


if __name__ == "__main__":
    unittest.main()
