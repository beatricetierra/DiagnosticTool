# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 09:47:29 2020

@author: btierra
"""
import os
import csv
import pandas as pd
import DiagnosticTool as dt

def DeleteFiles(folderpath):
    for root, dirs, files in os.walk(folderpath):
        for file in files:
            if '.log' not in file:
                os.remove(os.path.join(root, file))
            elif 'kvct' not in file:
                if 'pet' not in file:
                    if 'sysnode' not in file:
                        os.remove(os.path.join(root, file))
    return

def GetSWVersion(folderpath):
    filenames = dt.GetFiles(folderpath)
    dates = []
    files = []
    sw_version = []
    key = '* current branch: '
    
    for file in filenames:
        if '-kvct-' in file:
            with open(file) as log:
                for line in log:
                    if key in line:
                        entry = line.split(key)
                        sw_version.append(entry[-1].strip('\n'))
                        dates.append(file.split('\\')[-2])
                        files.append(file.split('\\')[-1])
                    
    sw_list = pd.DataFrame({'Date': dates, 'File': files,  'SW Version': sw_version})
    summary = sw_list.groupby('Date')['SW Version'].apply(lambda x: ','.join(x)).reset_index()
    summary['SW Version'] = [','.join(list(set(summary['SW Version'][i].split(',')))) for i in range(0,len(summary))]
    
    #To Save
    sw_list.to_csv(folderpath+'\sw_list.csv', index=False, sep='\t', quoting=csv.QUOTE_NONE)
    summary.to_csv(folderpath+'\summary.csv', index=False, sep='\t', quoting=csv.QUOTE_NONE)
    return(sw_list, summary) 