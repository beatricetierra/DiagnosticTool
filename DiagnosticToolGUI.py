# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 12:04:59 2020

@author: btierra
"""
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import tkinter.font as font
from tkcalendar import DateEntry
import DiagnosticToolGUISubfunctions as Subfunctions
from GetInterlocks import GetInterlocks as get
from threading import Thread

class Page(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
    def show(self):
        self.lift()

class Page1(Page):
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
      
       Frame = tk.Frame(self)
       Frame.place(relx=0.5, relwidth=0.95, relheight=1, anchor='n')
       
       ##### Scrollbox to list details of chosen log files #####
       scrollFrame = tk.Frame(Frame, bd=1, relief='solid')
       scrollFrame.place(relx=0.43, rely=0.28, relwidth=0.86, relheight=0.7, anchor='n')
       
       Page1.tree = ttk.Treeview(scrollFrame)
       Page1.tree['show'] = 'headings'
       
       scrollbar_x = ttk.Scrollbar(scrollFrame, orient="horizontal", command=Page1.tree.xview)
       scrollbar_y  = ttk.Scrollbar(scrollFrame, orient="vertical", command=Page1.tree.yview)
       
       Page1.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
       Page1.tree.grid(column=0, row=0, sticky='nsew', in_=scrollFrame)
       scrollbar_y.grid(column=1, row=0, sticky='ns', in_=scrollFrame)
       scrollbar_x.grid(column=0, row=1, sticky='ew', in_=scrollFrame)
       scrollFrame.grid_columnconfigure(0, weight=1)
       scrollFrame.grid_rowconfigure(0, weight=1)
       
       columns = ['File', 'Size', 'Path']
       Page1.tree["columns"] = columns
       [Page1.tree.heading(col, text=col, anchor='w', command=lambda c=col: Subfunctions.sortby(Page1.tree, c, 0, True)) for col in columns]
       Page1.tree.column('File', width=250, stretch='no')
       Page1.tree.column('Size', width=100, stretch='no')
       Page1.tree.column('Path', width=400, stretch='no')
       
       ###### Import remote machine ######      
       remoteFrame = tk.Frame(Frame, bd=1, relief="groove")
       remoteFrame.place(relx=0.25,rely=0.02, relwidth=0.5, relheight=0.25, anchor='n')
       remoteLabel = tk.Label(remoteFrame, text="Import from remote machine: ", font='Helvetica 12 bold', anchor='w')
       remoteLabel.place(relx=0.01, rely=0.01, relwidth=0.4, relheight=0.15)
       
       #IP Address label and text entry box
       ipLabel = tk.Label(remoteFrame, text="IP Address:", font='Helvetica 10')
       ipLabel.place(relx=0.16, rely=0.25, relwidth=0.15, relheight=0.15, anchor='e')
       ipaddress = tk.StringVar()
       ipEntry = tk.Entry(remoteFrame, textvariable=ipaddress, width = 50)
       ipEntry.place(relx=0.17, rely=0.25, relwidth=0.6, relheight=0.12, anchor='w')
       
       #username label and text entry box
       usernameLabel = tk.Label(remoteFrame, text="User:", font='Helvetica 10')
       usernameLabel.place(relx=0.19, rely=0.4, relwidth=0.15, relheight=0.15, anchor='e')
       username = tk.StringVar()
       usernameEntry = tk.Entry(remoteFrame, textvariable=username, width = 50)
       usernameEntry.place(relx=0.17, rely=0.4, relwidth=0.6, relheight=0.12, anchor='w')
      
       #password label and password entry box
       passwordLabel = tk.Label(remoteFrame,text="Password:", font='Helvetica 10')
       passwordLabel.place(relx=0.16, rely=0.55, relwidth=0.15, relheight=0.15, anchor='e')
       password = tk.StringVar()
       passwordEntry = tk.Entry(remoteFrame, textvariable=password, show='*', width = 50)
       passwordEntry.place(relx=0.17, rely=0.55, relwidth=0.6, relheight=0.12, anchor='w')
       
       #Date range input
       times = [str(hour) + ':00' for hour in list(range(0,24))] + ['23:59']
       daterangeLabel = tk.Label(remoteFrame, text="Date Range:", font='Helvetica 10')
       daterangeLabel.place(relx=0.16, rely=0.7, relwidth=0.15, relheight=0.15, anchor='e')
       toLabel = tk.Label(remoteFrame, text="to", font='Helvetica 10')
       toLabel.place(relx=0.42, rely=0.7, relwidth=0.1, relheight=0.15, anchor='w')
       
       startdate = DateEntry(remoteFrame,width=7,bg="darkblue",fg="white")
       startdate.place(relx=0.17, rely=0.7, relwidth=0.15, relheight=0.15, anchor='w')
       startdate._top_cal.overrideredirect(False)
       starttime = tk.Spinbox(remoteFrame, values=times, width=6)
       starttime.place(relx=0.33, rely=0.7, relwidth=0.1, relheight=0.15, anchor='w')
       
       enddate = DateEntry(remoteFrame,width=7,bg="darkblue",fg="white")
       enddate.place(relx=0.51, rely=0.7, relwidth=0.15, relheight=0.15, anchor='w')
       enddate._top_cal.overrideredirect(False)
       timevar = tk.IntVar()
       endtime = tk.Spinbox(remoteFrame, values=times, textvariable = timevar, width=6)
       timevar.set(times[-1])
       endtime.place(relx=0.67, rely=0.7, relwidth=0.1, relheight=0.15, anchor='w')
              
       #Output folder to store logs and reports
       outputLabel = tk.Label(remoteFrame,text="Output:", font='Helvetica 10')
       outputLabel.place(relx=0.16, rely=0.85, relwidth=0.15, relheight=0.15, anchor='e')
       button_output = tk.Button(remoteFrame , text='Select', font='Helvetica 10', command=lambda: self.addFolder('folderpath'))
       button_output.place(relx=0.67, rely=0.8, relwidth=0.1, relheight=0.12)

       self.output = tk.StringVar()
       self.outputEntry = tk.Entry(remoteFrame, textvariable=self.output, width = 45)
       self.outputEntry.place(relx=0.17, rely=0.85, relwidth=0.5, relheight=0.12, anchor='w') 
       
       #Buttons
       ConnectServerButton = tk.Button(remoteFrame, text="Get Logs", font=30, relief='raised', 
                                       command=lambda: Thread(target=Subfunctions.ConnectServer, daemon=True,
                  args=(Page1, ipaddress, username, password, startdate, starttime, enddate, endtime, self.output, ConnectServerButton)).start())
       ConnectServerButton.place(relx=0.8, rely=0.2, relwidth=0.15, relheight=0.15)
       
       ######  Import local drive ###### 
       self.localFrame = tk.Frame(Frame, bd=1, relief="groove")
       self.localFrame.place(relx=0.75, rely=0.02, relwidth=0.5, relheight=0.25, anchor='n')
       localLabel = tk.Label(self.localFrame, text="Import from local drive: ", font='Helvetica 12 bold', anchor='w')
       localLabel.place(relx=0.01, rely=0.01, relwidth=0.4, relheight=0.15)

       # Buttons for List of Files
       button_selectfolder = tk.Button(self.localFrame , text='Add Folder', font=10, command=lambda: self.addFolder('files'))
       button_selectfolder.place(relx=0.01, rely=0.2, relwidth=0.25, relheight=0.15)
          
       button_add = tk.Button(self.localFrame , text='Add File', height=1, width=8, font=10, command=self.addFile)
       button_add.place(relx=0.01, rely=0.42, relwidth=0.25, relheight=0.15)
       
       # Buttons to choose between reading LogNode or Kvct/Pet_Recon/SysNode files
       chooseLabel = tk.Label(self.localFrame, text='Choose node:', font='Helvetica 10')
       chooseLabel.place(relx=0.01, rely=0.62, relwidth=0.35, relheight=0.15)
       
       self.node = tk.IntVar()
       self.node.set(2)
       lognodeButton = tk.Radiobutton(self.localFrame, text='LogNode', variable=self.node, value=1, command=lambda: self.node.set(1))
       lognodeButton.place(relx=0.3, rely=0.62, relwidth=0.15, relheight=0.15)
       nodesButton = tk.Radiobutton(self.localFrame, text='KVCT, Pet Recon, Sysnode', variable=self.node, value=2, command=lambda: self.node.set(2))
       nodesButton.place(relx=0.45, rely=0.62, relwidth=0.4, relheight=0.15) 
       
       ######  Edit List Box ###### 
       editFrame = tk.Frame(Frame, bd=1)
       editFrame.place(relx=0.93, rely=0.28, relwidth=0.14, relheight=0.7, anchor='n')
       
       button_delete_select = tk.Button(editFrame , text='Delete', font=15, command=self.deleteFile_selected)
       button_delete_select.place(relx=0.01, rely=0.35, relwidth=0.99, relheight=0.1)
          
       button_delete = tk.Button(editFrame, text='Delete All', font=15, command=self.deleteFile_all)
       button_delete.place(relx=0.01, rely=0.45, relwidth=0.99,relheight=0.1)
       
       button_view = tk.Button(editFrame, text='View Results', command=lambda: Subfunctions.DisplayEntries(Page2, Page3, MainView))
       button_view.place()
       
       button_find = tk.Button(editFrame, text='Find Interlocks', command=lambda: Thread(
               target=self.findInterlocks, args=(button_view,), daemon=True).start(), font='Calibri 15 bold', borderwidth = '4')
       button_find.place(relx=0.01, rely=0.9, relwidth=0.99, relheight=0.1)
       
   def addFolder(self, output):
       folder = filedialog.askdirectory()
       
       if output == 'files':
           files = Subfunctions.GetFiles(folder)
           Page1.addFileDetails(self.tree, files)
       elif output == 'folderpath':
           self.outputEntry.delete(0, 'end')
           self.outputEntry.insert('end', folder)
      
   def addFile(self):
       content = filedialog.askopenfilenames(title='Choose files', filetypes=[('Text Document', '*.log')])
       Page1.addFileDetails(self.tree, content)
       
   def addFileDetails(tree, file_list):
       for file in file_list:
           if '\\' in file:
               file = file.replace('\\', '/')
           parse = file.split('/')
           filename = parse[-1]
           size = int((os.stat(file).st_size)/1000)
           path = ('/').join(parse[:-1])
           tree.insert('', 'end', values=[filename,size,path])
       
   def deleteFile_all(self):
       [self.tree.delete(i) for i in self.tree.get_children()]
    
   def deleteFile_selected(self):
       selected_item = self.tree.selection()[0]
       self.tree.delete(selected_item)
       
   def findInterlocks(self,button_view):
       global files
       global kvct_df, kvct_filtered, kvct_unfiltered, filtered_couchinterlocks
       global recon_df, recon_filtered, recon_unfiltered
       global system, dates
       
       # Clear old entries, restart progress bar, and reset toggled buttons
       [widget.destroy() for widget in Page2.Frame.winfo_children()]
       [widget.destroy() for widget in Page3.Frame.winfo_children()]    
       Page2.toggleButton.config(relief="raised")
       Page3.toggleButton.config(relief="raised")
       MainView.progress['value'] = 0
       
       # store all files listed in window and find interlocks
       files=[]
       if not self.tree.get_children():
           messagebox.showerror("Error", "No files found.")
           return
       else:
           for child in self.tree.get_children():
              files.append(self.tree.item(child)["values"][-1]+'/'+self.tree.item(child)["values"][0])
              
       # Check if given files and node selected match
       node = self.node.get()
       if node == 1:
           if any(['-log-' in file for file in files]):
               pass
           else:
               messagebox.showerror(message='No LogNode files found. Select \'KVCT , Pet_Recon, Sysnode\'.')
               return
       elif node == 2:
           if any(['-kvct-' in file or '-pet_recon-' in file or '-sysnode-' in file for file in files]):
               pass
           else:
               messagebox.showerror(message='KVCT, Pet_Recon, and/or Sysnode files were not found. Select \'LogNode\'.')
               return
      
       # Find interlock dataframes
       try:
           system, kvct_df, recon_df, dates = Subfunctions.FindEntries(files, node)
           if kvct_df.empty and recon_df.empty:         # Return if both dataframes are empty
               messagebox.showerror("Error", "No KVCT or Recon interlocks found.")
               return
           else:
               pass
       except:
           messagebox.showerror("Error", "Cannot find entries for listed files.")
           return
       # Filter interlock dataframes
       kvct_filtered, kvct_unfiltered, filtered_couchinterlocks, recon_filtered, recon_unfiltered = Subfunctions.FilterEntries(kvct_df, recon_df)
       # View dataframes
       button_view.invoke()
       return

class Page2(Page):
    def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       
       Page2.Frame = tk.Frame(self, bd=1, relief='solid')
       Page2.Frame.place(relx=0.5, rely=0.08, relwidth=0.99, relheight=0.91, anchor='n')
       
       Page2.toggleButton = tk.Button(self, text="Filter Expected Interlocks", width=12, relief="raised", command=Page2.toggle)
       Page2.toggleButton.place(relx=0.4, rely=0.02, relwidth=0.15, relheight=0.04)
           
       # Add filtering menubars
       FilterButtons = tk.Frame(self)
       FilterButtons.place(relx=0.65, relwidth=0.35, relheight=0.08, anchor='nw')
       
       Page2.menubar = tk.Menubutton(FilterButtons, text='Filter KVCT Interlocks \u25BE', font=14, relief='raised')
       Page2.menubar.place(rely=0.5, relwidth=0.55, relheight=0.45)
       
       button_filter = tk.Button(FilterButtons, text="Filter", font=20, command = Page2.filter_by_interlock)
       button_filter.place(relx=0.6, rely=0.5, relwidth=0.2, relheight=0.45)
       
       button_selectall = tk.Button(FilterButtons, text="Select All", font=12, command=Page2.selectall)
       button_selectall.place(relwidth= 0.22, relheight=0.45)
       
       button_selectnone = tk.Button(FilterButtons, text="Select None", font=12, command=Page2.selectnone)
       button_selectnone.place(relx=0.25,relwidth=0.28, relheight=0.45)
    
    def toggle():
       if Page2.toggleButton.config('relief')[-1] == 'sunken':
           Page2.toggleButton.config(relief="raised")
           [widget.destroy() for widget in Page2.Frame.winfo_children()]
           Subfunctions.df_tree(kvct_unfiltered, Page2.Frame)
           Page2.menubar_filter(kvct_unfiltered, Page2.menubar)
       else:
           Page2.toggleButton.config(relief="sunken")
           [widget.destroy() for widget in Page2.Frame.winfo_children()]
           Subfunctions.df_tree(kvct_filtered, Page2.Frame)
           Page2.menubar_filter(kvct_filtered, Page2.menubar)
            
    def menubar_filter(df, menubar):
        global kvct_interlock_set 
        if df.empty == False:
            items = sorted(list(set(df['Interlock Number'])))
            
            menubar.menu = tk.Menu(menubar, tearoff=0)
            menubar["menu"] = menubar.menu
            
            kvct_interlock_set = {}
            for idx, item in enumerate(items):
                var = tk.BooleanVar()
                var.set(True)
                menubar.menu.add_checkbutton(label=item, variable=var)
                kvct_interlock_set[str(item)] = var
        else:
            pass
       
    def filter_by_interlock():
        interlock_list = []
        for interlock, var in kvct_interlock_set.items():
            if var.get() == True:
                interlock_list.append(interlock)
                
        if Page2.toggleButton.config('relief')[-1] == 'raised':
            df1 = kvct_unfiltered[kvct_unfiltered['Interlock Number'].isin(interlock_list)]
            [widget.destroy() for widget in Page2.Frame.winfo_children()]
            Subfunctions.df_tree(df1, Page2.Frame)
        elif Page2.toggleButton.config('relief')[-1] == 'sunken':
            df2 = kvct_filtered[kvct_filtered['Interlock Number'].isin(interlock_list)]
            [widget.destroy() for widget in Page2.Frame.winfo_children()]
            Subfunctions.df_tree(df2, Page2.Frame)

    def selectall():
        for interlock, var in kvct_interlock_set.items():
            var.set(True)
        Page2.filter_by_interlock()
    def selectnone():
        for interlock, var in kvct_interlock_set.items():
            var.set(False)
        Page2.filter_by_interlock()
            
class Page3(Page):
    def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       
       Page3.Frame = tk.Frame(self, bd=1, relief='solid')
       Page3.Frame.place(relx=0.5, rely=0.08, relwidth=0.99, relheight=0.91, anchor='n')
       
       Page3.toggleButton = tk.Button(self, text="Filter Expected Interlocks", width=12, relief="raised", command=Page3.toggle)
       Page3.toggleButton.place(relx=0.4, rely=0.02, relwidth=0.15, relheight=0.04)
           
       # Add filtering menubars
       FilterButtons = tk.Frame(self)
       FilterButtons.place(relx=0.65, relwidth=0.35, relheight=0.08, anchor='nw')
       
       Page3.menubar = tk.Menubutton(FilterButtons, text='Filter Recon Interlocks \u25BE', font=20, relief='raised')
       Page3.menubar.place(rely=0.5, relwidth=0.55, relheight=0.45)
       
       button_filter = tk.Button(FilterButtons, text="Filter", font=20, command = Page3.filter_by_interlock)
       button_filter.place(relx=0.6, rely=0.5, relwidth=0.2, relheight=0.45)
       
       button_selectall = tk.Button(FilterButtons, text="Select All", font=20, command=Page3.selectall)
       button_selectall.place(relwidth= 0.22, relheight=0.45)
       
       button_selectnone = tk.Button(FilterButtons, text="Select None", font=20, command=Page3.selectnone)
       button_selectnone.place(relx=0.25,relwidth=0.28, relheight=0.45)
    
    def toggle():
       if Page3.toggleButton.config('relief')[-1] == 'sunken':
           Page3.toggleButton.config(relief="raised")
           [widget.destroy() for widget in Page3.Frame.winfo_children()]
           Subfunctions.df_tree(recon_unfiltered, Page3.Frame)
           Page3.menubar_filter(recon_unfiltered, Page3.menubar)
       else:
           Page3.toggleButton.config(relief="sunken")
           [widget.destroy() for widget in Page3.Frame.winfo_children()]
           Subfunctions.df_tree(recon_filtered, Page3.Frame)
           Page3.menubar_filter(recon_filtered, Page3.menubar)
            
    def menubar_filter(df, menubar):
        global recon_interlock_set 
        if df.empty == False:
            items = sorted(list(set(df['Interlock Number'])))
            
            menubar.menu = tk.Menu(menubar, tearoff=0)
            menubar["menu"] = menubar.menu
            
            recon_interlock_set = {}
            for idx, item in enumerate(items):
                var = tk.BooleanVar()
                var.set(True)
                menubar.menu.add_checkbutton(label=item, variable=var)
                recon_interlock_set[str(item)] = var
        else:
            pass
       
    def filter_by_interlock():
        interlock_list = []
        for interlock, var in recon_interlock_set.items():
            if var.get() == True:
                interlock_list.append(interlock)
                
        if Page3.toggleButton.config('relief')[-1] == 'raised':
            df1 = recon_unfiltered[recon_unfiltered['Interlock Number'].isin(interlock_list)]
            [widget.destroy() for widget in Page3.Frame.winfo_children()]
            Subfunctions.df_tree(df1, Page3.Frame)
        elif Page3.toggleButton.config('relief')[-1] == 'sunken':
            df2 = recon_filtered[recon_filtered['Interlock Number'].isin(interlock_list)]
            [widget.destroy() for widget in Page3.Frame.winfo_children()]
            Subfunctions.df_tree(df2, Page3.Frame)

    def selectall():
        for interlock, var in recon_interlock_set.items():
            var.set(True)
        Page3.filter_by_interlock()
    def selectnone():
        for interlock, var in recon_interlock_set.items():
            var.set(False)
        Page3.filter_by_interlock()

class MainView(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        
        # Menu Bar
        menubar = tk.Menu(self)
        file = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='File', menu = file)
        file.add_command(label='Save Results', command = Subfunctions.exportExcel)
        
        analyze = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Analyze', menu = analyze)
        analyze.add_command(label='Summary Report', command = Subfunctions.SummarizeResults)
        root.config(menu=menubar)
        
        # Navigate between pages
        MainView.p1 = Page1(self)
        MainView.p2 = Page2(self)
        MainView.p3 = Page3(self)

        buttonframe = tk.Frame(self)
        container = tk.Frame(self)
        buttonframe.pack(side="top", anchor='nw')
        container.pack(side="top", fill="both", expand=True)

        MainView.p1.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        MainView.p2.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        MainView.p3.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        
        Font = font.Font(family='Helvetica', weight='bold', size=12)
    
        MainView.b1 = tk.Button(buttonframe, text="Choose Files", font=Font, command=lambda: MainView.SwitchPage(MainView.p1))
        MainView.b2 = tk.Button(buttonframe, text="Kvct Results", font=Font, command=lambda: MainView.SwitchPage(MainView.p2))
        MainView.b3 = tk.Button(buttonframe, text="Recon Results", font=Font, command=lambda: MainView.SwitchPage(MainView.p3))

        MainView.b1.pack(side="left")
        MainView.b2.pack(side="left")
        MainView.b3.pack(side="left")

        MainView.p1.show()

        # Progress Bar
        MainView.progress_style = ttk.Style(root)
        # add label in the layout
        MainView.progress_style.layout('text.Horizontal.TProgressbar', 
                     [('Horizontal.Progressbar.trough',
                       {'children': [('Horizontal.Progressbar.pbar',
                                      {'side': 'left', 'sticky': 'ns'})],
                        'sticky': 'nswe'}), 
                      ('Horizontal.Progressbar.label', {'sticky': ''})])
        MainView.progress = ttk.Progressbar(self, style='text.Horizontal.TProgressbar', orient='horizontal', mode='determinate')
        MainView.progress.pack(side='bottom', fill='x')
        get(MainView.progress, MainView.progress_style, root)
        
    def SwitchPage(page):
        page.lift()
        if page == MainView.p1:
            MainView.b1.config(relief='sunken')
            MainView.b2.config(relief='raised')
            MainView.b3.config(relief='raised')
        elif page == MainView.p2:
            MainView.b1.config(relief='raised')
            MainView.b2.config(relief='sunken')
            MainView.b3.config(relief='raised')
        elif page == MainView.p3:
            MainView.b1.config(relief='raised')
            MainView.b2.config(relief='raised')
            MainView.b3.config(relief='sunken')     
    
if __name__ == "__main__":
    root = tk.Tk()
    main = MainView(root)
    main.pack(side="top", fill="both", expand=True)
    root.wm_geometry("1200x800")
    root.title('KVCT Diagnostic Tool')
    root.mainloop()

