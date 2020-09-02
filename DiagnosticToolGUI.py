 # -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 15:24:57 2020

@author: btierra
"""
import os
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

       # ****** Top Frame ******
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
       
       # ****** Bottom Frame ******
       bottomFrame = tk.Frame(self)
       bottomFrame.place(relx=0.5, rely=0.3, relwidth=0.9, relheight=0.7, anchor='n')
       
       fileLabel = tk.Label(bottomFrame, text="Choose Files", font=20)
       fileLabel.place(relx=0.08,relheight=0.1)
       
       # Scrollbox to list details of chosen log files
       scrollFrame2 = tk.Frame(bottomFrame, bd=1, relief='solid')
       scrollFrame2.place(relx=0.08,rely=0.08, relwidth=0.7, relheight=0.9)
       
       self.tree = ttk.Treeview(scrollFrame2)
       self.tree['show'] = 'headings'
       
       scrollbar_x2 = ttk.Scrollbar(scrollFrame2, orient="horizontal", command=self.tree.xview)
       scrollbar_y2  = ttk.Scrollbar(scrollFrame2, orient="vertical", command=self.tree.yview)
       
       self.tree.configure(yscrollcommand=scrollbar_y2.set, xscrollcommand=scrollbar_x2.set)
       self.tree.grid(column=0, row=0, sticky='nsew', in_=scrollFrame2)
       scrollbar_y2.grid(column=1, row=0, sticky='ns', in_=scrollFrame2)
       scrollbar_x2.grid(column=0, row=1, sticky='ew', in_=scrollFrame2)
       scrollFrame2.grid_columnconfigure(0, weight=1)
       scrollFrame2.grid_rowconfigure(0, weight=1)
       
       columns = ['File', 'Size', 'Path']
       self.tree["columns"] = columns
       [self.tree.heading(col, text=col, anchor='w', command=lambda c=col: SubFunctions.sortby(self.tree, c, 0, True)) for col in columns]
       self.tree.column('File', width=300, stretch='no')
       self.tree.column('Size', width=100, stretch='no')
       self.tree.column('Path', width=500, stretch='no')

       # Buttons for List of Files
       button_find2 = tk.Button(bottomFrame, text='Find Interlocks', font=15, command=self.findInterlocks)
       button_find2.place(relx=0.8, rely=0.9, relwidth=0.1, relheight=0.06)
          
       button_add2 = tk.Button(bottomFrame, text='Add', font=15, command=self.addFile)
       button_add2.place(relx=0.8, rely=0.1, relwidth=0.1, relheight=0.05)
       
       button_delete_select2 = tk.Button(bottomFrame, text='Delete', font=15, command=self.deleteFile_selected)
       button_delete_select2.place(relx=0.8, rely=0.15, relwidth=0.1, relheight=0.05)
          
       button_delete2 = tk.Button(bottomFrame, text='Delete All', font=15, command=self.deleteFile_all)
       button_delete2.place(relx=0.8, rely=0.2, relwidth=0.1, relheight=0.05)

   def addFolder(self):
       folderlist = []
       folder = filedialog.askdirectory()
       folderlist.append(folder)
       [self.listbox1.insert(tk.END, item) for item in folderlist]
     
   def deleteFolder_selected(self):
       self.listbox1.delete(tk.ANCHOR)
       
   def findFiles(self):
       global all_files
       folders = list(self.listbox1.get(0,tk.END))
       all_files = []
       for folder in folders:
           files = DiagnosticTool.GetFiles(folder)
           for file in files:
               all_files.append(file)
       Page1.addFileDetails(self.tree, all_files)
      
   def addFile(self):
       global content
       content = filedialog.askopenfilenames(title='Choose files', filetypes=[('Text Document', '*.log')])
       Page1.addFileDetails(self.tree, content)
       
   def addFileDetails(tree, file_list):
       for file in file_list:
           if '\\' in file:
               file = file.replace('\\', '/')
           parse = file.split('/')
           filename = parse[-1]
           size = int((os.stat(file).st_size)/1000)
           path = ('/').join(parse[:-1])
           tree.insert('', 'end', values=[filename,size,path])
       
   def deleteFile_all(self):
       [self.tree.delete(i) for i in self.tree.get_children()]
    
   def deleteFile_selected(self):
       selected_item = self.tree.selection()[0]
       self.tree.delete(selected_item)
       
   def findInterlocks(self):
       global files
       files=[]
       for child in self.tree.get_children():
          files.append(self.tree.item(child)["values"][-1]+'/'+self.tree.item(child)["values"][0])
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
       Page2.tabControl.add(Page2.tab4, text = 'KVCT Analysis (Unexpected)')
       
       Page2.tab5 = ttk.Frame(Page2.tabControl)
       Page2.tabControl.add(Page2.tab5, text = 'KVCT Analysis (Expected)')

       Page2.tabControl.pack(expan=1, fill='both')
       
       # Add filtering menubars
       Page2.menubar = tk.Menubutton(self, text='Filter KVCT Interlocks \u25BE', font=20, relief='raised')
       Page2.menubar.place(relx=0.62, relheight=0.025)
       
       button_filter = tk.Button(self, text="Filter", font=20, command = Page2.filter_by_interlock)
       button_filter.place(relx=0.89, relheight=0.025)
       
       button_selectall = tk.Button(self, text="Select All", font=20, command=Page2.selectall)
       button_selectall.place(relx=0.76, relheight=0.025)
       
       button_selectnone = tk.Button(self, text="Select None", font=20, command=Page2.selectnone)
       button_selectnone.place(relx=0.82, relheight=0.025)
       
    def menubar_filter(df, menubar):
        global kvct_interlock_set 
        items = sorted(list(set(df['Interlock Number'])))
        
        menubar.menu = tk.Menu(menubar, tearoff=0)
        menubar["menu"] = menubar.menu
        
        kvct_interlock_set = {}
        for idx, item in enumerate(items):
            var = tk.BooleanVar()
            var.set(True)
            menubar.menu.add_checkbutton(label=item, variable=var)
            kvct_interlock_set[str(item)] = var
       
    def filter_by_interlock():
        interlock_list = []
        for interlock, var in kvct_interlock_set.items():
            if var.get() == True:
                interlock_list.append(interlock)
                
        df1 = kvct_df[kvct_df['Interlock Number'].isin(interlock_list)]
        df2 = kvct_filtered[kvct_filtered['Interlock Number'].isin(interlock_list)]
        df3 = kvct_filtered_out[kvct_filtered_out['Interlock Number'].isin(interlock_list)]
        [widget.destroy() for widget in Page2.tab1.winfo_children()]
        [widget.destroy() for widget in Page2.tab2.winfo_children()]
        [widget.destroy() for widget in Page2.tab3.winfo_children()]
        SubFunctions.df_tree(df1, Page2.tab1)
        SubFunctions.df_tree(df2, Page2.tab2)
        SubFunctions.df_tree(df3, Page2.tab3)
    
    def selectall():
        for interlock, var in kvct_interlock_set.items():
            var.set(True)
        Page2.filter_by_interlock()
    def selectnone():
        for interlock, var in kvct_interlock_set.items():
            var.set(False)
        Page2.filter_by_interlock()
            
class Page3(Page):
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)        
       Page3.tabControl = ttk.Notebook(self)        
       
       Page3.tab1 = ttk.Frame(Page3.tabControl)
       Page3.tabControl.add(Page3.tab1, text = 'Recon Interlocks (All)')
       
       Page3.tab2 = ttk.Frame(Page3.tabControl)
       Page3.tabControl.add(Page3.tab2, text = 'Recon Interlocks (Unexpected)')
       
       Page3.tab3 = ttk.Frame(Page3.tabControl)
       Page3.tabControl.add(Page3.tab3, text = 'Recon Interlocks (Expected)')
       
       Page3.tab4 = ttk.Frame(Page3.tabControl)
       Page3.tabControl.add(Page3.tab4, text = 'Recon Interlocks (Expected)')
       
       Page3.tab5 = ttk.Frame(Page3.tabControl)
       Page3.tabControl.add(Page3.tab5, text = 'Recon Interlocks (Expected)')
       
       Page3.tabControl.pack(expan=1, fill='both')
       
       # Add filtering menubars
       Page3.menubar = tk.Menubutton(self, text='Filter Recon Interlocks \u25BE', font=20, relief='raised')
       Page3.menubar.place(relx=0.62, relheight=0.025)
       
       button_filter = tk.Button(self, text="Filter", font=20, command = Page3.filter_by_interlock)
       button_filter.place(relx=0.89, relheight=0.025)
       
       button_selectall = tk.Button(self, text="Select All", font=20, command=Page3.selectall)
       button_selectall.place(relx=0.76, relheight=0.025)
       
       button_selectnone = tk.Button(self, text="Select None", font=20, command=Page3.selectnone)
       button_selectnone.place(relx=0.82, relheight=0.025)
       
   def menubar_filter(df, menubar):
       global recon_interlock_set 
       items = sorted(list(set(df['Interlock Number'])))
        
       menubar.menu = tk.Menu(menubar, tearoff=0)
       menubar["menu"] = menubar.menu
       
       recon_interlock_set = {}
       for idx, item in enumerate(items):
           var = tk.BooleanVar()
           var.set(True)
           menubar.menu.add_checkbutton(label=item, variable=var)
           recon_interlock_set[str(item)] = var
       
   def filter_by_interlock():
       interlock_list = []
       for interlock, var in recon_interlock_set.items():
           if var.get() == True:
               interlock_list.append(interlock)
            
       df1 = recon_df[recon_df['Interlock Number'].isin(interlock_list)]
       df2 = recon_filtered[recon_filtered['Interlock Number'].isin(interlock_list)]
       df3 = recon_filtered_out[recon_filtered_out['Interlock Number'].isin(interlock_list)]
       [widget.destroy() for widget in Page3.tab1.winfo_children()]
       [widget.destroy() for widget in Page3.tab2.winfo_children()]
       [widget.destroy() for widget in Page3.tab3.winfo_children()]
       SubFunctions.df_tree(df1, Page3.tab1)
       SubFunctions.df_tree(df2, Page3.tab2)
       SubFunctions.df_tree(df3, Page3.tab3)
       
   def selectall():
       for interlock, var in recon_interlock_set.items():
           var.set(True)
       Page3.filter_by_interlock()
       
   def selectnone():
       for interlock, var in recon_interlock_set.items():
           var.set(False)
       Page3.filter_by_interlock()

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
        b2 = tk.Button(buttonframe, text="Kvct Results", command=p2.lift)
        b3 = tk.Button(buttonframe, text="Recon Results", command=p3.lift)

        b1.pack(side="left")
        b2.pack(side="left")
        b3.pack(side="left")

        p1.show()

class SubFunctions():
    def findEntries(files):
       global kvct_df, kvct_filtered, kvct_filtered_out, kvct_analysis, kvct_unfiltered_analysis
       global recon_df, recon_filtered, recon_filtered_out, recon_analysis, recon_unfiltered_analysis
       global system, dates
       
       # Find all interlocks
       try:
           system, kvct_df, recon_df = DiagnosticTool.GetEntries(files)
           SubFunctions.df_tree(kvct_df, Page2.tab1)
           SubFunctions.df_tree(recon_df, Page3.tab1)
           Page2.menubar_filter(kvct_df, Page2.menubar)
           Page3.menubar_filter(recon_df, Page3.menubar)
           
           # Get dates
           start_date = kvct_df['Date'][0]
           end_date = kvct_df['Date'][len(kvct_df)-1]
           dates = str(start_date)+' - '+str(end_date)
       except:
           messagebox.showerror("Error", "Cannot find entries for listed files.")
           pass
       
       # Filter interlocks
       try:
           kvct_filtered, kvct_filtered_out, recon_filtered, recon_filtered_out = DiagnosticTool.FilterEntries(kvct_df, recon_df)
           SubFunctions.df_tree(kvct_filtered, Page2.tab2)
           SubFunctions.df_tree(kvct_filtered_out, Page2.tab3)
           SubFunctions.df_tree(recon_filtered, Page3.tab2)
           SubFunctions.df_tree(recon_filtered_out, Page3.tab3)
       except:
           messagebox.showerror("Error", "Cannot filter interlocks.")
           pass
       
       # Analyze interlocks 
       try:
           kvct_analysis, kvct_unfiltered_analysis, recon_analysis, recon_unfiltered_analysis = \
           DiagnosticTool.Analysis(kvct_filtered, kvct_filtered_out, recon_filtered, recon_filtered_out)
           
           SubFunctions.df_tree(kvct_analysis, Page2.tab4)
           SubFunctions.df_tree(kvct_unfiltered_analysis, Page2.tab5)
           
           SubFunctions.df_tree(recon_analysis, Page3.tab4)
           SubFunctions.df_tree(recon_unfiltered_analysis, Page3.tab5)
       except: 
           messagebox.showerror("Error", "Cannot analyze filtered interlocks.")
           pass
       
    def df_tree(df, tab):
       # Scrollbars
       treeScroll_y = ttk.Scrollbar(tab)
       treeScroll_y.pack(side='right', fill='y')
       treeScroll_x = ttk.Scrollbar(tab, orient='horizontal')
       treeScroll_x.pack(side='bottom', fill='x')
       
       # View dataframe in Treeview format
       columns = list(df.columns)
       tree = ttk.Treeview(tab)
       tree.pack(expand=1, fill='both')
       tree["columns"] = columns
       
       for i in columns:
           tree.column(i, anchor="w")
           tree.heading(i, text=i, anchor='w')
            
       for index, row in df.iterrows():
           tree.insert("",tk.END,text=index,values=list(row))
       
       # Configure scrollbars to the Treeview
       treeScroll_y.configure(command=tree.yview)
       tree.configure(yscrollcommand=treeScroll_y.set)
       treeScroll_x.configure(command=tree.xview)
       tree.configure(xscrollcommand=treeScroll_x.set)
       
       # Format columns per tab
       tree.column("#0", width=50, stretch='no') 
       tree.column("Interlock Number", width=300, stretch='no')
       
       # format based on list or analysis dataframes
       if tab == Page2.tab1 or tab == Page2.tab2 or tab == Page2.tab3 or \
       tab == Page3.tab1 or tab == Page3.tab2 or tab == Page3.tab3:
           tree.column("Date", width=80, stretch='no')
           tree.column("Active Time", width=90, stretch='no')
           tree.column("Inactive Time", width=90, stretch='no')
           tree.column("Time from Node Start (min)", width=100, stretch='no')
           tree.column("Interlock Duration (min)", width=100, stretch='no')
           for i in range(6,len(columns)):
               tree.column(columns[i], width=200, stretch='no')

       # Analysis tabs
       if tab == Page2.tab4 or tab == Page2.tab5 or tab == Page3.tab4 or tab == Page3.tab5:
           tree.column(columns[1], width=100, stretch='no')
           for i in range(1,len(columns)):
               tree.column(columns[i], width=50, stretch='no')
               
    def sortby(tree, col, descending, int_descending):
        # grab values to sort
        data = [(tree.set(child, col), child) \
            for child in tree.get_children('')]
        
        if any(d[0].isnumeric() for d in data):
            data = sorted(data, key=lambda x: int(x[0].replace(',', '')), reverse=int_descending)
        else:
            data.sort(reverse=descending)
            
        for ix, item in enumerate(data):
            tree.move(item[1], '', ix)
        # switch the heading so it will sort in the opposite direction
        tree.heading(col, command=lambda col=col: SubFunctions.sortby(tree, col, int(not descending),int_descending=not int_descending))
        
    def exportExcel():  
       directory = filedialog.askdirectory()
       
       try:
           # Dates to save file under new name each time
           start_date = ('').join(dates.split('-')[1:3])
           end_date = ('').join(dates.split('-')[4:])
           filedate = ('-').join([start_date, end_date]).replace(' ','')
           
           # KVCT Interlocks
           kvct_writer = pd.ExcelWriter(directory + '\KvctInterlocks_' + system + '_' + filedate + '.xlsx', engine='xlsxwriter')
           sheetnames = ['KVCT Interlocks (All)' , 'KVCT Interlocks (Unexpect)', 'KVCT Interlocks (Expect)',
                         'KVCT Analysis (Unexpect)', 'KVCT Analysis (Expect)']
           dataframes = [kvct_df, kvct_filtered, kvct_filtered_out, kvct_analysis, kvct_unfiltered_analysis]
           for df,sheetname in zip(dataframes,sheetnames):
               df.to_excel(kvct_writer,sheetname, index=False)
               
           workbook  = kvct_writer.book
           align = workbook.add_format()
           for df, sheetname in zip(dataframes,sheetnames):
               worksheet = kvct_writer.sheets[sheetname]
               for idx, col in enumerate(df):  # loop through all columns
                   series = df[col]
                   max_len = max((series.astype(str).map(len).max(),len(str(series.name)))) + 1  # adding a little extra space
                   worksheet.set_column(idx, idx, max_len)  # set column width
                   align.set_align('center')
           kvct_writer.save()
           
           # Recon Interlocks
           recon_writer = pd.ExcelWriter(directory + '\ReconInterlocks_' + system + '_' + filedate + '.xlsx', engine='xlsxwriter')
           sheetnames = ['Recon Interlocks (All)' , 'Recon Interlocks (Unexpect)', 'Recon Interlocks (Expect)',
                         'Recon Analysis (Unexpect)', 'Recon Analysis (Expect)']
           dataframes = [recon_df, recon_filtered, recon_filtered_out, recon_analysis, recon_unfiltered_analysis]
           for df,sheetname in zip(dataframes,sheetnames):
               df.to_excel(recon_writer,sheetname, index=False)
               
           workbook  = recon_writer.book
           align = workbook.add_format()
           for df, sheetname in zip(dataframes,sheetnames):
               worksheet = recon_writer.sheets[sheetname]
               for idx, col in enumerate(df):  # loop through all columns
                   series = df[col]
                   max_len = max((series.astype(str).map(len).max(),len(str(series.name)))) + 1  # adding a little extra space
                   worksheet.set_column(idx, idx, max_len)  # set column width
                   align.set_align('center')
           recon_writer.save()
    
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
           

