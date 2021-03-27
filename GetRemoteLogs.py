# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 13:36:43 2021

@author: btierra
"""
import os
import paramiko
import datetime
from tkinter import messagebox
from scp import SCPClient
from DiagnosticToolGUISubfunctions import Subfunctions as sub

class GetRemoteLogs:
    def __init__(self, Page1, ipaddress, username, password, output, startdate, starttime, enddate, endtime, button):        
        self.Page1 = Page1 
        self.ipaddress = ipaddress.get()
        self.username = username.get()
        self.password = password.get() 
        self.output = output.get() 
        
        self.startdate = startdate.get_date()
        self.starttime = starttime.get()
        self.enddate = enddate.get_date()
        self.endtime = endtime.get()
        
        # Show button as pressed
        self.button = button
        self.button['relief'] = 'sunken'
        self.button['state'] = 'disabled'

        # Check entries
        self.CheckValidCredentials()
        self.CheckConnection()
        self.CheckOutputFolder()
        self.CheckTimes()
        
        # Import logs from gateway folder
        self.GetRemoteLogFilepaths()
        
        return self.ResetButton()
    def ResetButton(self):
        self.button['state'] = 'normal'
        self.button['relief'] = 'raised'
    
    def CheckValidCredentials(self):
        if not self.ipaddress or not self.username or not self.password:
            messagebox.showerror(title='Error', message='Enter ipaddress, username, and/or password.')
            self.ResetButton()
            raise
            
    def CheckOutputFolder(self):
        if os.path.exists(self.output) == False:
            messagebox.showerror(title='Error', message='Invalid output folder.')
            self.ResetButton()
            raise
            
    def CheckTimes(self):
        try:
            datetime.datetime.strptime(self.starttime, '%H:%M')
            datetime.datetime.strptime(self.endtime, '%H:%M')
        except ValueError as error: 
            messagebox.showerror(title='Error', message=error)
            self.ResetButton()
            raise
            
    def CheckConnection(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ipaddress , 22, self.username , self.password)
            ssh.close()
        except:
            messagebox.showerror(title='Error', message='Permission denied.')
            self.ResetButton()
            raise
            
    def FindFiles(self):
        global recon_files, kvct_files, sys_files
        ssh = self.ConnectServer()
        recon_files = self.SendFindFileCommand(ssh, 'recon')
        kvct_files = self.SendFindFileCommand(ssh, 'kvct')
        sys_files = self.SendFindFileCommand(ssh, 'sysnode')
        ssh.close()
        
        recon_files = self.FilterByTimes(recon_files)
        kvct_files = self.FilterByTimes(kvct_files)
        sys_files = self.FilterByTimes(sys_files)
            
    def SendFindFileCommand(self, ssh, node):
        command = '(cd /home/rxm/kvct/scripts; source FindKvctLogs.sh "{node}")'.format(node=node)
        stdin, stdout, stderr = ssh.exec_command(command)
        return stdout.readlines()
    
    def FilterByTimes(self, files):
        # Get times between startime and endtime + last logs right before startime
        startdatetime, enddatetime = self.CombineDateAndTime()
        
        files_filtered_idx = []
        for idx, filepath in enumerate(files):
            try:
                filename = filepath.split('/')[-1].strip()
                filedatetime = '-'.join(filename.split('-')[:4])
                filedatetime  = datetime.datetime.strptime(filedatetime, '%Y-%m-%d-%H%M%S')
                if startdatetime <= filedatetime <= enddatetime:
                    files_filtered_idx.append(idx)
            except ValueError:
                pass
        
        # Check if log files exist for given time period
        self.LogsFound(files_filtered_idx)
        
        # Add the last log before given starttime
        files_filtered_idx.insert(0,files_filtered_idx[0]-1)
        
        # Get filenames from idx list
        files_filtered = [files[idx] for idx in files_filtered_idx]
        return files_filtered 
    
    def LogsFound(self, filepaths_filtered_idx):
        if not filepaths_filtered_idx:
            messagebox.showinfo(message='No logs found in machine for given dates and times.')
            self.ResetButton()
            raise
        return
         
    def GetRemoteLogFilepaths(self):
        self.FindFiles()
        startdate, enddate = self.FindNewStartAndEndDates()

        # Connect to gateway and run command
        ssh = self.ConnectServer()
        command = '(cd /home/rxm/kvct/scripts; source GetKvctLogs.sh {startdate} {enddate})'.format(
                startdate = startdate, enddate = enddate)
        stdin, stdout, stderr = ssh.exec_command(command)
        results = stdout.readlines()
        
        # get all log files in results
        filepaths = [result for result in results if '.log' in result]
        filepaths.sort()
        
        self.ConnectToKVCT(results) # Check if connection to kvct was successful
        self.SCPLogs(ssh, filepaths)
        ssh.close()
        
    def FindNewStartAndEndDates(self):
        start_dates, end_dates = [],[]
        for file_list in [recon_files, kvct_files, sys_files]:
            start = file_list[0].split('/')[-2]
            end = file_list[-1].split('/')[-2]
            
            start_date = datetime.datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.datetime.strptime(end, '%Y-%m-%d')
            
            start_dates.append(start_date)
            end_dates.append(end_date)
        return str(min(start_dates).date()), str(max(end_dates).date())
        
    def ConnectServer(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ipaddress , 22, self.username , self.password)
            sub.UpdateProgress('reset import')
        except:
            messagebox.showerror(title='Error', message='Connection interrupted.')
            self.ResetButton()
            raise
        return ssh
    
    def ConnectToKVCT(self, results):
        if 'Cannot connect' in results[0]:
            messagebox.showinfo(title='Warning', message='Cannot connect to kvct. Downloading LogNode files (may take a while).')
        else:
            pass 
    
    def SCPLogs(self, ssh, filepaths):    
        filtered_filenames = self.FilteredFilenames(filepaths)
        with SCPClient(ssh.get_transport(), sanitize=lambda x: x) as scp:
            for filepath in filepaths:
                filename = filepath.split('/')[-1].strip()
                if filename in filtered_filenames:
                    scp.get(remote_path=filepath, local_path=self.output)
                    local_file = os.path.join(self.output, filename)
                    size = int((os.stat(local_file).st_size)/1000)
                    self.Page1.tree.insert('', 'end', values=[filename,size,self.output])
                    sub.UpdateProgress(100/len(filtered_filenames))
                else:
                    pass
        return
    
    def FilteredFilenames(self, filename):
        combined_filtered_files = sum([recon_files, kvct_files, sys_files], [])
        filtered_filenames = [file.split('/')[-1].strip() for file
                              in combined_filtered_files]
        return filtered_filenames
        
    def StrToTime(self):
        starttime = datetime.datetime.strptime(self.starttime, '%H:%M').time()
        endtime = datetime.datetime.strptime(self.endtime, '%H:%M').time()
        return starttime, endtime
            
    def DateToStr(self):    #Calendar date picker -> no need for exceptions
        startdate_str = self.startdate.strftime("%Y-%m-%d")
        enddate_str = self.enddate.strftime("%Y-%m-%d")
        return startdate_str, enddate_str
        
    def CombineDateAndTime(self):
        starttime, endtime = self.StrToTime()
        startdatetime = datetime.datetime.combine(self.startdate, starttime)
        enddatetime = datetime.datetime.combine(self.enddate, endtime)
        return startdatetime, enddatetime