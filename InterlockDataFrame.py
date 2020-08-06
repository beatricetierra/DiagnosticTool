# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 10:19:41 2020

@author: btierra
"""

import pandas as pd
import DiagnosticTool_Subfunctions as dts 

# Find interlocks and corresponding entry statuses 
def NodeInterlockDf(node_log, sys_log, endpoints):
    
     # Find node interlocks
    columns = ['Date', 'Time', 'Description']
    node_interlocks = pd.DataFrame(columns=columns)
    
    for idx, entry in enumerate(node_log['Description']):
        if 'Interlock' in entry:
            node_interlocks = node_interlocks.append(node_log.iloc[idx], ignore_index=True)

    # Group node (KV/PR) entries
    find_keys = ['Set HV', 'State machine', 'State set', 'received command', 'State transition', 'Top relevant interlock']
    
    machine_state = pd.DataFrame(columns=columns)
    node_state = pd.DataFrame(columns=columns)
    received_command = pd.DataFrame(columns=columns) 
    
    if node_log.name == 'kvct_log':
        global kvct_HV_status 
        
        kvct_HV_status = pd.DataFrame(columns=columns)
        
        for idx, entry in enumerate(node_log['Description']):
            if find_keys[0] in entry:
                kvct_HV_status = kvct_HV_status.append(node_log.iloc[idx], ignore_index=True)
            if find_keys[1] in entry:
                machine_state = machine_state.append(node_log.iloc[idx], ignore_index=True)
            if find_keys[2] in entry:
                node_state = node_state.append(node_log.iloc[idx], ignore_index=True)
            if find_keys[3] in entry:
                received_command = received_command.append(node_log.iloc[idx], ignore_index=True)
    if node_log.name == 'pet_log':
        for idx, entry in enumerate(node_log['Description']):
            if find_keys[1] in entry:
                machine_state = machine_state.append(node_log.iloc[idx], ignore_index=True)
            if find_keys[2] in entry:
               node_state = node_state.append(node_log.iloc[idx], ignore_index=True)
            if find_keys[3] in entry:
                received_command = received_command.append(node_log.iloc[idx], ignore_index=True)
            
    #Group sysnode entries
    sys_user_action = pd.DataFrame(columns=columns)
    sys_received_command = pd.DataFrame(columns=columns)
    sys_state_transition = pd.DataFrame(columns=columns)
    sys_relevant_interlock = pd.DataFrame(columns=columns)
    
    for idx, entry in enumerate(sys_log['Description']):
        if "***" in entry:
            sys_user_action = sys_user_action.append(sys_log.iloc[idx], ignore_index=True)
        if find_keys[3] in entry or find_keys[2] in entry:
            sys_received_command = sys_received_command.append(sys_log.iloc[idx], ignore_index=True)
        if find_keys[4] in entry:
            sys_state_transition = sys_state_transition.append(sys_log.iloc[idx], ignore_index=True)
        if find_keys[5] in entry:
            sys_relevant_interlock = sys_relevant_interlock.append(sys_log.iloc[idx], ignore_index=True)

    # Construct node_df 
    # Get node interlocks active vs inactive
    node_df = dts.find_interlocks(node_interlocks)
    
    # Insert node endpoints (start of log, start of node, end of node)
    node_df = dts.find_endpoints(node_df, endpoints)
    
    # Time since start/restart of node
    node_df = dts.node_start_delta(node_df)
     
    # Duration of node interlocks
    node_df['Interlock Duration'] = dts.interlock_duration(node_df)
    
    # HV status before active/ inactive interlock
    kvct_HV_status['Description'] = [descr.split("\n")[0].split(" ", 1)[1] for descr in kvct_HV_status['Description']]
    node_df['HV last status (before active)'] = dts.find_last_entry(node_df, node_df['Active Time'], kvct_HV_status)
    node_df['HV last status (before inactive)'] = dts.find_last_entry(node_df, node_df['Inactive Time'], kvct_HV_status)
    
    # Machine state before active/ inactive interlock
    machine_state['Description'] = [descr.split(": ")[-1].split("\n")[0] for descr in machine_state['Description']]
    node_df['Machine last state (before active)'] = dts.find_last_entry(node_df, node_df['Active Time'], machine_state)
    node_df['Machine last state (before inactive)'] = dts.find_last_entry(node_df, node_df['Inactive Time'], machine_state)
    
    # Node (kvct/pet) state
    node_state['Description'] = [descr.split(" ")[-1] for descr in node_state['Description']]
    node_df['Node State (before active)'] = dts.find_last_entry(node_df, node_df['Active Time'], node_state)
    node_df['Node State (before inactive)'] = dts.find_last_entry(node_df, node_df['Inactive Time'], node_state)
    
    # last command received before active/ inactive interlock
    received_command['Description'] = [descr.split(":")[0].split(" ", 1)[1] for descr in received_command['Description']]
    node_df['Last command received (before active)'] = dts.find_last_entry(node_df, node_df['Active Time'], received_command)
    node_df['Last command received (before inactive)'] = dts.find_last_entry(node_df, node_df['Inactive Time'], received_command)
    
    # last user action 
    sys_user_action['Description'] = ["***" + description.split(" = ")[1].split(" ")[0] for description in sys_user_action['Description']]
    node_df['Last user input'] = dts.find_last_entry(node_df, node_df['Active Time'], sys_user_action)
    
    # sysnode state (transition state)
    sys_state_transition['Description'] = [descr.split(" to ")[1].split(" ")[0] for descr in sys_state_transition['Description']]
    node_df['Sysnode State'] = dts.find_last_entry(node_df, node_df['Active Time'], sys_state_transition)
    
    # add relevant sys interlocks that occur right before kvct interlock is active
    node_df = dts.sys_interlocks_before(node_df, sys_relevant_interlock)
    
    # add relevant sys interlocks that occur while kvct interlock is active 
    node_df = dts.sys_interlocks_during(node_df, sys_relevant_interlock)
    
    # Clean up final kvct_df
    columns = ['Date','Active Time', 'Inactive Time', 'Interlock Number', 'Time from Node Start', 'Interlock Duration', 'HV last status (before active)', 
            'HV last status (before inactive)', 'Machine last state (before active)', 'Machine last state (before inactive)', 'Node State (before active)',
            'Node State (before inactive)', 'Last command received (before active)', 'Last command received (before inactive)', 'Last user input', 
            'Sysnode State', 'Sysnode Relevant Interlock (before)', 'Sysnode Relevant Interlock (during)']
    
    node_df.sort_values('Date', ascending=True, inplace=True)
    node_df['Date'] = node_df['Date'].dt.date
    node_df = node_df.reindex(columns= columns)
    
    return(node_df)