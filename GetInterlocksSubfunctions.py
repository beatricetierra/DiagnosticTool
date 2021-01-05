# -*- coding: utf-8 -*-
"""
Created on Mon May 18 19:32:01 2020

@author: btierra
"""
import pandas as pd
import datetime

# Read -log- log files (compiled log file of all node log files)
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

# read node log files (sysnode, kvct, and pet_recon)
def ReadNodeLogs(file, find_keys):            
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
    parse_idx = [0,1,4,7] #only keep date, time, node, and desciption per line
    
    with open(file) as log:
        while True:
            line = log.readline()
            if not line:
                break
            elif 'Configuring log file' in line or 'Operating mode' in line or 'command: set to load_config' in line or 'Signal 15' in line:
                entry = line.split(" ", 7)
                endpoints.append([swver] + [mode] + [entry[i] for i in parse_idx])
            elif 'Initialising Guardian' in line:
                system.append(line.split("Initialising Guardian for ")[-1].split(' ')[0])
            elif '***' in line:
                if ('TCP' in line or 'CCP' in line) and 'MV' not in line:
                    entry = line.split(" ", 7)
                    entries.append([swver] + [mode] +[entry[i] for i in parse_idx])
            elif 'Event sent to sysnode' in line and 'code' in line:
                entry = line.split(" ", 7)
                entries.append([swver] + [mode] +[entry[i] for i in parse_idx])
            elif 'Received command' in line:
                original_position = log.tell()
                if 'set_state' in line:
                    ten_next_entries = [log.readline() for i in range(10)]
                    state = [next_entry for next_entry in ten_next_entries if 'Got command set state' in next_entry]
                    if not state:
                        log.seek(original_position)
                        entry = line.split(" ", 7)
                        entries.append([swver] + [mode] +[entry[i] for i in parse_idx])
                    else:
                        state = state[0]
                        entry = state.split(" ", 7)
                        entries.append([swver] + [mode] +[entry[i] for i in parse_idx])
                        log.seek(original_position)
                else:
                    entry = line.split(" ", 7)
                    entries.append([swver] + [mode] +[entry[i] for i in parse_idx]) 
            else:
                for word in find_keys:
                    if word in line:
                        entry = line.split(" ", 7)
                        entries.append([swver] + [mode] +[entry[i] for i in parse_idx])    
                        
    return(system, endpoints, entries)

