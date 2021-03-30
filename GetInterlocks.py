# -*- coding: utf-8 -*-
"""
Created on Fri Mar  5 15:07:43 2021

@author: btierra
"""
import settings as var
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

def BreakdownEntries(entries_per_node):
    grouped_entries_per_node = {}
    for node, df in entries_per_node.items():
        find_keys = var.node_find_keys[node]
        entries = {}
        for key in find_keys + var.interlock_keys:
            if type(key) == list:
                rows_with_key = df.loc[MultipleKeysInRow(key, df)]
                key = '+'.join(key)
            elif type(key) == str:
                rows_with_key = df.loc[(df['Description'].str.contains(key))]
            rows_with_key.reset_index(drop=True)
            entries[key] = rows_with_key
            
        grouped_entries_per_node[node] = entries 
    return grouped_entries_per_node

def MultipleKeysInRow(key, df):
    rows_with_key_idx = []
    masks = [df['Description'].str.contains(FormatStr(string)) for string in key]
    masks_df = pd.DataFrame(masks).transpose()
    for row in range(len(masks_df)):
        if all(list(masks_df.iloc[row])):
            rows_with_key_idx.append(row)
    return rows_with_key_idx

def FormatStr(string):
    return string.replace('*', '\*')

def GetInterlocksPerNode(grouped_entries_per_node, endpoints_per_node):
    global endpoints
    
    interlocks_per_node = {}
    for node, dict_of_entries in grouped_entries_per_node.items():
        if node in var.detail_columns.keys():
            keys = dict_of_entries.keys()
            if any([key for key in keys if 'active' in key]):
                endpoints = endpoints_per_node[node]
                interlock_df = CreateInterlockDataframe(dict_of_entries)
                interlocks_per_node[node] = interlock_df
    return interlocks_per_node

def CreateInterlockDataframe(node_dictionary):
    global active_interlocks, inactive_interlocks
    active_interlocks, inactive_interlocks = FindInterlockEntries(node_dictionary)

    swvers = []
    modes = []
    interlock_names = []
    active_times = []
    inactive_times = []
    
    for row in range(len(active_interlocks)):
        try:
            swver = active_interlocks.loc[row, 'SW Version']
            mode = active_interlocks.loc[row, 'Mode']
            
            interlock_name = active_interlocks.loc[row, 'Description']
            interlock_name = interlock_name.split(" priority")[0].replace('- ','')
            
            active_time = active_interlocks.loc[row, 'Datetime']
            nearest_node_end = FindNearestNodeEnd(active_time, endpoints)
            nearest_inactive_time = FindNearestInactiveTime(interlock_name, active_time, nearest_node_end)
        except:
            nearest_inactive_time = 'Still active'
    
        swvers.append(swver) 
        modes.append(mode)
        interlock_names.append(interlock_name) 
        active_times.append(active_time)
        inactive_times.append(nearest_inactive_time)
    
    interlocks_df = pd.DataFrame({'SW Version':swvers, 'Mode':modes, 'Interlock Number':interlock_names,
                            'Active Time':active_times, 'Inactive Time':inactive_times})
    return interlocks_df

def FindInterlockEntries(node_dictionary):
    active_interlocks = pd.concat([node_dictionary[col] for col in var.rows], ignore_index=True)
    active_interlocks.reset_index(drop=True, inplace=True)
    active_interlocks.sort_values(by='Datetime', inplace=True)
    
    inactive_interlocks = pd.concat([node_dictionary['is inactive'], node_dictionary['is clear']], 
                                    ignore_index=True)
    inactive_interlocks.reset_index(drop=True, inplace=True)
    return active_interlocks, inactive_interlocks 

def FindNearestNodeEnd(active_time, endpoints):
    possible_node_ends = endpoints.loc[endpoints['Description'].str.contains('NODE END')]
    possible_node_ends = possible_node_ends.loc[possible_node_ends['Datetime'] > active_time]
    possible_node_ends.reset_index(drop=True, inplace=True)
    if possible_node_ends.empty:
        nearest_node_end = None
    else:
        nearest_node_end = possible_node_ends.loc[0,'Datetime']
    return nearest_node_end

def FindNearestInactiveTime(interlock_name, active_time, nearest_node_end):
    # Shorten interlock name to just interlock number (avoids string errors)
    interlock_num = interlock_name.split(':')[0]
    
    # 1. Find all inactive times with same interlock name
    possible_inactive_interlocks = inactive_interlocks.loc[inactive_interlocks['Description'].str.contains(interlock_num)]
    
    #2. Constrain possible_inactive_interlocks to those that occur after active_time and before upperlimit
    # upperlimit = nearest node end or None (node end not found, so no upperlimit)
    if nearest_node_end == None:
        possible_inactive_interlocks = possible_inactive_interlocks.loc[(possible_inactive_interlocks['Datetime'] > active_time)]
    else:
        possible_inactive_interlocks = possible_inactive_interlocks.loc[(possible_inactive_interlocks['Datetime'] > active_time) &
                                                                    (possible_inactive_interlocks['Datetime'] < nearest_node_end)]
    
    possible_inactive_interlocks.reset_index(drop=True, inplace=True)    
    nearest_inactive_time = possible_inactive_interlocks.loc[0,'Datetime']
    return nearest_inactive_time

##### FOR KVCT ONLY #####
# must read kvct logs and include findkey 'Set tube voltage' 
def InsertKVTubeUsage(grouped_entries_per_node, interlocks_per_node):    
    global kv_settings, HV
    kv_settings = grouped_entries_per_node['KV']['Set tube voltage']
    HV = grouped_entries_per_node['KV']['Set HV']
    
    interlocks_per_node_with_kvsettings = {}
    for node, interlocks_df in interlocks_per_node.items():
        settings_df = FindKVTubeSettings()
        combined = pd.concat([interlocks_df, settings_df])
        combined.sort_values(by='Active Time', inplace=True)
        combined.reset_index(drop=True, inplace=True)
        interlocks_per_node_with_kvsettings[node] = combined
    return interlocks_per_node_with_kvsettings 

def FindKVTubeSettings():   
    HV_on = HV[HV['Description'].str.contains('on')]
    HV_off = HV[HV['Description'].str.contains('off')]
    
    nearest_off, nearest_settings = [], []
    for on_time in HV_on['Datetime']:        
        off_after = HV_off.loc[(HV_off['Datetime']>on_time)]
        off_after.sort_values('Datetime', ascending=True, inplace=True)
        off_after.reset_index(inplace=True, drop=True)
        
        settings_before = kv_settings.loc[kv_settings['Datetime'] < on_time]
        settings_before.sort_values('Datetime', ascending=True, inplace=True)
        settings_before.reset_index(inplace=True, drop=True)
        
        try:
            nearest_off.append(off_after['Datetime'].iloc[0])
        except:
            nearest_off.append('\'Set HV off\' not found')
        try:
            nearest_settings.append(settings_before['Description'].iloc[-1].split('Set tube ')[1].strip())
        except: 
            nearest_settings.append('Settings not found')       

    
    settings_df = pd.DataFrame({'SW Version':['']*len(HV_on), 'Mode':['']*len(HV_on), 
                                'Interlock Number':nearest_settings,'Active Time':HV_on['Datetime'], 
                                'Inactive Time':nearest_off})
    return settings_df