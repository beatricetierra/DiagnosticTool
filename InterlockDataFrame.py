# -*- coding: utf-8 -*-
"""
Created on Fri May 29 10:35:27 2020

@author: btierra
"""
import pandas as pd
import DiagnosticTool_Subfunctions as dts 

# Find kvct interlocks and analysis 
def kvct_df(kvct_log, sys_log, kvct_start_times):
    
    # Find kvct interlocks
    columns = ['Date', 'Time', 'Description']
    kvct_interlocks = pd.DataFrame(columns=columns)
    
    for idx, entry in enumerate(kvct_log['Description']):
        if 'Interlock' in entry:
            kvct_interlocks = kvct_interlocks.append(kvct_log.iloc[idx], ignore_index=True)

    # Group kvct node entries
    find_keys = ['Set HV', 'State machine', 'State set', 'received command', 'State transition', 'Top relevant interlock']
    
    global kvct_HV_status
    
    kvct_HV_status = pd.DataFrame(columns=columns)
    kvct_machine_state = pd.DataFrame(columns=columns)
    kvct_node_state = pd.DataFrame(columns=columns)
    kvct_received_command = pd.DataFrame(columns=columns) 
    
    for idx, entry in enumerate(kvct_log['Description']):
        if find_keys[0] in entry:
            kvct_HV_status = kvct_HV_status.append(kvct_log.iloc[idx], ignore_index=True)
        if find_keys[1] in entry:
            kvct_machine_state = kvct_machine_state.append(kvct_log.iloc[idx], ignore_index=True)
        if find_keys[2] in entry:
            kvct_node_state = kvct_node_state.append(kvct_log.iloc[idx], ignore_index=True)
        if find_keys[3] in entry:
            kvct_received_command = kvct_received_command.append(kvct_log.iloc[idx], ignore_index=True)
            
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

    # Construct kvct_df 
    # Get kvct interlocks active vs inactive
    kvct_df = dts.find_interlocks(kvct_interlocks)
    
    # insert start/restart of kvct node entries
    kvct_df = dts.find_node_start(kvct_df, kvct_start_times)
    
    # Time since start/restart of kvct node
    kvct_df = dts.node_start_delta(kvct_df)
     
    # Duration of kvct interlocks
    kvct_df['Interlock Duration'] = dts.interlock_duration(kvct_df)
    
    # HV status before active/ inactive interlock
    kvct_HV_status['Description'] = [descr.split("\n")[0] for descr in kvct_HV_status['Description']]
    kvct_df['HV last status (before active)'] = dts.find_last_entry(kvct_df, kvct_df['Active Time'], kvct_HV_status)
    kvct_df['HV last status (before inactive)'] = dts.find_last_entry(kvct_df, kvct_df['Inactive Time'], kvct_HV_status)
    
    # Machine state before active/ inactive interlock
    kvct_machine_state['Description'] = [descr.split(": ")[-1].split("\n")[0] for descr in kvct_machine_state['Description']]
    kvct_df['Machine last state (before active)'] = dts.find_last_entry(kvct_df, kvct_df['Active Time'], kvct_machine_state)
    kvct_df['Machine last state (before inactive)'] = dts.find_last_entry(kvct_df, kvct_df['Inactive Time'], kvct_machine_state)
    
    # last command received before active/ inactive interlock
    kvct_received_command['Description'] = [descr.split(":")[0] for descr in kvct_received_command['Description']]
    kvct_df['Last command received (before active)'] = dts.find_last_entry(kvct_df, kvct_df['Active Time'], kvct_received_command)
    kvct_df['Last command received (before inactive)'] = dts.find_last_entry(kvct_df, kvct_df['Inactive Time'], kvct_received_command)
    
    # last user action 
    sys_user_action['Description'] = ["***" + description.split(" = ")[1].split(" ")[0] for description in sys_user_action['Description']]
    kvct_df['Last user input'] = dts.find_last_entry(kvct_df, kvct_df['Active Time'], sys_user_action)
    
    # sysnode state (transition state)
    sys_state_transition['Description'] = [descr.split(" to ")[1].split(" ")[0] for descr in sys_state_transition['Description']]
    kvct_df['Sysnode State'] = dts.find_last_entry(kvct_df, kvct_df['Active Time'], sys_state_transition)
    
    # add relevant sys interlocks that occur right before kvct interlock is active
    kvct_df = dts.sys_interlocks_before(kvct_df, sys_relevant_interlock)
    
    # add relevant sys interlocks that occur while kvct interlock is active 
    kvct_df = dts.sys_interlocks_during(kvct_df, sys_relevant_interlock)
    
    # Clean up final kvct_df
    columns = ['Date','Active Time', 'Inactive Time', 'Interlock Number', 'Time from Node Start', 'Interlock Duration', 'HV last status (before active)', 
            'HV last status (before inactive)', 'Machine last state (before active)', 'Machine last state (before inactive)', 
            'Last command received (before active)', 'Last command received (before inactive)', 'Last user input', 'Sysnode State',
            'Sysnode Relevant Interlock (before)', 'Sysnode Relevant Interlock (during)']
    
    kvct_df.sort_values('Date', ascending=True, inplace=True)
    kvct_df['Date'] = kvct_df['Date'].dt.date
    kvct_df = kvct_df.reindex(columns= columns)
    
    return(kvct_df)
       
