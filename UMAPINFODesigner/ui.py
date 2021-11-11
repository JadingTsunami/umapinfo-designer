# This file is part of UMAPINFO Designer.
#
# UMAPINFO Designer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# UMAPINFO Designer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with UMAPINFO Designer.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright 2021 Jading Tsunami

from tkinter.messagebox import *
from tkinter.filedialog import *
from tkinter.simpledialog import *
from tkinter import *
from tkinter.ttk import *
import io
import sys
import PIL.Image, PIL.ImageTk
import webbrowser

# Local import
from UMAPINFODesigner.structure import config
from UMAPINFODesigner.structure import umapinfo
from UMAPINFODesigner.structure.utypes import UType
from UMAPINFODesigner.structure.utypes import UMAPINFOValue
from UMAPINFODesigner.uio import wadreader
from UMAPINFODesigner.uio import wadwriter
from UMAPINFODesigner.uio import parser
from UMAPINFODesigner.rules import valuechecks
from UMAPINFODesigner.rules import valuechecker
from UMAPINFODesigner import rules

import os

# Version information
__MAJOR__ = 1
__MINOR__ = 0
__PATCH__ = 0

__VERSION__ = str(__MAJOR__) + "." + str(__MINOR__) + "." + str(__PATCH__)

png_header = bytes([137,80,78,71,13,10,26,10])

class ShowText(Toplevel):
    def __init__(self, parent, title=None, text=None):
        super().__init__(parent)

        self.geometry('500x500')
        if title:
            self.title(title)
        else:
            self.title('Text')

        self.displayText = Text(self)
        if text: self.displayText.insert(END, text)
        self.displayText.configure(state='disabled')
        self.displayText.pack(expand=True, fill=BOTH)
        Button(self, text='Close', command=self.destroy).pack(side=BOTTOM)

