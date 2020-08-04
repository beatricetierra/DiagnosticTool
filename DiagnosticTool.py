# -*- coding: utf-8 -*-
"""
Created on Wed May 20 17:58:42 2020

@author: btierra
"""

import os
import pandas as pd
import datetime
import InterlockDateFrame as idf
import DiagnosticTool_Analysis as dta

def DeleteFiles(folderpath):
    for root, dirs, files in os.walk(folderpath):
        for file in files:
            if '-log-' not in file:
                if 'kvct' not in file:
                    if 'pet' not in file:
                        if 'sysnode' not in file:
                            os.remove(os.path.join(root, file))
    return
    
def GetFiles(folderpath):
    acceptable_files = ['-log-','-kvct-','-pet_recon-','-sysnode-']
    filenames = []  

    for root, dirs, files in os.walk(folderpath):
        for word in acceptable_files:
            for file in files:
                if word in file:   
                    filenames.append(os.path.join(root, file))
    return(filenames)

def ReadLogs(file, find_keys):
    system, start_entries, end_entries, entries  = ([] for i in range(4))
    
    with open(file, encoding="cp437") as log:
        first_line = log.readline()     #read first line and find system (A1,A2,A4, or B1)
        sys = first_line.split(" ")
        system.append(sys[6])
        parse_idx = [3,4,7,10]  #only keep date, time, node, and description
        for line in log:
            if 'kvct connected' in line or 'pet_recon connected' in line:   # entry for start of node
                start = line.split(" ", 9)
                start_entries.append([start[i] for i in [0,1,-1]]) #only keep date, time, and description
            elif 'Signal 15' in line: # entry for end of node
                end = line.split(" ", 9) 
                end_entries.append([end[i] for i in [0,1,-1]]) #only keep date, time, and description
            elif 'KV' in line or 'PR' in line or 'SY' in line:
                if 'SysNode' in line and '***' in line:
                    if ('TCP' in line or 'CCP' in line) and 'MV' not in line:
                        entry = line.split(" ", 10)
                        entries.append([entry[i] for i in parse_idx]) 
                else: 
                    for word in find_keys:
                        if word in line:
                            entry = line.split(" ", 10)
                            entries.append([entry[i] for i in parse_idx])
    return(system, start_entries, end_entries, entries)

def ReadNodeLogs(file, find_keys):
    system, start_entries, end_entries, entries  = ([] for i in range(4))
    
    with open(file) as log:
        first_line = log.readline()
        sys = first_line.split(" ")
        system.append(sys[3])
        for line in log:
            if 'command: set to load_config' in line: #entry for start of node
                start = line.split(" ", 5)
                start_entries.append([start[i] for i in [0,1,4]])    #only keep date, time, and node
            elif 'Signal 15' in line: #entry for end of node
                end = line.split(" ",5)
                end_entries.append([end[i] for i in [0,1,4]]) #only keep date, time, and node
            elif '***' in line:
                if ('TCP' in line or 'CCP' in line) and 'MV' not in line:
                    entry = line.split(" ", 7)
                    entries.append([entry[i] for i in [0,1,4,7]])
            else:
                for word in find_keys:
                    if word in line:
                        entry = line.split(" ", 7)
                        entries.append([entry[i] for i in [0,1,4,7]])
    return(system, start_entries, end_entries, entries)