# Find pet interlocks and analysis 
def pet_df(pet_log, sys_log, pet_start_times):
    
    # Find pet interlocks
    columns = ['Date', 'Time', 'Seq Num', 'Description']
    pet_interlocks = pd.DataFrame(columns=columns)
    
    for idx, entry in enumerate(pet_log['Description']):
        if 'Interlock' in entry:
            pet_interlocks = pet_interlocks.append(pet_log.iloc[idx], ignore_index=True)

    # Group pet node entries
    find_keys = ['State machine', 'State set', 'Received command', 'State transition', 'Top relevant interlock']
    
    pet_machine_state = pd.DataFrame(columns=columns)
    pet_node_state = pd.DataFrame(columns=columns)
    pet_received_command = pd.DataFrame(columns=columns)
    
    for idx, entry in enumerate(pet_log['Description']):
        if find_keys[0] in entry:
            pet_machine_state = pet_machine_state.append(pet_log.iloc[idx], ignore_index=True)
        if find_keys[1] in entry:
            pet_node_state = pet_node_state.append(pet_log.iloc[idx], ignore_index=True)
        if find_keys[2] in entry:
            pet_received_command = pet_received_command.append(pet_log.iloc[idx], ignore_index=True)
            
    #Group sysnode entries
    sys_user_action = pd.DataFrame(columns=columns)
    sys_received_command = pd.DataFrame(columns=columns)
    sys_state_transition = pd.DataFrame(columns=columns)
    sys_relevant_interlock = pd.DataFrame(columns=columns)
    
    for idx, entry in enumerate(sys_log['Description']):
        if "***" in entry:
            sys_user_action = sys_user_action.append(sys_log.iloc[idx], ignore_index=True)
        if find_keys[2] in entry or find_keys[2] in entry:
            sys_received_command = sys_received_command.append(sys_log.iloc[idx], ignore_index=True)
        if find_keys[3] in entry:
            sys_state_transition = sys_state_transition.append(sys_log.iloc[idx], ignore_index=True)
        if find_keys[4] in entry:
            sys_relevant_interlock = sys_relevant_interlock.append(sys_log.iloc[idx], ignore_index=True)
            
    # Construct pet_df 
    # Get pet_recon interlocks
    pet_df = dts.find_interlocks(pet_interlocks)
    
    # insert start/restart of pet node entries
    pet_df = dts.find_node_start(pet_df, pet_start_times)
    
    # Time since start/restart of pet node
    pet_df = dts.node_start_delta(pet_df)
            
    # Duration of pet_recon interlock
    pet_df['Interlock Duration'] = dts.interlock_duration(pet_df)
    
    # HV status before active/ inactive interlock
    pet_df['HV last status (before active)'] = dts.find_last_entry(pet_df, pet_df['Active Time'], kvct_HV_status)
    pet_df['HV last status (before inactive)'] = dts.find_last_entry(pet_df, pet_df['Inactive Time'], kvct_HV_status)
    
    # Machine state before active/ inactive interlock
    pet_machine_state['Description'] = [descr.split(": ")[-1] for descr in pet_machine_state['Description']]
    pet_df['Machine last state (before active)'] = dts.find_last_entry(pet_df, pet_df['Active Time'], pet_machine_state)
    pet_df['Machine last state (before inactive)'] = dts.find_last_entry(pet_df, pet_df['Inactive Time'], pet_machine_state)
    
    # last command received before active/ inactive interlock
    for idx, descr in enumerate(pet_received_command['Description']):
        try:
            pet_received_command['Description'][idx] = descr.split(" ")[3].split("'")[1]
        except:
            pass
    pet_df['Last command received (before active)'] = dts.find_last_entry(pet_df, pet_df['Active Time'], pet_received_command)
    pet_df['Last command received (before inactive)'] = dts.find_last_entry(pet_df, pet_df['Inactive Time'], pet_received_command)
    
    # last user action 
    sys_user_action['Description'] = ["***" + description.split(" = ")[1].split(" ")[0] for description in sys_user_action['Description']]
    pet_df['Last user input'] = dts.find_last_entry(pet_df, pet_df['Active Time'], sys_user_action)
    
    # sysnode state (transition state)
    sys_state_transition['Description'] = [descr.split(" to ")[1].split(" ")[0] for descr in sys_state_transition['Description']]
    pet_df['Sysnode State'] = dts.find_last_entry(pet_df, pet_df['Active Time'], sys_state_transition)
    
    # relevant sys interlock after interlock
    pet_df = dts.sys_interlocks_before(pet_df, sys_relevant_interlock)
    
    # add relevant sys interlocks that occur while kvct interlock is active 
    pet_df = dts.sys_interlocks_during(pet_df, sys_relevant_interlock)
    
    # Finalize placement of columns
    columns = ['Date','Active Time', 'Inactive Time', 'Interlock Number', 'Time from Node Start', 'Interlock Duration', 'HV last status (before active)', 
            'HV last status (before inactive)', 'Machine last state (before active)', 'Machine last state (before inactive)', 
            'Last command received (before active)', 'Last command received (before inactive)', 'Last user input', 'Sysnode State',
            'Sysnode Relevant Interlock (before)', 'Sysnode Relevant Interlock (during)']
    
    pet_df.sort_values('Date', ascending=True, inplace=True)
    pet_df['Date'] = pet_df['Date'].dt.date
    pet_df = pet_df.reindex(columns= columns)
    
    return(pet_df)