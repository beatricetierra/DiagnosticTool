# -*- coding: utf-8 -*-
"""
Created on Wed Jun 10 14:23:57 2020

@author: btierra
"""
import numpy as np 
import pandas as pd
import datetime
import matplotlib.pyplot as plt

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
    
def BarGraph(df): 
    # Labels
    labels = df['Interlock Number']
    # find total over time
    sum_per_row = df.sum(axis = 1, skipna = True) 
    sum_per_row.index = labels
    
    size = (12,10)
    # Check if graph needs to be split (broken axis)
    if NeedsBrokenAxis(sum_per_row):
        try:
            fig, (ax1,ax2) = plt.subplots(1,2,sharey=True, figsize=size) 
            
            # Find limits of split graph
            left_side_limits, right_side_limits = FindRanges(sum_per_row)
            
            ax1.set_xlim(left_side_limits[0],left_side_limits[1])
            ax1.set_xticks(left_side_limits)
            
            ax2.set_xlim(right_side_limits[0], right_side_limits[1])
            ax2.set_xticks(right_side_limits)
            
            ax1.spines['right'].set_visible(False)
            ax2.spines['left'].set_visible(False)
            ax2.tick_params(axis='y',which='both',left=False)
            
            sum_per_row.plot(ax=ax1,kind='barh')
            sum_per_row.plot(ax=ax2,kind='barh')
            
            LabelValues(ax1)
            LabelValues(ax2)
            
            [tick.set_rotation(0) for tick in ax2.get_yticklabels()]
                
            d = .015  
            kwargs = dict(transform=ax1.transAxes, color='k', clip_on=False)
            ax1.plot((1-d, 1+d), (-d, +d), **kwargs)      
            ax1.plot((1-d, 1+d), (1-d, 1+d), **kwargs)
            kwargs.update(transform=ax2.transAxes)  
            ax2.plot((-d, +d), (1-d, 1+d), **kwargs)  
            ax2.plot((-d, +d), (-d, +d), **kwargs)
        except:
            fig,ax1 = plt.subplots(1, figsize=size)
            sum_per_row.plot(ax=ax1, kind='barh')
            LabelValues(ax1)
    else:
        fig,ax1 = plt.subplots(1, figsize=size)
        sum_per_row.plot(ax=ax1, kind='barh')
        LabelValues(ax1)
    
    plt.tight_layout()
    #plt.show()
    return(fig)

def FindOutliers(series):
    # Numbers outside lower and upper bounds are outliers
    q1, q3= np.percentile(series,[25,75])
    iqr= q3-q1
    lower_bound = q1 -(1.5 * iqr) 
    upper_bound = q3 +(1.5 * iqr)
    return(lower_bound, upper_bound)
    
def NeedsBrokenAxis(series):
    lower_bound, upper_bound = FindOutliers(series)
    # If ouliters exist
    if any([s < lower_bound or s > upper_bound for s in series]):
        return True
    else:
         return False
    
def FindRanges(series):
    limit = FindOutliers(series)[1]
    
    # split series
    first_half = series[series < limit]
    second_half = series[series > limit]
    
    # find increments
    if max(first_half) != min(first_half):
        increment1 = int((max(first_half)/3))
    elif max(first_half) == min(first_half):
        increment1 = int(max(first_half))
    
    if max(second_half) != min(second_half):
        increment2 = int((max(second_half) - min(second_half))/3)
    elif max(second_half) == min(second_half):
        raise 
    
    # limits as np.array
    left_max_pad = int(1.5*increment1)
    right_min_pad = int(0.1*increment2)
    right_max_pad = int(1.5*increment2)
    
    left_side_limits = np.arange(0, max(first_half)+left_max_pad, increment1)
    right_side_limits = np.arange(min(second_half)-right_min_pad, max(second_half)+right_max_pad, increment2)
    
    return(left_side_limits, right_side_limits)
    
def LabelValues(ax):
    for patch in ax.patches:
            ax.text(patch.get_width(), patch.get_y()+(patch.get_height()/2), str(patch.get_width()),
                    horizontalalignment='left', verticalalignment='center')

    
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
