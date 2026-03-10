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
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🌤️</text></svg>">
        <!-- Leaflet CSS (no integrity to avoid blocking in some browsers) -->
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            input { padding: 10px; font-size: 16px; }
            button { padding: 10px 20px; font-size: 16px; cursor: pointer; }
            .city-input { width: 200px; }
            .coord-input { width: 120px; }
            #weather { margin-top: 20px; padding: 20px; background: #f0f0f0; border-radius: 8px; display: none; }
            #results { margin-top: 10px; }
            .city-result { padding: 10px; margin: 5px 0; background: #e0e0e0; cursor: pointer; border-radius: 4px; }
            .city-result:hover { background: #d0d0d0; }
            .weather-card { text-align: center; }
            .temp { font-size: 48px; font-weight: bold; }
            .condition { font-size: 24px; margin: 10px 0; }
            /* map styles */
            #map { height: 320px; margin-top: 12px; display: none; border-radius: 8px; }
            .map-toggle { margin-top: 10px; }
        </style>
        <!-- Leaflet JS (no integrity to avoid blocking in some browsers) -->
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    </head>
    <body>
        <h1>Weather App</h1>
        <div style="margin-bottom: 10px;">
            <button onclick="getCurrentLocation()" style="background:#4CAF50;color:white;">📍 Use My Location</button>
        </div>
        <div style="margin-bottom: 20px;">
            <input type="text" id="city" class="city-input" placeholder="City name" onkeydown="if(event.key==='Enter')searchCity()">
            <button onclick="searchCity()">Search</button>
        </div>
        <div id="results"></div>
        <div style="margin-top: 20px;">
            <input type="text" id="lat" class="coord-input" placeholder="Latitude" onkeydown="if(event.key==='Enter')getWeather()">
            <input type="text" id="lon" class="coord-input" placeholder="Longitude" onkeydown="if(event.key==='Enter')getWeather()">
            <button onclick="getWeather()">Get Weather</button>
            <button class="map-toggle" onclick="toggleMap()">🗺️ Toggle Map</button>
        </div>
        <div id="map"></div>
        <div id="weather"></div>
        
        <script>
            function getCurrentLocation() {
                const div = document.getElementById('weather');
                if (!navigator.geolocation) {
                    div.innerHTML = 'Geolocation not supported';
                    div.style.display = 'block';
                    return;
                }
                div.innerHTML = 'Getting location...';
                div.style.display = 'block';
                
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const lat = position.coords.latitude.toFixed(4);
                        const lon = position.coords.longitude.toFixed(4);
                        document.getElementById('lat').value = lat;
                        document.getElementById('lon').value = lon;
                        locationName = 'Your Location';
                        locationTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                        getWeather();
                    },
                    (error) => {
                        div.innerHTML = 'Error: ' + error.message;
                    }
                );
            }
            
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
                            const details = `${r.latitude.toFixed(2)}, ${r.longitude.toFixed(2)} • ${r.admin1 || ''} • Pop: ${r.population ? r.population.toLocaleString() : 'N/A'}`;
                            html += `<div class="city-result" onclick="selectCity(${r.latitude}, ${r.longitude}, '${r.name}, ${r.country}', '${r.timezone}')">
                                <strong>${r.name}, ${r.country}</strong><br>
                                <small>${details}</small>
                            </div>`;
                        });
                        div.innerHTML = html;
                        // center map on first result if map initialized
                        const first = data.results[0];
                        if (window._map && first) {
                            const latlng = [first.latitude, first.longitude];
                            _map.setView(latlng, 10);
                            if (_marker) _marker.setLatLng(latlng);
                            else _marker = L.marker(latlng).addTo(_map);
                        }
                    } else {
                        div.innerHTML = 'City not found';
                    }
                } catch (e) {
                    div.innerHTML = 'Error searching city';
                }
            }

            function toggleMap() {
                const mapEl = document.getElementById('map');
                if (mapEl.style.display === 'block') {
                    mapEl.style.display = 'none';
                } else {
                    mapEl.style.display = 'block';
                    if (!window._leafletInit) initMap();
                }
            }

            let _map, _marker;
            function initMap() {
                window._leafletInit = true;
                _map = L.map('map').setView([20,0], 2);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                }).addTo(_map);

                _map.on('click', function(e) {
                    const lat = e.latlng.lat.toFixed(4);
                    const lon = e.latlng.lng.toFixed(4);
                    document.getElementById('lat').value = lat;
                    document.getElementById('lon').value = lon;
                    // reverse geocode to get place name and timezone
                    fetch(`/reverse?lat=${lat}&lon=${lon}`)
                        .then(r => r.json())
                        .then(info => {
                            if (info && info.name) {
                                locationName = info.name + (info.country ? (', ' + info.country) : '');
                                if (info.timezone) locationTimezone = info.timezone;
                                document.getElementById('results').innerHTML = `Selected: ${locationName}`;
                            } else {
                                locationName = `Map: ${lat}, ${lon}`;
                                document.getElementById('results').innerHTML = `Selected: ${locationName}`;
                            }
                        })
                        .catch(()=>{
                            locationName = `Map: ${lat}, ${lon}`;
                            document.getElementById('results').innerHTML = `Selected: ${locationName}`;
                        });
                    if (_marker) _marker.setLatLng(e.latlng);
                    else _marker = L.marker(e.latlng).addTo(_map);
                    getWeather();
                });
            }
            
            let locationName = '';
            let locationTimezone = '';
            
            function selectCity(lat, lon, name, tz) {
                locationName = name;
                locationTimezone = tz;
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
                div.style.display = 'block';
                
                try {
                    const tzParam = locationTimezone ? `&timezone=${encodeURIComponent(locationTimezone)}` : '';
                    const res = await fetch(`/weather?lat=${lat}&lon=${lon}${tzParam}`);
                    const data = await res.json();
                    
                    const code = data.current.weather_code;
                    const desc = data.current.weather_description || 'Unknown';
                    const c = data.current;
                    const tz = locationTimezone || data.timezone || '';
                    const weatherTime = c.time ? c.time.replace('T', ' ').slice(0, 16) : '';
                    
                    let sunData = '';
                    if (data.daily && data.daily.sunrise && data.daily.sunrise[0]) {
                        const sunrise = data.daily.sunrise[0].split('T')[1];
                        const sunset = data.daily.sunset[0].split('T')[1];
                        sunData = `
                            <div style="margin-top:15px;padding:10px;background:#fff3cd;border-radius:6px;">
                                🌅 Sunrise: ${sunrise} | 🌇 Sunset: ${sunset}
                            </div>
                        `;
                    }
                    
                    div.innerHTML = `
                        <div class="weather-card">
                            <h2>${locationName || 'Weather'}</h2>
                            ${tz ? '<p style="color:#666;" id="currentTime"></p>' : ''}
                            ${weatherTime ? '<p style="color:#999;font-size:12px;">Weather updated: ' + weatherTime + '</p>' : ''}
                            <div class="temp">${c.temperature_2m}°C</div>
                            <div class="condition">${desc}</div>
                            ${sunData}
                            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:15px;text-align:left;">
                                <div>🌡️ Feels like: ${c.apparent_temperature}°C</div>
                                <div>💧 Humidity: ${c.relative_humidity_2m}%</div>
                                <div>🌬️ Wind: ${c.wind_speed_10m} km/h</div>
                                <div>🧭 Wind dir: ${c.wind_direction_10m}°</div>
                                <div>☁️ Cloud cover: ${c.cloud_cover}%</div>
                                <div>📊 Pressure: ${c.pressure_msl} hPa</div>
                            </div>
                        </div>
                    `;
                    
                    if (tz) {
                        updateClock(tz);
                    }
                } catch (e) {
                    div.innerHTML = 'Error fetching weather';
                }
            }
            
            let clockInterval;
            function updateClock(timezone) {
                if (clockInterval) clearInterval(clockInterval);
                const timeEl = document.getElementById('currentTime');
                if (!timeEl) return;
                
                function tick() {
                    const now = new Date();
                    const fmt = new Intl.DateTimeFormat('en-US', {
                        timeZone: timezone,
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                        weekday: 'short',
                        day: 'numeric',
                        month: 'short'
                    });
                    timeEl.innerHTML = '🕐 ' + fmt.format(now);
                }
                tick();
                clockInterval = setInterval(tick, 1000);
            }
        </script>
    </body>
    </html>
    """


@app.get("/weather")
async def get_weather(lat: float, lon: float, timezone: str = ""):
    async with httpx.AsyncClient() as client:
        tz_param = f"&timezone={timezone}" if timezone else ""
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl,cloud_cover&daily=sunrise,sunset{tz_param}"
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


@app.get("/reverse")
async def reverse_geocode(lat: float, lon: float):
    async with httpx.AsyncClient() as client:
        url = f"https://geocoding-api.open-meteo.com/v1/reverse?latitude={lat}&longitude={lon}&format=json"
        resp = await client.get(url)
        return resp.json()


@app.get("/favicon.ico")
async def favicon():
    return ""


@app.get("/favicon.png")
async def favicon_png():
    return ""


@app.get("/apple-touch-icon.png")
async def apple_icon():
    return ""


@app.get("/favicon.png")
async def favicon_png():
    return ""
