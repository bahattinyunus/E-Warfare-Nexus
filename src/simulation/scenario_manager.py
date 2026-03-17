import numpy as np

class ScenarioManager:
    """
    Generates realistic Electronic Warfare scenarios with pulses and noise.
    """
    def __init__(self, sample_rate=1e6):
        self.sample_rate = sample_rate
        # Center of our 1x1km theater (lat/lon approximately)
        self.center_pos = (39.925, 32.866)
        self.field_width_m = 1000.0

    def calculate_path_loss(self, distance_m, freq_hz):
        """Simplistic Free Space Path Loss (FSPL) model."""
        if distance_m < 1.0: distance_m = 1.0
        c = 3e8
        loss_db = 20 * np.log10(distance_m) + 20 * np.log10(freq_hz) - 147.55
        return 10**(-loss_db / 20.0)

    def get_scenario_signal(self, scenario_name, duration=0.01, sensor_pos=(0, 0), custom_emitters=None):
        """
        Returns a signal based on predefined scenarios, now with spatial context.
        :param sensor_pos: (x, y) relative to center in meters.
        :param custom_emitters: optional list of emitters to override scenario defaults.
        """
        # Define target positions (x, y) in meters relative to center
        # scenario_name -> list of (pos, type, params)
        emitters = {
            "Drone Swarm": [
                ((200, 300), "Remote-ID", {"freq": 150e3}),
                ((-150, 400), "Remote-ID", {"freq": 160e3})
            ],
            "Tracking Radar": [
                ((800, 800), "Radar", {"freq": 450e3, "pri": 0.4e-3, "pw": 5e-6})
            ],
            "FHSS Comms": [
                ((0, 500), "FHSS", {"hop_freqs": [100e3, 200e3, 300e3], "dwell": 0.002})
            ],
            "LoRa Sensors": [
                ((100, 100), "LoRa", {"sf": 7, "bw": 125e3, "symbol": 42})
            ]
        }
        
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        combined_signal = np.zeros_like(t)
        
        active_emitters = custom_emitters if custom_emitters is not None else emitters.get(scenario_name, [])
        if not active_emitters and scenario_name != "Clear Sky":
            # Fallback to old behavior for legacy names
            return self._legacy_get_scenario_signal(scenario_name, duration)

        from src.signal_processing.generator import SignalGenerator
        gen = SignalGenerator(self.sample_rate)

        for pos, type, params in active_emitters:
            dist = np.sqrt((pos[0] - sensor_pos[0])**2 + (pos[1] - sensor_pos[1])**2)
            atten = self.calculate_path_loss(dist, params.get("freq", 150e3))
            
            if type == "Remote-ID":
                _, s = gen.generate_cw(params["freq"], duration, amplitude=atten)
            elif type == "Radar":
                _, s = gen.generate_pulsed(params["freq"], params["pri"], params["pw"], duration, amplitude=atten)
            elif type == "FHSS":
                _, s = gen.generate_fhss(params["hop_freqs"], params["dwell"], duration, amplitude=atten)
            elif type == "LoRa":
                _, s = gen.generate_lora(params["sf"], params["bw"], params["symbol"], duration, amplitude=atten)
            else:
                s = np.zeros_like(t)
                
            combined_signal = gen.add_signals(combined_signal, s)
            
        # Add background noise
        noise = np.random.normal(0, 0.05, len(t))
        return t, combined_signal + noise

    def _legacy_get_scenario_signal(self, scenario_name, duration):
        # ... (Implementation similar to original to maintain backward compatibility)
        if scenario_name == "Long Range Search":
            return self._generate_pulse_stream(150e3, 2e-3, 100e-6, duration)
        # etc.
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        return t, np.random.normal(0, 0.1, len(t))

    def _generate_pulse_stream(self, freq, pri, pw, duration, amplitude=1.0):
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        signal = np.zeros_like(t)
        num_pulses = int(duration / pri)
        for i in range(num_pulses):
            start_t = i * pri
            if start_t + pw > duration: break
            idx_s = int(start_t * self.sample_rate)
            idx_e = int((start_t + pw) * self.sample_rate)
            signal[idx_s:idx_e] = amplitude * np.cos(2 * np.pi * freq * t[idx_s:idx_e])
        return t, signal

    def export_dataset(self, scenario_name, num_samples, filename_prefix="dataset"):
        """
        Exports multiple signals of a scenario to a NumPy array for DL training.
        """
        import os
        import time
        
        logging_msg = f"Generating dataset for {scenario_name}..."
        print(logging_msg)
        dataset = []
        for _ in range(num_samples):
            # Vary duration slightly to add variance to the data
            dur = np.random.uniform(0.008, 0.012)
            t, signal = self.get_scenario_signal(scenario_name, duration=dur)
            dataset.append(signal)

        # Pad or truncate to a fixed size so we can stack
        ref_size = int(self.sample_rate * 0.01)
        dataset_padded = []
        for sig in dataset:
            if len(sig) > ref_size:
                dataset_padded.append(sig[:ref_size])
            else:
                dataset_padded.append(np.pad(sig, (0, ref_size - len(sig)), 'constant'))
                
        dataset_np = np.stack(dataset_padded)
        
        os.makedirs("data", exist_ok=True)
        filename = f"data/{filename_prefix}_{scenario_name.replace(' ', '_')}_{int(time.time())}.npy"
        np.save(filename, dataset_np)
        print(f"Exported {num_samples} samples to {filename}")
        return filename