class ChooseFromLists(Toplevel):
    """List chooser from waddata according to cateogry.
    Don't supply data -- if true/false flag is set, data will be appended
    with a special message."""
    def __init__(self, parent, title=None, cancel=None, waddata_category=None, selected=None, include_data=False):
        super().__init__(parent)

        if title:
            self.title(title)
        else:
            self.title('Choose an item')

        self.lf = LabelFrame(self, text=str(waddata_category).capitalize())
        self.lb = Listbox(self.lf, selectmode=BROWSE)
        self.lb.bind('<<ListboxSelect>>', self.user_selection_changed)
        self.sb = Scrollbar(self.lf, orient="vertical")

        self.glumps = None
        if waddata_category:
            waddata_category = waddata_category.lower()

        if waddata_category == "graphics":
            self.glumps = wadreader.get_waddata("glumps")
        elif waddata_category == "flats":
            self.glumps = wadreader.get_waddata("flumps")

        if self.glumps:
            self.usercanvas = Canvas(self, width=323, height=203)

        self.bb = Button(self, text="Select " + str(waddata_category).rstrip('s'), command=self.sel_user)

        self.sb.config(command=self.lb.yview)
        self.lb.config(yscrollcommand=self.sb.set)

        tosel = -1
        idx = 0
        for idx, el in enumerate(sorted(wadreader.get_waddata(waddata_category))):
            self.lb.insert(END, str(el))
            if str(el) == selected:
                tosel = idx

        if tosel >= 0:
            self.lb.select_set(tosel)
            self.lb.event_generate("<<ListboxSelect>>")
            self.lb.see(tosel)

        if include_data:
            self.dlf = LabelFrame(self, text="Other data lumps")
            self.labelwarn = Label(self.dlf, text="Warning! These may not work!\nUse these only if you know what they are.")
            self.dlb = Listbox(self.dlf, selectmode=BROWSE)
            self.dsb = Scrollbar(self.dlf, orient="vertical")
            self.dbb = Button(self, text="Select data lump", command=self.sel_data)

            self.dsb.config(command=self.dlb.yview)
            self.dlb.config(yscrollcommand=self.dsb.set)

            for el in sorted(wadreader.get_waddata("data")):
                self.dlb.insert(END, str(el))

        if not cancel:
            cancel = "Cancel"

        self.cancelbtn = Button(self, text=cancel, command=self.sel_nothing)

        self.lb.pack(side=LEFT, fill=BOTH, expand=True)
        self.sb.pack(side=RIGHT, anchor=W, fill=Y, expand=True)

        if include_data:
            self.labelwarn.pack(side=TOP)
            self.dlb.pack(side=LEFT, fill=BOTH, expand=True)
            self.dsb.pack(side=RIGHT, anchor=W, fill=Y, expand=True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        self.lf.grid(row=0, column=0, sticky='nsew')
        if self.glumps:
            self.usercanvas.grid(row=0,column=1,sticky='nsew',pady=32)
        self.bb.grid(row=1, column=0, sticky='ew')
        
        if include_data:
            self.dlf.grid(row=0, column=2, sticky='nsew')
            self.dbb.grid(row=1, column=2, sticky='ew')
        self.cancelbtn.grid(row=2, column=0, columnspan=2)

        self.chosen = ""

    def user_selection_changed(self, *args):
        if self.glumps and self.lb.curselection():
            chosen = self.lb.get(self.lb.curselection())
            if self.glumps[chosen].data[0:8] == png_header:
                image = PIL.Image.open(io.BytesIO(self.glumps[chosen].data))
            elif self.glumps[chosen].height <= 200 and self.glumps[chosen].width <= 320:
                image = self.glumps[chosen].to_Image(mode="RGBA")
            else:
                showwarning("Image not recognized", "Selected image format not recognized.")
                return
            self.img_conv = PIL.ImageTk.PhotoImage(image)
            imgx = (323 - self.img_conv.width())/2.0
            imgy = (203 - self.img_conv.height())/2.0
            self.usercanvas.create_image(imgx, imgy, image=self.img_conv, anchor=NW)

    def sel_nothing(self):
        self.chosen = ""
        self.destroy()

    def sel_data(self):
        if self.dlb.curselection():
            self.chosen = self.dlb.get(self.dlb.curselection())
            self.destroy()

    def sel_user(self):
        if self.lb.curselection():
            self.chosen = self.lb.get(self.lb.curselection())
            self.destroy()

    def get_selection(self):
        self.wm_deiconify()
        self.wait_visibility()
        self.focus_force()
        self.after(300, self.grab_set)
        self.wait_window()
        return self.chosen


class DesignerUI:
    """General note: refresh_* methods are responsible for updating UI elements (based on UMAPINFO values) and variable traces or event triggers are responsible for updating the UMAPINFO.
    This implies that the new map selection/IWAD change/trace/trigger is calling refresh as necessary."""
    def __init__(self):
        self.root = Tk()
        self.root.title("UMAPINFO Designer v" + __VERSION__)
        self.root.geometry("1200x600")
        self.root.protocol('WM_DELETE_WINDOW',self.close_warn)

        self.main = Frame(self.root, padding=(3, 3, 3, 3))
        self.side = Frame(self.root, padding=(3, 3, 3, 3))

        # global styling
        style = Style()
        style.map("TButton", foreground=[("disabled", "gray")])
        style.configure("Crimson.TLabel", foreground="crimson")
        style.configure('FixedFont.TLabel', font='TkFixedFont')

        # build side frame
        self.tree = Treeview(self.side, columns=("maps","names"))
        self.tree.column('#0', width=0, stretch=NO)
        self.tree.column('maps', width=64, stretch=NO)
        self.tree.heading('#0', text='', anchor=CENTER)
        self.tree.heading("maps", text="Map", anchor=W)
        self.tree.heading("names", text="Name", anchor=W)

        self.sb = Scrollbar(self.side, orient=VERTICAL)
        self.sb.config(command=self.tree.yview)

        self.buttonpanel = Frame(self.side)
        self.selectediwad = StringVar()
        self.selectediwad.trace('w', self.iwad_changed)

        self.chooseiwad = OptionMenu(self.buttonpanel, self.selectediwad)
        self.addmapbtn = Button(self.buttonpanel, text="+", command=self.addmap)
        self.submapbtn = Button(self.buttonpanel, text="-", command=self.submap)

        self.chooseiwad.pack(side=BOTTOM, anchor=N, expand=True)
        Button(self.buttonpanel, text="Choose IWAD", command=self.prompt_for_iwad).pack(side=BOTTOM, anchor=S, expand=False)
        self.addmapbtn.pack(side=LEFT, expand=True)
        self.submapbtn.pack(side=RIGHT, expand=True)
        self.buttonpanel.pack(side=BOTTOM)

        # convenience list for side panel elements
        self.sidepanel = [self.addmapbtn, self.submapbtn, self.tree]

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.selmap)
        self.tree.bind("<Double-1>", self.rename_map)
        self.sb.pack(side=RIGHT, fill=Y)
        
        # build bottom frame
        self.bottomframe = Frame(self.root)

        self.load_wad_button = Button(self.bottomframe, text="Load WAD", command=self.load_wad)
        self.load_wad_noerrors_button = Button(self.bottomframe, text="Load WAD (ignore errors)", command=self.load_wad_ignore_errors)
        self.clear_wad_button = Button(self.bottomframe, text="Restart", command=self.clear_wad)
        self.load_wad_button.grid(row=0, column=0)
        self.load_wad_noerrors_button.grid(row=0, column=1)
        Button(self.bottomframe, text="Show UMAPINFO", command=self.show_umapinfo).grid(row=0, column=2, padx=(16,0))
        Button(self.bottomframe, text="Save UMAPINFO into WAD", command=self.save_umapinfo).grid(row=0, column=3)
        self.bottomframe.grid_columnconfigure(4, weight=1)
        self.clear_wad_button.grid(row=0, column=4, sticky='e')

        
        # create a scrollable canvas inside the main frame
        self.maincanvas = Canvas(self.main)
        self.mainscrollbar = Scrollbar(self.main, orient="vertical", command=self.maincanvas.yview)

        self.mainscrollbar.pack(side=RIGHT, fill=Y)
        self.maincanvas.pack(expand=True, fill=BOTH)

        self.maincanvas.configure(yscrollcommand=self.mainscrollbar.set)

        self.mainsubframe = LabelFrame(self.maincanvas, text="Map Settings")
        self.maincanvas.bind('<Configure>', self.set_canvas_bounds)
        self.maincanvas.bind_all("<MouseWheel>", self.mousewheel)

        # build main frame
        self.mainframe_inputlist = []

        # subframe 1: automap
        self.automapframe = LabelFrame(self.mainsubframe, text="Automap Configuration")

        # subframe 2: map progression
        self.mapprogframe = LabelFrame(self.mainsubframe, text="Level Progression")

        # subframe 3: episode configuration
        self.episodeframe = LabelFrame(self.mainsubframe, text="Epiosde Configuration")

        # subframe 4: map configuration
        self.mapconfigframe = LabelFrame(self.mainsubframe, text="Level Configuration")

        # subframe 5: intermission
        self.interframe = LabelFrame(self.mainsubframe, text="Intermission Statistics / Text Screen Configuration")


        # subframe 1: automap, grid layout
        self.automapcanvas = Canvas(self.automapframe, width=192, height=192)
        self.automapcanvas.grid(row=0, column=0, rowspan=4, sticky='ns')

        self.automapname = StringVar(value="")
        self.automaplabelframe = LabelFrame(self.automapframe, text="Map title in automap")
        Label(self.automaplabelframe, textvariable=self.automapname, style="FixedFont.TLabel").pack(expand=True, fill=BOTH)
        self.automaplabelframe.grid(row=0, column=1, sticky='ew', columnspan=2)

        Label(self.automapframe, text="Level Name").grid(row=1, column=2, sticky='s')
        self.automaplabel_label = Label(self.automapframe, text="Automap Label")
        self.automaplabel_label.grid(row=1, column=1, sticky='s')

        self.levelname = StringVar()
        self.levelname_entry = Entry(self.automapframe, textvariable=self.levelname)
        self.levelname_entry.grid(row=2, column=2, sticky='n')
        self.mainframe_inputlist.append(self.levelname_entry)

        self.labelname = StringVar()
        self.labelname_entry = Entry(self.automapframe, textvariable=self.labelname)
        self.labelname_entry.grid(row=2, column=1, sticky='n')
        self.mainframe_inputlist.append(self.labelname_entry)

        self.labelclear = IntVar(value=0)
        self.labelclear_check = Checkbutton(self.automapframe, text="No label", onvalue=1, offvalue=0, command=self.toggle_labelclear, variable=self.labelclear)
        self.labelclear_check.grid(row=3, column=1, sticky='n')
        self.mainframe_inputlist.append(self.labelclear_check)

        self.labelname.trace('w', self.label_changed)
        self.levelname.trace('w', self.level_changed)


        # subframe 2: map progression
        Label(self.mapprogframe, text="Next Level").grid(row=0, column=0, sticky='s')
        Label(self.mapprogframe, text="Secret Exit").grid(row=0, column=1, sticky='s')
        
        self.choosenextlevel_stringvar = StringVar()
        self.choosenextlevel_stringvar.trace('w', self.nextlevel_changed)
        self.choosenextlevel_optmenu = OptionMenu(self.mapprogframe, self.choosenextlevel_stringvar)

        self.choosenextsecretlevel_stringvar = StringVar()
        self.choosenextsecretlevel_stringvar.trace('w', self.nextsecretlevel_changed)
        self.choosenextsecretlevel_optmenu = OptionMenu(self.mapprogframe, self.choosenextsecretlevel_stringvar)

        self.choosenextlevel_optmenu.grid(row=1, column=0, sticky='n')
        self.choosenextsecretlevel_optmenu.grid(row=1, column=1, sticky='n')

        self.endpic_label = Label(self.mapprogframe, text="End picture", state="disabled")
        self.endpic_stringvar = StringVar()
        self.endpic_entry = Entry(self.mapprogframe, state="disabled", textvariable=self.endpic_stringvar)
        self.endpic_label.grid(row=2, column=0, sticky='n')
        self.endpic_entry.grid(row=3, column=0, sticky='n')

        # subframe 3: episode configuration
        self.episodeclear = IntVar(value=0)
        self.episodeclear_check = Checkbutton(self.episodeframe, text="Start a new episode beginning with this map", onvalue=1, offvalue=0, command=self.toggle_episodeclear, variable=self.episodeclear)
        self.episodeclear_check.grid(row=0, column=0, columnspan=3, pady=6, sticky='s')
        Separator(self.episodeframe, orient='horizontal').grid(row=1, column=0, columnspan=3, pady=16, sticky='ew')
        self.epname_label = Label(self.episodeframe, text="Episode Name", state='disabled')
        self.epgfx_label = Label(self.episodeframe, text="Episode Menu Graphic\n(optional)", state='disabled')
        self.epkey_label = Label(self.episodeframe, text="Episode Menu Hotkey\n(optional)", state='disabled')
        self.episode_info = Label(self.episodeframe, text="")
        self.episode_info2 = Label(self.episodeframe, text="")

        self.epname_label.grid(row=2, column=0, sticky='s')
        self.epgfx_label.grid(row=2, column=1, sticky='s')
        self.epkey_label.grid(row=2, column=2, sticky='s')

        self.episodename_stringvar = StringVar()
        self.episodename_stringvar.trace('w', self.episodeentry_changed)

        self.episodehotkey_stringvar = StringVar()
        self.episodehotkey_stringvar.trace('w', self.episodeentry_changed)

        self.episodegraphic_stringvar = StringVar()
        self.episodegraphic_stringvar.trace('w', self.episodeentry_changed)

        self.episodegraphic_entry = Entry(self.episodeframe, state='disabled', textvariable=self.episodegraphic_stringvar)
        self.episodegraphic_button = Button(self.episodeframe, text="Choose graphic", command=self.episodegraphic_choose, state='disabled')
        self.episodegraphic_button_clear = Button(self.episodeframe, text="No graphic", command=self.episodegraphic_choose_none, state='disabled')

        self.episodename_entry = Entry(self.episodeframe, textvariable=self.episodename_stringvar, state='disabled')
        self.episodehotkey_entry = Entry(self.episodeframe, textvariable=self.episodehotkey_stringvar, state='disabled')

        self.episodename_entry.grid(row=3, column=0, sticky='n')
        self.episodegraphic_button.grid(row=4, column=1, sticky='n')
        self.episodegraphic_button_clear.grid(row=5, column=1, sticky='n')
        self.episodegraphic_entry.grid(row=3, column=1, sticky='n')
        self.episodehotkey_entry.grid(row=3, column=2, sticky='n')
        self.episode_info.grid(row=6, column=0, columnspan=3)
        self.episode_info2.grid(row=7, column=0, columnspan=3)
        # subframe 3: map configuration
        # self.mapconfigframe
        Label(self.mapconfigframe, text="Music").grid(row=0, column=0, sticky='s')
        Label(self.mapconfigframe, text="Sky Texture").grid(row=0, column=1, sticky='s')
        Label(self.mapconfigframe, text="Par Time (seconds)").grid(row=0, column=2, sticky='s')

        self.music_stringvar = StringVar()
        self.music_entry = Entry(self.mapconfigframe, textvariable=self.music_stringvar, state="disabled")
        self.music_button = Button(self.mapconfigframe, text="Choose Music", command=self.choose_music)
        self.music_entry.grid(row=1, column=0, sticky='n')
        self.music_button.grid(row=2, column=0, sticky='n')

        self.skytexture_stringvar = StringVar()
        self.skytexture_entry = Entry(self.mapconfigframe, textvariable=self.skytexture_stringvar, state="disabled")
        self.skytexture_button = Button(self.mapconfigframe, text="Choose Sky Texture", command=self.choose_skytexture)
        self.skytexture_entry.grid(row=1, column=1, sticky='n')
        self.skytexture_button.grid(row=2, column=1, sticky='n')

        self.partime_intvar = IntVar()
        self.partime_intvar.trace('w', self.set_partime)
        self.partime_entry = Entry(self.mapconfigframe, textvariable=self.partime_intvar)
        self.partime_entry.grid(row=1, column=2, sticky='n')

        self.bossaction_frame = Frame(self.mapconfigframe)
        self.bossaction_listbox = Listbox(self.bossaction_frame, selectmode=BROWSE)

        self.bossaction_scrollbar = Scrollbar(self.bossaction_frame, orient="vertical")
        self.bossaction_scrollbar.config(command=self.bossaction_listbox.yview)
        self.bossaction_listbox.config(yscrollcommand=self.bossaction_scrollbar.set)

        self.bossaction_scrollbarx = Scrollbar(self.bossaction_frame, orient="horizontal")
        self.bossaction_scrollbarx.config(command=self.bossaction_listbox.xview)
        self.bossaction_listbox.config(xscrollcommand=self.bossaction_scrollbarx.set)

        self.bossaction_remove = Button(self.bossaction_frame, text="Remove selected", command=self.remove_bossaction)
        self.bossaction_add = Button(self.mapconfigframe, text="Add new Boss Action", command=self.add_bossaction)

        self.bossaction_thingtype_stringvar = StringVar()
        self.bossaction_thingtype_menu = OptionMenu(self.mapconfigframe, self.bossaction_thingtype_stringvar)

        self.bossaction_linetype_stringvar = StringVar()
        self.bossaction_linetype_menu = OptionMenu(self.mapconfigframe, self.bossaction_linetype_stringvar)

        self.bossaction_linetag_intvar = IntVar()
        self.bossaction_linetag_menu = Entry(self.mapconfigframe, textvariable=self.bossaction_linetag_intvar)

        self.bossaction_remove.pack(side=BOTTOM, expand=True, fill=X)
        self.bossaction_scrollbar.pack(side=RIGHT, fill=Y, anchor='w')
        self.bossaction_scrollbarx.pack(side=BOTTOM, fill=X, anchor='n')
        self.bossaction_listbox.pack(side=LEFT, expand=True, fill=BOTH, anchor='center')

        self.bossaction_label_header = Label(self.mapconfigframe, text="Boss Enemy Death Special Actions")
        self.bossaction_label_header.grid(row=4, column=0, sticky='s', pady=16)

        self.bossaction_clear = IntVar(value=0)
        self.bossaction_clear_check = Checkbutton(self.mapconfigframe, text="Do not allow Boss Actions on this map", onvalue=1, offvalue=0, command=self.toggle_bossaction_clear, variable=self.bossaction_clear)
        self.bossaction_clear_check.grid(row=4, column=2, sticky='e')

        Separator(self.mapconfigframe, orient='horizontal').grid(row=4, column=0, columnspan=3, pady=8, sticky='new')
        self.bossaction_frame.grid(row=5, column=0, columnspan=3, sticky='nsew')
        self.bossaction_label_type = Label(self.mapconfigframe, text="Boss Thing Type")
        self.bossaction_label_type.grid(row=6, column=0, sticky='s')
        self.bossaction_thingtype_menu.grid(row=7, column=0, sticky='n')
        self.bossaction_label_action = Label(self.mapconfigframe, text="Special Action")
        self.bossaction_label_action.grid(row=6, column=1, sticky='s')
        self.bossaction_linetype_menu.grid(row=7, column=1, sticky='n')
        self.bossaction_label_tag = Label(self.mapconfigframe, text="Sector Tag")
        self.bossaction_label_tag.grid(row=6, column=2, sticky='s')
        self.bossaction_linetag_menu.grid(row=7, column=2, sticky='n')
        self.bossaction_add.grid(row=8, column=0, columnspan=3, sticky='n')
        self.bossaction_label_info = Label(self.mapconfigframe, text="For each Boss Action: When all of the Boss Thing Type are dead,\nthe Special Action will trigger on sectors marked with the Sector Tag.\nMultiple Boss Actions can be defined.")
        self.bossaction_label_info2 = Label(self.mapconfigframe, text="Special Action labels credit to the Doom Wiki (click here to open in browser).")
        self.bossaction_label_info2.bind("<Button-1>", self.open_doomwiki)
        self.bossaction_label_info.grid(row=10, column=0, columnspan=3, sticky='n')
        self.bossaction_label_info2.grid(row=9, column=0, columnspan=3, sticky='n')
        self.bossaction_label_extra_info = Label(self.mapconfigframe, text="", style="Crimson.TLabel")
        self.bossaction_label_extra_info.grid(row=11, column=0, columnspan=3, sticky='n')

        # subframe 4: intermission
        # Intermission statistics screen
        self.interstat_frame = LabelFrame(self.interframe, text="Intermission Statistics Screen Configuration")

        self.interstat_nointermission_intvar = IntVar(value=0) 
        self.interstat_nointermission_check = Checkbutton(self.interstat_frame, text="Skip intermission statistics screen (only availble when ending the game)", onvalue=1, offvalue=0, command=self.toggle_nointermission, variable=self.interstat_nointermission_intvar)

        self.interstat_levelpic_stringvar = StringVar()
        self.interstat_levelpic_label = Label(self.interstat_frame, text="Level name image\n(optional)")
        self.interstat_levelpic_entry = Entry(self.interstat_frame, state="disabled", textvariable=self.interstat_levelpic_stringvar)
        self.interstat_levelpic_button = Button(self.interstat_frame, text="Choose graphic", command=self.levelpic_choose)
        self.interstat_levelpic_button_clear = Button(self.interstat_frame, text="Use default", command=self.levelpic_clear)

        self.interstat_enterpic_stringvar = StringVar()
        self.interstat_enterpic_label = Label(self.interstat_frame, text="Background image\nwhen entering level")
        self.interstat_enterpic_entry = Entry(self.interstat_frame, state="disabled", textvariable=self.interstat_enterpic_stringvar)
        self.interstat_enterpic_button = Button(self.interstat_frame, text="Choose graphic", command=self.enterpic_choose)
        self.interstat_enterpic_button_flat = Button(self.interstat_frame, text="Choose flat", command=self.enterpic_choose_flat)
        self.interstat_enterpic_button_clear = Button(self.interstat_frame, text="Use default", command=self.enterpic_clear)

        self.interstat_exitpic_stringvar = StringVar()
        self.interstat_exitpic_label = Label(self.interstat_frame, text="Background image\nwhen exiting level")
        self.interstat_exitpic_entry = Entry(self.interstat_frame, state="disabled", textvariable=self.interstat_exitpic_stringvar)
        self.interstat_exitpic_button = Button(self.interstat_frame, text="Choose graphic", command=self.exitpic_choose)
        self.interstat_exitpic_button_flat = Button(self.interstat_frame, text="Choose flat", command=self.exitpic_choose_flat)
        self.interstat_exitpic_button_clear = Button(self.interstat_frame, text="Use default", command=self.exitpic_clear)

        self.interstat_nointermission_check.grid(row=0, column=0, sticky='ew', columnspan=3, pady=16, padx=8)
        self.interstat_levelpic_label.grid(row=1, column=0)
        self.interstat_levelpic_entry.grid(row=2, column=0)
        self.interstat_levelpic_button.grid(row=3, column=0)
        self.interstat_levelpic_button_clear.grid(row=5, column=0)

        self.interstat_enterpic_label.grid(row=1, column=1)
        self.interstat_enterpic_entry.grid(row=2, column=1)
        self.interstat_enterpic_button.grid(row=3, column=1)
        self.interstat_enterpic_button_flat.grid(row=4, column=1)
        self.interstat_enterpic_button_clear.grid(row=5, column=1)

        self.interstat_exitpic_label.grid(row=1, column=2)
        self.interstat_exitpic_entry.grid(row=2, column=2)
        self.interstat_exitpic_button.grid(row=3, column=2)
        self.interstat_exitpic_button_flat.grid(row=4, column=2)
        self.interstat_exitpic_button_clear.grid(row=5, column=2)

        self.interstat_frame.pack(expand=True, fill=BOTH)

        # Intermission text screen (shows after statistics)
        self.intertext_frame = LabelFrame(self.interframe, text="Intermission Text Screen Configuration")

        self.intertext_nointertext_intvar = IntVar(value=0) 
        self.intertext_nointertext_check = Checkbutton(self.intertext_frame, text="Do not show a text screen on normal exit", onvalue=1, offvalue=0, command=self.toggle_nointertext, variable=self.intertext_nointertext_intvar)
        self.intertext_intertext_preview_label = Label(self.intertext_frame, text="Normal Exit Text")
        self.intertext_intertext_entry = Text(self.intertext_frame, width=40, height=17, wrap='none')
        self.intertext_intertext_entry.bind('<KeyRelease>', self.set_intertext)


        self.intertext_nointertextsecret_intvar = IntVar(value=0) 
        self.intertext_nointertextsecret_check = Checkbutton(self.intertext_frame, text="Do not show a text screen on secret exit", onvalue=1, offvalue=0, command=self.toggle_nointertextsecret, variable=self.intertext_nointertextsecret_intvar)
        self.intertext_intertextsecret_preview_label = Label(self.intertext_frame, text="Secret Exit Text")
        self.intertext_intertextsecret_entry = Text(self.intertext_frame, width=40, height=17, wrap='none')
        self.intertext_intertextsecret_entry.bind('<KeyRelease>', self.set_intertextsecret)


        self.interbackdrop_frame = Frame(self.intertext_frame)
        self.interbackdrop_label = Label(self.interbackdrop_frame, text="Background Graphic\n(always the same for both\nnormal and secret exits)", justify='center')
        self.interbackdrop_stringvar = StringVar()
        self.interbackdrop_entry = Entry(self.interbackdrop_frame, state="disabled", textvariable=self.interbackdrop_stringvar)
        self.interbackdrop_button = Button(self.interbackdrop_frame, text="Choose graphic", command=self.interbackdrop_choose)
        self.interbackdrop_button_flat = Button(self.interbackdrop_frame, text="Choose flat", command=self.interbackdrop_choose_flat)
        self.interbackdrop_button_clear = Button(self.interbackdrop_frame, text="Use default", command=self.interbackdrop_clear)

        self.intermusic_frame = Frame(self.intertext_frame)
        self.intermusic_label = Label(self.intermusic_frame, text="Background Music\n(always the same for both\nnormal and secret exits)", justify='center')
        self.intermusic_stringvar = StringVar()
        self.intermusic_entry = Entry(self.intermusic_frame, state="disabled", textvariable=self.intermusic_stringvar)
        self.intermusic_button = Button(self.intermusic_frame, text="Choose Music", command=self.intermusic_choose)

        self.intertext_info_label = Label(self.intertext_frame, text="Note: The way the text looks above is how it will appear in-game.\nMake sure it's formatted the way you want it to appear.", justify='center')
        self.intertext_extra_info_label = Label(self.intertext_frame, text="", justify='center', style="Crimson.TLabel")

        self.intertext_intertext_preview_label.grid(row=0, column=0, pady=8)
        self.intertext_nointertext_check.grid(row=1, column=0)
        self.intertext_intertext_entry.grid(row=2, column=0, rowspan=2)

        self.intertext_intertextsecret_preview_label.grid(row=0, column=2, pady=8)
        self.intertext_nointertextsecret_check.grid(row=1, column=2)
        self.intertext_intertextsecret_entry.grid(row=2, column=2, rowspan=2)

        self.interbackdrop_label.grid(row=0, column=0)
        self.interbackdrop_entry.grid(row=1, column=0)
        self.interbackdrop_button.grid(row=2, column=0)
        self.interbackdrop_button_flat.grid(row=3, column=0)
        self.interbackdrop_button_clear.grid(row=4, column=0)
        self.interbackdrop_frame.grid(row=2, column=1)

        self.intermusic_label.grid(row=0, column=0)
        self.intermusic_entry.grid(row=1, column=0)
        self.intermusic_button.grid(row=2, column=0)
        self.intermusic_frame.grid(row=3, column=1, pady=8)

        self.intertext_info_label.grid(row=4, column=0, columnspan=3)
        self.intertext_extra_info_label.grid(row=5, column=0, columnspan=3)

        # pack label frames into main canvas frame
        self.automapframe.pack(fill=BOTH, expand=True, pady=12)
        self.mapprogframe.pack(fill=BOTH, expand=True, pady=12)
        self.episodeframe.pack(fill=BOTH, expand=True, pady=12)
        self.mapconfigframe.pack(fill=BOTH, expand=True, pady=12)
        self.interframe.pack(fill=BOTH, expand=True, pady=12)
        self.intertext_frame.pack(fill=BOTH, expand=True, pady=12)

        self.cframe = self.maincanvas.create_window((0,0), window=self.mainsubframe, anchor='nw')

        # install frames
        self.side.pack(side=LEFT, fill=Y, anchor=W, expand=True)
        self.bottomframe.pack(side=BOTTOM, anchor=S, fill=X, expand=True)
        self.main.pack(side=RIGHT, fill=BOTH, expand=True)

        self.root.iconbitmap("ud-icon.ico")

        # GUI is created; now populate and prepare the internals
        self.clear_mainframe()
        self.toggle_mainframe(False)
        if config.configdata.iwads and config.validate_iwad_list():
            last_iwad = config.get_last_iwad()
            self.refresh_iwad_list(last_iwad)
            self.change_iwad(last_iwad, config.get_iwad(last_iwad))
        else:
            showinfo("First time?", "Looks like this is the first time you're running UMAPINFO Designer.\n\nPlease select an IWAD \n(Doom or Doom 2 game WAD file) to get started.")
            if not self.prompt_for_iwad():
                showerror("Error: No IWAD", "You must select an IWAD.\nExiting now...")
                self.root.destroy()

        self.in_rename = False
        # Boss actions are one-time intialization
        # (values do not change)
        # Default: Baron of Hell (works for both IWADs)
        self.bossaction_thingtype_menu.set_menu(rules.keys.thing_types["BaronOfHell"], *rules.keys.thing_types.values())

        line_spc = ["I'll supply my own"]
        line_spc.extend(rules.keys.usable_specials.values())
        self.bossaction_linetype_menu.set_menu(rules.keys.usable_specials[11], *line_spc)

        self.delta_divider = 1
        if sys.platform.startswith("win"):
            self.delta_divider = 120

    def set_canvas_bounds(self, event):
        """Event function for canvas configure.
        Sets scrollable region and resizes the canvas to fit the frame."""
        self.maincanvas.config(width=event.width, height=event.height)
        self.maincanvas.itemconfig(self.cframe, height=self.mainsubframe.winfo_reqheight()*1.1, width=event.width-3)
        self.set_canvas_scrollregion()

    def set_canvas_scrollregion(self):
        self.maincanvas.configure(scrollregion=self.maincanvas.bbox('all'))

    def toggle_sidepanel(self, enable=True):
        """Eanble or disable all user-interactables in the side frame."""
        for s in self.sidepanel:
            if enable:
                s.state(['!disabled'])
            else:
                s.state(['disabled'])

    def refresh_iwad_list(self, sel=None):
        """Rebuilds the IWAD list at the bottom of the side frame.
        Does NOT validate the entries."""
        iwmenu = [*config.configdata.iwads.keys()]
        if not sel:
            sel = iwmenu[0]
        self.chooseiwad.set_menu(sel, *iwmenu)

    def change_iwad_warn(self, save=False):
        """Warn the user before changing an IWAD.
        Can ask for confirmation or allow saving to a file first.
        Only allows save if they intentionally selected a new IWAD."""
        if not umapinfo.umapinfo.modified:
            return True
        elif not save and askyesno("WARNING! UMAPINFO will be lost!", "WARNING! Loading an IWAD clears out UMAPINFO.\nYou have unsaved UMAPINFO changes which will be lost.\n\nAre you sure you want to do this?\n\nThis can not be undone."):
            return True
        elif save:
            if askyesno("WARNING! UMAPINFO will be lost!", "WARNING! Loading an IWAD clears out UMAPINFO.\nYou have unsaved UMAPINFO changes which will be lost.\n\nThis can not be undone.\n\nDo you want to save the UMAPINFO to a file first?"):
                self.save_umapinfo()
            return True
        return False

    def change_iwad(self, iwad_name, iwad_fullpath):
        """Assumes all validation has been done and the user
        has been warned."""
        config.set_iwad(iwad_name)
        umapinfo.clear_umapinfo()
        wadreader.read_waddata_from_wad(iwad_fullpath, clean=True)
        self.load_wad_button['text'] = "Load WAD"
        self.load_wad_noerrors_button['text'] = "Load WAD (ignore errors)"
        self.clear_mainframe()
        self.refresh_map_list()
        self.toggle_mainframe(False)

    def prompt_for_iwad(self):
        """Prompt and set a new IWAD."""
        if not self.change_iwad_warn():
            return
        iwfile = askopenfilename(parent=self.root, title="Choose an IWAD", filetypes=[("IWAD Files", "*.wad")], multiple=False)
        if iwfile:
            if not wadreader.is_iwad(iwfile):
                showerror("Not an IWAD", "Selected file is not an IWAD.")
                return False
            iwad_fullpath = os.path.abspath(iwfile)
            iwad_basename = os.path.basename(iwfile)
            config.add_iwad(iwad_basename, iwad_fullpath)
            self.refresh_iwad_list(iwad_basename.lower())
            self.change_iwad(iwad_basename, iwad_fullpath)
            return True
        return False

    def iwad_changed(self, *args):
        """Event trigger for user selecting a new IWAD from the drop-down list.
        This assumes the IWADs are all valid and validated."""
        self.change_iwad_warn(save=True)
        iw = self.selectediwad.get()
        self.change_iwad(iw, config.get_iwad(iw))

    def addmap(self):
        """Triggered when user clicks the '+' button.
        Prompts, validates, then adds to UMAPINFO.
        Relies on refresh_map_list to update UI elements."""
        newmap = self.prompt_for_map_name()
        if newmap:
            umapinfo.add_map(newmap)
            self.refresh_map_list()

    def prompt_for_map_name(self):
        dialogmsg = "Please enter a new map in "
        title = "Add new map"
        isdoom = config.settings.is_doom()
        isdoom2 = config.settings.is_doom2()

        if isdoom:
            dialogmsg += "ExMy format\n(where x is the episode number\nand y is the map number)\n\nExample: E4M5"
        elif isdoom2:
            dialogmsg += "MAPxx format\n(where xx is the map number)\n\nExample: MAP12"
        else:
            dialogmsg = "IWAD not recognized. Please enter the new map in the appropriate format (either MAPxx or ExMy)."
            isdoom = True
            isdoom2 = True

        newmap = askstring(title, dialogmsg)

        if newmap:
            newmap = newmap.upper()
            if not valuechecks.check_map_syntax(newmap, isdoom, isdoom2):
                extrastr = ""
                if isdoom2:
                    extrastr = "\nMake sure to use at least two digits if you are using MAPxx format.\n\nExample: MAP04 is correct, MAP4 is incorrect."
                showerror("Error: Invalid map name", "Error: " + str(newmap) + " is not a valid map name." + extrastr)
            elif umapinfo.has_map(newmap):
                showerror("Error: Map is already present", "Error: " + str(newmap) + " is already present.")
            else:
                return newmap
        return None

    def refresh_map_list(self):
        """Wipes out the tree view and repopulates. Assumes UMAPINFO is updated."""
        # store list of all available maps for later use
        self.all_maps = set()
        self.all_maps.update(wadreader.get_waddata('maps'))
        self.all_maps.update(umapinfo.umapinfo.u.keys())

        self.tree.delete(*self.tree.get_children())
        if not umapinfo.has_episodes():
            for umap in umapinfo.umapinfo.u.keys():
                # process map
                mapname = umapinfo.map_name(umap)
                self.tree.insert('', 'end', values=(umap,mapname))
        else:
            episode_tree = umapinfo.get_episode_tree()
            for episode in episode_tree:
                if episode == "__noepisode":
                    epid = ''
                else:
                    epid = self.tree.insert('', 'end', values=('',episode), open=True)
                for level in episode_tree[episode]:
                    self.tree.insert(epid, 'end', values=(level,umapinfo.map_name(level)))

    def selmap(self, event):
        """Triggered on map select change in tree view.
        IMPORTANT: This is the event responsible for setting/unsetting the
        self.umap which holds the currently-selected map value.
        The assumption is always that if self.umap is non-None, it is a *valid*
        map. Any pre-validation must happen before this step!"""
        focus = self.tree.item(self.tree.focus())
        if not focus or len(focus['values']) < 2:
            self.umap = None
        else:
            self.umap = focus['values'][0]
            if not umapinfo.has_map(self.umap):
                self.umap = None
        self.mapimg = None
        self.refresh_mainframe(self.umap)
    
    def refresh_extralabels_bossaction(self, umap, enable=True):
        # Boss Action
        if enable and (umap.endswith("M8") or umap in ["E4M6", "MAP07"]):
            self.bossaction_label_extra_info['text'] = "Note: This map contains built-in game default Boss Actions.\nIf you don't want to use these,\nadd your own or check the mark to disallow Boss Actions on this map."
        else:
            self.bossaction_label_extra_info['text'] = ""

    def refresh_extralabels_intertext(self, umap, normalenable=True, secretenable=True):
        if normalenable and (umap in ["E1M8", "E2M8", "E3M8", "E4M8"] or umap in ["MAP06", "MAP11", "MAP20", "MAP30"]):
            self.intertext_extra_info_label['text'] = "Note: This map contains a built-in text screen on normal exit.\nIf you don't want to use this, add your own or check the mark\nto disallow a normal exit text screen on this map."
        elif secretenable and (umap in ["MAP15", "MAP31"]):
            self.intertext_extra_info_label['text'] = "Note: This map contains a built-in text screen on secret exit.\nIf you don't want to use this, add your own or check the mark\nto disallow a secret exit text screen on this map."
        else:
            self.intertext_extra_info_label['text'] = ""

    def clear_mainframe(self):
        """Wipe out all main frame elements.
        MUST be called as an initialization step prior to populating UI elements."""
        self.umap = None
        self.automapname.set("")
        self.levelname.set("")
        self.labelname.set("")
        self.episodename_stringvar.set("")
        self.episodehotkey_stringvar.set("")
        self.episodegraphic_stringvar.set("")
        self.interstat_nointermission_intvar.set(0)
        self.interstat_levelpic_stringvar.set("")
        self.interstat_enterpic_stringvar.set("")
        self.interstat_exitpic_stringvar.set("")
        self.labelclear.set(0)
        self.mapimg = None
        self.help2_warn_shown = False

    def toggle_mainframe(self, enable=True):
        """Enable or disable all main frame elements."""
        if enable:
            newstate = 'normal'
            self.maincanvas.itemconfigure(self.cframe, state='normal')
        else:
            newstate = 'disabled'
            self.maincanvas.itemconfigure(self.cframe, state='hidden')
        self.set_canvas_scrollregion()
        for element in self.mainframe_inputlist:
            element['state'] = newstate

    def refresh_mainframe(self, umap=None):
        """Either populate the main frame with the selected map, or
        disable the main frame is no umap is supplied."""
        if not umap:
            self.clear_mainframe()
            self.toggle_mainframe(False)
        else:
            self.toggle_mainframe(True)
            self.refresh_automap(umap, True)
            self.refresh_mapprog(umap)
            self.refresh_episodeframe(umap)
            self.refresh_mapconfigframe(umap)
            self.refresh_interframe(umap)

    def refresh_episodeframe(self, umap):
        ep = umapinfo.get_key(umap, "episode")
        if not ep or (ep and ep.utype == UType.KEYWORD):
            # assumes only valid keyword is 'clear'
            self.episodename_stringvar.set("")
            self.episodehotkey_stringvar.set("")
            self.episodegraphic_stringvar.set("")
            self.episodeclear.set(0)
            self.toggle_episodeclear()
        elif ep.utype == UType.TUPLE and len(ep.value) == 3:
            # note we checked for "not ep" before, so nonetype
            # should not be possible here
            (epgfx, epname, epkey) = ep.value

            if epgfx == "\"-\"":
                epgfx = ""

            self.episodename_stringvar.set(epname.strip('"'))
            self.episodehotkey_stringvar.set(epkey.strip('"'))
            self.episodegraphic_stringvar.set(epgfx.strip('"'))
            self.episodeclear.set(1)
            self.toggle_episodeclear()

    def refresh_mapprog(self, umap):
        self.refresh_endpic(umap)
        map_choices = ["Same as normal exit"]
        map_choices.extend(sorted(self.all_maps))
        endgame = False
        nextsecretsel = map_choices[0]
        if umapinfo.has_key(umap, "nextsecret"):
            nextsecretsel = umapinfo.get_key(umap, "nextsecret").value

        self.choosenextsecretlevel_optmenu.set_menu(nextsecretsel, *map_choices)

        map_choices[0] = "Default"
        spc_end = "default special ending"
        if config.settings.is_doom2():
            spc_end = "cast call"
        elif config.settings.is_doom():
            spc_end = "bunny scroller"
        map_choices.extend(["End game with text screen and a custom picture", "End game with text screen and a default picture", "End game with " + spc_end])

        nextsel = map_choices[0]
        if umapinfo.has_key(umap, "next"):
            nextsel = umapinfo.get_key(umap, "next").value
        elif umapinfo.has_key(umap, "endgame") and umapinfo.get_key(umap, "endgame").value.lower() == 'true':
            nextsel = map_choices[-2]
            endgame = True
        elif umapinfo.has_key(umap, "endpic"):
            nextsel = map_choices[-3]
            endgame = True
        elif (umapinfo.has_key(umap, "endbunny") and umapinfo.get_key(umap, "endbunny").value.lower() == 'true') or (umapinfo.has_key(umap, "endcast") and umapinfo.get_key(umap, "endcast").value.lower() == 'true'):
            nextsel = map_choices[-1]
            endgame = True

        self.set_nointermission_state(endgame)

        self.choosenextlevel_optmenu.set_menu(nextsel, *map_choices)

    def refresh_endpic(self, umap):
        endpic = umapinfo.get_key(umap, "endpic")
        if endpic:
            self.endpic_label['state'] = 'normal'
            self.endpic_stringvar.set(str(endpic.value))
        else:
            self.endpic_label['state'] = 'disabled'
            self.endpic_stringvar.set("")


    def refresh_automap(self, umap, update_entries=False):
        """Refresh automap from UMAPINFO.
        Assumes UMAPINFO is updated."""
        label = str(umap)
        level = str(umapinfo.map_name(umap))
        userlabel = umapinfo.get_key(umap, 'label')
        midlabel = ": "
        if userlabel:
            if userlabel.utype == UType.KEYWORD:
                # assumes only valid keyword is clear
                label = ""
                midlabel = ""
            elif userlabel.utype == UType.STRING:
                label = str(userlabel.value)
        elif userlabel:
            label = userlabel
        self.automapname.set(label + midlabel + level)
        if update_entries:
            self.levelname.set(level)
            if userlabel:
                self.labelname.set(label)
            else:
                self.labelname.set("")
            if label == "":
                self.labelclear.set(1)
            else:
                self.labelclear.set(0)
        # update tree view
        self.tree.item(self.tree.focus(), values=(self.umap, level))
        if not self.mapimg:
            self.mapimg = wadreader.get_waddata_map_image(umap, width=189)
            self.automapcanvas.create_image(0, 0, anchor='nw', image=self.mapimg)

    def submap(self):
        """Remove the currently-selected map."""
        focus = self.tree.item(self.tree.focus())
        if not focus or len(focus['values']) < 2:
            showerror("Error: Select a map", "Error: First select a map to remove.")
            return
        umap = focus['values'][0]
        if not askyesno("Are you sure?", "This will remove " + str(umap) + " and all its contents.\nAre you sure? This cannot be undone."):
            return
        if not umapinfo.has_map(umap):
            showerror("Error", "Error: Can't remove episode all at once. Please remove maps individually.")
        else:
            umapinfo.sub_map(umap)
            self.refresh_map_list()
            self.toggle_mainframe(False)

    def load_wad_ignore_errors(self):
        if askyesno("Are you sure?", "This is dangerous.\n\nAre you sure?"):
            self.load_wad(validate=False)

    def load_wad(self, validate=True, show_errors=False, show_warnings=False):
        """Load a WAD and its contents into waddata."""
        if umapinfo.umapinfo.modified and not askyesno("Unsaved Changes","You have unsaved changes. Loading a new WAD will clear out any current UMAPINFO.\n\nAre you sure?"):
            return
        wfile = askopenfilename(parent=self.root, title="Choose a PWAD", filetypes=[("WAD Files", "*.wad")], multiple=False)
        if not wfile: return
        if wadreader.is_wad_loaded(wfile):
            showerror("Error: Already loaded", "Error: This WAD file is already loaded.")
            return
        try:
            if not wadreader.read_waddata_from_wad_if_match(wfile, config.settings.is_doom(), config.settings.is_doom2()):
                showerror("Error: Incompatible IWAD", "Error: The loaded PWAD has a UMAPINFO incompatible with the loaded IWAD.")
                return
            uinf = wadreader.get_waddata_umapinfo()
            self.load_wad_button['text'] = "Add another WAD"
            self.load_wad_noerrors_button['text'] = "Add another WAD (ignore errors)"
            if uinf:
                if validate:
                    warnings = {}
                    errors = {}
                    valuechecker.check_all_keys_and_remove_bad(uinf, warnings, errors)
                    # only show errors
                    if show_errors:
                        for umap in errors:
                            if errors[umap]:
                                errorstr = ""
                                for key in errors[umap]:
                                    errorstr += str(key) + ": "
                                    for err in errors[umap][key]:
                                        errorstr += str(err) + "\n"
                                showerror("Error: Removed Invalid key(s)", "Errors detected on " + str(umap) + "\n\nKeys removed:\n\n" + errorstr + "\n")
                    if show_warnings:
                        for umap in warnings:
                            if warnings[umap]:
                                warningstr = ""
                                for key in warnings[umap]:
                                    warningstr += str(key) + ": "
                                    for warn in warnings[umap][key]:
                                        warningstr += str(warn) + "\n"
                                showwarning("Warning: Issue with key(s)", "Warnings detected on " + str(umap) + "\n\nKeys warned:\n\n" + warningstr + "\n")
                umapinfo.load_umapinfo(uinf)
                umapinfo.umapinfo.modified = False
                self.refresh_map_list()
        except Exception as e:
            showerror("Error", "Error reading WAD file.\n" + "Error: " + str(e))

    def toggle_labelclear(self, *args):
        # disable label entry
        # clear label
        # change umapinfo variables
        # refresh automap title
        if not self.umap: return
        if self.labelclear.get():
            # no label
            self.labelname.set("")
            self.labelname_entry['state'] = 'disabled'
            self.automaplabel_label['state'] = 'disabled'
            umapinfo.add_key(self.umap, "label", UType.KEYWORD, 'clear')
        else:
            # yes label
            self.labelname_entry['state'] = 'normal'
            self.automaplabel_label['state'] = 'normal'
            umapinfo.del_key(self.umap, "label")
        self.refresh_automap(self.umap)

    def label_changed(self, *args):
        # change umapinfo variable
        # refresh automap
        if not self.umap: return
        userlabel = self.labelname.get()
        nolabel = self.labelclear.get()
        if nolabel:
            return # do nothing, user does not want a label
        elif userlabel:
            umapinfo.add_key(self.umap, "label", UType.STRING, userlabel)
        else:
            umapinfo.del_key(self.umap, "label")
        self.refresh_automap(self.umap)

    def level_changed(self, *args):
        # change umapinfo variable
        # update treeview name
        # refresh automap
        if not self.umap: return
        umapinfo.add_key(self.umap, "levelname", UType.STRING, self.levelname.get())
        self.refresh_automap(self.umap)

    def nextlevel_changed(self, *args):
        if not self.umap: return
        has_next = umapinfo.has_key(self.umap, "next")
        choice_next = self.choosenextlevel_stringvar.get()
        endgame = False

        # Default/Same as normal exit and end game do not
        # have next exits, so delete the "next" key if it's present.
        if choice_next == "Default" or choice_next.startswith("End game"):
            # clear out old keys (if present)
            # no error if key is not there, so it's
            # fine if they are not
            umapinfo.del_key(self.umap, "next")
            umapinfo.del_key(self.umap, "endgame")
            umapinfo.del_key(self.umap, "endcast")
            umapinfo.del_key(self.umap, "endbunny")
            umapinfo.del_key(self.umap, "endpic")

        if not choice_next.endswith("custom picture"):
            self.endpic_stringvar.set("")

        # now put the key (or keys) required based on
        # the user's selection
        if choice_next.endswith("text screen and a default picture") or choice_next.endswith("special ending"):
            umapinfo.add_key(self.umap, "endgame", UType.KEYWORD, "true")
            endgame = True
            if config.settings.is_doom2() and not self.help2_warn_shown:
                self.help2_warn_shown = True
                showwarning("Warning: HELP2 Lump Recommended", "Warning: There is a bug in early versions of PrBoom-Plus which will exit the game if the default picture is selected and there is no HELP2 picture lump to show. Make sure you have a HELP2 lump in your WAD!\n\nThis is not required, but your map may crash after this map if it is not present.")
        elif choice_next.endswith("text screen and a custom picture"):
            if not self.endpic_stringvar.get():
                gfxchoose = ChooseFromLists(self.root, title="Choose an end game graphic", waddata_category="graphics", include_data=True)
                chosen = gfxchoose.get_selection()
                if chosen:
                    umapinfo.add_key(self.umap, "endpic", UType.STRING, chosen)
                else:
                    showwarning("Defaulting end picture to title screen", "No custom picture was chosen.\nDefaulting to the title screen.")
                    umapinfo.add_key(self.umap, "endpic", UType.STRING, "TITLEPIC")
            else:
                umapinfo.add_key(self.umap, "endpic", UType.STRING, self.endpic_stringvar.get())
            self.refresh_endpic(self.umap)
            endgame = True
        elif choice_next.endswith("bunny scroller"):
            umapinfo.add_key(self.umap, "endbunny", UType.KEYWORD, "true")
            endgame = True
        elif choice_next.endswith("cast call"):
            umapinfo.add_key(self.umap, "endcast", UType.KEYWORD, "true")
            endgame = True
        elif choice_next == "Default":
            pass # we're done
        else:
            # normal exit BUT if we're on map30 (doom 2) or m8 (doom 1) we need to also not end the game here
            last_map = (config.settings.is_doom() and self.umap.endswith("M8")) or (config.settings.is_doom2() and self.umap == "MAP30")
            if last_map:
                umapinfo.add_key(self.umap, "endgame", UType.KEYWORD, "false")
            umapinfo.add_key(self.umap, "next", UType.STRING, choice_next)

        self.set_nointermission_state(endgame)


    def nextsecretlevel_changed(self, *args):
        if not self.umap: return
        has_nextsecret = umapinfo.has_key(self.umap, "nextsecret")
        choice_nextsecret = self.choosenextsecretlevel_stringvar.get()

        # Default/Same as normal exit and end game do not
        # have nextsecret exits, so delete the "nextsecret" key if it's present.
        if choice_nextsecret == "Same as normal exit":
            umapinfo.del_key(self.umap, "nextsecret")
        else:
            umapinfo.add_key(self.umap, "nextsecret", UType.STRING, choice_nextsecret)

    def episodeentry_changed(self, *args):
        if not self.umap: return
        epkey_raw = str(self.episodehotkey_stringvar.get())
        if len(epkey_raw) > 1:
            epkey_raw = epkey_raw[0]

        if epkey_raw and not epkey_raw.isalnum():
            showerror("Error: Bad hotkey", "Error: Hotkey must be a single alphanumeric value.")
            epkey_raw = ""

        self.episodehotkey_stringvar.set(epkey_raw)

        epgfx = self.episodegraphic_stringvar.get()
        if not epgfx:
            epgfx = '-'
            self.episode_info2['text'] = "Note: You must define a valid graphic for ALL episodes if you want your\nepisode graphics to appear, otherwise the episode name will be printed in the\nDoom font regardless of what you have put in the graphic field."
        else:
            self.episode_info2['text'] = ""


        epname = '"' + str(self.episodename_stringvar.get()) + '"'
        epgfx = '"' + str(epgfx) + '"'
        epkey = '"' + str(self.episodehotkey_stringvar.get()) + '"'
        ept = (epgfx, epname, epkey)

        umapinfo.add_key(self.umap, "episode", UType.TUPLE, ept)
        umapinfo.resolve_episodes()

    def episodegraphic_choose(self, *args):
        self.graphic_choose(self.episodegraphic_stringvar, window_title="Choose an episode title graphic")

    def episodegraphic_choose_none(self, *args):
        self.episodegraphic_stringvar.set("")
        self.episodeentry_changed()

    def graphic_choose(self, field_stringvar, window_title=None, lump_type="graphics", show_data=True):
        usersel = field_stringvar.get()
        if not window_title:
            window_title = "Choose a " + lump_type.rstrip('s')
        gfxchoose = ChooseFromLists(self.root, title=window_title, waddata_category=lump_type, include_data=show_data, selected=usersel)
        chosen = gfxchoose.get_selection()
        if chosen:
            field_stringvar.set(chosen)

    def toggle_episodeclear(self, *args):
        if not self.umap: return
        infotext = ""
        if self.episodeclear.get():
            num_ep = umapinfo.num_episodes()
            if num_ep >= 8:
                this_ep = umapinfo.get_key(self.umap, "episode")
                if not this_ep or this_ep.utype == UType.KEYWORD:
                    showerror("Episode Limit Reached", "Error: Episode Limit Reached.\n\nAt most, 8 episodes can be defined. You must remove an epiode before another can be added.")
                    self.episodeclear.set(0)
                    return
            elif num_ep == 0:
                infotext = "Note: You have only defined one episode so far.\nYou must define at least 2 for episodes to show up in the in-game menu.\n"
        if self.episodeclear.get():
            self.episodename_entry['state'] = 'normal'
            self.episodehotkey_entry['state'] = 'normal'
            self.episodegraphic_button ['state'] = 'normal'
            self.episodegraphic_button_clear ['state'] = 'normal'
            self.epname_label['state'] = 'normal'
            self.epgfx_label['state'] = 'normal'
            self.epkey_label['state'] = 'normal'
            self.episode_info['text'] = infotext
            self.episode_info['state'] = 'normal'
        else:
            # no episode
            self.episodename_stringvar.set("")
            self.episodehotkey_stringvar.set("")
            self.episodegraphic_stringvar.set("")
            umapinfo.del_key(self.umap, "episode")
            self.episodename_entry['state'] = 'disabled'
            self.episodehotkey_entry['state'] = 'disabled'
            self.episodegraphic_button ['state'] = 'disabled'
            self.episodegraphic_button_clear ['state'] = 'disabled'
            self.epname_label['state'] = 'disabled'
            self.epgfx_label['state'] = 'disabled'
            self.epkey_label['state'] = 'disabled'
            self.episode_info['text'] = ""
            self.episode_info2['text'] = ""
        umapinfo.resolve_episodes()

    def refresh_mapconfigframe(self, umap):
        self.refresh_music()
        self.refresh_skytexture()
        self.refresh_partime()
        self.refresh_bossaction()

    def choose_music(self, *args):
        musicchoose = ChooseFromLists(self.root, title="Choose Music", cancel="Use default music", waddata_category="music", include_data=True)
        chosen = musicchoose.get_selection()
        if chosen:
            umapinfo.add_key(self.umap, "music", UType.STRING, chosen)
        else:
            umapinfo.del_key(self.umap, "music")
        self.music_stringvar.set(chosen)

    def refresh_music(self):
        music = umapinfo.get_key(self.umap, "music")
        if music and music.utype == UType.STRING:
            self.music_stringvar.set(music.value)
        else:
            self.music_stringvar.set("")

    def choose_skytexture(self, *args):
        texchoose = ChooseFromLists(self.root, title="Choose a sky texture", cancel="Use default sky texture", waddata_category="textures", include_data=False)
        chosen = texchoose.get_selection()
        if chosen:
            umapinfo.add_key(self.umap, "skytexture", UType.STRING, chosen)
        else:
            umapinfo.del_key(self.umap, "skytexture")
        self.skytexture_stringvar.set(chosen)

    def refresh_skytexture(self):
        sky = umapinfo.get_key(self.umap, "skytexture")
        if sky and sky.utype == UType.STRING:
            self.skytexture_stringvar.set(sky.value)
        else:
            self.skytexture_stringvar.set("")

    def set_partime(self, *args):
        try:
            partime = max(0, self.partime_intvar.get())
        except TclError:
            partime = 0
        if partime > 0:
            umapinfo.add_key(self.umap, "partime", UType.NUMBER, partime)
        else:
            umapinfo.del_key(self.umap, "partime")

    def refresh_partime(self):
        par = umapinfo.get_key(self.umap, "partime")
        if par and par.utype == UType.NUMBER:
            partime = par.value
            if partime > 0:
                self.partime_intvar.set(str(partime))
        else:
            self.partime_intvar.set(0)

    
    def refresh_bossaction(self):
        self.bossaction_listbox.delete(0, END)
        bossactions = umapinfo.get_key(self.umap, "bossaction", full_list=True)
        ba_disallow = self.bossaction_clear.get()
        if not bossactions:
            if ba_disallow:
                self.bossaction_clear.set(0)
        else:
            for ba in bossactions:
                if ba.utype == UType.TUPLE and len(ba.value) == 3:
                    if ba_disallow:
                        self.bossaction_clear.set(0)
                        ba_disallow = 0

                    (ba_type, ba_spc, ba_tag) = ba.value

                    if int(ba_spc) in rules.keys.usable_specials:
                        ba_spc = rules.keys.usable_specials[int(ba_spc)]
                    
                    if ba_type in rules.keys.thing_types:
                        ba_type = rules.keys.thing_types[ba_type]
                    else:
                        showwarning("Thing type not found", "Warning: Thing type " + str(ba_type) + " is not a valid ZDoom Actor type.")
                    sba = ba_type + ", Action: " + ba_spc + ", Tag: " + ba_tag
                    self.bossaction_listbox.insert(END, str(sba))
                elif ba.utype == UType.KEYWORD and ba.value.lower() == 'clear':
                    self.bossaction_listbox.delete(0, END)
                    if not ba_disallow:
                        self.bossaction_clear.set(1)
                        ba_disallow = 1
        self.refresh_extralabels_bossaction(self.umap, (self.bossaction_clear.get() == 0 and self.bossaction_listbox.size() == 0))
        self.set_bossaction_activation()

    def remove_bossaction(self, *args):
        ba = self.bossaction_listbox.curselection()
        if not ba:
            showwarning("No boss action selected", "Select a boss action to remove.")
        else:
            ba_rem = self.bossaction_listbox.get(ba)
            # Should always have 3 elements
            (ba_type, ba_spc, ba_tag) = str(ba_rem).split(',')
            ba_spc = ba_spc.split(':')[1].strip()
            ba_type_key = rules.keys.key_from_value(rules.keys.thing_types, ba_type)
            ba_spc_key = rules.keys.key_from_value(rules.keys.usable_specials, ba_spc)
            ba_tag = ba_tag.split(':')[1].strip()
            if ba_type_key:
                ba_type = ba_type_key
            if ba_spc_key:
                ba_spc = ba_spc_key

            ba_uv = UMAPINFOValue((str(ba_type),str(ba_spc),str(ba_tag)), UType.TUPLE)

            all_ba = umapinfo.get_key(self.umap, "bossaction", full_list=True)
            umapinfo.del_key(self.umap, "bossaction")
            new_ba = []
            for ba in all_ba:
                if not (ba.utype == UType.TUPLE and tuple(ba.value) == ba_uv.value):
                    umapinfo.add_key(self.umap, "bossaction", UType.TUPLE, ba.value, append=True)
            self.refresh_bossaction()

    def add_bossaction(self, *args):
        ba_type = self.bossaction_thingtype_stringvar.get()
        ba_spc  = self.bossaction_linetype_stringvar.get()
        ba_tag  = self.bossaction_linetag_intvar.get()

        ba_type = rules.keys.key_from_value(rules.keys.thing_types, ba_type)
        if ba_spc == "I'll supply my own":
            # will be validated later
            ba_spc = askinteger("Supply a Linedef Special", "Supply a Linedef Special number: ")
        else:
            ba_spc = rules.keys.key_from_value(rules.keys.usable_specials, ba_spc)

        messages = []
        ba_uv = UMAPINFOValue((str(ba_type),str(ba_spc),str(ba_tag)), UType.TUPLE)
        if not valuechecks.bossaction_is_valid(ba_uv, messages):
            showerror("Invalid Boss Action", "Error: Boss Action is invalid.\nError: " + str(messages.pop()))
            return
        elif messages:
            showwarning("Warning: Boss Action Issue(s)", str(messages.pop()))
        # validation passed, add it
        umapinfo.add_key(self.umap, "bossaction", UType.TUPLE, ba_uv.value, append=True)
        self.refresh_bossaction()

    def toggle_bossaction_clear(self, *args):
        ba_disallow = self.bossaction_clear.get()
        if ba_disallow:
            if umapinfo.has_key(self.umap, "bossaction") and not askyesno("Are you sure?", "This will clear any defined Boss Actions, including map defaults.\nAre you sure?"):
                self.bossaction_clear.set(0)
                return
            umapinfo.del_key(self.umap, "bossaction")
            umapinfo.add_key(self.umap, "bossaction", UType.KEYWORD, "clear")
        else:
            umapinfo.del_key(self.umap, "bossaction")
        self.refresh_bossaction()

    def set_bossaction_activation(self):
        ba_disallow = self.bossaction_clear.get()
        if ba_disallow:
            # disable inputs
            self.bossaction_remove['state'] = 'disabled'
            self.bossaction_listbox['state'] = 'disabled'
            self.bossaction_add['state'] = 'disabled'
            self.bossaction_thingtype_menu['state'] = 'disabled'
            self.bossaction_linetype_menu['state'] = 'disabled'
            self.bossaction_linetag_menu['state'] = 'disabled'
            self.bossaction_label_header['state'] = 'disabled'
            self.bossaction_label_type['state'] = 'disabled'
            self.bossaction_label_action['state'] = 'disabled'
            self.bossaction_label_tag['state'] = 'disabled'
            self.bossaction_label_info['state'] = 'disabled'
            self.bossaction_label_info2['state'] = 'disabled'
        else:
            self.bossaction_remove['state'] = 'normal'
            self.bossaction_listbox['state'] = 'normal'
            self.bossaction_add['state'] = 'normal'
            self.bossaction_thingtype_menu['state'] = 'normal'
            self.bossaction_linetype_menu['state'] = 'normal'
            self.bossaction_linetag_menu['state'] = 'normal'
            self.bossaction_label_header['state'] = 'normal'
            self.bossaction_label_type['state'] = 'normal'
            self.bossaction_label_action['state'] = 'normal'
            self.bossaction_label_tag['state'] = 'normal'
            self.bossaction_label_info['state'] = 'normal'
            self.bossaction_label_info2['state'] = 'normal'

    def save_umapinfo(self):
        if not umapinfo.umapinfo.u:
            showerror("Error: No UMAPINFO", "Error: You haven't entered any UMAPINFO information yet.")
            return
        iwfile = asksaveasfilename(parent=self.root, title="Choose a PWAD", filetypes=[("PWAD Files", "*.wad")])
        if iwfile:
            try:
                wadwriter.write_umapinfo_to_wad(iwfile, parser.generate_umapinfo(umapinfo.umapinfo.u))
                umapinfo.umapinfo.modified = False
            except Exception as e:
                showerror("Error", "Error writing WAD file. Consider copying your UMAPINFO to a text file.\n" + "Error: " + str(e))

    def show_umapinfo(self):
        if not umapinfo.umapinfo.u:
            showerror("Error: No UMAPINFO", "Error: You haven't entered any UMAPINFO information yet.")
            return
        umapshow = ShowText(self.root, title="UMAPINFO Text", text=parser.generate_umapinfo(umapinfo.umapinfo.u))
        umapshow.grab_set()

    def close_warn(self):
        if not umapinfo.umapinfo.modified or askyesno("Unsaved changes", "You have unsaved changes.\nAre you sure you want to exit?"):
            self.root.destroy()

    def mousewheel(self, event):
        focus = str(self.root.focus_get()).lower()
        if "choosefromlists" not in focus and "showtext" not in focus:
            self.maincanvas.yview_scroll(-1*int(event.delta/self.delta_divider), "units")

    def rename_map(self, event):
        if not self.in_rename:
            self.in_rename = True
            focus = self.tree.item(self.tree.focus())
            if not focus or len(focus['values']) < 2:
                self.in_rename = False
                return # no error
            else:
                selected_map = focus['values'][0]
                if not umapinfo.has_map(selected_map):
                    self.in_rename = False
                    return # no error
                newmap = self.prompt_for_map_name()
                if not newmap:
                    self.in_rename = False
                    return
                umapinfo.rename_map(selected_map, newmap)

            self.umap = newmap
            self.mapimg = None
            self.refresh_mainframe(self.umap)
            self.in_rename = False

    def set_nointermission_state(self, endgame):
        if endgame:
            self.interstat_nointermission_check['state'] = 'normal'
        else:
            self.interstat_nointermission_check['state'] = 'disabled'
            self.interstat_nointermission_intvar.set(0)
            self.toggle_nointermission()

    def refresh_interframe(self, umap):
        self.refresh_interstat_frame()
        self.refresh_intertext_frame()

    def refresh_interstat_frame(self):
        ni_um = umapinfo.get_key(self.umap, "nointermission")
        noint = self.interstat_nointermission_intvar.get()
        if ni_um and ni_um.utype == UType.KEYWORD and ni_um.value.lower() == 'true':
            self.interstat_nointermission_intvar.set(1)
            self.interstat_levelpic_label['state'] = 'disabled'
            self.interstat_levelpic_button['state'] = 'disabled'
            self.interstat_levelpic_button_clear['state'] = 'disabled'
            self.interstat_enterpic_label['state'] = 'disabled'
            self.interstat_enterpic_button['state'] = 'disabled'
            self.interstat_enterpic_button_flat['state'] = 'disabled'
            self.interstat_enterpic_button_clear['state'] = 'disabled'
            self.interstat_exitpic_label['state'] = 'disabled'
            self.interstat_exitpic_button['state'] = 'disabled'
            self.interstat_exitpic_button_flat['state'] = 'disabled'
            self.interstat_exitpic_button_clear['state'] = 'disabled'
        else:
            self.interstat_nointermission_intvar.set(0)
            self.interstat_levelpic_label['state'] = 'normal'
            self.interstat_levelpic_button['state'] = 'normal'
            self.interstat_levelpic_button_clear['state'] = 'normal'
            self.interstat_enterpic_label['state'] = 'normal'
            self.interstat_enterpic_button['state'] = 'normal'
            self.interstat_enterpic_button_flat['state'] = 'normal'
            self.interstat_enterpic_button_clear['state'] = 'normal'
            self.interstat_exitpic_label['state'] = 'normal'
            self.interstat_exitpic_button['state'] = 'normal'
            self.interstat_exitpic_button_flat['state'] = 'normal'
            self.interstat_exitpic_button_clear['state'] = 'normal'

        self.set_field_to_umapinfo_key(self.interstat_levelpic_stringvar, "levelpic")
        self.set_field_to_umapinfo_key(self.interstat_enterpic_stringvar, "enterpic")
        self.set_field_to_umapinfo_key(self.interstat_exitpic_stringvar, "exitpic")

    def set_umapinfo_key_to_field(self, field_stringvar, umapinfo_key):
        umapinfo.del_key(self.umap, umapinfo_key)
        newval = field_stringvar.get()
        if newval:
            umapinfo.add_key(self.umap, umapinfo_key, UType.STRING, newval)

    def set_field_to_umapinfo_key(self, field_stringvar, umapinfo_key):
        ukv = umapinfo.get_key(self.umap, umapinfo_key)
        if ukv and ukv.utype == UType.STRING:
            field_stringvar.set(ukv.value)
        else:
            field_stringvar.set("")

    def toggle_nointermission(self, *args):
        noint = self.interstat_nointermission_intvar.get()
        if noint:
            umapinfo.add_key(self.umap, "nointermission", UType.KEYWORD, "true")
            umapinfo.del_key(self.umap, "levelpic")
            umapinfo.del_key(self.umap, "enterpic")
            umapinfo.del_key(self.umap, "exitpic")
        else:
            umapinfo.del_key(self.umap, "nointermission")
        self.refresh_interstat_frame()

    def levelpic_choose(self, *args):
        self.graphic_choose(self.interstat_levelpic_stringvar, window_title="Choose a level name graphic")
        self.set_umapinfo_key_to_field(self.interstat_levelpic_stringvar, "levelpic")

    def enterpic_choose(self, *args):
        self.graphic_choose(self.interstat_enterpic_stringvar, window_title="Choose a background level entering graphic")
        self.set_umapinfo_key_to_field(self.interstat_enterpic_stringvar, "enterpic")

    def exitpic_choose(self, *args):
        self.graphic_choose(self.interstat_exitpic_stringvar, window_title="Choose a background level exit graphic")
        self.set_umapinfo_key_to_field(self.interstat_exitpic_stringvar, "exitpic")

    def enterpic_choose_flat(self, *args):
        self.graphic_choose(self.interstat_enterpic_stringvar, window_title="Choose a background level entry flat", lump_type="flats", show_data=False)
        self.set_umapinfo_key_to_field(self.interstat_enterpic_stringvar, "enterpic")

    def exitpic_choose_flat(self, *args):
        self.graphic_choose(self.interstat_exitpic_stringvar, window_title="Choose a background level exit flat", lump_type="flats", show_data=False)
        self.set_umapinfo_key_to_field(self.interstat_exitpic_stringvar, "exitpic")

    def levelpic_clear(self, *args):
        self.interstat_levelpic_stringvar.set("")
        self.set_umapinfo_key_to_field(self.interstat_levelpic_stringvar, "levelpic")

    def enterpic_clear(self, *args):
        self.interstat_enterpic_stringvar.set("")
        self.set_umapinfo_key_to_field(self.interstat_enterpic_stringvar, "enterpic")

    def exitpic_clear(self, *args):
        self.interstat_exitpic_stringvar.set("")
        self.set_umapinfo_key_to_field(self.interstat_exitpic_stringvar, "exitpic")

    def refresh_intertext_frame(self):
        self.set_field_to_umapinfo_key(self.interbackdrop_stringvar, "interbackdrop")
        self.set_field_to_umapinfo_key(self.intermusic_stringvar, "intermusic")

        noint = umapinfo.get_key(self.umap, "intertext")
        noint_secret = umapinfo.get_key(self.umap, "intertextsecret")
        if noint and noint.utype == UType.KEYWORD:
            if not self.intertext_nointertext_intvar.get():
                self.intertext_nointertext_intvar.set(1)
            self.set_textarea_to_umapinfo_key(self.intertext_intertext_entry, "intertext")
            self.intertext_intertext_entry['state'] = 'disabled'
            self.intertext_intertext_preview_label['state'] = 'disabled'
            noint = True
        else:
            if self.intertext_nointertext_intvar.get():
                self.intertext_nointertext_intvar.set(0)
            self.intertext_intertext_entry['state'] = 'normal'
            self.intertext_intertext_preview_label['state'] = 'normal'
            self.set_textarea_to_umapinfo_key(self.intertext_intertext_entry, "intertext")
            noint = False

        if noint_secret and noint_secret.utype == UType.KEYWORD:
            if not self.intertext_nointertextsecret_intvar.get():
                self.intertext_nointertextsecret_intvar.set(1)
            self.set_textarea_to_umapinfo_key(self.intertext_intertextsecret_entry, "intertextsecret")
            self.intertext_intertextsecret_entry['state'] = 'disabled'
            self.intertext_intertextsecret_preview_label['state'] = 'disabled'
            noint_secret = True
        else:
            if self.intertext_nointertextsecret_intvar.get():
                self.intertext_nointertextsecret_intvar.set(0)
            self.intertext_intertextsecret_entry['state'] = 'normal'
            self.intertext_intertextsecret_preview_label['state'] = 'normal'
            self.set_textarea_to_umapinfo_key(self.intertext_intertextsecret_entry, "intertextsecret")
            noint_secret = False

        if noint and noint_secret:
            # disable all remaining intertext entries
            self.intertext_info_label['state'] = 'disabled'
            self.interbackdrop_label['state'] = 'disabled'
            self.interbackdrop_button['state'] = 'disabled'
            self.interbackdrop_button_flat['state'] = 'disabled'
            self.interbackdrop_button_clear['state'] = 'disabled'
            self.intermusic_label['state'] = 'disabled'
            self.intermusic_button['state'] = 'disabled'
        else:
            # enable the rest (entry + label already done)
            self.intertext_info_label['state'] = 'normal'
            self.interbackdrop_label['state'] = 'normal'
            self.interbackdrop_button['state'] = 'normal'
            self.interbackdrop_button_flat['state'] = 'normal'
            self.interbackdrop_button_clear['state'] = 'normal'
            self.intermusic_label['state'] = 'normal'
            self.intermusic_button['state'] = 'normal'

        self.refresh_extralabels_intertext(self.umap, (not noint and self.intertext_intertext_entry.get("1.0", END) == '\n'), (not noint_secret and self.intertext_intertextsecret_entry.get("1.0", END) == '\n'))

    def interbackdrop_choose(self, *args):
        self.graphic_choose(self.interbackdrop_stringvar, window_title="Choose a text screen background graphic")
        self.set_umapinfo_key_to_field(self.interbackdrop_stringvar, "interbackdrop")

    def interbackdrop_choose_flat(self, *args):
        self.graphic_choose(self.interbackdrop_stringvar, window_title="Choose a text screen background flat", lump_type="flats", show_data=False)
        self.set_umapinfo_key_to_field(self.interbackdrop_stringvar, "interbackdrop")

    def interbackdrop_clear(self, *args):
        self.interbackdrop_stringvar.set("")
        self.set_umapinfo_key_to_field(self.interbackdrop_stringvar, "interbackdrop")

    def intermusic_choose(self, *args):
        intermusicchoose = ChooseFromLists(self.root, title="Choose Music", cancel="Use default music", waddata_category="music", include_data=True)
        chosen = intermusicchoose.get_selection()
        if chosen:
            umapinfo.add_key(self.umap, "intermusic", UType.STRING, chosen)
        else:
            umapinfo.del_key(self.umap, "intermusic")
        self.intermusic_stringvar.set(chosen)

    def set_textarea_to_umapinfo_key(self, textarea, keyname):
        multistring = umapinfo.get_key(self.umap, keyname)
        textarea.delete("1.0", END)
        # if keyword, must be "clear" and clearing the text
        # area is the correct thing to do
        if multistring:
            if multistring.utype == UType.MULTISTRING:
                textarea.insert("1.0", "\n".join(multistring.value))
            elif multistring.utype == UType.STRING:
                textarea.insert("1.0", multistring.value)

    def set_umapinfo_key_to_textarea(self, textarea, keyname):
        if textarea.edit_modified() and not textarea['state'] == 'disabled':
            # don't bother getting anything beyond the margins we want
            pos = textarea.index(END)
            if not pos:
                return
            (r,c) = pos.split('.')
            textarea.see("1.0")
            newtext = textarea.get("1.0", "17.41")
            if int(r) > 18:
                textarea.delete("1.0", END)
                textarea.insert("1.0", newtext)
            # at this point, text is cropped/modified to fit
            umapinfo.del_key(self.umap, keyname)
            newtext = newtext.removesuffix("\n")
            if len(newtext) > 0:
                umapinfo.add_key(self.umap, keyname, UType.MULTISTRING, newtext.split('\n'))
        else:
            textarea.edit_modified(False)

    def set_intertext(self, *args):
        self.set_umapinfo_key_to_textarea(self.intertext_intertext_entry, "intertext")
        self.refresh_extralabels_intertext(self.umap, (self.intertext_nointertext_intvar.get() == 0 and self.intertext_intertext_entry.get("1.0", END) == '\n'), (self.intertext_nointertextsecret_intvar.get() == 0 and self.intertext_intertextsecret_entry.get("1.0", END) == '\n'))

    def set_intertextsecret(self, *args):
        self.set_umapinfo_key_to_textarea(self.intertext_intertextsecret_entry, "intertextsecret")
        self.refresh_extralabels_intertext(self.umap, (self.intertext_nointertext_intvar.get() == 0 and self.intertext_intertext_entry.get("1.0", END) == '\n'), (self.intertext_nointertextsecret_intvar.get() == 0 and self.intertext_intertextsecret_entry.get("1.0", END) == '\n'))

    def toggle_nointertext(self, *args):
        noi = self.intertext_nointertext_intvar.get()
        if noi:
            intertext = self.intertext_intertext_entry.index('end-1c')
            if intertext:
                (r,c) = intertext.split(".")
                if (int(r) > 1 or int(c) > 0) and not askyesno("Are you sure?", "This will delete your normal exit intermission text.\n\nAre you sure?"):
                    self.intertext_nointertext_intvar.set(0)
                    return
            umapinfo.del_key(self.umap, "intertext")
            umapinfo.add_key(self.umap, "intertext", UType.KEYWORD, "clear")
            nos = self.intertext_nointertextsecret_intvar.get()
            if nos:
                umapinfo.del_key(self.umap, "interbackdrop")
                umapinfo.del_key(self.umap, "intermusic")
        else:
            itkey = umapinfo.get_key(self.umap, "intertext")
            if itkey and itkey.utype == UType.KEYWORD:
                umapinfo.del_key(self.umap, "intertext")
        self.refresh_intertext_frame()

    def toggle_nointertextsecret(self, *args):
        noi = self.intertext_nointertextsecret_intvar.get()
        if noi:
            intertextsecret = self.intertext_intertextsecret_entry.index('end-1c')
            if intertextsecret:
                (r,c) = intertextsecret.split(".")
                if (int(r) > 1 or int(c) > 0) and not askyesno("Are you sure?", "This will delete your secret exit intermission text.\n\nAre you sure?"):
                    self.intertext_nointertextsecret_intvar.set(0)
                    return
            umapinfo.del_key(self.umap, "intertextsecret")
            umapinfo.add_key(self.umap, "intertextsecret", UType.KEYWORD, "clear")
            non = self.intertext_nointertext_intvar.get()
            if non:
                umapinfo.del_key(self.umap, "interbackdrop")
                umapinfo.del_key(self.umap, "intermusic")
        else:
            itkey = umapinfo.get_key(self.umap, "intertextsecret")
            if itkey and itkey.utype == UType.KEYWORD:
                umapinfo.del_key(self.umap, "intertextsecret")
        self.refresh_intertext_frame()

    def clear_wad(self):
        if not askyesno("Warning: All changes will be lost", "WARNING: All changes will be lost and all WAD files cleared out.\nThis can not be undone.\n\nAre you sure?"):
            return
        iw = self.selectediwad.get()
        self.change_iwad(iw, config.get_iwad(iw))

    def open_doomwiki(self, *args):
        webbrowser.open_new("https://doomwiki.org/wiki/Linedef_type")

    def run(self):
        self.root.mainloop()
