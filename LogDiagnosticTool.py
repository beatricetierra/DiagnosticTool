# -*- coding: utf-8 -*-
"""
Created on Fri May  8 10:43:42 2020

@author: btierra
"""
import tkinter as tk
from tkinter import filedialog, ttk
from pandastable import Table
import GetEntries as get

class LogDiagnosticToolTempalte():
    
    def __init__(self, master):
        self.canvas = tk.Canvas(master, height=800, width=1400)
        self.canvas.pack()
        
        # ***Top Frame***
        self.topFrame = tk.Frame(master)
        self.topFrame.place(relx=0.5, rely=0.02, relwidth=0.95, relheight=0.12, anchor='n')
        
        self.button1 = tk.Button(self.topFrame, text='Choose Files', font=30, bg='#D3D3D3', command=addFiles)
        self.button1.place(relx=0.01, rely=0.03, relwidth=0.15, relheight=0.2)
        
        self.button2 = tk.Button(self.topFrame, text='Get Entries', font=30, bg='#D3D3D3', command=findEntries)
        self.button2.place(relx=0.01, rely=0.25, relwidth=0.15, relheight=0.2)
        
        self.labelFiles = tk.Label(self.topFrame, text='Files:', font=12, anchor='w')
        self.labelFiles.place(relx=0.18, rely=0.01, relwidth=0.05, relheight=0.25)
        
        # Info Dashboard
        self.infoFrame = tk.Frame(self.topFrame, bd=1, relief='solid')
        self.infoFrame.place(relx=0.18, rely=0.3, relwidth=0.82, relheight=0.62)
        
        self.labelInfo1 = tk.Label(self.infoFrame, text='Number of Total Interlocks:', font=12, anchor='w')
        self.labelInfo1.place(relwidth=0.3, relheight=0.25)
        
        self.labelInfo2 = tk.Label(self.infoFrame, text='Number of Unexpected Interlocks:', font=12, anchor='w')
        self.labelInfo2.place(rely=0.4, relwidth=0.3, relheight=0.25)
        
        # ***Bottom Frame***
        self.bottomFrame = tk.Frame(master)
        self.bottomFrame.place(relx=0.5, rely=0.13, relwidth=1, relheight=0.87, anchor='n')
        
        self.tabControl = ttk.Notebook(self.bottomFrame)        
        
        self.tab1 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab1, text = 'Interlocks')
        
        self.tab2 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab2, text = 'Interlocks (Filtered)')
        
        self.tab3 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab3, text = 'Analysis')
        
        self.tabControl.pack(expan=1, fill='both')
        
def addFiles():
    global files
    
    root.update()
    files = filedialog.askopenfilenames(parent=app.topFrame,title='Choose files', defaultextension='.log')
    labelLog.config(text=files)
    
def findEntries():
    statusbar.config(text='Loading...')

    kvct_df, kvct_filtered, kvct_analysis = get.Diagnostic(files)
    
    table1 = Table(app.tab1, dataframe=kvct_df) #displays interlocks
    table1.show()
    
    table2 = Table(app.tab2, dataframe=kvct_filtered) #displays filtered interlocks
    table2.show()
    
    table3 = Table(app.tab3, dataframe=kvct_analysis) #displays filtered interlocks
    table3.show()
    
    statusbar.config(text='Done')
    
    labelInfo3.config(text=len(kvct_df), font=14) 
    labelInfo4.config(text=len(kvct_filtered), font=14)
    
root = tk.Tk()
app = LogDiagnosticToolTempalte(root)

# Top Frame
labelLog = tk.Label(app.topFrame, anchor='w', bg='#D0D3D4', relief='sunken')
labelLog.place(relx=0.22, rely=0.03, relwidth=0.8, relheight=0.2)

labelInfo3 = tk.Label(app.infoFrame, anchor='w')
labelInfo3.place(relx=0.18, relwidth=0.1, relheight=0.25)

labelInfo4 = tk.Label(app.infoFrame, anchor='w')
labelInfo4.place(relx=0.22, rely=0.4, relwidth=0.1, relheight=0.25)

# Bottom Frame
statusbar = tk.Label(app.bottomFrame, bd=1, relief='sunken', anchor='w')
statusbar.pack(side='bottom', fill='x')

root.mainloop()






