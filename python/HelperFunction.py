import tkinter.filedialog

import imageio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from os import listdir
from os.path import isfile, join
import tkinter
from tkinter import *
from scipy.ndimage import convolve, uniform_filter
from scipy.optimize import curve_fit
from scipy import stats
from scipy.ndimage import uniform_filter1d

class DataProcessing:
    @staticmethod
    def TemporalAverage(data):
        # Return 2D Image averaged over Time
        return data.mean(axis=0) if data.ndim == 3 else data

    @staticmethod
    def SpatialAverage(data):
        # Return 1D Temporal Array Averaged over All Pixels
        return data.mean(axis=(1,2)) if data.ndim == 3 else data.mean()

    @staticmethod
    def DN2Coulomb(DN, IFS=2, LSBC = 0.125E-12, LSBV = 61.035E-6):
        return LSBC*(IFS+1)*LSBV*DN

    @staticmethod
    def Coulomb2Electron(Coulomb):
        return Coulomb / 1.602E-19

    @staticmethod
    def DN2Electron(DN, IFS=2, LSBC = 0.125E-12, LSBV = 61.035E-6):
        return DataProcessing.Coulomb2Electron(DataProcessing.DN2Coulomb(DN, IFS, LSBC, LSBV))

    @staticmethod
    def DifferentialImage(data):
        return np.diff(data, axis=0)

    @staticmethod
    def GlueFrame_Vertical(data):
        return np.vstack((data[:]))

    @staticmethod
    def GlueFrame_Horizontal(data):
        return np.hstack((data[:]))

    @staticmethod
    def Binning_Horizontal(data):
        return data.mean(axis=1)

    @staticmethod
    def TemporalNoise(data, Differential = True):
        return np.std(data, axis=0) / np.sqrt(2) if Differential else np.std(data, axis=0)

    @staticmethod
    def TotalNoise(data, Differential = True):
        return np.std(data) / np.sqrt(2) if Differential else np.std(data)

    @staticmethod
    def FrameNoise(data, Differential = True):
        X = DataProcessing.SpatialAverage(data)
        return np.std(X) / np.sqrt(2) if Differential else np.std(X)

    @staticmethod
    def LineNoise(data, Differential = True, Orientation = 'Row'):
        X = DataProcessing.TemporalAverage(data)
        LineMeanX = DataProcessing.LineMean(X, Orientation)
        return np.std(LineMeanX) / np.sqrt(2) if Differential else np.std(LineMeanX)

    @staticmethod
    def PixelNoise(TotalNoise, FrameNoise, LineNoise):
        return np.sqrt(np.square(TotalNoise) - np.square(FrameNoise) - np.square(LineNoise))

    @staticmethod
    def Array2Maskedarray(imageinfo):
        return np.ma.masked_array(imageinfo, mask = False)

    @staticmethod
    def FlattenArray(imageinfo):
        return np.ravel(imageinfo)

    @staticmethod
    def FindMinimumValues(flattenimage, n):
        return flattenimage[flattenimage.argsort()[:n]]

    @staticmethod
    def IQR_Mask(imageinfo, MaskedArray, NIQR):
        Q1, Q2, Q3 = np.percentile(MaskedArray, [25, 50, 75], method='nearest')
        IQR = Q3 - Q1
        return (Q1 - NIQR * IQR < imageinfo) & (imageinfo < Q3 + NIQR * IQR)

    @staticmethod
    def Division_Mask(imageinfo, Mask, totalRow, numRow, j, totalCol, numCol, k):
        Mask.fill(False)
        Mask[int(totalRow * j / numRow):int(totalRow * (j + 1) / numRow),
        int(totalCol * k / numCol):int(totalCol * (k + 1) / numCol)] = True
        return Mask * ~imageinfo.mask

    @staticmethod
    def RMS(data):
        return np.sqrt(np.mean(data**2))

    @staticmethod
    def RMS_Division(data, numRow, numCol):
        totalRow, totalCol = data.shape[0], data.shape[1]
        Mask = data.mask.copy()
        rms = np.zeros(numRow*numCol)

        for j in range(numRow):
            for k in range(numCol):
                Mask = DataProcessing.Division_Mask(data, Mask, totalRow, numRow, j, totalCol, numCol, k)
                MaskedImage = np.ma.masked_array(data, mask = ~Mask)
                rms[j*numCol +k] = DataProcessing.RMS(MaskedImage)

        return rms
    @staticmethod
    def SpatialStddev_Division(imageinfo, numRow, numCol):
        totalRow, totalCol = imageinfo.shape[0], imageinfo.shape[1]
        Mask = imageinfo.mask.copy()
        stddev = np.zeros(numRow*numCol)

        for j in range(numRow):
            for k in range(numCol):
                Mask = DataProcessing.Division_Mask(imageinfo, Mask, totalRow, numRow, j, totalCol, numCol, k)
                MaskedImage = np.ma.masked_array(imageinfo, mask = ~Mask)
                stddev[j*numCol +k] = np.std(MaskedImage)

        return stddev

    @staticmethod
    def Data2Histogram(data, Mask = None):
        if Mask is not None:
            MaskedArray = np.ma.masked_array(data, mask=~Mask)[np.ma.masked_array(data, mask=~Mask).mask == False].data
            hist = np.histogram(MaskedArray, bins=int(np.ma.masked_array(data, ~Mask).max() - np.ma.masked_array(data, ~Mask).min()))

        else:
            hist = np.histogram(data, bins=int(data.max() - data.min()))

        return np.transpose(np.array((hist[1][:-1], hist[0])))

    @staticmethod
    def Highpass_Filter(data):

        Filtered_Data = np.zeros_like(data)
        binomial_filter = 1/16 * np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]])

        if data.ndim == 3:
            for l in range(data.shape[0]):
                img = data[l, :, :].copy()
                img = uniform_filter(img, size=7, mode='reflect')
                img = uniform_filter(img, size=11, mode='reflect')
                img = convolve(img, weights = binomial_filter, mode='reflect')

                Filtered_Data[l, :, :] = data[l, :, :] - img
        if data.ndim == 2:
            img = data.copy()
            img = uniform_filter(img, size=7, mode='reflect')
            img = uniform_filter(img, size=11, mode='reflect')
            img = convolve(img, weights=binomial_filter, mode='reflect')

            Filtered_Data = data - img
        return Filtered_Data

    @staticmethod
    def SelectBlock(data, r1, r2, c1, c2):

        L, R, U, D = min(c1, c2), max(c1, c2), min(r1, r2), max(r1, r2)

        if data.ndim == 2:
            return data[U:D, L:R]

        if data.ndim == 3:
            return data[:, U:D, L:R]

    @staticmethod
    def LowPassFilter_1stOrder(vi, vo_prev, tau, dt):

        return ((dt*vi) + (tau*vo_prev)) / (dt + tau)

    @staticmethod
    def LineMean(data, Orientation):
        return np.mean(data, axis=data.ndim-1) if Orientation == 'Row' else np.mean(data, axis=data.ndim-2)
    @staticmethod
    def LineCalibration(data, Orientation='Row'):
        return data + data.mean() - (DataProcessing.LineMean(data, Orientation))[:, None]

    @staticmethod
    def CurveFit(f, x, y, guess = 5, maxfev=10000):
        popt = None

        if f == 'Exponential':
            popt, _ = curve_fit(ModelingFunction.ExponentialCurve, x, y, guess, maxfev=maxfev)

        if f == 'Linear':
            popt = stats.linregress(x, y)[:2]

        if f == 'RollingAverage':
            if np.mean(y[:3]) <= np.mean(y[-3:]):
                y_sum = np.cumsum(y)
                n = guess
                popt = np.array([(y_sum[k] - y_sum[k-n])/n if k >= n else y_sum[k]/(k+1) for k in range(y.__len__())])
            else:
                y_sum = np.cumsum(np.flip(y))
                n = guess
                popt = np.array(
                    [(y_sum[k] - y_sum[k - n]) / n if k >= n else y_sum[k] / (k + 1) for k in range(y.__len__())])
                popt = np.flip(popt)

        if f == 'Constant':
                popt = y

        return popt

    @staticmethod
    def RSquared(x, y, fit_data):

        yhat = fit_data
        ybar = np.sum(y) / len(y)
        sse = np.sum((yhat - ybar)**2)
        sst = np.sum((y - ybar)**2)

        return sse/sst

class ModelingFunction:

    @staticmethod
    def ExponentialCurve(x, a, b, c):
        return a*np.exp(b*x) + c

    @staticmethod
    def Line1D(x, a, b):
        return a*x + b




