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

import HelperFunction as HF


class Plotting:
    @staticmethod
    def MakeFigureWidget(frame, figuresize):
        fig, ax = plt.subplots(figsize=figuresize, tight_layout=True)
        tk_plt = FigureCanvasTkAgg(fig, frame)
        tk_plt.get_tk_widget().pack(side=LEFT, fill=BOTH, expand=1)
        plt.close(fig)
        return ax

    @staticmethod
    def ShowImage(imageinfo, ax) -> None:
        ax.cla()
        ax.imshow(imageinfo, cmap="gray", vmin=max(0, np.mean(imageinfo) - 3*np.std(imageinfo)), vmax=np.mean(imageinfo) + 3*np.std(imageinfo), origin='lower')
        # ax.imshow(imageinfo, cmap="gray", vmin=35300, vmax=42700, origin='lower')
        plt.pause(0.1)
        plt.ion()

    @staticmethod
    def Show2DPlot(ax, x, y, c='r', label=None, cla = True, xlabel='', ylabel='') -> None:
        if cla:
            ax.cla()
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)

        ax.plot(x, y, c=c, alpha=0.7, label=label)
        ax.set_xlim(x.min(), x.max())
        ax.set_ylim(y.min(), y.max())
        ax.grid(True)
        ax.legend(loc='best')
        Plotting.forceAspect(ax, 1)
        plt.pause(0.1)
        plt.ion()

    @staticmethod
    def DrawDivision(ax, imageInfo, numRow, numCol) -> None:

        totalRow, totalCol = imageInfo.shape[0], imageInfo.shape[1]

        plt.pause(0.1)
        plt.ion()

        for j in range(numRow - 1):
            ax.axhline(y=totalRow*(j+1)/numRow, xmin=0, xmax=totalCol-1, color='red')
        for k in range(numCol - 1):
            ax.axvline(x=totalCol*(k+1)/numCol, ymin=0, ymax=totalRow-1, color='red')

    @staticmethod
    def ShowDivision_Average(ax, data, x, y):
        # if not np.ma.isMaskedArray(data):
        #     avg = data.sum() / np.count_nonzero(data)
        # else:
        avg = data.mean()
        ax.text(x, y, int(avg), c='r', horizontalalignment='center', verticalalignment='center')
        return avg

    @staticmethod
    def forceAspect(ax, aspect=1):
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        ax.set_aspect(abs((xlim[1] - xlim[0]) / (ylim[1] - ylim[0])) / aspect)

class UIConfiguration:

    @staticmethod
    def set_text(entry, text):
        entry.delete(0, END)
        entry.insert (0, text)
        return

    @staticmethod
    def Save2Clipboard(data):
        df = pd.DataFrame(data)
        df.to_clipboard(excel=True)

    @staticmethod
    def ButtonState(button, condition):
        if condition == True:
            button["state"] = 'normal'
        else:
            button["state"] = 'disable'


