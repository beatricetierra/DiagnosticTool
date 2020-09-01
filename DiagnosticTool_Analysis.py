# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 14:23:57 2020

@author: btierra
"""
import numpy as np 
import pandas as pd
import datetime

# Converts strings -> timedelta -> total seconds(int)
def total_seconds(column):
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
    # remove endpoints
    filtered_df = filtered_df[~filtered_df['Interlock Number'].str.contains("------")]
        
    dummies = pd.get_dummies(filtered_df['Date'])
    filtered_df = pd.concat([filtered_df['Interlock Number'], dummies], axis=1)
    analysis_df = filtered_df.groupby('Interlock Number').sum()
    analysis_df.reset_index(inplace=True)
    return(analysis_df)
    
# Analyzes expected interlocks (startup/shutdown interlocks, ViewAvgTooHigh, TriggerInvalid)
def analysis_expected(filtered_out):
    # Extract columns needed for analysis 
    columns = ['Date', 'Active Time', 'Interlock Number', 'Time from Node Start (min)', 'Interlock Duration (min)']
    filtered_out = filtered_out.reindex(columns= columns)
    
    # Find indices where node restarts
    restart_indices = filtered_out.loc[filtered_out['Interlock Number'] == '------ NODE START ------'].index.values.tolist()
    restart_indices = sorted(list(set(restart_indices)))

    # Divide into different sessions 
    session_num = [None] * len(filtered_out)
    
    for session, restart_idx in enumerate(restart_indices):
        if session == 0 and restart_idx!= 0:
            start = 0
        else:
            start = restart_idx
        try:
            end = restart_indices[session + 1]
        except:
            end = len(filtered_out)
        for idx in range(start, end):
            session_num[idx] = session+1
    
    filtered_out.insert(0, 'Session', session_num) 
    filtered_out.replace('', np.nan, inplace=True)
    
    # Count total sessions
    if 'START' in filtered_out['Interlock Number'][len(filtered_out)-1]:
        total_sessions = filtered_out['Session'][len(filtered_out)-1] - 1 
    else:
        total_sessions = filtered_out['Session'][len(filtered_out)-1]

    filtered_out = filtered_out[~filtered_out['Interlock Number'].str.contains('START')]
    filtered_out = filtered_out[~filtered_out['Interlock Number'].str.contains('END')]
    
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

    return(df)
