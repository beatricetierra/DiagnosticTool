# -*- coding: utf-8 -*-
"""
Created on Tue Sep  1 14:09:26 2020

@author: btierra
""" 
import pandas as pd
import datetime

def filter_kvct(interlocks_df):
    # find entries to be filtered out and insert into new dataframe
    filter_out_idx= [] 
    interlock_type = []
    
    # convert date and time to datetime column for time difference operations
    datetimes = []
    for date, time in zip(interlocks_df['Date'], interlocks_df['Active Time']):
        datetimes.append(datetime.datetime.combine(date, time))
    
    df = interlocks_df.copy()
    df.insert(0, 'Datetime', datetimes)
    
    # save start and end entries
    log_start = df.loc[df['Interlock Number'].str.contains('LOG START')]['Datetime']
    log_start_idx = log_start.index.values
    
    node_start = df.loc[(df['Interlock Number'] == '------ NODE START ------') | \
                        (df['Interlock Number'] == '------ LOG START (Maintenance) ------')]['Datetime']
    node_start_idx = node_start.index.values
    
    node_end = df.loc[df['Interlock Number'] == '------ NODE END ------']['Datetime']
    node_end_idx = node_end.index.values

    # skip all endpoint entries
    endpoint_idx = list(set(list(log_start_idx) + list(node_start_idx) + list(node_end_idx)))
    df = df.drop(endpoint_idx)
    df.reset_index(drop=True, inplace=True)
    
    # Remove startup and shutdown interlocks
    # keep separate because node start does not mean node ended properly every time (ex. wait_config error, unexpected shutdown)
    # filter interlocks that occur 30 seconds after node starts and duration is less than 2 minutes
    for start in node_start:
        limit = start + datetime.timedelta(seconds=30)   
        for idx, (time, duration) in enumerate(zip(df['Datetime'], df['Interlock Duration (min)'])):
            if duration == 'Still Active':
                pass
            elif start < time < limit and duration < 2:
                filter_out_idx.append(idx)
                interlock_type.append('Startup Interlock')
    
    #filter interlocks that occur one minute before node shutsdown 
    for end in node_end:     
        limit = end - datetime.timedelta(minutes=1) #filter shutdown interlocks
        for idx, time in enumerate(df['Datetime']):
            if limit < time < end:
                filter_out_idx.append(idx)
                interlock_type.append('Shutdown Interlock')
        try: 
            start_times = [] 
            for start in node_start:
                if start > end:
                    start_times.append(start)
            for start in log_start:
                if start > end:
                    start_times.append(start)
            start_times = sorted(start_times)
            next_start = start_times[0]
            for idx, time in enumerate(df['Datetime']):
                if end < time < next_start:     #filter interlocks that occur after a shutdown and before next node startup
                    filter_out_idx.append(idx)
                    interlock_type.append('Shutdown Interlock')
        except:
            pass

    #filter all interlocks after the last node_end if new session does not start
    if node_end_idx[-1] > log_start_idx[-1] and node_end_idx[-1] > node_start_idx[-1]:
        for idx, time in enumerate(df['Datetime']):
            if time > node_end.iloc[-1]:
                filter_out_idx.append(idx)
                interlock_type.append('Shutdown Interlock')
  
    # filter expected interlocks based on status of other events    
    for idx, (interlock, machine, sys_before, sys_during, node_state) in enumerate(zip\
    (df['Interlock Number'], df['Machine State (before active)'], df['Sysnode Relevant Interlock (before)'], \
    df['Sysnode Relevant Interlock (during)'], df['Node State (before active)'])):
        # Filter Interlock 161400:(DMS.SW.Check.ViewAvgTooHigh) when in TREATMENT state
        if 'ViewAvgTooHigh' in interlock and '' in sys_before and '' in sys_during:
            filter_out_idx.append(idx)
            interlock_type.append('ViewAvgTooHigh')
        # Filter Interlock 161216:(DMS.Status.RCB.ExternalTriggerInvalid)  when in MV_READY state
        if 'ExternalTriggerInvalid' in interlock and '' in sys_before and '' in sys_during: 
            filter_out_idx.append(idx)
            interlock_type.append('ExternalTriggerInvalid')
        if 'KV.Infra.SysHeartbeatTimeout' in interlock and '' in sys_before and '' in sys_during: 
            filter_out_idx.append(idx)
            interlock_type.append('SysNode Restart')
        if 'IDLE' in node_state and 'HVG' in interlock:
            filter_out_idx.append(idx)
            interlock_type.append('HVG while IDLE')
        if 'HVG.AnodeStatusMismatch' in interlock and 'AnodeRampDown' in machine:
            filter_out_idx.append(idx)
            interlock_type.append('AnodeRampDown')
        if 'HVG.ContactorStatusMismatch' in interlock and 'ContactorOn' in machine:
            filter_out_idx.append(idx)
            interlock_type.append('ContactorOn')
            
    # filter interlocks based on time of other known events
    # if time difference between BEL open and HVOnStatusMismatch interlock time is less than 0.1 seconds 
    for idx, (interlock, interlock_time, bel) in enumerate(zip(df['Interlock Number'], df['Datetime'], df['BEL Open'])):
        if 'HvOnStatusMismatch' in interlock and type(bel) == pd._libs.tslibs.timestamps.Timestamp:
            if interlock_time - bel < datetime.timedelta(seconds=.1):
                filter_out_idx.append(idx)
                interlock_type.append('BEL is open')
           
    # Combine index and interlock type to sort values by index 
    expected_interlocks = pd.DataFrame({'IDX': filter_out_idx, 'Type':interlock_type})
    expected_interlocks = expected_interlocks.drop_duplicates(subset=['IDX']).sort_values(['IDX'])   #remove duplicates and sort
                                                                                                            
    # Separate interlocks_df into filtered and unfiltered
    # Create new dataframe that removed expected interlocks 
    filtered = df.drop(list(expected_interlocks['IDX']))
    
    # Add new 'Expected Interlock Type' column to original unfiltered interlocks dataframe
    expected_interlock_types = ['']*len(df)
    for idx in expected_interlocks['IDX']:
        expected_interlock_types[idx] = expected_interlocks.loc[expected_interlocks['IDX']==idx, 'Type'].values[0]
    df.insert(5, 'Expected Interlock Type', expected_interlock_types)
    
    # finalize filtered and filtered out dataframes
    # insert start and end times and sort by date and active time
    log_start_entries = interlocks_df.iloc[log_start_idx]
    start_entries = interlocks_df.iloc[node_start_idx] 
    end_entries = interlocks_df.iloc[node_end_idx] 
    
    unfiltered = pd.concat([df, log_start_entries], axis=0, sort=False)
    unfiltered = pd.concat([unfiltered, start_entries], axis=0, sort=False)
    unfiltered = pd.concat([unfiltered, end_entries], axis=0, sort=False)
    
    filtered = pd.concat([filtered, log_start_entries], axis=0, sort=False)
    filtered = pd.concat([filtered, start_entries], axis=0, sort=False)
    filtered = pd.concat([filtered, end_entries ], axis=0, sort=False)
    
    # Sort and reset both filter and unfiltered dataframes 
    unfiltered.sort_values(['Date', 'Active Time'], ascending=[True, True], inplace=True)
    unfiltered.reset_index(drop=True, inplace=True)
    filtered.sort_values(['Date', 'Active Time'], ascending=[True, True], inplace=True) 
    filtered.reset_index(drop=True, inplace=True)
    
    # Clean up dataframes
    # remove column values if entry is log start, node start, or node end
    for idx, row in unfiltered.iterrows():
        if 'LOG' in row['Interlock Number'] or 'NODE' in row['Interlock Number']:
            unfiltered.loc[idx, 5:] = ''
            
    unfiltered.drop('Datetime', axis=1, inplace=True)
    filtered.drop('Datetime', axis=1, inplace=True)

    return(filtered, unfiltered)
    
