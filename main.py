#!/usr/bin/env python

import subprocess
import re
import os
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
import encoded_images

def wtwitch_config_file():
    if 'APPDATA' in os.environ:
        confighome = os.environ['APPDATA']
    elif 'XDG_CONFIG_HOME' in os.environ:
        confighome = os.environ['XDG_CONFIG_HOME']
    else:
        confighome = os.path.join(os.environ['HOME'], '.config')
    configfile = os.path.join(confighome, 'wtwitch/config.json')
    return configfile

def wtwitch_subscription_cache():
    if 'LOCALAPPDATA' in os.environ:
        cachehome = os.environ['LOCALAPPDATA']
    elif 'XDG_CONFIG_HOME' in os.environ:
        cachehome = os.environ['XDG_CACHE_HOME']
    else:
        cachehome = os.path.join(os.environ['HOME'], '.cache')
    cachepath = os.path.join(cachehome, 'wtwitch/subscription-cache.json')
    return cachepath

def extract_streamer_status():
    online_streamers = []
    online_package = []
    offline_streamers = []
    with open(wtwitch_subscription_cache(), 'r') as cache:
        cachefile = json.load(cache)
        for streamer in cachefile['data']:
            online_streamers.append(streamer['user_login'])
            login = streamer['user_login']
            name = streamer['user_name']
            categ = streamer['game_name']
            title = streamer['title']
            views = streamer['viewer_count']
            package = login,name,categ,title,views
            online_package.append(package)
    with open(wtwitch_config_file(), 'r') as config:
        configfile = json.load(config)
        subscriptions = configfile['subscriptions']
        for diction in subscriptions:
            streamer = diction['streamer']
            if streamer not in online_streamers:
                offline_streamers.append(streamer)
    online_streamers.sort()
    online_package.sort()
    offline_streamers.sort()
    return online_package, offline_streamers

def check_status():
    '''Call wtwitch c again when pressing the refresh button
    '''
    wtwitch_c = subprocess.run(['wtwitch', 'c'],
                        capture_output=True,
                        text=True
                        )

def fetch_vods(streamer):
    '''Run wtwitch v and extract all timestamps/titles of the streamer's VODs
    with regex. Cap the title length at 50 characters.
    '''
    wtwitch_v = subprocess.run(['wtwitch', 'v', streamer],
                        stderr=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        text=True
                        )
    timestamps = re.findall(r'\[96m\[(\S* \d.*:\d.*):\d.*\]', wtwitch_v.stdout)
    titles = re.findall(r'\]\x1b\[0m\s*(\S.*)\s\x1b\[93m', wtwitch_v.stdout)
    length = re.findall(r'\x1b\[93m(\S*)\x1b\[0m', wtwitch_v.stdout)
    #for i in range(len(titles)):
    #    if len(titles[i]) > 50:
    #        titles[i] = titles[i][:50] + "..."
    return timestamps, titles, length

