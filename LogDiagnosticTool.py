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
        self.topFrame.place(relx=0.5, relwidth=.98, relheight=0.15, anchor='n')
        
        self.button1 = tk.Button(self.topFrame, text='Get Entries', font=25, bg='#D3D3D3', command=findEntries)
        self.button1.place(relwidth=0.08, relheight=0.2)
        
        self.button2 = tk.Button(self.topFrame, text='Analyze', font=25, bg='#D3D3D3', command=analyze)
        self.button2.place(rely=0.25, relwidth=0.08, relheight=0.2)
        
        self.button3 = tk.Button(self.topFrame, text='Graphs', font=25, bg='#D3D3D3', command=graphs)
        self.button3.place(rely=0.50, relwidth=0.08, relheight=0.2)
        
        self.labelFiles = tk.Label(self.topFrame, text='Files:', font=12, anchor='w')
        self.labelFiles.place(relx=0.09, relwidth=0.04, relheight=0.25)

        # File List
        self.scrollFrame = tk.Frame(self.topFrame, bd=1, relief='solid')
        self.scrollFrame.place(relx=0.13, relwidth=0.6, relheight=0.92)
        
        # Info Dashboard
        self.infoFrame = tk.Frame(self.topFrame, bd=1, relief='solid')
        self.infoFrame.place(relx=0.74, relwidth=0.25, relheight=0.87)
    
        self.labelInfo1 = tk.Label(self.infoFrame, text='Number of Total Interlocks:', font=10, anchor='w')
        self.labelInfo1.place(relwidth=0.65, relheight=0.25)
    
        self.labelInfo2 = tk.Label(self.infoFrame, text='Number of Unexpected Interlocks:', font=10, anchor='w')
        self.labelInfo2.place(rely=0.4, relwidth=0.78, relheight=0.25)
        
        # ----- Bottom Frame -----
        self.bottomFrame = tk.Frame(master)
        self.bottomFrame.place(relx=0.5, rely=0.13, relwidth=1, relheight=0.85, anchor='n')
        
        # Left Side
        self.bottomLeft = tk.Frame(self.bottomFrame)
        self.bottomLeft.place(relwidth=0.6, relheight=1)
        
        self.tabControl1 = ttk.Notebook(self.bottomLeft)        
        
        self.tab1_left = ttk.Frame(self.tabControl1)
        self.tabControl1.add(self.tab1_left, text = 'KVCT Interlocks')
        
        self.tab2_left = ttk.Frame(self.tabControl1)
        self.tabControl1.add(self.tab2_left, text = 'KVCT Interlocks (Unexpected)')
        
        self.tab3_left = ttk.Frame(self.tabControl1)
        self.tabControl1.add(self.tab3_left, text = 'KVCT Interlocks (Expected)')
        
        self.tab4_left = ttk.Frame(self.tabControl1)
        self.tabControl1.add(self.tab4_left, text = 'PET Interlocks')
        
        self.tabControl1.pack(expan=1, fill='both')
        
        # Right Side 
        self.bottomRight = tk.Frame(self.bottomFrame)
        self.bottomRight.place(relx=0.6, relwidth=0.4, relheight=1)
        
        self.tabControl2 = ttk.Notebook(self.bottomRight)        
        
        self.tab1_right = ttk.Frame(self.tabControl2)
        self.tabControl2.add(self.tab1_right, text = 'KVCT Analysis (Unexpected)')
        
        self.tab2_right = ttk.Frame(self.tabControl2)
        self.tabControl2.add(self.tab2_right, text = 'KVCT Analysis (Expected)')
        
        self.tab3_right = ttk.Frame(self.tabControl2)
        self.tabControl2.add(self.tab3_right, text = 'PET Analysis')
        
        self.tabControl2.pack(expan=1, fill='both')

def addFiles():
    global files
    
    root.update()
    files = filedialog.askopenfilenames(parent=app.topFrame,title='Choose files', defaultextension='.log')
    [listbox.insert(tk.END, item) for item in files]

    
def findEntries():
    global kvct_df, pet_df, kvct_filtered, kvct_filtered_out 

    # Find all interlocks
    try:
        kvct_df, pet_df = DiagnosticTool.GetEntries(files)
        table1 = Table(app.tab1_left, dataframe=kvct_df, fontsize=5, rowheight=20) #displays all interlocks
        table1.show()
        table2 = Table(app.tab2_left, dataframe=pet_df, fontsize=5, rowheight=20)
        table2.show()
    except:
        messagebox.showerror("Error", "Cannot find entries for listed files.")
        pass
    # Filter interlocks
    try:
        kvct_filtered, kvct_filtered_out = DiagnosticTool.FilterEntries(kvct_df)
        table3 = Table(app.tab3_left, dataframe=kvct_filtered, fontsize=5, rowheight=20) #displays filtered interlocks
        table3.show()
        table4 = Table(app.tab4_left, dataframe=kvct_filtered_out, fontsize=5, rowheight=20) # displays expected interlock (interlocks that were filtered out)
        table4.show()
    except:
        messagebox.showerror("Error", "Cannot filter interlocks.")
        pass
    
    labelInfo3.config(text=len(kvct_df), font=14) 
    labelInfo4.config(text=len(kvct_filtered), font=14)

def analyze():
    global filtered_analysis, unfiltered_analysis, unfilter_analysis_export, plotting_data, pet_analysis
    
    try:
        filtered_analysis, unfiltered_analysis, plotting_data, pet_analysis = DiagnosticTool.Analysis(kvct_filtered, kvct_filtered_out, pet_df)
        
        table5 = Table(app.tab1_right, dataframe=filtered_analysis, fontsize=5, rowheight=20) #display unexpected interlock analysis
        table5.show()
        
        unfilter_analysis_export = unfiltered_analysis.set_index(['Session', 'Type'])
        table6 = Table(app.tab2_right, dataframe=unfiltered_analysis, fontsize=5, rowheight=20) #display unexpected interlock analysis
        table6.show()
        
        table7 = Table(app.tab3_right, dataframe=pet_analysis, fontsize=5, rowheight=20)
        table7.show()

    except:
        messagebox.showerror("Error", "Cannot analyze filtered interlocks.")
        pass
    
def graphs():
    plotting_data.plot(kind='bar', figsize=(8,5))
    plt.show()
    
def exportExcel():  
    export_filepath = filedialog.askdirectory()
    
    kvct_excel_writer = pd.ExcelWriter(export_filepath + '\KVCT Interlocks.xlsx', engine='xlsxwriter')
    kvct_df.to_excel(kvct_excel_writer, sheet_name='All Interlocks')
    kvct_filtered.to_excel(kvct_excel_writer, sheet_name='Unexpected Interlocks')
    kvct_filtered_out.to_excel(kvct_excel_writer, sheet_name='Expected Interlocks')
    filtered_analysis.to_excel(kvct_excel_writer, sheet_name='Unexpected Interlock Analysis')
    unfilter_analysis_export.to_excel(kvct_excel_writer, sheet_name='Expected Interlock Analysis')
    kvct_excel_writer.save()
    
    pet_excel_writer = pd.ExcelWriter(export_filepath + '\PET Interlocks.xlsx', engine='xlsxwriter')
    pet_df.to_excel(pet_excel_writer, sheet_name='Interlocks')
    pet_analysis.to_excel(pet_excel_writer, sheet_name='Analysis')
    pet_excel_writer.save()
    
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

root.mainloop()
