import tkinter as tk
from tkinter import ttk, filedialog
import tkinter.font as tkfont
import json
import os
import psutil
import subprocess
import glob
import sys
from common import load_config
# from tkinter.tooltip import Hovertip

# Пути к директориям и файлам
current_dir_path = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir_path)
grandparent_dir = os.path.dirname(parent_dir)  # Поднимаемся еще на уровень выше
stopwatchPY = os.path.join(parent_dir, "python", "stopwatch.py")
timerPY = os.path.join(parent_dir, "python", "timer.py")
pomodoroPY = os.path.join(parent_dir, "python", "pomodoro.py")
sounds_dir = os.path.join(grandparent_dir, "sounds")
ticks_dir = os.path.join(grandparent_dir, "sounds\\ticks")
alarm_sounds_dir = os.path.join(grandparent_dir, "sounds\\alarm")

icon_path = os.path.join(grandparent_dir, "icons\\settingsIcon.ico")

# Пути к файлам с PID
stopwatchPIDfile = os.path.join(grandparent_dir, "temp", "stopwatchPID.txt")
pomodoroPIDfile = os.path.join(grandparent_dir, "temp", "pomodoroPID.txt")
timerPIDfile = os.path.join(grandparent_dir, "temp", "timerPID.txt")



# Файл конфигурации
CONFIG_FILE = os.path.join(grandparent_dir, "python", "config.json")


class SettingsApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Options")

        # Альтернативный способ для Windows 10
        try:
            # Конвертируем ICO в PhotoImage для tkinter
            from PIL import Image, ImageTk
            
            # Загружаем иконку
            icon_image = Image.open(icon_path)
            icon_photo = ImageTk.PhotoImage(icon_image)
            
            # Устанавливаем иконку
            self.root.iconphoto(True, icon_photo)
            
            # Сохраняем ссылку на изображение
            self.icon_photo = icon_photo
            
            # Дополнительно для панели задач
            if sys.platform.startswith('win'):
                import ctypes
                myappid = 'SettingsApp.YourApp.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                
        except ImportError:
            print("PIL не установлен, используем стандартный метод")
            try:
                self.root.iconbitmap(icon_path)
            except:
                pass
        except Exception as e:
            print(f"Ошибка установки иконки: {e}")

        # Размер окна
        self.root.geometry("380x730")
        # Минимальный размер окна
        self.root.minsize(380, 730)
        
        # Устанавливаем светло-серый фон для всего приложения
        bg_color = "#f0f0f0"
        self.root.configure(bg=bg_color)
        
        # Загружаем конфигурацию
        self.cfg = load_config()
        
        # Инициализируем пустые списки для звуковых файлов
        self.tick_sound_files = []
        self.alarm_sound_files = []
        
        # Получаем списки доступных звуковых файлов
        self.get_sound_files()
        
        # Создаем основную рамку
        main_frame = tk.Frame(root, bg=bg_color, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        
        # Создаем и размещаем все элементы управления
        self.create_widgets(main_frame)

        self._updating = False

    def show_full_path_tooltip(self, combo, sound_var):
        """Показать всплывающую подсказку с полным путем при наведении на комбобокс с задержкой"""
        from tkinter import Toplevel
        
        tooltip = None
        timer = None
        
        def show_tooltip(event):
            nonlocal tooltip
            value = sound_var.get()
            if value and value != "off" and len(value) > 30:  # Показываем только для длинных путей
                tooltip = Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                label = tk.Label(tooltip, text=value, 
                            background="#ffffe0", 
                            relief="solid", 
                            borderwidth=1,
                            font=("Arial", 9))
                label.pack()
        
        def enter(event):
            nonlocal timer
            # Отменяем предыдущий таймер, если он есть
            if timer:
                combo.after_cancel(timer)
            # Запускаем новый таймер на 1 секунду
            timer = combo.after(1000, lambda: show_tooltip(event))
        
        def leave(event):
            nonlocal tooltip, timer
            # Отменяем таймер, если он активен
            if timer:
                combo.after_cancel(timer)
                timer = None
            # Удаляем подсказку, если она отображается
            if tooltip:
                tooltip.destroy()
                tooltip = None
        
        def motion(event):
            nonlocal timer
            # При движении мыши сбрасываем таймер
            if timer:
                combo.after_cancel(timer)
                timer = combo.after(1000, lambda: show_tooltip(event))
        
        combo.bind("<Enter>", enter)
        combo.bind("<Leave>", leave)
        combo.bind("<Motion>", motion)
    
    def get_sound_files(self):
        """Получаем списки звуковых файлов из разных папок"""
        # Создаем папки, если они не существуют
        if not os.path.exists(sounds_dir):
            os.makedirs(sounds_dir)
        if not os.path.exists(ticks_dir):
            os.makedirs(ticks_dir)
        if not os.path.exists(alarm_sounds_dir):
            os.makedirs(alarm_sounds_dir)
        
        sound_extensions = ['.mp3', '.wav', '.ogg']
        
        # Списки для разных типов звуков
        self.tick_sound_files = []
        self.alarm_sound_files = []
        
        # Встроенные системные звуки Windows для будильников
        windows_sounds = [
            "C:\\Windows\\Media\\Alarm01.wav",
            "C:\\Windows\\Media\\tada.wav"
        ]
        
        # Добавляем системные звуки в список звуков будильника
        for sound in windows_sounds:
            if os.path.exists(sound):
                self.alarm_sound_files.append(sound)
        
        # Добавляем звуки из папки ticks для тиканья
        for ext in sound_extensions:
            files = glob.glob(os.path.join(ticks_dir, f"*{ext}"))
            for file in files:
                # Преобразуем путь к Windows-стилю
                file = file.replace('/', '\\')
                self.tick_sound_files.append(file)
        
        # Добавляем звуки из папки alarm для будильников
        for ext in sound_extensions:
            files = glob.glob(os.path.join(alarm_sounds_dir, f"*{ext}"))
            for file in files:
                # Преобразуем путь к Windows-стилю
                file = file.replace('/', '\\')
                self.alarm_sound_files.append(file)
    
    
    def save_config(self):
        """Сохранение конфигурации в файл"""
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.cfg, f, indent=4)
    
    def kill_and_restart(self):
        """Убить и перезапустить процессы"""
        pidArray = []
        pidLibrary = {}
        
        # Читаем PID из файлов
        pid_files = [
            (stopwatchPIDfile, 'stopwatch'),
            (pomodoroPIDfile, 'pomodoro'),
            (timerPIDfile, 'timer')
        ]
        
        for pid_file, key in pid_files:
            try:
                with open(pid_file, "r") as f:
                    myPID = f.read().strip()
                    if myPID:
                        pidArray.append(int(myPID))
                        pidLibrary[key] = myPID
            except:
                pass
        
        # Завершаем процессы
        for i in pidArray:
            try:
                proc = psutil.Process(i)
                proc.terminate()
                # Ждем немного, чтобы процесс успел завершиться
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                # Если процесс не завершился, принудительно убиваем его
                try:
                    proc.kill()
                except:
                    pass
            except:
                print(f"Ошибка при закрытии процесса с PID {i}")
        
        # Даем время процессам полностью завершиться
        import time
        time.sleep(0.5)
        
        # Пути к скомпилированным exe файлам
        # Пути к скомпилированным exe файлам
        # stopwatchEXE = os.path.join(parent_dir, "main.dist", "main.exe")
        # timerEXE = os.path.join(parent_dir, "main.dist", "main.exe")
        # pomodoroEXE = os.path.join(parent_dir, "main.dist", "main.exe")

        distEXE = os.path.join(parent_dir, "main.dist", "main.exe")
        
        # Отладочная информация
        print(f"Config file path: {CONFIG_FILE}")
        print(f"Config file exists: {os.path.exists(CONFIG_FILE)}")
        if os.path.exists(CONFIG_FILE):
            print(f"Config file modified: {os.path.getmtime(CONFIG_FILE)}")
        
        # Перезапускаем процессы (теперь exe файлы)
        restart_processes = [
            ('stopwatch', distEXE, stopwatchPIDfile, ["stopwatch"]),
            ('timer', distEXE, timerPIDfile, ["timer"]),
            ('pomodoro', distEXE, pomodoroPIDfile, ["pomodoro","custom"])  # Добавляем аргумент "custom" для помодоро
        ]
        
        for key, exe_file, pid_file, args in restart_processes:
            if key in pidLibrary:
                if os.path.exists(exe_file):
                    try:
                        # Формируем команду для запуска exe файла с аргументами
                        command = [exe_file] + args
                        
                        # Запускаем процесс в той же рабочей директории, где лежит конфиг
                        process = subprocess.Popen(
                            command,
                            creationflags=subprocess.CREATE_NO_WINDOW,  # Только для Windows
                            cwd=current_dir_path  # Устанавливаем рабочую директорию
                        )
                        
                        with open(pid_file, "w") as f:
                            f.write(str(process.pid))
                        
                        print(f"Запущен {key} с PID {process.pid}")
                        print(f"Команда: {' '.join(command)}")
                        print(f"Рабочая директория: {current_dir_path}")
                        
                    except Exception as e:
                        print(f"Ошибка при запуске {key}: {e}")
                else:
                    print(f"Файл {exe_file} не найден для {key}")
                    # Попробуем запустить Python версию как fallback
                    py_files = {
                        'stopwatch': stopwatchPY,
                        'timer': timerPY,
                        'pomodoro': pomodoroPY
                    }
                    
                    if key in py_files and os.path.exists(py_files[key]):
                        try:
                            command = ["python", py_files[key]] + args
                            process = subprocess.Popen(
                                command,
                                creationflags=subprocess.CREATE_NO_WINDOW,
                                cwd=current_dir_path
                            )
                            with open(pid_file, "w") as f:
                                f.write(str(process.pid))
                            print(f"Запущена Python версия {key} с PID {process.pid}")
                        except Exception as e:
                            print(f"Ошибка при запуске Python версии {key}: {e}")
    

    def apply_changes(self, *args):
        """Применить изменения конфигурации с защитой от множественных вызовов"""
        if self._updating:
            return
        
        # Отменяем предыдущий таймер, если он есть
        if hasattr(self, '_apply_timer'):
            self.root.after_cancel(self._apply_timer)
        
        # Устанавливаем новый таймер с небольшой задержкой
        self._apply_timer = self.root.after(100, self._do_apply_changes)

    def _do_apply_changes(self):
        """Фактическое применение изменений"""
        if self._updating:
            return
            
        try:
            self._updating = True
            
            # Считываем значения всех элементов управления
            self.cfg["hideDuration"] = int(self.disappear_delay.get())
            self.cfg["font"] = self.font_var.get()
            self.cfg["position"] = self.position.get()
            self.cfg["tick_sound"] = self.tick_sound_var.get()
            self.cfg["use_ticks_in"] = self.use_ticks_in_var.get()
            self.cfg["tick_interval"] = self.tick_interval_var.get()
            self.cfg["alarm_duration"] = int(self.alarm_duration_var.get())
            self.cfg["alarm_sound"] = self.alarm_sound_var.get()
            self.cfg["final_pomodoro_sound"] = self.final_pomodoro_sound_var.get()
            self.cfg["custom_pomodoro"] = self.custom_pomodoro_var.get()

            # Save new pomodoro mode settings
            self.cfg["infinite_mode"] = self.infinite_mode_var.get()
            self.cfg["enable_symbols"] = self.enable_symbols_var.get()
            self.cfg["final_alarm_duration"] = int(self.final_alarm_duration_var.get())
            
            # Convert cycles to integer and validate
            try:
                cycles = int(self.custom_pomodoro_cycles_var.get())
                if cycles < 1:
                    cycles = 1
            except ValueError:
                cycles = 3  # Default value if invalid
            
            self.cfg["custom_pomodoro_cycles"] = cycles
            
            # Сохраняем конфигурацию и перезапускаем процессы
            self.save_config()
            self.kill_and_restart()
            
        finally:
            self._updating = False
    
          
    
    def select_sound_file(self, sound_var):
        """Открыть диалог выбора звукового файла или папки с учетом типа звука"""
        # Сохраняем текущее значение для возможного восстановления
        previous_value = sound_var.get()
        
        # Определяем начальную директорию в зависимости от типа звука
        if sound_var == self.tick_sound_var:
            initial_dir = ticks_dir
            files_list = self.tick_sound_files
            combo = self.tick_sound_combo
        else:
            initial_dir = alarm_sounds_dir
            files_list = self.alarm_sound_files
            if sound_var == self.alarm_sound_var:
                combo = self.alarm_sound_combo
            else:
                combo = self.final_pomodoro_sound_combo
        
        selection = filedialog.askopenfilename(
            title="Выберите звуковой файл",
            initialdir=initial_dir,
            filetypes=[("Звуковые файлы", "*.mp3 *.wav *.ogg"), ("Все файлы", "*.*")]
        )
        
        if not selection:  # Пользователь отменил выбор
            # Восстанавливаем предыдущее значение
            sound_var.set(previous_value)
            
            # Восстанавливаем отображение в комбобоксе
            if previous_value == "off":
                combo.set("off")
            else:
                if os.path.isdir(previous_value):
                    combo.set(f"{os.path.basename(previous_value)} (folder)")
                else:
                    combo.set(os.path.basename(previous_value))
            return
                
        if os.path.isdir(selection):
            # Если выбрана папка, добавляем ее в список
            folder_name = os.path.basename(selection)
            display_name = f"{folder_name} (folder)"
            
            # Добавляем папку в соответствующий список
            if selection not in files_list:
                files_list.append(selection)
            
            # Устанавливаем полный путь к папке в переменную
            sound_var.set(selection)
            
            # Определяем, какой комбобокс обновлять
            combo.set(display_name)
        else:
            # Если выбран файл
            file_name = os.path.basename(selection)
            
            # Добавляем полный путь к файлу в соответствующий список
            if selection not in files_list:
                files_list.append(selection)
            
            # Устанавливаем полный путь к файлу в переменную
            sound_var.set(selection)
            
            # Отображаем только имя файла в комбобоксе
            combo.set(file_name)
        
        # Обновляем значения в комбобоксах
        self.update_sound_combos()
        self.apply_changes()
    

    def update_sound_combos(self):
        """Обновляет списки звуков в комбобоксах"""
        # Создаем списки для отображения в комбобоксах с полными путями
        tick_display_values = ["off"] + self.tick_sound_files + ["Select file..."] + ["Select folder..."]
        alarm_display_values = ["off"] + self.alarm_sound_files + ["Select file..."] + ["Select folder..."]
        
        # Обновляем значения в комбобоксах
        self.tick_sound_combo['values'] = tick_display_values
        self.alarm_sound_combo['values'] = alarm_display_values
        self.final_pomodoro_sound_combo['values'] = alarm_display_values


    def on_sound_selected(self, event, sound_var, combo):
        """Обработчик выбора звука из выпадающего списка"""
        selected = combo.get()
        
        # Сохраняем текущее значение переменной звука и отображаемого значения для возможного восстановления
        previous_value = sound_var.get()
        previous_display = combo.get()
        
        if selected == "Select file...":
            # Определяем, для какого типа звука вызывается диалог
            if combo == self.tick_sound_combo:
                initial_dir = ticks_dir
                files_list = self.tick_sound_files
            else:
                initial_dir = alarm_sounds_dir
                files_list = self.alarm_sound_files
            
            # Вызываем диалог выбора файла с указанной начальной директорией
            selection = filedialog.askopenfilename(
                title="Выберите звуковой файл",
                initialdir=initial_dir,
                filetypes=[("Звуковые файлы", "*.mp3 *.wav *.ogg"), ("Все файлы", "*.*")]
            )
            
            if selection:  # Если пользователь выбрал файл
                # Преобразуем путь к Windows-стилю
                selection = selection.replace('/', '\\')
                
                # Добавляем файл в соответствующий список, если его там еще нет
                if selection not in files_list:
                    files_list.append(selection)
                
                # Устанавливаем полный путь к файлу в переменную
                sound_var.set(selection)
                
                # Обновляем отображение в комбобоксе (полный путь)
                combo.set(selection)
                
                # Обновляем списки звуков и применяем изменения
                self.update_sound_combos()
                self.apply_changes()
            else:
                # Пользователь отменил выбор - восстанавливаем предыдущее значение
                sound_var.set(previous_value)
                
                # Принудительно восстанавливаем предыдущее отображаемое значение
                self.root.after(10, lambda: combo.set(previous_display))
        
        elif selected == "Select folder...":
            # Определяем, для какого типа звука вызывается диалог
            if combo == self.tick_sound_combo:
                initial_dir = ticks_dir
                files_list = self.tick_sound_files
            else:
                initial_dir = alarm_sounds_dir
                files_list = self.alarm_sound_files
            
            # Вызываем диалог выбора папки
            selection = filedialog.askdirectory(
                title="Выберите папку со звуками",
                initialdir=initial_dir
            )
            
            if selection:  # Если пользователь выбрал папку
                # Преобразуем путь к Windows-стилю
                selection = selection.replace('/', '\\')
                
                # Добавляем папку в соответствующий список, если её там еще нет
                if selection not in files_list:
                    files_list.append(selection)
                
                # Устанавливаем полный путь к папке в переменную
                sound_var.set(selection)
                
                # Обновляем отображение в комбобоксе (полный путь)
                combo.set(selection)
                
                # Обновляем списки звуков и применяем изменения
                self.update_sound_combos()
                self.apply_changes()
            else:
                # Пользователь отменил выбор - восстанавливаем предыдущее значение
                sound_var.set(previous_value)
                
                
                # Принудительно восстанавливаем предыдущее отображаемое значение
                self.root.after(10, lambda: combo.set(previous_display))

                
        
        elif selected == "off":
            sound_var.set("off")
            self.apply_changes()
        else:
            # Выбран звук из списка (уже полный путь)
            sound_var.set(selected)
            self.apply_changes()
        
    def validate_custom_pomodoro(self, new_value):
        """Проверка ввода для поля Custom Pomodoro"""
        # Разрешаем только цифры и пробелы
        if all(c.isdigit() or c.isspace() for c in new_value):
            return True
        return False
    
    def on_custom_pomodoro_changed(self, *args):
        """Обработчик изменения значения Custom Pomodoro"""
        self.apply_changes()
    
    def create_widgets(self, parent):
        """Создание всех элементов управления"""
        # Переменные для хранения значений
        self.disappear_delay = tk.StringVar(value=str(self.cfg["hideDuration"]))
        self.position = tk.StringVar(value=self.cfg["position"])
        self.tick_sound_var = tk.StringVar(value=self.cfg["tick_sound"])
        self.use_ticks_in_var = tk.StringVar(value=self.cfg["use_ticks_in"])
        self.tick_interval_var = tk.StringVar(value=self.cfg["tick_interval"])
        self.alarm_sound_var = tk.StringVar(value=self.cfg["alarm_sound"])
        self.final_pomodoro_sound_var = tk.StringVar(value=self.cfg["final_pomodoro_sound"])
        self.custom_pomodoro_var = tk.StringVar(value=self.cfg["custom_pomodoro"])
        self.infinite_mode_var = tk.BooleanVar(value=self.cfg.get("infinite_mode", True))
        self.custom_pomodoro_cycles_var = tk.StringVar(value=str(self.cfg.get("custom_pomodoro_cycles", 3)))
    
        
        # Задержка исчезновения - ИСПРАВЛЕННАЯ ВЕРСИЯ
        delay_frame = tk.Frame(parent, bg=parent.cget('bg'))
        delay_frame.pack(fill='x', pady=3)
        
        delay_label = tk.Label(delay_frame, text="Dissapear duration (sec):", bg=parent.cget('bg'), font=("Arial", 10))
        delay_label.pack(side='left', padx=3)
        
        delay_spin = ttk.Spinbox(
            delay_frame, 
            from_=0, 
            to=60, 
            width=5, 
            textvariable=self.disappear_delay,
            increment=1  # Явно указываем шаг
            # НЕ используем command=self.apply_changes
        )
        delay_spin.pack(side='right', padx=3)

        # Добавляем обработчик через trace - ТОЛЬКО ОДИН РАЗ
        # self.disappear_delay.trace_add("write", self.apply_changes)
        # Добавляем обработчик с защитой от множественных вызовов
        def on_delay_changed(*args):
            if not self._updating:
                self.apply_changes()

        self.disappear_delay.trace_add("write", on_delay_changed)
                

        # Enable symbols блок
        enable_symbols_frame = tk.Frame(parent, bg=parent.cget('bg'))
        enable_symbols_frame.pack(fill='x', pady=3)

        enable_symbols_label = tk.Label(enable_symbols_frame, text="Enable symbols:", bg=parent.cget('bg'), font=("Arial", 10))
        enable_symbols_label.pack(side='left', padx=5)

        self.enable_symbols_var = tk.BooleanVar(value=self.cfg.get("enable_symbols", True))
        enable_symbols_check = tk.Checkbutton(
            enable_symbols_frame,
            variable=self.enable_symbols_var,
            bg=parent.cget('bg'),
            command=self.apply_changes
        )
        enable_symbols_check.pack(side='right', padx=5)



        # Добавляем выбор шрифта
        font_frame = tk.Frame(parent, bg=parent.cget('bg'))
        font_frame.pack(fill='x', pady=3)

        font_label = tk.Label(font_frame, text="Font:", bg=parent.cget('bg'), font=("Arial", 10))
        font_label.pack(side='left', padx=3)

        # Получаем список всех установленных шрифтов
        installed_fonts = sorted(list(tkfont.families()))
        self.font_var = tk.StringVar(value=self.cfg["font"])

        font_combo = ttk.Combobox(
            font_frame,
            textvariable=self.font_var,
            values=installed_fonts,
            width=25
        )
        font_combo.pack(side='right', padx=3)
        font_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_changes())







        # Position блок
        position_frame = tk.Frame(parent, bg=parent.cget('bg'), padx=10, pady=3)
        position_frame.pack(fill='x', pady=3)
        
        # Создаем канвас для отображения прямоугольника с закругленными углами
        canvas_height = 130
        canvas = tk.Canvas(position_frame, height=canvas_height, bg=parent.cget('bg'), highlightthickness=0)
        canvas.pack(fill='x')
        
        # Рисуем прямоугольник с закругленными углами
        def draw_rounded_rectangle(event):
            canvas.delete("all")
            width = event.width
            height = canvas_height
            rect_width = width - 20
            rect_height = height - 20
            
            x0 = 10
            y0 = 10
            x1 = x0 + rect_width
            y1 = y0 + rect_height
            
            radius = 15
            
            # Рисуем закругленный прямоугольник
            canvas.create_arc(x0, y0, x0 + 2*radius, y0 + 2*radius, 
                            start=90, extent=90, style="arc", outline="black", width=2)
            canvas.create_line(x0 + radius, y0, x1 - radius, y0, fill="black", width=2)
            canvas.create_arc(x1 - 2*radius, y0, x1, y0 + 2*radius, 
                            start=0, extent=90, style="arc", outline="black", width=2)
            canvas.create_line(x1, y0 + radius, x1, y1 - radius, fill="black", width=2)
            canvas.create_arc(x1 - 2*radius, y1 - 2*radius, x1, y1, 
                            start=270, extent=90, style="arc", outline="black", width=2)
            canvas.create_line(x0 + radius, y1, x1 - radius, y1, fill="black", width=2)
            canvas.create_arc(x0, y1 - 2*radius, x0 + 2*radius, y1, 
                            start=180, extent=90, style="arc", outline="black", width=2)
            canvas.create_line(x0, y0 + radius, x0, y1 - radius, fill="black", width=2)
            
            # Создаем текст "Position" в центре
            canvas.create_text(width/2, height/2, text="Position", font=("Arial", 16, "bold"))
            
            # Добавляем радиокнопки по углам
            # Верхний левый
            top_left_radio = tk.Radiobutton(
                canvas, 
                text="", 
                variable=self.position, 
                value="top_left", 
                bg=parent.cget('bg'), 
                activebackground=parent.cget('bg'),
                highlightthickness=0,
                command=self.apply_changes
            )
            canvas.create_window(x0 + 25, y0 + 25, window=top_left_radio)
            
            # Верхний правый
            top_right_radio = tk.Radiobutton(
                canvas, 
                text="", 
                variable=self.position, 
                value="top_right", 
                bg=parent.cget('bg'), 
                activebackground=parent.cget('bg'),
                highlightthickness=0,
                command=self.apply_changes
            )
            canvas.create_window(x1 - 25, y0 + 25, window=top_right_radio)
            
            # Нижний левый
            bottom_left_radio = tk.Radiobutton(
                canvas, 
                text="", 
                variable=self.position, 
                value="bottom_left", 
                bg=parent.cget('bg'), 
                activebackground=parent.cget('bg'),
                highlightthickness=0,
                command=self.apply_changes
            )
            canvas.create_window(x0 + 25, y1 - 25, window=bottom_left_radio)
            
            # Нижний правый
            bottom_right_radio = tk.Radiobutton(
                canvas, 
                text="", 
                variable=self.position, 
                value="bottom_right", 
                bg=parent.cget('bg'), 
                activebackground=parent.cget('bg'),
                highlightthickness=0,
                command=self.apply_changes
            )
            canvas.create_window(x1 - 25, y1 - 25, window=bottom_right_radio)
        
        canvas.bind("<Configure>", draw_rounded_rectangle)
        
        # Ticks блок
        ticks_frame = tk.LabelFrame(parent, text="Ticks", bg=parent.cget('bg'), padx=10, pady=3, font=("Arial", 12, "bold"))
        ticks_frame.pack(fill='x', pady=3)
        
        # Tick sound
        tick_sound_frame = tk.Frame(ticks_frame, bg=parent.cget('bg'), padx=5, pady=3)
        tick_sound_frame.pack(fill='x', pady=3)
        
        tick_sound_label = tk.Label(tick_sound_frame, text="Tick sound", bg=parent.cget('bg'))
        tick_sound_label.pack(side='left')
        
        # Для Tick sound combo:
        self.tick_sound_combo = ttk.Combobox(
            tick_sound_frame,
            textvariable=self.tick_sound_var,
            values=["off"] + self.tick_sound_files + ["Select file..."] + ["Select folder..."],  # Используем полные пути
            state="readonly",
            width=25
        )
        self.tick_sound_combo.pack(side='right')
        self.tick_sound_combo.bind("<<ComboboxSelected>>", lambda event: self.on_sound_selected(event, self.tick_sound_var, self.tick_sound_combo))

        # Установить отображаемое значение как полный путь
        if self.tick_sound_var.get() != "off":
            self.tick_sound_combo.set(self.tick_sound_var.get())
        
        # Use ticks in
        use_ticks_frame = tk.Frame(ticks_frame, bg=parent.cget('bg'), padx=5, pady=3)
        use_ticks_frame.pack(fill='x', pady=3)
        
        use_ticks_label = tk.Label(use_ticks_frame, text="Use ticks in", bg=parent.cget('bg'))
        use_ticks_label.pack(side='left')
        
        use_ticks_combo = ttk.Combobox(
            use_ticks_frame,
            textvariable=self.use_ticks_in_var,
            values=["stopwatch", "timer", "pomodoro"],
            state="readonly",
            width=25
        )
        use_ticks_combo.pack(side='right')
        use_ticks_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_changes())
        
        # Interval
        interval_frame = tk.Frame(ticks_frame, bg=parent.cget('bg'), padx=5, pady=5)
        interval_frame.pack(fill='x', pady=3)
        
        interval_label = tk.Label(interval_frame, text="Interval", bg=parent.cget('bg'))
        interval_label.pack(side='left')
        
        interval_combo = ttk.Combobox(
            interval_frame,
            textvariable=self.tick_interval_var,
            values=["per second", "per minute"],
            state="readonly",
            width=25
        )
        interval_combo.pack(side='right')
        interval_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_changes())
        
        # Alarm блок
        alarm_frame = tk.LabelFrame(parent, text="Alarm", bg=parent.cget('bg'), padx=10, pady=3, font=("Arial", 12, "bold"))
        alarm_frame.pack(fill='x', pady=5)
        

        # Добавляем поле Alarm duration
        alarm_duration_frame = tk.Frame(alarm_frame, bg=parent.cget('bg'), padx=5, pady=3)
        alarm_duration_frame.pack(fill='x', pady=3)

        alarm_duration_label = tk.Label(alarm_duration_frame, text="Alarm duration (sec)", bg=parent.cget('bg'))
        alarm_duration_label.pack(side='left')

        # Alarm duration - ИСПРАВЛЕННАЯ ВЕРСИЯ
        def validate_alarm_duration(new_value):
            if new_value == "":
                return True
            try:
                value = int(new_value)
                return value >= 0
            except ValueError:
                return False

        validate_alarm_cmd = parent.register(validate_alarm_duration)

        self.alarm_duration_var = tk.StringVar(value=str(self.cfg["alarm_duration"]))
        alarm_duration_entry = ttk.Spinbox(
            alarm_duration_frame,
            from_=0,
            to=300,
            width=5,
            textvariable=self.alarm_duration_var,
            validate="key",
            validatecommand=(validate_alarm_cmd, '%P'),
            increment=1  # Явно указываем шаг
            # НЕ используем command
        )
        alarm_duration_entry.pack(side='right')
        
        # Привязываем событие изменения - ТОЛЬКО ОДИН РАЗ
        # self.alarm_duration_var.trace_add("write", self.apply_changes)
        # Привязываем событие изменения с защитой
        def on_alarm_duration_changed(*args):
            if not self._updating:
                self.apply_changes()

        self.alarm_duration_var.trace_add("write", on_alarm_duration_changed)


        # Final alarm duration - ИСПРАВЛЕННАЯ ВЕРСИЯ

        final_alarm_duration_frame = tk.Frame(alarm_frame, bg=parent.cget('bg'), padx=5, pady=5)
        final_alarm_duration_frame.pack(fill='x', pady=3)

        final_alarm_duration_label = tk.Label(final_alarm_duration_frame, text="Final alarm duration (sec)", bg=parent.cget('bg'))
        final_alarm_duration_label.pack(side='left')

        self.final_alarm_duration_var = tk.StringVar(value=str(self.cfg["final_alarm_duration"]))
        final_alarm_duration_entry = ttk.Spinbox(
            final_alarm_duration_frame,
            from_=0,
            to=300,
            width=5,
            textvariable=self.final_alarm_duration_var,
            validate="key",
            validatecommand=(validate_alarm_cmd, '%P'),
            increment=1  # Явно указываем шаг
            # НЕ используем command
        )
        final_alarm_duration_entry.pack(side='right')
        
        # Привязываем событие изменения - ТОЛЬКО ОДИН РАЗ
        # self.final_alarm_duration_var.trace_add("write", self.apply_changes)
        # Привязываем событие изменения с защитой
        def on_final_alarm_duration_changed(*args):
            if not self._updating:
                self.apply_changes()

        self.final_alarm_duration_var.trace_add("write", on_final_alarm_duration_changed)



        # Alarm sound
        alarm_sound_frame = tk.Frame(alarm_frame, bg=parent.cget('bg'), padx=5, pady=3)
        alarm_sound_frame.pack(fill='x', pady=3)
        
        alarm_sound_label = tk.Label(alarm_sound_frame, text="Alarm sound", bg=parent.cget('bg'))
        alarm_sound_label.pack(side='left')
        
        # Для Alarm sound combo:
        self.alarm_sound_combo = ttk.Combobox(
            alarm_sound_frame,
            textvariable=self.alarm_sound_var,
            values=["off"] + self.alarm_sound_files + ["Select file..."] + ["Select folder..."],  # Используем полные пути
            state="readonly",
            width=25
        )
        self.alarm_sound_combo.pack(side='right')
        self.alarm_sound_combo.bind("<<ComboboxSelected>>", lambda event: self.on_sound_selected(event, self.alarm_sound_var, self.alarm_sound_combo))

        # Установить отображаемое значение как полный путь
        if self.alarm_sound_var.get() != "off":
            self.alarm_sound_combo.set(self.alarm_sound_var.get())
        
        # Final pomodoro sound
        final_sound_frame = tk.Frame(alarm_frame, bg=parent.cget('bg'), padx=5, pady=3)
        final_sound_frame.pack(fill='x', pady=3)
        
        final_sound_label = tk.Label(final_sound_frame, text="Final pomodoro sound", bg=parent.cget('bg'))
        final_sound_label.pack(side='left')
        final_sound_label.pack(side='left')
            
        # Для Final pomodoro sound combo:
        self.final_pomodoro_sound_combo = ttk.Combobox(
            final_sound_frame,
            textvariable=self.final_pomodoro_sound_var,
            values=["off"] + self.alarm_sound_files + ["Select file..."] + ["Select folder..."],  # Используем полные пути
            state="readonly",
            width=25
        )
        self.final_pomodoro_sound_combo.pack(side='right')
        self.final_pomodoro_sound_combo.bind("<<ComboboxSelected>>", lambda event: self.on_sound_selected(event, self.final_pomodoro_sound_var, self.final_pomodoro_sound_combo))

        # Установить отображаемое значение как полный путь
        if self.final_pomodoro_sound_var.get() != "off":
            self.final_pomodoro_sound_combo.set(self.final_pomodoro_sound_var.get())

        # После создания tick_sound_combo
        self.show_full_path_tooltip(self.tick_sound_combo, self.tick_sound_var)

        # После создания alarm_sound_combo
        self.show_full_path_tooltip(self.alarm_sound_combo, self.alarm_sound_var)

        # После создания final_pomodoro_sound_combo
        self.show_full_path_tooltip(self.final_pomodoro_sound_combo, self.final_pomodoro_sound_var)    
        
        # Custom Pomodoro блок
        pomodoro_frame = tk.LabelFrame(parent, text="Custom Pomodoro", bg=parent.cget('bg'), padx=10, pady=3, font=("Arial", 12, "bold"))
        pomodoro_frame.pack(fill='x', pady=10)
        
        # Добавляем пояснение (capslock + v)
        capslock_label = tk.Label(pomodoro_frame, text="(capslock + v)", bg=parent.cget('bg'))
        capslock_label.pack(anchor='center')
        
        # Поле ввода для Custom Pomodoro
        validate_cmd = parent.register(self.validate_custom_pomodoro)
        custom_pomodoro_entry = tk.Entry(
            pomodoro_frame,
            textvariable=self.custom_pomodoro_var,
            validate="key",
            validatecommand=(validate_cmd, '%P')
        )
        custom_pomodoro_entry.pack(fill='x', pady=3)
        
        # Добавляем пояснение
        last_two_label = tk.Label(pomodoro_frame, text="Last two numbers will be repeated", bg=parent.cget('bg'))
        last_two_label.pack(anchor='e')
        
        # Привязываем событие изменения
        self.custom_pomodoro_var.trace_add("write", self.on_custom_pomodoro_changed)




        # Добавляем новую строку в рамке Custom Pomodoro для режима и количества циклов
        mode_cycles_frame = tk.Frame(pomodoro_frame, bg=parent.cget('bg'), padx=5, pady=3)
        mode_cycles_frame.pack(fill='x', pady=3)
        
        # Выпадающий список для режима помодоро
        mode_frame = tk.Frame(mode_cycles_frame, bg=parent.cget('bg'))
        mode_frame.pack(side='left', fill='x', expand=True)
        
        mode_label = tk.Label(mode_frame, text="Mode:", bg=parent.cget('bg'))
        mode_label.pack(side='left', padx=(0, 5))
        
        mode_combo = ttk.Combobox(
            mode_frame,
            values=["Infinite (increasing)", "Limited cycles"],
            state="readonly",
            width=15
        )
        mode_combo.pack(side='left', fill='x', expand=True)
        # Установить выбранный элемент на основе infinite_mode
        mode_combo.current(0 if self.infinite_mode_var.get() else 1)
        
        # Обработчик изменения режима
        def on_mode_changed(event):
            selected_index = mode_combo.current()
            self.infinite_mode_var.set(selected_index == 0)  # 0 = Infinite, 1 = Limited
            self.apply_changes()
        
        mode_combo.bind("<<ComboboxSelected>>", on_mode_changed)
        
        # Поле ввода для количества циклов
        cycles_frame = tk.Frame(mode_cycles_frame, bg=parent.cget('bg'))
        cycles_frame.pack(side='right', padx=(10, 0))
        
        cycles_label = tk.Label(cycles_frame, text="Cycles:", bg=parent.cget('bg'))
        cycles_label.pack(side='left', padx=(0, 5))
        
        # Cycles spinbox - ИСПРАВЛЕННАЯ ВЕРСИЯ
        def validate_cycles(new_value):
            if new_value == "":
                return True
            try:
                value = int(new_value)
                return value > 0
            except ValueError:
                return False
        
        validate_cycles_cmd = parent.register(validate_cycles)
        
        cycles_spin = ttk.Spinbox(
            cycles_frame, 
            from_=1, 
            to=100, 
            width=5, 
            textvariable=self.custom_pomodoro_cycles_var,
            validate="key",
            validatecommand=(validate_cycles_cmd, '%P'),
            increment=1  # Явно указываем шаг
            # НЕ используем command
        )
        cycles_spin.pack(side='left')
        
        # Обработчик изменения количества циклов - ТОЛЬКО ОДИН РАЗ
        # self.custom_pomodoro_cycles_var.trace_add("write", self.apply_changes)
        # Обработчик изменения количества циклов с защитой
        def on_cycles_changed(*args):
            if not self._updating:
                self.apply_changes()

        self.custom_pomodoro_cycles_var.trace_add("write", on_cycles_changed)        


def startMain():
    root = tk.Tk()
    global app
    app = SettingsApp(root)
    root.mainloop()

# Запуск приложения
if __name__ == "__main__":
    startMain()

