# -*- coding: utf-8 -*-
"""
Created on Tue Sep  1 14:09:26 2020

@author: btierra
""" 
import pandas as pd
import datetime

def filter_kvct(interlocks_df):
    # prevent changing original dataframe
    df = interlocks_df.copy() 
    column_names = list(df.columns)
    
    # convert date and time to datetime column for time difference operations    
    df.insert(0, 'Datetime', pd.to_datetime(df['Date'].apply(str)+' '+df['Active Time'].apply(str))) 
    
    # find entries to be filtered out and insert into new dataframe
    filter_out_idx= [] 
    interlock_type = []
    
    # save start and end entries
    log_start = df.loc[df['Interlock Number'].str.contains('LOG START')]
    node_end = df.loc[df['Interlock Number'].str.contains('NODE END')]
    
    ## treat log start as node start if in maintenance mode 
    start = df.loc[df['Interlock Number'].str.contains('NODE START')]
    maintenance_start = df.loc[(df['Interlock Number'].str.contains('LOG START')) & (df['Mode'] == 'maintenance')]
    node_start = pd.concat([start, maintenance_start], axis = 0).sort_values('Datetime',ascending=True)
    
    log_start_idx = list(log_start.index.values)
    node_start_idx = list(node_start.index.values)
    node_end_idx = list(node_end.index.values)

    # skip all endpoint entries (in case endpoints are filtered)
    endpoint_idx = list(set(log_start_idx + node_start_idx + node_end_idx))
    df = df.drop(endpoint_idx)
    df.reset_index(drop=True, inplace=True)
    
    # Remove startup and shutdown interlocks
    ## keep separate because node start does not mean node ended properly every time (ex. unexpected shutdown)
    
    # filter interlocks that occur 30 seconds after node starts and duration is less than 2 minutes
    for start in node_start['Datetime']:
        limit = start + datetime.timedelta(seconds=30)
        df_temp = df.loc[(df['Datetime'] > start) & (df['Datetime'] < limit)]
        for idx, duration in zip(df_temp.index.values, df_temp['Interlock Duration (min)']):
            if duration == 'Still Active':
                pass
            elif duration < 2:
                filter_out_idx.append(idx)
                interlock_type.append('Startup Interlock')
    
    #filter interlocks that occur one minute before node shutsdown 
    for end in node_end['Datetime']:     
        limit = end - datetime.timedelta(minutes=1) #filter shutdown interlocks
        df_temp = df.loc[(df['Datetime'] < end) & (df['Datetime'] > limit)]
        filter_out_idx.extend(df_temp.index.values) 
        interlock_type.extend(['Shutdown Interlock']*len(df_temp))
        
    # filter interlocks that occur between node end and another node/log start
    after_end = pd.concat([log_start, node_start, df.iloc[[-1],:]]) # find indices between node end and log/start/end of dataframe 
    after_end.sort_values('Datetime', inplace=True)
    
    for end in node_end['Datetime']:
        try:
            after_time = after_end.loc[after_end['Datetime'] > end]['Datetime'].iloc[0]
            df_temp = df.loc[(df['Datetime'] > end) & (df['Datetime'] < after_time)]
            filter_out_idx.extend(df_temp.index.values)
            interlock_type.extend(['Shutdown Interlock']*len(df_temp))
        except: #node_end is last entry, so no interlocks to find
            pass
      
    # filter interlocks based on time of other known events
    # if time difference between BEL open and HVOnStatusMismatch interlock time is less than 0.1 seconds 
    # if time difference between ExternalTriggerInvalid and DMS.DRB.BadViewCounterChanged or DMS.Status.RCB.CRC_Error is less than 10 seconds
    # if time difference between Gantry Speed = 0 and DMS.DRB.BadViewCounterChanged or DMS.Status.RCB.CRC_Error is less than 10 seconds
    externaltrigger = df.loc[df['Interlock Number'].str.contains('ExternalTriggerInvalid')]
    externaltriggertimes = [datetime.datetime.combine(date,time) for date,time in zip(externaltrigger['Date'], externaltrigger['Active Time'])]
    externaltriggertimes.extend([datetime.datetime.combine(date,time) for date,time in zip(externaltrigger['Date'], externaltrigger['Inactive Time'])])
    
    for idx, (interlock, interlock_time, bel, gantry) in enumerate(zip(df['Interlock Number'], df['Datetime'], df['BEL Open'], df['Gantry Speed (RPM)'])):
        if 'HvOnStatusMismatch' in interlock and type(bel) == pd._libs.tslibs.timestamps.Timestamp:
            if interlock_time - bel < datetime.timedelta(seconds=.1):
                filter_out_idx.append(idx)
                interlock_type.append('BEL is open')
        if 'BadViewCounterChanged' in interlock or 'DMS.Status.RCB.CRC_Error' in interlock:
            external_diff = [interlock_time - externaltriggertime for externaltriggertime in externaltriggertimes]
            external_diff = [abs(diff.total_seconds()) for diff in external_diff]
            if any(diff < 10 for diff in external_diff):
                filter_out_idx.append(idx)
                interlock_type.append('DMS/ExternalTriggerInvalid')
            if 'Speed = 0' in gantry:
                gantry_time = datetime.datetime.strptime(gantry.split(': ')[0], '%Y-%m-%d %H:%M:%S.%f')
                if interlock_time - gantry_time < datetime.timedelta(seconds=10):
                    filter_out_idx.append(idx)
                    interlock_type.append('Gantry Stop')
                
                
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

    # Combine index and interlock type to sort values by index 
    expected_interlocks = pd.DataFrame({'IDX': filter_out_idx, 'Type':interlock_type})
    expected_interlocks = expected_interlocks.drop_duplicates(subset=['IDX']).sort_values(['IDX'])   #remove duplicates and sort
                                                                                                            
    # Separate interlocks_df into filtered and unfiltered
    # Create new dataframe that removed expected interlocks 
    filtered = df.drop(list(expected_interlocks['IDX']))
    
    # Add new 'Expected Interlock Type' column to original unfiltered interlocks dataframe
    df['Expected Interlock Type'] = ['']*len(df)
    df['Expected Interlock Type'][list(expected_interlocks['IDX'])] = list(expected_interlocks['Type'])

    # finalize filtered and filtered out dataframes
    # insert start and end times and sort by date and active time
    unfiltered = pd.concat([df, log_start], axis=0, sort=False)
    unfiltered = pd.concat([unfiltered, node_start], axis=0, sort=False)
    unfiltered = pd.concat([unfiltered, node_end], axis=0, sort=False)
    
    filtered = pd.concat([filtered, log_start], axis=0, sort=False)
    filtered = pd.concat([filtered, node_start], axis=0, sort=False)
    filtered = pd.concat([filtered, node_end], axis=0, sort=False)

    # Sort and reset both filter and unfiltered dataframes 
    unfiltered.sort_values('Datetime', ascending=True, inplace=True)
    unfiltered.reset_index(drop=True, inplace=True)
    filtered.sort_values('Datetime', ascending=True, inplace=True)
    filtered.reset_index(drop=True, inplace=True)
    
    # Clean up dataframes    
    filtered = filtered.reindex(columns=column_names)
    column_names.insert(6, 'Expected Interlock Type')
    unfiltered = unfiltered.reindex(columns=column_names)
    
    endpoints_idx  = unfiltered.loc[unfiltered['Interlock Number'].str.contains('LOG|NODE')].index.values
    unfiltered.iloc[endpoints_idx,6:] = ''
    
    # Extra dataframe to remove couch related interlocks
    filtered_couchinterlocks = filtered.loc[(~filtered['Interlock Number'].str.contains('DMS.SW.Check.TimeSyncWithCouch')) \
                                            &(~filtered['Interlock Number'].str.contains('SW.Comm.CouchPos.Disconnected'))] 
    return(filtered, unfiltered, filtered_couchinterlocks)
    
