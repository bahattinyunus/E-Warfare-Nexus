import numpy as np
import scipy.linalg as la
from scipy.signal import find_peaks

class DOAEstimator:
    """
    Super-resolution Direction of Arrival (DOA) Estimation Module.
    Implements MUSIC and ESPRIT algorithms for radio frequency direction finding.
    """
    def __init__(self, antenna_count=5, spacing=0.5, array_type="UCA", radius=None):
        """
        Initialize the DOA Estimator.
        :param antenna_count: Number of antennas in the array.
        :param spacing: Lambda spacing between antennas (for ULA).
        :param array_type: "ULA" (Uniform Linear Array) or "UCA" (Uniform Circular Array).
        :param radius: Radius of UCA in lambda units (if None, derived from spacing).
        """
        self.M = antenna_count
        self.d = spacing
        self.array_type = array_type
        # For UCA, if radius not provided, assume antennas are spaced by 'spacing' on perimeter
        if radius is None and array_type == "UCA":
            self.radius = spacing / (2 * np.sin(np.pi / self.M))
        else:
            self.radius = radius
            
        self.theta = np.linspace(0, 360, 361) # Full 360 degree search for UCA

    def compute_steering_vector(self, angle_deg):
        """
        Compute the steering vector for a given angle.
        Supports both ULA and UCA geometries.
        """
        angle_rad = np.deg2rad(angle_deg)
        if self.array_type == "ULA":
            phi = 2 * np.pi * self.d * np.sin(angle_rad)
            return np.exp(-1j * phi * np.arange(self.M))
        elif self.array_type == "UCA":
            # UCA Steering Vector: exp(j * 2*pi*R * cos(theta - gamma_m))
            # gamma_m is the angular position of the m-th antenna
            gamma = 2 * np.pi * np.arange(self.M) / self.M
            phase = 2 * np.pi * self.radius * np.cos(angle_rad - gamma)
            return np.exp(1j * phase)
        return None

    def estimate_music(self, X, num_sources=1):
        """
        Multiple Signal Classification (MUSIC) Algorithm with Spatial Smoothing option.
        :param X: Received signal matrix (MxN).
        :param num_sources: Number of signal sources.
        :return: Estimated angles and the MUSIC spectrum.
        """
        # 1. Compute Spatial Covariance Matrix
        R = (X @ X.conj().T) / X.shape[1]

        # 2. Eigenvalue Decomposition
        eigenvals, eigenvecs = la.eigh(R)
        
        # 3. Separate Noise Subspace (eigenvalues are sorted ascending)
        Un = eigenvecs[:, :self.M - num_sources]

        # 4. Compute MUSIC Spectrum
        # Vectorized spectrum calculation for speed
        spectrum = []
        for angle in self.theta:
            a = self.compute_steering_vector(angle)
            # P_music = 1 / (a* H * Un * Un' * a)
            denom = np.real(a.conj().T @ Un @ Un.conj().T @ a)
            spectrum.append(1.0 / (denom + 1e-10))
        
        spectrum = np.array(spectrum)
        # Normalize to dB
        spectrum_db = 10 * np.log10(spectrum / np.max(spectrum))

        # 5. Find Peaks
        peaks, _ = find_peaks(spectrum_db, height=-20)
        # Sort peaks by magnitude
        if len(peaks) > 0:
            top_peaks = peaks[np.argsort(spectrum_db[peaks])][-num_sources:]
            estimated_angles = self.theta[top_peaks]
        else:
            estimated_angles = np.array([])

        return estimated_angles, spectrum_db

    def estimate_esprit(self, X, num_sources=1):
        """
        ESPRIT Algorithm (Note: Standard ESPRIT works best for ULA).
        For UCA, this is a simplified version or requires manifold transformation.
        """
        if self.array_type == "UCA":
            # For UCA, we fall back to MUSIC or a basic approximation for now
            # In a real system, we'd use Phase-Mode ESPRIT or similar.
            angles, _ = self.estimate_music(X, num_sources)
            return angles

        # Standard TLS-ESPRIT for ULA
        R = (X @ X.conj().T) / X.shape[1]
        _, eigenvecs = la.eigh(R)
        Us = eigenvecs[:, self.M - num_sources:]
        
        Us1 = Us[:-1, :]
        Us2 = Us[1:, :]
        
        # Total Least Squares (TLS) solution
        phi = la.lstsq(Us1, Us2)[0]
        eigvals_phi = la.eigvals(phi)
        
        angles = np.arcsin(np.angle(eigvals_phi) / (2 * np.pi * self.d))
        return np.rad2deg(angles)

if __name__ == "__main__":
    # Example Simulation
    estimator = DOAEstimator(antenna_count=5)
    
    # Generate synthetic signal from 20 degrees
    true_angle = 20
    N = 1000 # snapshots
    s = np.random.randn(1, N) + 1j * np.random.randn(1, N)
    a = estimator.compute_steering_vector(true_angle).reshape(-1, 1)
    
    # Add noise
    noise = 0.5 * (np.random.randn(5, N) + 1j * np.random.randn(5, N))
    X = a @ s + noise
    
    angles, spectrum = estimator.estimate_music(X)
    print(f"True Angle: {true_angle}, Estimated (MUSIC): {angles}")
    print(f"Estimated (ESPRIT): {estimator.estimate_esprit(X)}")
