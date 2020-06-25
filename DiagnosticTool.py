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
import DiagnosticTool_Graphs as dtg

def GetFiles(folderpath):
    filenames = []    
    for root, dirs, files in os.walk(folderpath):
        for file in files:
            filenames.append(os.path.join(root, file))
    return(filenames)

def GetEntries(filenames):
    # Keep only necessary files
    files = []
    acceptable_files = ['-log-','-kvct-','-pet_recon-','-sysnode-']
    for word in acceptable_files:
        for file in filenames:
            if word in file:
                files.append(file)
    
    # Find entries of interest
    find_keys = ['is active', 'is inactive', 'Set HV', 'State machine', 'State set', 'received command', 'State transition', 'Top relevant interlock', 'Received command']
    
    entries = [] 
    start_entries = []
    system = []
    
    for file in files:
        if '-log-' in file: # read compiled log file from gateway
            with open(file, encoding="cp437") as log:
                first_line = log.readline()     #read first line and find system (A1,A2,A4, or B1)
                sys = first_line.split(" ")
                system.append(sys[6])
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
                first_line = log.readline()
                sys = first_line.split(" ")
                system.append(sys[3])
                for i,line in enumerate(log):
                    if i==0:
                        start = line.split(" ", 5)
                        start_entries.append([start[i] for i in [0,1,4]])    #only keep date, time, and node
                    elif '***' in line:
                        if ('TCP' in line or 'CCP' in line) and 'MV' not in line:
                            entry = line.split(" ", 7)
                            entries.append([entry[i] for i in [0,1,4,7]])
                    else:
                        for word in find_keys:
                            if word in line:
                                entry = line.split(" ", 7)
                                entries.append([entry[i] for i in [0,1,4,7]])
    
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
        if 'kvct' in descr or 'KV' in descr:
            time = datetime.datetime.combine(start_times['Date'][idx], start_times['Time'][idx])
            kvct_start_times.append(time)
        if 'pet' in descr or 'PR' in descr:
            time = datetime.datetime.combine(start_times['Date'][idx], start_times['Time'][idx])
            pet_start_times.append(time)
    
    # Seperate entries by nodes
    kvct_log = entries_df.loc[entries_df['Node'] == 'KV']
    kvct_log.drop(columns='Node', inplace = True)
    kvct_log.name = 'kvct_log'
    
    pet_log = entries_df.loc[entries_df['Node'] == 'PR']
    pet_log.drop(columns='Node', inplace = True)
    pet_log.name = 'pet_log'
    
    sys_log = entries_df.loc[entries_df['Node'] == 'SY']
    sys_log.drop(columns='Node', inplace = True)
    
    kvct_df = idf.NodeInterlockDf(kvct_log, sys_log, kvct_start_times)
    pet_interlocks = idf.NodeInterlockDf(pet_log, sys_log, pet_start_times)
    
    return(system_model, kvct_df, pet_interlocks)
    
def FilterEntries(kvct_interlocks):    
    # Remove Expected, Startup, and Shutdown Interlocks
    kvct_filtered, kvct_filtered_out = dta.filter_expected(kvct_interlocks, kvct_interlocks['Time from Node Start'], '0:5:0.0')
    
    return(kvct_filtered, kvct_filtered_out)
    
def Analysis(kvct_filtered, kvct_filtered_out, pet_interlocks):    
    kvct_analysis = dta.analysis(kvct_filtered)
    sessions, kvct_unfiltered_analysis = dta.analysis_expected(kvct_filtered_out)
    
    pet_analysis = dta.analysis(pet_interlocks)
    return(kvct_analysis, sessions, kvct_unfiltered_analysis, pet_analysis)
    
def Graph(kvct_unfiltered_analysis, kvct_filtered):
    dtg.filtered_graphing(kvct_filtered)
    dtg.unfilt_graphing(kvct_unfiltered_analysis)
    return()