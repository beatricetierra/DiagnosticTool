# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 12:04:59 2020

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
      
       Frame = tk.Frame(self)
       Frame.place(relx=0.5, relwidth=0.95, relheight=0.95, anchor='n')
       
       # Scrollbox to list details of chosen log files
       scrollFrame = tk.Frame(Frame, bd=1, relief='solid')
       scrollFrame.place(relx=0.42, rely=0.1, relwidth=0.80, relheight=0.9, anchor='n')
       
       self.tree = ttk.Treeview(scrollFrame)
       self.tree['show'] = 'headings'
       
       scrollbar_x = ttk.Scrollbar(scrollFrame, orient="horizontal", command=self.tree.xview)
       scrollbar_y  = ttk.Scrollbar(scrollFrame, orient="vertical", command=self.tree.yview)
       
       self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
       self.tree.grid(column=0, row=0, sticky='nsew', in_=scrollFrame)
       scrollbar_y.grid(column=1, row=0, sticky='ns', in_=scrollFrame)
       scrollbar_x.grid(column=0, row=1, sticky='ew', in_=scrollFrame)
       scrollFrame.grid_columnconfigure(0, weight=1)
       scrollFrame.grid_rowconfigure(0, weight=1)
       
       columns = ['File', 'Size', 'Path']
       self.tree["columns"] = columns
       [self.tree.heading(col, text=col, anchor='w', command=lambda c=col: SubFunctions.sortby(self.tree, c, 0, True)) for col in columns]
       self.tree.column('File', width=300, stretch='no')
       self.tree.column('Size', width=100, stretch='no')
       self.tree.column('Path', width=500, stretch='no')

       # Buttons for List of Files
       button_selectfolder = tk.Button(Frame, text='Select Folder', font=30, command=self.addFolder)
       button_selectfolder.place(relx=0.85, rely=0.1, relwidth=0.1, relheight=0.05)
          
       button_add = tk.Button(Frame, text='Add', font=15, command=self.addFile)
       button_add.place(relx=0.85, rely=0.4, relwidth=0.1, relheight=0.05)
       
       button_delete_select = tk.Button(Frame, text='Delete', font=15, command=self.deleteFile_selected)
       button_delete_select.place(relx=0.85, rely=0.45, relwidth=0.1, relheight=0.05)
          
       button_delete = tk.Button(Frame, text='Delete All', font=15, command=self.deleteFile_all)
       button_delete.place(relx=0.85, rely=0.5, relwidth=0.1, relheight=0.05)
       
       button_find = tk.Button(Frame, text='Find Interlocks', font=15, command=self.findInterlocks)
       button_find.place(relx=0.85, rely=0.9, relwidth=0.1, relheight=0.05)

   def addFolder(self):
       folder = filedialog.askdirectory()
       files = DiagnosticTool.GetFiles(folder)
       Page1.addFileDetails(self.tree, files)
      
   def addFile(self):
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
       
       Page2.Frame = tk.Frame(self, bd=1, relief='solid')
       Page2.Frame.place(relx=0.5, rely=0.08, relwidth=0.99, relheight=0.91, anchor='n')
       
       Page2.toggleButton = tk.Button(self, text="Filter Expected Interlocks", width=12, relief="raised", command=Page2.toggle)
       Page2.toggleButton.place(relx=0.4, rely=0.02, relwidth=0.15, relheight=0.04)
           
       # Add filtering menubars
       FilterButtons = tk.Frame(self)
       FilterButtons.place(relx=0.7, relwidth=0.3, relheight=0.08, anchor='nw')
       
       Page2.menubar = tk.Menubutton(FilterButtons, text='Filter KVCT Interlocks \u25BE', font=20, relief='raised')
       Page2.menubar.place(rely=0.5, relwidth=0.53, relheight=0.45)
       
       button_filter = tk.Button(FilterButtons, text="Filter", font=20, command = Page2.filter_by_interlock)
       button_filter.place(relx=0.6,rely=0.3, relwidth=0.3, relheight=0.4)
       
       button_selectall = tk.Button(FilterButtons, text="Select All", font=20, command=Page2.selectall)
       button_selectall.place(relwidth= 0.22, relheight=0.45)
       
       button_selectnone = tk.Button(FilterButtons, text="Select None", font=20, command=Page2.selectnone)
       button_selectnone.place(relx=0.25,relwidth=0.28, relheight=0.45)
    
    def toggle():
       if Page2.toggleButton.config('relief')[-1] == 'sunken':
           Page2.toggleButton.config(relief="raised")
           [widget.destroy() for widget in Page2.Frame.winfo_children()]
           SubFunctions.df_tree(kvct_unfiltered, Page2.Frame)
           Page2.menubar_filter(kvct_unfiltered, Page2.menubar)
       else:
           Page2.toggleButton.config(relief="sunken")
           [widget.destroy() for widget in Page2.Frame.winfo_children()]
           SubFunctions.df_tree(kvct_filtered, Page2.Frame)
           Page2.menubar_filter(kvct_filtered, Page2.menubar)
            
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
                
        if Page2.toggleButton.config('relief')[-1] == 'raised':
            df1 = kvct_unfiltered[kvct_unfiltered['Interlock Number'].isin(interlock_list)]
            [widget.destroy() for widget in Page2.Frame.winfo_children()]
            SubFunctions.df_tree(df1, Page2.Frame)
        elif Page2.toggleButton.config('relief')[-1] == 'sunken':
            df2 = kvct_filtered[kvct_filtered['Interlock Number'].isin(interlock_list)]
            [widget.destroy() for widget in Page2.Frame.winfo_children()]
            SubFunctions.df_tree(df2, Page2.Frame)

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
       
       Page3.Frame = tk.Frame(self, bd=1, relief='solid')
       Page3.Frame.place(relx=0.5, rely=0.08, relwidth=0.99, relheight=0.91, anchor='n')
       
       Page3.toggleButton = tk.Button(self, text="Filter Expected Interlocks", width=12, relief="raised", command=Page3.toggle)
       Page3.toggleButton.place(relx=0.4, rely=0.02, relwidth=0.15, relheight=0.04)
           
       # Add filtering menubars
       FilterButtons = tk.Frame(self)
       FilterButtons.place(relx=0.7, relwidth=0.3, relheight=0.08, anchor='nw')
       
       Page3.menubar = tk.Menubutton(FilterButtons, text='Filter Recon Interlocks \u25BE', font=20, relief='raised')
       Page3.menubar.place(rely=0.5, relwidth=0.53, relheight=0.45)
       
       button_filter = tk.Button(FilterButtons, text="Filter", font=20, command = Page3.filter_by_interlock)
       button_filter.place(relx=0.6,rely=0.3, relwidth=0.3, relheight=0.4)
       
       button_selectall = tk.Button(FilterButtons, text="Select All", font=20, command=Page3.selectall)
       button_selectall.place(relwidth= 0.22, relheight=0.45)
       
       button_selectnone = tk.Button(FilterButtons, text="Select None", font=20, command=Page3.selectnone)
       button_selectnone.place(relx=0.25,relwidth=0.28, relheight=0.45)
    
    def toggle():
       if Page3.toggleButton.config('relief')[-1] == 'sunken':
           Page3.toggleButton.config(relief="raised")
           [widget.destroy() for widget in Page3.Frame.winfo_children()]
           SubFunctions.df_tree(recon_unfiltered, Page3.Frame)
           Page3.menubar_filter(recon_unfiltered, Page3.menubar)
       else:
           Page3.toggleButton.config(relief="sunken")
           [widget.destroy() for widget in Page3.Frame.winfo_children()]
           SubFunctions.df_tree(recon_filtered, Page3.Frame)
           Page3.menubar_filter(recon_filtered, Page3.menubar)
            
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
                
        if Page3.toggleButton.config('relief')[-1] == 'raised':
            df1 = recon_unfiltered[recon_unfiltered['Interlock Number'].isin(interlock_list)]
            [widget.destroy() for widget in Page3.Frame.winfo_children()]
            SubFunctions.df_tree(df1, Page3.Frame)
        elif Page3.toggleButton.config('relief')[-1] == 'sunken':
            df2 = recon_filtered[recon_filtered['Interlock Number'].isin(interlock_list)]
            [widget.destroy() for widget in Page3.Frame.winfo_children()]
            SubFunctions.df_tree(df2, Page3.Frame)

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
        
        analyze = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Analyze', menu = analyze)
        analyze.add_command(label='Summary Report', command = SubFunctions.SummarizeResults)
        root.config(menu=menubar)
        
        # Navigate between pages
        p1 = Page1(self)
        p2 = Page2(self)
        p3 = Page3(self)

        buttonframe = tk.Frame(self)
        container = tk.Frame(self)
        buttonframe.pack(side="top", anchor='nw')
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
       global kvct_df, kvct_filtered, kvct_unfiltered
       global recon_df, recon_filtered, recon_unfiltered
       global system, dates
       
       # Clear old entries
       [widget.destroy() for widget in Page2.Frame.winfo_children()]
       [widget.destroy() for widget in Page3.Frame.winfo_children()]
       
       # Find interlocks from given log files and filter expected events
       try:
           system, kvct_df, recon_df = DiagnosticTool.GetEntries(files)
           # Get dates
           start_date = kvct_df['Date'][0]
           end_date = kvct_df['Date'][len(kvct_df)-1]
           dates = str(start_date)+' - '+str(end_date)
       except:
           messagebox.showerror("Error", "Cannot find entries for listed files.")
           
       try:
           kvct_filtered, kvct_unfiltered, recon_filtered, recon_unfiltered = DiagnosticTool.FilterEntries(kvct_df, recon_df)
           
           SubFunctions.df_tree(kvct_unfiltered, Page2.Frame)
           Page2.menubar_filter(kvct_unfiltered, Page2.menubar)
           SubFunctions.df_tree(recon_unfiltered, Page3.Frame)
           Page3.menubar_filter(recon_unfiltered, Page3.menubar)
       except:
           messagebox.showerror("Error", "Cannot filter interlocks.")
           SubFunctions.df_tree(kvct_df, Page2.Frame)
           Page2.menubar_filter(kvct_df, Page2.menubar)
           SubFunctions.df_tree(recon_df, Page3.Frame)
           Page3.menubar_filter(recon_df, Page3.menubar)

    def df_tree(df, frame):
       # Scrollbars
       treeScroll_y = ttk.Scrollbar(frame)
       treeScroll_y.pack(side='right', fill='y')
       treeScroll_x = ttk.Scrollbar(frame, orient='horizontal')
       treeScroll_x.pack(side='bottom', fill='x')
       
        # View dataframe in Treeview format
       columns = list(df.columns)      
       frame.tree = ttk.Treeview(frame)
       frame.tree.pack(expand=1, fill='both')
       frame.tree["columns"] = columns
       
       for i in columns:
           frame.tree.column(i, anchor="w")
           frame.tree.heading(i, text=i, anchor='w')
            
       for index, row in df.iterrows():
           frame.tree.insert("",tk.END,text=index,values=list(row))

       # Configure scrollbars to the Treeview
       treeScroll_y.configure(command=frame.tree.yview)
       frame.tree.configure(yscrollcommand=treeScroll_y.set)
       treeScroll_x.configure(command=frame.tree.xview)
       frame.tree.configure(xscrollcommand=treeScroll_x.set)
       
       try:
           # Format columns per tab
           frame.tree.column("#0", width=50, stretch='no') 
           frame.tree.column("Interlock Number", width=350, stretch='no')
           frame.tree.column("Date", width=80, stretch='no')
           frame.tree.column("Active Time", width=90, stretch='no')
           frame.tree.column("Inactive Time", width=90, stretch='no')
           frame.tree.column("Time from Node Start (min)", width=170, stretch='no')
           frame.tree.column("Interlock Duration (min)", width=150, stretch='no')
           for i in range(6,len(columns)):
               frame.tree.column(columns[i], width=200, stretch='no')    
       except:
           pass
        
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
    
    def SummarizeResults():      
        win = tk.Toplevel()
        win.wm_title("Window")
        win.wm_geometry("800x500")
        
        Frame = tk.Frame(win, bd=1, relief='solid')
        Frame.place(relx=0.5, relwidth=1, relheight=1, anchor='n')
        
        tabControl = ttk.Notebook(Frame)        
        tab1 = ttk.Frame(tabControl)
        tabControl.add(tab1, text = 'KVCT Interlocks')
        tab2 = ttk.Frame(tabControl)
        tabControl.add(tab2, text = 'Recon Interlocks')
        tabControl.pack(expand=1, fill='both')
       
        try:
            kvct_filtered_analysis, kvct_unfiltered_analysis, recon_filtered_analysis, recon_unfiltered_analysis = DiagnosticTool.Analysis(
                    kvct_unfiltered, kvct_filtered, recon_unfiltered, recon_filtered)
            
            SubFunctions.df_tree(kvct_filtered_analysis, tab1)
            SubFunctions.df_tree(recon_filtered_analysis, tab2)
        except:
            messagebox.showerror("Error", "Cannot analyze entries for listed files.")
            
    def exportExcel():  
       directory = filedialog.askdirectory()
       try:
           # Dates to save file under new name each time
           start_date = ('').join(dates.split('-')[1:3])
           end_date = ('').join(dates.split('-')[4:])
           filedate = ('-').join([start_date, end_date]).replace(' ','')
           
           # KVCT Interlocks
           kvct_writer = pd.ExcelWriter(directory + '\KvctInterlocks_' + system + '_' + filedate + '.xlsx', engine='xlsxwriter')
           sheetnames = ['KVCT Interlocks (All)' , 'KVCT Interlocks (Filtered)']
           dataframes = [kvct_unfiltered, kvct_filtered]
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
           sheetnames = ['Recon Interlocks (All)' , 'Recon Interlocks (Filtered)']
           dataframes = [recon_unfiltered, recon_filtered]
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
    main = MainView(root)
    main.pack(side="top", fill="both", expand=True)
    root.wm_geometry("1300x800")
    root.mainloop()           