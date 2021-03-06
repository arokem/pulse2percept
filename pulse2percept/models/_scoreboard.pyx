import numpy as np
cimport numpy as np
from cython.parallel import prange
from libc.math cimport(pow as c_pow, exp as c_exp)


cpdef scoreboard(double[:] stim, double[:] xel, double[:] yel,
                 double xtissue, double ytissue, double rho, double th):
    cdef np.intp_t idx, n_stim
    cdef double bright
    n_stim = len(stim)
    bright = 0.0
    if n_stim == 0:
        return bright
    with nogil:
        for idx in range(n_stim):
            dist2 = c_pow(xtissue - xel[idx], 2) + c_pow(ytissue - yel[idx], 2)
            bright += stim[idx] * c_exp(-dist2 / (2.0 * c_pow(rho, 2)))
    if bright < th:
        bright = 0
    return bright
