import os
import json
import random
import threading
import time
import socket
from itertools import cycle

pygame = None
screeninfo = None

def import_modules():
    global pygame, screeninfo
    try:
        # import pygame as pg
        import pygame.mixer
        import screeninfo as si
        # pygame = pg
        screeninfo = si
    except ImportError as e:
        print(f"Ошибка импорта модулей: {e}")

SUPPORTED_AUDIO_EXTENSIONS = ['.wav', '.mp3', '.ogg', '.flac']

def find_random_audio_file(directory):
    
    if not os.path.isdir(directory):
        return None
        
    audio_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() in SUPPORTED_AUDIO_EXTENSIONS:
                audio_files.append(os.path.join(root, file))
    
    return random.choice(audio_files) if audio_files else None

def load_config():
    config = {
        'hideDuration': 3,
        'position': 'bottom_left',
        'font_size': 14,
        'tick_sound': "off",
        'use_ticks_in': "timer",
        'tick_interval': "per minute",
        'alarm_sound': "C:\\Windows\\Media\\Alarm01.wav",
        'alarm_duration': 30,
        'enable_symbols': True,
        'font': 'Arial',
        'infinite_mode': False,
        'custom_pomodoro': "25 5 25 5 25 15",
        'custom_pomodoro_cycles': 3,
        'final_pomodoro_sound': "C:\\Windows\\Media\\tada.wav",
        'final_alarm_duration': 60
    }

    try:
        current_path = os.path.abspath(__file__)
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_path)))
        config_path = os.path.join(parent_dir, 'python', 'config.json')
        
        print(f"Ищем конфиг по пути: {config_path}")
        print(f"Конфиг существует: {os.path.exists(config_path)}")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                data = json.load(file)
                config.update(data)
                print("Загружена конфигурация:", config)
        else:
            print(f"Файл конфигурации не найден по пути: {config_path}")

            possible_paths = [
                os.path.join(os.path.dirname(current_path), 'config.json'),
                os.path.join(os.path.dirname(os.path.dirname(current_path)), 'config.json'),
                os.path.join(parent_dir, 'config.json')
            ]
            
            for fallback_path in possible_paths:
                print(f"Пробуем fallback путь: {fallback_path}")
                if os.path.exists(fallback_path):
                    with open(fallback_path, 'r') as file:
                        data = json.load(file)
                        config.update(data)
                        print(f"Загружена конфигурация из fallback: {fallback_path}")
                    break
                    
    except Exception as e:
        print(f"Ошибка чтения JSON файла: {e}")
    
    config['hideDuration'] = config['hideDuration']
    return config

def get_primary_monitor():
    try:
        if not screeninfo:
            import_modules()
        
        for monitor in screeninfo.get_monitors():
            if monitor.x == 0 and monitor.y == 0:
                return monitor
        return screeninfo.get_monitors()[0]
    except Exception as e:
        print(f"Ошибка получения информации о мониторе: {e}")

        class FallbackMonitor:
            def __init__(self):
                self.width = 1920
                self.height = 1080
        return FallbackMonitor()

def format_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes):02}:{int(seconds):02}"

