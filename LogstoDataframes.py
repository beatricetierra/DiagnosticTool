# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 17:52:06 2021

@author: btierra
"""
import settings as var
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

        
def CreateDataframes(entries, endpoints):
    # Convert lists to dataframes
    entries_df = ListtoDataframes(entries)
    endpoints_df = ListtoDataframes(endpoints)
    endpoints_df = LabelEndpoints(endpoints_df)
    
    # Separate entries and endpoints per node
    entries_per_node = SeparateByNode(entries_df)
    endpoints_per_node = SeparateByNode(endpoints_df)
    
    return entries_per_node, endpoints_per_node
    
def ListtoDataframes(list_of_entries):
    columns = ['SW Version', 'Mode', 'Date', 'Time', 'Node', 'Description']
    df = pd.DataFrame(list_of_entries, columns=columns)
    
    # Combine date and time to datetime column
    df.insert(0,'Datetime', pd.to_datetime(df['Date'] + ' ' + df['Time']))
    df.drop(columns=['Date', 'Time'], inplace=True)
    df.sort_values('Datetime', ascending=True, inplace=True)
    return df

def LabelEndpoints(df):
    logstart_findkey = var.endpoints['logstart_findkey']
    nodestart_findkey = var.endpoints['nodestart_findkey']
    nodeendfind_key = var.endpoints['nodeend_findkey']
    
    # find index of each endpoint category (log start, node start, node end)
    log_start = df.loc[df['Description'].str.contains(logstart_findkey)].index.values
    node_start = df.loc[df['Description'].str.contains(nodestart_findkey)].index.values
    node_end = df.loc[df['Description'].str.contains(nodeendfind_key)].index.values
    
    # Replace values with clear labels
    df['Description'][log_start] = '----- LOG START -----'
    df['Description'][node_start] = '----- NODE START -----'
    df['Description'][node_end] = '----- NODE END -----'
    return df 

def SeparateByNode(df):
    dictionary = {}
    for acceptable_file, node in var.node_acronyms.items():
        node_df = df[df['Node'] == node]
        node_df = CleanUpDataFrames(node_df)
        dictionary[node] = node_df
    return dictionary

def CleanUpDataFrames(df):
    df.sort_values('Datetime', ascending = True, inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.drop(columns='Node', inplace=True)
    df = CleanUpMode(df)
    df = CleanUpSWVersion(df)        
    return df 

def CleanUpSWVersion(df):   #shorten entry of swver version
                            # remove '...current branch' from entry
    for idx, entry in enumerate(df['SW Version']):
        try:
            swver = entry.split(": ")[1]
            df['SW Version'].iloc[idx] = swver
        except IndexError:
            pass
    return df

def CleanUpMode(df): # replace whole entry with single word 
                     #defined in settings.modes
    for idx, entry in enumerate(df['Mode']):
        for mode in var.modes:
            if mode in entry:
                df['Mode'].iloc[idx] = mode
            else:
                pass
    return df

