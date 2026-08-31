import asyncio
import json
import threading
import urllib.request
import tkinter as tk
from tkinter import ttk, filedialog
import os 
import websockets
import http.server
import socketserver
import shutil

SAVE_FILE = "draft_state.json"

default_state = {
    "patch": "NACE Week 1",
    "sponsor": "PURDUE FORT WAYNE ESPORTS",
    "ddragon_version": "14.1.1",
    "show_coaches": False,
    "show_spells": True,
    "blue": {
        "name": "PFW",
        "coach": "",
        "logo": "",
        "score": 0,
        "use_champ_names": True,
        "players": ["TOP", "JNG", "MID", "ADC", "SUP"],
        "picks": ["None", "None", "None", "None", "None"],
        "bans": ["None", "None", "None", "None", "None"],
        "spells": [["None", "None"] for _ in range(5)]
    },
    "red": {
        "name": "OPP",
        "coach": "",      
        "logo": "",
        "score": 0,
        "use_champ_names": True, 
        "players": ["TOP", "JNG", "MID", "ADC", "SUP"],
        "picks": ["None", "None", "None", "None", "None"],
        "bans": ["None", "None", "None", "None", "None"],
        "spells": [["None", "None"] for _ in range(5)]
    }
}

def load_state():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                saved_state = json.load(f)
                for key in default_state:
                    if key not in saved_state:
                        saved_state[key] = default_state[key]
                return saved_state
        except Exception as e:
            print(f"Error reading save file: {e}")
    return default_state

state = load_state()

connected_clients = set()
server_loop = None

def get_champion_data():
    try:
        ver_url = "https://ddragon.leagueoflegends.com/api/versions.json"
        with urllib.request.urlopen(ver_url, timeout=3) as res:
            latest_version = json.loads(res.read().decode())[0]
            state["ddragon_version"] = latest_version

        champ_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion.json"
        with urllib.request.urlopen(champ_url, timeout=3) as res:
            data = json.loads(res.read().decode())
            champion_keys = sorted(list(data["data"].keys()))
            return ["None"] + champion_keys
    except:
        return ["None", "Aatrox", "Ahri", "Ashe", "LeeSin", "Leona"]

CHAMPIONS_LIST = get_champion_data()

SUMMONER_SPELLS = [
    "None", "Barrier", "Cleanse", "Ignite", 
    "Exhaust", "Flash", "Ghost", "Heal", 
    "Clarity", "Smite", "Teleport", "Snowball"
]

def start_http_server():
    PORT = 8000
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("localhost", PORT), Handler) as httpd:
        print(f"Serving HTTP at http://localhost:{PORT}")
        httpd.serve_forever()

async def handler(websocket):
    connected_clients.add(websocket)
    await websocket.send(json.dumps(state))
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)

async def broadcast_state():
    if connected_clients:
        message = json.dumps(state)
        await asyncio.gather(*[client.send(message) for client in connected_clients])

def trigger_broadcast():
    if server_loop and server_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_state(), server_loop)

async def run_server():
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future() 

def start_server():
    global server_loop
    server_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(server_loop)
    server_loop.run_until_complete(run_server())

