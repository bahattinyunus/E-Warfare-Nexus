# E-Warfare-Nexus: Taktik Kontrol Modülü (Proje Ekibi İçin)
import time
import numpy as np
from src.signal_processing.generator import SignalGenerator
from src.signal_processing.analyzer import SpectrumAnalyzer, ParameterExtractor, HopTracker
from src.signal_processing.remote_id import RemoteIDDecoder
from src.signal_processing.doa_estimator import DOAEstimator
from src.signal_processing.lpi_detector import LPIDetector
from src.ai_engine.classifier import SignalClassifier
from src.ai_engine.autonomy_manager import AutonomyManager
from src.jamming_logic.jammers import JammerCoordinator
from src.jamming_logic.spoofers import GPSSpoofer
from src.simulation.scenario_manager import ScenarioManager

def run_autonomous_loop():
    print("====================================================")
    print("🛰️  E-WARFARE NEXUS: BİLİŞSEL SPEKTRUM ÜSTÜNLÜĞÜ [V2.0]")
    print("====================================================\n")
    print("[SİSTEM] Otonom EH Görev Döngüsü Başlatılıyor...")
    
    sample_rate = 1e6
    duration = 0.01 # 10ms window
    
    # Initialize components
    gen = SignalGenerator(sample_rate)
    sa = SpectrumAnalyzer(sample_rate)
    pe = ParameterExtractor(sample_rate)
    doa = DOAEstimator(antenna_count=5)
    lpi_detector = LPIDetector(sample_rate)
    scen = ScenarioManager(sample_rate)
    
    classifier = SignalClassifier()
    jammer_coord = JammerCoordinator(sample_rate)
    spoofer = GPSSpoofer()
    hop_tracker = HopTracker()
    remote_id_decoder = RemoteIDDecoder()
    
    autonomy = AutonomyManager(classifier, lpi_detector, jammer_coord)
    
    scenarios = [
        "Clear Sky",
        "Drone Swarm (Remote-ID)",
        "Frequency Hopping Agile Emitter",
        "Tracking Radar",
        "LPI Stealth Radar",
        "GNSS Spoofing Opportunity"
    ]
    
    try:
        for i, scenario_name in enumerate(scenarios, 1):
            print(f"--- [MİSYON {i}: {scenario_name}] ---")
            
            # 1. EM Spektrumu Tara (Simülasyon / SDR)
            if scenario_name == "Clear Sky":
                _, signal = gen.generate_noise(duration, noise_level=0.1)
                print("[ED] İzleme: Spektrum temiz. Dinleme devam ediyor...")
            elif scenario_name == "LPI Stealth Radar":
                t_lpi = np.linspace(0, duration, int(sample_rate*duration))
                signal = np.cos(2*np.pi*(100e3*t_lpi + 50e6*t_lpi**2))
                _, noise = gen.generate_noise(duration, noise_level=0.2)
                signal = gen.add_signals(signal, noise)
                print("[ED] İzleme: Karmaşık (LPI?) sinyal saptandı. AI analizi tetiklendi.")
            elif scenario_name == "Drone Swarm (Remote-ID)":
                # Simulated Remote-ID packet data
                rid_data = {"uas_id": "UAV-X-Delta", "lat": 41.0, "lon": 29.0, "alt": 100, "speed": 10}
                decoded = remote_id_decoder.decode_packet(rid_data)
                print(f"[ED] SIGINT: Remote-ID çözüldü! Drone ID: {decoded['uas_id']}, Konum: {decoded['lat']}, {decoded['lon']}")
                _, signal = gen.generate_noise(duration, noise_level=0.1) # Background noise
            elif scenario_name == "Frequency Hopping Agile Emitter":
                current_f = 200e3 + (int(time.time()) % 5) * 50e3
                hop_tracker.update(current_f, time.time())
                _, signal = gen.generate_cw(current_f, duration)
                print(f"[ED] İzleme: FHSS Sıçraması saptandı @ {current_f/1e3:.1f} kHz. Sıçrama hızı kestiriliyor...")
            elif scenario_name == "GNSS Spoofing Opportunity":
                # Create a simulated weak GPS-like signal
                t_gnss = np.linspace(0, duration, int(sample_rate*duration))
                signal = np.sin(2 * np.pi * 150e3 * t_gnss)
                _, noise = gen.generate_noise(duration, noise_level=0.3)
                signal = gen.add_signals(signal, noise)
                print("[ED] İzleme: GNSS (GPS L1) bandında düşük SNR'lı sinyal saptandı.")
                _, signal = scen.get_scenario_signal(scenario_name, duration)
                _, noise = gen.generate_noise(duration, noise_level=0.1)
                signal = gen.add_signals(signal, noise)
                print(f"[ED] İzleme: Aktif yayın saptandı ({scenario_name})")

            # 2. Teknik Parametre Çıkarımı & Yön Kestirimi
            params = pe.estimate_parameters(signal)
            if params["CenterFreq"]:
                print(f"[ED] Analiz: Frekans={params['CenterFreq']/1e3:.1f}kHz, BW={params.get('BW', 0)/1e3:.1f}kHz")
                
                # DOA Estimation (Simulated multi-channel from single signal for demo)
                # In real scenario: signal would be MxN matrix from SDR
                X_sim = np.tile(signal, (5, 1)) # Simulated 5-antenna array
                estimated_angles, _ = doa.estimate_music(X_sim)
                print(f"[ED] Konum: Yön kestirimi (MUSIC) -> {estimated_angles[0]:.1f}°")

            # 3. Otonom Analiz & Karar (AI Engined Based)
            freqs, mags = sa.compute_fft(signal)
            strategy = autonomy.process_detection(freqs, mags, raw_signal=signal, params=params)
            
            # 4. Müdahale Uygula (Electronic Attack)
            if strategy != "None" and strategy is not None:
                print(f"[ET] Karar: MÜDAHALE GEREKLİ! Aksiyon: {strategy}")
                
                # Check for GPS Deception
                if "GNSS" in strategy or "Spoofing" in strategy:
                    spoofer.generate_spoof_file("39.9,32.8,100", duration=10)
                    spoofer.start_spoofing()
                    time.sleep(2)
                    spoofer.stop_spoofing()
            else:
                print("[ET] Karar: Pasif izleme ve veri kaydı devam ediyor.")
                
            print("\n" + "-"*50 + "\n")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[SİSTEM] Kullanıcı tarafından durduruldu. Pasif güvenli moda geçiliyor.")

if __name__ == "__main__":
    run_autonomous_loop()
