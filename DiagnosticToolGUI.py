# -*- coding: utf-8 -*-
"""
Created on Thu Oct  8 12:04:59 2020

@author: btierra
"""
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import tkinter.font as font
import DiagnosticToolGUISubfunctions as Subfunctions
from GetInterlocks import GetInterlocks as get

class Page(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
    def show(self):
        self.lift()

class Page1(Page):
   def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
      
       Frame = tk.Frame(self)
       Frame.place(relx=0.5, relwidth=0.95, relheight=0.95, anchor='n')
       
       # Scrollbox to list details of chosen log files
       scrollFrame = tk.Frame(Frame, bd=1, relief='solid')
       scrollFrame.place(relx=0.42, rely=0.1, relwidth=0.80, relheight=0.9, anchor='n')
       
       self.tree = ttk.Treeview(scrollFrame)
       self.tree['show'] = 'headings'
       
       scrollbar_x = ttk.Scrollbar(scrollFrame, orient="horizontal", command=self.tree.xview)
       scrollbar_y  = ttk.Scrollbar(scrollFrame, orient="vertical", command=self.tree.yview)
       
       self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
       self.tree.grid(column=0, row=0, sticky='nsew', in_=scrollFrame)
       scrollbar_y.grid(column=1, row=0, sticky='ns', in_=scrollFrame)
       scrollbar_x.grid(column=0, row=1, sticky='ew', in_=scrollFrame)
       scrollFrame.grid_columnconfigure(0, weight=1)
       scrollFrame.grid_rowconfigure(0, weight=1)
       
       columns = ['File', 'Size', 'Path']
       self.tree["columns"] = columns
       [self.tree.heading(col, text=col, anchor='w', command=lambda c=col: Subfunctions.sortby(self.tree, c, 0, True)) for col in columns]
       self.tree.column('File', width=300, stretch='no')
       self.tree.column('Size', width=100, stretch='no')
       self.tree.column('Path', width=500, stretch='no')

       # Buttons for List of Files
       button_selectfolder = tk.Button(Frame, text='Select Folder', font=30, command=self.addFolder)
       button_selectfolder.place(relx=0.85, rely=0.1, relwidth=0.1, relheight=0.05)
          
       button_add = tk.Button(Frame, text='Add', font=15, command=self.addFile)
       button_add.place(relx=0.85, rely=0.4, relwidth=0.1, relheight=0.05)
       
       button_delete_select = tk.Button(Frame, text='Delete', font=15, command=self.deleteFile_selected)
       button_delete_select.place(relx=0.85, rely=0.45, relwidth=0.1, relheight=0.05)
          
       button_delete = tk.Button(Frame, text='Delete All', font=15, command=self.deleteFile_all)
       button_delete.place(relx=0.85, rely=0.5, relwidth=0.1, relheight=0.05)
       
       button_find = tk.Button(Frame, text='Find Interlocks', font=15, command=self.findInterlocks)
       button_find.place(relx=0.85, rely=0.9, relwidth=0.1, relheight=0.05)

   def addFolder(self):
       folder = filedialog.askdirectory()
       files = Subfunctions.GetFiles(folder)
       Page1.addFileDetails(self.tree, files)
      
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
       
   def findInterlocks(self):
       global files
       global kvct_df, kvct_filtered, kvct_unfiltered
       global recon_df, recon_filtered, recon_unfiltered
       global system, dates
       
       # Clear old entries and restart progress bar
       [widget.destroy() for widget in Page2.Frame.winfo_children()]
       [widget.destroy() for widget in Page3.Frame.winfo_children()]
       MainView.progress['value'] = 0
       
       # store all files listed in window and find interlocks
       files=[]
       if not self.tree.get_children():
           messagebox.showerror("Error", "No files found.")
       else:
           for child in self.tree.get_children():
              files.append(self.tree.item(child)["values"][-1]+'/'+self.tree.item(child)["values"][0])
           kvct_df, kvct_filtered, kvct_unfiltered, recon_df, recon_filtered, recon_unfiltered, system, dates = \
             Subfunctions.FindEntries(Page2, Page3, MainView, files)
      
class Page2(Page):
    def __init__(self, *args, **kwargs):
       Page.__init__(self, *args, **kwargs)
       
       Page2.Frame = tk.Frame(self, bd=1, relief='solid')
       Page2.Frame.place(relx=0.5, rely=0.08, relwidth=0.99, relheight=0.91, anchor='n')
       
       Page2.toggleButton = tk.Button(self, text="Filter Expected Interlocks", width=12, relief="raised", command=Page2.toggle)
       Page2.toggleButton.place(relx=0.4, rely=0.02, relwidth=0.15, relheight=0.04)
           
       # Add filtering menubars
       FilterButtons = tk.Frame(self)
       FilterButtons.place(relx=0.7, relwidth=0.3, relheight=0.08, anchor='nw')
       
       Page2.menubar = tk.Menubutton(FilterButtons, text='Filter KVCT Interlocks \u25BE', font=20, relief='raised')
       Page2.menubar.place(rely=0.5, relwidth=0.53, relheight=0.45)
       
       button_filter = tk.Button(FilterButtons, text="Filter", font=20, command = Page2.filter_by_interlock)
       button_filter.place(relx=0.6,rely=0.3, relwidth=0.3, relheight=0.4)
       
       button_selectall = tk.Button(FilterButtons, text="Select All", font=20, command=Page2.selectall)
       button_selectall.place(relwidth= 0.22, relheight=0.45)
       
       button_selectnone = tk.Button(FilterButtons, text="Select None", font=20, command=Page2.selectnone)
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
       FilterButtons.place(relx=0.7, relwidth=0.3, relheight=0.08, anchor='nw')
       
       Page3.menubar = tk.Menubutton(FilterButtons, text='Filter Recon Interlocks \u25BE', font=20, relief='raised')
       Page3.menubar.place(rely=0.5, relwidth=0.53, relheight=0.45)
       
       button_filter = tk.Button(FilterButtons, text="Filter", font=20, command = Page3.filter_by_interlock)
       button_filter.place(relx=0.6,rely=0.3, relwidth=0.3, relheight=0.4)
       
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
        MainView.progress = ttk.Progressbar(self, orient='horizontal', mode='determinate')
        MainView.progress.pack(side='bottom', fill='x')
        get(MainView.progress, root)
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
            
    def ConnectWindow():
        window = tk.Toplevel(root)
        window.geometry('500x200')  
        window.wm_title('Connect')
        
        #IP Address label and text entry box
        ipLabel = tk.Label(window, text="IP Address")
        ipLabel.grid(row=0, column=0)
        ipaddress = tk.StringVar()
        ipEntry = tk.Entry(window, textvariable=ipaddress)
        ipEntry.grid(row=0, column=1)  
        
        #username label and text entry box
        usernameLabel = tk.Label(window, text="User Name")
        usernameLabel.grid(row=1, column=0)
        username = tk.StringVar()
        usernameEntry = tk.Entry(window, textvariable=username)
        usernameEntry.grid(row=1, column=1)  
        
        #password label and password entry box
        passwordLabel = tk.Label(window,text="Password")
        passwordLabel.grid(row=2, column=0)  
        password = tk.StringVar()
        passwordEntry = tk.Entry(window, textvariable=password, show='*')
        passwordEntry.grid(row=2, column=1) 
        
        #Output folder to store logs and reports
        outputLabel = tk.Label(window,text="Output")
        outputLabel.grid(row=3, column=0)  
        output = tk.StringVar()
        outputEntry = tk.Entry(window, textvariable=output)
        outputEntry.grid(row=3, column=1)   
        
        #Date range input
        startdateLabel = tk.Label(window,text="Start Date")
        startdateLabel.grid(row=2, column=2)  
        startdate = tk.StringVar()
        startdateEntry = tk.Entry(window, textvariable=startdate)
        startdateEntry.grid(row=2, column=3)  
        
        enddateLabel = tk.Label(window,text="End Date")
        enddateLabel.grid(row=3, column=2)  
        enddate = tk.StringVar()
        enddateEntry = tk.Entry(window, textvariable=enddate)
        enddateEntry.grid(row=3, column=3)  
        
        #Buttons
        ConnectServerButton = tk.Button(window, text="Get Logs", command=lambda : Subfunctions.ConnectServer(ipaddress.get(), username.get(), password.get(), output.get(), startdate.get(), enddate.get()))
        ConnectServerButton.grid(row=4, column=2) 

if __name__ == "__main__":
    root = tk.Tk()
    main = MainView(root)
    main.pack(side="top", fill="both", expand=True)
    root.wm_geometry("1300x800")
    root.mainloop()           