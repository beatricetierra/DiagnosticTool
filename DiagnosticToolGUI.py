 # -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 15:24:57 2020

@author: btierra
"""
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import pandas as pd
import DiagnosticTool

class Page(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
    def show(self):
        self.lift()

class Page1(Page):
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)

       # Top Frame
       topFrame = tk.Frame(self)
       topFrame.place(relx=0.5, relwidth=0.9, relheight=0.30, anchor='n')
       
       folderLabel = tk.Label(topFrame, text="Choose Folder (optional: finds all log files under all subdirectories of given folders)", font=20)
       folderLabel.place(relx=0.08,relheight=0.1)
       
       scrollFrame1 = tk.Frame(topFrame, bd=1, relief='solid')
       scrollFrame1.place(relx=0.08,rely=0.08, relwidth=0.7, relheight=0.9)
       
       scrollbar_x1 = tk.Scrollbar(scrollFrame1, orient='horizontal')
       scrollbar_x1.pack(side='bottom', fill='x')
          
       scrollbar_y1 = tk.Scrollbar(scrollFrame1)
       scrollbar_y1.pack(side='right', fill='y')
          
       self.listbox1= tk.Listbox(scrollFrame1, height = 500, width = 350, xscrollcommand=scrollbar_x1.set, yscrollcommand=scrollbar_y1.set)
       self.listbox1.pack(expand=0, fill='both')
       scrollbar_x1.config(command=self.listbox1.xview)
       scrollbar_y1.config(command=self.listbox1.yview)
          
       # Buttons for List of Folders
       button_find1 = tk.Button(topFrame, text='Find Files', font=30, command=self.findFiles)
       button_find1.place(relx=0.8, rely=0.85, relwidth=0.1, relheight=0.08)
          
       button_add1 = tk.Button(topFrame, text='Add', font=20, command=self.addFolder)
       button_add1.place(relx=0.8, rely=0.1, relwidth=0.1, relheight=0.08)
          
       button_delete_select1 = tk.Button(topFrame, text='Delete', font=20, command=self.deleteFolder_selected)
       button_delete_select1.place(relx=0.8, rely=0.18, relwidth=0.1, relheight=0.08)
       
       # Bottom Frame
       bottomFrame = tk.Frame(self)
       bottomFrame.place(relx=0.5, rely=0.3, relwidth=0.9, relheight=0.65, anchor='n')
       
       folderLabel = tk.Label(bottomFrame, text="Choose Files", font=20)
       folderLabel.place(relx=0.08,relheight=0.1)
       
       scrollFrame2 = tk.Frame(bottomFrame, bd=1, relief='solid')
       scrollFrame2.place(relx=0.08, rely=0.08, relwidth=0.7, relheight=0.92)
       
       scrollbar_x2 = tk.Scrollbar(scrollFrame2, orient='horizontal')
       scrollbar_x2.pack(side='bottom', fill='x')
          
       scrollbar_y2 = tk.Scrollbar(scrollFrame2)
       scrollbar_y2.pack(side='right', fill='y')
          
       self.listbox2= tk.Listbox(scrollFrame2, height = 500, width = 350, xscrollcommand=scrollbar_x2.set, yscrollcommand=scrollbar_y2.set)
       self.listbox2.pack(expand=0, fill='both')
       scrollbar_x2.config(command=self.listbox2.xview)
       scrollbar_y2.config(command=self.listbox2.yview)
       
       # Buttons for List of Files
       button_find2 = tk.Button(bottomFrame, text='Find Interlocks', font=15, command=self.findInterlocks)
       button_find2.place(relx=0.8, rely=0.9, relwidth=0.1, relheight=0.06)
          
       button_add2 = tk.Button(bottomFrame, text='Add', font=15, command=self.addFile)
       button_add2.place(relx=0.8, rely=0.1, relwidth=0.1, relheight=0.05)
       
       button_delete_select2 = tk.Button(bottomFrame, text='Delete', font=15, command=self.deleteFile_selected)
       button_delete_select2.place(relx=0.8, rely=0.15, relwidth=0.1, relheight=0.05)
          
       button_delete2 = tk.Button(bottomFrame, text='Delete All', font=15, command=self.deleteFile)
       button_delete2.place(relx=0.8, rely=0.2, relwidth=0.1, relheight=0.05)

   def addFolder(self):
       folderlist = []
       folder = filedialog.askdirectory()
       folderlist.append(folder)
       [self.listbox1.insert(tk.END, item) for item in folderlist]
     
   def deleteFolder_selected(self):
       self.listbox1.delete(tk.ANCHOR)
       
   def findFiles(self):
       folders = list(self.listbox1.get(0,tk.END))
       all_files = []
       for folder in folders:
           files = DiagnosticTool.GetFiles(folder)
           for file in files:
               all_files.append(file)
       [self.listbox2.insert(tk.END, file) for file in all_files]
      
   def addFile(self):
       content = filedialog.askopenfilenames(title='Choose files', filetypes=[('Text Document', '*.log')])
       [self.listbox2.insert(tk.END, item) for item in content]
       
   def deleteFile(self):
       self.listbox2.delete(0, tk.END)
     
   def deleteFile_selected(self):
       self.listbox2.delete(tk.ANCHOR)
       
   def findInterlocks(self):
       global files
       files = list(self.listbox2.get(0,tk.END))
       SubFunctions.findEntries(files)

class Page2(Page):
    def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       Page2.tabControl = ttk.Notebook(self)        
        
       Page2.tab1 = ttk.Frame(Page2.tabControl)
       Page2.tabControl.add(Page2.tab1, text = 'KVCT Interlocks')
        
       Page2.tab2 = ttk.Frame(Page2.tabControl)
       Page2.tabControl.add(Page2.tab2, text = 'KVCT Interlocks (Unexpected)')
        
       Page2.tab3 = ttk.Frame(Page2.tabControl)
       Page2.tabControl.add(Page2.tab3, text = 'KVCT Interlocks (Expected)')
        
       Page2.tab4 = ttk.Frame(Page2.tabControl)
       Page2.tabControl.add(Page2.tab4, text = 'PET Interlocks')

       Page2.tabControl.pack(expan=1, fill='both')
       
       # Add filtering menubars
       # kvct dataframes
       Page2.menubar1 = tk.Menubutton(self, text='Filter KVCT Interlocks \u25BE', font=20, relief='raised')
       Page2.menubar1.place(relx=0.5, relheight=0.025)
       # pet dataframes
       Page2.menubar2 = tk.Menubutton(self, text='Filter PET Interlocks \u25BE', font=20, relief='raised')
       Page2.menubar2.place(relx=0.63, relheight=0.025)
       
       button_filter = tk.Button(self, text="Filter", font=20, command = Page2.filter_by_interlock)
       button_filter.place(relx=0.89, relheight=0.025)
       
       button_selectall = tk.Button(self, text="Select All", font=20, command=Page2.selectall)
       button_selectall.place(relx=0.76, relheight=0.025)
       
       button_selectnone = tk.Button(self, text="Show None", font=20, command=Page2.selectnone)
       button_selectnone.place(relx=0.82, relheight=0.025)
       
    def menubar_filter(df, menubar):
        global interlock_set 
        items = sorted(list(set(df['Interlock Number'])))
        
        menubar.menu = tk.Menu(menubar, tearoff=0)
        menubar["menu"] = menubar.menu
        
        interlock_set = {}
        for idx, item in enumerate(items):
            var = tk.BooleanVar()
            var.set(True)
            menubar.menu.add_checkbutton(label=item, variable=var)
            interlock_set[str(item)] = var
       
    def filter_by_interlock():
        interlock_list = []
        for interlock, var in interlock_set.items():
            if var.get() == True:
                interlock_list.append(interlock)
                
        df = kvct_df[kvct_df['Interlock Number'].isin(interlock_list)]
        [widget.destroy() for widget in Page2.tab1.winfo_children()]
        SubFunctions.df_tree(df, Page2.tab1)
    
    def selectall():
        for interlock, var in interlock_set.items():
            var.set(True)
        Page2.filter_by_interlock()
    def selectnone():
        for interlock, var in interlock_set.items():
            var.set(False)
        Page2.filter_by_interlock()
            
class Page3(Page):
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)        
       Page3.tabControl = ttk.Notebook(self)        
       
       Page3.tab1 = ttk.Frame(Page3.tabControl)
       Page3.tabControl.add(Page3.tab1, text = 'KVCT Analysis (Unexpected)')
       
       Page3.tab2 = ttk.Frame(Page3.tabControl)
       Page3.tabControl.add(Page3.tab2, text = 'KVCT Analysis (Expected)')
       
       Page3.tab3 = ttk.Frame(Page3.tabControl)
       Page3.tabControl.add(Page3.tab3, text = 'PET Analysis')
       
       Page3.tabControl.pack(expan=1, fill='both')

class MainView(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        
        # Menu Bar
        menubar = tk.Menu(self)
        file = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='File', menu = file)
        file.add_command(label='Save Results', command = SubFunctions.exportExcel)
        root.config(menu=menubar)
        
        # Navigate between pages
        p1 = Page1(self)
        p2 = Page2(self)
        p3 = Page3(self)

        buttonframe = tk.Frame(self)
        container = tk.Frame(self)
        buttonframe.pack(side="top", fill="x", expand=False)
        container.pack(side="top", fill="both", expand=True)

        p1.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p2.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p3.place(in_=container, x=0, y=0, relwidth=1, relheight=1)

        b1 = tk.Button(buttonframe, text="Choose Files", command=p1.lift)
        b2 = tk.Button(buttonframe, text="Interlocks List", command=p2.lift)
        b3 = tk.Button(buttonframe, text="Analysis", command=p3.lift)

        b1.pack(side="left")
        b2.pack(side="left")
        b3.pack(side="left")

        p1.show()

class SubFunctions():
    def findEntries(files):
       global kvct_df, pet_df, kvct_filtered, kvct_filtered_out, system, dates
       global filtered_analysis, sessions, unfiltered_analysis, pet_analysis
       
       # Find all interlocks
       try:
           system, kvct_df, pet_df = DiagnosticTool.GetEntries(files)
           SubFunctions.df_tree(kvct_df, Page2.tab1)
           SubFunctions.df_tree(pet_df, Page2.tab4)
           Page2.menubar_filter(kvct_df, Page2.menubar1)
           #Page2.menubar_filter(pet_df, Page2.menubar2)
           
           # Get dates
           start_date = kvct_df['Date'][0]
           end_date = kvct_df['Date'][len(kvct_df)-1]
           dates = str(start_date)+' - '+str(end_date)
       except:
           messagebox.showerror("Error", "Cannot find entries for listed files.")
           pass
       
       # Filter interlocks
       try:
           kvct_filtered, kvct_filtered_out = DiagnosticTool.FilterEntries(kvct_df)
           SubFunctions.df_tree(kvct_filtered, Page2.tab2)
           SubFunctions.df_tree(kvct_filtered_out, Page2.tab3)
       except:
           messagebox.showerror("Error", "Cannot filter interlocks.")
           pass
       
       # Analyze interlocks 
       try:
           filtered_analysis, sessions, unfiltered_analysis, pet_analysis = DiagnosticTool.Analysis(kvct_filtered, kvct_filtered_out, pet_df)
           SubFunctions.df_tree(filtered_analysis, Page3.tab1)
           SubFunctions.df_tree(unfiltered_analysis, Page3.tab2)
           SubFunctions.df_tree(pet_analysis, Page3.tab3)

       except: 
           messagebox.showerror("Error", "Cannot analyze filtered interlocks.")
           pass
       
    def df_tree(df, tab):
       # Scrollbars
       treeScroll_y = ttk.Scrollbar(tab)
       treeScroll_y.pack(side='right', fill='y')
       treeScroll_x = ttk.Scrollbar(tab, orient='horizontal')
       treeScroll_x.pack(side='bottom', fill='x')
       
       columns = list(df.columns)
       tree = ttk.Treeview(tab)
       tree.pack(expand=1, fill='both')
       tree["columns"] = columns
       
       for i in columns:
           tree.column(i, anchor="w")
           tree.heading(i, text=i, anchor='w')
            
       for index, row in df.iterrows():
           tree.insert("",tk.END,text=index,values=list(row))
       
       treeScroll_y.configure(command=tree.yview)
       tree.configure(yscrollcommand=treeScroll_y.set)
       treeScroll_x.configure(command=tree.xview)
       tree.configure(xscrollcommand=treeScroll_x.set)
       
       tree.column("#0", width=50, stretch='no') 
       tree.column("Interlock Number", width=300, stretch='no')
       if 'page2' in str(tab):
           tree.column("Date", width=100, stretch='no')
           tree.column("Active Time", width=100, stretch='no')
           tree.column("Inactive Time", width=100, stretch='no')
           tree.column("Time from Node Start", width=100, stretch='no')
           tree.column("Interlock Duration", width=100, stretch='no')
           
       if 'page3' in str(tab):
           for i in range(1,len(columns)):
               tree.column(columns[i], width=60, stretch='no')

    def exportExcel():  
       directory = filedialog.askdirectory()
       
       try:
           # Dates to save file under new name each time
           start_date = ('').join(dates.split('-')[1:3])
           end_date = ('').join(dates.split('-')[4:])
           filedate = ('-').join([start_date, end_date]).replace(' ','')
                
            # Summary Table
           info = ['System', 'Dates', 'Total Sessions', 'KVCT Total Interlocks', 'KVCT Unexpected Interlocks', 'KVCT Expected Interlocks', 'PET Interlocks']
           values = [system, dates, sessions, len(kvct_df), len(kvct_filtered), len(kvct_filtered_out), len(pet_df)]
           summary_df = pd.DataFrame([info, values]).transpose()
           
           # Interlocks Excel File
           interlocks_writer = pd.ExcelWriter(directory + '\InterlocksList_' + system + '_' + filedate + '.xlsx', engine='xlsxwriter')
           kvct_df.to_excel(interlocks_writer, sheet_name='KVCT Interlocks (All)')
           kvct_filtered.to_excel(interlocks_writer, sheet_name='KVCT Interlocks (Unexpect)')
           kvct_filtered_out.to_excel(interlocks_writer, sheet_name='KVCT Interlocks (Expected)')
           pet_df.to_excel(interlocks_writer, sheet_name='PET Interlocks')
           interlocks_writer.save()
           
           # Analysis Excel File
           analysis_writer = pd.ExcelWriter(directory + '\InterlocksAnalysis_' + system + '_' + filedate + '.xlsx', engine='xlsxwriter')
           summary_df.to_excel(analysis_writer, sheet_name='Summary')
           filtered_analysis.to_excel(analysis_writer, sheet_name='KVCT Analysis (Unexpect)')
           unfiltered_analysis.to_excel(analysis_writer, sheet_name='KVCT Analysis (Expect)')
           pet_analysis.to_excel(analysis_writer, sheet_name='PET Analysis')
           analysis_writer.save()
           
           tk.messagebox.showinfo(title='Info', message='Excel files exported')
       except:
            tk.messagebox.showerror(title='Error', message='Cannot export files')
            
if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed')
    main = MainView(root)
    main.pack(side="top", fill="both", expand=True)
    root.wm_geometry("1500x800")
    root.mainloop()