def filter_recon(interlocks_df):
     # find entries to be filtered out and insert into new dataframe
    filter_out_idx= [] 
    interlock_type = []
    
    # convert date and time to datetime column for time difference operations
    datetimes = []
    for date, time in zip(interlocks_df['Date'], interlocks_df['Active Time']):
        datetimes.append(datetime.datetime.combine(date, time))
    
    df = interlocks_df.copy()
    df.insert(0, 'Datetime', datetimes)
    
    # save start and end entries
    log_start = df.loc[df['Interlock Number'].str.contains('LOG START')]['Datetime']
    log_start_idx = log_start.index.values
    
    node_start = df.loc[(df['Interlock Number'] == '------ NODE START ------') | \
                        (df['Interlock Number'] == '------ LOG START (Maintenance) ------')]['Datetime']
    node_start_idx = node_start.index.values
    
    node_end = df.loc[df['Interlock Number'] == '------ NODE END ------']['Datetime']
    node_end_idx = node_end.index.values

    # skip all endpoint entries
    endpoint_idx = list(set(list(log_start_idx) + list(node_start_idx) + list(node_end_idx)))
    df = df.drop(endpoint_idx)
    df.reset_index(drop=True, inplace=True)
    
    # Remove startup and shutdown interlocks
    # keep separate because node start != node end everytime (ex. wait_config error, unexpected shutdown)
    #filter interlocks that occur 30 seconds after node starts and duration is less than 2 minutes
    
    for start in node_start:
        limit = start + datetime.timedelta(seconds=30)   
        for idx, (time, duration) in enumerate(zip(df['Datetime'], df['Interlock Duration (min)'])):
            if duration == 'Still Active':
                pass
            elif start < time < limit and duration < 2:
                filter_out_idx.append(idx)
                interlock_type.append('Startup Interlock')
                
    for end in node_end:
        limit = end - datetime.timedelta(minutes=1)
        for idx, time in enumerate(df['Datetime']):
            if limit < time < end:
                filter_out_idx.append(idx)
                interlock_type.append('Shutdown Interlock')
            else:
                pass         
    
    # Combine index and interlock type to sort values by index 
    expected_interlocks = pd.DataFrame({'IDX': filter_out_idx, 'Type':interlock_type})
    expected_interlocks = expected_interlocks.drop_duplicates(subset=['IDX']).sort_values(['IDX'])   #remove duplicates and sort
                                                                                                            
    # Separate interlocks_df into filtered and unfiltered
    # Create new dataframe that removed expected interlocks 
    filtered = df.drop(list(expected_interlocks['IDX']))
    
    # Add new 'Expected Interlock Type' column to original unfiltered interlocks dataframe
    expected_interlock_types = ['']*len(df)
    for idx in expected_interlocks['IDX']:
        expected_interlock_types[idx] = expected_interlocks.loc[expected_interlocks['IDX']==idx, 'Type'].values[0]
    df.insert(5, 'Expected Interlock Type', expected_interlock_types)
    
    # finalize filtered and filtered out dataframes
    # insert start and end times and sort by date and active time
    log_start_entries = interlocks_df.iloc[log_start_idx]
    start_entries = interlocks_df.iloc[node_start_idx] 
    end_entries = interlocks_df.iloc[node_end_idx] 
    
    unfiltered = pd.concat([df, log_start_entries], axis=0, sort=False)
    unfiltered = pd.concat([unfiltered, start_entries], axis=0, sort=False)
    unfiltered = pd.concat([unfiltered, end_entries], axis=0, sort=False)
    
    filtered = pd.concat([filtered, log_start_entries], axis=0, sort=False)
    filtered = pd.concat([filtered, start_entries], axis=0, sort=False)
    filtered = pd.concat([filtered, end_entries ], axis=0, sort=False)
    
    # Sort and reset both filter and unfiltered dataframes 
    unfiltered.sort_values(['Date', 'Active Time'], ascending=[True, True], inplace=True)
    unfiltered.reset_index(drop=True, inplace=True)
    filtered.sort_values(['Date', 'Active Time'], ascending=[True, True], inplace=True) 
    filtered.reset_index(drop=True, inplace=True)
    
    # Clean up dataframes
    # remove column values if entry is log start, node start, or node end
    for idx, row in unfiltered.iterrows():
        if 'LOG' in row['Interlock Number'] or 'NODE' in row['Interlock Number']:
            unfiltered.loc[idx, 5:] = ''
            
    unfiltered.drop('Datetime', axis=1, inplace=True)
    filtered.drop('Datetime', axis=1, inplace=True)

    return(filtered, unfiltered)                