def vod_panel(streamer):
    '''Draw 2 columns for the watch buttons and timestamps/stream length of
    the last 20 VODs.
    '''
    # Retrieve the streamer's VODs:
    vods = fetch_vods(streamer)
    # Account for streamer having zero VODs:
    if len(vods[0]) == 0:
        no_vods = messagebox.showinfo(title=f"No VODs",
                        message=f"{streamer} has no VODs",
                        parent=root
                        )
        return
    # frame-canvas-frame to attach a scrollbar:
    close_button = tk.Button(
                        root,
                        image=close_icon,
                        relief='flat',
                        command=lambda: [vw_frame.forget(), vw_frame.destroy()]
                        )
    vw_frame = ttk.Labelframe(root, labelwidget=close_button)
    vw_frame.grid(column='0', row='1', sticky='nsew')
    vw_frame.columnconfigure(0, weight=1)
    vw_frame.rowconfigure(0, weight=1)
    met_frame = ttk.Frame(vw_frame)
    met_frame.grid(column='0', row='1', sticky='nsew')
    met_frame.columnconfigure(0, weight=1)
    met_frame.rowconfigure(0, weight=1)
    vw_canvas = tk.Canvas(met_frame)
    vw_scrollbar = ttk.Scrollbar(met_frame,orient="vertical",
                        command=vw_canvas.yview
                        )
    vw_canvas.configure(yscrollcommand=vw_scrollbar.set)
    vod_frame = ttk.Labelframe(met_frame,
                        text=f"{streamer}'s VODs",
                        )
    vod_frame.bind("<Configure>", lambda e:
                        vw_canvas.configure(
                        scrollregion=vw_canvas.bbox("all"))
                        )
    # Draw the VOD grid:
    vod_number = 1
    for timestamp, title, length in zip(vods[0], vods[1], vods[2]):
        watch_button = tk.Button(vod_frame,
                        image=play_icon,
                        relief='flat',
                        height='24', width='24',
                        command=lambda s=streamer, v=vod_number:
                        [subprocess.run(['wtwitch', 'v', s, str(v)])]
                        )
        watch_button.grid(column=0, row=vod_number, sticky='nesw')
        timestamp_button = tk.Button(vod_frame, text=f"{timestamp} {length}",
                        command=lambda ts=timestamp, t=title, p=root:
                        messagebox.showinfo("VOD", ts, detail=t, parent=p),
                        font=('', '10'),
                        relief='flat',
                        anchor='w'
                        )
        timestamp_button.grid(column=1, row=vod_number, sticky='nesw')
        vod_number += 1
    # Finish the scrollbar
    vw_canvas.create_window((0, 0), window=vod_frame, anchor="nw")
    vw_canvas.grid(row=0, column=0, sticky="nsew", padx=8, pady=5)
    vw_scrollbar.grid(row=0, column=1, sticky="ns")
    vw_canvas.bind_all("<MouseWheel>", mouse_scroll)

def streamer_buttons(parent):
    online_streamers = streamer_status[0]
    offline_streamers = streamer_status[1]
    count_rows = 0
    for package in online_streamers:
        watch_button = tk.Button(parent,
                        image=streaming_icon,
                        relief='flat',
                        command=lambda s=package[0]:
                        [subprocess.run(['wtwitch', 'w', s])]
                        )
        watch_button.grid(column=0, row=count_rows, sticky='ns')
        info_button = tk.Button(parent,
                        text=package[1],
                        anchor='w',
                        font=('Cantarell', '12', 'bold'),
                        relief='flat',
                        width=15,
                        disabledforeground='#464646',
                        command= lambda s=package[1], c=package[2],
                                        t=package[3], v=package[4]:
                        info_dialog(s, c, t, v)
                        )
        info_button.grid(column=1, row=count_rows, sticky='nesw')
        unfollow_b = tk.Button(parent,
                        image=unfollow_icon,
                        relief='flat',
                        command=lambda s=package[1]:
                        [unfollow_dialog(s)]
                        )
        unfollow_b.grid(column=2, row=count_rows, sticky='ns')
        vod_b = tk.Button(parent,
                        image=vod_icon,
                        relief='flat',
                        command=lambda s=package[1]:
                        vod_panel(s)
                        )
        vod_b.grid(column=3, row=count_rows, sticky='ns')
        count_rows += 1
    for streamer in offline_streamers:
        watch_button = tk.Label(parent, image=offline_icon)
        watch_button.grid(column=0, row=count_rows, sticky='ns')
        info_button = tk.Button(parent,
                        text=streamer,
                        anchor='w',
                        font=('Cantarell', '12', 'bold'),
                        state='disabled', relief='flat',
                        compound='left',
                        disabledforeground='#464646'
                        )
        info_button.grid(column=1, row=count_rows, sticky='nesw')
        unfollow_b = tk.Button(parent,
                        image=unfollow_icon,
                        relief='flat',
                        command=lambda s=streamer:
                        [unfollow_dialog(s)]
                        )
        unfollow_b.grid(column=2, row=count_rows, sticky='ns')
        vod_b = tk.Button(parent,
                        image=vod_icon,
                        relief='flat',
                        command=lambda s=streamer:
                        vod_panel(s)
                        )
        vod_b.grid(column=3, row=count_rows, sticky='ns')
        count_rows += 1

def info_dialog(streamer, category, title, viewers):
    '''Info dialog, including stream title and stream category
    '''
    info = messagebox.showinfo(title=f"{streamer} is streaming",
                        message=category,
                        detail=f"{title}\n({viewers} viewers)",
                        parent=root,
                        )

