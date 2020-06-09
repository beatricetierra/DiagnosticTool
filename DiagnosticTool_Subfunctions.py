# -*- coding: utf-8 -*-
"""
Created on Mon May 18 19:32:01 2020

@author: btierra
"""
import numpy as np
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
        interlock = interlock.split(" priority")[0]
        interlocks_set.append(interlock)
        
    interlocks_set = list(set(interlocks_set))
    
    #sepearte active vs inactive interlock entries (sepearate interlock name and time)
    for idx, interlock_desc in enumerate(node_interlocks['Description']):
        for interlock in interlocks_set:
            if interlock in interlock_desc:
                if 'is active' in interlock_desc:
                    interlock_active_name.append(interlock)
                    interlock_active_time.append(datetime.datetime.combine(node_interlocks['Date'][idx],node_interlocks['Time'][idx]))
                elif 'is inactive' in interlock_desc:
                    interlock_inactive_name.append(interlock)
                    interlock_inactive_time.append(datetime.datetime.combine(node_interlocks['Date'][idx],node_interlocks['Time'][idx]))
    
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
            interlocks_df['Inactive Time'][i] = instances[nearest_time]
        except:
            interlocks_df['Inactive Time'][i] = "Still Active"
    
    #format date and time columns
    interlocks_df.insert(0, 'Date', ""*len(interlocks_df))
    
    for idx, (active, inactive) in enumerate(zip(interlocks_df['Active Time'], interlocks_df['Inactive Time'])):
        interlocks_df['Date'][idx] = active.to_pydatetime().date()
        try:
            interlocks_df['Active Time'][idx] = active.to_pydatetime().time()
            interlocks_df['Inactive Time'][idx] = inactive.to_pydatetime().time()
        except:
            pass
 
    return(interlocks_df)
    
def find_node_start(interlocks_df, interlock_start_times):
    start_times = pd.DataFrame({'Interlock Number': '------ NODE RESTART ------', 'Datetime': interlock_start_times,
                               'Active Time': '', 'Inactive Time': ''})
    result = pd.concat([interlocks_df, start_times], sort=False)
    result.reset_index(drop=True, inplace=True)
    
    for idx, (date, time) in enumerate(zip(result['Date'], result['Active Time'])):
        try:
            result['Datetime'][idx] = datetime.datetime.combine(date,time)
        except:
            pass
        
    result.sort_values(by=['Datetime'], inplace=True)
    result['Date'] = result['Datetime']
    result.drop(columns = 'Datetime', inplace=True)
    result.reset_index(drop=True, inplace=True)
    return(result)

# Time since start of node
def node_start_delta(interlocks_df):
    interlocks_df['Time from KVCT Start'] = ''*len(interlocks_df)
    restart_times = interlocks_df.loc[interlocks_df['Interlock Number'] == '------ NODE RESTART ------']['Date']
    restart_times_idx = restart_times.index.values
    
    for idx, active_time in enumerate(interlocks_df['Date']):
        if idx not in restart_times_idx:
            restart = [] 
            for start_time in restart_times:
                if start_time < active_time:
                    restart.append(start_time)
            try:
                interlocks_df['Time from KVCT Start'][idx] = timedelta_format(active_time - restart[-1])
            except:
                pass
    return(interlocks_df)
    
# Time duration of interlock
def interlock_duration(interlock_df):
    time_delta = []
    for idx, (active, inactive) in enumerate(zip(interlock_df['Active Time'], interlock_df['Inactive Time'])):
        date = interlock_df['Date'][idx].to_pydatetime()
        date = datetime.date(2020, 6, 3)
        try:
            inactive_time = datetime.datetime.combine(date, inactive)
            active_time = datetime.datetime.combine(date, active)
            time_delta.append(timedelta_format(inactive_time - active_time))
        except:
            if not active:
                time_delta.append('')
            else:
                time_delta.append('Still Active')
    return(time_delta)

#find the the last entry of given entry dataframe prior to given interlock (active or inactive) time
#given entry dataframe should already be (1) filtered based on entries of interest, (2) include entry times (active or inactive column), 
                                        #(3) include entry description 
