# -*- coding: utf-8 -*-
"""
Created on Tue Oct 20 13:42:34 2020

@author: btierra
"""
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import datetime
import json
import InterlockDataframesSubfunctions as sub

def GetEntries(filenames):    
    # Find entries of interest
    find_keys = ['is active', 'is inactive', 'is clear', 'Set HV ', 'State machine', 'State set', 'received command', 
                 'State transition', 'Top relevant interlock', 'BEL is open', 'Updating gantry speed RPM']

    # Read log files.
    system, endpoints, entries  = ([] for i in range(3))
    for file in filenames:
        if '-log-' in file: # read compiled log file from gateway
            system_tmp, endpoints_tmp, entries_tmp = sub.ReadLogs(file, find_keys)
        else:
            system_tmp, endpoints_tmp, entries_tmp = sub.ReadNodeLogs(file, find_keys)
        [system.append(system_tmp[i]) for i in range(0, len(system_tmp))]
        [endpoints.append(endpoints_tmp[i]) for i in range(0, len(endpoints_tmp))]
        [entries.append(entries_tmp[i]) for i in range(0, len(entries_tmp))]
    
    # Find system model
    if all(i == system[0] for i in system): # checks all log files are from the same system
        try:
            system_model = system[0]    
        except:
            system_model = 'Unknown' # if no system are found 
        
    # Create dataframe of all entries and endpoints
    columns = ['SW Version', 'Mode', 'Date', 'Time', 'Node', 'Description']
    
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
            else:
                mode = 'Unknown'
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
    
        kvct_df = NodeInterlocks(kvct_log, sys_log, endpoints_df)
    else:
        kvct_df = pd.DataFrame()
    
    if any(entries_df['Node'] == 'PR') == True:
        recon_log = entries_df.loc[entries_df['Node'] == 'PR']
        recon_log.drop(columns='Node', inplace = True)
        recon_log.name = 'recon_log'
        
        recon_df = NodeInterlocks(recon_log, sys_log, endpoints_df)
    else:
        recon_df = pd.DataFrame()
        
    return(system_model, kvct_df, recon_df)
    
def NodeInterlocks(node_log, sys_log, endpoints):
# Get all Interlocks 
    node_interlocks = node_log.loc[(node_log['Description'].str.contains('Interlock |KV.Error'))].reset_index(drop=True)
    
    # Group node (KV/PR) entries and endpoints
    if node_log.name == 'kvct_log':
        global kvct_HV_status, BEL_open
        
        kvct_HV_status = node_log.loc[(node_log['Description'].str.contains('Set HV '))].reset_index(drop=True)
        BEL_open = node_log.loc[(node_log['Description'].str.contains('BEL is open'))].reset_index(drop=True)
        machine_state = node_log.loc[(node_log['Description'].str.contains('State machine'))].reset_index(drop=True)
        node_state = node_log.loc[(node_log['Description'].str.contains('State set'))].reset_index(drop=True)
        received_command =  node_log.loc[(node_log['Description'].str.contains('received command'))].reset_index(drop=True)
        user_command = node_log.loc[(node_log['Description'].str.contains('Received command|Got command'))].reset_index(drop=True)
        
        node_endpoints = endpoints[endpoints['Node'] == 'KV']
        node_endpoints.drop(columns='Node', inplace = True)
    
    elif node_log.name == 'recon_log':
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
        sys_endpoints = pd.DataFrame()     
        
    # Construct node_df 
    # Get node interlocks active vs inactive
    node_df = find_interlocks(node_interlocks)
    
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
    for idx, descr in enumerate(received_command['Description']):
        if '-' in descr:
            received_command.loc[idx, 'Description'] = descr.split(':')[0].split(' ' )[1]
        else:
            received_command.loc[idx, 'Description'] = descr.split(':')[0]
    node_df['Last command received (before active)'] = sub.find_last_entry(node_df, node_df['Active Time'], received_command)
    node_df['Last command received (before inactive)'] = sub.find_last_entry(node_df, node_df['Inactive Time'], received_command)
    
    # Last user command recerived before activer interlock
    user_command['Description'] = [descr.split("command")[-1] for descr in user_command['Description']]
    node_df['Last user command received (before active)'] = sub.find_last_entry(node_df, node_df['Active Time'], user_command)
    node_df['Last user command received (before inactive)'] = sub.find_last_entry(node_df, node_df['Inactive Time'], user_command)
    
    # last user action 
    sys_user_action['Description'] = ["***" + description.split(" = ")[1].split(" ")[0] for description in sys_user_action['Description']]
    node_df['Last user input'] = sub.find_last_entry(node_df, node_df['Active Time'], sys_user_action)
    
    # BEL open 
    if 'BEL_open' in globals():
        BEL_open['Description'] = [datetime.datetime.combine(date, bel_time) for date, bel_time in zip(BEL_open['Date'], BEL_open['Time'])]
        node_df['BEL Open'] = sub.find_last_entry(node_df, node_df['Active Time'], BEL_open)
    else:
        node_df['BEL Open'] = ''
    
    # Sysnode start time before active interlock
    if sys_endpoints.empty == False:
        sys_endpoints['Description'] = [datetime.datetime.combine(date, sys_time) for date,sys_time in zip(sys_endpoints['Date'], sys_endpoints['Time'])]
        node_df['Sysnode Restart'] = sub.find_last_entry(node_df, node_df['Active Time'], sys_endpoints)
    else:
        node_df['Sysnode Restart'] = '' 
    
    # sysnode state (transition state)
    sys_state_transition['Description'] = [descr.split(" to ")[1].split(" ")[0] for descr in sys_state_transition['Description']]
    node_df['Sysnode State'] = sub.find_last_entry(node_df, node_df['Active Time'], sys_state_transition)
    
    # add relevant sys interlocks that occur right before kvct interlock is active
    node_df = sub.sys_interlocks_before(node_df, sys_relevant_interlock)
    
    # add relevant sys interlocks that occur while kvct interlock is active 
    node_df = sub.sys_interlocks_during(node_df, sys_relevant_interlock)

    # Gantry speed
    gantry_speed['Description'] = [descr.split("=")[-1] for descr in gantry_speed['Description']]
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
    for idx, row in node_df.iterrows():
        if 'LOG' in row['Interlock Number'] or 'NODE' in row['Interlock Number']:
            node_df.loc[idx, 6:] = ''
    
    return(node_df)
    
def find_interlocks(node_interlocks):
    #combine date and time columns
    all_interlocks = node_interlocks.copy()
    datetimes = []
    for idx in range(len(all_interlocks)):
        date = all_interlocks.loc[idx, 'Date']
        interlock_time = all_interlocks.loc[idx, 'Time']
        datetimes.append(datetime.datetime.combine(date,interlock_time))
    all_interlocks.insert(0, 'Datetime', datetimes)
    all_interlocks.drop('Date', axis=1, inplace=True)
    all_interlocks.drop('Time', axis=1, inplace=True)
    all_interlocks.sort_values('Datetime', ascending=True, inplace=True)
        
    active_interlocks = all_interlocks.loc[(all_interlocks['Description'].str.contains('is active|KV.Error'))]
    active_interlocks.reset_index(drop=True, inplace=True)
    inactive_interlocks = all_interlocks.loc[(all_interlocks['Description'].str.contains('is inactive|is clear'))]
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
    
    # Create new dataframe
    interlocks_df = pd.DataFrame({'SW Version':swver, 'Mode':mode, 'Interlock Number':interlock_names,
                            'Active Time':active_times, 'Inactive Time':inactive_times})
    interlocks_df.sort_values('Active Time', ascending=True, inplace=True)
    return(interlocks_df)