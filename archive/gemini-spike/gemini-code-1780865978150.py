import asyncio
import json
import random
from datetime import datetime
import requests
from kafka import KafkaProducer

REDPANDA_BROKER = "localhost:19092"
TOPIC_NAME = "chapeco-traffic-events"

def get_chapeco_nodes():
    url = "[https://overpass-api.de/api/interpreter](https://overpass-api.de/api/interpreter)"
    query = """
    [out:json][timeout:25];
    area["name"="Chapecó"]->.searchArea;
    (node["highway"="traffic_signals"](area.searchArea););
    out body;
    """
    try:
        response = requests.post(url, data={"data": query})
        if response.status_code == 200:
            elements = response.json().get("elements", [])
            nodes = []
            for el in elements:
                nodes.append({
                    "id": f"osm_node_{el['id']}",
                    "lat": el["lat"],
                    "lon": el["lon"],
                    "name": el.get("tags", {}).get("name", "Cruzamento Urbano")
                })
            return nodes if nodes else get_fallback_nodes()
    except Exception as e:
        print(f"OSM Fetch failed, utilizing local fallback cluster: {e}")
        return get_fallback_nodes()

def get_fallback_nodes():
    return [
        {"id": "fallback_efapi_1", "lat": -27.1145, "lon": -52.6412, "name": "Av. Attilio Fontana x Rua Cunha Porã"},
        {"id": "fallback_centro_1", "lat": -27.1001, "lon": -52.6148, "name": "Av. Getúlio Vargas x Rua Uruguai"}
    ]

async run_intersection_simulation(producer, node):
    intersection_id = node["id"]
    lat, lon = node["lat"], node["lon"]
    name = node["name"]
    is_adaptive_node = "Attilio Fontana" in name or "fallback_efapi" in intersection_id

    while True:
        now = datetime.now()
        current_hour = now.hour

        # Nocturnal Safety Flashing Yellow (00:00 - 06:00)
        if 0 <= current_hour < 6:
            payload = build_payload(intersection_id, name, lat, lon, "FLASHING_YELLOW", 0.0, 45.0, False, False, 0, now)
            producer.send(TOPIC_NAME, value=json.dumps(payload).encode('utf-8'))
            await asyncio.sleep(10)
            continue

        is_peak = (7 <= current_hour <= 9) or (17 <= current_hour <= 19)
        macro_cycle = 150 if is_peak else 120
        state = random.choice(["GREEN", "RED"])
        sensor_override = False
        stop_duration = round(random.uniform(15.0, float(macro_cycle // 2)), 1) if state == "RED" else 0.0
        speed = 48.5 if state == "GREEN" else 0.0

        if state == "GREEN" and is_adaptive_node:
            if random.uniform(0.5, 6.0) > 3.0:
                sensor_override = True
                speed = 52.0 

        payload = build_payload(intersection_id, name, lat, lon, state, stop_duration, speed, sensor_override, is_peak, macro_cycle, now)
        producer.send(TOPIC_NAME, value=json.dumps(payload).encode('utf-8'))
        await asyncio.sleep(random.uniform(3.0, 7.0))

def build_payload(id, name, lat, lon, state, stop, speed, override, peak, cycle, ts):
    return {
        "intersection_id": id,
        "location": {"description": name, "latitude": lat, "longitude": lon},
        "telemetry": {
            "current_signal_state": state,
            "measured_stop_duration_seconds": stop,
            "observed_vehicle_speed_kmh": speed,
            "sensor_gap_triggered_override": override
        },
        "environment": {
            "is_peak_hour_cycle": peak,
            "macro_cycle_setting_seconds": cycle,
            "timestamp": ts.isoformat()
        }
    }

async def main():
    producer = KafkaProducer(bootstrap_servers=[REDPANDA_BROKER])
    intersections = get_chapeco_nodes()
    tasks = [run_intersection_simulation(producer, node) for node in intersections]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())