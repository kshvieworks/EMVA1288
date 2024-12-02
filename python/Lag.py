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

class LagAnalysis:
    def __init__(self, window):
        self.window = window
        self.window.title("Lag Analysis")
        # self.window.config(background='#FFFFFF')
        self.window.geometry(f"{fw+350}x{int(2*fh/3)+100}")
        self.window.resizable(True, True)

        self.filepath = ""
        self.ImageSize_Row = IntVar()
        self.ImageSize_Col = IntVar()

        self.FOI_Start, self.FOI_End, self.ROI_Left, self.ROI_Right, self.ROI_Up, self.ROI_Dn =\
            IntVar(), IntVar(), IntVar(), IntVar(), IntVar(), IntVar()
        self.read_data = np.array([], dtype=np.float64)
        self.frame_average = np.array([], dtype=np.float64)
        self.Average = np.array([], dtype=np.float64)

        self.DarkSubtraction = BooleanVar()
        self.ExposuredFrame_Start, self.ExposuredFrame_End, self.DarkFrame_Start, self.DarkFrame_End =\
            IntVar(), IntVar(), IntVar(), IntVar()

        self.Division_Column, self.Division_Row = IntVar(), IntVar()

        self.Output1 = np.array([], dtype=np.float64)
        self.Output1s = np.array([], dtype=np.float64)
        self.Output2 = np.array([], dtype=np.float64)
        self.Output2s = np.array([], dtype=np.float64)

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
        WH.UIConfiguration.set_text(self.Entry5_1_1, '0')
        WH.UIConfiguration.set_text(self.Entry5_1_2, f"{int(self.InputData.shape[2]) - 1}")
        WH.UIConfiguration.set_text(self.Entry5_2_1, '0')
        WH.UIConfiguration.set_text(self.Entry5_2_2, f'{int(self.InputData.shape[1]) - 1}')

    def Show_ROI(self, ax, Frame):

        FOI = np.array([int(self.FOI_Start.get()), int(self.FOI_End.get())])
        ROI1 = np.array([int(self.ROI_Left.get()), int(self.ROI_Dn.get())])
        ROI2 = np.array([int(self.ROI_Right.get()), int(self.ROI_Up.get())])

        Frame = WH.ButtonClickedEvent.Set_ROI(Frame, ROI1, ROI2)
        Frame = WH.ButtonClickedEvent.Set_FOI(Frame, FOI)
        self.ROI_Data = Frame

        WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(self.ROI_Data), ax)

    def ShowBlock(self, ax, lag, dark, row, col):

        WH.Plotting.DrawDivision(ax, HF.DataProcessing.TemporalAverage(lag), row, col)

        self.Output1s = np.array([], dtype=np.float64)
        self.Output2s = np.array([], dtype=np.float64)

        lag = HF.DataProcessing.Array2Maskedarray(lag)
        for data in lag:
            if self.Output1s.size == 0:
                self.Output1s = WH.ButtonClickedEvent.Average(ax, data, row, col, text=False)[:, np.newaxis].copy()
            else:
                self.Output1s = np.append(self.Output1s, WH.ButtonClickedEvent.Average(ax, data, row, col, text=False)[:, np.newaxis].copy(), axis=1)

        dark = HF.DataProcessing.Array2Maskedarray(dark)
        for data in dark:
            if self.Output2s.size == 0:
                self.Output2s = WH.ButtonClickedEvent.Average(ax, data, row, col, text=False)[:, np.newaxis].copy()
            else:
                self.Output2s = np.append(self.Output2s, WH.ButtonClickedEvent.Average(ax, data, row, col, text=False)[:, np.newaxis].copy(), axis=1)

    def Calculate(self, ax1, ax2, ROIData):

        WH.Plotting.ShowImage(HF.DataProcessing.TemporalAverage(ROIData), ax1)

        # ROIData = HF.DataProcessing.Array2Maskedarray(ROIData)
        Average = HF.DataProcessing.SpatialAverage(ROIData)

        WH.Plotting.Show2DPlot(ax2, np.arange(Average.shape[0]) + 1, Average, c='r', label='Time Response',
                               cla=True, xlabel='Frame Number $n^{th}$', ylabel='Pixel Value [DN]')

    def LagFrameSpatialAverage(self, ax, ROIData, Start, End):

        Average = ROIData[Start - 1: End]

        WH.Plotting.Show2DPlot(ax, np.arange(Start, End + 1), HF.DataProcessing.SpatialAverage(Average), c='b',
                               label='Lag Data', cla=False, axLimSet=False)

        self.Output1 = Average.copy()

    def DarkFrameSpatialAverage(self, ax, ROIData, Start, End):

        Average = ROIData[Start - 1: End]

        WH.Plotting.Show2DPlot(ax, np.arange(Start, End + 1), HF.DataProcessing.SpatialAverage(Average), c='g',
                               label='Dark Data', cla=False, axLimSet = False)

        self.Output2 = Average.copy()

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
        self.Button1 = tkinter.Button(self.InputinfoFrame, text='Open File', command=self.Open_Path)
        self.Button1.grid(column=col, row=2)
        self.Label1_1 = tkinter.Label(self.InputinfoFrame, text='Image Size(Row, Col)')
        self.Label1_1.grid(column=col, row=3)
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

        col = col + Entry2Span

        Entry3span = 0
        # self.Label3 = tkinter.Label(self.InputinfoFrame)
        # self.Label3.grid(column=col, row = 1, columnspan=10)
        # self.Button3 = tkinter.Button(self.InputinfoFrame, text='Dark File', command=self.Dark_Image)
        # self.Button3.grid(column=col, row=2, columnspan=Entry3span)
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
        self.Button6 = tkinter.Button(self.InputinfoFrame, text='Show ROI', command=lambda: self.Show_ROI(self.ROIWidget, self.InputData.copy()))
        self.Button6.grid(column=col, row=2, columnspan=Entry6Span)
        self.Label6_1_1 = tkinter.Label(self.InputinfoFrame, text='Image Size')
        self.Label6_1_1.grid(column=col, row=3)
        self.Label6_2_1 = tkinter.Label(self.InputinfoFrame, text='Frame')
        self.Label6_2_1.grid(column=col, row=4)
        self.Label6_3_1 = tkinter.Label(self.InputinfoFrame, text='ROI(Left, Right)')
        self.Label6_3_1.grid(column=col, row=5)
        self.Label6_4_1 = tkinter.Label(self.InputinfoFrame, text='ROI(Down, Up')
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

        Entry7Span = 1
        self.Button7 = tkinter.Button(self.InputinfoFrame, text='Calculate',
                                      command=lambda: self.Calculate(self.ImageWidget, self.ROIWidget,
                                                                     self.ROI_Data.copy()
                                                                     ))
        self.Button7.grid(column=col, row=2, columnspan=Entry7Span)
        col = col + Entry7Span

        Entry8Span = 2
        self.Button8 = tkinter.Button(self.InputinfoFrame, text='Lag Frame Range',
                                      command=lambda: self.LagFrameSpatialAverage(self.ROIWidget, self.ROI_Data.copy(),
                                                                             self.ExposuredFrame_Start.get(),
                                                                             self.ExposuredFrame_End.get())
                                      )
        self.Button8.grid(column=col, row=2, columnspan=Entry8Span)
        self.Entry8_1_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ExposuredFrame_Start, relief="ridge")
        self.Entry8_1_1.grid(column=col, row=3)
        self.Entry8_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.ExposuredFrame_End, relief="ridge")
        self.Entry8_1_2.grid(column=col+1, row=3)
        self.CheckButton8_2 = tkinter.Checkbutton(self.InputinfoFrame, text="Get Dark Frame",
                                                    variable=self.DarkSubtraction,
                                                    command=lambda: WH.UIConfiguration.ButtonState(
                                                        [self.Entry9_1_1, self.Entry9_1_2, self.Button9, self.Button11],
                                                        self.DarkSubtraction.get()))
        self.CheckButton8_2.grid(column=col, row=4, columnspan=Entry8Span)
        self.CheckButton8_2.select()
        col = col + Entry8Span

        Entry9Span = 2
        self.Button9 = tkinter.Button(self.InputinfoFrame, text='Dark Frame Range',
                                      command=lambda: self.DarkFrameSpatialAverage(self.ROIWidget, self.ROI_Data.copy(),
                                                                        self.DarkFrame_Start.get(),
                                                                        self.DarkFrame_End.get())
                                      )
        self.Button9.grid(column=col, row=2, columnspan=Entry9Span)
        self.Entry9_1_1 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.DarkFrame_Start, relief="ridge")
        self.Entry9_1_1.grid(column=col, row=3)
        self.Entry9_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.DarkFrame_End, relief="ridge")
        self.Entry9_1_2.grid(column=col+1, row=3)
        col = col + Entry9Span

        Entry10Span = 2
        self.Label10_1_1 = tkinter.Label(self.InputinfoFrame, text='Column')
        self.Label10_1_1.grid(column = col, row = 3)
        self.Label10_2_1 = tkinter.Label(self.InputinfoFrame, text='Row')
        self.Label10_2_1.grid(column = col, row = 4)

        self.Entry10_1_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.Division_Column, relief="ridge")
        self.Entry10_1_2.grid(column=col + 1, row=3)
        self.Entry10_2_2 = tkinter.Entry(self.InputinfoFrame, width=4, textvariable=self.Division_Row, relief="ridge")
        self.Entry10_2_2.grid(column=col + 1, row=4)

        self.Button10 = tkinter.Button(self.InputinfoFrame, text='Division',
                                      command=lambda: self.ShowBlock(self.ImageWidget, self.Output1, self.Output2, int(self.Division_Row.get()), int(self.Division_Column.get())))
        self.Button10.grid(column=col, row=2, columnspan=Entry10Span)
        col = col + Entry10Span

        Entry11Span = 1
        self.Button11 = tkinter.Button(self.InputinfoFrame, text='Save Dark to Clipboard', command=lambda: self.SaveClipboardBTNEvent(self.Output2s.copy()))
        self.Button11.grid(column=col, row=2, columnspan=Entry11Span)
        self.Button11_2 = tkinter.Button(self.InputinfoFrame, text='Save Lag to Clipboard', command=lambda: self.SaveClipboardBTNEvent(self.Output1s.copy()))
        self.Button11_2.grid(column=col, row=3)
        col = col + Entry11Span


if __name__ == '__main__':
    window = tkinter.Tk()
    LagAnalysis(window)
    window.mainloop()