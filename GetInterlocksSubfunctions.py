# -*- coding: utf-8 -*-
"""
Created on Mon May 18 19:32:01 2020

@author: btierra
"""
import pandas as pd
import datetime
import GetInterlocks as get

# Read -log- log files (compiled log file of all node log files)
def ReadLogs(file, find_keys, logtype):
    # First find software version and operating mode of file
    swver, mode = '', ''
    with open(file) as log:
        while True:
            line = log.readline().strip()
            if not line:
                break
            elif '* current branch: ' in line:
                swver = line.split('* current branch: ')[-1]
            elif 'Operating mode' in line:
                mode = line.split('-')[-1]
                
    # Find entries of interest
    system, endpoints, entries  = ([] for i in range(3))
    if logtype == 'LogNode':
        parse_idx = [3,4,7,10] #only keep date, time, node, and desciption per line
        max_split = 10
    elif logtype == 'SeparateNodes':
        parse_idx = [0,1,4,7]
        max_split = 7
    
    with open(file) as log:
        while True:
            line = log.readline()
            if not line:
                break
            elif 'Configuring log file:' in line or 'set to load_config' in line or 'Signal 15' in line:
                entry = line.split(" ", max_split)
                endpoints.append([swver] + [mode] + [entry[i] for i in parse_idx])
            elif 'Initialising Guardian' in line:
                system.append(line.split("Initialising Guardian for ")[-1].split(' ')[0])
            elif '***' in line:
                if ('TCP' in line or 'CCP' in line) and 'MV' not in line:
                    entry = line.split(" ", max_split)
                    entries.append([swver] + [mode] +[entry[i] for i in parse_idx])
            elif 'Event sent to sysnode' in line and 'code' in line:
                entry = line.split(" ", max_split)
                entries.append([swver] + [mode] +[entry[i] for i in parse_idx])
            elif 'Received command' in line:
                original_position = log.tell()
                if 'set_state' in line:
                    ten_next_entries = [log.readline() for i in range(10)]
                    state = [next_entry for next_entry in ten_next_entries if 'Got command set state' in next_entry]
                    if not state:
                        log.seek(original_position)
                        entry = line.split(" ", max_split)
                        entries.append([swver] + [mode] +[entry[i] for i in parse_idx])
                    else:
                        state = state[0]
                        entry = state.split(" ", max_split)
                        entries.append([swver] + [mode] +[entry[i] for i in parse_idx])
                        log.seek(original_position)
                else:
                    entry = line.split(" ", max_split)
                    entries.append([swver] + [mode] +[entry[i] for i in parse_idx]) 
            else:
                for word in find_keys:
                    if word in line:
                        entry = line.split(" ", max_split)
                        entries.append([swver] + [mode] +[entry[i] for i in parse_idx])
                        
    if logtype == 'LogNode':
        # Filter endpoints
        endpoints_filtered = []
        for endpoint in endpoints:
            if 'KV' in endpoint[4] or 'PR' in endpoint[4] or 'SY' in endpoint[4]:
                endpoints_filtered.append(endpoint)        
        # Filter entries
        entries_filtered = []
        for entry in entries:
            if 'KV' in entry[4] or 'PR' in entry[4] or 'SY' in entry[4]:
                entries_filtered.append(entry)
    elif logtype == 'SeparateNodes':
        endpoints_filtered = endpoints
        entries_filtered = entries
        pass
    
    return(system, endpoints_filtered, entries_filtered)

def find_endpoints(interlocks_df, node_endpoints):
    endpoints_df = pd.DataFrame({'SW Version': node_endpoints['SW Version'], 'Mode': node_endpoints['Mode'], 
                                 'Interlock Number': node_endpoints['Description'], 'Active Time': node_endpoints['Datetime'], 'Inactive Time': ''})
    
    result = pd.concat([interlocks_df, endpoints_df], sort=False)
    result.reset_index(drop=True, inplace=True)
        
    result.sort_values(by=['Active Time'], inplace=True)
    result.reset_index(drop=True, inplace=True)
    return(result)

