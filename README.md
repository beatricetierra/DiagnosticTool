## Table of Contents
1. [General Info](#general-info)
2. [Basic Process](#basic-process)
3. [Create Executable](#create-executable)

### General Info
***
The Dianostic Tool GUI was created as an in-house tool to analyze the interlocks that occured on the RefleXion System, specifically for the kVCT subsystem. 
This tool was built to:
* Save time on trouble shooting system
* Report statistics of issue investigations
* Monitor system automatically for reliablity measurements

## Basic Process
***
The basic backed process and overall steps of the tool: 
1. Import log files from remote system database 
2. Extract entries containing certain find keys (determined by system owner)
3. Construct dataframes centered around the found interlock issues
4. Filter expected interlocks to rid of noise (highlights persistent issues)
5. Reports stats and visualization of interlocks
6. Sends report through Slack message to specified users 

## Create Executable
***
To install GUI:
1. Git clone https://github.com/beatricetierra/DiagnosticTool
2. Using Python 3.7, install the following packages:
    * tkcalendar
    * pandas
    * matplotlib
    * paramiko
    * scp
    * xlrd
    * xlsxwriter
    * pyinstaller
3. cd to cloned directory and run the following command: pyinstaller --hidden-import "babel.numbers" --hidden-import "cmath" --onefile --noconsole DiagnosticToolGUI.py
4. Executable located in 'dist' folder
