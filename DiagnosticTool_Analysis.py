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
    view_avg_count = 0
    invalid_count = 0
    startup_count = 0
    shutdown_count = 0

    # filter expected interlocks
    for idx in range(0, len(interlocks_df)):
        # Filter Interlock 161400:(DMS.SW.Check.ViewAvgTooHigh) when in TREATMENT state
        if 'ViewAvgTooHigh' in interlocks_df['Interlock Number'][idx] and '' in interlocks_df['Sysnode Relevant Interlock (before)'][idx]:
            indices.append(idx)
            view_avg_count += 1
        # Filter Interlock 161216:(DMS.Status.RCB.ExternalTriggerInvalid)  when in MV_READY state
        if 'ExternalTriggerInvalid' in interlocks_df['Interlock Number'][idx] and '' in interlocks_df['Sysnode Relevant Interlock (before)'][idx]: 
            indices.append(idx)
            invalid_count += 1
        # Filter all interlocks right after shutdown 
        if interlocks_df['Sysnode State'][idx] == 'NODE_STATE_SHUTDOWN':
            indices.append(idx)
            shutdown_count += 1
            
    # filter startup interlocks
    for idx, start_delt in enumerate(column):
        threshold = datetime.datetime.strptime(time_threshold, '%H:%M:%S.%f')
        try:
            start_delt_time = datetime.datetime.strptime(start_delt, '%H:%M:%S.%f')
            if start_delt_time < threshold:
                indices.append(idx)
                startup_count += 1
        except:
            pass
    
    filtered_df = interlocks_df.drop(indices)        
    filtered_df.reset_index(drop=True, inplace=True)
    
    count_df = pd.DataFrame({'ViewAvgTooHigh #': [view_avg_count], 'ExternalTriggerInvalid #': [invalid_count], 'Startup Interlocks': [startup_count], 'Shutdown Interlocks': [shutdown_count]})
                             
    return(filtered_df, count_df)

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