def unfollow_dialog(streamer):
    '''Asks for confirmation, if the unfollow button is pressed. Rebuild the
    main panel, if confirmed.
    '''
    answer = messagebox.askyesno(title='Unfollow',
                        message='Are you sure that you '
                                f'want to unfollow {streamer}?',
                        default='no',
                        parent=root
                        )
    if answer:
        update = subprocess.run(['wtwitch', 'u', streamer],
                        capture_output=True,
                        text=True
                        )
        refresh_main_quiet()

def follow_dialog():
    '''Opens a text dialog and adds the entered string to the follow list.
    '''
    streamer = simpledialog.askstring(title='Follow',
                        prompt='Enter streamer name: ',
                        parent=root
                        )
    if streamer is None or len(streamer) <= 2:
        return
    else:
        update = subprocess.run(['wtwitch', 's', streamer],
                        capture_output=True,
                        text=True
                        )
        refresh_main_quiet()

def refresh_main_quiet():
    '''Refresh the main panel without running wtwitch c to avoid unnecessary
    Twitch API calls.
    '''
    global streamer_status
    streamer_status = extract_streamer_status()
    extract_streamer_status()
    main_frame.pack_forget()
    main_frame.destroy()
    draw_main()

def refresh_main():
    '''Runs wtwitch c and then rebuilds the main panel.
    '''
    check_status()
    global streamer_status
    streamer_status = extract_streamer_status()
    main_frame.pack_forget()
    main_frame.destroy()
    draw_main()

def mouse_scroll(event):
    meta_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

def draw_main():
    '''The main window. Calls streamer_buttons() twice, to draw buttons for
    online and offline streamers.
    '''
    # frame-canvas-frame to attach a scrollbar:
    meta_frame = ttk.Frame(root)
    meta_frame.grid(column='0', row='0', sticky='nsew')
    meta_canvas = tk.Canvas(meta_frame, highlightthickness='0')
    scrollbar = ttk.Scrollbar(meta_frame,
                        orient="vertical", command=meta_canvas.yview)
    meta_canvas.configure(yscrollcommand=scrollbar.set)
    global main_frame
    main_frame = ttk.Frame(meta_canvas)
    main_frame.grid(column=0, row=0, sticky='nesw')
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(0, weight=1)
    main_frame.bind("<Configure>", lambda e:
                        meta_canvas.configure(
                        scrollregion=meta_canvas.bbox("all"))
                        )
    # Draw main content:
    streamer_buttons(main_frame)
    # Finish scrollbar:
    meta_frame.columnconfigure(0, weight=1)
    meta_frame.rowconfigure(0, weight=1)
    meta_canvas.create_window((0, 0), window=main_frame, anchor="nw")
    meta_canvas.grid(row=0, column=0, sticky="nsew", pady=5, padx=5)
    scrollbar.grid(row=0, column=1, sticky="ns")
    meta_canvas.bind_all("<MouseWheel>", mouse_scroll)

def custom_player():
    '''Opens a dialog to set a custom media player.
    '''
    global user_settings
    user_settings = check_config()
    new_player = simpledialog.askstring(title='Player',
                        prompt='Enter your media player:',
                        parent=settings,
                        initialvalue=user_settings[0])
    if new_player is None or len(new_player) == 0:
        return
    else:
        set_player = subprocess.run(['wtwitch', 'p', new_player],
                        text=True,
                        capture_output=True
                        )
        confirmation = re.findall(r'\n (.*)\n\x1b\[0m', set_player.stdout)
        if len(confirmation) >= 1:
            user_settings = check_config()
            return messagebox.showinfo(title='Player',
                            message=confirmation[0],
                            parent=settings)
        else:
            error = re.findall(r'\[0m: (\S.*?\.)', set_player.stderr)
            return messagebox.showerror(title='Error',
                        message=error[0],
                        parent=settings)

