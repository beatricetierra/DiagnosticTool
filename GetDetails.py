# -*- coding: utf-8 -*-
"""
Created on Tue Mar  9 09:57:34 2021

@author: btierra
"""
import settings as var
import pandas as pd
import datetime 
try:
    import DiagnosticToolGUISubfunctions   #needed for GUI, not for alpha monitoring
except:
    pass

def AddTimeDetails(interlocks_per_node, endpoints_per_node):
    interlocks_per_node_time_details = {}
    for node, node_interlocks in interlocks_per_node.items():
        node_endpoints = endpoints_per_node[node]
        combined = CombineEntriesAndEndpoints(node_interlocks, node_endpoints)
        combined_with_startdelta = InsertStartDelta(combined)
        combined_with_duration = InsertInterlockDuration(combined_with_startdelta)
        interlocks_per_node_time_details[node] = combined_with_duration
    return interlocks_per_node_time_details

def CombineEntriesAndEndpoints(node_interlocks, node_endpoints):
    # Rename node_endpoints columns to match node_interlocks
    node_endpoints = pd.DataFrame({'SW Version': node_endpoints['SW Version'], 
                             'Mode': node_endpoints['Mode'], 
                             'Interlock Number': node_endpoints['Description'],
                             'Active Time': node_endpoints['Datetime'],
                             'Inactive Time': ''})
    
    combined = pd.concat([node_interlocks, node_endpoints], sort=False)        
    combined.sort_values(by=['Active Time'], inplace=True)
    combined.reset_index(drop=True, inplace=True)
    return combined

# Time since start of node
def InsertStartDelta(df):
    # create copy of df and insert new column 
    df_with_startdelta = df.copy()
    df_with_startdelta['Time from Node Start (min)'] = ''*len(df_with_startdelta)
    
    # find all node start times
    node_start = df_with_startdelta.loc[df_with_startdelta['Interlock Number'].str.contains('NODE START|Maintancence')]
    node_start_times = node_start['Active Time']
    
    # find all indices of interlock entries 
    # (only find node start delta for interlocks)
    interlocks = df_with_startdelta[df_with_startdelta['Interlock Number'].str.contains('Interlock|KV.Error|voltage')]
    interlocks_idx = interlocks.index.values
    
    # Find differece between each interlock and
    # node start time that occurred right before interlock was active
    for row in interlocks_idx:
        try:
            active_time = interlocks['Active Time'][row]
            start = node_start_times[node_start_times < active_time].iloc[-1] 
            difference = active_time - start
            df_with_startdelta.loc[row, 'Time from Node Start (min)'] = round(difference.total_seconds()/60,6)
        except IndexError:  # no node start time before interlock (could be missing from log, usually LogNode)
            df_with_startdelta.loc[row, 'Time from Node Start (min)'] = ''
            
    return df_with_startdelta
    
# Time duration of interlock
def InsertInterlockDuration(df):
     # create copy of df and insert new column 
    df_with_duration = df.copy()
    df_with_duration['Interlock Duration (min)'] = ''*len(df_with_duration)
    
    # find all indices of interlock entries 
    # (only find node start delta for interlocks)
    interlocks = df_with_duration[df_with_duration['Interlock Number'].str.contains('Interlock|KV.Error|voltage')]
    interlocks_idx = interlocks.index.values
    
    for row, active, inactive in zip(interlocks_idx, interlocks['Active Time'], interlocks['Inactive Time']):
        try:
            duration = datetime.timedelta.total_seconds(inactive - active)
            duration = round(duration/60,6)
            df_with_duration.loc[row,'Interlock Duration (min)'] = duration
        except TypeError:
            df_with_duration.loc[row, 'Interlock Duration (min)'] = 'Still Active'
    return df_with_duration 

def AddEventDetails(interlocks_per_node_time_details, grouped_entries_per_node):
    interlocks_per_node_event_details = {}
    total_dfs = len(interlocks_per_node_time_details)
    for node, interlocks_df in interlocks_per_node_time_details.items():
        global column_detail   
        column_details = var.detail_columns[node]
        total_columns = len(column_details)
        for column_detail in column_details:
            GetNewColumnDetails()
            entries = grouped_entries_per_node[find_key_location][find_key]
            interlocks_df = InsertLastEntry(interlocks_df, entries)
            # updated progress
            try:
                DiagnosticToolGUISubfunctions.Subfunctions.UpdateProgress(60/total_dfs/total_columns) 
            except: #module was not imported b/c not using GUI
                pass
        interlocks_per_node_event_details[node] = interlocks_df
    return interlocks_per_node_event_details

