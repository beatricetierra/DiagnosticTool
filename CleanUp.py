# -*- coding: utf-8 -*-
"""
Created on Wed Mar 10 16:31:58 2021

@author: btierra
"""
import settings as var
import pandas as pd
import json
import re

def CleanDataframes(interlocks_per_node_event_details):
    global dfs 
    dfs = interlocks_per_node_event_details.copy()
    dfs = RenameColumns()
    dfs = FormatDatetimeColumns()
    dfs = ReorderColumns()
    ParseColumns()
    dfs = ReadAsJSON()
    return dfs

def RenameColumns():
    try:
        renamed_dfs = {}
        for node, df in dfs.items():
            column_names = var.column_names[node]
            for col_original, col_new in zip(df.columns[7:], column_names):
                df = df.rename(columns={col_original:col_new})
            renamed_dfs[node] = df
        return renamed_dfs
    except:
        return dfs

def FormatDatetimeColumns():
    for node, df in dfs.items():
         # Add Date column
         df['Date'] = [activetime.date() for activetime in df['Active Time']]
         # Remove date from active/ inactive timestamps
         df['Active Time'] = [activetime.time() for activetime in df['Active Time']]
         for idx, inactivetime in enumerate(df['Inactive Time']):
             if type(inactivetime) == pd._libs.tslibs.timestamps.Timestamp:
                 df['Inactive Time'].iloc[idx] = inactivetime.time()
             else:
                 df['Inactive Time'].iloc[idx] = ''
    return dfs     

def ReorderColumns():
    # Move fixed columns in the front
    try:
        reorderd_dfs = {}
        for node, df in dfs.items():
            fixed_columns = var.fixed_columns
            add_columns = var.column_names[node]
            df = df[fixed_columns + add_columns]
            reorderd_dfs[node] = df
        return reorderd_dfs
    except:
        return dfs 

def ParseColumns():
    for node, df in dfs.items():
        try:
            columns_to_parse = var.parse_column_entries[node]   #within try in case no parse formatting given in json file
            for col, entry_parse_struct in columns_to_parse.items():
                if col in df.columns:
                    for idx, entry in enumerate(df[col]):
                        match = re.search(entry_parse_struct, entry)
                        if type(match) != type(None):
                            wildcard = match.group(1)
                            df[col].iloc[idx] = wildcard
                        else:  # no matching objects found
                            df[col].iloc[idx] = entry
        except:
            pass
    

def ReadAsJSON():
    for node, df in dfs.items():
        kv_errors = df['Interlock Number'][df['Interlock Number'].str.contains('KV.Error')]
        if kv_errors.empty == False:
            for idx, message in kv_errors.items():
                info = message.split("=> ")[1]
                dictionary = json.loads(info)
                error_name = dictionary['obj']['code']
                info = str(dictionary['obj']['result'])
                new_message = error_name + ', result:' + info
                df['Interlock Number'].iloc[idx] = new_message
        else:
            pass
    return dfs