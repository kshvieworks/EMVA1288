import numpy as np
import os
import tkinter
from tkinter import *

import pandas as pd

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
        self.window.title("Time Response with Line Sensor Platform")
        # self.window.config(background='#FFFFFF')
        self.window.geometry(f"{fw+350}x{int(2*fh/3)+100}")
        self.window.resizable(True, True)

        self.filepath = ""
        self.OffsetCalibration = BooleanVar()
        self.ImageSize_Row = IntVar()
        self.ImageSize_Col = IntVar()

        self.FOI_Start, self.FOI_End, self.ROI_Columns = IntVar(), IntVar(), StringVar()
        self.FPS, self.Fit_Range_Start, self.Fit_Range_End, self.LPF, self.LPF_tau \
            = IntVar(), IntVar(), IntVar(), BooleanVar(), DoubleVar()

        self.read_data = np.array([], dtype=np.float64)
        self.dark_data = np.array([], dtype=np.float64)
        self.frame_average = np.array([], dtype=np.float64)
        self.variance_ij = np.array([], dtype=np.float64)
        self.Average = 0

        self.Division_Column, self.Division_Row = IntVar(), IntVar()

        self.Output = FALSE
        self.Output_Cut = FALSE

        self.__main__()

    def Open_Path(self):

        self.filepath = WH.ButtonClickedEvent.Open_Path(fd)
        self.label1.configure(text=f"{self.filepath[-40:]}")

    def Read_Image(self):

        Image_Size = [int(self.ImageSize_Row.get()), int(self.ImageSize_Col.get())]
        self.read_data = WH.ButtonClickedEvent.Read_Folder(self.filepath, 'raw', np.uint16, Image_Size)

        if not hasattr(self, 'ImageWidget'):
            self.ImageWidget = WH.Plotting.MakeFigureWidget(self.ImagePlotFrame, fs)

        if not hasattr(self, 'ROIWidget'):
            self.ROIWidget = WH.Plotting.MakeFigureWidget(self.ROIPlotFrame, fs)

        self.InputData = self.read_data.copy()
        self.frame_average = HF.DataProcessing.TemporalAverage(self.InputData)

        WH.Plotting.ShowImage(self.frame_average, self.ImageWidget)
        WH.UIConfiguration.set_text(self.Entry4_1, '1')
        WH.UIConfiguration.set_text(self.Entry4_2, f"{int(len(self.InputData))}")
        WH.UIConfiguration.set_text(self.Entry5_1, '0')
        WH.UIConfiguration.set_text(self.Entry9_1_1, '1')
        WH.UIConfiguration.set_text(self.Entry9_1_2, f"{int(len(self.InputData))}")

    def Dark_Image(self):

        Image_Size = [int(self.ImageSize_Row.get()), int(self.ImageSize_Col.get())]

        fpath = WH.ButtonClickedEvent.Open_File(self.filepath)
        self.Label3.configure(text=f"{fpath[-40:]}")

        self.dark_data = WH.ButtonClickedEvent.Read_File(fpath, fpath[-3:], np.uint16, Image_Size)
        self.InputData = self.InputData - self.dark_data
        self.frame_average = HF.DataProcessing.TemporalAverage(self.InputData)
        WH.Plotting.ShowImage(self.frame_average, self.ImageWidget)

    def Show_ROI(self, ax, Frame):

        FOI = np.array([int(self.FOI_Start.get()), int(self.FOI_End.get())])
        Columns = self.ROI_Columns.get()

        # Frame = HF.DataProcessing.TemporalAverage(WH.ButtonClickedEvent.Set_FOI(Frame, FOI))
        Frame = WH.ButtonClickedEvent.Set_Columns(Frame, Columns)
        Frame = WH.ButtonClickedEvent.Set_FOI(Frame, FOI)
        self.ROI_Data = HF.DataProcessing.GlueFrame_Vertical(Frame)

        # WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(Frame), self.ImageWidget)
        WH.Plotting.ShowImage(HF.DataProcessing.GlueFrame_Horizontal(Frame), ax)
        self.ShowBlock(ax, HF.DataProcessing.GlueFrame_Horizontal(Frame), 1, Frame.shape[0])

    def ShowBlock(self, ax, Frame, row, col):

        WH.Plotting.DrawDivision(ax, Frame, row, col)

    def Calculate(self, ax1, ax2, Frame, ROIData):

        self.Show_ROI(ax1, Frame)
        WH.Plotting.Show2DPlot(ax2, np.arange(ROIData.shape[0]) + 1, HF.DataProcessing.Binning_Horizontal(ROIData),
                               c='r', label=f'Time Response',
                               cla=True, xlabel='Frame Number $n^{th}$', ylabel='Pixel Value [DN]')

        WH.UIConfiguration.set_text(self.Entry9_1_2, f"{int(len(ROIData))}")
        self.Output = (HF.DataProcessing.Binning_Horizontal(ROIData))[:, np.newaxis].copy()

    def ApplyLPF(self, ax1, ROIData, FPS, LPF, tau) -> None:

        Avg = HF.DataProcessing.Binning_Horizontal(ROIData)

        WH.Plotting.Show2DPlot(ax1, np.arange(Avg.shape[0]) + 1, Avg,
                               c='r', label=f'Time Response',
                               cla=True, xlabel='Frame Number $n^{th}$', ylabel='Pixel Value [DN]')

        if LPF:
            v0 = WH.ButtonClickedEvent.LPF_1stOrder(Avg, tau, 1/FPS)
            WH.Plotting.Show2DPlot(ax1, np.arange(Avg.shape[0]) + 1, v0, c='b', label=f'1st Order LPF', cla=False, axLimSet=False)

            self.Output = np.append(self.Output, v0[:, np.newaxis].copy(), axis=1)

        self.Output = np.insert(self.Output, 0, np.arange(Avg.shape[0])/FPS, axis=1)

    def SetFrameRange(self,ax2, Data, LPF, Start, End) -> None:

        Data = WH.ButtonClickedEvent.Set_FOI(Data, [Start, End])

        WH.Plotting.Show2DPlot(ax2, Data[:, 0], Data[:, 1],
                               c='r', label=f'Time Response',
                               cla=True, xlabel='Time, t [s]', ylabel='Pixel Value [DN]')

        if LPF:
            WH.Plotting.Show2DPlot(ax2, Data[:, 0], Data[:, -1], c='b', label=f'1st Order LPF', cla=False, axLimSet=False)

        self.Output_Cut = Data.copy()

    def Fitting(self, ax2, Data) -> None:
        popt, R2, fit_data = WH.ButtonClickedEvent.Fit_Exponential(Data[:, 0], Data[:, -1])
        'Make Label'
        #
        # params = f"f(x) = {popt[0]:.2e}$\\times$$e^\\frac{{t-{np.round(Data[0, 0], 1)}}}{{{np.round(1/popt[1], 2)}}}$ + {popt[2]:.2e} " + \
        #          f"\n $t_r$ = {np.abs(np.round(1/popt[1]*np.log(9), 2))} s" + \
        #          f"\n R$^2$ = {np.round(R2, 3)}"

        WH.Plotting.Show2DPlot(ax2, Data[:, 0], fit_data, c='g', label = f'Fitting', cla=False, axLimSet=False)

        self.Label9_3_2.configure(text=f"{np.abs(np.round(1/popt[1]*np.log(9), 3))} s")
        self.Label9_4_2.configure(text=f"{np.round(R2, 3)}")

    def SaveBTNEvent(self, data):

        WH.ButtonClickedEvent.Save_csv(self.filepath, data)

    def SaveClipboardBTNEvent(self, data):
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
        self.Button1 = tkinter.Button(self.InputinfoFrame, text='Open Path', command=self.Open_Path)
        self.Button1.grid(column=col, row=2)
        self.Label1_1 = tkinter.Label(self.InputinfoFrame, text='Image Size(Row, Col)')
        self.Label1_1.grid(column=col, row=3)
        self.Label1_2 = tkinter.Label(self.InputinfoFrame, text='Offset Calibration')
        self.Label1_2.grid(column=col, row=4)
        col = col + Entry1Span

        Entry2Span = 2
        self.Button2 = tkinter.Button(self.InputinfoFrame, text='Read Files', command=self.Read_Image)
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
        self.Entry4_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.FOI_Start, relief="ridge")
        self.Entry4_1.grid(column=col, row=3)
        WH.UIConfiguration.set_text(self.Entry4_1, '0')
        self.Entry4_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.FOI_End, relief="ridge")
        self.Entry4_2.grid(column=col+1, row=3)
        WH.UIConfiguration.set_text(self.Entry4_2, '0')
        self.Button4 = tkinter.Button(self.InputinfoFrame, text='Frame')
        self.Button4["state"] = 'disable'
        self.Button4.grid(column=col, row=2, columnspan=Entry4Span)
        col = col + Entry4Span


        Entry5Span = 2
        self.Entry5_1 = tkinter.Entry(self.InputinfoFrame, width=12, textvariable=self.ROI_Columns, relief="ridge")
        self.Entry5_1.grid(column=col, row=3)
        WH.UIConfiguration.set_text(self.Entry5_1, '0')

        self.Button5 = tkinter.Button(self.InputinfoFrame, text='ROI (Columns)')
        self.Button5["state"] = "disable"
        self.Button5.grid(column=col, row=2, columnspan=Entry5Span)
        col = col + Entry5Span

        Entry6Span = 3
        self.Button6 = tkinter.Button(self.InputinfoFrame, text='Show ROI',
                                      command=lambda: self.Show_ROI(self.ROIWidget, self.InputData.copy()), width=20)
        self.Button6.grid(column=col, row=2, columnspan=Entry6Span)
        self.Label6_1_1 = tkinter.Label(self.InputinfoFrame, text='Image Size')
        self.Label6_1_1.grid(column=col, row=3)
        self.Label6_2_1 = tkinter.Label(self.InputinfoFrame, text='Frame')
        self.Label6_2_1.grid(column=col, row=4)
        self.Label6_3_1 = tkinter.Label(self.InputinfoFrame, text='Columns')
        self.Label6_3_1.grid(column=col, row=5)
        self.Label6_1_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ImageSize_Row)
        self.Label6_1_2.grid(column=col+1, row=3)
        self.Label6_2_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.FOI_Start)
        self.Label6_2_2.grid(column=col+1, row=4)
        self.Label6_3_2 = tkinter.Label(self.InputinfoFrame, textvariable=self.ROI_Columns)
        self.Label6_3_2.grid(column=col+1, row=5, columnspan=2)
        self.Label6_1_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.ImageSize_Col)
        self.Label6_1_3.grid(column=col+2, row=3)
        self.Label6_2_3 = tkinter.Label(self.InputinfoFrame, textvariable=self.FOI_End)
        self.Label6_2_3.grid(column=col+2, row=4)
        col = col + Entry6Span

        Entry7Span = 1
        # self.Label7_1_1 = tkinter.Label(self.InputinfoFrame, text='Calculate')
        # self.Label7_1_1.grid(column = col, row = 3)
        # self.Label7_2_1 = tkinter.Label(self.InputinfoFrame, text='Row')
        # self.Label7_2_1.grid(column = col, row = 4)

        # self.Entry7_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.Division_Column, relief="ridge")
        # self.Entry7_1_2.grid(column=col + 1, row=3)
        # self.Entry7_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.Division_Row, relief="ridge")
        # self.Entry7_2_2.grid(column=col + 1, row=4)

        self.Button7 = tkinter.Button(self.InputinfoFrame, text='Calculate',
                                      command=lambda: self.Calculate(self.ImageWidget, self.ROIWidget,
                                                                     self.InputData.copy(), self.ROI_Data.copy(),
                                                                     ))
        self.Button7.grid(column=col, row=2, columnspan=Entry7Span)


        # self.Button7["state"] = "disable"

        col = col + Entry7Span

        Entry8Span = 2
        self.Button8 = tkinter.Button(self.InputinfoFrame, text='Apply LPF',
                                      command=lambda: self.ApplyLPF(self.ImageWidget, self.ROI_Data.copy(),
                                                                    self.FPS.get(),
                                                                    self.LPF.get(), self.LPF_tau.get()
                                                                    )
                                      )
        self.Button8.grid(column=col, row=2, columnspan=Entry8Span)
        self.Entry8_1_1 = tkinter.Entry(self.InputinfoFrame, width=6, textvariable=self.FPS, relief="ridge")
        self.Entry8_1_1.grid(column=col, row=3)
        self.Label8_1_2 = Label(self.InputinfoFrame, text="FPS")
        self.Label8_1_2.grid(column=col+1, row=3)
        self.CheckButton8_2_1 = tkinter.Checkbutton(self.InputinfoFrame, text="LowPass Filter",
                                                    variable=self.LPF,
                                                    command=lambda: WH.UIConfiguration.ButtonState([self.Entry8_3_1, self.Button8], self.LPF.get()))
        self.CheckButton8_2_1.grid(column = col, row = 4, columnspan = Entry8Span)
        self.CheckButton8_2_1.select()
        self.Entry8_3_1 = tkinter.Entry(self.InputinfoFrame, width=6, textvariable=self.LPF_tau, relief="ridge")
        self.Entry8_3_1.grid(column=col, row=5)
        self.Label8_3_2 = Label(self.InputinfoFrame, text="τ LPF")
        self.Label8_3_2.grid(column=col+1, row=5)

        col = col + Entry8Span

        Entry9Span = 2
        self.Button9 = tkinter.Button(self.InputinfoFrame, text='Set Frame Range',
                                      command=lambda: self.SetFrameRange(
                                                                         self.ROIWidget,
                                                                         self.Output.copy(),
                                                                         self.LPF.get(),
                                                                         int(self.Fit_Range_Start.get()),
                                                                         int(self.Fit_Range_End.get())
                                                                         )
                                      )
        self.Button9.grid(column=col, row=2, columnspan=Entry9Span)
        self.Entry9_1_1 = tkinter.Entry(self.InputinfoFrame, width=6, textvariable=self.Fit_Range_Start, relief="ridge")
        self.Entry9_1_1.grid(column=col, row=3)
        self.Entry9_1_2 = tkinter.Entry(self.InputinfoFrame, width=6, textvariable=self.Fit_Range_End, relief="ridge")
        self.Entry9_1_2.grid(column=col+1, row=3)

        self.Button9_2 = tkinter.Button(self.InputinfoFrame, text = 'Fitting',
                                        command = lambda: self.Fitting(self.ROIWidget, self.Output_Cut.copy()))
        self.Button9_2.grid(column=col, row=4, columnspan=Entry9Span)
        self.Label9_3_1 = Label(self.InputinfoFrame, text="τ")
        self.Label9_3_1.grid(column=col, row=5)
        self.Label9_3_2 = Label(self.InputinfoFrame, text="")
        self.Label9_3_2.grid(column=col+1, row=5)
        self.Label9_4_1 = Label(self.InputinfoFrame, text="R²")
        self.Label9_4_1.grid(column=col, row=6)
        self.Label9_4_2 = Label(self.InputinfoFrame, text="")
        self.Label9_4_2.grid(column=col+1, row=6)

        col = col + Entry9Span


        Entry11Span = 1
        self.Button11 = tkinter.Button(self.InputinfoFrame, text='Save Image', command=lambda: self.SaveBTNEvent(self.Output_Cut))
        self.Button11.grid(column=col, row=2, columnspan=Entry11Span)
        self.Button11_2 = tkinter.Button(self.InputinfoFrame, text='Save Clipboard', command=lambda: self.SaveClipboardBTNEvent(self.Output_Cut))
        self.Button11_2.grid(column=col, row=3)
        col = col + Entry11Span

        # Entry10Span = 1
        # col = col + Entry10Span


if __name__ == '__main__':
    window = tkinter.Tk()
    DarkCurrentAnalysis(window)
    window.mainloop()