class ButtonClickedEvent:
    @staticmethod
    def Open_Path(fd):

        filepath = tkinter.filedialog.askdirectory(initialdir=f"{fd}/")
        return filepath

    @staticmethod
    def Open_File(fd):

        filepath = tkinter.filedialog.askopenfilename(initialdir=f"{fd}/")
        return filepath

    @staticmethod
    def Read_Folder(filepath, fileformat, filedtype, ImageSize):

        read_data = np.array([], dtype=np.float64)
        onlyfiles = [f for f in listdir(filepath) if isfile(join(filepath, f))]

        for file_now in onlyfiles:
            if file_now[-3:] == fileformat:
                try:
                    fid = open(f"{filepath}/{file_now}", "rb")
                    read_data_now = np.fromfile(fid, dtype=filedtype, sep="")
                    read_data_now = read_data_now.reshape(ImageSize)
                    fid.close()

                    if not read_data.any():
                        read_data = read_data_now[np.newaxis, :]
                        continue

                    read_data = np.append(read_data, read_data_now[np.newaxis, :], axis=0)

                except ValueError:
                    print(f'{file_now} Skipped')

        return np.array(read_data, dtype=np.float64)

    @staticmethod
    def Read_File(filepath, fileformat, filedtype, ImageSize):

        read_data = np.array([], dtype=np.float64)
        file_now = filepath

        if file_now[-3:] == fileformat:

            fid = open(f"{file_now}", "rb")
            read_data = np.fromfile(fid, dtype=filedtype, sep="")
            read_data = read_data.reshape(ImageSize)
            fid.close()

        return np.array(read_data, dtype=np.float64)

    @staticmethod
    def Save_File(filepath, filedtype, data):

        fn = filepath[filepath.rfind('/')+1:filepath.rfind('.')]

        filepath = tkinter.filedialog.asksaveasfilename(initialdir=f"{filepath}/",
                                                        initialfile = f'Line Calibrated {fn} W{data.shape[1]}H{data.shape[0]}',
                                                        title="Save as",
                                                        defaultextension=".raw",
                                                        filetypes=(("raw", ".raw"),
                                                                   ("tif", ".tiff"),
                                                                   ("all files", "*")))

        if filepath[-3:] == "raw":
            with open(filepath, 'wb') as f:
                f.write((data.astype(filedtype)).tobytes())
                f.close()
        elif filepath[-4:] == "tiff":
            imageio.imwrite(filepath, data.astype(filedtype))

    @staticmethod
    def Save_Files(filepath, filedtype, data):

        filepath = ButtonClickedEvent.Open_Path(filepath)

        for k, d in enumerate(data):
            fname = filepath + f"/IMG{k:04} + W{data.shape[1]}xH{data.shape[2]} {filedtype.__name__}.raw"

            with open(fname, 'wb') as f:
                f.write((d.astype(filedtype)).tobytes())
                f.close()

    @staticmethod
    def Save_csv(filepath, data):
        filepath = tkinter.filedialog.asksaveasfilename(initialdir=f"{filepath}/",
                                                        title="Save as",
                                                        defaultextension=".xlsx",
                                                        filetypes=(("Xlsx Files", ".xlsx"),
                                                                   ("all files", "*")))
        filepath = f"{filepath}.xlsx"

        mean = pd.DataFrame(data)
        writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
        mean.to_excel(writer, sheet_name='Mean')
        writer.close()

    @staticmethod
    def SaveClipboard(dataframe):
        dataframe.to_clipboard(excel=True)

    @staticmethod
    def Set_ROI(Data, ROI1, ROI2):
        X1, X2, Y1, Y2 = ROI1[0], ROI2[0], ROI1[1], ROI2[1]

        L, R = min(X1, X2), max(X1, X2)
        U, D = min(Y1, Y2), max(Y1, Y2)

        if Data.ndim == 2:
            return Data[U:D+1, L:R+1]

        if Data.ndim == 3:
            return Data[:, U:D + 1, L:R + 1]

    @staticmethod
    def Set_FOI(Data, FOI):
    #"""FOI: Frame of Interest"""

        return Data[FOI[0]-1:FOI[1]]

    @staticmethod
    def Division(ax, imageinfo, numRow, numCol) -> None:
        Plotting.DrawDivision(ax, imageinfo, numRow, numCol)

    @staticmethod
    def Average(ax, imageinfo, numRow, numCol):

        # if not np.ma.isMaskedArray(imageinfo):
        #     totalRow, totalCol = imageinfo.shape[0], imageinfo.shape[1]
        #     mask = np.zeros((totalRow, totalCol))
        #     avg = np.zeros(numRow * numCol)
        #     Division = np.zeros((numRow * numCol, totalRow, totalCol))
        #
        #     for j in range(numRow):
        #         for k in range(numCol):
        #             mask[int(totalRow * j / numRow):int(totalRow * (j + 1) / numRow),
        #             int(totalCol * k / numCol):int(totalCol * (k + 1) / numCol)] = 1
        #             Division[j * numCol + k] = imageinfo * mask
        #             avg[j * numCol + k] = Plotting.ShowDivision_Average(ax, Division[j * numCol + k],
        #                                                                    int(totalRow * (j + 0.5) / numRow),
        #                                                                    int(totalCol * (k + 0.5) / numCol))
        #             mask[:, :] = 0

        # else:
        totalRow, totalCol = imageinfo.shape[0], imageinfo.shape[1]
        Mask = imageinfo.mask.copy()
        avg = np.zeros(numRow*numCol)

        for j in range(numRow):
            for k in range(numCol):
                Mask = HF.DataProcessing.Division_Mask(imageinfo, Mask, totalRow, numRow, j, totalCol, numCol, k)
                MaskedImage = np.ma.masked_array(imageinfo, mask = ~Mask)
                avg[j*numCol +k] = Plotting.ShowDivision_Average(ax, MaskedImage, int(totalRow*(j+0.5)/numRow), int(totalCol*(k+0.5)/numCol))

        return avg

    @staticmethod
    def Calculate_DSNU(imageinfo, Differential = True):
        if Differential:
            imageinfo = HF.DataProcessing.DifferentialImage(imageinfo)
        FrameNoise = HF.DataProcessing.FrameNoise(data = imageinfo, Differential = Differential)
        TotalNoise = HF.DataProcessing.TotalNoise(data = imageinfo, Differential = Differential)
        RowLineNoise = HF.DataProcessing.LineNoise(data = imageinfo, Differential = Differential, Orientation = 'Row')
        ColLineNoise = HF.DataProcessing.LineNoise(data = imageinfo, Differential = Differential, Orientation = 'Col')
        LineNoise = np.sqrt(np.square(RowLineNoise) + np.square(ColLineNoise))
        PixelNoise = HF.DataProcessing.PixelNoise(TotalNoise, FrameNoise, LineNoise)
        return {"TotalNoise" : TotalNoise, "FrameNoise" : FrameNoise, "RowLineNoise" : RowLineNoise,
                "ColLineNoise" : ColLineNoise, "PixelNoise" : PixelNoise, "ImageInfo": imageinfo}

    @staticmethod
    def Calculate_TemporalNoise(imageinfo, Differential = True):
        if Differential:
            imageinfo = HF.DataProcessing.DifferentialImage(imageinfo)
        FrameNoise = HF.DataProcessing.FrameNoise(data = imageinfo, Differential = Differential)
        TotalNoise = HF.DataProcessing.RMS(HF.DataProcessing.TemporalNoise(data = imageinfo, Differential = Differential))
        RowLineNoise = HF.DataProcessing.LineNoise(data = imageinfo, Differential = Differential, Orientation = 'Row')
        ColLineNoise = HF.DataProcessing.LineNoise(data = imageinfo, Differential = Differential, Orientation = 'Col')
        LineNoise = np.sqrt(np.square(RowLineNoise) + np.square(ColLineNoise))
        # PixelNoise = HF.DataProcessing.PixelNoise(TotalNoise, FrameNoise, LineNoise)
        return {"TotalNoise" : TotalNoise, "FrameNoise" : FrameNoise, "RowLineNoise" : RowLineNoise,
                "ColLineNoise" : ColLineNoise, "PixelNoise" : 'None', "ImageInfo": imageinfo}

    @staticmethod
    def Apply_IQR_DSNU(imageinfo, NIQR, NIteration, Differential = True, ExcludingZero = True, HPF = True):
        if Differential:
            imageinfo = HF.DataProcessing.DifferentialImage(imageinfo)

        if HPF:
            imageinfo = HF.DataProcessing.Highpass_Filter(imageinfo)

        Mask = (imageinfo.copy()).astype(bool)
        Mask.fill(True)

        if ExcludingZero:
            Mask = (imageinfo!=0)

        for k in range(NIteration):
            MaskedArray = np.ma.masked_array(imageinfo, mask=~Mask)[np.ma.masked_array(imageinfo, mask=~Mask).mask==False].data
            Mask = Mask * HF.DataProcessing.IQR_Mask(imageinfo = imageinfo, MaskedArray = MaskedArray, NIQR = NIQR)

        MaskedImage = np.ma.masked_array(data=imageinfo, mask=~Mask)

        FrameNoise = HF.DataProcessing.FrameNoise(data = MaskedImage, Differential = Differential)
        TotalNoise = HF.DataProcessing.TotalNoise(data = MaskedImage, Differential = Differential)
        RowLineNoise = HF.DataProcessing.LineNoise(data = MaskedImage, Differential = Differential, Orientation = 'Row')
        ColLineNoise = HF.DataProcessing.LineNoise(data = MaskedImage, Differential = Differential, Orientation = 'Col')
        LineNoise = np.sqrt(np.square(RowLineNoise) + np.square(ColLineNoise))
        PixelNoise = HF.DataProcessing.PixelNoise(TotalNoise, FrameNoise, LineNoise)
        return {"TotalNoise" : TotalNoise, "FrameNoise" : FrameNoise, "RowLineNoise" : RowLineNoise,
                "ColLineNoise" : ColLineNoise, "PixelNoise" : PixelNoise, "ImageInfo" : MaskedImage.data.copy(), "Mask": Mask}

    @staticmethod
    def Apply_IQR_TemporalNoise(imageinfo, NIQR, NIteration, Differential = True, ExcludingZero = True, HPF = True):
        if Differential:
            imageinfo = HF.DataProcessing.DifferentialImage(imageinfo)

        if HPF:
            imageinfo = HF.DataProcessing.Highpass_Filter(imageinfo)

        Mask = (imageinfo.copy()).astype(bool)
        Mask.fill(True)

        if ExcludingZero:
            Mask = (imageinfo!=0)

        for k in range(NIteration):
            MaskedArray = np.ma.masked_array(imageinfo, mask=~Mask)[np.ma.masked_array(imageinfo, mask=~Mask).mask==False].data
            Mask = Mask * HF.DataProcessing.IQR_Mask(imageinfo = imageinfo, MaskedArray = MaskedArray, NIQR = NIQR)

        MaskedImage = np.ma.masked_array(data=imageinfo, mask=~Mask)

        FrameNoise = HF.DataProcessing.FrameNoise(data = MaskedImage, Differential = Differential)
        TotalNoise = HF.DataProcessing.RMS(HF.DataProcessing.TemporalNoise(data = MaskedImage, Differential = Differential))

        if Differential == False:
            TemporalNoise_Temp = HF.DataProcessing.TemporalNoise(data=MaskedImage, Differential=Differential)
            TemporalNoise = ButtonClickedEvent.IQR(TemporalNoise_Temp, NIQR, NIteration, ExcludingZero)
            TotalNoise = HF.DataProcessing.RMS(TemporalNoise)

        RowLineNoise = HF.DataProcessing.LineNoise(data = MaskedImage, Differential = Differential, Orientation = 'Row')
        ColLineNoise = HF.DataProcessing.LineNoise(data = MaskedImage, Differential = Differential, Orientation = 'Col')
        LineNoise = np.sqrt(np.square(RowLineNoise) + np.square(ColLineNoise))
        return {"TotalNoise" : TotalNoise, "FrameNoise" : FrameNoise, "RowLineNoise" : RowLineNoise,
                "ColLineNoise" : ColLineNoise, "PixelNoise" : 'None', "ImageInfo" : MaskedImage.data.copy(), "Mask": Mask}

    @staticmethod
    def IQR(imageinfo, NIQR, NIteration, ExcludingZero = True):
        Mask = (imageinfo.copy()).astype(bool)
        Mask.fill(True)
        if ExcludingZero:
            Mask = (imageinfo!=0)

        for k in range(NIteration):
            MaskedArray = np.ma.masked_array(imageinfo, mask=~Mask)[np.ma.masked_array(imageinfo, mask=~Mask).mask==False].data
            Mask = Mask * HF.DataProcessing.IQR_Mask(imageinfo = imageinfo, MaskedArray = MaskedArray, NIQR = NIQR)

        MaskedImage = np.ma.masked_array(data=imageinfo, mask=~Mask)

        return MaskedImage

    @staticmethod
    def DeNoise(imageInfo, nG, nD):
        r = int(imageInfo.shape[0] / nG)
        c = int(imageInfo.shape[1] / nD)

        for j in range(r):
            for k in range(c):
                tempData = HF.DataProcessing.SelectBlock(imageInfo, nG*j, nG*(j+1), nD*k, nD*(k+1))
                imageInfo[nG*j:nG*(j+1), nD*k:nD*(k+1)] = HF.DataProcessing.LineCalibration(tempData)

        return imageInfo