def find_last_entry(interlock_df, interlock_times, entries_df):
    last_entries = []
    for idx, time in enumerate(interlock_times):
        date = interlock_df['Date'][idx]
        date = date.date()
        try:
            time = datetime.datetime.combine(date, time)
            possible_entries = []
            for idx in range(0, len(entries_df)):
                status_time = datetime.datetime.combine(entries_df['Date'][idx], entries_df['Time'][idx])
                if time > status_time:
                    possible_entries.append(entries_df['Description'][idx])
            try:
                last_entries.append(possible_entries[-1])
            except:
                last_entries.append('')
        except:
            last_entries.append('')
    return(last_entries)

# Add column "Sysnode Relevant Interlocks" to given dataframe
def sys_interlocks(interlock_df, entries_df):
    interlock_df['Sysnode Relevant Interlock'] = ''*len(interlock_df)
    interlock_times = interlock_df['Date'].tolist()
        
    for idx in range(0,len(entries_df)):
        try:
            sys_interlock_time = datetime.datetime.combine(entries_df['Date'][idx], entries_df['Time'][idx])
            nearest_times_idx = nearest(interlock_times, sys_interlock_time)
            previous = interlock_df['Sysnode Relevant Interlock'][nearest_times_idx]
            interlock_df['Sysnode Relevant Interlock'][nearest_times_idx] = previous + str(entries_df['Time'][idx]) + ': ' + str(entries_df['Description'][idx])
        except:
            pass
    return(interlock_df)
    
# filter expected interlocks     
def filter_expected(interlocks_df):
    indices = []
    for idx in range(0, len(interlocks_df)):
        # Filter Interlock 161400:(DMS.SW.Check.ViewAvgTooHigh) when in TREATMENT state
        if 'ViewAvgTooHigh' in interlocks_df['Interlock Number'][idx] and '' in interlocks_df['Sysnode Relevant Interlock'][idx]:
            indices.append(idx)
        # Filter Interlock 161216:(DMS.Status.RCB.ExternalTriggerInvalid)  when in MV_READY state
        if 'ExternalTriggerInvalid' in interlocks_df['Interlock Number'][idx] and '' in interlocks_df['Sysnode Relevant Interlock'][idx]: 
            indices.append(idx)
        # Filter all interlocks right after shutdown 
        if interlocks_df['Sysnode State'][idx] == 'NODE_STATE_SHUTDOWN':
            indices.append(idx)
            
    filtered_df = interlocks_df.drop(indices)        
    filtered_df.reset_index(drop=True, inplace=True)
    return(filtered_df)

# filtered startup interlocks
def filter_startup(interlocks_df, column, time_threshold):
    # filtered startup interlocks
    indices = []
    for idx, start_delt in enumerate(column):
        threshold = datetime.datetime.strptime(time_threshold, '%H:%M:%S.%f')
        try:
            start_delt_time = datetime.datetime.strptime(start_delt, '%H:%M:%S.%f')
            if start_delt_time < threshold:
                indices.append(idx)
        except:
            pass
    
    filtered_df = interlocks_df.drop(indices)
    filtered_df.reset_index(drop=True, inplace=True)
    return(filtered_df)

def analysis(filtered_df):
    filtered_df = filtered_df[filtered_df['Interlock Number'] != '------ NODE RESTART ------']

    #counter column
    filtered_df['Count'] = 1
    count = pd.DataFrame(filtered_df.groupby('Interlock Number').count()['Count'])
    
    #average, min, and max duration
        #first convert strings -> timedelta -> integer 
    timedelta = []
    for duration in filtered_df['Interlock Duration']:
        try:
            duration = datetime.datetime.strptime(duration, '%H:%M:%S.%f')
            total = duration - datetime.datetime(1900, 1, 1)
            timedelta.append(total.total_seconds())
        except:
            timedelta.append(np.nan)
    
    filtered_df['Interlock Duration(sec)'] = timedelta
    avg_duration = pd.DataFrame(filtered_df.groupby('Interlock Number').mean()['Interlock Duration(sec)'])
    min_duration = pd.DataFrame(filtered_df.groupby('Interlock Number').min()['Interlock Duration(sec)'])
    max_duration = pd.DataFrame(filtered_df.groupby('Interlock Number').max()['Interlock Duration(sec)'])
    
    #combine
    analysis_df = count.merge(avg_duration, left_index=True, right_index=True)
    analysis_df = analysis_df.merge(min_duration, left_index=True, right_index=True)
    analysis_df = analysis_df.merge(max_duration, left_index=True, right_index=True)
    analysis_df.columns = ['Count', 'Avg Duration(sec)', 'Min Duration(sec)', 'Max Duration(sec)']
    analysis_df.reset_index(inplace=True)

    return(analysis_df)