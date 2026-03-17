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
        "Drone Swarm",
        "Tracking Radar",
        "FHSS Comms",
        "LoRa Sensors"
    ]
    
    # Simulation settings
    sensor_pos = (500, 500) # Meters from center
    
    try:
        for i, scenario_name in enumerate(scenarios, 1):
            print(f"--- [MİSYON {i}: {scenario_name}] ---")
            
            # 1. EM Spektrumu Tara (Spatial Simülasyon)
            t, signal = scen.get_scenario_signal(scenario_name, duration, sensor_pos=sensor_pos)
            print(f"[ED] İzleme: {scenario_name} senaryosu aktif. Spektrum taranıyor...")

            # 2. Teknik Parametre Çıkarımı & Yön Kestirimi
            params = pe.estimate_parameters(signal)
            if params.get("CenterFreq"):
                print(f"[ED] Analiz: Frekans={params['CenterFreq']/1e3:.1f}kHz, Sinyal Sayısı={params['SignalCount']}")
                if params.get("IsLoRa"):
                    print("[ED] SIGINT: LoRa (CSS) sinyali saptandı! LPI skoru yüksek.")
                
                # DOA Estimation (Simulated multi-channel from single signal)
                X_sim = np.tile(signal, (5, 1)) 
                # Add delay based on DOA for UCA support demo
                # (Ideally we'd use steering vectors here, but keeping it simple for loop)
                estimated_angles, _ = doa.estimate_music(X_sim)
                print(f"[ED] Konum: Yön kestirimi (MUSIC UCA) -> {estimated_angles[0]:.1f}°")

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
