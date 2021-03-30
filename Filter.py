# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 16:11:45 2021

@author: btierra
"""
import settings as var
import pandas as pd
import datetime 

class Filters():
    def __init__(self, df):
        # Instert datetime column
        self.df = df.copy()
        datetimes = pd.to_datetime(self.df['Date'].apply(str)+' '+self.df['Active Time'].apply(str))
        self.df.insert(0, 'Datetime', datetimes) 
    
    def StartUpInterlockRows(self):
        filter_type = []
        startup_interlock_idx = []
        for (idx, time), duration in zip(self.df['Time from Node Start (min)'].items(), self.df['Interlock Duration (min)']):
            try:
                if time < 0.5 and duration < 2: # 30 seconds
                    startup_interlock_idx.append(idx)
                    filter_type.append('startup')
            except TypeError:
                pass
        return startup_interlock_idx, filter_type

    def ShutDownInterlockRows(self):
        filter_type = []
        shutdown_interlock_idx = []
        node_ends = self.df.loc[self.df['Interlock Number'].str.contains('NODE END')]
        for end in node_ends['Datetime']:
            lowerlimit = end - datetime.timedelta(minutes=1) 
            upperlimit = end
            rows_between = self.df.loc[(self.df['Datetime'] > lowerlimit) & (self.df['Datetime'] < upperlimit)]
            rows_between_idx = rows_between.index.values
            shutdown_interlock_idx.extend(rows_between_idx)
            filter_type.extend(['shutdown']*len(rows_between_idx))
        return shutdown_interlock_idx, filter_type
    
    def AfterShutDownInterlockRows(self):
        filter_type = []
        after_shutdown_interlock_idx = []
        
        # Filter interlocks between node_end and log_start
        node_ends = self.df.loc[self.df['Interlock Number'].str.contains('NODE END')]
        log_starts = self.df.loc[self.df['Interlock Number'].str.contains('LOG START')]
        try: # Add last entry of df incase no logstart after node end
            log_starts.append(self.df.iloc[-1]) 
        except IndexError:  # In case empty df
            return after_shutdown_interlock_idx, filter_type
        
        for end in node_ends['Datetime']:
            try:
                lowerlimit = end
                upperlimit = log_starts.loc[log_starts['Datetime'] > end]['Datetime'].iloc[0]
                rows_between = self.df.loc[(self.df['Datetime'] > lowerlimit) & (self.df['Datetime'] < upperlimit)]
                rows_between_idx = rows_between.index.values
                after_shutdown_interlock_idx.extend(rows_between_idx)
                filter_type.extend(['after shutdown']*len(rows_between_idx))
            except:
                pass
        return after_shutdown_interlock_idx, filter_type
        
    def RowsMeetColumnConditions(self, node):
        global filter_conditions, filter_on
        all_expected_interlocks_idx = []
        all_filter_types = []
        
        try:
            filter_conditions = var.FilterByDescriptionAndTime[node]  
        except:
            return all_expected_interlocks_idx, all_filter_types
        
        for filter_on, conditions in filter_conditions.items():
            expected_interlocks_idx, filter_types = self.GetConditionalRows(node)                 
            all_expected_interlocks_idx.extend(expected_interlocks_idx)
            all_filter_types.extend(filter_types)
        return all_expected_interlocks_idx, all_filter_types
    
    def GetConditionalRows(self, node):
        global expected_interlocks_idx, filter_types
        global filter_interlock, interlock_rows
        expected_interlocks_idx = []
        filter_types = []
        filter_interlocks = filter_conditions[filter_on]
        
        for filter_interlock, conditions in filter_interlocks.items():
            interlock_rows = self.df[self.df['Interlock Number'].str.contains(filter_interlock)]
            if interlock_rows.empty:
                pass
            else:
                for condition in conditions:
                    if filter_on == 'Description':
                        self.PerColumnDescription(condition)
                    if filter_on == 'Time':
                        self.PerColumnTime(condition)
                    if filter_on == 'DescriptionAndTime':
                        self.PerColumnDescriptionAndTime(condition)
        return expected_interlocks_idx, filter_types
                    
    def PerColumnDescription(self, condition):
        global key, contains, column_name_desc
        
        if not condition:
            expected_interlocks_idx.extend(interlock_rows.index.values)
            filter_types.extend([filter_interlock]*len(interlock_rows))
        else:
            key, contains, column_name_desc = self.ExtractConditionInputs('Description', condition)
            for idx, row in interlock_rows.iterrows():
                if contains == "in":
                    if key in row[column_name_desc]:
                        expected_interlocks_idx.append(idx)
                        filter_types.append(' '.join(condition))
                if contains == "not in":
                    if key not in row[column_name_desc]:
                        expected_interlocks_idx.append(idx)
                        filter_types.append(' '.join(condition))
    
    def PerColumnTime(self, condition):
        global placement, column_name_time, compare, time_limit

        placement, column_name_time, compare, time_limit = self.ExtractConditionInputs('Time', condition)
        interlock_times = interlock_rows['Datetime']
        column_times = interlock_rows[column_name_time]
        
        for (idx, interlock_time), column_time in zip(interlock_times.items(), column_times):
            if not isinstance(column_time,str):
                if self.EvalTimeConditionCommands(interlock_time, column_time):
                    expected_interlocks_idx.append(idx)
                    filter_types.append('close to {col_name}'.format(col_name = column_name_time))

    def PerColumnDescriptionAndTime(self, condition):
        global key, contains, column_name_desc
        global placement, column_name_time, compare, time_limit
        
        key, contains, column_name_desc = self.ExtractConditionInputs('Description', condition['Description'])
        placement, column_name_time, compare, time_limit = self.ExtractConditionInputs('Time', condition['Time'])

        desc_column = interlock_rows[column_name_desc]
        time_column = interlock_rows[column_name_time]
        interlock_times = interlock_rows['Datetime']
        
        for (idx, desc), interlock_time, col_time in zip(desc_column.items(), interlock_times, time_column):
            if key in desc:
                try:
                    col_time = col_time.split(': ')[0]
                    if self.EvalTimeConditionCommands(interlock_time, col_time):
                        expected_interlocks_idx.append(idx)
                        filter_types.append(' '.join(condition['Description']) + 
                                           ' and close to {col_name}'.format(col_name = column_name_time))
                except:
                    pass
    
    def EvalTimeConditionCommands(self, interlock_time, column_time):
        interlocktime_str = 'datetime.datetime.strptime(\'{time}\', \'%Y-%m-%d %H:%M:%S.%f\')'.format(time=interlock_time)
        columntime_str = 'datetime.datetime.strptime(\'{time}\', \'%Y-%m-%d %H:%M:%S.%f\')'.format(time=column_time)
        time_limit_str = 'datetime.timedelta(seconds={time})'.format(time=time_limit)
        
        if placement == 'before':
            PassCondition = '{interlock_time} - {column_time} {comp} {time_limit}'.format(
                    interlock_time=interlocktime_str, column_time=columntime_str, comp=compare, time_limit=time_limit_str)
        elif placement == 'after':
            PassCondition = '{column_time} - {interlock_time} {comp} {time_limit}'.format(
                    interlock_time=interlocktime_str, column_time=columntime_str, comp=compare, time_limit=time_limit_str)
        elif placement == 'within':
            PassCondition = 'abs({interlock_time} - {column_time}) {comp} {time_limit}'.format(
                    interlock_time=interlocktime_str, column_time=columntime_str, comp=compare, time_limit=time_limit_str)
        return eval(PassCondition)

    def RowsRelativeToOtherInterlocks(self, node):
        global filter_conditions
        global other_interlock, time_limit, relative, pivot_column
        expected_interlocks_idx = []
        filter_types = []
        
        try:
            filter_conditions = var.FilterRelativeToOtherInterlocks[node]  
        except:
            return expected_interlocks_idx, filter_types
    
        for filter_interlock, conditions in filter_conditions.items():
            interlock_rows = self.df[self.df['Interlock Number'].str.contains(filter_interlock)]
            if interlock_rows.empty:
                pass
            else:
                for condition in conditions:
                    other_interlock, time_limit, relative, pivot_column = self.ExtractConditionInputs('Relative', condition)
                    
                    interlock_times = interlock_rows['Datetime']
                    other_interlock_rows = self.df.loc[self.df['Interlock Number'].str.contains(other_interlock)]
                    other_interlock_times = self.OtherInterlockTimes(other_interlock_rows)
    
                    for idx, interlock_time in interlock_times.items():
                        time_diff = self.RelativeTimeDifference(interlock_time, other_interlock_times)
                        if any(diff < time_limit for diff in time_diff):
                            expected_interlocks_idx.append(idx)
                            filter_types.append('close to {other_interlock}'.format(other_interlock = other_interlock))
        return expected_interlocks_idx, filter_types
    
    def OtherInterlockTimes(self, other_interlock_rows):
        if 'active' in pivot_column.lower():
            other_interlock_times = other_interlock_rows['Datetime'].to_list()
        elif 'inactive' in pivot_column.lower():
            other_interlock_times = [datetime.datetime.combine(date,time) for date,time in zip(
                        other_interlock_rows['Date'], other_interlock_rows['Inactive Time']) if isinstance(time, datetime.time)]
        elif 'both' in pivot_column.lower():
            other_interlock_times = other_interlock_rows['Datetime'].to_list()
            other_interlock_times_inactive = [datetime.datetime.combine(date,time) for date,time in zip(
                        other_interlock_rows['Date'], other_interlock_rows['Inactive Time']) if isinstance(time, datetime.time)]
            other_interlock_times.extend(other_interlock_times_inactive)
        return other_interlock_times
    
    def RelativeTimeDifference(self, interlock_time, other_interlock_times):
        if relative == 'before':
            time_diff = [interlock_time - other_interlock_time for other_interlock_time in other_interlock_times]
        elif relative == 'after':
            time_diff = [other_interlock_time - interlock_time for other_interlock_time in other_interlock_times]
        elif relative == 'within':
            time_diff = [abs(interlock_time - other_interlock_time) for other_interlock_time in other_interlock_times]
            
        time_diff = [diff.total_seconds() for diff in time_diff]
        return time_diff
    
    def ExtractConditionInputs(self, condition_type, condition):
        if condition_type == 'Description':
            key, contains, column_name_dec = [condition[i] for i in range(len(condition))]
            return key, contains, column_name_dec
        elif condition_type == 'Time':
            placement, column_name_time, compare, time_limit = [condition[i] for i in range(len(condition))]
            return placement, column_name_time, compare, time_limit
        elif condition_type == 'Relative':
            other_interlock, time_limit, relative, pivot_column = [condition[i] for i in range(len(condition))]
            return other_interlock, time_limit, relative, pivot_column
 
def FilterExpectedInterlocks(dfs):
    global df, filtered_idx, filtered_types
    
    unfiltered_dfs = {}
    filtered_dfs = {}
    for node, df in dfs.items():
        filt = Filters(df)
        
        filtered = []
        filtered.append(filt.StartUpInterlockRows())
        filtered.append(filt.ShutDownInterlockRows())
        filtered.append(filt.AfterShutDownInterlockRows())
        
        filtered.append(filt.RowsMeetColumnConditions(node))
        filtered.append(filt.RowsRelativeToOtherInterlocks(node))
        
        filtered_idx, filtered_types = GetFilteredRowAndTypes(filtered)
        
        unfiltered_dfs[node] = CreateUnfilteredDf()
        filtered_dfs[node] = CreateFilteredDf()

    return unfiltered_dfs, filtered_dfs

def GetFilteredRowAndTypes(filtered):
    filtered_idx, filtered_types = [], [] 
    endpoints = df.loc[df['Interlock Number'].str.contains('NODE END | NODE START | LOG START')]
    endpoints_idx = endpoints.index.values  # skip endpoints from filtering
    
    for tupe in filtered:
        for idx, filter_type in zip(tupe[0], tupe[1]):
            if idx not in endpoints_idx:
                filtered_idx.append(idx)
                filtered_types.append(filter_type)
    return filtered_idx, filtered_types

def CreateUnfilteredDf():
     # Create unfiltered df (add column of filter type -> why interlock was filtered)
    unfiltered_df = df.copy()
    expected_interlocks = pd.DataFrame({'IDX': filtered_idx, 'Type':filtered_types})
    expected_interlocks = expected_interlocks.drop_duplicates(subset=['IDX']).sort_values(['IDX']) 
    unfiltered_df.insert(6, 'Expected Interlock Type', ['']*len(unfiltered_df))
    unfiltered_df['Expected Interlock Type'][list(expected_interlocks['IDX'])] = list(expected_interlocks['Type'])
    return unfiltered_df

def CreateFilteredDf():
    # Filter original df
    filtered_df = df.copy()
    filtered_idx_unique = list(set(filtered_idx))
    filtered_df = filtered_df.drop(filtered_idx_unique)
    return filtered_df

