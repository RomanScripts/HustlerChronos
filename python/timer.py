import tkinter as tk
from sys import argv
from itertools import cycle
import threading

from common import (
    load_config, format_time, 
    WindowPositioner, SocketServer,
    load_sound, import_modules
)

TIMER_MINUTES = int(argv[1]) if len(argv) > 1 else 1
DEFAULT_ALARM_SOUND_PATH = "C:\\Windows\\Media\\Alarm01.wav"
ALARM_VOLUME = 0.5

class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.attributes("-topmost", True)
        self.root.title("Timer")
        
        self.config = load_config()
        self.font_size = self.config['font_size']
        
        scale_factor = self.font_size / 14
        self.window_width = int(500 * scale_factor)
        self.window_height = int(1 * scale_factor)
        
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.configure(bg="#121212")

        # make_window_clickthrough(self.root)
        self._setup_move_handlers()
        self._init_timer_state()
        self._setup_ui()
        self._setup_hide_show_handlers()
        
        self.root.overrideredirect(True)
        self.root.attributes("-transparentcolor", "#121212")
        
        self.root.after(100, self.delayed_initialization)

    def _setup_move_handlers(self):
        self.offset_x = 0    
        self.offset_y = 0
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.do_move)

    def _init_timer_state(self):
        self.running = False
        self.remaining_time = TIMER_MINUTES * 60
        self.timer_completed = False
        self.last_minute = self.remaining_time // 60
        self.tick_sound = None
        self.alarm_sound = None

    def _setup_ui(self):
        scale_factor = self.font_size / 14
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        main_frame = tk.Frame(self.root, bg="#121212")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        time_frame = tk.Frame(main_frame, bg="#121212")
        time_frame.grid(row=0, column=0, pady=int(20 * scale_factor))
        
        for i in range(3):
            time_frame.grid_columnconfigure(i, weight=1)

        self.hourglass_colors = cycle(["#FF3333", "#FF6666"])
        hourglass_font_size = int(30 * scale_factor)
        time_font_size = int(60 * scale_factor)

        self.left_hourglass = tk.Label(
            time_frame, text="🔥", font=("Arial", hourglass_font_size),
            bg="#121212", fg="#FF3333"
        )
        
        self.time_display = tk.Label(
            time_frame, text=format_time(self.remaining_time),
            font=(self.config.get("font", "Arial"), time_font_size),
            bg="#121212", fg="#f0f0f0"
        )
        
        self.right_hourglass = tk.Label(
            time_frame, text="🔥", font=("Arial", hourglass_font_size),
            bg="#121212", fg="#FF3333"
        )

        if self.config.get('enable_symbols', True):
            self.left_hourglass.grid(row=0, column=0, padx=int(10 * scale_factor))
            self.right_hourglass.grid(row=0, column=2, padx=int(10 * scale_factor))
        
        self.time_display.grid(row=0, column=1)

        self.animate_hourglass()
        self.reset()
        self.start()

    def _setup_hide_show_handlers(self):
        self.root.bind("<Enter>", self.hide_timer)
        self.root.bind("<Leave>", self.show_timer)

    def delayed_initialization(self):
        import_thread = threading.Thread(target=import_modules, daemon=True)
        import_thread.start()
        
        pygame_thread = threading.Thread(target=self.init_sounds, daemon=True)
        pygame_thread.start()
        
        WindowPositioner.position_window(
            self.root, self.config, self.window_width, self.window_height, 90, 150, 47
        )

    def init_sounds(self):
        if (self.config['use_ticks_in'] == "timer" and 
            self.config['tick_sound'] not in ["Select folder...", "off"]):
            self.tick_sound = load_sound(self.config['tick_sound'], 0.3)

        if self.config['alarm_sound'] != "off":
            sound_path = (DEFAULT_ALARM_SOUND_PATH 
                         if self.config['alarm_sound'] == "Select folder..." 
                         else self.config['alarm_sound'])
            self.alarm_sound = load_sound(sound_path, ALARM_VOLUME)

    def start_move(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def do_move(self, event):
        x = event.x_root - self.offset_x
        y = event.y_root - self.offset_y
        self.root.geometry(f"+{x}+{y}")

    def animate_hourglass(self):
        if self.running and self.config.get('enable_symbols', True):
            next_color = next(self.hourglass_colors)
            self.left_hourglass.config(fg=next_color)
            self.right_hourglass.config(fg=next_color)
            self.root.after(500, self.animate_hourglass)
        elif self.timer_completed and self.config.get('enable_symbols', True):
            self.left_hourglass.config(fg="#00FF00")
            self.right_hourglass.config(fg="#00FF00")
        elif not self.running and self.config.get('enable_symbols', True):
            self.left_hourglass.config(fg="#666666")
            self.right_hourglass.config(fg="#666666")

    def update_time(self):
        if self.running and self.remaining_time > 0:
            self.remaining_time -= 1
            self.time_display.config(text=format_time(self.remaining_time))

            self._handle_tick_sound()
            
            if self.remaining_time <= 0:
                self.end_timer()
            else:
                self.root.after(1000, self.update_time)

    def _handle_tick_sound(self):
        if not self.tick_sound or self.config['use_ticks_in'] != "timer":
            return
            
        current_minute = self.remaining_time // 60
        
        try:
            if (self.config['tick_interval'] == "per second" or
                (self.config['tick_interval'] == "per minute" and 
                 current_minute != self.last_minute)):
                self.tick_sound.play()
        except Exception as e:
            print(f"Ошибка воспроизведения тика: {e}")
        
        self.last_minute = current_minute

    def hide_timer(self, event):
        self.time_display.grid_remove()
        if self.config.get('enable_symbols', True):
            self.left_hourglass.grid_remove()
            self.right_hourglass.grid_remove()

    def show_timer(self, event):
        scale_factor = self.font_size / 14
        self.root.after(self.config['hideDuration'], lambda: [
            self.left_hourglass.grid(row=0, column=0, padx=int(10 * scale_factor)),
            self.time_display.grid(row=0, column=1),
            self.right_hourglass.grid(row=0, column=2, padx=int(10 * scale_factor))
        ])

    def start(self):
        if not self.running and self.remaining_time > 0:
            self.running = True
            self.timer_completed = False
            self.update_time()
            self.animate_hourglass()

    def toggle(self):
        if self.running:
            self.running = False
        elif self.remaining_time > 0:
            self.running = True
            self.timer_completed = False
            self.update_time()
            self.animate_hourglass()

    def reset(self):
        self.running = False
        self.timer_completed = False
        self.remaining_time = TIMER_MINUTES * 60
        self.time_display.config(text=format_time(self.remaining_time))
        self.left_hourglass.config(fg="#FF3333")
        self.right_hourglass.config(fg="#FF3333")

    def end_timer(self):
        self.running = False
        self.timer_completed = True
        self.left_hourglass.config(fg="#00FF00")
        self.right_hourglass.config(fg="#00FF00")
        
        if self.alarm_sound:
            try:
                alarm_duration = int(self.config.get('alarm_duration', 0))
                if alarm_duration > 0:
                    self.alarm_sound.play()
                    self.root.after(alarm_duration * 1000, self.start_fade_out)
            except Exception as e:
                print(f"Ошибка воспроизведения будильника: {e}")

    def start_fade_out(self):
        try:
            self.current_volume = ALARM_VOLUME
            self.fade_step = self.current_volume / 50
            self.fade_out_step()
        except Exception as e:
            print(f"Ошибка затухания: {e}")
            if self.alarm_sound:
                self.alarm_sound.stop()

    def fade_out_step(self):
        try:
            if self.current_volume > 0 and self.alarm_sound:
                self.current_volume -= self.fade_step
                if self.current_volume < 0:
                    self.current_volume = 0
                    
                self.alarm_sound.set_volume(self.current_volume)
                
                if self.current_volume > 0:
                    self.root.after(100, self.fade_out_step)
                else:
                    self.alarm_sound.stop()
            else:
                if self.alarm_sound:
                    self.alarm_sound.stop()
        except Exception as e:
            print(f"Ошибка в процессе затухания: {e}")
            if self.alarm_sound:
                self.alarm_sound.stop()

def handle_socket_command(command):
    if command == "pauseTimer":
        print("Получена команда паузы")
        app.toggle()

def startMain():
    root = tk.Tk()
    global app
    app = TimerApp(root)
    
    socket_server = SocketServer(65434, handle_socket_command)
    root.after(100, socket_server.start)
    
    root.mainloop()

if __name__ == "__main__":
    startMain()