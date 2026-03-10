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


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Weather App</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            input { padding: 10px; font-size: 16px; width: 150px; }
            button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
            #weather { margin-top: 20px; padding: 20px; background: #f0f0f0; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>Weather App</h1>
        <div style="margin-bottom: 20px;">
            <input type="text" id="city" placeholder="City name" style="width: 200px;">
            <button onclick="searchCity()">Search</button>
        </div>
        <div>
            <input type="text" id="lat" placeholder="Latitude">
            <input type="text" id="lon" placeholder="Longitude">
            <button onclick="getWeather()">Get Weather</button>
        </div>
        <div id="weather"></div>
        
        <script>
            async function searchCity() {
                const city = document.getElementById('city').value;
                const div = document.getElementById('weather');
                
                if (!city) {
                    div.innerHTML = 'Please enter a city name';
                    return;
                }
                
                div.innerHTML = 'Searching...';
                
                try {
                    const res = await fetch(`/search?q=${encodeURIComponent(city)}`);
                    const data = await res.json();
                    
                    if (data.results && data.results.length > 0) {
                        const result = data.results[0];
                        document.getElementById('lat').value = result.latitude;
                        document.getElementById('lon').value = result.longitude;
                        div.innerHTML = `Found: ${result.name}, ${result.country}`;
                    } else {
                        div.innerHTML = 'City not found';
                    }
                } catch (e) {
                    div.innerHTML = 'Error searching city';
                }
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
                    
                    div.innerHTML = `
                        <h2>Weather</h2>
                        <p><strong>Temperature:</strong> ${data.current.temperature_2m}°C</p>
                        <p><strong>Weather:</strong> ${data.current.weather_code}</p>
                        <p><strong>Wind:</strong> ${data.current.wind_speed_10m} km/h</p>
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
        return resp.json()


@app.get("/search")
async def search_city(q: str):
    async with httpx.AsyncClient() as client:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count=5&language=en&format=json"
        resp = await client.get(url)
        return resp.json()
