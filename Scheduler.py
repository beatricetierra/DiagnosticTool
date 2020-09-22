# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 14:40:49 2020

@author: btierra
"""

import schedule
import time
from datetime import datetime
import os
import paramiko
from scp import SCPClient

def GetLogs():
    # Connect to system gateway (A2)
    ssh = paramiko.SSHClient() 
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect(hostname='192.168.45.210', username='rxm', password='plokokok')
    sftp = ssh.open_sftp()
    
    # Create folder to keep logs before transfer
    sftp = paramiko.SFTPClient.from_transport(ssh.get_transport())
    storage_folder = '/home/rxm/kvctlogs'
    try:
        stdin, stdout, stderr = ssh.exec_command("rm -r "  +  storage_folder)   # remove existing files
        sftp.mkdir(storage_folder)  
    except:
        sftp.mkdir(storage_folder)  # Create new folder 
        
    # Copy kvct, pet, and sysnode log files to new directory
    date_time = datetime.today()
    date = date_time.strftime('%Y-%m-%d')
    
    stdin, stdout, stderr = ssh.exec_command('cp -r /home/rxm/log/archive/' + date + ' /home/rxm/kvctlogs')
    stdin, stdout, stderr = ssh.exec_command('scp -r 192.168.10.106:/home/rxm/log/archive/' + date +' /home/rxm/kvctlogs')
    stdin, stdout, stderr = ssh.exec_command('scp -r 192.168.10.110:/home/rxm/log/archive/' + date +' /home/rxm/kvctlogs')
    
    # Remove large -log- files
    stdin, stdout, stderr = ssh.exec_command(r'find -name \'*-log-*\' -delete')
    
    # Export to local computer
    parent_dir = r'C:/Users/btierra/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Python 3.7/Log Diagnostic Tool/Output/'
    foldername = date_time.strftime("%Y%m%d_%H%M%S")
    os.mkdir(parent_dir + foldername)
    
    scp = SCPClient(ssh.get_transport())
    scp.get(r'/home/rxm/kvctlogs', parent_dir + foldername, recursive=True)
    
    sftp.close()
    ssh.close()

schedule.every(1).minutes.do(GetLogs)
#schedule.every().day.at("23:00").do(GetLogs)
while True:
    schedule.run_pending()
    time.sleep(60) # wait one minute