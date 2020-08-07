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
    filter_out_idx= [] 
    interlock_type = []
    
    # convert date and time to datetime column for time difference operations
    datetimes = []
    for date, time in zip(interlocks_df['Date'], interlocks_df['Active Time']):
        datetimes.append(datetime.datetime.combine(date, time))
    
    # save start and end entries
    df = interlocks_df.copy()
    df.insert(0, 'Datetime', datetimes)
    
    log_start = df.loc[df['Interlock Number'] == '------ LOG START ------']['Datetime']
    log_start_idx = log_start.index.values
    
    node_start = df.loc[df['Interlock Number'] == '------ NODE START ------']['Datetime']
    node_start_idx = node_start.index.values
    
    node_end = df.loc[df['Interlock Number'] == '------ NODE END ------']['Datetime']
    node_end_idx = node_end.index.values
    
    # skip all endpoint entries
    df = df.drop(log_start_idx)
    df = df.drop(node_start_idx)
    df = df.drop(node_end_idx)
    df.reset_index(drop=True, inplace=True)
    
    # Remove startup and shutdown interlocks
    # keep separate because node start != node end everytime (ex. wait_config error, unexpected shutdown)
    #filter interlocks that occur 5 minutes after node starts
    
    for start in node_start:
        limit = start + datetime.timedelta(minutes=5)   
        for idx, time in enumerate(df['Datetime']):
            if start < time < limit:
                filter_out_idx.append(idx)
                interlock_type.append('Startup Interlock')
    
    #filter interlocks that occur one minute before node shutsdown 
    for end in node_end:     
        limit = end - datetime.timedelta(minutes=1) #filter shutdown interlocks
        for idx, time in enumerate(df['Datetime']):
            if limit < time < end:
                filter_out_idx.append(idx)
                interlock_type.append('Shutdown Interlock')
        try: 
            start_entries = [] 
            for start in node_start:
                if start > end:
                    start_entries.append(start)
            next_start = start_entries[0]
            for idx, time in enumerate(df['Datetime']):
                if end < time < next_start:     #filter interlocks that occur after a shutdown and before next node startup
                    filter_out_idx.append(idx)
                    interlock_type.append('Shutdown Interlock')
        except:
            pass

    #filter all interlocks after the last node_end if new session does not start
    if node_end_idx[-1] > log_start_idx[-1] and node_end_idx[-1] > node_start_idx[-1]:
        for idx in range(node_end_idx[-1]+1, df.index[-1]+1):
            filter_out_idx.append(idx)
            interlock_type.append('Shutdown Interlock')
  
    # filter expected interlocks        
    for idx, (interlock, machine, sys_before, sys_during, node_state) in enumerate(zip(df['Interlock Number'], df['Machine last state (before active)'], df['Sysnode Relevant Interlock (before)'], df['Sysnode Relevant Interlock (during)'], df['Node State (before active)'])):
        # Filter Interlock 161400:(DMS.SW.Check.ViewAvgTooHigh) when in TREATMENT state
        if 'ViewAvgTooHigh' in interlock and '' in sys_before and '' in sys_during:
            filter_out_idx.append(idx)
            interlock_type.append('ViewAvgTooHigh')
        # Filter Interlock 161216:(DMS.Status.RCB.ExternalTriggerInvalid)  when in MV_READY state
        if 'ExternalTriggerInvalid' in interlock and '' in sys_before and '' in sys_during: 
            filter_out_idx.append(idx)
            interlock_type.append('ExternalTriggerInvalid')
        if 'IDLE' in node_state and 'HVG' in interlock:
            filter_out_idx.append(idx)
            interlock_type.append('HVG while IDLE')
        if 'HVG.AnodeStatusMismatch' in interlock and 'AnodeRampDown' in machine:
            filter_out_idx.append(idx)
            interlock_type.append('AnodeRampDown')
            
            
    # separate interlocks_df into filtered and filtered_out 
    df2 = pd.DataFrame({'Index': filter_out_idx, 'Type':interlock_type})
    df2 = df2.drop_duplicates(subset=['Index']).sort_values(['Index'])    #remove duplicates (incase interlock meets multiple filtering criteria)
    
    filtered = df.drop(list(df2['Index']))
    filtered_out = df.iloc[list(df2['Index'])]
    filtered_out.insert(5, 'Type', df2['Type'])
    
    # finalize filtered and filtered out dataframes
    # insert start and end times and sort by date and active time
    log_start_entries = interlocks_df.iloc[log_start_idx]
    start_entries = interlocks_df.iloc[node_start_idx] 
    end_entries = interlocks_df.iloc[node_end_idx] 
    
    filtered_out = pd.concat([filtered_out, log_start_entries], axis=0, sort=False)
    filtered = pd.concat([filtered, log_start_entries], axis=0, sort=False)
    filtered_out = pd.concat([filtered_out, start_entries], axis=0, sort=False)
    filtered = pd.concat([filtered, start_entries], axis=0, sort=False)
    filtered_out = pd.concat([filtered_out, end_entries], axis=0, sort=False)
    filtered = pd.concat([filtered, end_entries ], axis=0, sort=False)
    
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
    filtered_df = filtered_df[filtered_df['Interlock Number'] != '------ LOG START ------']
    filtered_df = filtered_df[filtered_df['Interlock Number'] != '------ NODE START ------']
    filtered_df = filtered_df[filtered_df['Interlock Number'] != '------ END START ------']

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
    restart_indices = filtered_out.loc[filtered_out['Interlock Number'] == '------ NODE START ------'].index.values.tolist()
    restart_indices.insert(0, 0)
    restart_indices = sorted(list(set(restart_indices)))

    # Divide into different sessions 
    session_num = [None] * len(filtered_out)
    
    for session, restart_idx in enumerate(restart_indices):
        try:
            end = restart_indices[session + 1]
        except:
            end = len(filtered_out)
        for idx in range(restart_idx, end):
            session_num[idx] = session+1
    
    filtered_out.insert(0, 'Session', session_num) 
    filtered_out.replace('', np.nan, inplace=True)
    
    # Count total sessions
    if 'START' in filtered_out['Interlock Number'][len(filtered_out)-1]:
        total_sessions = filtered_out['Session'][len(filtered_out)-1] - 1 
    else:
        total_sessions = filtered_out['Session'][len(filtered_out)-1]
    
    # Convert time durations to total seconds
    filtered_out['Time from Node Start'] = total_seconds(filtered_out, filtered_out['Time from Node Start'])
    filtered_out['Interlock Duration'] = total_seconds(filtered_out, filtered_out['Interlock Duration'])
    filtered_out = filtered_out[~filtered_out['Interlock Number'].str.contains('START')]
    
    # Analyze per session
    # Count
    df_count = pd.DataFrame({'Session': filtered_out['Session'], 'Interlock Number': filtered_out['Interlock Number']})

    # Create dummies table
    dummies = pd.get_dummies(df_count['Session'])
    df = pd.concat([df_count['Interlock Number'], dummies], axis=1)
    df = df.groupby('Interlock Number').sum()
    df.reset_index(inplace=True)
    df.insert(1, 'Total in ' + str(total_sessions) + ' Sessions', df.sum(axis=1))
    df.iloc[:,1:] = df.iloc[:,1:].astype(int)

    return(total_sessions, df)
