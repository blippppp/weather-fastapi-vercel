from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Rime Fog",
    51: "Light Drizzle",
    53: "Drizzle",
    55: "Heavy Drizzle",
    56: "Light Freezing Drizzle",
    57: "Freezing Drizzle",
    61: "Light Rain",
    63: "Rain",
    65: "Heavy Rain",
    66: "Light Freezing Rain",
    67: "Freezing Rain",
    71: "Light Snow",
    73: "Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    80: "Light Showers",
    81: "Showers",
    82: "Heavy Showers",
    85: "Light Snow Showers",
    86: "Snow Showers",
    95: "Thunderstorm",
    96: "Light Thunderstorm with Hail",
    99: "Thunderstorm with Hail",
}


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Weather App</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            input { padding: 10px; font-size: 16px; }
            button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
            .city-input { width: 200px; }
            .coord-input { width: 120px; }
            #weather { margin-top: 20px; padding: 20px; background: #f0f0f0; border-radius: 8px; }
            .city-result { padding: 10px; margin: 5px 0; background: #e0e0e0; cursor: pointer; border-radius: 4px; }
            .city-result:hover { background: #d0d0d0; }
            .weather-card { text-align: center; }
            .temp { font-size: 48px; font-weight: bold; }
            .condition { font-size: 24px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>Weather App</h1>
        <div style="margin-bottom: 20px;">
            <input type="text" id="city" class="city-input" placeholder="City name" onkeydown="if(event.key==='Enter')searchCity()">
            <button onclick="searchCity()">Search</button>
        </div>
        <div id="results"></div>
        <div style="margin-top: 20px;">
            <input type="text" id="lat" class="coord-input" placeholder="Latitude" onkeydown="if(event.key==='Enter')getWeather()">
            <input type="text" id="lon" class="coord-input" placeholder="Longitude" onkeydown="if(event.key==='Enter')getWeather()">
            <button onclick="getWeather()">Get Weather</button>
        </div>
        <div id="weather"></div>
        
        <script>
            async function searchCity() {
                const city = document.getElementById('city').value;
                const div = document.getElementById('results');
                
                if (!city) {
                    div.innerHTML = 'Please enter a city name';
                    return;
                }
                
                div.innerHTML = 'Searching...';
                
                try {
                    const res = await fetch(`/search?q=${encodeURIComponent(city)}`);
                    const data = await res.json();
                    
                    if (data.results && data.results.length > 0) {
                        let html = '<p>Select a city:</p>';
                        data.results.forEach((r, i) => {
                            html += `<div class="city-result" onclick="selectCity(${r.latitude}, ${r.longitude}, '${r.name}, ${r.country}')">${r.name}, ${r.country}</div>`;
                        });
                        div.innerHTML = html;
                    } else {
                        div.innerHTML = 'City not found';
                    }
                } catch (e) {
                    div.innerHTML = 'Error searching city';
                }
            }
            
            function selectCity(lat, lon, name) {
                document.getElementById('lat').value = lat;
                document.getElementById('lon').value = lon;
                document.getElementById('results').innerHTML = `Selected: ${name}`;
                getWeather();
            }
            
            async function getWeather() {
                const lat = document.getElementById('lat').value;
                const lon = document.getElementById('lon').value;
                const div = document.getElementById('weather');
                
                if (!lat || !lon) {
                    div.innerHTML = 'Please enter both latitude and longitude';
                    return;
                }
                
                div.innerHTML = 'Loading...';
                
                try {
                    const res = await fetch(`/weather?lat=${lat}&lon=${lon}`);
                    const data = await res.json();
                    
                    const code = data.current.weather_code;
                    const desc = data.current.weather_description || 'Unknown';
                    
                    div.innerHTML = `
                        <div class="weather-card">
                            <div class="temp">${data.current.temperature_2m}°C</div>
                            <div class="condition">${desc}</div>
                            <p>Wind: ${data.current.wind_speed_10m} km/h</p>
                        </div>
                    `;
                } catch (e) {
                    div.innerHTML = 'Error fetching weather';
                }
            }
        </script>
    </body>
    </html>
    """


@app.get("/weather")
async def get_weather(lat: float, lon: float):
    async with httpx.AsyncClient() as client:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m"
        resp = await client.get(url)
        data = resp.json()
        code = data.get("current", {}).get("weather_code", 0)
        data["current"]["weather_description"] = WEATHER_CODES.get(code, f"Code {code}")
        return data


@app.get("/search")
async def search_city(q: str):
    async with httpx.AsyncClient() as client:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count=5&language=en&format=json"
        resp = await client.get(url)
        return resp.json()
