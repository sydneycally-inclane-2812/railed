import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture

class MLEEstimator:
    """
    Estimate parameters for common distributions using MLE,
    and fit distributions to observed or synthetic data.
    """

    def __init__(self, data):
        self.data = np.asarray(data)
        self.fits = {}

    def fit_exponential(self):
        loc, scale = stats.expon.fit(self.data, floc=0)
        lam = 1 / scale
        self.fits['exponential'] = {'lambda': lam, 'loc': loc, 'scale': scale}
        return self.fits['exponential']

    def fit_normal(self):
        mu, std = stats.norm.fit(self.data)
        self.fits['normal'] = {'mu': mu, 'std': std}
        return self.fits['normal']

    def fit_gamma(self):
        shape, loc, scale = stats.gamma.fit(self.data)
        self.fits['gamma'] = {'shape': shape, 'loc': loc, 'scale': scale}
        return self.fits['gamma']

    def fit_lognorm(self):
        shape, loc, scale = stats.lognorm.fit(self.data)
        self.fits['lognorm'] = {'shape': shape, 'loc': loc, 'scale': scale}
        return self.fits['lognorm']

    def plot_fit(self, dist_name):
        # Map user-friendly names to scipy.stats names and required param order
        dist_map = {
            'exponential': ('expon', ['loc', 'scale']),
            'normal': ('norm', ['mu', 'std']),
            'gamma': ('gamma', ['shape', 'loc', 'scale']),
            'lognorm': ('lognorm', ['shape', 'loc', 'scale'])
        }
        if dist_name not in self.fits:
            raise ValueError(f"Fit {dist_name} first.")
        params = self.fits[dist_name]
        scipy_name, param_keys = dist_map[dist_name]
        dist = getattr(stats, scipy_name)
        x = np.linspace(min(self.data), max(self.data), 100)
        param_values = [params[k] for k in param_keys]
        plt.hist(self.data, bins=20, density=True, alpha=0.5, label='Data')
        plt.plot(x, dist.pdf(x, *param_values), label=f'{dist_name} fit')
        plt.legend()
        plt.title(f"{dist_name.capitalize()} Fit")
        plt.show()

    def summary(self):
        for name, params in self.fits.items():
            print(f"{name}: {params}")

class BootstrapSampler:
    """
    Perform bootstrap resampling to estimate the distribution of a statistic.
    """
    def __init__(self, data):
        self.data = np.asarray(data)

    def sample(self, n_samples=30, stat_func=np.mean, ci=95):
        """
        Perform bootstrap and return metrics for the statistic:
        - bootstrap mean
        - bias
        - standard error
        - confidence interval
        """
        stats_arr = []
        n = len(self.data)
        for _ in range(n_samples):
            sample = np.random.choice(self.data, size=n, replace=True)
            stats_arr.append(stat_func(sample))
        stats_arr = np.array(stats_arr)
        orig_stat = stat_func(self.data)
        boot_mean = np.mean(stats_arr)
        bias = boot_mean - orig_stat
        std_err = np.std(stats_arr)
        lower = np.percentile(stats_arr, (100 - ci) / 2)
        upper = np.percentile(stats_arr, 100 - (100 - ci) / 2)
        return {
            'original_stat': orig_stat,
            'bootstrap_mean': boot_mean,
            'bias': bias,
            'std_error': std_err,
            f'{ci}%_ci': (lower, upper),
            'all_samples': stats_arr
        }

# --- Queueing Theory Models ---
class MM1Queue:
    """
    M/M/1 Queueing Model
    lambda_: arrival rate
    mu: service rate
    """
    def __init__(self, lambda_, mu):
        self.lambda_ = lambda_
        self.mu = mu
        if lambda_ >= mu:
            raise ValueError("System is unstable: arrival rate must be less than service rate.")

    @property
    def rho(self):
        return self.lambda_ / self.mu

    @property
    def L(self):
        """Average number in system"""
        return self.rho / (1 - self.rho)

    @property
    def Lq(self):
        """Average number in queue"""
        return self.rho ** 2 / (1 - self.rho)

    @property
    def W(self):
        """Average time in system"""
        return 1 / (self.mu - self.lambda_)

    @property
    def Wq(self):
        """Average waiting time in queue"""
        return self.rho / (self.mu - self.lambda_)

    def summary(self):
        print(f"M/M/1 Queue: λ={self.lambda_:.3f}, μ={self.mu:.3f}")
        print(f"Utilization (ρ): {self.rho:.3f}")
        print(f"Avg number in system (L): {self.L:.3f}")
        print(f"Avg number in queue (Lq): {self.Lq:.3f}")
        print(f"Avg time in system (W): {self.W:.3f}")
        print(f"Avg waiting time in queue (Wq): {self.Wq:.3f}")

