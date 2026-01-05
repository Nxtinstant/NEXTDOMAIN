import requests
import tkinter as tk
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import subprocess
import threading
import time
from tkinter import simpledialog, ttk
import urllib.request
import sys
import traceback
import os
import platform


# Global crash handler
crash_log = []


def log_crash(error_info):
    """Log crashes for debugging"""
    crash_log.append({
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'error': error_info
    })
    try:
        with open('crash_log.txt', 'a') as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_info}\n")
    except:
        pass


# Activity log function
def log_domain(domain):
    """Log each domain entered by the user"""
    log_path = os.path.expanduser("~/activity.log")
    try:
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(domain + "\n")
    except Exception as e:
        log_crash(f"Activity log write error: {str(e)}")


def show_activity_log():
    """Display all previously logged domains"""
    log_path = os.path.expanduser("~/activity.log")
    try:
        with open(log_path, "r", encoding="utf-8") as log_file:
            domains = log_file.readlines()
            if domains:
                log_text = "\n".join([d.strip() for d in domains])
                typewriter("=== Activity Log ===", output)
                typewriter(log_text, output)
            else:
                typewriter("No domains have been logged yet.", output)
    except FileNotFoundError:
        typewriter("No domains have been logged yet.", output)
    except Exception as e:
        log_crash(f"Activity log read error: {str(e)}")
        typewriter("Error reading activity log.", output)


# Shortcut creation (Windows only)
def install_pywin32():
    """Install pywin32 using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
        return True
    except Exception as e:
        return False


def create_shortcut_manual():
    """Create a manual shortcut file for the user to drag to desktop"""
    try:
        shortcut_path = os.path.join(os.path.expanduser("~"), "nextdomain.lnk")
        with open(shortcut_path, "w") as f:
            f.write(f"[InternetShortcut]\nURL=file://{__file__}\n")
        typewriter(f"Manual shortcut created at: {shortcut_path}", output)
        typewriter("Drag this file to your desktop to create a shortcut.", output)
    except Exception as e:
        log_crash(f"Manual shortcut creation error: {str(e)}")
        typewriter("Error creating manual shortcut.", output)


def create_shortcut():
    """Create a desktop shortcut for the app (Windows only)"""
    if platform.system() != "Windows":
        typewriter("Shortcut creation is only supported on Windows.", output)
        return


    try:
        import win32com.client
        import pythoncom
    except ImportError:
        typewriter("Installing pywin32...", output)
        if not install_pywin32():
            typewriter("Failed to install pywin32. Please install it manually with 'pip install pywin32'.", output)
            create_shortcut_manual()
            return
        try:
            import win32com.client
            import pythoncom
        except ImportError:
            typewriter("Failed to import pywin32 after installation. Please restart the program.", output)
            create_shortcut_manual()
            return


    try:
        pythoncom.CoInitialize()
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop, "nextdomain.lnk")
        if os.path.exists(shortcut_path):
            typewriter("Shortcut already exists.", output)
            return


        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = __file__
        shortcut.WorkingDirectory = os.path.dirname(__file__)
        shortcut.IconLocation = sys.executable
        shortcut.save()
        typewriter(f"Shortcut created at: {shortcut_path}", output)
    except Exception as e:
        log_crash(f"Shortcut creation error: {str(e)}")
        typewriter("Error creating shortcut. Make sure you have write access.", output)
        create_shortcut_manual()


def safe_execute(func, fallback_message="Operation failed. Continuing safely...", *args, **kwargs):
    """Wrapper to safely execute functions and handle crashes"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_msg = f"{func.__name__}: {str(e)}"
        log_crash(error_msg)
        return fallback_message


def typewriter(text, text_widget, delay=0.01):
    try:
        for char in text:
            text_widget.insert(tk.END, char)
            text_widget.update()
            time.sleep(delay)
        text_widget.insert(tk.END, "\n")
    except Exception as e:
        log_crash(f"Typewriter error: {str(e)}")
        try:
            text_widget.insert(tk.END, text + "\n")
        except:
            pass


def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