class SearchableDropdown(ttk.Frame):
    def __init__(self, parent, values, width=14, **kwargs):
        super().__init__(parent)
        self.values = values
        self.current_value = tk.StringVar(value="None")
        
        self.btn = ttk.Button(self, textvariable=self.current_value, width=width, command=self.open_popup)
        self.btn.pack(fill="both", expand=True)
        self.popup = None

    def set(self, value):
        self.current_value.set(value)

    def get(self):
        return self.current_value.get()
        
    def bind(self, sequence, func, add=None):
        self.btn.bind(sequence, func, add)
        
    def event_generate(self, sequence):
        self.btn.event_generate(sequence)

    def open_popup(self):
        if self.popup and self.popup.winfo_exists():
            return

        self.popup = tk.Toplevel(self)
        self.popup.wm_overrideredirect(True)
        self.popup.attributes('-topmost', True)
        
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        self.popup.geometry(f"{self.winfo_width() + 40}x200+{x}+{y}")

        search_var = tk.StringVar()
        search_entry = ttk.Entry(self.popup, textvariable=search_var)
        search_entry.pack(fill="x", padx=1, pady=1)
        search_entry.focus_set()

        list_frame = ttk.Frame(self.popup)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode="browse")
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        def update_list(*args):
            typed = search_var.get().lower()
            listbox.delete(0, tk.END)
            for item in self.values:
                if typed in item.lower():
                    listbox.insert(tk.END, item)
            if listbox.size() > 0:
                listbox.selection_set(0)

        update_list()
        search_var.trace_add("write", update_list)

        def make_selection(event=None):
            if listbox.curselection():
                self.set(listbox.get(listbox.curselection()[0]))
                self.event_generate("<<ComboboxSelected>>")
            self.popup.destroy()

        def check_focus():
            if self.popup and self.popup.winfo_exists():
                focus = self.popup.focus_get()
                if not focus or not str(focus).startswith(str(self.popup)):
                    self.popup.destroy()

        listbox.bind("<ButtonRelease-1>", make_selection)
        search_entry.bind("<Return>", make_selection)
        search_entry.bind("<Escape>", lambda e: self.popup.destroy())
        self.popup.bind("<FocusOut>", lambda e: self.popup.after(100, check_focus))

