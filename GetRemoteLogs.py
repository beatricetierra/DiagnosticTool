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
from GetInterlocks import GetInterlocks as get

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
            
    def GetRemoteLogFilepaths(self):
        # Checks if day before should be included
        get_daybefore_logs = self.LastLogsDayBefore()  
        startdate_str, enddate_str = self.DateToStr()
        
        # Connect to gateway and run command
        ssh = self.ConnectServer()
        command = '(cd /home/rxm/kvct/scripts; source GetKvctLogs.sh {startdate} {enddate})'.format(startdate = 
                   startdate_str , enddate = enddate_str)
        stdin, stdout, stderr = ssh.exec_command(command)
        results = stdout.readlines()
        
        # Check if connection to kvct node is successful
        GetLogNodeFiles = self.ConnectToKVCT(results)
        
        filepaths = [result for result in results if '.log' in result]
        filepaths.sort()

        if GetLogNodeFiles == True:
            self.SCPLogs(ssh, filepaths)
        elif GetLogNodeFiles == False: 
            filepaths_filtered = self.FilterFilepaths(filepaths, get_daybefore_logs)
            self.SCPLogs(ssh, filepaths_filtered)
        ssh.close()
        
    def LastLogsDayBefore(self):    #If starttime is midnight (0:00) -> get last logs of day before
        starttime = self.StrToTime()[0]
        if starttime == datetime.time(0,0):
            self.startdate = self.startdate - datetime.timedelta(days=1)
            get_daybefore_logs = True
        else:
            self.startdate = self.startdate
            get_daybefore_logs = False
        return get_daybefore_logs
        
    def ConnectServer(self):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.ipaddress , 22, self.username , self.password)
            get.UpdateProgress('reset import')
        except:
            messagebox.showerror(title='Error', message='Connection interrupted.')
            self.ResetButton()
            raise
        return ssh
    
    def ConnectToKVCT(self, results):
        if 'Cannot connect' in results[0]:
            messagebox.showinfo(title='Warning', message='Cannot connect to kvct. Downloading LogNode files (may take a while).')
            GetLogNodeFiles = True
        else:
            GetLogNodeFiles = False
        return GetLogNodeFiles
    
    def SCPLogs(self, ssh, filepaths):        
        with SCPClient(ssh.get_transport(), sanitize=lambda x: x) as scp:
            for filepath in filepaths:
                filename = filepath.split('/')[-1].replace('\n','')
                scp.get(remote_path=filepath, local_path=self.output)
                local_file = os.path.join(self.output, filename)
                size = int((os.stat(local_file).st_size)/1000)
                self.Page1.tree.insert('', 'end', values=[filename,size,self.output])
                    
                get.UpdateProgress(100/len(filepaths))
        
        return
            
    def FilterFilepaths(self, filepaths, get_daybefore_logs):
        if get_daybefore_logs == True:
            filepaths_filtered = self.GetLastLogsOfPrevDay(filepaths)
        elif get_daybefore_logs == False:
            filepaths_filtered = self.FilterByTimes(filepaths)
        return filepaths_filtered 
    
    def GetLastLogsOfPrevDay(self, filepaths):            
        # update startdatetime and enddatetime
        self.startdate = self.startdate + datetime.timedelta(days=1)
        filepaths_filtered = self.FilterByTimes(filepaths)
        return filepaths_filtered      
    
    def FilterByTimes(self, filepaths):
        # Get times between startime and endtime + last logs right before startime
        startdatetime, enddatetime = self.CombineDateAndTime()
        
        filepaths_filtered_idx = []
        for idx, filepath in enumerate(filepaths):
            filename = filepath.split('/')[-1].replace('\n','')
            filedatetime = '-'.join(filename.split('-')[:4])
            filedatetime  = datetime.datetime.strptime(filedatetime, '%Y-%m-%d-%H%M%S')
            if startdatetime <= filedatetime <= enddatetime:
                filepaths_filtered_idx.append(idx)
        
        # Check if log files exist for given time period
        self.LogsFound(filepaths_filtered_idx)
        
        # Get last log before startdatetime
        first_log_idx = filepaths_filtered_idx[0]
        prev_logs = list(range(first_log_idx-3, first_log_idx)) #get previous 3 logs (kvct, pet_recon, and sys)
        [filepaths_filtered_idx.insert(0, log) for log in prev_logs]
        
        filepaths_filtered = [filepaths[idx] for idx in filepaths_filtered_idx]
        return filepaths_filtered 
    
    def LogsFound(self, filepaths_filtered_idx):
        if not filepaths_filtered_idx:
            messagebox.showinfo(message='No logs found in machine for given dates and times.')
            self.ResetButton()
            raise
        return
    
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