# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 11:44:13 2021

@author: btierra
"""
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import pandas as pd
import threading
import time

import ProcessLogs
import LogstoDataframes
import GetInterlocks
import GetDetails
import CleanUp
import Filter

class Subfunctions(threading.Thread):
    def __init__(self, progress, progress_style, root):
        threading.Thread.__init__(self)
        Subfunctions.progress = progress
        Subfunctions.setDaemon(self, daemonic=True)
        Subfunctions.progress_style = progress_style
        Subfunctions.root = root 
        
    def UpdateProgress(perc):
        if perc == 'reset import':
            Subfunctions.progress['value'] = 0
            Subfunctions.progress_style.configure('text.Horizontal.TProgressbar', 
                    text='Fetching log files...')
        elif perc == 'reset process':
            Subfunctions.progress['value'] = 0
            Subfunctions.progress_style.configure('text.Horizontal.TProgressbar', 
                    text='Reading log files...')
        else:
            Subfunctions.progress['value'] += perc
            Subfunctions.progress_style.configure('text.Horizontal.TProgressbar', 
                text='{:.2f} %'.format(Subfunctions.progress['value']))
            time.sleep(0.005)
            Subfunctions.root.update_idletasks()
        return

    def FindInterlockDataframes(files, logtype):
        global system
        global kvct_unfiltered, kvct_filtered
        global recon_unfiltered, recon_filtered
        # Expects only kvct and pet_recon dataframes
        system, unfiltered_dfs, filtered_dfs = Subfunctions.RunMainFunctions(files, logtype)
        
        # kvct dfs
        kvct_unfiltered = unfiltered_dfs['KV']
        kvct_filtered = filtered_dfs['KV']
        
        # pet dfs
        recon_unfiltered = unfiltered_dfs['PR']
        recon_filtered = filtered_dfs['PR']
        return system, kvct_unfiltered, kvct_filtered, recon_unfiltered, recon_filtered
    
        
    def RunMainFunctions(files, logtype):
       Subfunctions.UpdateProgress('reset process')
       filenames = ProcessLogs.FilterFiles(files, logtype)
       endpoints, entries = ProcessLogs.GetLogEntries(filenames, logtype)
       Subfunctions.UpdateProgress(5)
       
       system = ProcessLogs.FindSystem(filenames)
       entries_per_node, endpoints_per_node = LogstoDataframes.CreateDataframes(entries, endpoints)
       Subfunctions.UpdateProgress(15)
       
       grouped_entries_per_node = GetInterlocks.BreakdownEntries(entries_per_node)
       interlocks_per_node = GetInterlocks.GetInterlocksPerNode(grouped_entries_per_node, endpoints_per_node)
       Subfunctions.UpdateProgress(10)
       
       interlocks_per_node_time_details = GetDetails.AddTimeDetails(interlocks_per_node, endpoints_per_node)
       interlocks_per_node_event_details = GetDetails.AddEventDetails(interlocks_per_node_time_details, grouped_entries_per_node)
           # progress bar updated in GetDetail > AddEventDetails function
           
       final_dfs = CleanUp.CleanDataframes(interlocks_per_node_event_details)
       unfiltered_dfs, filtered_dfs = Filter.FilterExpectedInterlocks(final_dfs)
       Subfunctions.UpdateProgress(10)
       return system, unfiltered_dfs, filtered_dfs
    
    def DisplayEntries(Page2, Page3, MainView):       
       #Add dataframes to window
       if kvct_unfiltered.empty == False and recon_unfiltered.empty == False:
           Subfunctions.df_tree(kvct_unfiltered, Page2.Frame)
           Page2.menubar_filter(kvct_unfiltered, Page2.menubar)
           Subfunctions.df_tree(recon_unfiltered, Page3.Frame)
           Page3.menubar_filter(recon_unfiltered, Page3.menubar)     
           MainView.SwitchPage(MainView.p2)
       elif kvct_unfiltered.empty == False and recon_unfiltered.empty == True:
           Subfunctions.df_tree(kvct_unfiltered, Page2.Frame)
           Page2.menubar_filter(kvct_unfiltered, Page2.menubar)
           MainView.SwitchPage(MainView.p2)
       elif kvct_unfiltered.empty == True and recon_unfiltered.empty == False:
           Subfunctions.df_tree(recon_unfiltered, Page3.Frame)
           Page3.menubar_filter(recon_unfiltered, Page3.menubar)
           MainView.SwitchPage(MainView.p3)
           
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
       
       # Format columns per tab
       try:
           frame.tree.column("#0", width=50, stretch='no') 
           frame.tree.column("SW Version", width=130, stretch='no')
           frame.tree.column("Mode", width=80, stretch='no')  
           frame.tree.column("Interlock Number", width=350, stretch='no')
           frame.tree.column("Date", width=80, stretch='no')
           frame.tree.column("Active Time", width=90, stretch='no')
           frame.tree.column("Inactive Time", width=90, stretch='no')
           frame.tree.column("Time from Node Start (min)", width=170, stretch='no')
           frame.tree.column("Interlock Duration (min)", width=150, stretch='no')
           for i in range(6,len(columns)):
               frame.tree.column(columns[i], width=200, stretch='no')
       except:
           frame.tree.column("#0", width=50, stretch='no')
           frame.tree.column(columns[0], width=300, stretch='no')                 
           for i in range(1,len(columns)):
               frame.tree.column(columns[i], width=80, stretch='no')
           
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
        tree.heading(col, command=lambda col=col: 
            Subfunctions.sortby(tree, col, int(not descending),int_descending=not int_descending))   
    
    def exportExcel():  
       directory = filedialog.askdirectory()
       try:       
           # KVCT Interlocks
           kvct_xlsxname = directory + '\KvctInterlocks_' + system + '.xlsx'
           kvct_writer = pd.ExcelWriter(kvct_xlsxname, engine='xlsxwriter')
           sheetnames = ['KVCT Interlocks (All)' , 'KVCT Interlocks (Filtered)', 'KVCT Interlocks (No Couch)']
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
           recon_xlsxname = directory + '\ReconInterlocks_' + system + '.xlsx'
           recon_writer = pd.ExcelWriter(recon_xlsxname, engine='xlsxwriter')
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


