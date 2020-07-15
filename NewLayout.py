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
       
       # Saving Directory
       savingFrame = tk.Frame(self)
       savingFrame.place(relx=0.25, rely=0.15, relwidth=0.5, relheight=0.03)
       
       label1 = tk.Label(savingFrame, text='Directory:', font=20)
       label1.pack(side='left')
       button_save = tk.Button(savingFrame, text='Save Results', font=20, command=self.exportExcel)
       button_save.pack(side='right')
       
       self.entry_directory = tk.Entry(savingFrame)
       self.entry_directory.pack(fill='x')
       
       # List of Files
       scrollFrame = tk.Frame(self, bd=1, relief='solid')
       scrollFrame.place(relx=0.25, rely=0.2, relwidth=0.5, relheight=0.7)
       
       scrollbar_x = tk.Scrollbar(scrollFrame, orient='horizontal')
       scrollbar_x.pack(side='bottom', fill='x')
       
       scrollbar_y = tk.Scrollbar(scrollFrame)
       scrollbar_y.pack(side='right', fill='y')
       
       # Buttons
       button_find = tk.Button(self, text='Find Interlocks', font=20, command=self.findEntries)
       button_find.place(relx=0.1, rely=0.3, relwidth=0.1, relheight=0.1)
       
       button_add = tk.Button(self, text='Add Files', font=20, command=self.clicked)
       button_add.place(relx=0.8, rely=0.5, relwidth=0.1, relheight=0.1)
        
       button_delete = tk.Button(self, text='Delete All', font=20, command=self.delete)
       button_delete.place(relx=0.8, rely=0.6, relwidth=0.1, relheight=0.1)
        
       button_delete_select = tk.Button(self, text='Delete Selected', font=20, command=self.delete_selected)
       button_delete_select.place(relx=0.8, rely=0.7, relwidth=0.1, relheight=0.1)
       
       self.listbox= tk.Listbox(scrollFrame, height = 500, width = 350, xscrollcommand=scrollbar_x.set, yscrollcommand=scrollbar_y.set)
       self.listbox.pack(expand=0, fill='both')
       scrollbar_x.config(command=self.listbox.xview)
       scrollbar_y.config(command=self.listbox.yview)
       
   def clicked(self):
       content = filedialog.askopenfilenames(title='Choose files', defaultextension='.log')
       [self.listbox.insert(tk.END, item) for item in content]
       
   def delete(self):
       self.listbox.delete(0, tk.END)
     
   def delete_selected(self):
       self.listbox.delete(tk.ANCHOR)
       
   def df_tree(self, df, tab):
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
               tree.column(i, width=50, stretch='no')
       
   def findEntries(self):
       global files, kvct_df, pet_df, kvct_filtered, kvct_filtered_out, system, dates
       global filtered_analysis, sessions, unfiltered_analysis, pet_analysis
       
       files = list(self.listbox.get(0,tk.END))
       
       # Find all interlocks
       try:
           system, kvct_df, pet_df = DiagnosticTool.GetEntries(files)
           self.df_tree(kvct_df, Page2.tab1)
           self.df_tree(pet_df, Page2.tab4)
           Page2.menubar_filter(kvct_df, Page2.menubar1)
           Page2.menubar_filter(pet_df, Page2.menubar2)
           
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
           self.df_tree(kvct_filtered, Page2.tab2)
           self.df_tree(kvct_filtered_out, Page2.tab3)
       except:
           messagebox.showerror("Error", "Cannot filter interlocks.")
           pass
       
       # Analyze interlocks 
       try:
           filtered_analysis, sessions, unfiltered_analysis, pet_analysis = DiagnosticTool.Analysis(kvct_filtered, kvct_filtered_out, pet_df)
           self.df_tree(filtered_analysis, Page3.tab1)
           self.df_tree(unfiltered_analysis, Page3.tab2)
           self.df_tree(pet_analysis, Page3.tab3)

       except: 
           messagebox.showerror("Error", "Cannot analyze filtered interlocks.")
           pass
       
   def exportExcel(self):  
       directory = self.entry_directory.get()
           
        # Summary Table
       info = ['System', 'Dates', 'Total Sessions', 'KVCT Total Interlocks', 'KVCT Unexpected Interlocks', 'KVCT Expected Interlocks', 'PET Interlocks']
       values = [system, dates, sessions, len(kvct_df), len(kvct_filtered), len(kvct_filtered_out), len(pet_df)]
       summary_df = pd.DataFrame([info, values]).transpose()
       
       # Interlocks Excel File
       interlocks_writer = pd.ExcelWriter(directory + '\InterlocksList.xlsx', engine='xlsxwriter')
       kvct_df.to_excel(interlocks_writer, sheet_name='KVCT Interlocks (All)')
       kvct_filtered.to_excel(interlocks_writer, sheet_name='KVCT Interlocks (Unexpect)')
       kvct_filtered_out.to_excel(interlocks_writer, sheet_name='KVCT Interlocks (Expected)')
       pet_df.to_excel(interlocks_writer, sheet_name='PET Interlocks')
       interlocks_writer.save()
       
       # Analysis Excel File
       analysis_writer = pd.ExcelWriter(directory + '\InterlocksAnalysis.xlsx', engine='xlsxwriter')
       summary_df.to_excel(analysis_writer, sheet_name='Summary')
       filtered_analysis.to_excel(analysis_writer, sheet_name='KVCT Analysis (Unexpect)')
       unfiltered_analysis.to_excel(analysis_writer, sheet_name='KVCT Analysis (Expect)')
       pet_analysis.to_excel(analysis_writer, sheet_name='PET Analysis')
       analysis_writer.save()
       
       tk.messagebox.showinfo(title='Info', message='Excel files exported')
       
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
       Page2.menubar1.place(relx=0.6, relheight=0.025)
       # pet dataframes
       Page2.menubar2 = tk.Menubutton(self, text='Filter PET Interlocks \u25BE', font=20, relief='raised')
       Page2.menubar2.place(relx=0.8, relheight=0.025)
       
       button_filter = tk.Button(self, text="Filter", command = self.filter_by_interlock)
       button_filter.place(relx=0.4, relheight=0.025)
       
    def menubar_filter(df, menubar):
       menubar.menu = tk.Menu(menubar, tearoff=0)
       menubar["menu"] = menubar.menu

       Page2.items = sorted(list(set(df['Interlock Number'])))
       for item in Page2.items:
           menubar.menu.add_checkbutton(label=item, variable=item)
       
    def filter_by_interlock(self):
        return()
#        for item in Page2.items:
#            if item.get() == True:
#                print(item, 'True')
        
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

        b1 = tk.Button(buttonframe, text="Files", command=p1.lift)
        b2 = tk.Button(buttonframe, text="Interlocks List", command=p2.lift)
        b3 = tk.Button(buttonframe, text="Analysis", command=p3.lift)

        b1.pack(side="left")
        b2.pack(side="left")
        b3.pack(side="left")

        p1.show()

if __name__ == "__main__":
    root = tk.Tk()
    root.state('zoomed')
    main = MainView(root)
    main.pack(side="top", fill="both", expand=True)
    root.wm_geometry("1500x800")
    root.mainloop()
