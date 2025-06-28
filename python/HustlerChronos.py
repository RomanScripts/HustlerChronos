from sys import argv

# argv = [1,"timer", 5]

def main():
    if len(argv) < 2:
        print("Usage: main.exe [1|2|3|4] [args...]")
        return
    
    script_num = argv[1]
    
    if script_num == "options":
        import options
        options.startMain()
    elif script_num == "stopwatch":
        del argv[1]
        import stopwatch
        stopwatch.startMain()
    elif script_num == "timer":
        del argv[1]
        import timer
        timer.startMain()
    elif script_num == "pomodoro":
        del argv[1]
        import pomodoro
        pomodoro.startMain()


if __name__ == "__main__":
    main()
