"""Written by Anirudh Patel."""
from scipy import signal
from scipy.fftpack import fft
from scipy.fftpack import ifft
import numpy as np
import scipy.io as sio
import time

def createFilters():
    fs = 500 
    f_nyquist = fs/2 # Calling nyquist fs/2 because this corresponds to pi radians
    numtaps = 71 # must be less than sig_length / 3

    h_lp_ecg = signal.firwin(numtaps, 150./f_nyquist)
    h_lp_icg = signal.firwin(numtaps, 1./f_nyquist)
    h_lp_ppg = signal.firwin(numtaps, 30./f_nyquist) # Can be used for ICG - cardiac
    h_60 = signal.firwin(numtaps, [55./f_nyquist, 65./f_nyquist])

    return(h_lp_ecg, h_lp_icg, h_lp_ppg, h_60)

def filterSignals(buff1, buff2, buff3, buff4, h_ecg, h_icg, h_ppg, h_60):

    ecg_filt = signal.filtfilt(h_ecg,1,buff1)
    ecg_out = signal.filtfilt(h_60,1,ecg_filt)

    resp_filt = signal.filtfilt(h_icg,1,buff2)
    resp_out = signal.filtfilt(h_60,1,resp_filt)

    icg_filt = signal.filtfilt(h_ppg,1,buff3)
    icg_out = signal.filtfilt(h_60,1,icg_filt)

    ppg_filt = signal.filtfilt(h_ppg,1,buff4)
    ppg_out = signal.filtfilt(h_60,1,ppg_filt)

    return(ecg_out, resp_out, icg_out, ppg_out)