class MMCQueue:
    """
    M/M/c Queueing Model
    lambda_: arrival rate
    mu: service rate per server
    c: number of servers
    """
    def __init__(self, lambda_, mu, c):
        self.lambda_ = lambda_
        self.mu = mu
        self.c = c
        self.rho = lambda_ / (c * mu)
        if self.rho >= 1:
            raise ValueError("System is unstable: traffic intensity must be less than 1.")

    def P0(self):
        """Probability system is empty"""
        sum_terms = sum([(self.c * self.rho) ** n / np.math.factorial(n) for n in range(self.c)])
        last_term = ((self.c * self.rho) ** self.c) / (np.math.factorial(self.c) * (1 - self.rho))
        return 1 / (sum_terms + last_term)

    def Lq(self):
        """Average number in queue"""
        P0 = self.P0()
        num = P0 * ((self.c * self.rho) ** self.c) * self.rho
        denom = np.math.factorial(self.c) * (1 - self.rho) ** 2
        return num / denom

    def L(self):
        """Average number in system"""
        return self.Lq() + self.lambda_ / self.mu

    def Wq(self):
        """Average waiting time in queue"""
        return self.Lq() / self.lambda_

    def W(self):
        """Average time in system"""
        return self.Wq() + 1 / self.mu

    def summary(self):
        print(f"M/M/{self.c} Queue: λ={self.lambda_:.3f}, μ={self.mu:.3f}, c={self.c}")
        print(f"Traffic Intensity (ρ): {self.rho:.3f}")
        print(f"P0 (empty): {self.P0():.3f}")
        print(f"Avg number in system (L): {self.L():.3f}")
        print(f"Avg number in queue (Lq): {self.Lq():.3f}")
        print(f"Avg time in system (W): {self.W():.3f}")
        print(f"Avg waiting time in queue (Wq): {self.Wq():.3f}")


def mle_gmm(data, n_components=2, random_state=None):
    """
    Fit a Gaussian Mixture Model (GMM) to data using MLE.
    Returns means, variances, and weights for each component.
    """
    data = np.array(data).reshape(-1, 1)
    gmm = GaussianMixture(n_components=n_components, random_state=random_state)
    gmm.fit(data)
    means = gmm.means_.flatten()
    variances = gmm.covariances_.flatten()
    weights = gmm.weights_.flatten()
    return {
        'means': means,
        'variances': variances,
        'weights': weights,
        'gmm': gmm
    }


# Example usage:
if __name__ == "__main__":
    # --- Single peak hour: normal distribution MLE comparison ---
    from arrival_rate_profile import random_peak_hour
    single_sampler = random_peak_hour(peak_hour=8, spread=2.0)
    single_arrival_times = [single_sampler() for _ in range(1000)]

    # Fit normal distribution using MLEEstimator
    mle_est = MLEEstimator(single_arrival_times)
    norm_params = mle_est.fit_normal()
    print("Normal MLE mu:", norm_params['mu'])
    print("Normal MLE std:", norm_params['std'])

    # Plot actual arrival_times histogram and overlay normal fit
    plt.figure(figsize=(8, 5))
    plt.hist(single_arrival_times, bins=30, density=True, alpha=0.5, label='Actual Arrival Times (Single Peak)')
    x = np.linspace(min(single_arrival_times), max(single_arrival_times), 500)
    pdf = stats.norm.pdf(x, loc=norm_params['mu'], scale=norm_params['std'])
    plt.plot(x, pdf, color='green', lw=2, label='Normal (MLE) Fit')
    plt.title('Single Peak Arrival Times: Actual vs Normal (MLE)')
    plt.xlabel('Arrival Time')
    plt.ylabel('Density')
    plt.legend()
    plt.tight_layout()
    plt.show()

    np.random.seed(42)
    arrival_times = np.random.exponential(scale=2.0, size=200)
    service_times = np.random.normal(loc=3.0, scale=0.5, size=200)

    from arrival_rate_profile import random_multi_peak_hour
    # Generate synthetic arrival times using random_multi_peak_hour
    sampler = random_multi_peak_hour(peak_hours=[8, 17], spreads=[1.5, 2.0], weights=[1, 0.8])
    arrival_times = [sampler() for _ in range(1000)]

    # MLE for normal distribution parameters
    np.random.seed(42)
  
    result = mle_gmm(arrival_times, n_components=2)
    print("GMM Means:", result['means'])
    print("GMM Variances:", result['variances'])
    print("GMM Weights:", result['weights'])

    # Plot actual arrival_times histogram and overlay GMM fit
    plt.figure(figsize=(8, 5))
    plt.hist(arrival_times, bins=30, density=True, alpha=0.5, label='Actual Arrival Times')
    x = np.linspace(min(arrival_times), max(arrival_times), 500)
    gmm = result['gmm']
    # GMM PDF is weighted sum of component PDFs
    pdf = np.exp(gmm.score_samples(x.reshape(-1, 1)))
    plt.plot(x, pdf, color='red', lw=2, label='GMM (MLE) Fit')
    plt.title('Arrival Times: Actual vs GMM (MLE)')
    plt.xlabel('Arrival Time')
    plt.ylabel('Density')
    plt.legend()
    plt.tight_layout()
    plt.show()

    # Bootstrap mean arrival time
    boot = BootstrapSampler(arrival_times)
    boot_result = boot.sample(n_samples=1000, stat_func=np.mean)
    print(f"Bootstrap mean: {boot_result['bootstrap_mean']:.3f}")
    print(f"Bootstrap bias: {boot_result['bias']:.3f}")
    print(f"Bootstrap std error: {boot_result['std_error']:.3f}")
    ci_low, ci_high = boot_result['95%_ci']
    print(f"Bootstrap 95% CI: {ci_low:.3f} - {ci_high:.3f}")


