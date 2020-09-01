# -*- coding: utf-8 -*-
"""
Created on Mon May 18 19:32:01 2020

@author: btierra
"""
import pandas as pd
import datetime

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

#Find Interlocks (KVCT or PET)
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
            nearest_time = nearest(instances, active_time)
            interlocks_df.loc[i,'Inactive Time'] = instances[nearest_time]
        except:
            interlocks_df.loc[i,'Inactive Time'] = "Still Active"
        
    interlocks_df.sort_values('Active Time', ascending=True, inplace=True)
    return(interlocks_df)
    
def find_endpoints(interlocks_df, node_endpoints):
    endpoints_time = [datetime.datetime.combine(date, time) for date,time in zip(node_endpoints['Date'], node_endpoints['Time'])]
    endpoints_df = pd.DataFrame({'Interlock Number': node_endpoints['Description'], 'Active Time': endpoints_time, 
                                 'Inactive Time': ''})
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
        limits = []
        try:
            for logstart in logstart_times:
                if time >= logstart:
                    limits.append(logstart)
            limit = limits[-1]
            try: 
                possible_entries = []
                try:
                    for status_time, description in zip(entries['Datetime'], entries['Description']):
                        if status_time > limit and status_time < time:
                            possible_entries.append(description)
                    try:
                        last_entries.append(possible_entries[-1])
                    except:
                        last_entries.append('')
                except:
                    last_entries.append('')
            except:
                last_entries.append('')
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