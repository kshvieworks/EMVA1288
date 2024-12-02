import numpy as np
import os
import pandas as pd
import tkinter
from tkinter import *

import HelperFunction as HF
import WidgetHelper as WH

# fd = pathlib.Path(__file__).parent.resolve()
fd = os.getcwd()
Window_Size = [1280, 1280]
fw = int(Window_Size[0]/2)
fh = int(Window_Size[1]/2)
fs = (fw/200, fh/200)
fsPTC = (fw/200, fh/100)

class DarkCurrentAnalysis:
    def __init__(self, window):
        self.window = window
        self.window.title("Temporal Stability and Calibration")
        # self.window.config(background='#FFFFFF')
        self.window.geometry(f"{fw+450}x{int(2*fh/3)+100}")
        self.window.resizable(True, True)

        self.filepath = ""
        self.OffsetCalibration = BooleanVar()
        self.ImageSize_Row = IntVar()
        self.ImageSize_Col = IntVar()

        self.FOI_Start, self.FOI_End, self.ROI_Left, self.ROI_Right, self.ROI_Up, self.ROI_Dn =\
            IntVar(), IntVar(), IntVar(), IntVar(), IntVar(), IntVar()
        self.read_data = np.array([], dtype=np.float64)
        self.dark_data = np.array([], dtype=np.float64)
        self.frame_average = np.array([], dtype=np.float64)

        self.Division_Column, self.Division_Row = IntVar(), IntVar()
        self.NIQR, self.NIteration = DoubleVar(), IntVar()
        self.NIQR_S, self.NIteration_S = DoubleVar(), IntVar()

        self.SpatialMask = FALSE
        self.OutputFrame = FALSE
        self.Output = FALSE

        self.__main__()

    def Open_Path(self):

        self.filepath = WH.ButtonClickedEvent.Open_Path(fd)
        self.label1.configure(text=f"{self.filepath[-40:]}")

    def Read_Image(self):

        Image_Size = [int(self.ImageSize_Row.get()), int(self.ImageSize_Col.get())]
        self.read_data = WH.ButtonClickedEvent.Read_Folder(self.filepath, 'raw', np.uint16, Image_Size)

        if not hasattr(self, 'ImageWidget'):
            self.ImageWidget = WH.Plotting.MakeFigureWidget(self.ImagePlotFrame, fs)

        self.InputData = self.read_data.copy()
        self.frame_average = HF.DataProcessing.TemporalAverage(self.InputData)

        WH.Plotting.ShowImage(self.frame_average, self.ImageWidget)
        WH.UIConfiguration.set_text(self.Entry4_1_1, '1')
        WH.UIConfiguration.set_text(self.Entry4_1_2, f"{int(len(self.InputData))}")
        self.Label4_2_1.configure(text = f"1 ~ {int(len(self.InputData))}")
        WH.UIConfiguration.set_text(self.Entry5_1_1, '0')
        WH.UIConfiguration.set_text(self.Entry5_1_2, f"{int(self.InputData.shape[2]) - 1}")
        WH.UIConfiguration.set_text(self.Entry5_2_1, '0')
        WH.UIConfiguration.set_text(self.Entry5_2_2, f'{int(self.InputData.shape[1]) - 1}')


    def Dark_Image(self):

        Image_Size = [int(self.ImageSize_Row.get()), int(self.ImageSize_Col.get())]

        fpath = WH.ButtonClickedEvent.Open_File(self.filepath)
        self.Label3.configure(text=f"{fpath[-40:]}")

        self.dark_data = WH.ButtonClickedEvent.Read_File(fpath, fpath[-3:], np.uint16, Image_Size)
        self.InputData = self.InputData - self.dark_data
        self.frame_average = HF.DataProcessing.TemporalAverage(self.InputData)
        WH.Plotting.ShowImage(self.frame_average, self.ImageWidget)

    def Show_ROI(self, Frame):

        FOI = np.array([int(self.FOI_Start.get()), int(self.FOI_End.get())])
        ROI1 = np.array([int(self.ROI_Left.get()), int(self.ROI_Dn.get())])
        ROI2 = np.array([int(self.ROI_Right.get()), int(self.ROI_Up.get())])

        Frame = WH.ButtonClickedEvent.Set_ROI(Frame, ROI1, ROI2)
        Frame = WH.ButtonClickedEvent.Set_FOI(Frame, FOI)

        self.ROI_Data = Frame

        if not hasattr(self, 'ROIWidget'):
            self.ROIWidget = WH.Plotting.MakeFigureWidget(self.ROIPlotFrame, fs)

        WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(self.ROI_Data), self.ImageWidget)
        # WH.Plotting.ShowImage(self.ROI_Data, self.ROIWidget)

    def ShowBlock(self, ax, Frame, row, col):

        WH.Plotting.DrawDivision(ax, Frame, row, col)

    def Calculate(self, ax1, ax2, Frame, row, col):

        self.Show_ROI(self.InputData.copy())
        self.ShowBlock(ax1, HF.DataProcessing.TemporalAverage(Frame), row, col)

        variance_ij = (HF.DataProcessing.TemporalNoise(Frame, Differential=False))**2
        variance_ij = HF.DataProcessing.Array2Maskedarray(variance_ij)
        stddev_y = HF.DataProcessing.RMS_Division(np.sqrt(variance_ij), row, col)

        # Frame = HF.DataProcessing.Array2Maskedarray(Frame)
        Average = HF.DataProcessing.SpatialAverage(Frame)

        WH.Plotting.Show2DPlot(ax2, np.arange(Average.__len__()), Average,
                               c='r', label=f'Raw ($\\mu$={int(np.mean(Average))} $\\sigma$={int(np.std(Average))})',
                               cla=True, xlabel='Frame Number $n^{th}$', ylabel='Pixel Value [DN]')

        self.Label8_2_1.configure(text=f"{np.format_float_scientific(np.mean(Average), unique=False, precision=2)}")
        self.Label8_2_2.configure(text=f"{np.format_float_scientific(np.sqrt(np.mean(variance_ij)), unique=False, precision=2)}")
        self.Output = Average[:, np.newaxis].copy()
        self.OutputFrame = Frame.copy()


    def Apply_IQR(self, Frame, NIQR, NIteration, ax1, ax2, row, col):

        MaskedImage = WH.ButtonClickedEvent.IQR(HF.DataProcessing.TemporalAverage(Frame), NIQR, NIteration, False)
        WH.Plotting.ShowImage(MaskedImage, ax1)
        self.ShowBlock(ax1, MaskedImage.copy(), row, col)
        WH.ButtonClickedEvent.Average(ax1, MaskedImage.copy(), row, col)

        # variance_ij = HF.DataProcessing.Array2Maskedarray(variance_ij)
        # variance_ij.mask = MaskedImage.mask

        Frame = HF.DataProcessing.Array2Maskedarray(Frame)
        Frame.mask = MaskedImage.mask
        Average = HF.DataProcessing.SpatialAverage(Frame)

        variance_ij = (HF.DataProcessing.TemporalNoise(Frame, Differential=False))**2
        stddev_y = HF.DataProcessing.RMS_Division(np.sqrt(variance_ij), row, col)

        WH.Plotting.Show2DPlot(ax2, np.arange(Average.__len__()), Average,
                               c='b', label=f'IQR ($\\mu$={int(np.mean(Average))} $\\sigma$={int(np.std(Average))})',
                               cla=False)

        self.Label9_3_2.configure(text=f"{np.format_float_scientific(np.mean(Average), unique=False, precision=2)}")
        self.Label9_4_2.configure(text=f"{np.format_float_scientific(np.sqrt(np.mean(variance_ij)), unique=False, precision=2)}")

        self.SpatialMask = MaskedImage.mask
        self.Output = np.append(self.Output, Average[:, np.newaxis].copy(), axis=1)
        self.OutputFrame = Frame.data.copy()

    def Stability_Calibration(self, Frame, SpatialMask, NIQR, NIteration, ax1, ax2, row, col, FittingCurve = 'Exponential'):
        pady = Frame.shape[0]
        Frame = HF.DataProcessing.Array2Maskedarray(Frame)
        Frame.mask = SpatialMask
        Average = HF.DataProcessing.SpatialAverage(Frame)

        FittingCurve = 'Constant'
        k = 0
        for k in range(NIteration):
            x = np.arange(Average.__len__())
            if FittingCurve == 'Exponential':
                popt = HF.DataProcessing.CurveFit(FittingCurve, x, Average,
                                                  [np.mean(Average[:3] - Average[-3:]), -0.3, np.mean(Average[-3:])],
                                                  maxfev=10000)
                y = HF.ModelingFunction.ExponentialCurve(x, *popt)
                calFactor = popt[-1] - y

            elif FittingCurve == 'Linear':
                popt = HF.DataProcessing.CurveFit(FittingCurve, x, Average)
                y = HF.ModelingFunction.Line1D(x, *popt)
                calFactor = -y

            elif FittingCurve == 'RollingAverage':
                popt = HF.DataProcessing.CurveFit(FittingCurve, x, Average, 5)
                y = popt
                calFactor = -y + np.mean(y)

            elif FittingCurve == 'Constant':
                popt = HF.DataProcessing.CurveFit(FittingCurve, x, Average)
                y = popt
                calFactor = -y + np.mean(y)

            Frame = Frame + calFactor[:, np.newaxis, np.newaxis]

            MaskedFrame = WH.ButtonClickedEvent.IQR(HF.DataProcessing.SpatialAverage(Frame), NIQR, 1, False)
            Frame = np.delete(Frame, np.where(MaskedFrame.mask == True), axis=0)
            Frame.mask = SpatialMask
            Average = HF.DataProcessing.SpatialAverage(Frame)

        x = np.arange(Average.__len__())
        variance_ij = (HF.DataProcessing.TemporalNoise(Frame, Differential=False))**2
        stddev_y = HF.DataProcessing.RMS_Division(np.sqrt(variance_ij), row, col)

        WH.Plotting.Show2DPlot(ax2, x, Average, c='g', label=f'Cal({k+1}) ($\\mu$={int(np.mean(Average))} $\\sigma$={int(np.std(Average))})',
                           cla=False)

        self.Label10_3_2.configure(text=f"{np.format_float_scientific(np.mean(Average), unique=False, precision=2)}")
        self.Label10_4_2.configure(text=f"{np.format_float_scientific(np.sqrt(np.mean(variance_ij)), unique=False, precision=2)}")

        Average = np.pad(Average.data, (0, int(pady - Average.shape[0])), 'constant')
        self.Output = np.append(self.Output, Average[:, np.newaxis].copy(), axis=1)
        self.OutputFrame = Frame.data.copy()

    def SaveBTNEvent(self, fp, dtype, data):

        WH.ButtonClickedEvent.Save_Files(fp, dtype, data)

    def SaveClipboardBTNEvent(self, data):

        if data.shape[1] == 1:
            df = pd.DataFrame(data, columns=['Raw'])
        elif data.shape[1] == 2:
            df = pd.DataFrame(data, columns=['Raw', 'IQR'])
        elif data.shape[1] == 3:
            df = pd.DataFrame(data, columns=['Raw', 'IQR', 'Cal'])
        else:
            df = pd.DataFrame(data)

        WH.ButtonClickedEvent.SaveClipboard(df)

    def __main__(self):

        self.InputFrame = tkinter.Frame(self.window, width=fw, height=fh+100)
        self.InputFrame.grid(column=0, row=0)
        self.ImagePlotFrame = tkinter.Frame(self.InputFrame, bg='white', width=fw/2, height=fh/2)
        self.ImagePlotFrame.grid(column=0, row=0)
        self.ROIPlotFrame = tkinter.Frame(self.InputFrame, bg='white', width=fw / 2, height=fh / 2)
        self.ROIPlotFrame.grid(column=1, row=0)

        self.InputinfoFrame = tkinter.Frame(self.InputFrame, width=fw, height=100)
        self.InputinfoFrame.grid(column=0, row=1, columnspan = 2)

        col = 0

        Entry1Span = 1
        self.label1 = tkinter.Label(self.InputinfoFrame)
        self.label1.grid(column=col, row=1, columnspan=3)
        self.Button1 = tkinter.Button(self.InputinfoFrame, text='Open File', command=self.Open_Path)
        self.Button1.grid(column=col, row=2)
        self.Label1_1 = tkinter.Label(self.InputinfoFrame, text='Image Size(Row, Col)')
        self.Label1_1.grid(column=col, row=3)
        self.Label1_2 = tkinter.Label(self.InputinfoFrame, text='Offset Calibration')
        self.Label1_2.grid(column=col, row=4)
        col = col + Entry1Span

        Entry2Span = 2
        self.Button2 = tkinter.Button(self.InputinfoFrame, text='Read File', command=self.Read_Image)
        self.Button2.grid(column=col, row=2, columnspan=Entry2Span)
        self.Entry2_1_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ImageSize_Row, relief="ridge")
        self.Entry2_1_1.grid(column=col, row=3)
        WH.UIConfiguration.set_text(self.Entry2_1_1, '1280')
        self.Entry2_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ImageSize_Col, relief="ridge")
        self.Entry2_1_2.grid(column=col+1, row=3)
        WH.UIConfiguration.set_text(self.Entry2_1_2, '1280')
        self.CheckButton2_2 = tkinter.Checkbutton(self.InputinfoFrame, text="", variable=self.OffsetCalibration,
                                                  command=lambda: WH.UIConfiguration.ButtonState([self.Button3], self.OffsetCalibration.get()))
        self.CheckButton2_2.select()
        self.CheckButton2_2.grid(column = col, row = 4, columnspan=Entry2Span)
        col = col + Entry2Span

        Entry3span = 1
        self.Label3 = tkinter.Label(self.InputinfoFrame)
        self.Label3.grid(column=col, row = 1, columnspan=10)
        self.Button3 = tkinter.Button(self.InputinfoFrame, text='Dark File', command=self.Dark_Image)
        self.Button3.grid(column=col, row=2, columnspan=Entry3span)
        col = col + Entry3span

        Entry4Span = 2
        self.Entry4_1_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.FOI_Start, relief="ridge")
        self.Entry4_1_1.grid(column=col, row=3)
        WH.UIConfiguration.set_text(self.Entry4_1_1, '0')
        self.Entry4_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.FOI_End, relief="ridge")
        self.Entry4_1_2.grid(column=col+1, row=3)
        WH.UIConfiguration.set_text(self.Entry4_1_2, '0')
        self.Label4_2_1 = tkinter.Label(self.InputinfoFrame)
        self.Label4_2_1.grid(column=col, row = 4, columnspan=Entry4Span)

        self.Button4 = tkinter.Button(self.InputinfoFrame, text='Frame')
        self.Button4["state"] = 'disable'
        self.Button4.grid(column=col, row=2, columnspan=Entry4Span)
        col = col + Entry4Span

        Entry5Span = 2
        self.Entry5_1_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Left, relief="ridge")
        self.Entry5_1_1.grid(column=col, row=3)
        WH.UIConfiguration.set_text(self.Entry5_1_1, '0')
        self.Entry5_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Right, relief="ridge")
        self.Entry5_1_2.grid(column=col+1, row=3)
        WH.UIConfiguration.set_text(self.Entry5_1_2, '0')
        self.Entry5_2_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Dn, relief="ridge")
        self.Entry5_2_1.grid(column=col, row=4)
        WH.UIConfiguration.set_text(self.Entry5_2_1, '0')
        self.Entry5_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ROI_Up, relief="ridge")
        self.Entry5_2_2.grid(column=col+1, row=4)
        WH.UIConfiguration.set_text(self.Entry5_2_2, '0')

        self.Button5 = tkinter.Button(self.InputinfoFrame, text='ROI (Left, Right \n Down, Up)')
        self.Button5["state"] = "disable"
        self.Button5.grid(column=col, row=2, columnspan=Entry5Span)
        col = col + Entry5Span

        Entry6Span = 3
        self.Button6 = tkinter.Button(self.InputinfoFrame, text='Show ROI', command=lambda: self.Show_ROI(self.InputData.copy()))
        self.Button6.grid(column=col, row=2, columnspan=Entry6Span)
        self.Label6_1_1 = tkinter.Label(self.InputinfoFrame, text='Image Size')
        self.Label6_1_1.grid(column=col, row=3)
        self.Label6_2_1 = tkinter.Label(self.InputinfoFrame, text='Frame')
        self.Label6_2_1.grid(column=col, row=4)
        self.Label6_3_1 = tkinter.Label(self.InputinfoFrame, text='ROI(Left, Right)')
        self.Label6_3_1.grid(column=col, row=5)
        self.Label6_4_1 = tkinter.Label(self.InputinfoFrame, text='ROI(Down, Up)')
        self.Label6_4_1.grid(column=col, row=6)
        self.Label6_1_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ImageSize_Row)
        self.Label6_1_2.grid(column=col+1, row=3)
        self.Label6_2_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.FOI_Start)
        self.Label6_2_2.grid(column=col+1, row=4)
        self.Label6_3_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Left)
        self.Label6_3_2.grid(column=col+1, row=5)
        self.Label6_4_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Dn)
        self.Label6_4_2.grid(column=col+1, row=6)
        self.Label6_1_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ImageSize_Col)
        self.Label6_1_3.grid(column=col+2, row=3)
        self.Label6_2_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.FOI_End)
        self.Label6_2_3.grid(column=col+2, row=4)
        self.Label6_3_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Right)
        self.Label6_3_3.grid(column=col+2, row=5)
        self.Label6_4_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Up)
        self.Label6_4_3.grid(column=col+2, row=6)
        col = col + Entry6Span

        Entry7Span = 2
        self.Label7_1_1 = tkinter.Label(self.InputinfoFrame, text='Column')
        self.Label7_1_1.grid(column = col, row = 3)
        self.Label7_2_1 = tkinter.Label(self.InputinfoFrame, text='Row')
        self.Label7_2_1.grid(column = col, row = 4)

        self.Entry7_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.Division_Column, relief="ridge")
        self.Entry7_1_2.grid(column=col + 1, row=3)
        self.Entry7_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.Division_Row, relief="ridge")
        self.Entry7_2_2.grid(column=col + 1, row=4)

        self.Button7 = tkinter.Button(self.InputinfoFrame, text='Division',
                                      command=lambda: self.ShowBlock(self.ImageWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get())))
        self.Button7.grid(column=col, row=2, columnspan=Entry7Span)
        WH.UIConfiguration.ButtonState([self.Button7], False)
        WH.UIConfiguration.set_text(self.Entry7_1_2, '1')
        WH.UIConfiguration.set_text(self.Entry7_2_2, '1')
        self.Entry7_1_2.configure(state='readonly')
        self.Entry7_2_2.configure(state='readonly')

        col = col + Entry7Span

        Entry8Span = 2
        self.Button8 = tkinter.Button(self.InputinfoFrame, text='Calculate',
                                      command=lambda: self.Calculate(self.ImageWidget,
                                                                     self.ROIWidget,
                                                                     self.ROI_Data.copy(),
                                                                     int(self.Division_Row.get()),
                                                                     int(self.Division_Column.get())))
        self.Button8.grid(column=col, row=2, columnspan=Entry8Span)

        self.Label8_1_1 = tkinter.Label(self.InputinfoFrame, text='Mean')
        self.Label8_1_1.grid(column=col, row=3)
        self.Label8_1_2 = tkinter.Label(self.InputinfoFrame, text='stddev')
        self.Label8_1_2.grid(column=col, row=4)
        self.Label8_2_1 = tkinter.Label(self.InputinfoFrame)
        self.Label8_2_1.grid(column=col+1, row=3)
        self.Label8_2_2 = tkinter.Label(self.InputinfoFrame)
        self.Label8_2_2.grid(column=col+1, row=4)
        col = col + Entry8Span

        Entry9Span = 2
        self.Button9 = tkinter.Button(self.InputinfoFrame, text='Spatial IQR', command=lambda: self.Apply_IQR(self.ROI_Data.copy(),
                                                                                                            self.NIQR.get(),
                                                                                                            self.NIteration.get(),
                                                                                                            self.ImageWidget,
                                                                                                            self.ROIWidget,
                                                                                                            int(self.Division_Row.get()),
                                                                                                            int(self.Division_Column.get())))
        self.Button9.grid(column=col, row=2, columnspan=Entry9Span)
        self.Label9_1_1 = tkinter.Label(self.InputinfoFrame, text='IQR')
        self.Label9_1_1.grid(column=col, row=3)
        self.Label9_2_1 = tkinter.Label(self.InputinfoFrame, text='Iterations')
        self.Label9_2_1.grid(column=col, row=4)

        self.Entry9_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.NIQR, relief="ridge")
        self.Entry9_1_2.grid(column=col + 1, row=3)
        self.Entry9_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.NIteration, relief="ridge")
        self.Entry9_2_2.grid(column=col + 1, row=4)

        self.Label9_3_1 = tkinter.Label(self.InputinfoFrame, text='Mean')
        self.Label9_3_1.grid(column=col, row=5)
        self.Label9_4_1 = tkinter.Label(self.InputinfoFrame, text='stddev')
        self.Label9_4_1.grid(column=col, row=6)
        self.Label9_3_2 = tkinter.Label(self.InputinfoFrame)
        self.Label9_3_2.grid(column=col+1, row=5)
        self.Label9_4_2 = tkinter.Label(self.InputinfoFrame)
        self.Label9_4_2.grid(column=col+1, row=6)
        col = col + Entry9Span

        Entry10Span = 2
        self.Button10 = tkinter.Button(self.InputinfoFrame, text='Stability \n Calibration',
                                      command=lambda: self.Stability_Calibration(self.ROI_Data.copy(),
                                                                                 self.SpatialMask.copy(),
                                                                                 self.NIQR_S.get(),
                                                                                 self.NIteration_S.get(),
                                                                                 self.ImageWidget,
                                                                                 self.ROIWidget,
                                                                                 int(self.Division_Row.get()),
                                                                                 int(self.Division_Column.get())))

        self.Button10.grid(column=col, row=2, columnspan=Entry10Span)
        self.Label10_1_1 = tkinter.Label(self.InputinfoFrame, text='IQR')
        self.Label10_1_1.grid(column=col, row=3)
        self.Label10_2_1 = tkinter.Label(self.InputinfoFrame, text='Iterations')
        self.Label10_2_1.grid(column=col, row=4)

        self.Entry10_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.NIQR_S, relief="ridge")
        self.Entry10_1_2.grid(column=col + 1, row=3)
        self.Entry10_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.NIteration_S, relief="ridge")
        self.Entry10_2_2.grid(column=col + 1, row=4)

        self.Label10_3_1 = tkinter.Label(self.InputinfoFrame, text='Mean')
        self.Label10_3_1.grid(column=col, row=5)
        self.Label10_4_1 = tkinter.Label(self.InputinfoFrame, text='stddev')
        self.Label10_4_1.grid(column=col, row=6)
        self.Label10_3_2 = tkinter.Label(self.InputinfoFrame)
        self.Label10_3_2.grid(column=col + 1, row=5)
        self.Label10_4_2 = tkinter.Label(self.InputinfoFrame)
        self.Label10_4_2.grid(column=col + 1, row=6)

        col = col + Entry10Span

        Entry11Span = 1
        self.Button11_1 = tkinter.Button(self.InputinfoFrame, text='Save Clipboard',
                                        command=lambda: self.SaveClipboardBTNEvent(self.Output))
        self.Button11_1.grid(column=col, row=2, columnspan=Entry11Span)

        self.Button11_2 = tkinter.Button(self.InputinfoFrame, text='Save Image',
                                        command=lambda: self.SaveBTNEvent(self.filepath, np.uint16, self.OutputFrame))
        self.Button11_2.grid(column=col, row=3, columnspan=Entry11Span)
        col = col + Entry11Span


if __name__ == '__main__':
    window = tkinter.Tk()
    DarkCurrentAnalysis(window)
    window.mainloop()