def scan_website(url, progress_bar):
    pages = set()
    hidden_pages = set()
    try:
        progress_bar.start()
        time.sleep(2)
        progress_bar.stop()
    except Exception as e:
        log_crash(f"Progress bar error: {str(e)}")
    
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            full_url = urljoin(url, link['href'])
            if url in full_url:
                pages.add(full_url)
            elif full_url.startswith('/'):
                hidden_pages.add(urljoin(url, full_url[1:]))
        return pages, hidden_pages
    except requests.exceptions.Timeout:
        log_crash(f"Timeout scanning {url}")
        return set(), {"Error: Connection timeout. Website might be slow or unavailable."}
    except requests.exceptions.ConnectionError:
        log_crash(f"Connection error scanning {url}")
        return set(), {"Error: Cannot connect to website. Check internet connection."}
    except Exception as e:
        log_crash(f"Scan error: {str(e)}")
        return set(), {f"Error: Unable to scan website. Continuing safely."}


def analyze_stream(url):
    try:
        result = subprocess.check_output(['curl', '-I', url], timeout=5).decode()
        return f"Headers:\n{result}"
    except subprocess.TimeoutExpired:
        log_crash(f"Curl timeout for {url}")
        return "Error: Request timed out. Website not responding."
    except FileNotFoundError:
        log_crash("Curl not found")
        try:
            response = requests.head(url, timeout=5)
            headers = "\n".join([f"{k}: {v}" for k, v in response.headers.items()])
            return f"Headers (using alternative method):\n{headers}"
        except:
            return "Error: Cannot analyze headers. Tool unavailable."
    except Exception as e:
        log_crash(f"Analyze stream error: {str(e)}")
        return "Error: Unable to analyze stream. Continuing safely."


# Theme variables
current_theme = "dark"
truncate_backend = True


def save_theme():
    with open("theme.txt", "w") as f:
        f.write(current_theme)


def load_theme():
    if os.path.exists("theme.txt"):
        with open("theme.txt", "r") as f:
            theme = f.read().strip()
            if theme == "light":
                set_light_theme()
            else:
                set_dark_theme()
    else:
        set_dark_theme()


def set_light_theme():
    global current_theme
    current_theme = "light"
    output.config(bg="white", fg="black")
    entry.config(bg="white", fg="black")
    root.configure(bg="white")
    style.configure("TButton", foreground="black", background="#d1d1d1")
    style.map("TButton", background=[('active', '#c1c1c1'), ('!active', '#d1d1d1')])
    save_theme()


def set_dark_theme():
    global current_theme
    current_theme = "dark"
    output.config(bg="black", fg="green")
    entry.config(bg="black", fg="green")
    root.configure(bg="black")
    style.configure("TButton", foreground="white", background="#0f5132")
    style.map("TButton", background=[('active', '#14532d'), ('!active', '#0f5132')])
    save_theme()


def toggle_truncation():
    global truncate_backend
    truncate_backend = not truncate_backend
    typewriter(f"Truncate backend code: {'On' if truncate_backend else 'Off'}", output)


def get_frontend_code(url):
    try:
        response = requests.get(url, timeout=5)
        return response.text
    except requests.exceptions.Timeout:
        log_crash(f"Frontend timeout for {url}")
        return "Error: Connection timeout. Website taking too long to respond."
    except requests.exceptions.ConnectionError:
        log_crash(f"Frontend connection error for {url}")
        return "Error: Cannot connect to website. Check URL or internet connection."
    except Exception as e:
        log_crash(f"Frontend code error: {str(e)}")
        return "Error: Unable to retrieve frontend code. Continuing safely."


def get_backend_code(url):
    try:
        result = subprocess.check_output(['curl', '-L', url], timeout=5).decode()
        if truncate_backend:
            return result[:1000] + "\n... (truncated)" if len(result) > 1000 else result
        else:
            return result
    except subprocess.TimeoutExpired:
        log_crash(f"Backend curl timeout for {url}")
        return "Error: Request timed out. Backend not responding."
    except FileNotFoundError:
        log_crash("Curl not found for backend")
        try:
            response = requests.get(url, timeout=5)
            result = response.text
            if truncate_backend:
                return result[:1000] + "\n... (truncated)" if len(result) > 1000 else result
            else:
                return result
        except:
            return "Error: Cannot retrieve backend code. Tool unavailable."
    except Exception as e:
        log_crash(f"Backend code error: {str(e)}")
        return "Error: Unable to retrieve backend code. Continuing safely."


