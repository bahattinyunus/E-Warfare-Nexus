import numpy as np

class SignalGenerator:
    """
    Simulates RF signal generation for testing purposes.
    Supports: CW, Noise, CHIRP (FMCW), BPSK, QPSK, Pulsed, FHSS
    """
    def __init__(self, sample_rate=1e6):
        self.sample_rate = sample_rate

    def _t(self, duration):
        return np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)

    def generate_cw(self, frequency, duration, amplitude=1.0):
        """Generates a Continuous Wave (CW) sinusoidal signal."""
        t = self._t(duration)
        return t, amplitude * np.sin(2 * np.pi * frequency * t)

    def generate_noise(self, duration, noise_level=0.1):
        """Generates Gaussian white noise."""
        t = self._t(duration)
        return t, np.random.normal(0, noise_level, len(t))

    def generate_chirp(self, f_start, f_end, duration, amplitude=1.0):
        """
        Generates an FMCW (Linear Chirp) signal — the primary waveform
        of LPI radars. Frequency sweeps linearly from f_start to f_end.
        """
        t = self._t(duration)
        k = (f_end - f_start) / duration  # chirp rate [Hz/s]
        phase = 2 * np.pi * (f_start * t + 0.5 * k * t**2)
        return t, amplitude * np.cos(phase)

    def generate_bpsk(self, carrier_freq, bit_rate, duration, amplitude=1.0):
        """
        Generates Binary Phase Shift Keying (BPSK) signal.
        Random bit sequence modulated onto the carrier.
        """
        t = self._t(duration)
        samples_per_bit = int(self.sample_rate / bit_rate)
        num_bits = int(np.ceil(len(t) / samples_per_bit))
        bits = np.random.choice([-1, 1], size=num_bits)
        bit_stream = np.repeat(bits, samples_per_bit)[:len(t)]
        carrier = np.cos(2 * np.pi * carrier_freq * t)
        return t, amplitude * bit_stream * carrier

    def generate_qpsk(self, carrier_freq, symbol_rate, duration, amplitude=1.0):
        """
        Generates Quadrature Phase Shift Keying (QPSK) signal.
        Two bits per symbol: I and Q components.
        """
        t = self._t(duration)
        samples_per_sym = int(self.sample_rate / symbol_rate)
        num_syms = int(np.ceil(len(t) / samples_per_sym))
        # Random QPSK symbols: phases = {45, 135, 225, 315} degrees
        phases = np.random.choice([np.pi/4, 3*np.pi/4, 5*np.pi/4, 7*np.pi/4], size=num_syms)
        phase_stream = np.repeat(phases, samples_per_sym)[:len(t)]
        carrier = amplitude * np.cos(2 * np.pi * carrier_freq * t + phase_stream)
        return t, carrier

    def generate_pulsed(self, carrier_freq, pri, pw, duration, amplitude=1.0):
        """
        Generates a pulsed radar waveform with given PRI and PW.
        """
        t = self._t(duration)
        signal = np.zeros(len(t))
        carrier = np.cos(2 * np.pi * carrier_freq * t)
        pulse_mask = (t % pri) < pw
        signal[pulse_mask] = amplitude * carrier[pulse_mask]
        return t, signal

    def generate_fhss(self, hop_frequencies, hop_duration, total_duration, amplitude=1.0):
        """
        Generates a Frequency Hopping Spread Spectrum (FHSS) signal.
        Jumps between given hop_frequencies every hop_duration.
        """
        t = self._t(total_duration)
        signal = np.zeros(len(t))
        
        samples_per_hop = int(self.sample_rate * hop_duration)
        num_hops = int(np.ceil(len(t) / samples_per_hop))
        
        last_phase = 0
        for i in range(num_hops):
            start_idx = i * samples_per_hop
            end_idx = min((i + 1) * samples_per_hop, len(t))
            freq = hop_frequencies[i % len(hop_frequencies)]
            
            t_hop = t[start_idx:end_idx]
            # Ensure phase continuity
            phase = 2 * np.pi * freq * (t_hop - t_hop[0]) + last_phase
            signal[start_idx:end_idx] = amplitude * np.cos(phase)
            last_phase = phase[-1] if len(phase) > 0 else last_phase
            
        return t, signal

    def generate_lora(self, sf, bw, symbol, duration, amplitude=1.0):
        """
        Generates a LoRa Chirp Spread Spectrum (CSS) symbol.
        :param sf: Spreading Factor (7-12)
        :param bw: Bandwidth in Hz
        :param symbol: Integer symbol value (0 to 2^sf - 1)
        """
        t = self._t(duration)
        n_samples = len(t)
        m = 2**sf
        
        # Base chirp frequency sweep from -BW/2 to BW/2
        k = bw / duration # chirp rate
        f0 = -bw / 2
        
        # Symbol shift
        shift = symbol / m * duration
        t_shifted = (t + shift) % duration
        
        phase = 2 * np.pi * (f0 * t_shifted + 0.5 * k * t_shifted**2)
        return t, amplitude * np.cos(phase)

    def add_signals(self, signal1, signal2):
        """Adds two signals together (must be same length)."""
        if len(signal1) != len(signal2):
            # Pad shorter signal with zeros
            target_len = max(len(signal1), len(signal2))
            s1 = np.pad(signal1, (0, target_len - len(signal1)))
            s2 = np.pad(signal2, (0, target_len - len(signal2)))
            return s1 + s2
        return signal1 + signal2
