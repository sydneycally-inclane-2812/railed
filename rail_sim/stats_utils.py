import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

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

    def sample(self, n_samples=1000, stat_func=np.mean):
        stats_arr = []
        n = len(self.data)
        for _ in range(n_samples):
            sample = np.random.choice(self.data, size=n, replace=True)
            stats_arr.append(stat_func(sample))
        return np.array(stats_arr)

class MonteCarloSampler:
    """
    Generate random samples from a fitted distribution using Monte Carlo simulation.
    """
    def __init__(self, fits):
        self.fits = fits

    def sample(self, dist_name, size=1000):
        if dist_name not in self.fits:
            raise ValueError(f"Fit {dist_name} first.")
        params = self.fits[dist_name]
        if dist_name == 'exponential':
            return np.random.exponential(scale=params['scale'], size=size)
        elif dist_name == 'normal':
            return np.random.normal(loc=params['mu'], scale=params['std'], size=size)
        elif dist_name == 'gamma':
            return np.random.gamma(shape=params['shape'], scale=params['scale'], size=size)
        elif dist_name == 'lognorm':
            return np.random.lognormal(mean=np.log(params['scale']), sigma=params['shape'], size=size)
        else:
            raise ValueError(f"Sampling not implemented for {dist_name}")

# Example usage:
if __name__ == "__main__":
    np.random.seed(42)
    arrival_times = np.random.exponential(scale=2.0, size=200)
    service_times = np.random.normal(loc=3.0, scale=0.5, size=200)

    print("=== Arrival Rate Estimation (Exponential) ===")
    arrival_est = MLEEstimator(arrival_times)
    print(arrival_est.fit_exponential())
    arrival_est.plot_fit('exponential')

    # Bootstrap mean arrival time
    boot = BootstrapSampler(arrival_times)
    boot_means = boot.sample(n_samples=1000, stat_func=np.mean)
    print(f"Bootstrap mean (95% CI): {np.percentile(boot_means, 2.5):.3f} - {np.percentile(boot_means, 97.5):.3f}")

    # Monte Carlo sampling from exponential fit
    mc = MonteCarloSampler(arrival_est.fits)
    mc_samples = mc.sample('exponential', size=1000)
    plt.hist(mc_samples, bins=30, alpha=0.5, label='Monte Carlo Samples')
    plt.title("Monte Carlo Sampling (Exponential Fit)")
    plt.legend()
    plt.show()

    print("=== Service Time Estimation (Normal) ===")
    service_est = MLEEstimator(service_times)
    print(service_est.fit_normal())
    service_est.plot_fit('normal')

    # Bootstrap std of service times
    boot_service = BootstrapSampler(service_times)
    boot_stds = boot_service.sample(n_samples=1000, stat_func=np.std)
    print(f"Bootstrap std (95% CI): {np.percentile(boot_stds, 2.5):.3f} - {np.percentile(boot_stds, 97.5):.3f}")

    # Monte Carlo sampling from normal fit
    mc_service = MonteCarloSampler(service_est.fits)
    mc_samples_norm = mc_service.sample('normal', size=1000)
    plt.hist(mc_samples_norm, bins=30, alpha=0.5, label='Monte Carlo Samples')
    plt.title("Monte Carlo Sampling (Normal Fit)")
    plt.legend()
    plt.show()

    print("=== Fitting Gamma to Service Times ===")
    print(service_est.fit_gamma())
    service_est.plot_fit('gamma')