def fetch_text(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        return text
    except Exception as e:
        log_crash(f"Fetch text error: {str(e)}")
        return "Error: Unable to fetch text from URL. Continuing safely."


def send_requests(url):
    methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD']
    responses = []
    for method in methods:
        try:
            response = requests.request(method, url, timeout=5)
            responses.append(f"{method} {url} - Status: {response.status_code}")
        except requests.exceptions.Timeout:
            responses.append(f"{method} {url} - Timeout (skipped)")
            log_crash(f"Request timeout: {method} {url}")
        except requests.exceptions.ConnectionError:
            responses.append(f"{method} {url} - Connection failed (skipped)")
            log_crash(f"Connection error: {method} {url}")
        except Exception as e:
            responses.append(f"{method} {url} - Error handled (continuing)")
            log_crash(f"Request error {method}: {str(e)}")
    return "\n".join(responses)


def download_update():
    url = simpledialog.askstring("Update", "Enter update link:")
    if url:
        progress_window = tk.Toplevel(root)
        progress_window.title("Updating...")
        progress_label = tk.Label(progress_window, text="Downloading Update...", fg="green")
        progress_label.pack()
        progress = ttk.Progressbar(progress_window, mode="determinate", length=300)
        progress.pack()
        progress.start()
        try:
            urllib.request.urlretrieve(url, "Nextdomain_Scanner.py")
            progress.stop()
            progress_label.config(text="Update Completed. Restarting application...")
            progress_window.update()
            time.sleep(1)
            progress_window.destroy()
            try:
                with open("version_info.txt", "w") as f:
                    f.write(f"Dropbox Version: {url}")
            except Exception as e:
                log_crash(f"Version save error: {str(e)}")
            root.destroy()
            try:
                subprocess.Popen(['python3', 'Nextdomain_Scanner.py'])
            except FileNotFoundError:
                try:
                    subprocess.Popen(['python', 'Nextdomain_Scanner.py'])
                except:
                    log_crash("Cannot restart application automatically")
        except urllib.error.URLError:
            progress.stop()
            progress_label.config(text="Error: Invalid URL or connection failed")
            log_crash(f"Update URL error: {url}")
        except Exception as e:
            progress_label.config(text=f"Error: Update failed. Continuing safely.")
            progress.stop()
            log_crash(f"Update error: {str(e)}")


def display_help():
    return """Commands:
    analyze stream - Analyze website headers
    codewebfront - Show frontend code
    codewebback - Attempt backend code view
    deldo - Clear and restart
    pause - Pause output
    about - Show project details
    update - Update the program
    help - Show this menu
    chatpost - Open chat interface to POST messages
    runfile - Run a Python file by specifying path
    logconsole - Open realtime log console window
    exitconsole - Close log console window
    rethack - Show matrix animation text
    crashlog - View crash and bug log
    activitylog - View all previously searched domains
    addshortcut - Create desktop shortcut (Windows only)
    runbackground - Run scans in background
    settings - Open settings window
    clear - Clear output
    clearlog - Clear all logs and start fresh
    fetchtext - Fetch and display text from URL
    exit - Exit the program"""


# Globals for logconsole
log_console = None
log_console_text = None
log_console_running = False


def open_log_console():
    global log_console, log_console_text, log_console_running
    if log_console is not None:
        return
    log_console_running = True
    try:
        log_console = tk.Toplevel(root)
        log_console.title("Log Console nxtinstant")
        log_console.geometry("700x400")
        log_console.configure(bg="black")
        log_console_text = tk.Text(log_console, bg="black", fg="lime", font=("Courier", 12), state=tk.DISABLED, wrap=tk.WORD)
        log_console_text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        def log_writer():
            count = 0
            while log_console_running:
                try:
                    time.sleep(1)
                    if log_console_text and log_console_text.winfo_exists():
                        log_console_text.config(state=tk.NORMAL)
                        log_console_text.insert(tk.END, f"NEXTDOMAIN running perfectly... {count}\n")
                        log_console_text.see(tk.END)
                        log_console_text.config(state=tk.DISABLED)
                        count += 1
                    else:
                        break
                except Exception as e:
                    log_crash(f"Log writer error: {str(e)}")
                    break
        threading.Thread(target=log_writer, daemon=True).start()
    except Exception as e:
        log_crash(f"Open log console error: {str(e)}")
        log_console_running = False


def close_log_console():
    global log_console_running, log_console
    try:
        if log_console is not None:
            log_console_running = False
            log_console.destroy()
            log_console = None
    except Exception as e:
        log_crash(f"Close log console error: {str(e)}")
        log_console_running = False
        log_console = None


def type_matrix_text(text_widget, text, delay=0.05):
    try:
        text_widget.delete(1.0, tk.END)
        for char in text:
            text_widget.insert(tk.END, char)
            text_widget.update()
            time.sleep(delay)
    except Exception as e:
        log_crash(f"Matrix text error: {str(e)}")
        try:
            text_widget.insert(tk.END, text)
        except:
            pass


def open_chat_post():
    target_url = simpledialog.askstring("ChatPost", "Enter URL to send POST requests to:")
    if not target_url:
        return
    try:
        chat_win = tk.Toplevel(root)
        chat_win.title("Chat POST Interface")
        chat_win.geometry("500x500")
        chat_win.configure(bg="black")
        chat_display = tk.Text(chat_win, bg="black", fg="lime", font=("Courier", 12), state=tk.DISABLED, wrap=tk.WORD)
        chat_display.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        msg_entry = tk.Entry(chat_win, bg="black", fg="lime", font=("Courier", 12), insertbackground="lime")
        msg_entry.pack(fill=tk.X, padx=5, pady=5)
        def post_message(event=None):
            message = msg_entry.get().strip()
            if not message:
                return
            msg_entry.delete(0, tk.END)
            try:
                chat_display.config(state=tk.NORMAL)
                chat_display.insert(tk.END, f"You: {message}\n")
                chat_display.config(state=tk.DISABLED)
                chat_display.see(tk.END)
            except Exception as e:
                log_crash(f"Chat display error: {str(e)}")
            def send():
                try:
                    response = requests.post(target_url, data={"message": message}, timeout=5)
                    reply = f"Server: {response.text.strip()}"
                except requests.exceptions.Timeout:
                    reply = "Error: Server timeout (continuing safely)"
                    log_crash(f"Chat POST timeout to {target_url}")
                except requests.exceptions.ConnectionError:
                    reply = "Error: Cannot connect to server"
                    log_crash(f"Chat POST connection error to {target_url}")
                except Exception as e:
                    reply = f"Error: Request failed (continuing safely)"
                    log_crash(f"Chat POST error: {str(e)}")
                try:
                    chat_display.config(state=tk.NORMAL)
                    chat_display.insert(tk.END, reply + "\n")
                    chat_display.config(state=tk.DISABLED)
                    chat_display.see(tk.END)
                except Exception as e:
                    log_crash(f"Chat reply display error: {str(e)}")
            threading.Thread(target=send).start()
        msg_entry.bind("<Return>", post_message)
    except Exception as e:
        log_crash(f"Open chat post error: {str(e)}")


def run_file():
    filepath = simpledialog.askstring("Run File", "Enter full file path to run:")
    if not filepath:
        return "No file path provided."
    try:
        if not os.path.exists(filepath):
            log_crash(f"File not found: {filepath}")
            return f"Error: File not found at {filepath}"
        result = subprocess.check_output(['python3', filepath], stderr=subprocess.STDOUT, timeout=10).decode()
        return f"Output from {filepath}:\n{result}"
    except subprocess.TimeoutExpired:
        log_crash(f"File execution timeout: {filepath}")
        return f"Error: File execution timed out. File may have infinite loop."
    except subprocess.CalledProcessError as e:
        log_crash(f"File execution error: {filepath}")
        return f"Error running file:\n{e.output.decode()}"
    except FileNotFoundError:
        log_crash("Python3 not found, trying python")
        try:
            result = subprocess.check_output(['python', filepath], stderr=subprocess.STDOUT, timeout=10).decode()
            return f"Output from {filepath}:\n{result}"
        except Exception as e:
            log_crash(f"Python execution failed: {str(e)}")
            return f"Error: Python not available. Cannot run file."
    except Exception as e:
        log_crash(f"Run file error: {str(e)}")
        return f"Error: Unable to run file. Continuing safely."


copy_button = None


def setup_copy_button():
    global copy_button
    if copy_button is not None:
        copy_button.destroy()
        copy_button = None


def add_copy_button():
    global copy_button
    setup_copy_button()
    copy_button = tk.Button(root, text="Copy Code", bg="#0afd47", fg="black", font=("Courier", 10, "bold"),
                            command=copy_code, relief=tk.RAISED)
    copy_button.pack(pady=5)


def copy_code():
    try:
        content = output.get(1.0, tk.END)
        root.clipboard_clear()
        root.clipboard_append(content)
        typewriter("Code copied to clipboard!", output)
    except Exception as e:
        log_crash(f"Copy code error: {str(e)}")
        typewriter("Error: Unable to copy code. Continuing safely.", output)


def process_initial_input():
    try:
        cmd = entry.get().strip()
        output.delete(1.0, tk.END)
        progress_bar.start()
        time.sleep(2)
        progress_bar.stop()
        if is_valid_url(cmd):
            pages, hidden = scan_website(cmd, progress_bar)
            if "Error" in str(hidden):
                typewriter(str(hidden.pop()) if hidden else "Error scanning website", output)
            else:
                typewriter("Pages Found:", output)
                for p in pages:
                    typewriter(f" - {p}", output)
                typewriter("\nHidden Pages:", output)
                for h in hidden:
                    typewriter(f" - {h}", output)
                entry.delete(0, tk.END)
                entry.insert(0, f"{cmd}> ")
                entry.bind("<Return>", lambda e: threading.Thread(target=lambda: process_command(cmd)).start())
                log_domain(cmd)
        else:
            typewriter("Error: Please enter a valid domain (e.g., https://nxtinstant.in)", output)
    except Exception as e:
        log_crash(f"Process initial input error: {str(e)}")
        typewriter("Error processing input. Please try again.", output)
        setup_initial_screen()


def run_background_task(url, subcommand, btn_frame):
    if subcommand == "codewebfront":
        result = get_frontend_code(url)
    elif subcommand == "codewebback":
        result = get_backend_code(url)
    else:
        typewriter("Invalid subcommand.", output)
        btn_frame.pack_forget()
        return
    typewriter(result, output)
    typewriter("done", output)
    btn_frame.pack_forget()


def runbackground_command(url):
    output.delete(1.0, tk.END)
    typewriter("Run background subcommand:\n1: codewebfront\n2: codewebback", output)
    btn_frame = tk.Frame(root, bg="black")
    btn_frame.pack(pady=5)
    btn1 = tk.Button(btn_frame, text="1", command=lambda: run_background_task(url, "codewebfront", btn_frame), width=5)
    btn1.pack(side=tk.LEFT, padx=10)
    btn2 = tk.Button(btn_frame, text="2", command=lambda: run_background_task(url, "codewebback", btn_frame), width=5)
    btn2.pack(side=tk.RIGHT, padx=10)


def open_settings():
    settings_win = tk.Toplevel(root)
    settings_win.title("Settings")
    settings_win.geometry("400x300")
    settings_win.configure(bg="black")
    tk.Label(settings_win, text="Settings", bg="black", fg="lime", font=("Courier", 14)).pack(pady=10)
    tk.Button(settings_win, text="Light Theme", bg="#0f5132", fg="white", font=("Courier", 10, "bold"),
              command=set_light_theme).pack(pady=5)
    tk.Button(settings_win, text="Dark Theme", bg="#0f5132", fg="white", font=("Courier", 10, "bold"),
              command=set_dark_theme).pack(pady=5)
    tk.Button(settings_win, text="Toggle Truncate Backend Code", bg="#0f5132", fg="white", font=("Courier", 10, "bold"),
              command=toggle_truncation).pack(pady=5)


def clear_output():
    output.delete(1.0, tk.END)


def clear_logs():
    log_path = os.path.expanduser("~/activity.log")
    if os.path.exists(log_path):
        os.remove(log_path)
    if os.path.exists("crash_log.txt"):
        os.remove("crash_log.txt")
    global crash_log
    crash_log = []
    typewriter("All logs cleared. Starting a fresh journey!", output)


def process_command(url):
    global copy_button
    try:
        cmd = entry.get().replace(f"{url}> ", "").strip()
        output.delete(1.0, tk.END)
        setup_copy_button()
        if cmd == "analyze stream":
            typewriter(analyze_stream(url), output)
        elif cmd == "codewebfront":
            typewriter(get_frontend_code(url), output)
            add_copy_button()
        elif cmd == "codewebback":
            typewriter(get_backend_code(url), output)
            add_copy_button()
        elif cmd == "deldo":
            setup_initial_screen()
            return
        elif cmd == "pause":
            typewriter("Output paused. Hit Enter to continue.", output)
            entry.wait_variable(tk.StringVar())
        elif cmd == "about":
            typewriter("nextdomain v3.1211 - Created by Aryan Wankhede", output)
            typewriter("Website: web.nxtinstant.in", output)
        elif cmd == "update":
            download_update()
        elif cmd == "help":
            typewriter(display_help(), output)
        elif cmd == "secret1211":
            password = simpledialog.askstring("verify that you are Aryan", "Enter password:", show='A')
            if password == "1211":
                typewriter("Welcome, Aryan! Sending all possible requests...", output)
                typewriter(send_requests(url), output)
            else:
                typewriter("Incorrect password!", output)
        elif cmd == "chatpost":
            open_chat_post()
        elif cmd == "runfile":
            output_text = run_file()
            typewriter(output_text, output)
        elif cmd == "logconsole":
            open_log_console()
        elif cmd == "exitconsole":
            close_log_console()
        elif cmd == "crashlog":
            if crash_log:
                typewriter("=== Crash & Bug Log ===", output)
                for log_entry in crash_log[-10:]:
                    typewriter(f"[{log_entry['time']}] {log_entry['error']}", output)
                typewriter(f"\nTotal crashes handled: {len(crash_log)}", output)
            else:
                typewriter("No crashes detected. System running smoothly!", output)
        elif cmd == "rethack":
            matrix_text = ("developers are the best")
            type_matrix_text(output, matrix_text)
        elif cmd == "activitylog":
            show_activity_log()
        elif cmd == "addshortcut":
            create_shortcut()
        elif cmd == "runbackground":
            runbackground_command(url)
        elif cmd == "settings":
            open_settings()
        elif cmd == "clear":
            clear_output()
        elif cmd == "clearlog":
            clear_logs()
        elif cmd == "fetchtext":
            typewriter("Fetching text from URL...", output)
            text = fetch_text(url)
            typewriter(text, output)
        elif cmd == "exit":
            typewriter("exiting server nxtinstant closed...", output)
            root.quit()
        else:
            typewriter("Error: Invalid command. Type 'help' for options.", output)
        entry.delete(0, tk.END)
        entry.insert(0, f"{url}> ")
    except Exception as e:
        log_crash(f"Process command error: {str(e)}")
        typewriter("Error processing command. System continuing safely.", output)
        try:
            entry.delete(0, tk.END)
            entry.insert(0, f"{url}> ")
        except:
            pass


def setup_initial_screen():
    try:
        output.delete(1.0, tk.END)
        load_theme()
        version_text = "Nextdomain v3.1211 - Matrix Style Scanner"
        try:
            with open("version_info.txt", "r") as f:
                dropbox_version = f.read().strip()
                version_text += f"\n{dropbox_version}"
        except FileNotFoundError:
            pass
        except Exception as e:
            log_crash(f"Version info read error: {str(e)}")
        typewriter(version_text, output)
        typewriter(">" * 25, output)
        entry.delete(0, tk.END)
        entry.insert(0, "https://")
        entry.config(state=tk.NORMAL)
        entry.focus_set()
        entry.bind("<Return>", lambda e: threading.Thread(target=process_initial_input).start())
    except Exception as e:
        log_crash(f"Setup initial screen error: {str(e)}")
        try:
            output.insert(tk.END, "Nextdomain v3.1211 - Matrix Style Scanner\n")
            entry.delete(0, tk.END)
            entry.insert(0, "https://")
            entry.focus_set()
            entry.bind("<Return>", lambda e: threading.Thread(target=process_initial_input).start())
        except:
            pass


root = tk.Tk()
root.title("nextdomain part 2")
root.geometry("800x600")
root.configure(bg="black")


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_crash(f"Uncaught exception: {error_msg}")
    try:
        if output and output.winfo_exists():
            output.insert(tk.END, f"\n[System] Error handled. Continuing safely...\n")
    except:
        pass


sys.excepthook = handle_exception


output = tk.Text(root, bg="black", fg="green", font=("Courier", 12), wrap=tk.WORD)
output.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)


entry = tk.Entry(root, bg="black", fg="green", font=("Courier", 12), insertbackground="green")
entry.pack(fill=tk.X, padx=5, pady=5)


style = ttk.Style()
style.theme_use('clam')
style.configure("TButton", foreground="white", background="#0f5132", font=("Courier", 10, "bold"), padding=5)
style.map("TButton", background=[('active', '#14532d'), ('!active', '#0f5132')])


progress_bar = ttk.Progressbar(root, mode="indeterminate")
progress_bar.pack(fill=tk.X, padx=5, pady=5)


setup_initial_screen()


root.mainloop()
