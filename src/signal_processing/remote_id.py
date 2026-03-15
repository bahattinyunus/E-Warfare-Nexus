import json
import time

class RemoteIDDecoder:
    """
    Decodes ASTM F3411 / ASD-STAN 4709-002 Remote-ID Broadcasts.
    Used for Drone SIGINT (Signal Intelligence).
    """
    def __init__(self):
        self.active_drones = {}

    def decode_packet(self, data):
        """
        Simulates parsing a Remote-ID packet.
        In reality, this would parse Wi-Fi Beacon elements or BT AD structures.
        """
        try:
            # Simulated parsing logic: identifies ID, Location, Altitude
            # Check for magic signatures or preamble (Simulated)
            drone_id = data.get("uas_id", "Unknown-UAV")
            
            telemetry = {
                "uas_id": drone_id,
                "lat": data.get("lat", 0.0),
                "lon": data.get("lon", 0.0),
                "alt": data.get("alt", 0.0),
                "velocity": data.get("speed", 0.0),
                "pilot_lat": data.get("pilot_lat", 0.0),
                "pilot_lon": data.get("pilot_lon", 0.0),
                "last_seen": time.time(),
                "type": data.get("uas_type", "Multi-Rotor")
            }
            
            self.active_drones[drone_id] = telemetry
            return telemetry
        except Exception as e:
            print(f"[HATA] Remote-ID çözme hatası: {e}")
            return None

    def get_tactical_picture(self):
        """Returns the current list of active drones in range."""
        # Clean up stale drones (not seen for > 10 seconds)
        now = time.time()
        self.active_drones = {id: d for id, d in self.active_drones.items() if now - d["last_seen"] < 10}
        return self.active_drones

if __name__ == "__main__":
    # Test case
    decoder = RemoteIDDecoder()
    test_packet = {
        "uas_id": "TR-D62719",
        "uas_type": "Fixed-Wing",
        "lat": 39.9334,
        "lon": 32.8597,
        "alt": 150.5,
        "speed": 15.2,
        "pilot_lat": 39.9300,
        "pilot_lon": 32.8500
    }
    
    result = decoder.decode_packet(test_packet)
    print(f"Decoded Drone: {result['uas_id']} at {result['lat']}, {result['lon']}")
