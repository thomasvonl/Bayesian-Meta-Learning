import math
import numpy as np
from torch.distributions.multivariate_normal import MultivariateNormal
from torch.distributions.normal import Normal

from metalearning_eval_util.util import log_marginal_likelihood_mc

import torch
import random

from ais import ais_trajectory

class BayesianLinearRegression():

    def __init__(self, feature_dim):
        self.posterior_mean = None
        self.posterior_cov = None

        self.feature_dim = feature_dim

        self.precision = 0.2
        prior_mean = torch.zeros(feature_dim)
        prior_cov = torch.eye(feature_dim) * (1.0/self.precision)

        self.prior = MultivariateNormal(prior_mean, prior_cov)

        self.noise_var = 0.25


    def train(self, dataset):
        train_points, noisy_labels, true_labels = dataset
        train_points = torch.from_numpy(train_points).float()
        noisy_labels = torch.from_numpy(noisy_labels).float()

        print("shape of train_points: " + str(train_points.size()))
        n_datapoints = train_points.size()[0]
        feature_matrix = torch.stack((torch.ones(n_datapoints),train_points), dim=1)

        print("shape of feature_matrix: " + str(feature_matrix.size()))

        inverse_mat = torch.linalg.inv(torch.matmul(feature_matrix.T, feature_matrix) + self.noise_var * self.precision * torch.eye(self.feature_dim))

        print("shape of inverse_mat: " + str(inverse_mat.size()))

        # Compute the posterior distribution
        self.posterior_mean = torch.matmul(inverse_mat, torch.matmul(feature_matrix.T, noisy_labels))
        self.posterior_cov = self.noise_var * inverse_mat

        print("shape of posterior_mean: " + str(self.posterior_mean.size()))
        print("shape of posterior_cov: " + str(self.posterior_cov.size()))
        
    def predict(self, x):
        ones = torch.ones(x.size()[0])
        train_features = torch.stack([ones, x], dim=1)
        print("shape of train features: " + str(train_features.size()))

        mu_y = torch.matmul(train_features, self.posterior_mean)
        print("shape of mu_y: " + str(mu_y.size()))

        # cov_y should have shape n_points x d_y x d_y
        first_dot_product = torch.matmul(self.posterior_cov, train_features.T)
        intermediate_result = torch.mul(train_features, first_dot_product.T)
        print("shape of intermediate_result: " + str(intermediate_result.size()))

        cov_y = torch.sum(intermediate_result, dim=1) + self.noise_var

        return mu_y, cov_y

    def predict_param(self, x, z):
        ones = torch.ones(x.size()[0])
        train_features = torch.stack([ones, x], dim=1)
        print("shape of train features: " + str(train_features.size()))
        print("shape of z: " + str(z.size()))

        mu_y = torch.matmul(train_features, z.T)
        cov_y = torch.tensor(self.noise_var).expand(mu_y.size())
        print("shape of mu_y: " + str(mu_y.size()))
        print("shape of cov_y: " + str(cov_y.size()))

        return mu_y, cov_y


    def generate_dataset(n_datapoints, slope, intercept, noise_std_dev, seed = 42):
        np.random.seed(seed)
        lower_bound = -1.5
        upper_bound = 1.5

        train_points = np.random.uniform(lower_bound, upper_bound, n_datapoints)
        noisy_labels = slope * train_points + intercept + np.random.normal(0, noise_std_dev, n_datapoints)
        true_labels = slope * train_points + intercept

        return train_points, noisy_labels, true_labels

    def get_log_dataset_likelihood(self, test_values, test_labels):
        mu_y, cov_y = self.predict(test_values)
        print("shape of mu_y: " + str(mu_y.shape) + ", shape of cov_y: " + str(cov_y.shape))
        predictive = Normal(mu_y, np.sqrt(cov_y))
        
        log_lhds = predictive.log_prob(test_labels)
        return torch.sum(log_lhds, dim=-1)

    def get_log_dataset_likelihood_param(self, test_values, test_labels, parameter_val):
        ones = torch.ones(test_values.size()[0])
        train_features = torch.stack([ones, test_values], dim=1)
        
        pred_means = torch.matmul(train_features, parameter_val.T).T
        pred_cov = torch.tensor(self.noise_var)
        predictive = Normal(pred_means, torch.sqrt(pred_cov))
        
        log_lhds = predictive.log_prob(test_labels)
        return torch.sum(log_lhds, dim=-1)

    def mc_estimator(self, dataset, n_samples=3):
        train_points, noisy_labels, true_labels = dataset
        train_points = torch.from_numpy(train_points[:10]).float()
        noisy_labels = torch.from_numpy(noisy_labels[:10]).float()
        true_labels = torch.from_numpy(true_labels[:10]).float()

        print("shape of posterior mean: " + str(self.posterior_mean.size()) + "shape of posterior cov: " + str(self.posterior_cov.size()))
        posterior = MultivariateNormal(self.posterior_mean, torch.sqrt(self.posterior_cov))
        pos_samples = posterior.sample((n_samples,))
        print("shape of pos_samples: " + str(pos_samples.size()))

        mu_y, cov_y = self.predict_param(train_points, pos_samples)

        mu_y = torch.unsqueeze(torch.unsqueeze(mu_y.T, dim=1), dim=-1)
        cov_y = torch.unsqueeze(torch.unsqueeze(cov_y.T, dim=1), dim=-1)
        true_labels = torch.unsqueeze(torch.unsqueeze(true_labels, dim=0), dim=-1)
        print("shape of mu_y: " + str(mu_y.size()) + ", shape of cov_y: " + str(cov_y.size()))
        print("shape of true labels: " + str(true_labels.size()))

        print("mu_y: " + str(mu_y))
        print("cov_y: " + str(cov_y))
        print("true_labels: " + str(true_labels))

        lm_lhd_mc = log_marginal_likelihood_mc(mu_y.numpy(), cov_y.numpy(), true_labels.numpy())

        print("MC estimate of Log marginal likelihood: " + str(lm_lhd_mc))



if __name__ == "__main__":
    blr = BayesianLinearRegression(feature_dim = 2)
    dataset = BayesianLinearRegression.generate_dataset(n_datapoints = 1000, slope = 0.9, intercept = -0.7, noise_std_dev = 0.5, seed = 42)

    train_points, noisy_labels, true_labels = dataset
    train_points = torch.from_numpy(train_points).float()
    noisy_labels = torch.from_numpy(noisy_labels).float()
    true_labels = torch.from_numpy(true_labels).float()

    blr.train(dataset)

    log_dataset_likelihood = blr.get_log_dataset_likelihood(train_points, noisy_labels)
    print("True log dataset likelihood: " + str(log_dataset_likelihood))

    n_samples = 100

    blr.mc_estimator(dataset)
    
    '''
    initial_state = (blr.prior.sample((n_samples,))).float()
    # Check shape of initial_state

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    chain_length = 1000

    forward_schedule = torch.linspace(0, 1, chain_length, device=device)
    
    ais_trajectory(
    lambda z: blr.prior.log_prob(z),
    lambda z: blr.get_log_dataset_likelihood_param(train_points, noisy_labels, z),
    initial_state,
    forward=True,
    schedule=forward_schedule)
    '''
    

