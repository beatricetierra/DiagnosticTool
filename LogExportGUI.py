# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 12:04:22 2020

@author: btierra
"""

import tkinter as tk
import tkcalendar
import os
import paramiko
from scp import SCPClient
from datetime import datetime, timedelta

class LogExportGUI(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        
        cal_start = tkcalendar.Calendar(self, selectmode='day', year=2020, month=9, day=6)
        cal_start.place(relx=0.1, rely=0.05, relwidth=0.38, relheight=0.40)
        
        cal_end = tkcalendar.Calendar(self, selectmode='day', year=2020, month=10, day=15)
        cal_end.place(relx=0.52, rely=0.05, relwidth=0.38, relheight=0.40)
        
        label = tk.Label(self, text='Output Directory:')
        label.place(relx=0.1, rely=0.5, relwidth=0.15, relheight=0.05)
        
        entry = tk.Entry(self)
        entry.place(relx=0.26, rely=0.5, relwidth=0.64, relheight=0.05)
        
        button = tk.Button(self, text='Get Logs', command=lambda: SubFunctions.FindLogs(cal_start.get_date(), cal_end.get_date(), entry.get()))
        button.place(relx=0.5, rely=0.6, relwidth=0.15, relheight=0.05, anchor='n')

        
class SubFunctions():
    def FindLogs(date_start, date_end, ouput):
        
        # Get all dates from given range
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
        scp = SCPClient(ssh.get_transport())
        
        ## Create folder to keep logs before transfer        
        storage_folder = '/home/rxm/kvctlogs/'
        try:
            stdin, stdout, stderr = ssh.exec_command("rm -r "  +  storage_folder)   # remove existing files
            stdin, stdout, stderr = ssh.exec_command("mkdir "  +  storage_folder)
        except:
            stdin, stdout, stderr = ssh.exec_command("mkdir "  +  storage_folder)
            
        ## Transfer kvct, pet_recon, and sysnode log files to new directory
        for date in dates:
            stdin, stdout, stderr = ssh.exec_command("mkdir "  +  storage_folder + date)
            stdin, stdout, stderr = ssh.exec_command('cp -r /home/rxm/log/archive/' + date + '/*-pet_recon-* ' + storage_folder + date)
            stdin, stdout, stderr = ssh.exec_command('scp -r 192.168.10.106:/home/rxm/log/archive/' + date +  '/*-kvct-* ' + storage_folder + date)
            stdin, stdout, stderr = ssh.exec_command('scp -r 192.168.10.110:/home/rxm/log/archive/' + date +  '/*-sysnode-* ' + storage_folder + date)    
            scp.get(storage_folder+date, r'C:\Users\btierra\Downloads\A2\new', recursive=True)

        ssh.close()

if __name__ == "__main__":
    root = tk.Tk()
    LogExportGUI(root).pack(side="top", fill="both", expand=True)
    root.wm_geometry("600x500")
    root.mainloop()