def format_time_hms(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

def init_pygame():
    
    global pygame
    if not pygame:
        import_modules()
    try:
        pygame.mixer.init()
        return True
    except Exception as e:
        print(f"Ошибка инициализации pygame: {e}")
        return False

def load_sound(sound_path, volume=0.5):
    
    if not pygame:
        if not init_pygame():
            return None
    
    try:
        if os.path.isdir(sound_path):
            sound_path = find_random_audio_file(sound_path)
        
        if sound_path and os.path.isfile(sound_path):
            sound = pygame.mixer.Sound(sound_path)
            sound.set_volume(volume)
            return sound
    except Exception as e:
        print(f"Ошибка загрузки звука: {e}")
    
    return None


class WindowPositioner:
    @staticmethod
    def position_window(root, config, window_width, window_height, y_offset, additional_y_top, additional_side_offset):
        try:
            screen = get_primary_monitor()
            screen_width = screen.width
            screen_height = screen.height
            
            scale_factor = config['font_size'] / 14
            #  = 47
            top_offset = int(50 * scale_factor)
            side_offset = int(20 * scale_factor)
            
            root.update_idletasks()
            actual_width = root.winfo_reqwidth()
            actual_height = root.winfo_reqheight()
            
            window_width = max(window_width, actual_width)
            window_height = max(window_height, actual_height)
            
            x_offset_compensation = int((config['font_size'] - 14) * 9)
            y_offset_compensation = int((config['font_size'] - 14) * 1.5)
            additional_y_offset_bottom = int(y_offset * scale_factor)
            
            
            position = config['position']
            if position == 'top_left':
                x = side_offset - x_offset_compensation + additional_side_offset
                y = top_offset + y_offset_compensation + additional_y_top
            elif position == 'top_right':
                x = screen_width - window_width - side_offset + x_offset_compensation - additional_side_offset
                y = top_offset + y_offset_compensation + additional_y_top
            elif position == 'bottom_right':
                taskbar_height = 40
                x = screen_width - window_width - side_offset + x_offset_compensation - additional_side_offset
                y = screen_height - window_height - taskbar_height - side_offset + y_offset_compensation - additional_y_offset_bottom
            else:  # bottom_left
                taskbar_height = 40
                x = side_offset - x_offset_compensation + additional_side_offset
                y = screen_height - window_height - taskbar_height - side_offset + y_offset_compensation - additional_y_offset_bottom

            x = max(0, min(x, screen_width - window_width))
            y = max(0, min(y, screen_height - window_height))

            root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        except Exception as e:
            print(f"Ошибка позиционирования окна: {e}")




            
class SocketServer:
    def __init__(self, port, callback):
        self.port = port
        self.callback = callback
        self.server = None
    
    def start(self):
        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()
    
    def _run_server(self):
        HOST = "127.0.0.1"
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((HOST, self.port))
            self.server.listen(1)
            
            print(f"Socket server started on {HOST}:{self.port}")
            
            while True:
                try:
                    conn, addr = self.server.accept()
                    with conn:
                        data = conn.recv(1024).decode().strip()
                        if data and self.callback:
                            self.callback(data)
                except Exception as e:
                    print(f"Error in socket connection: {e}")
                    time.sleep(1)
                    
        except OSError as e:
            if e.errno == 10048:
                print(f"Port {self.port} is already in use.")
                try:
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.connect((HOST, self.port))
                    client.sendall(b"pausePomodoro")
                    client.close()
                    print("Command sent to existing instance")
                except Exception as client_error:
                    print(f"Failed to communicate with existing instance: {client_error}")
            else:
                print(f"Socket error: {e}")
        except Exception as e:
            print(f"Unexpected error in socket server: {e}")

# class WindowDragHandler:
#     def __init__(self, root):
#         self.root = root
#         self.offset_x = 0
#         self.offset_y = 0
#         self.setup_bindings()
    
#     def setup_bindings(self):
        
#         self.root.bind("<Button-1>", self.start_move)
#         self.root.bind("<B1-Motion>", self.do_move)
    
#     def start_move(self, event):
        
#         self.offset_x = event.x
#         self.offset_y = event.y
    
#     def do_move(self, event):
        
#         x = event.x_root - self.offset_x
#         y = event.y_root - self.offset_y
#         self.root.geometry(f"+{x}+{y}")

class SoundManager:
    def __init__(self, config):
        self.config = config
        self.sounds = {}
        self.sound_directories = {}
        self.init_pygame_async()
    
    def init_pygame_async(self):
        def init_in_thread():
            if init_pygame():
                self.load_sounds()
        threading.Thread(target=init_in_thread, daemon=True).start()
    
    def load_sounds(self):
        if self.config['use_ticks_in'] == "pomodoro" and self.config['tick_sound'] != "Select folder..." and self.config['tick_sound'] != "off":
            self.load_tick_sound()
    
        if self.config['alarm_sound'] != "off":
            self.load_alarm_sound()
        self.load_final_sound()

    def load_tick_sound(self):
        sound_path = self.config['tick_sound']
        if os.path.isdir(sound_path):
            self.sound_directories['tick_sound'] = sound_path
            sound_path = find_random_audio_file(sound_path)
        
        if sound_path:
            self.sounds['tick_sound'] = load_sound(sound_path, 0.3)
    
    def load_alarm_sound(self):
        sound_path = self.config['alarm_sound']
        if sound_path == "Select folder...":
            sound_path = "C:\\Windows\\Media\\Alarm01.wav"
        
        if os.path.isdir(sound_path):
            self.sound_directories['alarm_sound'] = sound_path
        
        self.sounds['alarm_sound'] = load_sound(sound_path, 0.5)
    
    def load_final_sound(self):
        sound_path = self.config.get('final_pomodoro_sound', "C:\\Windows\\Media\\Alarm01.wav")
        if os.path.isdir(sound_path):
            self.sound_directories['final_alarm_sound'] = sound_path
        
        self.sounds['final_alarm_sound'] = load_sound(sound_path, 0.5)
    
    def play_tick(self):
        if 'tick_sound' in self.sounds and self.sounds['tick_sound']:
            try:
                self.sounds['tick_sound'].play()
            except Exception as e:
                print(f"Ошибка воспроизведения тика: {e}")
    
    def play_with_fade_out(self, sound_type, duration):
        try:
            duration = int(duration)
            if duration <= 0:
                print("Alarm duration is set to 0 or negative, not playing sound")
                return
        except (ValueError, TypeError):
            print("Invalid alarm duration value, not playing sound")
            return
    
        actual_sound = None
        
        if sound_type in self.sound_directories:
            random_file = find_random_audio_file(self.sound_directories[sound_type])
            if random_file:
                actual_sound = load_sound(random_file, 0.5)
        elif sound_type in self.sounds:
            actual_sound = self.sounds[sound_type]
        
        if not actual_sound:
            print(f"Звук {sound_type} не найден")
            return

        actual_sound.play()
        
        fade_start_time = time.time() + (duration - 5)
        fade_end_time = fade_start_time + 5
        
        def fade_out_sound():
            current_time = time.time()
            if current_time < fade_start_time:
                threading.Timer(0.1, fade_out_sound).start()
                return
            if current_time < fade_end_time:
                remaining_fade_time = fade_end_time - current_time
                volume = remaining_fade_time / 5.0
                volume = max(0.0, min(volume * 0.5, 0.5))
                actual_sound.set_volume(volume)
                threading.Timer(0.1, fade_out_sound).start()
            else:
                actual_sound.stop()
                actual_sound.set_volume(0.5)
        
        threading.Timer(0.1, fade_out_sound).start()

class LightningAnimator:
    def __init__(self, left_lightning, right_lightning, config):
        self.left_lightning = left_lightning
        self.right_lightning = right_lightning
        self.config = config
        self.lightning_colors = cycle(["#FF6F00", "#FFB300", "#FF6F00"])
        self.running = False
    
    def start_animation(self, root):
        self.running = True
        self._animate(root)
    
    def stop_animation(self):
        self.running = False
        if self.config.get('enable_symbols', True):
            self.left_lightning.config(fg="#666666")
            self.right_lightning.config(fg="#666666")
    
    def _animate(self, root):
        if self.running and self.config.get('enable_symbols', True):
            next_color = next(self.lightning_colors)
            self.left_lightning.config(fg=next_color)
            self.right_lightning.config(fg=next_color)
            root.after(500, lambda: self._animate(root))
        elif not self.running and self.config.get('enable_symbols', True):
            self.left_lightning.config(fg="#666666")
            self.right_lightning.config(fg="#666666")


class StateManager:
    @staticmethod
    def save_stopwatch_state(start_time, elapsed_time, running):

        temp_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '\\temp\\stopwatch_state.txt'
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        with open(temp_path, 'w') as file:
            file.write(f"{start_time},{elapsed_time},{running}")
    
    @staticmethod
    def load_stopwatch_state():

        temp_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '\\temp\\stopwatch_state.txt'
        if os.path.exists(temp_path):
            with open(temp_path, 'r') as file:
                data = file.read().split(",")
                start_time = float(data[0]) if data[0] != "None" else None
                elapsed_time = float(data[1])
                running = data[2] == "True"
                return start_time, elapsed_time, running
        return None, 0, False