def custom_quality():
    '''Opens a dialog to set a custom stream quality.
    '''
    global user_settings
    user_settings = check_config()
    new_quality = simpledialog.askstring(title='Quality',
                        prompt= '\n Options: 1080p60, 720p60, 720p, 480p, \n'
                                ' 360p, 160p, best, worst, and audio_only \n'
                                '\n'
                                ' Specify fallbacks separated by a comma: \n'
                                ' E.g. "720p,480p,worst" \n',
                        initialvalue=user_settings[1],
                        parent=settings)
    if new_quality is None or len(new_quality) == 0:
        return
    else:
        set_quality = subprocess.run(['wtwitch', 'q', new_quality],
                        text=True,
                        capture_output=True
                        )
        confirmation = re.findall(r'\n\s(.*)\n\x1b\[0m', set_quality.stdout)
        if len(confirmation) >= 1:
            user_settings = check_config()
            return messagebox.showinfo(title='Quality',
                        message=confirmation[0],
                        parent=settings)
        else:
            error = re.findall(r'\[0m: (\S.*?\.)', set_quality.stderr)
            return messagebox.showerror(title='Error',
                        message=error[0],
                        parent=settings)

def check_config():
    with open(wtwitch_config_file(), 'r') as config:
        config = json.load(config)
        player = config['player']
        quality = config['quality']
        colors = config['colors']
        print_offline_subs = config['printOfflineSubscriptions']
    return player, quality, colors, print_offline_subs

def settings_dialog():
    '''Opens a toplevel window with four settings options.
    '''
    global user_settings
    user_settings = check_config()
    global selected_player
    selected_player = tk.StringVar()
    if user_settings[0] in ['mpv', 'vlc']:
        selected_player.set(user_settings[0])
    else:
        selected_player.set('custom')
    global selected_quality
    selected_quality = tk.StringVar()
    if user_settings[1] in ['best', '720p,720p60,480p,best', '480p,worst']:
        selected_quality.set(user_settings[1])
    else:
        selected_quality.set('custom')
    global settings
    settings = tk.Toplevel(master=root)
    settings.title('Settings')
    settings.transient(root)
    settings.grab_set()
    meta_frame = ttk.Frame(settings)
    meta_frame.pack(expand=True, fill='both', ipadx=10, ipady=10)
    top_f = ttk.Frame(meta_frame)
    top_f.pack()
    qual_f = ttk.Labelframe(top_f, text='Stream quality')
    qual_f.pack(side='left', anchor='nw', padx=5, pady=5)
    high_qual = ttk.Radiobutton(qual_f, text='High',
                value='best', variable=selected_quality,
                command=lambda u = user_settings:
                [subprocess.run(['wtwitch', 'q', 'best'],
                capture_output=True,
                text=True)]
                )
    high_qual.pack(expand=True, fill='both')
    mid_qual = ttk.Radiobutton(qual_f, text='Medium',
                value='720p,720p60,480p,best', variable=selected_quality,
                command=lambda:
                [subprocess.run(['wtwitch', 'q', '720p,720p60,480p,best'],
                capture_output=True,
                text=True)]
                )
    mid_qual.pack(expand=True, fill='both')
    low_qual = ttk.Radiobutton(qual_f, text='Low',
                value='480p,worst', variable=selected_quality,
                command=lambda:
                [subprocess.run(['wtwitch', 'q', '480p,worst'],
                capture_output=True,
                text=True)]
                )
    low_qual.pack(expand=True, fill='both')
    custom_qual = ttk.Radiobutton(qual_f, text='Custom',
                value='custom', variable=selected_quality,
                command=lambda: custom_quality())
    custom_qual.pack(expand=True, fill='both')
    play_f = ttk.Labelframe(top_f, text='Choose player')
    play_f.pack(side='right', anchor='ne', padx=5, pady=5)
    pick_mpv = ttk.Radiobutton(play_f, text='mpv',
                value='mpv', variable=selected_player,
                command=lambda: [subprocess.run(['wtwitch', 'p', 'mpv'],
                capture_output=True,
                text=True)]
                )
    pick_mpv.pack(expand=True, fill='both')
    pick_vlc = ttk.Radiobutton(play_f, text='VLC',
                value='vlc', variable=selected_player,
                command=lambda: [subprocess.run(['wtwitch', 'p', 'vlc'],
                capture_output=True,
                text=True)]
                )
    pick_vlc.pack(expand=True, fill='both')
    pick_custom = ttk.Radiobutton(play_f, text='Custom',
                value='custom', variable=selected_player,
                command=lambda: custom_player())
    pick_custom.pack(expand=True, fill='both')
    bottom_f = ttk.Frame(meta_frame)
    bottom_f.pack()
    global selected_theme
    style = ttk.Style()
    selected_theme = tk.StringVar()
    theme_f = ttk.LabelFrame(bottom_f, text='Themes')
    theme_f.pack(anchor='nw', side='left', padx=5, pady=5)
    for theme_name in ttk.Style.theme_names(style):
        pick_theme = ttk.Radiobutton(theme_f,
                text=theme_name,
                value=theme_name,
                variable=selected_theme,
                command=lambda t=theme_name: style.theme_use(t)
                )
        pick_theme.pack(expand=True, fill='both')
    scale_f = ttk.Labelframe(bottom_f, text='Window scale')
    scale_f.pack(side='left', anchor='nw', padx=5, pady=5)
    color_f = ttk.Labelframe(bottom_f, text='Window color:')
    color_f.pack(side='right', anchor='ne', padx=5, pady=5)

