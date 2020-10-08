# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 12:04:22 2020

@author: btierra
"""

import tkinter as tk
from tkinter import ttk
import tkcalendar
import os
import paramiko
import socket
from scp import SCPClient
from datetime import datetime, timedelta

class LogExportGUI(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        
        cal_start = tkcalendar.Calendar(self, selectmode='day', year=2020, month=9, day=6)
        cal_start.place(relx=0.1, rely=0.02, relwidth=0.38, relheight=0.25)
        
        cal_end = tkcalendar.Calendar(self, selectmode='day', year=2020, month=10, day=15)
        cal_end.place(relx=0.52, rely=0.02, relwidth=0.38, relheight=0.25)
        
        label = tk.Label(self, text='Output Directory:')
        label.place(relx=0.1, rely=0.28, relwidth=0.15, relheight=0.03)
        
        entry = tk.Entry(self)
        entry.place(relx=0.26, rely=0.28, relwidth=0.64, relheight=0.03)
        
        button1 = tk.Button(self, text='List Files', command=lambda: SubFunctions.ListFiles(cal_start.get_date(), cal_end.get_date()))
        button1.place(relx=0.40, rely=0.33, relwidth=0.15, relheight=0.03, anchor='n')

        button2 = tk.Button(self, text='Get Logs', command=lambda: SubFunctions.GetLogs(entry.get()))
        button2.place(relx=0.60, rely=0.33, relwidth=0.15, relheight=0.03, anchor='n')
        
        # Scrollbox to list log files found
        scrollFrame = tk.Frame(self, bd=1, relief='solid')
        scrollFrame.place(relx=0.5,rely=0.38, relwidth=0.95, relheight=0.6, anchor='n')
        
        LogExportGUI.tree = ttk.Treeview(scrollFrame)
        LogExportGUI.tree['show'] = 'headings'

        scrollbar  = ttk.Scrollbar(scrollFrame, orient="vertical", command=self.tree.yview)
        LogExportGUI.tree.configure(yscrollcommand=scrollbar.set)
        
        LogExportGUI.tree.grid(column=0, row=0, sticky='nsew', in_=scrollFrame)
        scrollbar.grid(column=1, row=0, sticky='ns', in_=scrollFrame)
        scrollFrame.grid_columnconfigure(0, weight=1)
        scrollFrame.grid_rowconfigure(0, weight=1)      
        LogExportGUI.tree["columns"] = ['File']
        [LogExportGUI.tree.heading(col, text=col, anchor='w') for col in self.tree["columns"]]
        
class SubFunctions():
    def ListFiles(date_start, date_end):
        
        # Get all dates from given range
        global dates, storage_folder
        
        date_start = datetime.strptime(date_start, '%m/%d/%y').date()
        date_end = datetime.strptime(date_end, '%m/%d/%y').date()       
        delta = date_end - date_start
        dates = [date_start + timedelta(days=i) for i in range(delta.days + 1)]
        dates = [date.strftime('%Y-%m-%d') for date in dates]
        
        # Get log files from all dates
        ## Log in to Alpha2
        ssh = paramiko.SSHClient() 
        ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
        ssh.connect(hostname='192.168.45.210', username='rxm', password='plokokok')
        socket.settimeout(timeout)

        ## Create folder to keep logs before transfer    
        storage_folder = '/home/rxm/kvctlogs/'
        try:
            stdin, stdout, stderr = ssh.exec_command('rm -r ' + storage_folder)
            stdin, stdout, stderr = ssh.exec_command('mkdir ' + storage_folder)
        except:
            stdin, stdout, stderr = ssh.exec_command('mkdir ' + storage_folder)
            
        ## Transfer kvct, pet_recon, and sysnode log files to new directory
        for date in dates:
            stdin, stdout, stderr = ssh.exec_command("mkdir "  +  storage_folder + date)
            stdin, stdout, stderr = ssh.exec_command('cp -r /home/rxm/log/archive/' + date + '/*-pet_recon-* ' + storage_folder + date)
            stdin, stdout, stderr = ssh.exec_command('scp -r 192.168.10.106:/home/rxm/log/archive/' + date +  '/*-kvct-* ' + storage_folder + date)
            stdin, stdout, stderr = ssh.exec_command('scp -r 192.168.10.110:/home/rxm/log/archive/' + date +  '/*-sysnode-* ' + storage_folder + date)
        
        ## List files in folder
        sftp = ssh.open_sftp()
        for date in dates:
            for file in sftp.listdir(storage_folder+date):
                LogExportGUI.tree.insert('', 'end', values=[file])
        
#        for date in dates:
#            print('\n*****' + date + '*****')
#            [print(file) for file in sftp.listdir(storage_folder+date)]
            
        ssh.close()
        
    def GetLogs(output):
        ## Log in to Alpha2
        ssh = paramiko.SSHClient() 
        ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
        ssh.connect(hostname='192.168.45.210', username='rxm', password='plokokok')
        socket.settimeout(timeout)
        
        scp = SCPClient(ssh.get_transport())
        [scp.get(storage_folder+date, output, recursive=True) for date in dates]
        
if __name__ == "__main__":
    root = tk.Tk()
    LogExportGUI(root).pack(side="top", fill="both", expand=True)
    root.wm_geometry("700x800")
    root.mainloop()