class OverlayController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LoL Esports Broadcast Controller")
        self.geometry("1040x760")
        self.configure(padx=10, pady=10)

        meta_frame = ttk.LabelFrame(self, text="Broadcast Match Info", padding=8)
        meta_frame.pack(fill="x", pady=5)

        ttk.Label(meta_frame, text="League/Match:").grid(row=0, column=0, padx=4)
        self.patch_entry = ttk.Entry(meta_frame, width=15)
        self.patch_entry.insert(0, state["patch"])
        self.patch_entry.grid(row=0, column=1, padx=4)

        ttk.Label(meta_frame, text="TOP INFO:").grid(row=0, column=2, padx=4)
        self.sponsor_entry = ttk.Entry(meta_frame, width=15)
        self.sponsor_entry.insert(0, state["sponsor"])
        self.sponsor_entry.grid(row=0, column=3, padx=4)

        self.show_coaches_var = tk.BooleanVar(value=state["show_coaches"])
        self.coach_checkbox = ttk.Checkbutton(
            meta_frame, 
            text="Show Coaches", 
            variable=self.show_coaches_var,
            command=self.push_updates
        )
        self.coach_checkbox.grid(row=0, column=4, padx=15)

        self.show_spells_var = tk.BooleanVar(value=state["show_spells"])
        self.spell_checkbox = ttk.Checkbutton(
            meta_frame, 
            text="Show Spells", 
            variable=self.show_spells_var,
            command=self.push_updates
        )
        self.spell_checkbox.grid(row=0, column=5, padx=15)

        teams_container = ttk.Frame(self)
        teams_container.pack(fill="both", expand=True, pady=5)

        # NEW: Small swap button centered above the teams
        swap_btn = ttk.Button(teams_container, text="⇄ Swap Names & Logos", command=self.swap_teams)
        swap_btn.grid(row=0, column=0, columnspan=2, pady=(0, 5))

        self.blue_widgets = self._build_team_column(teams_container, "Blue Side", "blue", 0)
        self.red_widgets = self._build_team_column(teams_container, "Red Side", "red", 1)

        # --- RESTORE SINGLE BROADCAST BUTTON ---
        broadcast_btn = tk.Button(
            self, text="BROADCAST UPDATE TO OVERLAY", bg="#007acc", fg="white",
            font=("Segoe UI", 12, "bold"), command=self.push_updates
        )
        broadcast_btn.pack(fill="x", pady=5)

    def swap_teams(self):
        blue_name = self.blue_widgets["name"].get()
        blue_logo = self.blue_widgets["logo"].get()
        
        red_name = self.red_widgets["name"].get()
        red_logo = self.red_widgets["logo"].get()
        
        self.blue_widgets["name"].delete(0, tk.END)
        self.blue_widgets["name"].insert(0, red_name)
        
        self.red_widgets["name"].delete(0, tk.END)
        self.red_widgets["name"].insert(0, blue_name)
        
        self.blue_widgets["logo"].set(red_logo)
        self.red_widgets["logo"].set(blue_logo)
        
        self.push_updates()

    def _build_team_column(self, parent, title, side_key, column_idx):
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.grid(row=1, column=column_idx, sticky="nsew", padx=5)
        parent.grid_columnconfigure(column_idx, weight=1)

        # Team, Coach & Logo Info
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill="x", pady=2)

        ttk.Label(info_frame, text="Team Tag:").grid(row=0, column=0, sticky="w")
        team_name_entry = ttk.Entry(info_frame, width=12)
        team_name_entry.insert(0, state[side_key]["name"])
        team_name_entry.grid(row=0, column=1, padx=4, pady=2)

        ttk.Label(info_frame, text="Coach:").grid(row=1, column=0, sticky="w")
        coach_entry = ttk.Entry(info_frame, width=12)
        coach_entry.insert(0, state[side_key]["coach"])
        coach_entry.grid(row=1, column=1, padx=4, pady=2)

        # NEW: Logo Selection
        ttk.Label(info_frame, text="Logo:").grid(row=2, column=0, sticky="w")
        logo_path_var = tk.StringVar(value=state[side_key].get("logo", ""))
        
        def browse_logo():
            filename = filedialog.askopenfilename(
                title="Select Team Logo",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp *.svg")]
            )
            if filename:
                # Copy the selected image into the local folder so the web server can serve it
                ext = os.path.splitext(filename)[1]
                local_name = f"{side_key}_logo{ext}"
                dest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), local_name)
                
                try:
                    shutil.copy(filename, dest_path)
                    logo_path_var.set(local_name)  # Save the local file name instead of the C:/ path
                    self.push_updates()
                except Exception as e:
                    print(f"Failed to copy image: {e}")

        logo_btn = ttk.Button(info_frame, textvariable=logo_path_var, width=10, command=browse_logo)
        logo_btn.grid(row=2, column=1, padx=4, pady=2)

        # Bans Section
        ban_frame = ttk.LabelFrame(frame, text="Bans (1 to 5)", padding=6)
        ban_frame.pack(fill="x", pady=6)
        ban_combos = []
        for i in range(5):
            ttk.Label(ban_frame, text=f"Ban {i+1}:").grid(row=i, column=0, sticky="w", pady=1)
            cb = SearchableDropdown(ban_frame, values=CHAMPIONS_LIST, width=18)
            cb.set(state[side_key]["bans"][i])
            cb.bind("<<ComboboxSelected>>", lambda e: self.push_updates())
            cb.grid(row=i, column=1, padx=4, pady=1)
            ban_combos.append(cb)

        def clear_bans():
            for cb in ban_combos:
                cb.set("None")
            self.push_updates()

        ttk.Button(ban_frame, text="Clear Bans", command=clear_bans).grid(row=5, column=0, columnspan=2, pady=5)

        # Picks & Player Section
        pick_frame = ttk.LabelFrame(frame, text="Picks, Players & Spells (1 to 5)", padding=6)
        pick_frame.pack(fill="x", pady=6)
        player_entries, pick_combos, spell_combos_list = [], [], []
        
        stored_player_names = list(state[side_key]["players"])
        use_champ_var = tk.BooleanVar(value=state[side_key].get("use_champ_names", True))

        def refresh_ui_entries(push=False):
            is_champ_mode = use_champ_var.get()
            for i in range(5):
                entry = player_entries[i]
                if is_champ_mode and str(entry['state']) == 'normal':
                    stored_player_names[i] = entry.get()

                entry.config(state="normal")
                entry.delete(0, tk.END)
                
                if is_champ_mode:
                    champ = pick_combos[i].get()
                    entry.insert(0, champ if champ != "None" else "")
                    entry.config(state="readonly")
                else:
                    entry.insert(0, stored_player_names[i])
            
            if is_champ_mode:
                clear_names_btn.config(state="disabled")
            else:
                clear_names_btn.config(state="normal")
                
            if push:
                self.push_updates()

        ttk.Checkbutton(
            pick_frame, 
            text="Show Champion Names Instead of Players", 
            variable=use_champ_var,
            command=lambda: refresh_ui_entries(push=True)
        ).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 6))

        def on_pick_change(event, idx):
            if use_champ_var.get():
                entry = player_entries[idx]
                entry.config(state="normal")
                entry.delete(0, tk.END)
                champ = pick_combos[idx].get()
                entry.insert(0, champ if champ != "None" else "")
                entry.config(state="readonly")
            self.push_updates()

        for i in range(5):
            r = i + 1
            ttk.Label(pick_frame, text=f"P{r}:").grid(row=r, column=0, sticky="w", pady=2)
            
            p_entry = ttk.Entry(pick_frame, width=9)
            p_entry.grid(row=r, column=1, padx=1, pady=2)
            player_entries.append(p_entry)

            cb = SearchableDropdown(pick_frame, values=CHAMPIONS_LIST, width=12)
            cb.set(state[side_key]["picks"][i])
            cb.grid(row=r, column=2, padx=1, pady=2)
            cb.bind("<<ComboboxSelected>>", lambda e, idx=i: on_pick_change(e, idx), add="+")
            pick_combos.append(cb)

            # Visual spacer column separating Champion picks from Summoner Spells
            ttk.Separator(pick_frame, orient="vertical").grid(row=r, column=3, sticky="ns", padx=8, pady=2)

            # Two Spell Dropdowns
            row_spells = []
            saved_spells = state[side_key].get("spells", [["None", "None"] for _ in range(5)])[i]
            for s_idx in range(2):
                scb = SearchableDropdown(pick_frame, values=SUMMONER_SPELLS, width=9)
                scb.set(saved_spells[s_idx] if s_idx < len(saved_spells) else "None")
                scb.bind("<<ComboboxSelected>>", lambda e: self.push_updates())
                scb.grid(row=r, column=4+s_idx, padx=1, pady=2)
                row_spells.append(scb)
            spell_combos_list.append(row_spells)

        def clear_names():
            if not use_champ_var.get():
                for i, entry in enumerate(player_entries):
                    stored_player_names[i] = ""
                    entry.delete(0, tk.END)
                self.push_updates()

        def clear_picks():
            for cb in pick_combos:
                cb.set("None")
                cb.event_generate("<<ComboboxSelected>>") 
            self.push_updates()

        def clear_spells():
            for row_spells in spell_combos_list:
                for scb in row_spells:
                    scb.set("None")
            self.push_updates()

        # Action Buttons positioned precisely under their columns
        clear_names_btn = ttk.Button(pick_frame, text="Clear Names", command=clear_names)
        clear_names_btn.grid(row=6, column=1, pady=6, padx=1, sticky="ew")
        
        ttk.Button(pick_frame, text="Clear Picks", command=clear_picks).grid(row=6, column=2, pady=6, padx=1, sticky="ew")
        ttk.Button(pick_frame, text="Clear Spells", command=clear_spells).grid(row=6, column=4, columnspan=2, pady=6, padx=1, sticky="ew")

        refresh_ui_entries(push=False)

        return {
            "name": team_name_entry, 
            "coach": coach_entry, 
            "logo": logo_path_var,
            "bans": ban_combos, 
            "players": player_entries, 
            "picks": pick_combos,
            "spells": spell_combos_list,
            "use_champ_names": use_champ_var
        }

    def push_updates(self):
        state["patch"] = self.patch_entry.get()
        state["sponsor"] = self.sponsor_entry.get()
        state["show_coaches"] = self.show_coaches_var.get()
        state["show_spells"] = self.show_spells_var.get()

        for side_key, widgets in [("blue", self.blue_widgets), ("red", self.red_widgets)]:
            state[side_key]["name"] = widgets["name"].get()
            state[side_key]["coach"] = widgets["coach"].get()
            state[side_key]["logo"] = widgets["logo"].get()
            state[side_key]["use_champ_names"] = widgets["use_champ_names"].get()
            state[side_key]["bans"] = [cb.get() for cb in widgets["bans"]]
            state[side_key]["picks"] = [cb.get() for cb in widgets["picks"]]
            
            state[side_key]["spells"] = [[scb.get() for scb in row_spells] for row_spells in widgets["spells"]]

            if not state[side_key]["use_champ_names"]:
                state[side_key]["players"] = [entry.get() for entry in widgets["players"]]

        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            print(f"Error writing save file: {e}")

        trigger_broadcast()

if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()
    threading.Thread(target=start_http_server, daemon=True).start()
    app = OverlayController()
    app.mainloop()