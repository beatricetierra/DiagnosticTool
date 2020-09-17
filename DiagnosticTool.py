# -*- coding: utf-8 -*-
"""
Created on Wed May 20 17:58:42 2020

@author: btierra
"""

import os
import csv
import pandas as pd
import InterlockDataFrame as idf
import DiagnosticTool_Filter as dtf
import DiagnosticTool_Analysis as dta

def DeleteFiles(folderpath):
    for root, dirs, files in os.walk(folderpath):
        for file in files:
            if '.log' not in file:
                os.remove(os.path.join(root, file))
            elif 'kvct' not in file:
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
    system, endpoints, entries  = ([] for i in range(3))
    # read whole file as one large string
    lines = []
    with open(file) as log:
        first_line = log.readline()
        sys = first_line.split(" ")
        system.append(sys[6])    
        for line in log:
            try:
                node = line.split(' ', 8)[7]
                if node == 'KV' or node == 'PR' or node == 'SY':
                    lines.append(line)
            except:
                pass
    # find entries of interest
    parse_idx = [3,4,7,10] #only keep date, time, node, and desciption
    for i, line in enumerate(lines):
        if 'Configuring log file:' in line or 'Operating mode' in line or 'set to load_config' in line or 'Signal 15' in line:
            entry = line.split(" ", 10)
            endpoints.append([entry[i] for i in parse_idx]) 
        if '***' in line:
            if ('TCP' in line or 'CCP' in line) and 'MV' not in line:
                entry = line.split(" ", 10)
                entries.append([entry[i] for i in parse_idx])
        if 'Received command' in line:
            if 'set_state' in line:
                next_entries = lines[i+1:i+10]
                possible_entries = []
                for next_entry in next_entries:
                    if 'Got command set state' in next_entry:
                        possible_entries.append(next_entry)
                        entry = possible_entries[0].split(" ", 10)
                        entries.append([entry[i] for i in parse_idx])
            else:
                entry = line.split(" ", 10)
                entries.append([entry[i] for i in parse_idx])        
        else:
            for word in find_keys:
                if word in line:
                    entry = line.split(" ", 10)
                    entries.append([entry[i] for i in parse_idx])
    return(system, endpoints, entries)

def ReadNodeLogs(file, find_keys):
    system, endpoints, entries  = ([] for i in range(3))
    
    # read whole file as one large string
    with open(file) as log:
        first_line = log.readline()
        sys = first_line.split(" ")
        system.append(sys[3])    
        file = log.read().split('\n\n')
        if len(file) > 1:
            del file[1:]
    
    # break each line into another element of list
    for f in file:
        lines = [line for line in f.split('\n')]

    # find entries of interest
    parse_idx = [0,1,4,7] #only keep date, time, node, and desciption
    for i, line in enumerate(lines):
        if i == 0 or 'Operating mode' in line or 'command: set to load_config' in line or 'Signal 15' in line:
            entry = line.split(" ", 7)
            endpoints.append([entry[i] for i in parse_idx]) 
        if '***' in line:
            if ('TCP' in line or 'CCP' in line) and 'MV' not in line:
                entry = line.split(" ", 7)
                entries.append([entry[i] for i in parse_idx])
        if 'Received command' in line:
            if 'set_state' in line:
                next_entries = lines[i+1:i+10]
                possible_entries = []
                for next_entry in next_entries:
                    if 'Got command set state' in next_entry:
                        possible_entries.append(next_entry)
                        entry = possible_entries[0].split(" ", 7)
                        entries.append([entry[i] for i in parse_idx])
            else:
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
    find_keys = ['is active', 'is inactive', 'Set HV ', 'State machine', 'State set', 'received command', 
                 'State transition', 'Top relevant interlock', 'BEL is open']
    
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
        elif 'Log' in row or 'log' in row:
            operating_mode = endpoints_df.loc[i+1,'Description']
            if 'clinical' in operating_mode:
                mode = 'Clinical'
            elif 'service' in operating_mode:
                mode = 'Service'
            elif 'maintenance' in operating_mode:
                mode = 'Maintenance' 
            endpoints_df.loc[i,'Description'] = '------ LOG START (' + mode +') ------'
    endpoints_df = endpoints_df[~endpoints_df['Description'].str.contains("Operating")]
    
    # Seperate entries by nodes
    sys_log = entries_df.loc[entries_df['Node'] == 'SY']
    sys_log.drop(columns='Node', inplace = True)
    
    kvct_log = entries_df.loc[entries_df['Node'] == 'KV']
    kvct_log.drop(columns='Node', inplace = True)
    kvct_log.name = 'kvct_log'

    kvct_df = idf.NodeInterlocks(kvct_log, sys_log, endpoints_df)

    try:
        recon_log = entries_df.loc[entries_df['Node'] == 'PR']
        recon_log.drop(columns='Node', inplace = True)
        recon_log.name = 'recon_log'
        
        recon_df = idf.NodeInterlocks(recon_log, sys_log, endpoints_df)
    except:
        recon_df = pd.DataFrame()
    
    return(system_model, kvct_df, recon_df)
    
def FilterEntries(kvct_interlocks, recon_interlocks):    
    # Remove Expected, Startup, and Shutdown Interlocks
    kvct_filtered, kvct_filtered_out = dtf.filter_kvct(kvct_interlocks)
    try:
        recon_filtered, recon_filtered_out = dtf.filter_recon(recon_interlocks)
    except:
        recon_filtered, recon_filtered_out = pd.DataFrame(), pd.DataFrame()
    
    return(kvct_filtered, kvct_filtered_out, recon_filtered, recon_filtered_out)
    
def Analysis(kvct_filtered, kvct_filtered_out, recon_filtered, recon_filtered_out):    
    kvct_analysis = dta.analysis(kvct_filtered)
    kvct_unfiltered_analysis = dta.analysis_expected(kvct_filtered_out)
    try:    
        recon_analysis = dta.analysis(recon_filtered)
    except:
        recon_analysis = pd.DataFrame()
    try:
        recon_unfiltered_analysis = dta.analysis_expected(recon_filtered_out)
    except:
        recon_unfiltered_analysis = pd.DataFrame()
    return(kvct_analysis, kvct_unfiltered_analysis, recon_analysis, recon_unfiltered_analysis)