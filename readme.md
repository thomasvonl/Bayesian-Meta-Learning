# Annealed Importance sampling

Annealed importance sampling combines the concepts of MCMC sampling and importance weights. It gives us a stochastic lower bound of the marginal likelihood. This means with infinite samples, the probability of overestimating the true ML goes down to zero. The idea of annealed importance sampling is using a series of intermediate distributions to bridge between prior and posterior distribution, because it is inefficient to use a single importance sampling computation between two very dissimilar distributions.

This algorithm takes as input a sequence of T distributions $p_0$,...,$p_T$, with $p_t(z) = f_t(z) / Z_t$, where $p_T$ is the target distribution (posterior $p(z|y, x)$) and $p_0$ is the proposal distribution (prior $p(z)$) and the intermediate distributions are taken to be geometric averages of the initial and target distribution: $f_t(z) = f_0(z)^{1-\beta_t}f_T(z)^{\beta_t}$, where $\beta$ are monotonically increasing parameters with $\beta_0 = 0$ and $\beta_T = 1$, in our case we take $\beta_t = t/T$ and we can represent intermediate distribution with prior and posterior

\begin{equation}
f_t(z) = f_0(z)^{1-\beta_t}f_T(z)^{\beta_t}
\end{equation}
\begin{equation}
f_0(z) = p(z)
\end{equation}
\begin{equation}
f_T(z) = p(y|z,x)p(z)
\end{equation}

When we insert the last two equations into the first one, we get the following representation:

\begin{equation}
f_t(z) = p(z)^{1-\beta_t}(p(y|z,x)p(z))^{\beta_t} \\
\end{equation}
\begin{equation}
==> f_t(z) = p(z)p(y|z,x)^{\beta_t}
\end{equation}


## Applying AIS to Neural Processes
Neural Processes are trained on meta-training tasks X. After meta-training, they are adapted to a task-specific context set $D^C$ and asked to make predictions $y$ for test inputs $x^t$. We want to evaluate, how much probability the model assigns to the true labels $y^t$ of this test task. More specifically, the quantity we want to estimate is the held-out predictive likelihood:


\begin{equation}
p(y^t|x^t, D^C, X) = \int p(z|D^C) \prod_{m = 1}^{M} p(y_m^t|z, x_m^t, X) dz
\end{equation}
The posterior of the latent variable $z$ can be decomposed using Bayes rule to the following:
\begin{equation}
p(z|x_t, y_t, D^C, X) = {p(y^t|z, x_t, X)p(z|D^C, X) \over p(y^t|x^t, D^C, X)} 
\end{equation}
We start by defining our initial distribution as $f_0(z) := p_0(z) = p(z|D^C)$. Our final unnormalized distribution is $f_T(z) = p(y^t|z, x^t, X) p(z|D^C)$. Per definition $p_T$ is the normalized distribution that corresponds to $f_T$, so $p_T(z) = f_T(z) / Z_T$. We know that the normalization constant $Z_T$ is actually the held-out predictive likelihood that we want to estimate. The only difference to the above approach is that we condition the prior on a context set $D^C$. The intermediate distributions can be written as  $f_t(z) = p(z|D^C)p(y^t|z, x^t, X)^{\beta_t}$.

To start the AIS chains, we need to sample from $p_0(z) = f_0(z) = p(z|D^C)$. After the Neural Process model is adapted to the context set, the encoder gives us mean and variance of $p(z|D^C)$. Thus we know the distribution and can sample from it. To evaluate the intermediate distribution, we need to compute $p(y^t|z, x^t, X) = \prod_{m = 1}^{M} p(y_m^t|z, x_m^t, X)$. Those probabilities are given by the decoder. It takes as input a latent variable $z$ and a test point $x_m^t$. For these inputs, it computes a distribution over possible outputs $y$. More specifically, the distribution of $y$ is assumed to be Gaussian and the decoder outputs mean and variance of the distribution. Because the weights of the decoder are trained on the meta-training set $X$, the distribution over $y$ is also conditioned on $X$.