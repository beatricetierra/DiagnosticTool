# -*- coding: utf-8 -*-
"""
Created on Wed Nov  4 17:03:01 2020

@author: btierra
"""

import sys
import os
import pandas as pd
import requests

import ProcessLogs
import LogstoDataframes
import GetInterlocks
import GetDetails
import CleanUp
import Filter

def ExportExcel(system, date):  
   global kvct_xlsxname, recon_xlsxname
    # Dates to save file under new name each time
   filedate = date.replace('-','')
   
   # KVCT Interlocks
   kvct_xlsxname = folder + '/KvctInterlocks_' + system + '_' + filedate + '.xlsx'
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
   recon_xlsxname = folder + '/ReconInterlocks_' + system + '_' + filedate + '.xlsx'
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
    
def AnalysisReport(filtered_couchinterlocks, recon_filtered):
    global analysis
    # Count unexpected interlocks from kvct and recon 
    dataframes = {'kvct': filtered_couchinterlocks, 'recon': recon_filtered}
    try:
        for key, dataframe in dataframes.items():
            analysis = dataframe.groupby('Interlock Number').count()
            analysis.reset_index(inplace=True)
            analysis = analysis[analysis['Interlock Number'].str.contains('Interlock|KV.Error')] 
            analysis = analysis.iloc[:,:2]
            analysis.columns = ['Interlock Number', 'Count']
            analysis = analysis[analysis.columns[::-1]]
            dataframes[key] = analysis
        
        # Combine and export
        analysis = dataframes['kvct'].append(dataframes['recon'])
    except:
        analysis = pd.DataFrame()
    
def SendSlackMessage(message):
    for user in users:
        # Initialize token
        slack_token = "xoxb-20121787398-1726721349940-Ol0JS6ankCTRqwwZC3eLQq8w"
        channel_id = user
        
        # Send message
        message_data = {
                "token": slack_token,
                "channel": channel_id,
                "text": message
        }
        requests.post(url='https://slack.com/api/chat.postMessage',
                      data=message_data)
    
def SendSlackFiles(kvctfilepath, reconfilepath):
    for user in users:
        # link to files.upload method 
        url = "https://slack.com/api/files.upload" 
        # file data
        file_data = {
                "token": "xoxb-20121787398-1726721349940-Ol0JS6ankCTRqwwZC3eLQq8w",
                "channels": user
        }
        
        kvct_upload = {"file":(kvctfilepath, open(kvctfilepath, 'rb'), 'xlsx')} 
        recon_upload = {"file":(reconfilepath, open(reconfilepath, 'rb'), 'xlsx')} 
        
        requests.post(url, data=file_data, files=kvct_upload)
        requests.post(url, data=file_data, files=recon_upload)

# Setup users that get sent slack message
global users
users = ["UN70M875H", "U2JQVHVLK", "#kvct-alpha-monitor"]
         
# command arugments
folder = sys.argv[1] # second argument of command line      
date = sys.argv[2]
  
# 1. Get dataframes
logtype = 'SeparateNodes' 
files = ProcessLogs.FindLogs(folder)
filenames = ProcessLogs.FilterFiles(files, logtype)
endpoints, entries = ProcessLogs.GetLogEntries(filenames, logtype)
   
system = ProcessLogs.FindSystem(filenames)
entries_per_node, endpoints_per_node = LogstoDataframes.CreateDataframes(entries, endpoints)
   
grouped_entries_per_node = GetInterlocks.BreakdownEntries(entries_per_node)
interlocks_per_node = GetInterlocks.GetInterlocksPerNode(grouped_entries_per_node, endpoints_per_node)
interlocks_per_node = GetInterlocks.InsertKVTubeUsage(grouped_entries_per_node, interlocks_per_node)
   
interlocks_per_node_time_details = GetDetails.AddTimeDetails(interlocks_per_node, endpoints_per_node)
interlocks_per_node_event_details = GetDetails.AddEventDetails(interlocks_per_node_time_details, grouped_entries_per_node)
   
final_dfs = CleanUp.CleanDataframes(interlocks_per_node_event_details)
unfiltered_dfs, filtered_dfs = Filter.FilterExpectedInterlocks(final_dfs)

# 2. Get dataframes per node
kvct_unfiltered = unfiltered_dfs['KV']
kvct_filtered = filtered_dfs['KV']

recon_unfiltered = unfiltered_dfs['PR']
recon_filtered = filtered_dfs['PR']

   
# Export excel files
ExportExcel(system, date)

# Analyze filtered interlocks
AnalysisReport(kvct_filtered, recon_filtered)

# Slack report if unexpected kvct interlocks occur
if analysis.empty:
    message = "No unexpected interlock occured on {sys} on {d}:".format(sys=system, d=date)
    SendSlackMessage(message)
    SendSlackFiles(kvct_xlsxname, recon_xlsxname)
else:
    message = "Unexpected interlocks occured on {sys} on {d}:".format(sys=system, d=date)
    unexpected_interlocks = "\n".join(analysis['Interlock Number'].to_list())
    SendSlackMessage("\n".join([message, unexpected_interlocks]))
    SendSlackFiles(kvct_xlsxname, recon_xlsxname)