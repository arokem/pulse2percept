# -*effectivecurrent2brightness -*-
"""effectivecurrent2brightness
This transforms the effective current into brightness for a single point in
space based on the Horsager model as modified by Devyani
Inputs: a vector of effective current over time
Output: a vector of brightness over time
"""
#from __future__ import print_function
from scipy.misc import factorial
from scipy.signal import fftconvolve
import numpy as np
import matplotlib.pyplot as plt
import utils


def gamma(n, tau, t):
    """
    returns a gamma function from in [0, t]:

    y = (t/theta).^(n-1).*exp(-t/theta)/(theta*factorial(n-1))

    which is the result of an n stage leaky integrator.
    """

    flag = 0
    if t[0] == 0:
        t = t[2:len(t)]
        flag = 1

    y = ((t/tau)  ** (n-1) *
        np.exp(-t / tau) /
        (tau * factorial(n-1)))

    if flag == 1:
        y = np.concatenate([[0], y])

    return y


class TemporalModel(object):
    def __init__(self, Fs=.01/1000, tau1=.42/1000, tau2=45.25/1000, tau3=26.25/1000,
                 e=8.73, beta=.6, asymptote=14, slope=3, shift=16):
        """
        A model of temporal integration from retina pixels

        Fs : sampling rate

        tau1 = .42/1000  is a parameter for the fast leaky integrator, from
        Alan model, tends to be between .24 - .65

        tau2 = 45.25/1000  integrator for charge accumulation, has values
        between 38-57

        e = scaling factor for the effects of charge accumulation 2-3 for
        threshold or 8-10 for suprathreshold

        tau3 = ??

        parameters for a stationary nonlinearity providing a continuous
        function that nonlinearly rescales the response based on Nanduri et al
        2012, equation 3:

        asymptote = 14
        slope =.3
        shift =47
        """
        self.tau1 = tau1
        self.tau2 = tau2
        self.tau3 = tau3
        self.e = e
        self.beta = beta
        self.asymptote = asymptote
        self.slope = slope
        self.shift = shift
        self.Fs = Fs

    def fast_response(self, stim):
        """
        Fast response function
        """
        t = np.arange(0, 20 * self.tau1, self.Fs)
        R1 = self.Fs * np.convolve(gamma(1, self.tau1, t), stim)
        return R1

    def charge_accumulation(self, fast_response, stim):
        t = np.arange(0, 8 * self.tau2, self.Fs)

        # calculated accumulated charge
        rect_stim = np.where(stim> 0, stim, 0)  # rectify
        ca = self.Fs * np.cumsum(rect_stim.astype(float))
        chargeaccumulated = (self.e * self.Fs *
                             np.convolve(gamma(1, self.tau2, t), ca))


        fast_response = np.concatenate([fast_response, np.zeros(len(chargeaccumulated) -
                            fast_response.shape[0])])

        R2 = fast_response - chargeaccumulated
        ind = R2 < 0
        R2 = np.where(R2 > 0, R2, 0)  # rectify again
        return R2

    def stationary_nonlinearity(self, fast_response_ca):
        # now we put in the stationary nonlinearity of Devyani's:
        R2norm = fast_response_ca / fast_response_ca.max()  # normalize
        scale_factor = (self.asymptote / (1 + np.exp(-(fast_response_ca / self.slope) +
                        self.shift)))
        R3 = R2norm * scale_factor  # scaling factor varies with original
        return R3

    def slow_response(self, fast_response_ca_snl, convolution=None):
        # this is cropped as tightly as
        # possible for speed sake
        t = np.arange(0, self.tau3 * 8, self.Fs)
        G3 = gamma(3, self.tau3, t)

        if convolution=='numpy':
            conv = np.convolve(G3, fast_response_ca_snl)
        elif convolution=='fftconvolve':
            conv = fftconvolve(G3, fast_response_ca_snl)
        elif convolution=='sparseconv':
            conv = utils.sparseconv(G3, fast_response_ca_snl)

        R4 = self.Fs * conv

        return R4