def menu_bar():
    '''The menu bar of the root window.
    '''
    font = ('Cantarell', '11')
    font2 = ('Cantarell', '11', 'bold')
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    menubar.add_command(label='Refresh', font=font2,
            command=lambda: refresh_main())
    menubar.add_command(label='Follow streamer', font=font,
            command=lambda: follow_dialog())
    menubar.add_command(label='Settings', font=font,
            command=lambda: settings_dialog())

def window_size():
    """Sets the default window length, depending on the number of streamers in
    the follow list. Fixed between 360 and 550 px. Width fixed at 280 px.
    """
    min_height = 360
    max_height = 550
    variable_height = len(streamer_status[0])*28+len(streamer_status[1])*28+100
    if variable_height > max_height:
        window_height = str(max_height)
    elif variable_height < min_height:
        window_height = str(min_height)
    else:
        window_height = str(variable_height)
    return f"285x{window_height}"

def toggle_settings():
    """Checks if wtwitch prints offline streamers and color output. Latter is
    needed to filter wtwitch output with regex.
    """
    user_settings = check_config()
    if user_settings[2] == 'true' and user_settings[3] == 'true':
        return
    else:
        if user_settings[2] == 'false':
            wtwitch_l = subprocess.run(['wtwitch', 'l'],
                            capture_output=True,
                            text=True
                            )
            if wtwitch_l.stderr:
                messagebox.showerror("Error", wtwitch_l.stderr)
        if user_settings[3] == 'false':
            wtwitch_f = subprocess.run(['wtwitch', 'f'],
                            capture_output=True,
                            text=True
                            )
            if wtwitch_f.stderr:
                messagebox.showerror("Error", wtwitch_f.stderr)


# Make sure that colors in the terminal output are activated:
toggle_settings()
# Check the online/offline status once before window initialization:
check_status()
streamer_status = extract_streamer_status()

# Create the main window
root = tk.Tk()
root.title("GUI for wtwitch")
root.geometry(window_size())
root.resizable(False, True)
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Import icons:
unfollow_icon = tk.PhotoImage(file=encoded_images.unfollow_icon)
vod_icon = tk.PhotoImage(file=encoded_images.vod_icon)
streaming_icon = tk.PhotoImage(file=encoded_images.streaming_icon)
offline_icon = tk.PhotoImage(file=encoded_images.offline_icon)
play_icon = tk.PhotoImage(file=encoded_images.play_icon)
close_icon = tk.PhotoImage(file=encoded_images.close_icon)

app_icon = tk.PhotoImage(file=encoded_images.app_icon)
root.iconphoto(False, app_icon)

# Remove icon temp files:
os.remove(encoded_images.unfollow_icon)
os.remove(encoded_images.vod_icon)
os.remove(encoded_images.streaming_icon)
os.remove(encoded_images.offline_icon)
os.remove(encoded_images.play_icon)
os.remove(encoded_images.close_icon)
os.remove(encoded_images.app_icon)

menu_bar()
draw_main()
root.mainloop()