import tkinter as tk
import time
import threading
from sys import argv
from common import (
    import_modules, load_config, format_time_hms,
    init_pygame, load_sound, WindowPositioner,
    SocketServer, StateManager, LightningAnimator
)

import_thread = threading.Thread(target=import_modules, daemon=True)
import_thread.start()

class StopwatchApp:
    def __init__(self, root):
        self.root = root
        self.root.attributes("-topmost", True)
        self.root.title("Stopwatch")
        
        self.config = load_config()
        self.font_size = self.config['font_size']
        
        scale_factor = self.font_size / 14
        self.window_width = int(500 * scale_factor)
        self.window_height = int(1 * scale_factor)
        
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.configure(bg="#121212")

        # make_window_clickthrough(self.root)

        # self.drag_handler = WindowDragHandler(self.root)

        self.running = False
        self.start_time = None
        self.elapsed_time = 0
        self.last_minute = None
        
        self.tick_sound = None
        self.tick_sound_path = None

        self._create_ui(scale_factor)
        
        self.lightning_animator = LightningAnimator(
            self.left_lightning, self.right_lightning, self.config
        )

        self.load_state()

        if self.elapsed_time == 0 or self.start_time is None or argv[-1] == 'reset' or len(argv)==1:
            self.reset()
            self.start()

        self.root.bind("<Enter>", self.hide_stopwatch)
        self.root.bind("<Leave>", self.show_stopwatch)

        self.root.overrideredirect(True)
        self.root.attributes("-transparentcolor", "#121212")

        self.root.after(100, self.delayed_initialization)

    def _create_ui(self, scale_factor):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        main_frame = tk.Frame(self.root, bg="#121212")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        time_frame = tk.Frame(main_frame, bg="#121212")
        time_frame.grid(row=0, column=0, pady=int(20 * scale_factor))
        time_frame.grid_columnconfigure(0, weight=1)
        time_frame.grid_columnconfigure(1, weight=1)
        time_frame.grid_columnconfigure(2, weight=1)

        lightning_font_size = int(30 * scale_factor)
        time_font_size = int(60 * scale_factor)

        self.left_lightning = tk.Label(
            time_frame,
            text="\u26A1",
            font=("Arial", lightning_font_size),
            bg="#121212",
            fg="#666666"
        )
        if self.config.get('enable_symbols', True):
            self.left_lightning.grid(row=0, column=0, padx=int(10 * scale_factor))

        self.time_display = tk.Label(
            time_frame,
            text="00:00:00",
            font=(self.config.get('font', 'Arial'), time_font_size),
            bg="#121212",
            fg="#f0f0f0"
        )
        self.time_display.grid(row=0, column=1)

        self.right_lightning = tk.Label(
            time_frame,
            text="\u26A1",
            font=("Arial", lightning_font_size),
            bg="#121212",
            fg="#666666"
        )
        if self.config.get('enable_symbols', True):
            self.right_lightning.grid(row=0, column=2, padx=int(10 * scale_factor))

    def delayed_initialization(self):
        import_thread.join()

        pygame_thread = threading.Thread(target=self.init_pygame, daemon=True)
        pygame_thread.start()
        
        WindowPositioner.position_window(
            self.root, self.config, self.window_width, self.window_height, 0, 240, 47
        )
        # WindowPositioner.position_stopwatch_window(
        #     self.root, self.config, self.window_width, self.window_height
        # )

    def init_pygame(self):
        try:
            if init_pygame():
                self.root.after(100, self.init_sounds)
        except Exception as e:
            print(f"Ошибка инициализации pygame: {e}")

    def init_sounds(self):
        try:
            if (self.config['use_ticks_in'] == "stopwatch" and 
                self.config['tick_sound'] != "Select folder..." and 
                self.config['tick_sound'] != "off"):
                
                self.tick_sound = load_sound(self.config['tick_sound'], 0.3)
                if self.tick_sound:
                    print(f"Загружен звук тиков")
                else:
                    print("Тики отключены или не настроены для секундомера")
        except Exception as e:
            print(f"Ошибка в init_sounds: {e}")

    def update_time(self):
        if self.running:
            current_time = time.time()
            self.elapsed_time = current_time - self.start_time
            formatted_time = format_time_hms(self.elapsed_time)
            self.time_display.config(text=formatted_time)

            current_minute = int(self.elapsed_time // 60)
            
            if self.tick_sound and self.config['use_ticks_in'] == "stopwatch":
                try:
                    if self.config['tick_interval'] == "per second":
                        self.tick_sound.play()
                    elif (self.config['tick_interval'] == "per minute" and 
                          (self.last_minute is None or current_minute != self.last_minute)):
                        self.tick_sound.play()
                except Exception as e:
                    print(f"Ошибка воспроизведения тика: {e}")
            
            self.last_minute = current_minute
            self.root.after(1000, self.update_time)

    def hide_stopwatch(self, event):
        self.time_display.grid_remove()
        self.left_lightning.grid_remove()
        self.right_lightning.grid_remove()

    def show_stopwatch(self, event):
        def display_elements():
            scale_factor = self.font_size / 14
            if self.config.get('enable_symbols', True):
                self.left_lightning.grid(row=0, column=0, padx=int(10 * scale_factor))
                self.right_lightning.grid(row=0, column=2, padx=int(10 * scale_factor))
            self.time_display.grid(row=0, column=1)
            
        self.root.after(self.config['hideDuration'], display_elements)

    def start(self):
        if not self.running:
            self.running = True
            self.start_time = time.time() - self.elapsed_time
            self.update_time()
            self.lightning_animator.start_animation(self.root)
            self.save_state()

    def toggle(self):
        if self.running:
            self.running = False
            self.lightning_animator.stop_animation()
            self.save_state()
        else:
            self.running = True
            self.start_time = time.time() - self.elapsed_time
            self.update_time()
            self.lightning_animator.start_animation(self.root)
            self.save_state()
        
    def reset(self):
        self.running = False
        self.start_time = None
        self.elapsed_time = 0
        self.last_minute = None
        self.time_display.config(text="00:00:00")
        self.lightning_animator.stop_animation()
        self.save_state()

    def save_state(self):
        StateManager.save_stopwatch_state(self.start_time, self.elapsed_time, self.running)

    def load_state(self):
        start_time, elapsed_time, running = StateManager.load_stopwatch_state()
        self.start_time = start_time
        self.elapsed_time = elapsed_time
        self.running = running
        
        if self.elapsed_time > 0:
            self.last_minute = int(self.elapsed_time // 60)
        
        if self.running:
            self.update_time()
            self.lightning_animator.start_animation(self.root)

    def handle_socket_command(self, command):
        if command == "pauseStopwatch":
            print("Получена команда паузы")
            self.toggle()

def startMain():
    root = tk.Tk()
    global app
    app = StopwatchApp(root)

    socket_server = SocketServer(65433, app.handle_socket_command)
    root.after(100, socket_server.start)
    
    root.mainloop()

if __name__ == "__main__":
    startMain()