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
    
def expected_analysis(filtered_out):
    # Extract columns needed for analysis 
    columns = ['Date', 'Active Time', 'Interlock Number', 'Time from KVCT Start', 'Interlock Duration', 'Sysnode Relevant Interlock (before)',
               'Sysnode Relevant Interlock (during)', 'Type']
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
    filtered_out['Time from KVCT Start'] = total_seconds(filtered_out, filtered_out['Time from KVCT Start'])
    filtered_out['Interlock Duration'] = total_seconds(filtered_out, filtered_out['Interlock Duration'])
    
    # Analyze per session
    # Initialize expected dataframe
    columns = ['Session', 'Type', 'Count', 'Sysnode Relevant Interlock (before)', 'Sysnode Relevant Interlock (during)', 
               'Time from KVCT Start (AVG)', 'Time from KVCT Start (Min)', 'Time from KVCT Start (Max)',
               'Interlock Duration (AVG)', 'Interlock Duration (Min)', 'Interlock Duration (Max)']
    
    sessions = list(set(session_num))
    rows = 4*len(sessions)
    
    df_analysis = pd.DataFrame(columns=columns, index=list(range(0, rows)))
    idx = 0

    for session in sessions:
        df = filtered_out.loc[filtered_out['Session'] == session]
        df_analysis['Session'][idx:idx+4] = session
        
        # Count 
        df['Count'] = 1
        df_count = df.groupby('Type').count()
        df_count = df_count[['Sysnode Relevant Interlock (before)', 'Sysnode Relevant Interlock (during)', 'Count']]
        
        # Average 
        df_avg = df.groupby('Type').mean()
        df_avg = df_avg[['Time from KVCT Start', 'Interlock Duration']]
        df_avg.columns = ['Time from KVCT Start (AVG)', 'Interlock Duration (AVG)']
        
        # Min
        df_min = df.groupby('Type').min()
        df_min = df_min[['Time from KVCT Start', 'Interlock Duration']]
        df_min.columns = ['Time from KVCT Start (Min)', 'Interlock Duration (Min)']
        
        # Max
        df_max = df.groupby('Type').max()
        df_max = df_max[['Time from KVCT Start', 'Interlock Duration']]
        df_max.columns = ['Time from KVCT Start (Max)', 'Interlock Duration (Max)']
        
        # Combine
        df = pd.concat([df_count, df_avg, df_min, df_max], axis = 1)
        
        # construct df_analysis
        inter_types = ['ViewAvgTooHigh Interlock','ExternalTriggerInvalid Interlock', 'Startup Interlock', 'Shutdown Interlock']
        
        for i in range(0, len(inter_types)):
            df_analysis['Type'][idx+i] = inter_types[i]

        for inter_type in inter_types:
            try:
                row = df_analysis.loc[df_analysis['Session']==session].loc[df_analysis['Type'] == inter_type].index.values[0]
                df_analysis['Count'][row] = df.loc[inter_type, 'Count']
                print(session, inter_type)
            except:
                pass

        idx += 4   
        
    return(filtered_out, df, df_analysis)
    
# overall analysis
def analysis(filtered_df):
    # remove restart entries
    filtered_df = filtered_df[filtered_df['Interlock Number'] != '------ NODE RESTART ------']

    #counter column
    filtered_df['Count'] = 1
    count = pd.DataFrame(filtered_df.groupby('Interlock Number').count()['Count'])
    
    #average, min, and max duration
    filtered_df['Interlock Duration(sec)'] = total_seconds(filtered_df, filtered_df['Interlock Duration'])

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

# analyze per day
def analysis_per_day(filtered_df):
    return(analysis_df)
    
# analyze per session
def analysis_per_day(filtered_df):
    return(analysis_df)