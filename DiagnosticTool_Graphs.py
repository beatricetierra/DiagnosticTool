# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 13:42:58 2020

@author: btierra
"""

def unfilt_graphing(unfilt_analysis):
    # Shorten Interlock Number Description for graphing
    try:
        unfilt_analysis['Interlock Number'] = [idx.split(":")[1] for idx in unfilt_analysis['Interlock Number']]
    except:
        pass
    
    # Total count vs interlocks
    count = unfilt_analysis.groupby('Interlock Number').sum().iloc[:,:3]
    count.plot(kind='bar', title='Total Count per Interlock')
    
    # total count vs session
    session = unfilt_analysis.groupby('Session').sum().iloc[:,:3]
    session.plot(kind='bar', title='Total Interlocks per Session')
    
    # total count vs interlocks per session
    sessions = list(set(unfilt_analysis['Session']))
    for session in sessions:
        df = unfilt_analysis.loc[unfilt_analysis['Session'] == session].iloc[:,:5]
        df = df.groupby('Interlock Number').sum()
        df.plot(kind='bar', title=str(session) + ' Total Interlocks')