def filter_recon(interlocks_df):
    # prevent changing original dataframe
    df = interlocks_df.copy() 
    column_names = list(df.columns)
    
    # convert date and time to datetime column for time difference operations    
    df.insert(0, 'Datetime', pd.to_datetime(df['Date'].apply(str)+' '+df['Active Time'].apply(str))) 
    
    # find entries to be filtered out and insert into new dataframe
    filter_out_idx= [] 
    interlock_type = []
    
    # save start and end entries
    log_start = df.loc[df['Interlock Number'].str.contains('LOG START')]
    node_end = df.loc[df['Interlock Number'].str.contains('NODE END')]
    
    ## treat log start as node start if in maintenance mode 
    start = df.loc[df['Interlock Number'].str.contains('NODE START')]
    maintenance_start = df.loc[(df['Interlock Number'].str.contains('LOG START')) & (df['Mode'] == 'maintenance')]
    node_start = pd.concat([start, maintenance_start], axis = 0).sort_values('Datetime',ascending=True)
    
    log_start_idx = list(log_start.index.values)
    node_start_idx = list(node_start.index.values)
    node_end_idx = list(node_end.index.values)

    # skip all endpoint entries (in case endpoints are filtered)
    endpoint_idx = list(set(log_start_idx + node_start_idx + node_end_idx))
    df = df.drop(endpoint_idx)
    df.reset_index(drop=True, inplace=True)
    
    # Remove startup and shutdown interlocks
    ## keep separate because node start does not mean node ended properly every time (ex. unexpected shutdown)
    
    # filter interlocks that occur 30 seconds after node starts and duration is less than 2 minutes
    for start in node_start['Datetime']:
        limit = start + datetime.timedelta(seconds=30)
        df_temp = df.loc[(df['Datetime'] > start) & (df['Datetime'] < limit)]
        for idx, duration in zip(df_temp.index.values, df_temp['Interlock Duration (min)']):
            if duration == 'Still Active':
                pass
            elif duration < 2:
                filter_out_idx.append(idx)
                interlock_type.append('Startup Interlock')
    
    #filter interlocks that occur one minute before node shutsdown 
    for end in node_end['Datetime']:     
        limit = end - datetime.timedelta(minutes=1) #filter shutdown interlocks
        df_temp = df.loc[(df['Datetime'] < end) & (df['Datetime'] > limit)]
        filter_out_idx.extend(df_temp.index.values) 
        interlock_type.extend(['Shutdown Interlock']*len(df_temp))
        
    # filter interlocks that occur between node end and another node/log start
    after_end = pd.concat([log_start, node_start, df.iloc[[-1],:]]) # find indices between node end and log/start/end of dataframe 
    after_end.sort_values('Datetime', inplace=True)
    
    for end in node_end['Datetime']:
        try:
            after_time = after_end.loc[after_end['Datetime'] > end]['Datetime'].iloc[0]
            df_temp = df.loc[(df['Datetime'] > end) & (df['Datetime'] < after_time)]
            filter_out_idx.extend(df_temp.index.values)
            interlock_type.extend(['Shutdown Interlock']*len(df_temp))
        except: #node_end is last entry, so no interlocks to find
            pass
      
    # Combine index and interlock type to sort values by index 
    expected_interlocks = pd.DataFrame({'IDX': filter_out_idx, 'Type':interlock_type})
    expected_interlocks = expected_interlocks.drop_duplicates(subset=['IDX']).sort_values(['IDX'])   #remove duplicates and sort
                                                                                                            
    # Separate interlocks_df into filtered and unfiltered
    # Create new dataframe that removed expected interlocks 
    filtered = df.drop(list(expected_interlocks['IDX']))
    
    # Add new 'Expected Interlock Type' column to original unfiltered interlocks dataframe
    df['Expected Interlock Type'] = ['']*len(df)
    df['Expected Interlock Type'][list(expected_interlocks['IDX'])] = list(expected_interlocks['Type'])

    # finalize filtered and filtered out dataframes
    # insert start and end times and sort by date and active time
    unfiltered = pd.concat([df, log_start], axis=0, sort=False)
    unfiltered = pd.concat([unfiltered, node_start], axis=0, sort=False)
    unfiltered = pd.concat([unfiltered, node_end], axis=0, sort=False)
    
    filtered = pd.concat([filtered, log_start], axis=0, sort=False)
    filtered = pd.concat([filtered, node_start], axis=0, sort=False)
    filtered = pd.concat([filtered, node_end], axis=0, sort=False)

    # Sort and reset both filter and unfiltered dataframes 
    unfiltered.sort_values('Datetime', ascending=True, inplace=True)
    unfiltered.reset_index(drop=True, inplace=True)
    filtered.sort_values('Datetime', ascending=True, inplace=True)
    filtered.reset_index(drop=True, inplace=True)
    
    # Clean up dataframes    
    filtered = filtered.reindex(columns=column_names)
    column_names.insert(6, 'Expected Interlock Type')
    unfiltered = unfiltered.reindex(columns=column_names)
    
    endpoints_idx  = unfiltered.loc[unfiltered['Interlock Number'].str.contains('LOG|NODE')].index.values
    unfiltered.iloc[endpoints_idx,6:] = ''
    return(filtered, unfiltered)                