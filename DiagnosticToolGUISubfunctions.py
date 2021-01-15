# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 13:52:02 2020

@author: btierra
"""
# import libraryies
import os
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import pandas as pd
import paramiko
from scp import SCPClient

# import script dependencies 
from GetInterlocks import GetInterlocks as get
import FilterInterlocks as filt
import AnalyzeInterlocks as analyze 

def ConnectServer(Page1, ipaddress, username, password, start, end, output):
    ipaddress, username, password, output = ipaddress.get(), username.get(), password.get(), output.get()
    # Check if all arguments are filled
    if not ipaddress or not username or not password:
        messagebox.showerror(title='Error', message='Enter ipaddress, username, and/or password.')
        return
    if os.path.exists(output)  == False:
        messagebox.showerror(title='Error', message='Invalid output folder.')
        return
    else:
        try:
            # Collect all log files in gateway 
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ipaddress , 22, username , password)
        except:
            messagebox.showerror(title='Error', message='Permission denied')
            return
            
        start = start.get_date().strftime("%Y-%m-%d")
        end = end.get_date().strftime("%Y-%m-%d")
        command = '(cd /home/rxm/; source .GetKvctLogs.sh {startdate} {enddate})'.format(startdate = start , enddate = end)
        stdin, stdout, stderr = ssh.exec_command(command)
        filepaths = stdout.readlines()
    
        # SCP to local folder
        with SCPClient(ssh.get_transport(), sanitize=lambda x: x) as scp:
            for filepath in filepaths:
                scp.get(remote_path=filepath, local_path=output)
                
                filename = filepath.split('/')[-1].replace('\n','')
                local_file = os.path.join(output, filename)
                size = int((os.stat(local_file).st_size)/1000)
                Page1.tree.insert('', 'end', values=[filename,size,output])
                get.UpdateProgress(100/len(filepaths))
    
        ssh.close()
        return
    return

def GetFiles(folderpath):
    acceptable_files = ['-log-','-kvct-','-pet_recon-','-sysnode-']
    filenames = []  

    for root, dirs, files in os.walk(folderpath):
        for file in files:
            if '.log' in file:
                for word in acceptable_files:
                    if word in file:   
                        filenames.append(os.path.join(root, file))
    return(filenames)
    
def FindEntries(Page2, Page3, MainView, files):        
   global kvct_df, kvct_filtered, kvct_unfiltered
   global recon_df, recon_filtered, recon_unfiltered
   global system, dates
   
   # Find interlocks and dates from given log files
   try:
       system, kvct_df, recon_df = get.GetEntries(files)
       # Get dates 
       if kvct_df.empty == False:
           start_date = str(kvct_df['Date'][0]).replace('-', '')
           end_date = str(kvct_df['Date'][len(kvct_df)-1]).replace('-', '')
           dates = start_date + '-' + end_date
       elif kvct_df.empty == True and recon_df.empty == False:
           start_date = str(recon_df['Date'][0]).replace('-','')
           end_date = str(recon_df['Date'][len(recon_df)-1]).replace('-','')
           dates = start_date + '-' + end_date
       else:
           dates = 'NA'
   except:
       messagebox.showerror("Error", "Cannot find entries for listed files.")
       
   # Filter interlocks
   try:
       if kvct_df.empty == False:
           kvct_filtered, kvct_unfiltered = filt.filter_kvct(kvct_df)
       else:
           kvct_filtered, kvct_unfiltered = kvct_df, kvct_df
           messagebox.showinfo(title=None, message='No kVCT interlocks to filter')
       if recon_df.empty == False:
           recon_filtered, recon_unfiltered = filt.filter_recon(recon_df)
       else:
           recon_filtered, recon_unfiltered = recon_df, recon_df
           messagebox.showinfo(title=None, message='No recon interlocks to filter')
   except:
       kvct_filtered, kvct_unfiltered = pd.DataFrame(), pd.DataFrame()
       recon_filtered, recon_unfiltered = pd.DataFrame(), pd.DataFrame()
       messagebox.showerror("Error", "Cannot filter interlocks.")
       
    # Add dataframes to window
   if kvct_unfiltered.empty == False and recon_unfiltered.empty == False:
       df_tree(kvct_unfiltered, Page2.Frame)
       Page2.menubar_filter(kvct_unfiltered, Page2.menubar)
       df_tree(recon_unfiltered, Page3.Frame)
       Page3.menubar_filter(recon_unfiltered, Page3.menubar)
       MainView.SwitchPage(MainView.p2)
   elif kvct_unfiltered.empty == False and recon_unfiltered.empty == True:
       df_tree(kvct_unfiltered, Page2.Frame)
       Page2.menubar_filter(kvct_unfiltered, Page2.menubar)
       MainView.SwitchPage(MainView.p2)
   elif kvct_unfiltered.empty == True and recon_unfiltered.empty == False:
       df_tree(recon_unfiltered, Page3.Frame)
       Page3.menubar_filter(recon_unfiltered, Page3.menubar)
       MainView.SwitchPage(MainView.p3)
   elif kvct_unfiltered.empty == True and recon_unfiltered.empty == True:
       df_tree(kvct_df, Page2.Frame)
       Page2.menubar_filter(kvct_df, Page2.menubar)
       df_tree(recon_df, Page3.Frame)
       Page3.menubar_filter(recon_df, Page3.menubar)
       MainView.SwitchPage(MainView.p2)
       messagebox.showinfo(title=None, message='No interlocks found')
       
   return(kvct_df, kvct_filtered, kvct_unfiltered, recon_df, recon_filtered, recon_unfiltered, system, dates)

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
    tree.heading(col, command=lambda col=col: sortby(tree, col, int(not descending),int_descending=not int_descending))

def SummarizeResults():      
    win = tk.Toplevel()
    win.wm_title("Window")
    win.wm_geometry("800x500")
    
    Frame = tk.Frame(win, bd=1, relief='solid')
    Frame.place(relx=0.5, relwidth=1, relheight=1, anchor='n')
    
    tabControl = ttk.Notebook(Frame)        
    SummarizeResults.tab1 = ttk.Frame(tabControl)
    tabControl.add(SummarizeResults.tab1, text = 'KVCT Interlocks')
    SummarizeResults.tab2 = ttk.Frame(tabControl)
    tabControl.add(SummarizeResults.tab2, text = 'Recon Interlocks')
    tabControl.pack(expand=1, fill='both')
    
    try: # if filtered dataframes are empty, analyze function return empty dataframes
        kvct_filtered_analysis = analyze.unexpected(kvct_filtered)
        recon_filtered_analysis = analyze.unexpected(recon_filtered)
    except:
        messagebox.showerror("Error", "Cannot analyze entries for listed files.")
    
    # display dataframes in pop-up window
    if kvct_filtered_analysis.empty == False:
        df_tree(kvct_filtered_analysis, SummarizeResults.tab1)
    else:
        pass
    if recon_filtered_analysis.empty == False:
        df_tree(recon_filtered_analysis, SummarizeResults.tab2)
    else:
        pass
        
def exportExcel():  
   directory = filedialog.askdirectory()
   try:       
       # KVCT Interlocks
       kvct_writer = pd.ExcelWriter(directory + '\KvctInterlocks_' + system + '_' + dates + '.xlsx', engine='xlsxwriter')
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
       recon_writer = pd.ExcelWriter(directory + '\ReconInterlocks_' + system + '_' + dates + '.xlsx', engine='xlsxwriter')
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