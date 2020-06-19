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
    find_keys = ['is active', 'is inactive', 'Set HV', 'State machine', 'State set', 'received command', 'State transition', 'Top relevant interlock', 'Received command']
    
    entries = [] 
    start_entries = []
    
    for file in filenames:
        if '-log-' in file: # read compiled log file from gateway
            with open(file, encoding="cp437") as log:
                parse_idx = [3,4,7,10]  #only keep date, time, node, and description
                for line in log:
                    if 'kvct connected' in line or 'pet_recon connected' in line:   # entry for start of node
                        start = (line.split(" ", 9))
                        start_entries.append([start[i] for i in [0,1,-1]]) #only keep date, time, and description
                    if 'KV' in line or 'PR' in line or 'SY' in line:
                        if 'SysNode' in line and '***' in line:
                            if ('TCP' in line or 'CCP' in line) and 'MV' not in line:
                                entry = line.split(" ", 10)
                                entries.append([entry[i] for i in parse_idx]) 
                        else: 
                            for word in find_keys:
                                if word in line:
                                    entry = line.split(" ", 10)
                                    entries.append([entry[i] for i in parse_idx])
                                    
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
    pet_interlocks = idf.pet_df(pet_log, sys_log, pet_start_times)
    
    return(kvct_interlocks, pet_interlocks)
    
def FilterEntries(kvct_interlocks):    
    # Remove Expected, Startup, and Shutdown Interlocks
    kvct_filtered, kvct_filtered_out = dta.filter_expected(kvct_interlocks, kvct_interlocks['Time from Node Start'], '0:5:0.0')
    
    return(kvct_filtered, kvct_filtered_out)
    
def Analysis(kvct_filtered, kvct_filtered_out, pet_interlocks):    
    kvct_analysis = dta.analysis(kvct_filtered)
    kvct_unfiltered_analysis = dta.analysis_expected(kvct_filtered_out)
    
    pet_analysis = dta.analysis(pet_interlocks)
    
    return(kvct_analysis, kvct_unfiltered_analysis, pet_analysis)

