# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 15:24:57 2020

@author: btierra
"""
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
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
        
        self.labelFiles = tk.Label(self.topFrame, text='Files:', font=5, anchor='w')
        self.labelFiles.place(relx=0.09, rely=0.02, relwidth=0.04, relheight=0.1)

        # File List
        self.scrollFrame = tk.Frame(self.topFrame, bd=1, relief='solid')
        self.scrollFrame.place(relx=0.13, relwidth=0.5, relheight=0.92)
        
        # Info Dashboard
        self.infoFrame = tk.Frame(self.topFrame, bd=1, relief='solid')
        self.infoFrame.place(relx=0.64, relwidth=0.35, relheight=0.87)
    
        self.labelInfo1 = tk.Label(self.infoFrame, text='System: ', font=10, anchor='w')
        self.labelInfo1.place(rely=0.02, relwidth=0.2, relheight=0.15)
    
        self.labelInfo2 = tk.Label(self.infoFrame, text='Log Dates:', font=10, anchor='w')
        self.labelInfo2.place(rely=0.22, relwidth=0.35, relheight=0.15)
        
        self.labelInfo3 = tk.Label(self.infoFrame, text='Total Sessions:', font=10, anchor='w')
        self.labelInfo3.place(rely=0.42, relwidth=0.35, relheight=0.15)
        
        self.labelInfo4 = tk.Label(self.infoFrame, text='Total KVCT Interlocks:', font=10, anchor='w')
        self.labelInfo4.place(rely=0.62, relwidth=.35, relheight=0.15)
        
        self.labelInfo5 = tk.Label(self.infoFrame, text='Total PET Interlocks:', font=10, anchor='w')
        self.labelInfo5.place(rely=0.82, relwidth=.35, relheight=0.15)
        
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
    
def clicked():
    content = filedialog.askopenfilenames(title='Choose files', defaultextension='.log')
    [listbox.insert(tk.END, item) for item in content]
 
def delete():
	listbox.delete(0, tk.END)
 
def delete_selected():
	listbox.delete(tk.ANCHOR)
    
def findEntries():
    global files, kvct_df, pet_df, kvct_filtered, kvct_filtered_out, system, dates
    files = list(listbox.get(0,tk.END))
    # Find all interlocks
    try:
        system, kvct_df, pet_df = DiagnosticTool.GetEntries(files)
        table1 = Table(app.tab1_left, dataframe=kvct_df, fontsize=5, rowheight=20) #displays all interlocks
        table1.show()
        table2 = Table(app.tab4_left, dataframe=pet_df, fontsize=5, rowheight=20)
        table2.show()
        
        # Show which system files came from
        if system == 'SN-unknown':
            system = 'B1'
        labelInfo6.config(text=system, font=12)
        
        # Show dates analyzed
        start_date = kvct_df['Date'][0]
        end_date = kvct_df['Date'][len(kvct_df)-1]
        dates = str(start_date)+' - '+str(end_date)
        labelInfo7.config(text=dates, font=12)
        
        # Show number of interlocks for kvct and pet_recon nodes
        labelInfo9.config(text=len(kvct_df), font=12) 
        labelInfo10.config(text=len(pet_df), font=12)
    except:
        messagebox.showerror("Error", "Cannot find entries for listed files.")
        pass
    # Filter interlocks
    try:
        kvct_filtered, kvct_filtered_out = DiagnosticTool.FilterEntries(kvct_df)
        table3 = Table(app.tab2_left, dataframe=kvct_filtered, fontsize=5, rowheight=20) #displays filtered interlocks
        table3.show()
        table4 = Table(app.tab3_left, dataframe=kvct_filtered_out, fontsize=5, rowheight=20) # displays expected interlock (interlocks that were filtered out)
        table4.show()
    except:
        messagebox.showerror("Error", "Cannot filter interlocks.")
        pass

def analyze():
    global filtered_analysis, unfiltered_analysis, unfilter_analysis_export, pet_analysis, sessions

    try: 
        filtered_analysis, sessions, unfiltered_analysis, pet_analysis = DiagnosticTool.Analysis(kvct_filtered, kvct_filtered_out, pet_df)
        
        table5 = Table(app.tab1_right, dataframe=filtered_analysis, fontsize=5, rowheight=20) #display unexpected interlock analysis
        table5.show()
        
        table6 = Table(app.tab2_right, dataframe=unfiltered_analysis, fontsize=5, rowheight=20) #display expected interlock analysis
        table6.show()
        
        table7 = Table(app.tab3_right, dataframe=pet_analysis, fontsize=5, rowheight=20)
        table7.show()
        
        labelInfo8.config(text=str(sessions), font=12)

    except:
        messagebox.showerror("Error", "Cannot analyze filtered interlocks.")
        pass
    
def exportExcel():  
    export_filepath = filedialog.askdirectory()
    
    # Summary Table
    info = ['System', 'Dates', 'Total Sessions', 'KVCT Total Interlocks', 'KVCT Unexpected Interlocks', 'KVCT Expected Interlocks', 'PET Interlocks']
    values = [system, dates, sessions, len(kvct_df), len(kvct_filtered), len(kvct_filtered_out), len(pet_df)]
    summary_df = pd.DataFrame([info, values]).transpose()
    
    # Interlocks Excel File
    interlocks_writer = pd.ExcelWriter(export_filepath + '\InterlocksList.xlsx', engine='xlsxwriter')
    kvct_df.to_excel(interlocks_writer, sheet_name='KVCT Interlocks (All)')
    kvct_filtered.to_excel(interlocks_writer, sheet_name='KVCT Interlocks (Unexpect)')
    kvct_filtered_out.to_excel(interlocks_writer, sheet_name='KVCT Interlocks (Expected)')
    pet_df.to_excel(interlocks_writer, sheet_name='PET Interlocks')
    interlocks_writer.save()
    
    # Analysis Excel File
    analysis_writer = pd.ExcelWriter(export_filepath + '\InterlocksAnalysis.xlsx', engine='xlsxwriter')
    summary_df.to_excel(analysis_writer, sheet_name='Summary')
    filtered_analysis.to_excel(analysis_writer, sheet_name='KVCT Analysis (Unexpect)')
    unfiltered_analysis.to_excel(analysis_writer, sheet_name='KVCT Analysis (Expect)')
    pet_analysis.to_excel(analysis_writer, sheet_name='PET Analysis')
    analysis_writer.save()
    
root = tk.Tk()
app = LogDiagnosticToolTempalte(root)

# ----- Top Frame ------
# Menu Bar
menubar = tk.Menu(app.topFrame)

file = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label='File', menu = file)
file.add_command(label='Save Results', command = exportExcel)

root.config(menu=menubar)

# List chosen files
scrollbar_x = tk.Scrollbar(app.scrollFrame, orient='horizontal')
scrollbar_x.pack(side='bottom', fill='x')

scrollbar_y = tk.Scrollbar(app.scrollFrame)
scrollbar_y.pack(side='right', fill='y')

button_add = tk.Button(app.topFrame, text='Add Files', command=clicked)
button_add.place(relx=0.09, rely=0.15, relwidth=0.04, relheight=0.1)

button_delete = tk.Button(app.topFrame, text='Delete All', command=delete)
button_delete.place(relx=0.09, rely=0.3, relwidth=0.04, relheight=0.1)

button_delete_select = tk.Button(app.topFrame, text='Delete Selected', command=delete_selected)
button_delete_select.place(relx=0.09, rely=0.45, relwidth=0.04, relheight=0.1)

listbox= tk.Listbox(app.scrollFrame, height = 500, width = 350, xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_y.set)
listbox.pack(expand=0, fill='both')
scrollbar_x.config(command=listbox.xview)
scrollbar_y.config(command=listbox.yview)

# Summary of tables
labelInfo6 = tk.Label(app.infoFrame, anchor='w')
labelInfo6.place(relx=0.15, relwidth=0.5, relheight=0.2)

labelInfo7 = tk.Label(app.infoFrame, anchor='w')
labelInfo7.place(relx=0.2, rely=0.20, relwidth=0.5, relheight=0.2)

labelInfo8 = tk.Label(app.infoFrame, anchor='w')
labelInfo8.place(relx=0.25, rely=0.40, relwidth=0.5, relheight=0.2)

labelInfo9 = tk.Label(app.infoFrame, anchor='w')
labelInfo9.place(relx=0.35, rely=0.60, relwidth=0.5, relheight=0.2)

labelInfo10 = tk.Label(app.infoFrame, anchor='w')
labelInfo10.place(relx=0.35, rely=0.80, relwidth=0.5, relheight=0.2)

root.mainloop()
