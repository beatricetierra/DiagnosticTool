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
def unexpected(filtered_df):

    if filtered_df.empty == False:  
        filtered_df = filtered_df[~filtered_df['Interlock Number'].str.contains('NODE|LOG')]  # remove endpoints
        if filtered_df.empty == False:  # if filtered_df is not empty and contains unexpected interlocks
            dummies = pd.get_dummies(filtered_df['Date'])
            filtered_df = pd.concat([filtered_df['Interlock Number'], dummies], axis=1)
            analysis_df = filtered_df.groupby('Interlock Number').sum()
            analysis_df.reset_index(inplace=True)
        else: # if filtered_df has no unexpected interlocks
            analysis_df = pd.DataFrame()
    elif filtered_df.empty == True: #if filtered_df is empty (no interlocks found at all)
        analysis_df = pd.DataFrame()
        
    return(analysis_df)
    
# Analyzes expected interlocks (startup/shutdown interlocks, ViewAvgTooHigh, TriggerInvalid)
def expected(unfiltered_df):
    # Extract filtered out interlock rows
    filtered_out = unfiltered_df.loc[(unfiltered_df['Expected Interlock Type'] != '') | (unfiltered_df['Interlock Number'].str.contains('NODE START'))]
    filtered_out.reset_index(inplace=True, drop=True)
    # Extract columns needed for analysis 
    columns = ['Date', 'Active Time', 'Interlock Number', 'Time from Node Start (min)', 'Interlock Duration (min)']
    filtered_out = filtered_out.reindex(columns= columns)
    
    # Divide into different sessions 
    node_start_idx = filtered_out[filtered_out['Interlock Number'].str.contains('NODE START')].index.values
    
    session = []
    for idx, node_start in enumerate(node_start_idx):
        if idx == len(node_start_idx)-1:
            limit = len(filtered_out)
        else:
            limit = node_start_idx[idx+1]
        array_len = len(range(node_start, limit))
        session_num = [idx+1]*array_len
        session.extend(session_num)
    
    filtered_out.insert(0, 'Session', session) 
    
    # Analyze per session
    df_count = pd.DataFrame({'Session': filtered_out['Session'], 'Interlock Number': filtered_out['Interlock Number']})
    df_count = df_count[~df_count['Interlock Number'].str.contains('NODE START')]
    total_sessions = session[-1] 

    dummies = pd.get_dummies(df_count['Session'])
    analysis_df = pd.concat([df_count['Interlock Number'], dummies], axis=1)
    analysis_df = analysis_df.groupby('Interlock Number').sum()
    analysis_df.reset_index(inplace=True)
    analysis_df.insert(1, 'Total in ' + str(total_sessions) + ' Sessions', analysis_df.sum(axis=1))
    analysis_df.iloc[:,1:] = analysis_df.iloc[:,1:].astype(int)

    return(analysis_df)
