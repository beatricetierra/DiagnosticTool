# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 11:44:13 2021

@author: btierra
"""
import ProcessLogs
import LogstoDataframes
import GetInterlocks
import GetDetails
import CleanUp
import Filter
    
# 1. Find files from directory
logtype = 'SeparateNodes' 
folder = r'C:\Users\btierra\Downloads\test break'
filenames = ProcessLogs.FindLogs(folder)
filenames = ProcessLogs.FilterFiles(filenames, logtype)

# 2. Logs to dataframes
endpoints, entries = ProcessLogs.GetLogEntries(filenames, logtype)

# 3. Find system 
system = ProcessLogs.FindSystem(filenames)

# 4. Divide entries and endpoints by node
entries_per_node, endpoints_per_node = LogstoDataframes.CreateDataframes(entries, endpoints)

# 5. Group entries for each node in entries_per_node
# Ex: Group interlocks, BEL open, HV on entries together within KV node
grouped_entries_per_node = GetInterlocks.BreakdownEntries(entries_per_node)

# 6. Find interlock dataframes per node
interlocks_per_node = GetInterlocks.GetInterlocksPerNode(grouped_entries_per_node, endpoints_per_node)

### OPTIONAL: Get KV Tube Usage  ###
interlocks_per_node = GetInterlocks.InsertKVTubeUsage(grouped_entries_per_node, interlocks_per_node)

# 7. Insert endpoints, interlock duration, and time from node start details
interlocks_per_node_time_details = GetDetails.AddTimeDetails(interlocks_per_node, endpoints_per_node)

#8. Insert entry columns from grouped_entries_per_node in step 5
interlocks_per_node_event_details = GetDetails.AddEventDetails(interlocks_per_node_time_details, grouped_entries_per_node)

# 9. Clean up 
final_dfs = CleanUp.CleanDataframes(interlocks_per_node_event_details)

# 10. Filter Interlocks
unfiltered_dfs, filtered_dfs = Filter.FilterExpectedInterlocks(final_dfs)

