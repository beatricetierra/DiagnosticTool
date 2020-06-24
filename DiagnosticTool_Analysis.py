# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 14:23:57 2020

@author: btierra
"""
import numpy as np 
import pandas as pd
import datetime

def filter_expected(interlocks_df, column, time_threshold):
    indices = []
    filtered_out = pd.DataFrame(columns=interlocks_df.columns)
    interlock_type = []

    # filter expected interlocks
    for idx in range(0, len(interlocks_df)):
        # Add restart nodes entries
        if '------ NODE RESTART ------' in interlocks_df['Interlock Number'][idx]:
            filtered_out = filtered_out.append(interlocks_df.iloc[idx], ignore_index=True)
            interlock_type.append('')
        # Filter Interlock 161400:(DMS.SW.Check.ViewAvgTooHigh) when in TREATMENT state
        if 'ViewAvgTooHigh' in interlocks_df['Interlock Number'][idx] and '' in interlocks_df['Sysnode Relevant Interlock (before)'][idx]:
            indices.append(idx)
            filtered_out = filtered_out.append(interlocks_df.iloc[idx], ignore_index=True)
            interlock_type.append('ViewAvgTooHigh Interlock')
        # Filter Interlock 161216:(DMS.Status.RCB.ExternalTriggerInvalid)  when in MV_READY state
        if 'ExternalTriggerInvalid' in interlocks_df['Interlock Number'][idx] and '' in interlocks_df['Sysnode Relevant Interlock (before)'][idx]: 
            indices.append(idx)
            filtered_out = filtered_out.append(interlocks_df.iloc[idx], ignore_index=True)
            interlock_type.append('ExternalTriggerInvalid Interlock')
        # Filter all interlocks right after shutdown 
        if interlocks_df['Sysnode State'][idx] == 'NODE_STATE_SHUTDOWN':
            indices.append(idx)
            filtered_out = filtered_out.append(interlocks_df.iloc[idx], ignore_index=True)
            interlock_type.append('Shutdown Interlock')

    # filter startup interlocks
    for idx, start_delt in enumerate(column):
        threshold = datetime.datetime.strptime(time_threshold, '%H:%M:%S.%f')
        try:
            start_delt_time = datetime.datetime.strptime(start_delt, '%H:%M:%S.%f')
            if start_delt_time < threshold:
                indices.append(idx)
                filtered_out = filtered_out.append(interlocks_df.iloc[idx], ignore_index=True)
                interlock_type.append('Startup Interlock')
        except:
            pass
        
    filtered_out['Type'] = interlock_type
    filtered_out.sort_values(['Date', 'Active Time'], ascending=[True, True], inplace=True)
    filtered_out.reset_index(drop=True, inplace=True)

    filtered_df = interlocks_df.drop(indices)        
    filtered_df.reset_index(drop=True, inplace=True)
                             
    return(filtered_df, filtered_out)

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
    filtered_df['Count'] = 1
    count = pd.DataFrame(filtered_df.groupby('Interlock Number').count()['Count'])
    
    #average, std, min, and max duration
    filtered_df['Interlock Duration(sec)'] = total_seconds(filtered_df, filtered_df['Interlock Duration'])

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
    columns = ['Date', 'Active Time', 'Interlock Number', 'Time from Node Start', 'Interlock Duration', 'Sysnode Relevant Interlock (before)',
               'Sysnode Relevant Interlock (during)']
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
            session_num[idx] = 'Session: ' + str(session+1)
                  
    filtered_out.insert(0, 'Session', session_num) 
    filtered_out.replace('', np.nan, inplace=True)
    
    # Convert time durations to total seconds
    filtered_out['Time from Node Start'] = total_seconds(filtered_out, filtered_out['Time from Node Start'])
    filtered_out['Interlock Duration'] = total_seconds(filtered_out, filtered_out['Interlock Duration'])
    
    # Analyze per session
    # Initialize expected dataframe
    columns = ['Session', 'Interlock Number', 'Count', 'Sysnode Relevant Interlock (before)', 'Sysnode Relevant Interlock (during)', 
               'Time from Node Start (AVG)', 'Time from Node Start (STD)', 'Time from Node Start (Min)', 'Time from Node Start (Max)',
               'Interlock Duration (AVG)', 'Interlock Duration (STD)', 'Interlock Duration (Min)', 'Interlock Duration (Max)']
    
    sessions = list(set(session_num))
    idx = 0 
    analysis_df = pd.DataFrame(columns=columns)

    for session in sessions:
        df = filtered_out.loc[filtered_out['Session'] == session]
        # Count 
        df['Count'] = 1
        df_count = df.groupby('Interlock Number').count()
        df_count = df_count[[columns[2], columns[3], columns[4]]]
        df_count = df_count.astype(float)
        
        # Average 
        df_avg = df.groupby('Interlock Number').mean()
        df_avg = df_avg[['Time from Node Start', 'Interlock Duration']]
        df_avg.columns = ['Time from Node Start (AVG)', 'Interlock Duration (AVG)']
        
        # Standard Deviation
        df_std = df.groupby('Interlock Number').std()
        df_std = df_std[['Time from Node Start', 'Interlock Duration']]
        df_std.columns = ['Time from Node Start (STD)', 'Interlock Duration (STD)']
        
        # Min
        df_min = df.groupby('Interlock Number').min()
        df_min = df_min[['Time from Node Start', 'Interlock Duration']]
        df_min.columns = ['Time from Node Start (Min)', 'Interlock Duration (Min)']
        
        # Max
        df_max = df.groupby('Interlock Number').max()
        df_max = df_max[['Time from Node Start', 'Interlock Duration']]
        df_max.columns = ['Time from Node Start (Max)', 'Interlock Duration (Max)']
        
        # Combine
        df = pd.concat([df_count, df_avg, df_std, df_min, df_max], axis = 1)
        
        # Construct columns
        rows = len(df)
        df['Session'] = rows*[session]
        df['Interlock Number'] = df.index.tolist()
        
        # Append to analysis_df
        analysis_df = analysis_df.append(df, ignore_index=True)
        analysis_df = analysis_df[~analysis_df['Interlock Number'].isin(['------ NODE RESTART ------'])]
        analysis_df = analysis_df.reindex(columns= columns)
        analysis_df.sort_values(by=['Session'], inplace=True)
    return(analysis_df)