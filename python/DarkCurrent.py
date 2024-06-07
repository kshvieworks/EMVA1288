import numpy as np
import os
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
        self.window.title("Frame Averaging and Signal Mean")
        # self.window.config(background='#FFFFFF')
        self.window.geometry(f"{fw+350}x{int(2*fh/3)+100}")
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
        self.variance_ij = np.array([], dtype=np.float64)
        self.Average = 0

        self.Division_Column, self.Division_Row = IntVar(), IntVar()

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
        WH.UIConfiguration.set_text(self.Entry4_1, '1')
        WH.UIConfiguration.set_text(self.Entry4_2, f"{int(len(self.InputData))}")
        WH.UIConfiguration.set_text(self.Entry5_1_1, '0')
        WH.UIConfiguration.set_text(self.Entry5_1_2, f"{int(self.InputData.shape[2]) - 1}")
        WH.UIConfiguration.set_text(self.Entry5_2_1, '0')
        WH.UIConfiguration.set_text(self.Entry5_2_2, f'{int(self.InputData.shape[1]) - 1}')


    def Dark_Image(self):

        Image_Size = [int(self.ImageSize_Row.get()), int(self.ImageSize_Col.get())]

        fpath = WH.ButtonClickedEvent.Open_Path(self.filepath)
        self.Label3.configure(text=f"{fpath[-40:]}")

        self.dark_data = WH.ButtonClickedEvent.Read_Folder(fpath, self.filepath[-3:], np.uint16, Image_Size)
        self.InputData = self.InputData - self.dark_data
        self.frame_average = HF.DataProcessing.TemporalAverage(self.InputData)
        WH.Plotting.ShowImage(self.frame_average, self.ImageWidget)

    def Show_ROI(self, Frame):

        FOI = np.array([int(self.FOI_Start.get()), int(self.FOI_End.get())])
        ROI1 = np.array([int(self.ROI_Left.get()), int(self.ROI_Dn.get())])
        ROI2 = np.array([int(self.ROI_Right.get()), int(self.ROI_Up.get())])

        Frame = HF.DataProcessing.TemporalAverage(WH.ButtonClickedEvent.Set_FOI(Frame, FOI))
        self.ROI_Data = WH.ButtonClickedEvent.Set_ROI(Frame, ROI1, ROI2)

        if not hasattr(self, 'ROIWidget'):
            self.ROIWidget = WH.Plotting.MakeFigureWidget(self.ROIPlotFrame, fs)

        WH.Plotting.ShowImage(Frame, self.ImageWidget)
        WH.Plotting.ShowImage(self.ROI_Data, self.ROIWidget)

    def ShowBlock(self, ax, Frame, row, col):

        WH.Plotting.DrawDivision(ax, Frame, row, col)

    def Calculate(self, ax, Frame, row, col):

        self.Average = WH.ButtonClickedEvent.Average(ax, Frame, row, col)

        self.Label8_2_1.configure(text=f"{np.format_float_scientific(np.mean(Frame), unique=False, precision=2)}")
        self.Label8_2_2.configure(text=f"{np.format_float_scientific(np.std(Frame), unique=False, precision=2)}")
        self.Output = self.Average.copy()

    def SaveBTNEvent(self, data):

        WH.ButtonClickedEvent.Save_csv(self.filepath, data)

    def SaveClipboardBTNEvent(self, data):

        WH.ButtonClickedEvent.SaveClipboard(data)

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
                                                  command=lambda: WH.UIConfiguration.ButtonState(self.Button3, self.OffsetCalibration.get()))
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
                                      command=lambda: self.ShowBlock(self.ROIWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get())))
        self.Button7.grid(column=col, row=2, columnspan=Entry7Span)
        col = col + Entry7Span

        Entry8Span = 2
        self.Button8 = tkinter.Button(self.InputinfoFrame, text='Calculate',
                                      command=lambda: self.Calculate(self.ROIWidget, self.ROI_Data.copy(), int(self.Division_Row.get()), int(self.Division_Column.get())))
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

        Entry9Span = 1
        self.Button9 = tkinter.Button(self.InputinfoFrame, text='Save Image', command=lambda: self.SaveBTNEvent(self.Output))
        self.Button9.grid(column=col, row=2, columnspan=Entry8Span)
        self.Button9_2 = tkinter.Button(self.InputinfoFrame, text='Save Clipboard', command=lambda: self.SaveClipboardBTNEvent(self.Output))
        self.Button9_2.grid(column=col, row=3)
        col = col + Entry9Span

        # Entry10Span = 1
        # col = col + Entry10Span


if __name__ == '__main__':
    window = tkinter.Tk()
    DarkCurrentAnalysis(window)
    window.mainloop()