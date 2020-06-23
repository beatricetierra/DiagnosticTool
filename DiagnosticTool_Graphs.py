# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 13:42:58 2020

@author: btierra
"""
import matplotlib.pyplot as plt

def filtered_graphing(filtered_analysis):
     # Shorten Interlock Number Description for graphing
    try:
        filtered_analysis['Interlock Number'] = [idx.split(":")[1] for idx in filtered_analysis['Interlock Number']]
    except:
        pass
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15,5))
    # Total count vs interlocks
    count = filtered_analysis.groupby('Interlock Number').sum()['Count']
    count.plot(kind='bar', title='Total Count per Interlock', ax=ax1)
    
    # Start of Node and Interlock Duration Times
    average = filtered_analysis.groupby('Interlock Number').sum()['Avg Duration(sec)']
    std = filtered_analysis.groupby('Interlock Number').sum()['Std Duration(sec)']
    average.plot(kind='bar', yerr=[std], title='AVG Interlock Duration', ax=ax2)
    
def unfilt_graphing(unfilt_analysis):
    # Shorten Interlock Number Description for graphing
    try:
        unfilt_analysis['Interlock Number'] = [idx.split(":")[1] for idx in unfilt_analysis['Interlock Number']]
    except:
        pass
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15,5))
    # Total count vs interlocks
    count = unfilt_analysis.groupby('Interlock Number').sum().iloc[:,:3]
    count.plot(kind='bar', title='Total Count per Interlock', ax=ax1)
    
    # total count vs session
    session = unfilt_analysis.groupby('Session').sum().iloc[:,:3]
    session.plot(kind='bar', title='Total Interlocks per Session', ax=ax2)
    
    # total count vs interlocks per session
    sessions = list(set(unfilt_analysis['Session']))
    
    for session in sessions:
        df = unfilt_analysis.loc[unfilt_analysis['Session'] == session].iloc[:,:5]
        df = df.groupby('Interlock Number').sum()
        df.plot(kind='bar', title=str(session) + ' Total Interlocks')
        