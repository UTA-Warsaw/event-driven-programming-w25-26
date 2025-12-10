import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
import random
from PIL import Image, ImageTk
import pygame


class RPGMapExplorer:
    """
    FEATURE: Cleared Map Layer added.
    NEW FEATURE: Once the player leaves a normal terrain (F or G), it is marked as cleared
                 and subsequent visits to that specific spot will not trigger a battle.
    BATTLE CHANCE: Set to 25% (0.25) on uncleared 'F' and 'G' tiles.
    """

    def __init__(self, master):
        self.master = master
        master.title("RPG Adventure: Visual Battles - HARD MODE LIGHT")

        # --- PYGAME & MUSIC SETUP ---
        self.music_file = "game_music.mp3"
        self.music_initialized = False

        try:
            pygame.mixer.init()
            self.music_initialized = True
            self.play_music()
        except pygame.error as e:
            print(f"Warning: Could not initialize Pygame mixer or load music. Error: {e}")

        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Game Setup ---
        self.map_size = 15
        self.cell_size = 35
        self.map_pixel_size = self.map_size * self.cell_size
        self.player_pos = [0, 0]
        self.game_over = False
        self.in_dialogue = False
        self.battle_window_open = False

        # --- DIFFICULTY AND STATS ---
        self.CRIT_CHANCE = 0.20
        self.CRIT_MULTIPLIER = 1.5
        self.BATTLE_CHANCE = 0.25  # 25% battle chance
        self.player_stats = {
            'Health': 90, 'MaxHealth': 90,
            'Gold': 20, 'Level': 1,
            'Attack': 10, 'XP': 0, 'NextLevel': 100
        }
        self.inventory = {'Health Potion': 0}
        self.stat_vars = {}
        self.enemy_gallery = [
            {'name': 'Goblin', 'color': '#2ecc71', 'symbol': '👹'},
            {'name': 'Orc Warrior', 'color': '#e74c3c', 'symbol': '👺'},
            {'name': 'Dark Mage', 'color': '#8e44ad', 'symbol': '🧙‍♂️'},
            {'name': 'Bandit', 'color': '#f39c12', 'symbol': '🦹'}
        ]

        self.player_image_path = "rambo_okan.png"
        self.player_photo = None
        self.player_photo_tk_icon = None
        self.player_icon = '🤠'
        self.load_player_image()

        # --- RIDDLES LIST (Expanded and Translated) ---
        self.riddles = [
            {
                'question': "Filled by day, emptied by night. What is it?",
                'answer': "shoe",
                'reward': {'type': 'MaxHealth', 'amount': 15}
            },
            {
                'question': "It has teeth but cannot eat. What is it?",
                'answer': "comb",
                'reward': {'type': 'Gold', 'amount': 50}
            },
            {
                'question': "It runs but never walks, often murmurs, never talks, has a bed but never sleeps, has a mouth but never eats. What is it?",
                'answer': "river",
                'reward': {'type': 'Attack', 'amount': 3}
            },
            {
                'question': "What gets smaller the more you add to it?",
                'answer': "hole",
                'reward': {'type': 'Health', 'amount': 30}
            },
            {
                'question': "What has an eye but cannot see?",
                'answer': "needle",
                'reward': {'type': 'MaxHealth', 'amount': 10}
            },
            {
                'question': "I am tall when I am young, and I am short when I am old. What am I?",
                'answer': "candle",
                'reward': {'type': 'Gold', 'amount': 40}
            },
            {
                'question': "What is full of holes but still holds water?",
                'answer': "sponge",
                'reward': {'type': 'Attack', 'amount': 4}
            },
        ]

        # --- BACKGROUND IMAGE SETUP (FOR ENTIRE WINDOW) ---
        self.background_image_path = "background.jpg"
        self.background_photo = None

        master.update_idletasks()
        initial_width = master.winfo_width()
        initial_height = master.winfo_height()
        if initial_width < 100 or initial_height < 100:
            initial_width, initial_height = 800, 700
            master.geometry(f"{initial_width}x{initial_height}")

        self.load_root_background_image(initial_width, initial_height)

        self.bg_label = tk.Label(master, image=self.background_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_label.image = self.background_photo

        # --- Terrain Types ---
        self.terrains = {
            'F': {'color': '#27ae60', 'symbol': '🌲', 'name': 'Forest', 'message': 'Dark woods.'},
            'M': {'color': '#7f8c8d', 'symbol': '⛰', 'name': 'Mountain Pass', 'message': 'Rocky path. (-2 Health)'},
            'W': {'color': '#3498db', 'symbol': '🌊', 'name': 'River', 'message': 'Cool waters.'},
            'T': {'color': '#f39c12', 'symbol': '🏠', 'name': 'Town', 'message': 'A place to rest.'},
            'G': {'color': '#88b04b', 'symbol': '🟩', 'name': 'Grassland', 'message': 'Open field.'},
            '?': {'color': '#8e44ad', 'symbol': '❓', 'name': 'Mystery Spot', 'message': 'Something strange is here...'},
            'K': {'color': '#c0392b', 'symbol': '🏰', 'name': 'King\'s Castle', 'message': 'The Goal!'},
            'E': {'color': '#5a4d45', 'symbol': '👴', 'name': 'Elder\'s Hut',
                  'message': 'An old man sits here, waiting to test your wits.'}
        }

        self.generate_map()

        # New: Cleared map layer to prevent battles on revisited common tiles (F, G)
        self.cleared_map = [[False for _ in range(self.map_size)] for _ in range(self.map_size)]
        self.cleared_map[0][0] = True  # Starting tile is considered cleared

        # --- GUI Components ---
        WIDGET_BG = "#34495e"
        WIDGET_FG = "#ecf0f1"

        self.stats_frame = tk.Frame(master, bg=WIDGET_BG, padx=10, pady=5)
        self.stats_frame.pack(fill='x', padx=10, pady=(5, 5))
        self.setup_stats_display(WIDGET_BG, WIDGET_FG)

        self.inventory_frame = tk.Frame(master, bg=WIDGET_BG, padx=10, pady=5)
        self.inventory_frame.pack(fill='x', padx=10, pady=(5, 10))
        self.setup_inventory_display(WIDGET_BG, WIDGET_FG)

        self.canvas = tk.Canvas(master, width=self.map_pixel_size,
                                height=self.map_pixel_size,
                                bg="#ecf0f1", highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)

        self.status_text = tk.StringVar(
            value="Mission: Reach the King's Castle (🏰) in the bottom right! (HARD MODE LIGHT)")
        self.status_label = tk.Label(master, textvariable=self.status_text,
                                     font=('Helvetica', 10), bg=WIDGET_BG, fg="#f1c40f", pady=5)
        self.status_label.pack(fill='x')

        # Key Bindings
        master.bind('<Up>', lambda e: self.move_player('up'))
        master.bind('<Down>', lambda e: self.move_player('down'))
        master.bind('<Left>', lambda e: self.move_player('left'))
        master.bind('<Right>', lambda e: self.move_player('right'))
        master.bind('1', lambda e: self.handle_dialogue_choice(1))
        master.bind('2', lambda e: self.handle_dialogue_choice(2))
        master.bind('3', lambda e: self.handle_dialogue_choice(3))

        master.bind('<Configure>', self.on_resize)

        self.draw_map()
        self.draw_player()
        self.update_stats_display()

    # --- HELPER METHODS ---

    def on_closing(self):
        """Stops music and closes the window safely."""
        if self.music_initialized:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        self.master.destroy()

    def play_music(self):
        """Starts background music."""
        if not self.music_initialized: return
        try:
            pygame.mixer.music.load(self.music_file)
            pygame.mixer.music.play(-1, 10.0)
            pygame.mixer.music.set_volume(0.3)
        except pygame.error as e:
            self.music_initialized = False

    def on_resize(self, event):
        """Resizes the background image when the window size changes."""
        if event.widget == self.master:
            self.load_root_background_image(event.width, event.height)
            if self.bg_label:
                self.bg_label.config(image=self.background_photo)
                self.bg_label.image = self.background_photo

    def load_root_background_image(self, width, height):
        """Loads and prepares the background image for the main window."""
        if width == 1 or height == 1: return
        try:
            img = Image.open(self.background_image_path)
            img = img.resize((width, height), Image.LANCZOS)
            self.background_photo = ImageTk.PhotoImage(img)
        except FileNotFoundError:
            self.background_photo = None
            self.master.configure(bg="#2c3e50")
        except Exception as e:
            self.background_photo = None
            self.master.configure(bg="#2c3e50")

    def setup_stats_display(self, bg, fg):
        """Initializes the display widgets for player stats."""
        stats = ['Health', 'Gold', 'Level', 'XP']
        for i, stat in enumerate(stats):
            var = tk.StringVar()
            self.stat_vars[stat] = var
            lbl = tk.Label(self.stats_frame, textvariable=var, font=('Helvetica', 9, 'bold'), bg=bg, fg=fg)
            lbl.grid(row=0, column=i, padx=10)

    def update_stats_display(self):
        """Updates the text variables displaying player statistics."""
        self.stat_vars['Health'].set(f"❤️ {self.player_stats['Health']}/{self.player_stats['MaxHealth']}")
        self.stat_vars['Gold'].set(f"💰 {self.player_stats['Gold']}")
        self.stat_vars['Level'].set(f"⭐ Lvl {self.player_stats['Level']}")
        self.stat_vars['XP'].set(f"✨ XP {self.player_stats['XP']}/{self.player_stats['NextLevel']}")

    def gain_xp(self, amount):
        """Handles XP gain and checks for level up."""
        self.player_stats['XP'] += amount
        if self.player_stats['XP'] >= self.player_stats['NextLevel']:
            self.player_stats['Level'] += 1
            self.player_stats['XP'] -= self.player_stats['NextLevel']
            self.player_stats['NextLevel'] = int(self.player_stats['NextLevel'] * 1.5)
            self.player_stats['MaxHealth'] += 20
            self.player_stats['Health'] = self.player_stats['MaxHealth']
            self.player_stats['Attack'] += 5
            messagebox.showinfo("Level Up!",
                                f"CONGRATULATIONS! You reached Level {self.player_stats['Level']}! You feel much stronger.")
        self.update_stats_display()

    def setup_inventory_display(self, bg, fg):
        """Sets up the inventory display and use potion button."""
        self.potion_count_var = tk.StringVar(value=f"Potions: {self.inventory.get('Health Potion', 0)}")
        potion_label = tk.Label(self.inventory_frame, textvariable=self.potion_count_var,
                                font=('Helvetica', 10, 'bold'), bg=bg, fg=fg, padx=10)
        potion_label.pack(side=tk.LEFT, padx=(0, 15))
        use_button = tk.Button(self.inventory_frame, text="Use Potion (+30 Health)", command=self.use_potion,
                               font=('Helvetica', 10, 'bold'), bg="#27ae60", fg="white", relief='raised')
        use_button.pack(side=tk.LEFT)

    def update_inventory_display(self):
        """Updates the potion count display."""
        count = self.inventory.get('Health Potion', 0)
        self.potion_count_var.set(f"Potions: {count}")

    def use_potion(self):
        """Allows the player to use a health potion."""
        if self.inventory.get('Health Potion', 0) > 0:
            if self.player_stats['Health'] < self.player_stats['MaxHealth']:
                self.inventory['Health Potion'] -= 1
                heal = 30
                self.player_stats['Health'] = min(self.player_stats['MaxHealth'], self.player_stats['Health'] + heal)
                self.update_stats_display()
                self.update_inventory_display()
                self.status_text.set("You used a potion and restored 30 Health!")
            else:
                self.status_text.set("You are already at full health!")
        else:
            self.status_text.set("You have no health potions left!")

    def generate_map(self):
        """Creates the initial game map with terrains and special spots."""
        keys = ['F', 'M', 'W', 'G', 'F', 'G']
        self.map_grid = [[random.choice(keys) for _ in range(self.map_size)] for _ in range(self.map_size)]
        self.map_grid[0][0] = 'G'
        self.map_grid[self.map_size - 1][self.map_size - 1] = 'K'
        num_towns = random.randint(3, 6)
        towns_placed = 0
        while towns_placed < num_towns:
            tr, tc = random.randint(1, self.map_size - 2), random.randint(1, self.map_size - 2)
            if self.map_grid[tr][tc] not in ['T', 'K'] and (tr, tc) != (0, 0):
                self.map_grid[tr][tc] = 'T'
                towns_placed += 1

        # Place '?' mystery spots
        for _ in range(4):
            self.map_grid[random.randint(1, 13)][random.randint(1, 13)] = '?'

        # Place 'E' Elder's hut spots
        num_elders = random.randint(2, 4)
        elders_placed = 0
        while elders_placed < num_elders:
            er, ec = random.randint(1, self.map_size - 2), random.randint(1, self.map_size - 2)
            if self.map_grid[er][ec] not in ['T', 'K', '?', 'E'] and (er, ec) != (0, 0):
                self.map_grid[er][ec] = 'E'
                elders_placed += 1

    def load_player_image(self):
        """Loads and prepares the player image for both large and map icon display."""
        try:
            img = Image.open(self.player_image_path)
            img = img.resize((120, 120), Image.LANCZOS)
            self.player_photo = ImageTk.PhotoImage(img)
            img_icon = Image.open(self.player_image_path)
            img = img_icon.resize((35, 35), Image.LANCZOS)
            self.player_photo_tk_icon = ImageTk.PhotoImage(img)
        except FileNotFoundError:
            self.player_photo = None;
            self.player_photo_tk_icon = None
        except Exception as e:
            self.player_photo = None;
            self.player_photo_tk_icon = None

    def draw_map(self):
        """Draws the map grid on the canvas."""
        self.canvas.delete("all")
        for r in range(self.map_size):
            for c in range(self.map_size):
                t = self.terrains[self.map_grid[r][c]]
                x1, y1 = c * self.cell_size, r * self.cell_size
                self.canvas.create_rectangle(x1, y1, x1 + self.cell_size, y1 + self.cell_size, fill=t['color'],
                                             outline="#bdc3c7")
                self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text=t['symbol'],
                                        font=('Segoe UI Emoji', 14), fill="black")

    def draw_player(self):
        """Draws the player icon at the current position."""
        self.canvas.delete("player")
        r, c = self.player_pos
        x, y = c * self.cell_size + self.cell_size / 2, r * self.cell_size + self.cell_size / 2
        if self.player_photo_tk_icon:
            self.canvas.create_image(x, y, image=self.player_photo_tk_icon, tags="player")
        else:
            self.canvas.create_text(x, y, text=self.player_icon, font=('Segoe UI Emoji', 18), tags="player")

    def move_player(self, d):
        """Moves the player and marks the previous tile as cleared."""
        if self.game_over or self.in_dialogue or self.battle_window_open: return

        # Save the current position to mark as cleared
        old_r, old_c = self.player_pos

        nr, nc = self.player_pos
        if d == 'up':
            nr -= 1
        elif d == 'down':
            nr += 1
        elif d == 'left':
            nc -= 1
        elif d == 'right':
            nc += 1

        if 0 <= nr < self.map_size and 0 <= nc < self.map_size:
            # Mark the previous tile as cleared if it's a common terrain (F or G)
            old_key = self.map_grid[old_r][old_c]
            if old_key in ['F', 'G']:
                self.cleared_map[old_r][old_c] = True

            self.player_pos = [nr, nc]
            self.draw_player()
            self.handle_encounter(nr, nc)
        else:
            self.status_text.set("You cannot move further in that direction!")

    def handle_encounter(self, r, c):
        """Triggers specific events based on the terrain."""
        key = self.map_grid[r][c]

        if key == 'K':
            messagebox.showinfo("VICTORY!", "You reached the King's Castle! You won the game.")
            self.game_over = True;
            self.on_closing()
        elif key == 'M':
            self.take_damage(2)
            self.status_text.set("Mountain path is rough. -2 Health.")
        elif key == 'T':
            self.start_dialogue()
        elif key == '?':
            self.trigger_mystery_event()
        elif key == 'E':
            self.trigger_riddle()
        elif key in ['F', 'G']:
            # Check if the tile has already been cleared
            if self.cleared_map[r][c]:
                self.status_text.set(f"Location: {self.terrains[key]['name']} - The area is quiet and safe.")
                return

                # If not cleared, check for battle chance
            if random.random() < self.BATTLE_CHANCE:
                self.initiate_battle()
            else:
                self.update_status()

    def trigger_riddle(self):
        """Starts a riddle encounter with the Elder."""
        self.in_dialogue = True
        riddle = random.choice(self.riddles)

        try:
            riddle_win = tk.Toplevel(self.master)
            riddle_win.title("👴 ELDER'S RIDDLE!")
            riddle_win.geometry("350x180")
            riddle_win.configure(bg="#34495e")
            riddle_win.resizable(False, False)
            riddle_win.attributes("-topmost", True)

            tk.Label(riddle_win, text="Old Man: 'Welcome, young traveler. Let's test your wits.'",
                     font=('Helvetica', 10, 'italic'), bg="#34495e", fg="#f1c40f", wraplength=300).pack(pady=5)
            tk.Label(riddle_win, text=riddle['question'], font=('Helvetica', 12, 'bold'), bg="#34495e", fg="white",
                     wraplength=300).pack(pady=5)

            answer_var = tk.StringVar()
            answer_entry = tk.Entry(riddle_win, textvariable=answer_var, font=('Helvetica', 10), width=30)
            answer_entry.pack(pady=5)
            answer_entry.focus_set()

            def submit_answer():
                player_answer = answer_var.get().strip().lower()
                correct_answer = riddle['answer'].lower()
                riddle_win.destroy()

                if player_answer == correct_answer:
                    reward_type = riddle['reward']['type']
                    reward_amount = riddle['reward']['amount']
                    self.apply_reward(reward_type, reward_amount)
                    messagebox.showinfo("Correct Answer!",
                                        f"Old Man: 'Your mind is sharp! Take your reward!'\nGain: {reward_amount} {reward_type}!")
                else:
                    messagebox.showerror("Wrong Answer",
                                         f"Old Man: 'Hmm, you couldn't guess it.'\nCorrect answer: **{riddle['answer']}**.")

                self.in_dialogue = False
                self.update_stats_display()
                self.update_status()

            tk.Button(riddle_win, text="Answer", command=submit_answer, bg="#27ae60", fg="white").pack(pady=10)

            riddle_win.protocol("WM_DELETE_WINDOW", lambda: [riddle_win.destroy(), setattr(self, 'in_dialogue', False),
                                                             self.update_status()])

        except Exception as e:
            self.in_dialogue = False
            messagebox.showerror("Error", f"An error occurred in the riddle event: {e}")
            self.update_status()

    def apply_reward(self, reward_type, amount):
        """Applies a given reward to the player's stats."""
        if reward_type == 'Health':
            self.player_stats['Health'] = min(self.player_stats['MaxHealth'], self.player_stats['Health'] + amount)
        elif reward_type == 'MaxHealth':
            self.player_stats['MaxHealth'] += amount
            self.player_stats['Health'] = min(self.player_stats['MaxHealth'], self.player_stats['Health'] + amount)
        elif reward_type == 'Gold':
            self.player_stats['Gold'] += amount
        elif reward_type == 'Attack':
            self.player_stats['Attack'] += amount

    def die(self):
        """Handles player death and ends the game."""
        messagebox.showerror("You Died", "Your adventure has ended.");
        self.game_over = True
        self.on_closing()

    def take_damage(self, amount):
        """Subtracts health and checks if the player is dead."""
        self.player_stats['Health'] -= amount
        self.update_stats_display()
        if self.player_stats['Health'] <= 0:
            self.die()

    def check_for_crit(self):
        """Checks if a critical hit occurs."""
        return random.random() < self.CRIT_CHANCE

    def trigger_mystery_event(self):
        """Triggers a random risk/reward event."""
        events = [
            {
                "text": "You found an ancient altar. It says 'Gain power with blood'.\nWould you sacrifice some Health for Attack power?",
                "cost_type": "health", "cost_val": 20, "reward_type": "attack", "reward_val": 5,
                "yes_msg": "You cut your hand. It hurts but you feel stronger! (-20 Health, +5 Attack)",
                "no_msg": "You decide not to risk it and walk away."},
            {"text": "A shining pouch is on the ground, but the area looks trapped.\nDo you try to grab it?",
             "cost_type": "chance_damage", "cost_val": 25, "reward_type": "gold", "reward_val": 50,
             "yes_msg": "Lucky! You grabbed the pouch.", "fail_msg": "The trap sprang! Arrows hit you. (-25 Health)",
             "no_msg": "You prioritize your health over quick riches."},
        ]

        event = random.choice(events)
        choice = messagebox.askyesno("Mystery Event", event["text"])

        if choice:
            if event["cost_type"] == "health":
                self.take_damage(event["cost_val"])
                self.player_stats['Attack'] += event["reward_val"]
                messagebox.showinfo("Result", event["yes_msg"])
            elif event["cost_type"] == "chance_damage":
                if random.random() > 0.55:
                    self.player_stats['Gold'] += event["reward_val"]
                    messagebox.showinfo("Success!", f"{event['yes_msg']} (+{event['reward_val']} Gold)")
                else:
                    self.take_damage(event["cost_val"])
                    messagebox.showerror("Failure!", event["fail_msg"])
        else:
            self.status_text.set(event["no_msg"])

        self.update_stats_display()

    def initiate_battle(self):
        """Starts a new battle encounter."""
        self.battle_window_open = True
        self.current_enemy = random.choice(self.enemy_gallery)
        lvl_mod_health = self.player_stats['Level'] * 4
        lvl_mod_attack = self.player_stats['Level'] * 1.5
        self.enemy_stats = {
            'Health': random.randint(30 + int(lvl_mod_health), 50 + int(lvl_mod_health)),
            'MaxHealth': 0,
            'Attack': random.randint(7 + int(lvl_mod_attack), 12 + int(lvl_mod_attack))
        }
        self.enemy_stats['MaxHealth'] = self.enemy_stats['Health']
        self.battle_win = tk.Toplevel(self.master)
        self.battle_win.title("⚔️ Battle!")
        self.battle_win.geometry("500x400")
        self.battle_win.configure(bg="#2c3e50")
        self.battle_win.protocol("WM_DELETE_WINDOW", self.close_battle_forced)
        top_frame = tk.Frame(self.battle_win, bg="#34495e", pady=10)
        top_frame.pack(fill='x')

        if self.player_photo:
            player_img_label = tk.Label(top_frame, image=self.player_photo, bg="#34495e")
            player_img_label.image = self.player_photo
            player_img_label.pack(side=tk.LEFT, padx=20)
        else:
            self.player_photo_canvas = tk.Canvas(top_frame, width=120, height=120, bg='#3498db', highlightthickness=2,
                                                 highlightbackground="white")
            self.player_photo_canvas.pack(side=tk.LEFT, padx=20)
            self.player_photo_canvas.create_text(60, 60, text=self.player_icon, font=('Arial', 30))

        self.player_battle_lbl = tk.Label(top_frame, text=f"You\nHealth: {self.player_stats['Health']}",
                                          font=('Arial', 12, 'bold'), bg="#34495e", fg="white")
        self.player_battle_lbl.pack(side=tk.LEFT)
        self.enemy_photo_canvas = tk.Canvas(top_frame, width=120, height=120, bg=self.current_enemy['color'],
                                            highlightthickness=2, highlightbackground="red")
        self.enemy_photo_canvas.pack(side=tk.RIGHT, padx=20)
        self.enemy_photo_canvas.create_text(60, 60, text=self.current_enemy['symbol'], font=('Arial', 30))
        self.enemy_battle_lbl = tk.Label(top_frame,
                                         text=f"{self.current_enemy['name']}\nHealth: {self.enemy_stats['Health']}",
                                         font=('Arial', 12, 'bold'), bg="#34495e", fg="red")
        self.enemy_battle_lbl.pack(side=tk.RIGHT)
        log_frame = tk.Frame(self.battle_win, bg="white", padx=5, pady=5)
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.battle_log = scrolledtext.ScrolledText(log_frame, height=10, state='disabled', font=('Courier', 10))
        self.battle_log.pack(fill='both', expand=True)
        self.log_message(f"A fierce {self.current_enemy['name']} appeared!")
        btn_frame = tk.Frame(self.battle_win, bg="#2c3e50", pady=10)
        btn_frame.pack(fill='x')
        atk_btn = tk.Button(btn_frame, text="⚔️ ATTACK", command=self.battle_round, bg="#c0392b", fg="white",
                            font=('Arial', 14, 'bold'), padx=20)
        atk_btn.pack()

    def log_message(self, msg):
        """Adds a message to the battle log."""
        self.battle_log.config(state='normal')
        self.battle_log.insert(tk.END, msg + "\n")
        self.battle_log.see(tk.END)
        self.battle_log.config(state='disabled')

    def battle_round(self):
        """Executes one round of combat (player attack, enemy attack, checks)."""
        if self.enemy_stats['Health'] <= 0:
            self.log_message("> The enemy is already defeated. Claim your victory!")
            return

        # Player Attack
        is_player_crit = self.check_for_crit()
        p_dmg = self.player_stats['Attack'] + random.randint(-3, 5)
        if is_player_crit:
            p_dmg = int(p_dmg * self.CRIT_MULTIPLIER)
            self.log_message(f"⭐ CRITICAL HIT! ⭐")

        self.enemy_stats['Health'] -= p_dmg
        self.log_message(f"> You dealt {p_dmg} damage to {self.current_enemy['name']}!")

        # Enemy Check (Defeat)
        if self.enemy_stats['Health'] <= 0:
            self.enemy_stats['Health'] = 0
            self.player_battle_lbl.config(text=f"You\nHealth: {self.player_stats['Health']}")
            self.enemy_battle_lbl.config(text=f"{self.current_enemy['name']}\nHealth: 0")
            self.log_message(f"--- {self.current_enemy['name']} DEFEATED! ---")

            gold = random.randint(10, 25) * self.player_stats['Level']
            xp = random.randint(30, 50)
            self.player_stats['Gold'] += gold
            self.log_message(f"Loot: {gold} Gold, {xp} XP.")
            self.gain_xp(xp)

            # Remove Attack button, add Exit button
            btn_frame = self.battle_win.winfo_children()[-1]
            for widget in btn_frame.winfo_children():
                widget.destroy()
            close_btn = tk.Button(btn_frame, text="Claim Victory and Exit", command=self.close_battle_win, bg="#27ae60",
                                  fg="white", font=('Arial', 12))
            close_btn.pack(pady=10)
            return

        # Enemy Attack
        is_enemy_crit = self.check_for_crit()
        e_dmg = self.enemy_stats['Attack'] + random.randint(-2, 3)
        if is_enemy_crit:
            e_dmg = int(e_dmg * self.CRIT_MULTIPLIER)
            self.log_message(f"💥 ENEMY CRITICAL HIT! 💥")

        self.player_stats['Health'] -= e_dmg
        self.log_message(f"> The enemy retaliated for {e_dmg} damage!")

        # Update Stats
        self.player_battle_lbl.config(text=f"You\nHealth: {self.player_stats['Health']}")
        self.enemy_battle_lbl.config(text=f"{self.current_enemy['name']}\nHealth: {self.enemy_stats['Health']}")
        self.update_stats_display()

        # Player Check (Defeat)
        if self.player_stats['Health'] <= 0:
            self.battle_win.destroy()
            self.die()

    def close_battle_win(self):
        """Closes the battle window normally after victory."""
        self.battle_window_open = False
        self.battle_win.destroy()
        self.update_status()

    def close_battle_forced(self):
        """Prevents closing the battle window while combat is ongoing."""
        if self.player_stats['Health'] > 0 and self.enemy_stats['Health'] > 0:
            messagebox.showwarning("Hold On!", "You cannot escape the battle! You must fight to the end.")
        else:
            self.close_battle_win()

    def start_dialogue(self):
        """Initiates the town/tavern dialogue."""
        if self.in_dialogue: return
        self.in_dialogue = True
        self.town_has_potion = random.choice([True, False])
        potion_price = 25
        d_text = "TAVERN KEEPER: 'Welcome, traveler. What do you need?'\n\n"
        d_text += "1) Rest (Free, Full Health)\n"
        if self.town_has_potion:
            d_text += f"2) Buy Potion ({potion_price} Gold)\n"
        else:
            d_text += "2) Buy Potion (SOLD OUT)\n"
        d_text += "3) Exit Town"
        self.status_text.set(d_text)

    def handle_dialogue_choice(self, c):
        """Handles the player's choice in town dialogue."""
        if not self.in_dialogue: return
        msg = ""
        potion_price = 25
        if c == 1:
            self.player_stats['Health'] = self.player_stats['MaxHealth'];
            msg = "Tavern Keeper: 'Sleep well.' (Health Restored)"
        elif c == 2:
            if not self.town_has_potion:
                msg = "Tavern Keeper: 'Sorry, the last caravan hasn't arrived.' (SOLD OUT)"
            elif self.player_stats['Gold'] >= potion_price:
                self.player_stats['Gold'] -= potion_price
                self.inventory['Health Potion'] += 1
                msg = "Tavern Keeper: 'Here is your potion.' (-25 Gold, +1 Potion)"
            else:
                msg = "Tavern Keeper: 'You don't have enough coin, friend.'"
        elif c == 3:
            msg = "Tavern Keeper: 'Safe travels!'"
        else:
            return
        self.in_dialogue = False
        messagebox.showinfo("Town Dialogue", msg)
        self.update_stats_display()
        self.update_inventory_display()
        self.update_status()

    def update_status(self):
        """Updates the status bar based on the player's current location."""
        if self.in_dialogue or self.battle_window_open: return
        r, c = self.player_pos
        t = self.terrains[self.map_grid[r][c]]
        self.status_text.set(f"Location: {t['name']} - {t['message']}")


if __name__ == '__main__':
    root = tk.Tk()
    game = RPGMapExplorer(root)
    root.focus_set()
    root.mainloop()