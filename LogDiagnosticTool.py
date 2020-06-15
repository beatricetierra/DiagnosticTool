# -*- coding: utf-8 -*-
"""
Created on Fri May  8 10:43:42 2020

@author: btierra
"""
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import matplotlib.pyplot as plt
import pandas as pd
from pandastable import Table
import DiagnosticTool

class LogDiagnosticToolTempalte():
    
    def __init__(self, master):
        self.canvas = tk.Canvas(master, height=800, width=1400)
        self.canvas.pack()
        
        # ----- Top Frame -----
        self.topFrame = tk.Frame(master)
        self.topFrame.place(relx=0.5, relwidth=.98, relheight=0.12, anchor='n')
        
        self.button1 = tk.Button(self.topFrame, text='Get Entries', font=25, bg='#D3D3D3', command=findEntries)
        self.button1.place(relwidth=0.1, relheight=0.2)
        
        self.button2 = tk.Button(self.topFrame, text='Graphs', font=25, bg='#D3D3D3', command=graphs)
        self.button2.place(rely=0.22, relwidth=0.1, relheight=0.2)
        
        self.labelFiles = tk.Label(self.topFrame, text='Files:', font=12, anchor='w')
        self.labelFiles.place(relx=0.12, relwidth=0.04, relheight=0.25)

        # File List
        self.scrollFrame = tk.Frame(self.topFrame, bd=1, relief='solid')
        self.scrollFrame.place(relx=0.16, relwidth=0.6, relheight=0.92)
        
        # Info Dashboard
        self.infoFrame = tk.Frame(self.topFrame, bd=1, relief='solid')
        self.infoFrame.place(relx=0.77, rely=0.01, relwidth=0.22, relheight=0.82)
    
        self.labelInfo1 = tk.Label(self.infoFrame, text='Number of Total Interlocks:', font=10, anchor='w')
        self.labelInfo1.place(relwidth=0.65, relheight=0.25)
    
        self.labelInfo2 = tk.Label(self.infoFrame, text='Number of Unexpected Interlocks:', font=10, anchor='w')
        self.labelInfo2.place(rely=0.4, relwidth=0.78, relheight=0.25)
        
        # ----- Bottom Frame -----
        self.bottomFrame = tk.Frame(master)
        self.bottomFrame.place(relx=0.5, rely=0.13, relwidth=1, relheight=0.87, anchor='n')
        
        self.tabControl = ttk.Notebook(self.bottomFrame)        
        
        self.tab1 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab1, text = 'All Interlocks')
        
        self.tab2 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab2, text = 'Unexpected Interlocks')
        
        self.tab3 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab3, text = 'Expected Interlocks')
        
        self.tab4 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab4, text = 'Unexpected Interlock Analysis')
        
        self.tab5 = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab5, text = 'Expected Interlock Analysis')
        
        self.tabControl.pack(expan=1, fill='both')
        
def addFiles():
    global files
    
    root.update()
    files = filedialog.askopenfilenames(parent=app.topFrame,title='Choose files', defaultextension='.log')
    [listbox.insert(tk.END, item) for item in files]

    
def findEntries():
    global kvct_df, kvct_filtered, filtered_out, filtered_analysis, unfiltered_analysis, unfilter_analysis_export, plotting_data
    
    statusbar.config(text='Loading...')
    
    # Find all interlocks
    try:
        kvct_df = DiagnosticTool.GetEntries(files)
        table1 = Table(app.tab1, dataframe=kvct_df) #displays all interlocks
        table1.show()
    except:
        messagebox.showerror("Error", "Cannot find entries for listed files.")
        pass
    # Filter interlocks
    try:
        kvct_filtered, filtered_out = DiagnosticTool.FilterEntries(kvct_df)
        table2 = Table(app.tab2, dataframe=kvct_filtered) #displays filtered interlocks
        table2.show()
        table3 = Table(app.tab3, dataframe=filtered_out) # displays expected interlock (interlocks that were filtered out)
        table3.show()
    except:
        messagebox.showerror("Error", "Cannot filter interlocks.")
        pass
    # Interlock Analysis
    try:
        filtered_analysis, unfiltered_analysis, plotting_data = DiagnosticTool.Analysis(kvct_filtered, filtered_out)
        table4 = Table(app.tab4, dataframe=filtered_analysis) #display unexpected interlock analysis
        table4.show()
        
        unfilter_analysis_export = unfiltered_analysis.set_index(['Session', 'Type'])
        table5 = Table(app.tab5, dataframe=unfiltered_analysis) #display unexpected interlock analysis
        table5.show()

    except:
        messagebox.showerror("Error", "Cannot analyze filtered interlocks.")
        pass
        
    statusbar.config(text='Done')
    
    labelInfo3.config(text=len(kvct_df), font=14) 
    labelInfo4.config(text=len(kvct_filtered), font=14)
    
def graphs():
    plotting_data.plot(kind='bar', figsize=(8,5))
    plt.show()
    
def exportExcel():  
    export_filepath = filedialog.asksaveasfilename(defaultextension='.xlsx')
    excel_writer = pd.ExcelWriter(export_filepath, engine='xlsxwriter')
    kvct_df.to_excel(excel_writer, sheet_name='All Interlocks')
    kvct_filtered.to_excel(excel_writer, sheet_name='Unexpected Interlocks')
    filtered_out.to_excel(excel_writer, sheet_name='Expected Interlocks')
    filtered_analysis.to_excel(excel_writer, sheet_name='Unexpected Interlock Analysis')
    unfilter_analysis_export.to_excel(excel_writer, sheet_name='Expected Interlock Analysis')
    excel_writer.save()
    
root = tk.Tk()
app = LogDiagnosticToolTempalte(root)

# ----- Top Frame ------
# Menu Bar
menubar = tk.Menu(app.topFrame)

file = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label='File', menu = file)
file.add_command(label='Choose Files', command=addFiles)
file.add_command(label='Save Results', command = exportExcel)

root.config(menu=menubar)

# List chosen files
scrollbar_x = tk.Scrollbar(app.scrollFrame, orient='horizontal')
scrollbar_x.pack(side='bottom', fill='x')

scrollbar_y = tk.Scrollbar(app.scrollFrame)
scrollbar_y.pack(side='right', fill='y')

listbox= tk.Listbox(app.scrollFrame, height = 500, width = 350, xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_y.set)
listbox.pack(expand=0, fill='both')
scrollbar_x.config(command=listbox.xview)
scrollbar_y.config(command=listbox.yview)

# Summary of tables
labelInfo3 = tk.Label(app.infoFrame, anchor='w')
labelInfo3.place(relx=0.66, relwidth=0.1, relheight=0.25)

labelInfo4 = tk.Label(app.infoFrame, anchor='w')
labelInfo4.place(relx=0.8, rely=0.4, relwidth=0.1, relheight=0.25)

# ----- Bottom Frame ------
statusbar = tk.Label(app.bottomFrame, bd=1, relief='sunken', anchor='w')
statusbar.pack(side='bottom', fill='x')

root.mainloop()
