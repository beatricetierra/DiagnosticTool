# -*- coding: utf-8 -*-
"""
Created on Tue Mar  2 15:25:14 2021

@author: btierra
"""
import os
import settings as var

# Get log filenames from directory
def FindLogs(folder):
    filenames = []  
    for root, dirs, files in os.walk(folder):
        for file in files:
            for word in var.acceptable_files:
                if '.log' in file and word in file:   
                    filenames.append(os.path.join(root, file))
    return filenames

def FilterFiles(filenames, logtype):
    if logtype == 'LogNode':
        filtered_files = [file for file in filenames if '-log-' in file]
    elif logtype == 'SeparateNodes':
        filtered_files = [file for file in filenames if '-log-' not in file]
    return filtered_files 

def GetLogEntries(filenames, logtype):
    global file, find_keys
    endpoints, entries  = ([] for i in range(2))
    for file in filenames:
        find_keys = GetFindKeys()
        endpoints_tmp, entries_tmp = ReadLog(file, logtype)
        [endpoints.append(endpoints_tmp[i]) for i in range(len(endpoints_tmp))]
        [entries.append(entries_tmp[i]) for i in range(len(entries_tmp))]
    return endpoints, entries

def GetFindKeys():
    for acceptable_file, node in var.node_acronyms.items():
        if acceptable_file in file:
            find_keys = var.node_find_keys[node]
            return find_keys
        elif '-log-' in file:
            find_keys = var.node_find_keys.values()
            find_keys_unique = []
            for sublist in find_keys:
                for item in sublist:
                    if item not in find_keys_unique:
                        find_keys_unique.append(item)
            return find_keys_unique

def ReadLog(log, logtype):
    global file, parse_idx, max_split
    global endpoints, entries
    file = log 
    
    parse_idx, max_split = ParseLines(logtype)    
    endpoints, entries = FindEntries()
    
    # split nodes if using lognode
    if IsLogNode(logtype):
        endpoints = SplitPerNode(endpoints)
        entries = SplitPerNode(entries)
    else:
        pass 
    return endpoints, entries
    
def ParseLines(logtype):
    if logtype == 'LogNode':
        parse_idx = [3,4,7,10] #only keep date, time, node, and desciption per line
        max_split = 10
    elif logtype == 'SeparateNodes':
        parse_idx = [0,1,4,7]
        max_split = 7
    return parse_idx, max_split

def FindEntries():
    global line, entries
     # Find entries of interest
    SetupEndpointFindKeys() 
    system, endpoints, entries  = ([] for i in range(3))
    swver, mode = '',''
    with open(file,  errors="ignore") as log:
        while True:
            line = log.readline()
            if not line:
                break
            elif 'current branch' in line:
                swver = line.split(" ", max_split)[-1].strip()
            elif 'Operating mode' in line:
                mode = line.split(" ", max_split)[-1] 
            elif logstart in line or nodestart in line or nodeend in line:
                entry = line.split(" ", max_split)
                endpoints.append([swver] + [mode] + [entry[i] for i in parse_idx])
            else:
                for keys in find_keys + var.interlock_keys:
                    if type(keys) == list:
                            RenderListCondition(keys, swver, mode)
                    elif type(keys) == str:
                        if keys in line:
                            AppendEntriesContainingFindKeys(swver, mode)
    return endpoints, entries

def RenderListCondition(keys, swver, mode):
    and_ = [key for key in keys if '|' not in key]
    or_ = [key.split('|') for key in keys if '|' in key][0]
    if all([a in line for a in and_]):
        if any([o in line for o in or_]):
            AppendEntriesContainingFindKeys(swver, mode)

def AppendEntriesContainingFindKeys(swver, mode):
    entry = line.split(" ", max_split)
    try:
        entries.append([swver] + [mode] +[entry[i] for i in parse_idx])
    except IndexError: # some log entries contain word but are long warning messages
        pass 

def SetupEndpointFindKeys():
    global logstart, nodestart, nodeend
    logstart = var.endpoints['logstart_findkey']
    nodestart = var.endpoints['nodestart_findkey']
    nodeend = var.endpoints['nodeend_findkey']

def IsLogNode(logtype):
    if logtype == 'LogNode':
        return True
    elif logtype == 'SeparateNodes':
        return False

def SplitPerNode(log_entry_list):
    filtered = []
    for entry in log_entry_list:
        for accpetable_file, node in var.node_acronyms.items():
            if node in entry[4]:
                filtered.append(entry)        
    return filtered

def FindSystem(filenames):
    systems = []
    for file in filenames:
        with open(file) as log:
            while True:
                line = log.readline().strip()
                if not line:
                    break
                elif 'Initialising Guardian' in line:
                    for machine in var.machines:
                        if machine in line:
                            systems.append(machine)
    
    system = CompareFoundSystems(systems)
    return system

def CompareFoundSystems(systems):
    try:
        if all(sys == systems[0] for sys in systems): # checks all log files are from the same system
                system = systems[0]
        else:
            system = 'Unknown' # if no system are found 
    except:
        system = 'Unknown'
    return system