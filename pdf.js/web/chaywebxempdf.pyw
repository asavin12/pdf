import customtkinter as ctk
import subprocess
import webbrowser
import os
import signal
import time
import psutil
from threading import Thread
import ctypes  # Thêm cho Windows taskbar icon

class ServerTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Công cụ Server")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Thiết lập biểu tượng
        self.set_icon()
        
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        self.server_process = None
        self.is_running = False
        self.PORT = 8000
        
        # Frame chính
        self.main_frame = ctk.CTkFrame(root, corner_radius=10)
        self.main_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Tiêu đề
        self.title_label = ctk.CTkLabel(
            self.main_frame, 
            text="Server Control",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.pack(pady=(10, 5))
        
        # Frame chứa các nút
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(pady=5)
        
        # Nút Start
        self.start_button = ctk.CTkButton(
            self.button_frame,
            text="Chạy",
            command=self.start_server,
            width=80,
            height=30,
            font=ctk.CTkFont(size=12)
        )
        self.start_button.pack(side="left", padx=5)
        
        # Nút Stop
        self.stop_button = ctk.CTkButton(
            self.button_frame,
            text="Tắt",
            command=self.stop_server,
            width=80,
            height=30,
            font=ctk.CTkFont(size=12),
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)
        
        # Nút Homepage
        self.home_button = ctk.CTkButton(
            self.button_frame,
            text="Trang Chủ",
            command=self.open_homepage,
            width=80,
            height=30,
            font=ctk.CTkFont(size=12),
            state="disabled"
        )
        self.home_button.pack(side="left", padx=5)
        
        # Frame trạng thái
        self.status_frame = ctk.CTkFrame(self.main_frame, corner_radius=5)
        self.status_frame.pack(pady=10, padx=10, fill="x")
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Trạng thái: Chưa chạy",
            wraplength=350,
            justify="center",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
        
        # Thông tin địa chỉ
        self.info_label = ctk.CTkLabel(
            self.main_frame,
            text=f"Địa chỉ: http://localhost:{self.PORT}",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.info_label.pack(pady=5)
        
        # Nút chuyển đổi theme
        self.theme_switch = ctk.CTkSwitch(
            self.main_frame,
            text="Dark Mode",
            command=self.toggle_theme,
            onvalue="Dark",
            offvalue="Light",
            font=ctk.CTkFont(size=12)
        )
        self.theme_switch.pack(pady=5)
    
    def set_icon(self):
        """Thiết lập biểu tượng cho chương trình"""
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
                if os.name == 'nt':
                    app_id = "ServerwebPDF"  # ID duy nhất cho ứng dụng
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            except Exception as e:
                print(f"Không thể tải biểu tượng: {e}")
        else:
            print(f"Không tìm thấy tệp biểu tượng tại: {icon_path}")
    
    def update_status(self, message, color="gray"):
        self.status_label.configure(text=f"Trạng thái: {message}", text_color=color)
        
    def toggle_theme(self):
        ctk.set_appearance_mode(self.theme_switch.get())
        
    def find_process_by_port(self, port):
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr and conn.laddr.port == port and conn.pid is not None:
                    return conn.pid
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
        return None
    
    def kill_process_by_pid(self, pid):
        if pid:
            try:
                if os.name == "nt":
                    os.system(f"taskkill /PID {pid} /F")
                else:
                    os.system(f"kill -9 {pid}")
                time.sleep(1)
                return True
            except Exception as e:
                self.update_status(f"Lỗi khi kill PID {pid}: {str(e)}", "orange")
                return False
        return False
    
    def start_server(self):
        if not self.is_running:
            pid = self.find_process_by_port(self.PORT)
            if pid:
                self.update_status(f"Cổng {self.PORT} đang bị chiếm bởi PID {pid}", "red")
                self.kill_process_by_pid(pid)
                time.sleep(1)
            
            try:
                self.server_process = subprocess.Popen(
                    ["python", "-m", "http.server", str(self.PORT)],
                    cwd=os.getcwd(),
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False
                )
                
                time.sleep(1)
                if self.server_process.poll() is not None:
                    raise Exception("Server không thể khởi động")
                
                self.is_running = True
                self.update_status(f"Server chạy trên cổng {self.PORT}", "green")
                
                self.start_button.configure(state="disabled")
                self.stop_button.configure(state="normal")
                self.home_button.configure(state="normal")
                
                Thread(target=self.monitor_server, daemon=True).start()
                
            except Exception as e:
                self.update_status(f"Lỗi: {str(e)}", "red")
                self.server_process = None
                self.is_running = False
    
    def stop_server(self):
        if self.is_running or self.server_process:
            try:
                if self.server_process and self.server_process.poll() is None:
                    if os.name == 'nt':
                        self.server_process.terminate()
                    else:
                        self.server_process.send_signal(signal.SIGTERM)
                    self.server_process.wait(timeout=5)
                
                pid = self.find_process_by_port(self.PORT)
                if pid:
                    self.update_status(f"Tắt PID {pid} trên cổng {self.PORT}", "orange")
                    self.kill_process_by_pid(pid)
                
                self.server_process = None
                self.is_running = False
                self.update_status("Server đã dừng", "green")
                
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.home_button.configure(state="disabled")
                
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                pid = self.find_process_by_port(self.PORT)
                if pid:
                    self.kill_process_by_pid(pid)
                self.server_process = None
                self.is_running = False
                self.update_status("Server buộc dừng", "green")
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.home_button.configure(state="disabled")
            except Exception as e:
                self.update_status(f"Lỗi khi dừng: {str(e)}", "orange")
                pid = self.find_process_by_port(self.PORT)
                if pid:
                    self.kill_process_by_pid(pid)
                self.server_process = None
                self.is_running = False
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.home_button.configure(state="disabled")
        else:
            pid = self.find_process_by_port(self.PORT)
            if pid:
                self.update_status(f"Tắt PID {pid} trên cổng {self.PORT}", "orange")
                self.kill_process_by_pid(pid)
                self.update_status("Đã giải phóng cổng", "green")
            else:
                self.update_status("Không có server chạy!", "red")
    
    def monitor_server(self):
        while self.is_running and self.server_process:
            if self.server_process.poll() is not None:
                self.is_running = False
                self.root.after(0, lambda: self.update_status("Server dừng bất ngờ", "red"))
                self.root.after(0, lambda: self.start_button.configure(state="normal"))
                self.root.after(0, lambda: self.stop_button.configure(state="disabled"))
                self.root.after(0, lambda: self.home_button.configure(state="disabled"))
                break
            time.sleep(1)
    
    def open_homepage(self):
        if self.is_running and self.server_process.poll() is None:
            webbrowser.open(f"http://localhost:{self.PORT}/viewer.html")
            self.update_status("Đã mở trang chủ", "green")
        else:
            self.update_status("Server không chạy!", "red")

if __name__ == "__main__":
    root = ctk.CTk()
    app = ServerTool(root)
    root.mainloop()
