# -*- coding: utf-8 -*-
"""
Created on Thu Oct 15 13:57:25 2020

@author: btierra
"""
import os
import pandas as pd
import datetime
import threading
import time
import DiagnosticToolFilter as dtf
import DiagnosticToolAnalysis as dta
import DiagnosticToolSubfunctions as dts 


class ThreadedTasks(threading.Thread):
    def __init__(self, progress, root):
        threading.Thread.__init__(self)
        ThreadedTasks.progress = progress
        ThreadedTasks.root = root 
        
    def UpdateProgress(perc):
        ThreadedTasks.progress['value'] += perc
        time.sleep(0.1)
        ThreadedTasks.root.update_idletasks()
        
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
                system_tmp, endpoints_tmp, entries_tmp = ThreadedTasks.ReadLogs(file, find_keys)
            else:
                system_tmp, endpoints_tmp, entries_tmp = ThreadedTasks.ReadNodeLogs(file, find_keys)
            [system.append(system_tmp[i]) for i in range(0, len(system_tmp))]
            [endpoints.append(endpoints_tmp[i]) for i in range(0, len(endpoints_tmp))]
            [entries.append(entries_tmp[i]) for i in range(0, len(entries_tmp))]
            
        ThreadedTasks.UpdateProgress(2)     #Update Progressbar
            
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
    
        kvct_df = ThreadedTasks.NodeInterlocks(kvct_log, sys_log, endpoints_df)
        
    
        try:
            recon_log = entries_df.loc[entries_df['Node'] == 'PR']
            recon_log.drop(columns='Node', inplace = True)
            recon_log.name = 'recon_log'
            
            recon_df = ThreadedTasks.NodeInterlocks(recon_log, sys_log, endpoints_df)
        except:
            recon_df = pd.DataFrame()
            
        return(system_model, kvct_df, recon_df)
        
    def NodeInterlocks(node_log, sys_log, endpoints):
    
         # Find node interlocks
        columns = ['Date', 'Time', 'Description']
        node_interlocks = pd.DataFrame(columns=columns)
        
        for idx, entry in enumerate(node_log['Description']):
            if 'Interlock' in entry:
                node_interlocks = node_interlocks.append(node_log.iloc[idx], ignore_index=True)
    
        # Group node (KV/PR) entries and endpoints
        find_keys = ['Set HV ', 'State machine', 'State set', 'received command', 'Received command', 'BEL is open', 
                     'State transition', 'Top relevant interlock']
        
        machine_state = pd.DataFrame(columns=columns)
        node_state = pd.DataFrame(columns=columns)
        received_command = pd.DataFrame(columns=columns) 
        user_command = pd.DataFrame(columns=columns) 
        
        if node_log.name == 'kvct_log':
            global kvct_HV_status, BEL_open
            
            kvct_HV_status = pd.DataFrame(columns=columns)
            BEL_open = pd.DataFrame(columns=columns)
            
            for idx, entry in enumerate(node_log['Description']):
                if find_keys[0] in entry:
                    kvct_HV_status = kvct_HV_status.append(node_log.iloc[idx], ignore_index=True)
                if find_keys[1] in entry and 'KVCTControl' in entry:
                    machine_state = machine_state.append(node_log.iloc[idx], ignore_index=True)
                if find_keys[2] in entry:
                    node_state = node_state.append(node_log.iloc[idx], ignore_index=True)
                if find_keys[3] in entry:
                    received_command = received_command.append(node_log.iloc[idx], ignore_index=True)
                if find_keys[4] in entry or 'Got command' in entry:
                    user_command = user_command.append(node_log.iloc[idx], ignore_index=True)
                if find_keys[5] in entry:
                    BEL_open = BEL_open.append(node_log.iloc[idx], ignore_index=True)
                    
            node_endpoints = endpoints[endpoints['Node'] == 'KV']
            node_endpoints.drop(columns='Node', inplace = True)
        
        if node_log.name == 'recon_log':
            for idx, entry in enumerate(node_log['Description']):
                if find_keys[1] in entry:
                    machine_state = machine_state.append(node_log.iloc[idx], ignore_index=True)
                if find_keys[2] in entry:
                   node_state = node_state.append(node_log.iloc[idx], ignore_index=True)
                if find_keys[3] in entry:
                    received_command = received_command.append(node_log.iloc[idx], ignore_index=True)
                    
            node_endpoints = endpoints[endpoints['Node'] == 'PR']
            node_endpoints.drop(columns='Node', inplace = True)
                
        #Group sysnode entries and endpoints
        sys_user_action = pd.DataFrame(columns=columns)
        sys_received_command = pd.DataFrame(columns=columns)
        sys_state_transition = pd.DataFrame(columns=columns)
        sys_relevant_interlock = pd.DataFrame(columns=columns)
        
        for idx, entry in enumerate(sys_log['Description']):
            if "***" in entry:
                sys_user_action = sys_user_action.append(sys_log.iloc[idx], ignore_index=True)
            if find_keys[3] in entry or find_keys[2] in entry:
                sys_received_command = sys_received_command.append(sys_log.iloc[idx], ignore_index=True)
            if find_keys[6] in entry:
                sys_state_transition = sys_state_transition.append(sys_log.iloc[idx], ignore_index=True)
            if find_keys[7] in entry:
                sys_relevant_interlock = sys_relevant_interlock.append(sys_log.iloc[idx], ignore_index=True)
                
        sys_endpoints = endpoints[(endpoints['Node'] == 'SY') & (endpoints['Description'] == '------ NODE START ------')]
        sys_endpoints.drop(columns='Node', inplace = True)
        sys_endpoints.reset_index(drop=True, inplace=True)
    
        # Construct node_df 
        # Get node interlocks active vs inactive
        node_df = dts.find_interlocks(node_interlocks)
        ThreadedTasks.UpdateProgress(15)
        
        # Insert node endpoints (start of log, start of node, end of node)
        node_df = dts.find_endpoints(node_df, node_endpoints)
    
        # Time since start/restart of node
        node_df = dts.node_start_delta(node_df)
        ThreadedTasks.UpdateProgress(3)
         
        # Duration of node interlocks
        node_df = dts.interlock_duration(node_df)
        ThreadedTasks.UpdateProgress(3)
    
        # HV status before active/ inactive interlock
        kvct_HV_status['Description'] = [descr.split('Set HV ')[-1] for descr in kvct_HV_status['Description']]
        node_df['HV Status (before active)'] = dts.find_last_entry(node_df, node_df['Active Time'], kvct_HV_status)
        node_df['HV Status (before inactive)'] = dts.find_last_entry(node_df, node_df['Inactive Time'], kvct_HV_status)
        ThreadedTasks.UpdateProgress(3)
        
        # Machine state before active/ inactive interlock
        machine_state['Description'] = [descr.split(": ")[-1].split("\n")[0] for descr in machine_state['Description']]
        node_df['Machine State (before active)'] = dts.find_last_entry(node_df, node_df['Active Time'], machine_state)
        node_df['Machine State (before inactive)'] = dts.find_last_entry(node_df, node_df['Inactive Time'], machine_state)
        ThreadedTasks.UpdateProgress(3)
        
        # Node (kvct/pet) state
        node_state['Description'] = [descr.split(" ")[-1] for descr in node_state['Description']]
        node_df['Node State (before active)'] = dts.find_last_entry(node_df, node_df['Active Time'], node_state)
        node_df['Node State (before inactive)'] = dts.find_last_entry(node_df, node_df['Inactive Time'], node_state)
        ThreadedTasks.UpdateProgress(3)
        
        # last command received before active/ inactive interlock
        for idx, descr in enumerate(received_command['Description']):
            if '-' in descr:
                received_command.loc[idx, 'Description'] = descr.split(':')[0].split(' ' )[1]
            else:
                received_command.loc[idx, 'Description'] = descr.split(':')[0]
        node_df['Last command received (before active)'] = dts.find_last_entry(node_df, node_df['Active Time'], received_command)
        node_df['Last command received (before inactive)'] = dts.find_last_entry(node_df, node_df['Inactive Time'], received_command)
        ThreadedTasks.UpdateProgress(3)
        
        # Last user command recerived before activer interlock
        user_command['Description'] = [descr.split("command")[-1] for descr in user_command['Description']]
        node_df['Last user command received (before active)'] = dts.find_last_entry(node_df, node_df['Active Time'], user_command)
        node_df['Last user command received (before inactive)'] = dts.find_last_entry(node_df, node_df['Inactive Time'], user_command)
        ThreadedTasks.UpdateProgress(3)
        
        # last user action 
        sys_user_action['Description'] = ["***" + description.split(" = ")[1].split(" ")[0] for description in sys_user_action['Description']]
        node_df['Last user input'] = dts.find_last_entry(node_df, node_df['Active Time'], sys_user_action)
        ThreadedTasks.UpdateProgress(3)
        
        # BEL open 
        BEL_open['Description'] = [datetime.datetime.combine(date, time) for date,time in zip(BEL_open['Date'], BEL_open['Time'])]
        node_df['BEL Open'] = dts.find_last_entry(node_df, node_df['Active Time'], BEL_open)
        ThreadedTasks.UpdateProgress(3)
        
        # Sysnode start time before active interlock
        sys_endpoints['Description'] = [datetime.datetime.combine(date, time) for date,time in zip(sys_endpoints['Date'], sys_endpoints['Time'])]
        node_df['Sysnode Restart'] = dts.find_last_entry(node_df, node_df['Active Time'], sys_endpoints)
        ThreadedTasks.UpdateProgress(3)
        
        # sysnode state (transition state)
        sys_state_transition['Description'] = [descr.split(" to ")[1].split(" ")[0] for descr in sys_state_transition['Description']]
        node_df['Sysnode State'] = dts.find_last_entry(node_df, node_df['Active Time'], sys_state_transition)
        ThreadedTasks.UpdateProgress(3)
        
        # add relevant sys interlocks that occur right before kvct interlock is active
        node_df = dts.sys_interlocks_before(node_df, sys_relevant_interlock)
        
        # add relevant sys interlocks that occur while kvct interlock is active 
        node_df = dts.sys_interlocks_during(node_df, sys_relevant_interlock)
        
        # Clean up final kvct_df
        node_df['Date'] = [activetime.date() for activetime in node_df['Active Time']]
        
        columns = ['Date', 'Active Time', 'Inactive Time', 'Interlock Number', 'Time from Node Start (min)', 'Interlock Duration (min)', 'HV Status (before active)', 
                'HV Status (before inactive)', 'BEL Open', 'Machine State (before active)', 'Machine State (before inactive)', 'Node State (before active)',
                'Node State (before inactive)', 'Last command received (before active)', 'Last command received (before inactive)', 
                'Last user command received (before active)', 'Last user command received (before inactive)', 'Last user input', 'Sysnode State', 'Sysnode Restart', 
                'Sysnode Relevant Interlock (before)', 'Sysnode Relevant Interlock (during)']
        
        node_df.sort_values('Active Time', ascending=True, inplace=True)
        node_df = node_df.reindex(columns= columns)
        
        # Save active and inactive times as datetime.time formats
        node_df['Active Time'] = [activetime.time() for activetime in node_df['Active Time']]
        for idx, inactivetime in enumerate(node_df['Inactive Time']):
            if isinstance(inactivetime, str):
                pass
            else:
                node_df.loc[idx,'Inactive Time'] = inactivetime.time()
                
        # Remove all column values for log start, node start, and node end entries
        for idx, row in node_df.iterrows():
            if 'LOG' in row['Interlock Number'] or 'NODE' in row['Interlock Number']:
                node_df.loc[idx, 4:] = ''
        
        return(node_df)
        
    def FilterEntries(kvct_interlocks, recon_interlocks):    
        # Remove Expected, Startup, and Shutdown Interlocks
        kvct_filtered, kvct_unfiltered = dtf.filter_kvct(kvct_interlocks)
        try:
            recon_filtered, recon_unfiltered = dtf.filter_recon(recon_interlocks)
        except:
            recon_filtered, recon_unfiltered = pd.DataFrame(), pd.DataFrame()
        ThreadedTasks.UpdateProgress(3)
        
        return(kvct_filtered, kvct_unfiltered, recon_filtered, recon_unfiltered)
        
    def Analysis(kvct_unfiltered, kvct_filtered, recon_unfiltered, recon_filtered):    
        kvct_filtered_analysis = dta.analysis(kvct_filtered)
        kvct_unfiltered_analysis = dta.analysis_expected(kvct_unfiltered)
        try:    
            recon_filtered_analysis = dta.analysis(recon_filtered)
        except:
            recon_filtered_analysis = pd.DataFrame()
        try:
            recon_unfiltered_analysis = dta.analysis_expected(recon_unfiltered)
        except:
            recon_unfiltered_analysis = pd.DataFrame()
        return(kvct_filtered_analysis, kvct_unfiltered_analysis, recon_filtered_analysis, recon_unfiltered_analysis)
