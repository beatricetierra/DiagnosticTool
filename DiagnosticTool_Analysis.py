# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 14:23:57 2020

@author: btierra
"""
import numpy as np 
import pandas as pd
import datetime

def filter_expected(interlocks_df):
    
    # find entries to be filtered out and insert into new dataframe
    filtered_out = pd.DataFrame(columns=interlocks_df.columns)
    interlock_type = []
    
    # convert date and time to datetime column for time difference operations
    datetimes = []
    for date, time in zip(interlocks_df['Date'], interlocks_df['Active Time']):
        datetimes.append(datetime.datetime.combine(date, time))
    
    # save restart entries
    df = interlocks_df.copy()
    df.insert(0, 'Datetime', datetimes)
    restart_times = df.loc[df['Interlock Number'] == '------ NODE RESTART ------']['Datetime']
    restart_times_idx = restart_times.index.values
    df.drop(restart_times_idx, inplace=True)
    
    # filter all startup (5 min after node start) and shutdown (1 min before node start) interlocks 
    for restart in restart_times:
        lowerlimit = restart - datetime.timedelta(minutes=1)
        upperlimit = restart + datetime.timedelta(minutes=5)
        for idx, time in enumerate(df['Datetime']):
            if restart < time < upperlimit:
                filtered_out = filtered_out.append(df.iloc[idx])
                interlock_type.append('Startup Interlock')
            if lowerlimit < time < restart:
                filtered_out = filtered_out.append(df.iloc[idx])
                interlock_type.append('Shutdown Interlock')
                
    # filter expected interlocks
    filtered = df.drop(filtered_out.index.values)
    
    for idx, (interlock, sys_before, sys_during) in enumerate(zip(filtered['Interlock Number'], filtered['Sysnode Relevant Interlock (before)'], filtered['Sysnode Relevant Interlock (during)'])):
        # Filter Interlock 161400:(DMS.SW.Check.ViewAvgTooHigh) when in TREATMENT state
        if 'ViewAvgTooHigh' in interlock and '' in sys_before and '' in sys_during:
            filtered_out = filtered_out.append(filtered.iloc[idx])
            interlock_type.append('ViewAvgTooHigh')
        # Filter Interlock 161216:(DMS.Status.RCB.ExternalTriggerInvalid)  when in MV_READY state
        if 'ExternalTriggerInvalid' in interlock and '' in sys_before and '' in sys_during: 
            filtered_out = filtered_out.append(filtered.iloc[idx])
            interlock_type.append('ExternalTriggerInvalid')
            
    # finalize filtered and filtered out dataframes
    filtered_out.insert(4, 'Type', interlock_type)
    filtered = df.drop(filtered_out.index.values)
    
    # insert restart times and sort by date and active time
    restart_entries = interlocks_df.iloc[restart_times_idx] 
    filtered_out = pd.concat([filtered_out, restart_entries], axis=0, sort=False)
    filtered = pd.concat([filtered, restart_entries], axis=0, sort=False)
    
    filtered_out.sort_values(['Date', 'Active Time'], ascending=[True, True], inplace=True)
    filtered_out.reset_index(drop=True, inplace=True)
    filtered.sort_values(['Date', 'Active Time'], ascending=[True, True], inplace=True) 
    filtered.reset_index(drop=True, inplace=True)
    
    filtered_out.drop('Datetime', axis=1, inplace=True)
    filtered.drop('Datetime', axis=1, inplace=True)
    
    return(filtered, filtered_out)

# Converts strings -> timedelta -> total seconds(int)
def total_seconds(filtered_out, column):
    timedelta = []
    for duration in column:
        try:
            duration = datetime.datetime.strptime(duration, '%H:%M:%S.%f')
            total = duration - datetime.datetime(1900, 1, 1)
            timedelta.append(total.total_seconds())
        except:
            timedelta.append(np.nan)
    return(timedelta)

# Analyze unexpected interlocks
def analysis(filtered_df):
    # remove restart entries
    filtered_df = filtered_df[filtered_df['Interlock Number'] != '------ NODE RESTART ------']

    #counter column
    filtered_df['Count'] = [1]*len(filtered_df)
    count = pd.DataFrame(filtered_df.groupby('Interlock Number').count()['Count'])
    
    #average, std, min, and max duration
    durations = total_seconds(filtered_df, filtered_df['Interlock Duration'])
    filtered_df['Interlock Duration(sec)'] = durations

    avg_duration = pd.DataFrame(filtered_df.groupby('Interlock Number').mean()['Interlock Duration(sec)'])
    std_duration = pd.DataFrame(filtered_df.groupby('Interlock Number').std()['Interlock Duration(sec)'])
    min_duration = pd.DataFrame(filtered_df.groupby('Interlock Number').agg('min')['Interlock Duration(sec)'])
    max_duration = pd.DataFrame(filtered_df.groupby('Interlock Number').agg('max')['Interlock Duration(sec)'])
    
    #combine
    analysis_df = count.merge(avg_duration, left_index=True, right_index=True)
    analysis_df = analysis_df.merge(std_duration, left_index=True, right_index=True)
    analysis_df = analysis_df.merge(min_duration, left_index=True, right_index=True)
    analysis_df = analysis_df.merge(max_duration, left_index=True, right_index=True)
    analysis_df.columns = ['Count', 'Avg Duration(sec)', 'Std Duration(sec)', 'Min Duration(sec)', 'Max Duration(sec)']
    analysis_df.reset_index(inplace=True)

    return(analysis_df)
    
# Analyzes expected interlocks (startup/shutdown interlocks, ViewAvgTooHigh, TriggerInvalid)
def analysis_expected(filtered_out):
    # Extract columns needed for analysis 
    columns = ['Date', 'Active Time', 'Interlock Number', 'Time from Node Start', 'Interlock Duration']
    filtered_out = filtered_out.reindex(columns= columns)
    
    # Find indices which 
    restart_indices = filtered_out.loc[filtered_out['Interlock Number'] == '------ NODE RESTART ------'].index.values
    
    # Divide into different sessions 
    session_num = [None] * len(filtered_out)
    
    for session, restart_idx in enumerate(restart_indices):
        try:
            end = restart_indices[session + 1]
        except:
            end = len(filtered_out)
        for idx in range(restart_idx, end):
            session_num[idx] = session+1
    
    total_sessions = session+1
    filtered_out.insert(0, 'Session', session_num) 
    filtered_out.replace('', np.nan, inplace=True)
    
    # Convert time durations to total seconds
    filtered_out['Time from Node Start'] = total_seconds(filtered_out, filtered_out['Time from Node Start'])
    filtered_out['Interlock Duration'] = total_seconds(filtered_out, filtered_out['Interlock Duration'])
    filtered_out = filtered_out[~filtered_out['Interlock Number'].str.contains('RESTART')]
    
    # Analyze per session
    # Count
    df_count = pd.DataFrame({'Session': filtered_out['Session'], 'Interlock Number': filtered_out['Interlock Number']})

    # Create dummies table
    dummies = pd.get_dummies(df_count['Session'])
    df = pd.concat([df_count['Interlock Number'], dummies], axis=1)
    df = df.groupby('Interlock Number').sum()
    df.reset_index(inplace=True)
    df.insert(1, 'Total in ' + str(total_sessions) + ' Sessions', df.sum(axis=1))

    return(total_sessions, df)