def GetNewColumnDetails():
    global find_key_location, find_key, relative, time_column, display
    
    find_key_location = column_detail[0]
    find_key = column_detail[1]
    relative = column_detail[2]
    time_column = column_detail[3]
    display = column_detail[4]

def InsertLastEntry(interlocks_df, entries_df):   
    global logstart_times
    
    # create copy of interlocks and insert new column 
    df = interlocks_df.copy()
    colname = NewColumnName(df, find_key)
    df[colname] = ''*len(df)
    
    # Find log times 
    logstart = df[df['Interlock Number'].str.contains("LOG START")]
    logstart_times = logstart['Active Time']

    interlock_rows = df[df['Interlock Number'].str.contains('Interlock|KV.Error|voltage')]
    interlock_idx = interlock_rows.index.values
    
    for row, time in zip(interlock_idx, InterlockTimeColumn(interlock_rows)):
        nearest_entry = FindNearest(entries_df, time)
        df.loc[row, colname] = nearest_entry
    return df

def NewColumnName(df, colname): # Always creates new column name
    i = 0                       # Creates copy w/ ver number if colname exists
    while colname in df.columns:
        colname = colname.replace(' ({num})'.format(num=i), '')
        i+=1
        colname = colname + ' ({num})'.format(num=i)
    return colname

def InterlockTimeColumn(interlock_rows):
    if time_column.lower() == 'active':
        return interlock_rows['Active Time']
    elif time_column.lower() == 'inactive':
        return interlock_rows['Inactive Time']
    elif time_column.lower() == 'both':
        return list(zip(interlock_rows['Active Time'], interlock_rows['Inactive Time']))
    
def FindNearest(entries, time):
    # Find nearest entry before or after interlock occurs
    if relative.lower() == 'before':
        return FindNearestEntryBefore(entries, time)
    if relative.lower() == 'after':
        return FindNearestEntryAfter(entries, time)
    if relative.lower() == 'during':
        return FindBetweenActiveAndInactive(entries, time)

def FindNearestEntryBefore(entries, time):
    try:
        lowerlimit = [logstart for logstart in logstart_times if logstart < time][-1]
        possible_entries = entries.loc[(entries['Datetime'] > lowerlimit) & (entries['Datetime'] < time)]
        last_entry_before_interlock = DescriptionOrTime(possible_entries).iloc[-1]
    except IndexError:
        last_entry_before_interlock = '' # no entries meet criteria
    except TypeError:
        last_entry_before_interlock = '' # interlock inactive time == 'Still Active"
    return last_entry_before_interlock

def FindNearestEntryAfter(entries, time):
    try:
        upperlimit = [logstart for logstart in logstart_times if logstart > time][0]
        possible_entries = entries.loc[(entries['Datetime'] < upperlimit) & (entries['Datetime'] > time)]
        first_entry_after_interlock = DescriptionOrTime(possible_entries).iloc[0]
    except IndexError:
        first_entry_after_interlock = ''
    except TypeError:
        first_entry_after_interlock = '' # interlock inactive time == 'Still Active"
    return first_entry_after_interlock

def FindBetweenActiveAndInactive(entries, time):
    active_time = time[0]
    inactive_time = time[1]
    try:
        possible_entries = entries.loc[(entries['Datetime'] < inactive_time) & (entries['Datetime'] > active_time)]
        possible_entries_col = DescriptionOrTime(possible_entries)
        possible_entries_str = '\n'.join(possible_entries_col)
    except IndexError:
        possible_entries_str = ''
    except TypeError:
        possible_entries_str = '' # interlock inactive time == 'Still Active"
    return possible_entries_str

def DescriptionOrTime(possible_entries):
    if display.lower() == 'description':
        return possible_entries['Description']
    elif display.lower() == 'time':
        return possible_entries['Datetime']
    elif display.lower() == 'both':
        possible_entries['combined'] = [str(time) +': '+ str(desc) for time, desc in zip(
                possible_entries['Datetime'], possible_entries['Description'])]
        return possible_entries['combined']