import numpy as np
import scipy.linalg as la
from scipy.signal import find_peaks

class DOAEstimator:
    """
    Super-resolution Direction of Arrival (DOA) Estimation Module.
    Implements MUSIC and ESPRIT algorithms for radio frequency direction finding.
    """
    def __init__(self, antenna_count=5, spacing=0.5):
        """
        Initialize the DOA Estimator.
        :param antenna_count: Number of antennas in the array.
        :param spacing: Lambda spacing between antennas (default 0.5 for ULA).
        """
        self.M = antenna_count
        self.d = spacing
        self.theta = np.linspace(-90, 90, 181) # Search range from -90 to 90 degrees

    def compute_steering_vector(self, angle):
        """
        Compute the steering vector for a given angle (in degrees).
        """
        phi = 2 * np.pi * self.d * np.sin(np.deg2rad(angle))
        return np.exp(-1j * phi * np.arange(self.M))

    def estimate_music(self, X, num_sources=1):
        """
        Multiple Signal Classification (MUSIC) Algorithm.
        :param X: Received signal matrix (MxN, where M is antenna count and N is snapshots).
        :param num_sources: Number of signal sources to detect.
        :return: Estimated angles and the MUSIC spectrum.
        """
        # 1. Compute Spatial Covariance Matrix
        R = (X @ X.conj().T) / X.shape[1]

        # 2. Eigenvalue Decomposition
        eigenvals, eigenvecs = la.eigh(R)
        
        # 3. Separate Noise Subspace
        # eigenvalues are sorted in ascending order
        Un = eigenvecs[:, :self.M - num_sources]

        # 4. Compute MUSIC Spectrum
        spectrum = []
        for angle in self.theta:
            a = self.compute_steering_vector(angle)
            p = 1 / (a.conj().T @ Un @ Un.conj().T @ a)
            spectrum.append(np.abs(p))
        
        spectrum = np.array(spectrum)
        spectrum = 10 * np.log10(spectrum / np.max(spectrum))

        # 5. Find Peaks
        peaks, _ = find_peaks(spectrum)
        top_peaks = peaks[np.argsort(spectrum[peaks])][-num_sources:]
        estimated_angles = self.theta[top_peaks]

        return estimated_angles, spectrum

    def estimate_esprit(self, X, num_sources=1):
        """
        Estimation of Signal Parameters via Rotational Invariance Techniques (ESPRIT).
        :param X: Received signal matrix (MxN).
        :param num_sources: Number of signal sources.
        :return: Estimated angles.
        """
        # 1. Compute Spatial Covariance Matrix
        R = (X @ X.conj().T) / X.shape[1]

        # 2. Eigenvalue Decomposition
        _, eigenvecs = la.eigh(R)
        
        # Signal Subspace
        Us = eigenvecs[:, self.M - num_sources:]

        # 3. Sub-array separation
        Us1 = Us[:-1, :]
        Us2 = Us[1:, :]

        # 4. Compute Rotation Operator (phi)
        phi = la.lstsq(Us1, Us2)[0]

        # 5. Eigenvalues of phi
        eigvals_phi = la.eigvals(phi)
        
        # 6. Estimate angles
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