# Time since start of node
def node_start_delta(interlocks_df):
    interlocks_df['Time from Node Start (min)'] = ''*len(interlocks_df)
    
    restart_times = interlocks_df.loc[interlocks_df['Interlock Number'].str.contains('NODE START|Maintancence')]['Active Time'].reset_index(drop=True)
    endpoints_idx = interlocks_df.loc[interlocks_df['Interlock Number'].str.contains('-----')].index.values

    for idx, active_time in enumerate(interlocks_df['Active Time']):
        if idx not in endpoints_idx:  
            try:
                restart = restart_times[restart_times < active_time].iloc[-1] 
                difference = active_time - restart
                interlocks_df.loc[idx, 'Time from Node Start (min)'] = round(difference.total_seconds()/60,6)
            except:
                pass
    get.GetInterlocks.UpdateProgress(1.25)
    return(interlocks_df)
    
# Time duration of interlock
def interlock_duration(interlock_df):
    interlock_df['Interlock Duration (min)'] = ''*len(interlock_df)
    for idx, (active, inactive) in enumerate(zip(interlock_df['Active Time'], interlock_df['Inactive Time'])):
        try:
            interlock_df.loc[idx, 'Interlock Duration (min)'] =  round(datetime.timedelta.total_seconds(inactive - active)/60, 6)
        except:
            if not active or not inactive:
                pass
            else:
                interlock_df.loc[idx, 'Interlock Duration (min)'] = 'Still Active'
    get.GetInterlocks.UpdateProgress(1.25)
    return(interlock_df)

#find the the last entry of given entry dataframe prior to given interlock (active or inactive) time
#given entry dataframe should already be (1) filtered based on entries of interest, (2) include entry times (active or inactive column), 
                                        #(3) include entry description 
def find_last_entry(interlock_df, interlock_times, entries_df):    
    # Find log times 
    logstart_times = interlock_df[interlock_df['Interlock Number'].str.contains("LOG START")]['Active Time']

    # Find last entry before interlock active/ inactive    
    last_entries = []
    for time in interlock_times:
        try:
            lowerlimit = min([logstart for logstart in logstart_times if logstart < time], key=lambda x: abs(x - time)) # find closest logstart entry
            possible_entries = entries_df.loc[(entries_df['Datetime'] > lowerlimit) & (entries_df['Datetime'] < time)]
            last_entries.append(possible_entries['Description'].iloc[-1])
        except:
            last_entries.append('')
    get.GetInterlocks.UpdateProgress(2)
    return(last_entries)

# Finds top relevant interlocks that occur before and during kvct interlocks
def sysnode_relevant_interlocks(interlock_df, sys_relevant_interlocks):
    interlock_times = interlock_df['Active Time'].tolist()
    interlock_df['Sysnode Relevant Interlock (before)'] = ''*len(interlock_df)
    interlock_df['Sysnode Relevant Interlock (during)'] = ''*len(interlock_df)
    
    for idx, sys_relevant_interlock in enumerate(sys_relevant_interlocks['Datetime']):
        for row, (active_time, inactive_time) in enumerate(zip(interlock_df['Active Time'], interlock_df['Inactive Time'])):
            try:
                if active_time < sys_relevant_interlock < inactive_time:
                    previous = interlock_df['Sysnode Relevant Interlock (during)'][row]
                    interlock_df.loc[row,'Sysnode Relevant Interlock (during)'] = previous + \
                    str(sys_relevant_interlock) + ': ' + str(sys_relevant_interlocks['Description'][idx])
            except:
                pass
        try:
            nearest_times_idx = interlock_times.index(min(interlock_time for interlock_time in interlock_times if interlock_time > sys_relevant_interlock))
            previous = interlock_df['Sysnode Relevant Interlock (before)'][nearest_times_idx]
            interlock_df.loc[nearest_times_idx,'Sysnode Relevant Interlock (before)'] = previous + \
            str(sys_relevant_interlock) + ': ' + str(sys_relevant_interlocks['Description'][idx])
        except:
            pass
    get.GetInterlocks.UpdateProgress(2)
    return(interlock_df)