def GetEntries(filenames):    
    # Find entries of interest
    acceptable_files = ['kvct','pet','sysnode']
    find_keys = ['is active', 'is inactive', 'Set HV', 'State machine', 'State set', 'received command', 'State transition', 'Top relevant interlock', 'Received command']
    
    files = []

    # filter out log files
    # accepts all -log- files and only kvct, pet_recon, and sysnode files ending in '000'
    for file in filenames:
        if '-log-' in file:
            files.append(file)
        for word in acceptable_files:
            if word in file and '000' in file:
                files.append(file)
    
    # Read log files.
    system, start_entries, end_entries, entries  = ([] for i in range(4))
    
    for file in files:
        if '-log-' in file: # read compiled log file from gateway
            system_tmp, start_entries_tmp, end_entries_tmp, entries_tmp = ReadLogs(file, find_keys)
        else:
            system_tmp, start_entries_tmp, end_entries_tmp, entries_tmp = ReadNodeLogs(file, find_keys)
        [system.append(system_tmp[i]) for i in range(0, len(system_tmp))]
        [start_entries.append(start_entries_tmp[i]) for i in range(0, len(start_entries_tmp))]
        [end_entries.append(end_entries_tmp[i]) for i in range(0, len(end_entries_tmp))]
        [entries.append(entries_tmp[i]) for i in range(0, len(entries_tmp))]
            
    # Find system model (check if all log files are from same system)
    if all(i == system[0] for i in system):
        system_model = system[0]
    else:
        system_model = 'Unknown'
        
    # Create dataframe of all entries
    columns = ['Date', 'Time', 'Node', 'Description']
    
    entries_df = pd.DataFrame(entries, columns=columns)
    entries_df['Date'] = pd.to_datetime(entries_df['Date']).dt.date #convert to datetime format
    entries_df['Time'] = pd.to_datetime(entries_df['Time']).dt.time
    
    nodes = ['KV', 'PR', 'SY']  #only keep kvct, pet_recon, and sysnode entries
    entries_df = entries_df.loc[entries_df['Node'].isin(nodes)]
    entries_df.reset_index(inplace=True, drop=True)
    
    # Find kvct and pet start and end times
    start_times = pd.DataFrame(start_entries, columns = columns[0:3])
    start_times['Date'] = pd.to_datetime(start_times['Date']).dt.date #convert to datetime format
    start_times['Time'] = pd.to_datetime(start_times['Time']).dt.time
    
    end_times = pd.DataFrame(end_entries, columns = columns[0:3])
    end_times['Date'] = pd.to_datetime(end_times['Date']).dt.date #convert to datetime format
    end_times['Time'] = pd.to_datetime(end_times['Time']).dt.time
    
    kvct_start_times = []
    kvct_end_times = []
    pet_start_times = []
    pet_end_times = []
    
    for idx, (start, end) in enumerate(zip(start_times['Node'], end_times['Node'])):
        if 'kvct' in start or 'KV' in start:
            time = datetime.datetime.combine(start_times['Date'][idx], start_times['Time'][idx])
            kvct_start_times.append(time)
        if 'kvct' in end or 'KV' in end:
            time = datetime.datetime.combine(end_times['Date'][idx], end_times['Time'][idx])
            kvct_end_times.append(time)
        if 'pet' in start or 'PR' in start:
            time = datetime.datetime.combine(start_times['Date'][idx], start_times['Time'][idx])
            pet_start_times.append(time)
        if 'pet' in start or 'PR' in start:
            time = datetime.datetime.combine(end_times['Date'][idx], end_times['Time'][idx])
            pet_end_times.append(time)

    # Seperate entries by nodes
    sys_log = entries_df.loc[entries_df['Node'] == 'SY']
    sys_log.drop(columns='Node', inplace = True)
    
    kvct_log = entries_df.loc[entries_df['Node'] == 'KV']
    kvct_log.drop(columns='Node', inplace = True)
    kvct_log.name = 'kvct_log'
    
    kvct_df = idf.NodeInterlockDf(kvct_log, sys_log, kvct_start_times, kvct_end_times)

    try:
        pet_log = entries_df.loc[entries_df['Node'] == 'PR']
        pet_log.drop(columns='Node', inplace = True)
        pet_log.name = 'pet_log'
        
        pet_interlocks = idf.NodeInterlockDf(pet_log, sys_log, pet_start_times, pet_end_times)
    except:
        pet_interlocks = pd.DataFrame()
    
    return(system_model, kvct_df, pet_interlocks)
    
def FilterEntries(kvct_interlocks):    
    # Remove Expected, Startup, and Shutdown Interlocks
    kvct_filtered, kvct_filtered_out = dta.filter_expected(kvct_interlocks)
    
    return(kvct_filtered, kvct_filtered_out)
    
def Analysis(kvct_filtered, kvct_filtered_out, pet_interlocks):    
    kvct_analysis = dta.analysis(kvct_filtered)
    sessions, kvct_unfiltered_analysis = dta.analysis_expected(kvct_filtered_out)
    
    try:    
        pet_analysis = dta.analysis(pet_interlocks)
    except:
        pet_analysis = pd.DataFrame()
    return(kvct_analysis, sessions, kvct_unfiltered_analysis, pet_analysis)