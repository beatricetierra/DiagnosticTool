# -*- coding: utf-8 -*-
"""
Created on Wed May 20 17:58:42 2020

@author: btierra
"""

import os
import pandas as pd
import datetime
import InterlockDataFrame as idf
import DiagnosticTool_Analysis as dta

def GetFiles(folderpath):
    filenames = []    
    for root, dirs, files in os.walk(folderpath):
        for file in files:
            filenames.append(os.path.join(root, file))
    return(filenames)

def GetEntries(filenames):
    find_keys = ['is active', 'is inactive', 'Set HV', 'State machine', 'State set', 'received command', 'State transition', 'Top relevant interlock']
    
    entries = [] 
    start_entries = []
    
    for file in filenames:
        if '-log-' in file: # read compiled log file from gateway
            with open(file, encoding="cp437") as log:
                first_line = log.readline()
                if 'A2' in first_line:      #for A2 system
                    parse_idx = [3,4,7,9]
                else:                       #for A4 and B1 system
                    parse_idx = [3,4,7,10]
                for line in log:
                    if 'kvct connected' in line or 'pet_recon connected' in line:   # entry for start of node
                        start = (line.split(" ", 9))
                        start_entries.append([start[i] for i in [0,1,-1]]) #only keep date, time, and description
                    if 'KV' in line or 'PR' in line or 'SY' in line:
                        if 'SysNode' in line and '***' in line:
                            if ('TCP' in line or 'CCP' in line) and 'MV' not in line:
                                entry = line.split(" ", 10)
                                entries.append([entry[i] for i in parse_idx]) #only keep date, time, node, and description
                        else: 
                            for word in find_keys:
                                if word in line:
                                    entry = line.split(" ", 10)
                                    entries.append([entry[i] for i in parse_idx]) #only keep date, time, node, and description
                                    
        else:   # read separate kvct, pet_recon, and sysnode log files 
            with open(file) as log:
                for i,line in enumerate(log):
                    if i==0:
                        start = line.split(" ", 5)
                        start_entries.append([start[i] for i in [0,1,-1]])
                    elif '***' in line:
                        if ('TCP' in line or 'CCP' in line) and 'MV' not in line:
                            entry = line.split(" ", 7)
                            entries.append([entry[i] for i in [0,1,4,7]])
                    else:
                        for word in find_keys:
                            if word in line:
                                entry = line.split(" ", 7)
                                entries.append([entry[i] for i in [0,1,4,7]])            
    
    # Create dataframe of all entries
    columns = ['Date', 'Time', 'Node', 'Description']
    
    entries_df = pd.DataFrame(entries, columns=columns)
    entries_df['Date'] = pd.to_datetime(entries_df['Date']).dt.date #convert to datetime format
    entries_df['Time'] = pd.to_datetime(entries_df['Time']).dt.time
    
    nodes = ['KV', 'PR', 'SY']  #only keep kvct, pet_recon, sysnode and gantry entries
    entries_df = entries_df.loc[entries_df['Node'].isin(nodes)]
    entries_df.reset_index(inplace=True, drop=True)
    
    
    # Find kvct and pet start/ restart times
    start_times = pd.DataFrame(start_entries, columns = columns[0:3])
    start_times['Date'] = pd.to_datetime(start_times['Date']).dt.date #convert to datetime format
    start_times['Time'] = pd.to_datetime(start_times['Time']).dt.time
    
    kvct_start_times = []
    pet_start_times = []
    
    for idx, descr in enumerate(start_times['Node']):
        if 'kvct' in descr:
            time = datetime.datetime.combine(start_times['Date'][idx], start_times['Time'][idx])
            kvct_start_times.append(time)
        if 'pet' in descr:
            time = datetime.datetime.combine(start_times['Date'][idx], start_times['Time'][idx])
            pet_start_times.append(time)
    
    # Seperate entries by nodes
    kvct_log = entries_df.loc[entries_df['Node'] == 'KV']
    kvct_log.drop(columns='Node', inplace = True)
    
    pet_log = entries_df.loc[entries_df['Node'] == 'PR']
    pet_log.drop(columns='Node', inplace = True)
    
    sys_log = entries_df.loc[entries_df['Node'] == 'SY']
    sys_log.drop(columns='Node', inplace = True)
    
    kvct_interlocks = idf.kvct_df(kvct_log, sys_log, kvct_start_times)
    return(kvct_interlocks)
    
def FilteredEntries(interlocks):    
    # Remove Invalid Interlocks
    kvct_filtered, count = dta.filter_expected(interlocks)
    
    # Startup Interlocks (clears interlocks with in 5 minutes of node startup)
    kvct_filtered, startup_count = dta.filter_startup(kvct_filtered, kvct_filtered['Time from KVCT Start'], '0:5:0.0')
    
    # combine expected interlock count
    count['Startup #'] = [startup_count]
    
    return(kvct_filtered, count)
    
def Analysis(filtered_interlocks):    
    analysis_df = dta.analysis(filtered_interlocks)
    return(analysis_df)

