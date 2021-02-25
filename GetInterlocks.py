# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 13:42:34 2020

@author: btierra
"""
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import threading
import time
import json
import GetInterlocksSubfunctions as sub

class GetInterlocks(threading.Thread):
    def __init__(self, progress, progress_style, root):
        threading.Thread.__init__(self)
        GetInterlocks.progress = progress
        GetInterlocks.setDaemon(self, daemonic=True)
        GetInterlocks.progress_style = progress_style
        GetInterlocks.root = root 
                    
    def UpdateProgress(perc):
        if perc == 'reset import':
            GetInterlocks.progress['value'] = 0
            GetInterlocks.progress_style.configure('text.Horizontal.TProgressbar', 
                    text='Fetching log files...')
        elif perc == 'reset reading':
            GetInterlocks.progress['value'] = 0
            GetInterlocks.progress_style.configure('text.Horizontal.TProgressbar', 
                    text='Reading log files...')
        else:
            GetInterlocks.progress['value'] += perc
            GetInterlocks.progress_style.configure('text.Horizontal.TProgressbar', 
                    text='{:.2f} %'.format(GetInterlocks.progress['value']))
            time.sleep(0.005)
            GetInterlocks.root.update_idletasks()
        return

    def GetEntries(filenames, node):            
        # Find entries of interest
        find_keys = ['is active', 'is inactive', 'is clear', 'Set HV ', 'State machine', 'State set', 'received command', 
                     'State transition', 'Top relevant interlock', 'BEL is open', 'Updating gantry speed RPM']
        
        acceptable_files = ['kvct-000', 'pet_recon-000', 'sysnode-000']
        
        files = []
        # filter out log files
        # accepts all -log- files and only kvct, pet_recon, and sysnode files ending in '000'
        for file in filenames:
            if '.log' in file:
                if node == 1:
                    if '-log-' in file:
                        files.append(file)
                elif node == 2:
                    for acceptable_file in acceptable_files:
                        if acceptable_file in file:
                            files.append(file)
                      
        # Read log files.
        GetInterlocks.UpdateProgress('reset reading')
        system, endpoints, entries  = ([] for i in range(3))
        for file in files:
            if node == 1: # read compiled log file from gateway
                system_tmp, endpoints_tmp, entries_tmp = sub.ReadLogs(file, find_keys, 'LogNode')
            elif node == 2:
                system_tmp, endpoints_tmp, entries_tmp = sub.ReadLogs(file, find_keys, 'SeparateNodes')
            [system.append(system_tmp[i]) for i in range(0, len(system_tmp))]
            [endpoints.append(endpoints_tmp[i]) for i in range(0, len(endpoints_tmp))]
            [entries.append(entries_tmp[i]) for i in range(0, len(entries_tmp))]
            GetInterlocks.UpdateProgress(5/len(files))
            
        # Find system model
        if all(i == system[0] for i in system): # checks all log files are from the same system
            try:
                system_model = system[0]    
                system_model = system_model.replace('-a', '').replace('alpha','A')
            except:
                system_model = 'Unknown' # if no system are found 
        else:
            system_model = 'Unknown' # if no system are found 
            
        # Create dataframe of all entries and endpoints
        columns = ['SW Version', 'Mode', 'Date', 'Time', 'Node', 'Description']
    
        entries_df = pd.DataFrame(entries, columns=columns)
        entries_df.insert(0,'Datetime', pd.to_datetime(entries_df['Date'] + ' ' + entries_df['Time']))
        entries_df.drop(columns=['Date', 'Time'], inplace=True)
        entries_df.sort_values('Datetime', ascending=True, inplace=True)
        
        endpoints_df = pd.DataFrame(endpoints, columns=columns)
        endpoints_df.insert(0,'Datetime', pd.to_datetime(endpoints_df['Date'] + ' ' + endpoints_df['Time']))
        endpoints_df.drop(columns=['Date', 'Time'], inplace=True)
        endpoints_df.sort_values('Datetime', ascending=True, inplace=True)
    
        # Change endpoint_df descriptions to combine with entries_df
        log_start = endpoints_df.loc[endpoints_df['Description'].str.contains('Configuring log file')].index.values
        node_start = endpoints_df.loc[endpoints_df['Description'].str.contains('set to load_config')].index.values
        node_end = endpoints_df.loc[endpoints_df['Description'].str.contains('Signal 15')].index.values
        
        endpoints_df['Description'][log_start] = '----- LOG START -----'
        endpoints_df['Description'][node_start] = '----- NODE START -----'
        endpoints_df['Description'][node_end] = '----- NODE END -----'
    
        # Seperate entries by nodes
        if any(entries_df['Node'] == 'SY') == True:
            sys_log = entries_df.loc[entries_df['Node'] == 'SY']
            sys_log.drop(columns='Node', inplace = True)
        else:
            sys_log = pd.DataFrame()
    
        if any(entries_df['Node'] == 'KV') == True:
            kvct_log = entries_df.loc[entries_df['Node'] == 'KV']
            kvct_df = GetInterlocks.NodeInterlocks(kvct_log, sys_log, endpoints_df)
        else:
            GetInterlocks.UpdateProgress(47.5)
            kvct_df = pd.DataFrame()
        
        if any(entries_df['Node'] == 'PR') == True:
            recon_log = entries_df.loc[entries_df['Node'] == 'PR']
            recon_df = GetInterlocks.NodeInterlocks(recon_log, sys_log, endpoints_df)
        else:
            recon_df = pd.DataFrame()
            GetInterlocks.UpdateProgress(47.5)
        
        return(system_model, kvct_df, recon_df)
       
    def NodeInterlocks(node_log, sys_log, endpoints):
        node_log.reset_index(inplace=True, drop=True)
        node = node_log.loc[0,'Node']
        
        # Get all Interlocks 
        node_interlocks = node_log.loc[(node_log['Description'].str.contains('Interlock |KV.Error'))].reset_index(drop=True)
        
        # Group node (KV/PR) entries and endpoints
        if node == 'KV':
            global kvct_HV_status, BEL_open
                
            kvct_HV_status = node_log.loc[(node_log['Description'].str.contains('Set HV '))].reset_index(drop=True)
            BEL_open = node_log.loc[(node_log['Description'].str.contains('BEL is open'))].reset_index(drop=True)
            machine_state = node_log.loc[(node_log['Description'].str.contains('State machine'))].reset_index(drop=True)
            node_state = node_log.loc[(node_log['Description'].str.contains('State set'))].reset_index(drop=True)
            received_command =  node_log.loc[(node_log['Description'].str.contains('received command'))].reset_index(drop=True)
            user_command = node_log.loc[(node_log['Description'].str.contains('Received command|Got command|State set'))].reset_index(drop=True)
            
            node_endpoints = endpoints[endpoints['Node'] == 'KV']
            node_endpoints.drop(columns='Node', inplace = True)
        
        elif node == 'PR':
            machine_state = node_log.loc[(node_log['Description'].str.contains('State machine'))].reset_index(drop=True)
            node_state = node_log.loc[(node_log['Description'].str.contains('State set'))].reset_index(drop=True)
            received_command =  node_log.loc[(node_log['Description'].str.contains('received command'))].reset_index(drop=True)
            user_command =node_log.loc[(node_log['Description'].str.contains('Received command'))].reset_index(drop=True)
            
            node_endpoints = endpoints[endpoints['Node'] == 'PR']
            node_endpoints.drop(columns='Node', inplace = True)
        
        if sys_log.empty == False:
            sys_user_action = sys_log.loc[sys_log['Description'].str.contains('\*\*\*')].reset_index(drop=True)
            sys_state_transition = sys_log.loc[sys_log['Description'].str.contains('State transition')].reset_index(drop=True)
            sys_relevant_interlock = sys_log.loc[sys_log['Description'].str.contains('Top relevant interlock')].reset_index(drop=True)
            gantry_speed = sys_log.loc[sys_log['Description'].str.contains('Updating gantry speed RPM')].reset_index(drop=True)
            
            sys_endpoints = endpoints[(endpoints['Node'] == 'SY') & (endpoints['Description'] == '------ NODE START ------')]
            sys_endpoints.drop(columns='Node', inplace = True)
            sys_endpoints.reset_index(drop=True, inplace=True)
        else:
            columns = ['SW Version', 'Mode', 'Datetime', 'Node', 'Description']
            sys_endpoints = pd.DataFrame(columns=columns)     
            sys_user_action = pd.DataFrame(columns=columns)  
            sys_state_transition = pd.DataFrame(columns=columns)  
            sys_relevant_interlock = pd.DataFrame(columns=columns)  
            gantry_speed = pd.DataFrame(columns=columns)  
        # Construct node_df 
        # Get node interlocks active vs inactive
        node_df = GetInterlocks.find_interlocks(node_interlocks)
        
        # Insert node endpoints (start of log, start of node, end of node)
        node_df = sub.find_endpoints(node_df, node_endpoints)
    
        # Time since start/restart of node
        node_df = sub.node_start_delta(node_df)

        # Duration of node interlocks
        node_df = sub.interlock_duration(node_df)
    
        # HV status before active/ inactive interlock
        if 'kvct_HV_status' in globals():
            kvct_HV_status['Description'] = [descr.split('Set HV ')[-1] for descr in kvct_HV_status['Description']]
            node_df['HV Status (before active)'] = sub.find_last_entry(node_df, node_df['Active Time'], kvct_HV_status)
            node_df['HV Status (before inactive)'] = sub.find_last_entry(node_df, node_df['Inactive Time'], kvct_HV_status)
        else:
            node_df['HV Status (before active)'] = ''
            node_df['HV Status (before inactive)'] = ''
        
        # Machine state before active/ inactive interlock
        machine_state['Description'] = [descr.split(": ")[-1].split("\n")[0] for descr in machine_state['Description']]
        node_df['Machine State (before active)'] = sub.find_last_entry(node_df, node_df['Active Time'], machine_state)
        node_df['Machine State (before inactive)'] = sub.find_last_entry(node_df, node_df['Inactive Time'], machine_state)
        
        # Node (kvct/pet) state
        node_state['Description'] = [descr.split(" ")[-1] for descr in node_state['Description']]
        node_df['Node State (before active)'] = sub.find_last_entry(node_df, node_df['Active Time'], node_state)
        node_df['Node State (before inactive)'] = sub.find_last_entry(node_df, node_df['Inactive Time'], node_state)
        
        # last command received before active/ inactive interlock
        received_command['Description'] = [descr.split(':')[0].replace('- ','') for descr in received_command['Description']]
        node_df['Last command received (before active)'] = sub.find_last_entry(node_df, node_df['Active Time'], received_command)
        node_df['Last command received (before inactive)'] = sub.find_last_entry(node_df, node_df['Inactive Time'], received_command)
        
        # Last user command recerived before activer interlock
        user_command['Description'] = [descr.split("command")[-1].replace('-','') for descr in user_command['Description']]
        node_df['Last user command received (before active)'] = sub.find_last_entry(node_df, node_df['Active Time'], user_command)
        node_df['Last user command received (before inactive)'] = sub.find_last_entry(node_df, node_df['Inactive Time'], user_command)
        
        # last user action 
        sys_user_action['Description'] = ["***" + description.split(" = ")[1].split(" ")[0] for description in sys_user_action['Description']]
        node_df['Last user input'] = sub.find_last_entry(node_df, node_df['Active Time'], sys_user_action)
        
        # BEL open 
        # check if in globals in case no kvctlogs in files
        if 'BEL_open' in globals():
            BEL_open['Description'] = BEL_open['Datetime']
            node_df['BEL Open'] = sub.find_last_entry(node_df, node_df['Active Time'], BEL_open)
        else:
            node_df['BEL Open'] = ''
        
        # Sysnode start time before active interlock
        if sys_endpoints.empty == False: 
             sys_endpoints['Description'] = sys_endpoints['Datetime']
             node_df['Sysnode Restart'] = sub.find_last_entry(node_df, node_df['Active Time'], sys_endpoints)
        else:
            node_df['Sysnode Restart'] = '' 

        # sysnode state (transition state)
        sys_state_transition['Description'] = [descr.split(" to ")[1].split(" ")[0] for descr in sys_state_transition['Description']]
        node_df['Sysnode State'] = sub.find_last_entry(node_df, node_df['Active Time'], sys_state_transition)

        # add all relevant sys interlocks that occur before and during interlocks
        node_df = sub.sysnode_relevant_interlocks(node_df, sys_relevant_interlock)
        
        # Gantry speed
        gantry_speed['Description'] = [str(gantry_time) +': Speed ='+ descr.split("=")[-1] for gantry_time, descr in zip(gantry_speed['Datetime'], gantry_speed['Description'])]
        node_df['Gantry Speed (RPM)'] = sub.find_last_entry(node_df, node_df['Active Time'], gantry_speed)
        
        # Clean up final kvct_df
        node_df['Date'] = [activetime.date() for activetime in node_df['Active Time']]
        
        columns = ['Date', 'Active Time', 'Inactive Time', 'SW Version', 'Mode', 'Interlock Number', 'Time from Node Start (min)', 'Interlock Duration (min)', 
               'HV Status (before active)', 'HV Status (before inactive)', 'BEL Open', 'Machine State (before active)', 'Machine State (before inactive)', 
               'Node State (before active)', 'Node State (before inactive)', 'Last command received (before active)', 'Last command received (before inactive)', 
               'Last user command received (before active)', 'Last user command received (before inactive)', 'Last user input', 'Gantry Speed (RPM)', 
               'Sysnode State', 'Sysnode Restart', 'Sysnode Relevant Interlock (before)', 'Sysnode Relevant Interlock (during)']
        
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
        endpoints_idx  = node_df.loc[node_df['Interlock Number'].str.contains('LOG|NODE')].index.values
        node_df.loc[endpoints_idx , columns[6:]] = ''   
        return(node_df)
        
    def find_interlocks(node_interlocks):         
        active_interlocks = node_interlocks.loc[(node_interlocks['Description'].str.contains('is active|KV.Error'))]
        active_interlocks.reset_index(drop=True, inplace=True)
        inactive_interlocks = node_interlocks.loc[(node_interlocks['Description'].str.contains('is inactive|is clear'))]
        inactive_interlocks.reset_index(drop=True, inplace=True)
        
        swver, mode = [], []
        interlock_names, active_times, inactive_times = [], [], [] 
        for idx, active_interlock in enumerate(active_interlocks['Description']):
            if 'is active' in active_interlock:
                swver.append(active_interlocks['SW Version'].iloc[idx])
                mode.append(active_interlocks['Mode'].iloc[idx])
                interlock_name = active_interlock.split(" priority")[0].replace('- ','')
                interlock_names.append(interlock_name)
                
                interlock_active_time = active_interlocks['Datetime'].iloc[idx]
                active_times.append(interlock_active_time)
                interlock_inactive_times = inactive_interlocks.loc[inactive_interlocks['Description'].str.contains(interlock_name.split(':')[0])]['Datetime']
                try:
                    nearest_time = min(interlock_inactive_time for interlock_inactive_time in interlock_inactive_times if interlock_inactive_time > interlock_active_time)
                    inactive_times.append(nearest_time)
                except:
                    inactive_times.append('Still active')
            elif 'KV.Error' in active_interlock:
                info = active_interlock.split("=> ")[1]
                dictionary = json.loads(info)
                interlock_name = dictionary['obj']['code']
                info = str(dictionary['obj']['result'])
                interlock_names.append(interlock_name + ', result:' + info)
                
                active_times.append(active_interlocks['Datetime'].iloc[idx])
                inactive_times.append('')
                swver.append(active_interlocks['SW Version'].iloc[idx])
                mode.append(active_interlocks['Mode'].iloc[idx])
                
            GetInterlocks.UpdateProgress(15/len(active_interlocks))
        
        # Create new dataframe
        interlocks_df = pd.DataFrame({'SW Version':swver, 'Mode':mode, 'Interlock Number':interlock_names,
                                'Active Time':active_times, 'Inactive Time':inactive_times})
        interlocks_df.sort_values('Active Time', ascending=True, inplace=True)
        return(interlocks_df)