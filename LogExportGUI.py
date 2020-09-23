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
from datetime import datetime

class LogExportGUI(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        
        cal = tkcalendar.Calendar(self, selectmode='day', year=2020, month=9, day=22)
        cal.pack(pady=20)
        
        button = tk.Button(self, text='Get Logs', command=lambda: Subfunctions.FindLogs(cal.get_date()))
        button.pack(pady=20)
        
        label = tk.Label(self, text='')
        label.pack(pady=20)
        
class Subfunctions():
    def FindLogs(date_time):
        ssh = paramiko.SSHClient() 
        ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
        ssh.connect(hostname='192.168.45.210', username='rxm', password='plokokok')

        # Create folder to keep logs before transfer
        date_time = datetime.strptime(date_time, '%m/%d/%y').date()
        date = date_time.strftime('%Y-%m-%d')    
        
        storage_folder = '/home/rxm/kvctlogs'
        try:
            stdin, stdout, stderr = ssh.exec_command("rm -r "  +  storage_folder)   # remove existing files
            stdin, stdout, stderr = ssh.exec_command("mkdir "  +  storage_folder) 
        except:
            stdin, stdout, stderr = ssh.exec_command("mkdir "  +  storage_folder) 
            
        # Copy kvct, pet, and sysnode log files to new directory
        stdin, stdout, stderr = ssh.exec_command('cp -r /home/rxm/log/archive/' + date + ' /home/rxm/kvctlogs')
        stdin, stdout, stderr = ssh.exec_command('scp -r 192.168.10.106:/home/rxm/log/archive/' + date +' /home/rxm/kvctlogs')
        stdin, stdout, stderr = ssh.exec_command('scp -r 192.168.10.110:/home/rxm/log/archive/' + date +' /home/rxm/kvctlogs')
        
        # Remove large -log- files
        stdin, stdout, stderr = ssh.exec_command(r'find -name \'*-log-*\' -delete')
        
        # Export to local computer
        parent_dir = r'C:\Users\btierra\Downloads\A2\\'
        foldername = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.mkdir(parent_dir + foldername)
        print(parent_dir + foldername)
        
        scp = SCPClient(ssh.get_transport())
        scp.get(r'/home/rxm/kvctlogs', parent_dir + foldername, recursive=True)

        ssh.close()

if __name__ == "__main__":
    root = tk.Tk()
    LogExportGUI(root).pack(side="top", fill="both", expand=True)
    root.wm_geometry("600x500")
    root.mainloop()