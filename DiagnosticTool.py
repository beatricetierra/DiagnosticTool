# -*- coding: utf-8 -*-
"""
Created on Wed May 20 17:58:42 2020

@author: btierra
"""

import os
import csv
import pandas as pd
import InterlockDataFrame as idf
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
        for file in files:
            if '.log' in file:
                for word in acceptable_files:
                    if word in file:   
                        filenames.append(os.path.join(root, file))
    return(filenames)

def GetSWVersion(folderpath):
    filenames = GetFiles(folderpath)
    dates = []
    files = []
    sw_version = []
    key = '* current branch: '
    
    for file in filenames:
        if '-kvct-' in file:
            with open(file) as log:
                for line in log:
                    if key in line:
                        entry = line.split(key)
                        sw_version.append(entry[-1].strip('\n'))
                        dates.append(file.split('\\')[-2])
                        files.append(file.split('\\')[-1])
                    
    sw_list = pd.DataFrame({'Date': dates, 'File': files,  'SW Version': sw_version})
    summary = sw_list.groupby('Date')['SW Version'].apply(lambda x: ','.join(x)).reset_index()
    summary['SW Version'] = [','.join(list(set(summary['SW Version'][i].split(',')))) for i in range(0,len(summary))]
    
    #To Save
    sw_list.to_csv(folderpath+'\sw_list.csv', index=False, sep='\t', quoting=csv.QUOTE_NONE)
    summary.to_csv(folderpath+'\summary.csv', index=False, sep='\t', quoting=csv.QUOTE_NONE)
    return(sw_list, summary) 
    
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
    system, endpoints, entries  = ([] for i in range(3))
    parse_idx = [0,1,4,7] #only keep date, time, node, and desciption
    
    with open(file) as log:
        first_line = log.readline()
        sys = first_line.split(" ")
        system.append(sys[3])    
        for i, line in enumerate(log):
            if i == 0 or 'command: set to load_config' in line or 'Signal 15' in line:
                entry = line.split(" ", 7)
                endpoints.append([entry[i] for i in parse_idx]) 
            if '***' in line:
                if ('TCP' in line or 'CCP' in line) and 'MV' not in line:
                    entry = line.split(" ", 7)
                    entries.append([entry[i] for i in parse_idx])
            else:
                for word in find_keys:
                    if word in line:
                        entry = line.split(" ", 7)
                        entries.append([entry[i] for i in parse_idx])
    return(system, endpoints, entries)

def GetEntries(filenames):    
    # Find entries of interest
    acceptable_files = ['kvct','pet','sysnode']
    find_keys = ['is active', 'is inactive', 'Set HV', 'State machine', 'State set', 'received command', 'State transition', 'Top relevant interlock', 'Received command']
    
    files = []

    # filter out log files
    # accepts all -log- files and only kvct, pet_recon, and sysnode files ending in '000'
    for file in filenames:
        if '.log' in file:
            if '-log-' in file:
                files.append(file)
            for word in acceptable_files:
                if word in file and '000' in file:
                    files.append(file)
    
    # Read log files.
    system, endpoints, entries  = ([] for i in range(3))
    for file in files:
        if '-log-' in file: # read compiled log file from gateway
            system_tmp, endpoints_tmp, entries_tmp = ReadLogs(file, find_keys)
        else:
            system_tmp, endpoints_tmp, entries_tmp = ReadNodeLogs(file, find_keys)
        [system.append(system_tmp[i]) for i in range(0, len(system_tmp))]
        [endpoints.append(endpoints_tmp[i]) for i in range(0, len(endpoints_tmp))]
        [entries.append(entries_tmp[i]) for i in range(0, len(entries_tmp))]
            
    # Find system model (check if all log files are from same system)
    if all(i == system[0] for i in system):
        system_model = system[0]
    else:
        system_model = 'Unknown'
        
    # Create dataframe of all entries and endpoints
    columns = ['Date', 'Time', 'Node', 'Description']
    
    entries_df = pd.DataFrame(entries, columns=columns)
    entries_df['Date'] = pd.to_datetime(entries_df['Date']).dt.date #convert to datetime format
    entries_df['Time'] = pd.to_datetime(entries_df['Time']).dt.time
    
    endpoints_df = pd.DataFrame(endpoints, columns=columns)
    endpoints_df['Date'] = pd.to_datetime(endpoints_df['Date']).dt.date #convert to datetime format
    endpoints_df['Time'] = pd.to_datetime(endpoints_df['Time']).dt.time
    
    # Change endpoint_df descriptions and combine with entries_df
    for i, row in enumerate(endpoints_df['Description']):
        if 'command' in row:
            endpoints_df.loc[i,'Description'] = '------ NODE START ------'
        elif 'Signal' in row:
            endpoints_df.loc[i,'Description'] = '------ NODE END ------'
        else:
            endpoints_df.loc[i,'Description'] = '------ LOG START ------'
            
#    nodes = ['KV', 'PR', 'SY']  #only keep kvct, pet_recon, and sysnode entries
#    entries_df = entries_df.loc[entries_df['Node'].isin(nodes)]
#    entries_df.reset_index(inplace=True, drop=True)    

    # Seperate entries by nodes
    sys_log = entries_df.loc[entries_df['Node'] == 'SY']
    sys_log.drop(columns='Node', inplace = True)
    
    kvct_log = entries_df.loc[entries_df['Node'] == 'KV']
    kvct_log.drop(columns='Node', inplace = True)
    kvct_log.name = 'kvct_log'
    
    kvct_endpoints = endpoints_df.loc[endpoints_df['Node'] == 'KV']
    kvct_endpoints.drop(columns='Node', inplace = True)

    kvct_df = idf.NodeInterlockDf(kvct_log, sys_log, kvct_endpoints)

    try:
        pet_log = entries_df.loc[entries_df['Node'] == 'PR']
        pet_log.drop(columns='Node', inplace = True)
        pet_log.name = 'pet_log'
        
        pet_endpoints = endpoints_df.loc[endpoints_df['Node'] == 'PR']
        pet_endpoints.drop(columns='Node', inplace = True)
    
        pet_interlocks = idf.NodeInterlockDf(pet_log, sys_log, pet_endpoints)
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