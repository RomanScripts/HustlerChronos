import tkinter as tk
from itertools import cycle
from sys import argv

from common import (
    load_config,
    format_time, WindowPositioner, SocketServer,
    SoundManager
)

config = load_config()

if len(argv) > 1:
    if argv[1] == "custom":
        POMODORO_SEQUENCE = [int(x) for x in config['custom_pomodoro'].split()]
        INFINITE_MODE = bool(config['infinite_mode'])
        POMODORO_CYCLES = config['custom_pomodoro_cycles']
    else:
        newList = argv.copy()
        newList = newList[2:]   
        POMODORO_SEQUENCE = [int(item) for item in newList]
        INFINITE_MODE = bool(int(argv[1]))
        print(bool(int(argv[1])), "   ", argv[1])
else:
    POMODORO_SEQUENCE = [1,1,1]
    INFINITE_MODE = bool(config['infinite_mode'])
    POMODORO_CYCLES = 3

if INFINITE_MODE:
    POMODORO_CYCLES = 0
else:
    if 'POMODORO_CYCLES' not in globals():
        POMODORO_CYCLES = 3
        print("POMODORO_CYCLES not in globals")

DISPLAY_CYCLES_AS_BARS = False

class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.root.attributes("-topmost", True)
        self.root.title("Pomodoro Timer")
        
        self.config = config
        self.font_size = self.config['font_size']
        
        scale_factor = self.font_size / 14
        self.window_width = int(500 * scale_factor)
        self.window_height = int(1 * scale_factor)
        
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.configure(bg="#121212")
        
        self.root.overrideredirect(True)
        self.root.attributes("-transparentcolor", "#121212")
        
        # make_window_clickthrough(self.root)
        # self.drag_handler = WindowDragHandler(self.root)
        
        self.sequence = cycle(POMODORO_SEQUENCE)
        self.current_interval = iter(POMODORO_SEQUENCE)
        self.remaining_time = next(self.current_interval) * 60
        self.is_working = True
        self.running = False
        self.paused = False
        self.cycle_count = POMODORO_CYCLES
        self.last_minute = self.remaining_time // 60
        
        self.sound_manager = SoundManager(self.config)
        
        self.work_cycle = cycle(["#FF3333", "#FF6666"])
        self.rest_cycle = cycle(["#FFA500", "#FFCC66"])
        self.cycle_symbols = {True: "🔴", False: "☀"}
        
        main_frame = tk.Frame(root, bg="#121212")
        main_frame.pack(fill="both", expand=True)
        
        self.cycle_counter_frame = tk.Frame(main_frame, bg="#121212")
        self.cycle_counter_frame.pack(pady=int(10 * scale_factor))

        self.cycle_counter_label = tk.Label(
            self.cycle_counter_frame, 
            text=self.get_cycle_display(),
            font=(self.config['font'], int(20 * scale_factor)), 
            bg="#121212", 
            fg="#FFFFFF"
        )
        self.cycle_counter_label.pack()

        self.time_frame = tk.Frame(main_frame, bg="#121212")
        self.time_frame.pack(pady=int(10 * scale_factor))

        self.left_symbol = tk.Label(
            self.time_frame, 
            text=self.cycle_symbols[self.is_working],
            font=("Arial", int(30 * scale_factor)), 
            bg="#121212", 
            fg="#FF3333"
        )
        if self.config.get('enable_symbols', False):
            self.left_symbol.pack(side="left", padx=int(10 * scale_factor))

        self.time_display = tk.Label(
            self.time_frame, 
            text=format_time(self.remaining_time),
            font=(self.config['font'], int(60 * scale_factor)), 
            bg="#121212", 
            fg="#FFFFFF"
        )
        self.time_display.pack(side="left")

        self.right_symbol = tk.Label(
            self.time_frame, 
            text=self.cycle_symbols[self.is_working],
            font=("Arial", int(30 * scale_factor)), 
            bg="#121212", 
            fg="#FF3333"
        )
        if self.config.get('enable_symbols', False):
            self.right_symbol.pack(side="left", padx=int(10 * scale_factor))
        
        self.root.bind("<Enter>", self.hide_timer)
        self.root.bind("<Leave>", self.show_timer)
        
        self.root.after(100, self.delayed_initialization)
        self.start()

    def delayed_initialization(self):
        WindowPositioner.position_window(
            self.root, self.config, self.window_width, self.window_height, 190, 8, 47
        )


    def get_cycle_display(self):
        if INFINITE_MODE:
            return str(self.cycle_count)
        else:
            return "|" * self.cycle_count if DISPLAY_CYCLES_AS_BARS else str(self.cycle_count)

    def toggle_pause(self):
        if self.paused:
            self.paused = False
            self.running = True
            self.update_time()
        else:
            self.paused = True
            self.running = False
            self.update_icon_color()
            if hasattr(self, "timer_id"):
                self.root.after_cancel(self.timer_id)

    def update_time(self):
        if not self.running or self.paused or self.remaining_time <= 0:
            return

        self.remaining_time -= 1
        self.time_display.config(text=format_time(self.remaining_time))
        self.update_icon_color()
        
        current_minute = self.remaining_time // 60
        
        if self.config['use_ticks_in'] == "pomodoro" and self.config['alarm_sound'] != "off":
            try:
                if self.config['tick_interval'] == "per second":
                    self.sound_manager.play_tick()
                elif self.config['tick_interval'] == "per minute" and current_minute != self.last_minute:
                    self.sound_manager.play_tick()
            except Exception as e:
                print(f"Ошибка воспроизведения тика: {e}")
        
        self.last_minute = current_minute

        if self.remaining_time > 0:
            self.timer_id = self.root.after(1000, self.update_time)
        else:
            self.end_period()

    def update_icon_color(self):
        if self.paused:
            gray_color = "#666666"
            self.left_symbol.config(fg=gray_color)
            self.right_symbol.config(fg=gray_color)
        else:
            next_color = next(self.work_cycle if self.is_working else self.rest_cycle)
            self.left_symbol.config(fg=next_color)
            self.right_symbol.config(fg=next_color)

    def start(self):
        if not self.running:
            self.running = True
            self.update_time()

    def end_period(self):
        if self.is_working:
            if INFINITE_MODE:
                self.cycle_count += 1
            else:
                self.cycle_count -= 1

            self.update_cycle_counter()

        if not INFINITE_MODE and self.cycle_count == 0 and self.is_working:
            try:
                final_alarm_duration = self.config.get('final_alarm_duration', 60)
                self.sound_manager.play_with_fade_out('final_alarm_sound', final_alarm_duration)
            except Exception as e:
                print(f"Ошибка воспроизведения финального звука: {e}")
                
            self.time_display.config(text="00:00")
            
            if self.config.get('enable_symbols', False):
                self.left_symbol.config(text="🎉", fg="#FFD700")
                self.right_symbol.config(text="🎉", fg="#FFD700")
            self.running = False
            return

        try:
            alarm_duration = self.config.get('alarm_duration', 30)
            self.sound_manager.play_with_fade_out('alarm_sound', alarm_duration)
        except Exception as e:
            print(f"Ошибка воспроизведения звука будильника: {e}")
            
        self.is_working = not self.is_working
        
        if self.config.get('enable_symbols', False):
            symbol = self.cycle_symbols[self.is_working]
            self.left_symbol.config(text=symbol)
            self.right_symbol.config(text=symbol)

        try:
            self.remaining_time = next(self.current_interval) * 60
        except StopIteration:
            self.current_interval = iter(POMODORO_SEQUENCE)
            self.remaining_time = next(self.current_interval) * 60
        
        self.time_display.config(text=format_time(self.remaining_time))
        
        if self.running:
            self.timer_id = self.root.after(1000, self.update_time)

    def update_cycle_counter(self):
        self.cycle_counter_label.config(text=self.get_cycle_display())

    def skip_rest_period(self):
        if not self.is_working:
            if hasattr(self, "timer_id"):
                self.root.after_cancel(self.timer_id)
                del self.timer_id
            
            self.is_working = True
            
            if self.config.get('enable_symbols', False):
                symbol = self.cycle_symbols[self.is_working]
                self.left_symbol.config(text=symbol)
                self.right_symbol.config(text=symbol)
            
            try:
                self.remaining_time = next(self.current_interval) * 60
            except StopIteration:
                self.current_interval = iter(POMODORO_SEQUENCE)
                self.remaining_time = next(self.current_interval) * 60
            
            self.time_display.config(text=format_time(self.remaining_time))
            
            if self.running:
                self.timer_id = self.root.after(1000, self.update_time)

    def hide_timer(self, event):
        self.root.attributes("-alpha", 0)

    def show_timer(self, event):
        self.root.after(self.config['hideDuration'], lambda: self.root.attributes("-alpha", 1))

def handle_socket_command(command):
    if command == "pausePomodoro":
        print("Получена команда паузы")
        app.toggle_pause()
    elif command == "skipRest":
        print("Получена команда пропуска отдыха")
        app.skip_rest_period()

def startMain():
    root = tk.Tk()
    global app
    app = PomodoroTimer(root)
    
    socket_server = SocketServer(65432, handle_socket_command)
    socket_server.start()
    
    root.mainloop()

if __name__ == "__main__":
    startMain()