#Format Time Differences (values of datetime.timedelta formats)
def timedelta_format(timedelta):
    sec = timedelta.total_seconds()
    timedelta = '{:.0f}:{:.0f}:{:.0f}:{:.4f}'.format(int(sec // 86400), int(sec // 3600), int(sec % 3600 // 60), sec % 60)
    if timedelta.split(":", 1)[0] == '0':
        timedelta = timedelta.split(":", 1)[1]
    else: 
        timedelta = timedelta + ' days'
    return(timedelta)
    
# gets the index of the closest time in items after pivot time
def nearest(items, pivot_time):  
    return items.index(min(item for item in items if item > pivot_time))
    
def find_endpoints(interlocks_df, node_endpoints):
    endpoints_time = [datetime.datetime.combine(date, time) for date,time in zip(node_endpoints['Date'], node_endpoints['Time'])]
    endpoints_df = pd.DataFrame({'SW Version': node_endpoints['SW Version'], 'Mode': node_endpoints['Mode'], 
                                 'Interlock Number': node_endpoints['Description'], 'Active Time': endpoints_time, 'Inactive Time': ''})
    
    result = pd.concat([interlocks_df, endpoints_df], sort=False)
    result.reset_index(drop=True, inplace=True)
        
    result.sort_values(by=['Active Time'], inplace=True)
    result.reset_index(drop=True, inplace=True)
    return(result)

# Time since start of node
def node_start_delta(interlocks_df):
    interlocks_df['Time from Node Start (min)'] = ''*len(interlocks_df)
    restart_times = []
    restart_times_idx = []
    endpoint_times_idx = []
    for idx, entry in enumerate(interlocks_df['Interlock Number']):
        if 'NODE START' in entry or 'Maintenance' in entry:
            restart_times.append(interlocks_df.loc[idx,'Active Time'])
            restart_times_idx.append(idx)
        elif '-----' in entry:
            endpoint_times_idx.append(idx)

    for idx, active_time in enumerate(interlocks_df['Active Time']):
        if idx not in restart_times_idx and idx not in endpoint_times_idx:
            restart = [] 
            for start_time in restart_times:
                if start_time < active_time:
                    restart.append(start_time)            
            try:
                interlocks_df.loc[idx, 'Time from Node Start (min)'] = round(datetime.timedelta.total_seconds(active_time - restart[-1])/60,6)
            except:
                pass
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
    return(interlock_df)

#find the the last entry of given entry dataframe prior to given interlock (active or inactive) time
#given entry dataframe should already be (1) filtered based on entries of interest, (2) include entry times (active or inactive column), 
                                        #(3) include entry description 
def find_last_entry(interlock_df, interlock_times, entries_df):
    #combine date and time columns for entries_df
    entries = entries_df.copy()
    datetimes = []
    for idx in range(0,len(entries)):
        date = entries.loc[idx, 'Date']
        time = entries.loc[idx, 'Time']
        datetimes.append(datetime.datetime.combine(date,time))
    entries.insert(0, 'Datetime', datetimes)
    entries.drop('Date', axis=1, inplace=True)
    entries.drop('Time', axis=1, inplace=True)
    entries.sort_values('Datetime', ascending=True, inplace=True)
    
    # Find log times 
    logstart_times = interlock_df[interlock_df['Interlock Number'].str.contains("LOG START")]['Active Time']

    # Find last entry before interlock active/ inactive    
    last_entries = []
    for idx, time in enumerate(interlock_times):
        # find closest logstart entry
        try:
            lowerlimit = min([logstart for logstart in logstart_times if logstart < time], key=lambda x: abs(x - time))
            possible_entries = entries.loc[(entries['Datetime'] > lowerlimit) & (entries['Datetime'] < time)]
            last_entries.append(possible_entries['Description'].iloc[-1])
        except:
            last_entries.append('')
    return(last_entries)

# Add column "Sysnode Relevant Interlocks (before)" to given dataframe
# Finds top relevant interlocks that occur before kvct interlock
def sys_interlocks_before(interlock_df, entries_df):
    interlock_df['Sysnode Relevant Interlock (before)'] = ''*len(interlock_df)
    interlock_times = interlock_df['Active Time'].tolist()
        
    for idx in range(0,len(entries_df)):
        try:
            sys_interlock_time = datetime.datetime.combine(entries_df['Date'][idx], entries_df['Time'][idx])
            nearest_times_idx = nearest(interlock_times, sys_interlock_time)
            previous = interlock_df['Sysnode Relevant Interlock (before)'][nearest_times_idx]
            interlock_df.loc[nearest_times_idx,'Sysnode Relevant Interlock (before)'] = previous + \
            str(entries_df['Time'][idx]) + ': ' + str(entries_df['Description'][idx])
        except:
            pass
    return(interlock_df)

# Add column "Sysnode Relevant Interlocks (during)" to given dataframe
# Finds top relevant interlocks that occur while kvct interlock is active
def sys_interlocks_during(interlock_df, entries_df):
    interlock_df['Sysnode Relevant Interlock (during)'] = ''*len(interlock_df)
    
    for idx in range(0,len(entries_df)):
        sys_interlock_time = datetime.datetime.combine(entries_df['Date'][idx], entries_df['Time'][idx])
        for row, (active_time, inactive_time) in enumerate(zip(interlock_df['Active Time'], interlock_df['Inactive Time'])):
            try:
                if active_time < sys_interlock_time < inactive_time:
                    previous = interlock_df['Sysnode Relevant Interlock (during)'][row]
                    interlock_df.loc[row,'Sysnode Relevant Interlock (during)'] = previous + \
                    str(entries_df['Time'][idx]) + ': ' + str(entries_df['Description'][idx])
            except:
                pass
    return(interlock_df)