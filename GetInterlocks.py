# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 13:42:34 2020

@author: btierra
"""
import pandas as pd
import datetime
import threading
import time
import GetInterlocksSubfunctions as sub

class GetInterlocks(threading.Thread):
    def __init__(self, progress, root):
        threading.Thread.__init__(self)
        GetInterlocks.progress = progress
        GetInterlocks.root = root 
        
    def UpdateProgress(perc):
        GetInterlocks.progress['value'] += perc
        time.sleep(0.1)
        GetInterlocks.root.update_idletasks()
        
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
                system_tmp, endpoints_tmp, entries_tmp = sub.ReadLogs(file, find_keys)
            else:
                system_tmp, endpoints_tmp, entries_tmp = sub.ReadNodeLogs(file, find_keys)
            [system.append(system_tmp[i]) for i in range(0, len(system_tmp))]
            [endpoints.append(endpoints_tmp[i]) for i in range(0, len(endpoints_tmp))]
            [entries.append(entries_tmp[i]) for i in range(0, len(entries_tmp))]
            
        GetInterlocks.UpdateProgress(4)
            
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
    
        # Change endpoint_df descriptions to combine with entries_df
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
        if any(entries_df['Node'] == 'SY') == True:
            sys_log = entries_df.loc[entries_df['Node'] == 'SY']
            sys_log.drop(columns='Node', inplace = True)
        else:
            sys_log = pd.DataFrame()
            
        if any(entries_df['Node'] == 'KV') == True:
            kvct_log = entries_df.loc[entries_df['Node'] == 'KV']
            kvct_log.drop(columns='Node', inplace = True)
            kvct_log.name = 'kvct_log'
        
            kvct_df = GetInterlocks.NodeInterlocks(kvct_log, sys_log, endpoints_df)
        else:
            kvct_df = pd.DataFrame()
        
        if any(entries_df['Node'] == 'PR') == True:
            recon_log = entries_df.loc[entries_df['Node'] == 'PR']
            recon_log.drop(columns='Node', inplace = True)
            recon_log.name = 'recon_log'
            
            recon_df = GetInterlocks.NodeInterlocks(recon_log, sys_log, endpoints_df)
        else:
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
        
        if sys_log.empty == False:
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
        else:
            sys_endpoints = pd.DataFrame()
            
        # Construct node_df 
        # Get node interlocks active vs inactive
        node_df = GetInterlocks.find_interlocks(node_interlocks)
        
        # Insert node endpoints (start of log, start of node, end of node)
        node_df = sub.find_endpoints(node_df, node_endpoints)
    
        # Time since start/restart of node
        node_df = sub.node_start_delta(node_df)
        GetInterlocks.UpdateProgress(3)
         
        # Duration of node interlocks
        node_df = sub.interlock_duration(node_df)
        GetInterlocks.UpdateProgress(3)
    
        # HV status before active/ inactive interlock
        if 'kvct_HV_status' in globals():
            kvct_HV_status['Description'] = [descr.split('Set HV ')[-1] for descr in kvct_HV_status['Description']]
            node_df['HV Status (before active)'] = sub.find_last_entry(node_df, node_df['Active Time'], kvct_HV_status)
            node_df['HV Status (before inactive)'] = sub.find_last_entry(node_df, node_df['Inactive Time'], kvct_HV_status)
        else:
            node_df['HV Status (before active)'] = ''
            node_df['HV Status (before inactive)'] = ''
        GetInterlocks.UpdateProgress(3)
        
        # Machine state before active/ inactive interlock
        machine_state['Description'] = [descr.split(": ")[-1].split("\n")[0] for descr in machine_state['Description']]
        node_df['Machine State (before active)'] = sub.find_last_entry(node_df, node_df['Active Time'], machine_state)
        node_df['Machine State (before inactive)'] = sub.find_last_entry(node_df, node_df['Inactive Time'], machine_state)
        GetInterlocks.UpdateProgress(3)
        
        # Node (kvct/pet) state
        node_state['Description'] = [descr.split(" ")[-1] for descr in node_state['Description']]
        node_df['Node State (before active)'] = sub.find_last_entry(node_df, node_df['Active Time'], node_state)
        node_df['Node State (before inactive)'] = sub.find_last_entry(node_df, node_df['Inactive Time'], node_state)
        GetInterlocks.UpdateProgress(3)
        
        # last command received before active/ inactive interlock
        for idx, descr in enumerate(received_command['Description']):
            if '-' in descr:
                received_command.loc[idx, 'Description'] = descr.split(':')[0].split(' ' )[1]
            else:
                received_command.loc[idx, 'Description'] = descr.split(':')[0]
        node_df['Last command received (before active)'] = sub.find_last_entry(node_df, node_df['Active Time'], received_command)
        node_df['Last command received (before inactive)'] = sub.find_last_entry(node_df, node_df['Inactive Time'], received_command)
        GetInterlocks.UpdateProgress(3)
        
        # Last user command recerived before activer interlock
        user_command['Description'] = [descr.split("command")[-1] for descr in user_command['Description']]
        node_df['Last user command received (before active)'] = sub.find_last_entry(node_df, node_df['Active Time'], user_command)
        node_df['Last user command received (before inactive)'] = sub.find_last_entry(node_df, node_df['Inactive Time'], user_command)
        GetInterlocks.UpdateProgress(3)
        
        # last user action 
        sys_user_action['Description'] = ["***" + description.split(" = ")[1].split(" ")[0] for description in sys_user_action['Description']]
        node_df['Last user input'] = sub.find_last_entry(node_df, node_df['Active Time'], sys_user_action)
        GetInterlocks.UpdateProgress(3)
        
        # BEL open 
        if 'BEL_open' in globals():
            BEL_open['Description'] = [datetime.datetime.combine(date, bel_time) for date, bel_time in zip(BEL_open['Date'], BEL_open['Time'])]
            node_df['BEL Open'] = sub.find_last_entry(node_df, node_df['Active Time'], BEL_open)
        else:
            node_df['BEL Open'] = ''
        GetInterlocks.UpdateProgress(3)
        
        # Sysnode start time before active interlock
        if sys_endpoints.empty == False:
            sys_endpoints['Description'] = [datetime.datetime.combine(date, sys_time) for date,sys_time in zip(sys_endpoints['Date'], sys_endpoints['Time'])]
            node_df['Sysnode Restart'] = sub.find_last_entry(node_df, node_df['Active Time'], sys_endpoints)
        else:
            node_df['Sysnode Restart'] = '' 
        GetInterlocks.UpdateProgress(3)
        
        # sysnode state (transition state)
        sys_state_transition['Description'] = [descr.split(" to ")[1].split(" ")[0] for descr in sys_state_transition['Description']]
        node_df['Sysnode State'] = sub.find_last_entry(node_df, node_df['Active Time'], sys_state_transition)
        GetInterlocks.UpdateProgress(3)
        
        # add relevant sys interlocks that occur right before kvct interlock is active
        node_df = sub.sys_interlocks_before(node_df, sys_relevant_interlock)
        
        # add relevant sys interlocks that occur while kvct interlock is active 
        node_df = sub.sys_interlocks_during(node_df, sys_relevant_interlock)
        
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
        
    def find_interlocks(node_interlocks):
        interlocks_set = []
        interlock_active_name = [] 
        interlock_active_time = [] 
        interlock_inactive_name =[]
        interlock_inactive_time =[]
        
        #find all unique interlocks 
        for interlock in node_interlocks['Description']:
            interlock = interlock.split(" priority")[0].split(" ", 1)[1]
            interlocks_set.append(interlock)
            
        interlocks_set = list(set(interlocks_set))
        
        #sepearte active vs inactive interlock entries (sepearate interlock name and time)
        for idx, interlock_desc in enumerate(node_interlocks['Description']):
            for interlock in interlocks_set:
                if interlock in interlock_desc:
                    if 'is active' in interlock_desc:
                        interlock_active_name.append(interlock)
                        interlock_active_time.append(datetime.datetime.combine(node_interlocks['Date'][idx],\
                                                                               node_interlocks['Time'][idx]))
                    elif 'is inactive' in interlock_desc:
                        interlock_inactive_name.append(interlock)
                        interlock_inactive_time.append(datetime.datetime.combine(node_interlocks['Date'][idx],\
                                                                                 node_interlocks['Time'][idx]))
        GetInterlocks.UpdateProgress(5)
        
        interlocks_df = pd.DataFrame({'Interlock Number': interlock_active_name, 'Active Time': interlock_active_time})
        inactive_df = pd.DataFrame({'Interlock Number': interlock_inactive_name, 'Inactive Time': interlock_inactive_time})
        
        #find closest inactive time to each active time
        interlocks_df['Inactive Time'] = ''*len(interlocks_df)
        
        for i, active_interlock in enumerate(interlocks_df['Interlock Number']):
            instances = []
            active_time = interlocks_df['Active Time'][i]
            for j, inactive_interlock in enumerate(inactive_df['Interlock Number']):
                if active_interlock == inactive_interlock:
                    instances.append(inactive_df['Inactive Time'][j])
            try: 
                nearest_time = sub.nearest(instances, active_time)
                interlocks_df.loc[i,'Inactive Time'] = instances[nearest_time]
            except:
                interlocks_df.loc[i,'Inactive Time'] = "Still Active"
                
        GetInterlocks.UpdateProgress(10)
        interlocks_df.sort_values('Active Time', ascending=True, inplace=True)
        return(interlocks_df)