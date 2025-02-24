import tkinter as tk
from tkinter import simpledialog, messagebox
from openai import OpenAI
import os
import json
from threading import Thread

# Constants
CONTEXT_WINDOW_SIZE = 4
SESSION_DIR = "D:/GPTASSISTANT/sessions"
CONFIG_FILE = "D:/GPTASSISTANT/config.json"
API_KEY=""
BASE_URL=""
BASE_TEMPERATURE=0.7
os.makedirs(SESSION_DIR, exist_ok=True)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            config["OPENAI_API_KEY"] = config.get("OPENAI_API_KEY", "").strip()  # 去除末尾的换行和空格
            config["OPENAI_BASE_URL"] = config.get("OPENAI_BASE_URL", "https://api.openai.com/v1/").strip()  # 去除末尾的换行和空格
            return config
    return {"OPENAI_API_KEY": "", "OPENAI_BASE_URL": ""}

config = load_config()
API_KEY = config.get("OPENAI_API_KEY", "sk-xxxxxxxx")  # 默认值为占位符
BASE_URL= config.get("OPENAI_BASE_URL","https://api.openai.com/v1/")  # 默认值为占位符

# 设置API客户端
client = OpenAI(
    # api_key=os.environ.get("OPENAI_API_KEY"),  # 从环境变量中获取API密钥
    # base_url=os.environ.get("OPENAI_BASE_URL")  # 从环境变量中获取API基本URL
    api_key=API_KEY,
    base_url=BASE_URL
)


class ChatGPTGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ChatGPT GUI")
        self.geometry("600x400")
        self.minsize(400, 300)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.attributes("-topmost", True)

        self.session_file = None
        self.history = []
        self.context_window = []

        self.create_widgets()
        self.create_menu()  
        self.load_session()

    def create_widgets(self):
        self.text_display = tk.Text(self, wrap=tk.WORD)
        self.text_display.pack(expand=True, fill=tk.BOTH)

        self.entry = tk.Entry(self)
        self.entry.pack(fill=tk.X)
        self.entry.bind("<Return>", self.on_enter)

        self.send_button = tk.Button(self, text="Send", command=self.on_enter)
        self.send_button.pack()

    def create_menu(self):  
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Set API Key", command=self.set_api_key)
        settings_menu.add_command(label="Set BASE URL", command=self.set_base_url)
        settings_menu.add_command(label="Set Temperature", command=self.set_temperature)
    
    def set_api_key(self):  
        new_api_key = simpledialog.askstring("Set API Key", "Enter new API Key:")
        if new_api_key:
            new_api_key = new_api_key.strip()  
            config["OPENAI_API_KEY"] = new_api_key  
            with open(CONFIG_FILE, "w") as f: 
                json.dump(config, f)
            messagebox.showinfo("Info", "API Key updated. Please restart the application to apply changes.")

    def set_base_url(self):  # 修改：新增的函数
        new_base_url = simpledialog.askstring("Set base url", "Enter new base url:")
        if new_base_url:
            new_base_url = new_base_url.strip()  
            config["OPENAI_BASE_URL"] = new_base_url 
            with open(CONFIG_FILE, "w") as f: 
                json.dump(config, f)
            messagebox.showinfo("Info", "Base URL updated. Please restart the application to apply changes.")

    def set_temperature(self):  # 修改：新增的函数
        global BASE_TEMPERATURE
        new_temperature = simpledialog.askstring("Set temperature", "Enter new temperature:")
        if new_temperature:
            new_temperature = new_temperature.strip()  
            try:
                BASE_TEMPERATURE = float(new_temperature)  # 将字符串转换为浮点数
                messagebox.showinfo("Info", "Temperature has changed.")
            except ValueError:
                messagebox.showerror("Error", "Invalid temperature value. Please enter a numeric value.")


    def load_session(self):
        session_files = [f for f in os.listdir(SESSION_DIR) if f.endswith(".json")]
        
        # 添加一个新会话的选项
        session_files.insert(0, "Create New Session")
        
        # 使用弹出窗口显示可用的会话文件
        dialog = tk.Toplevel(self)
        dialog.title("Load Session")

        listbox = tk.Listbox(dialog, selectmode=tk.SINGLE)
        for session_file in session_files:
            listbox.insert(tk.END, session_file)
        listbox.pack(padx=10, pady=10)

        def on_select():
            selected_file = listbox.get(tk.ACTIVE)
            if selected_file == "Create New Session":
                self.session_file = None  # 新会话
                self.history = []
                self.text_display.delete(1.0, tk.END)
                self.context_window = []
                self.save_session()  # 保存新会话文件
            elif selected_file:
                self.session_file = os.path.join(SESSION_DIR, selected_file)
                if os.path.exists(self.session_file):
                    with open(self.session_file, "r") as f:
                        self.history = json.load(f)
                    for message in self.history:
                        self.text_display.insert(tk.END, f"{message['role']}: {message['content']}\n")
                    self.context_window = self.history[-CONTEXT_WINDOW_SIZE:]
            dialog.destroy()

        load_button = tk.Button(dialog, text="Load", command=on_select)
        load_button.pack(pady=10)

        cancel_button = tk.Button(dialog, text="Cancel", command=dialog.destroy)
        cancel_button.pack()

        dialog.transient(self)
        dialog.grab_set()
        self.wait_window(dialog)


    def on_enter(self, event=None):
        user_input = self.entry.get()
        if user_input:
            self.add_message("user", user_input)
            self.entry.delete(0, tk.END)
            self.generate_response(user_input)

    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})
        self.context_window.append({"role": role, "content": content})
        if len(self.context_window) > CONTEXT_WINDOW_SIZE:
            self.context_window.pop(0)
        self.text_display.insert(tk.END, f"{role}: {content}\n")
        self.text_display.see(tk.END)

    def generate_response(self, user_input):
        def async_generate():
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=self.context_window,
                    temperature=BASE_TEMPERATURE,
                    stream=True
                )

                response_content = ""
                self.text_display.insert(tk.END, "ChatGPT:")
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        chunk_content=chunk.choices[0].delta.content
                        response_content += chunk_content
                        self.text_display.insert(tk.END, chunk_content)
                        self.text_display.see(tk.END)
                self.text_display.insert(tk.END,"\n")
                

                self.history.append({"role": "assistant", "content": response_content})
                self.context_window.append({"role": "assistant", "content": response_content})
                if len(self.context_window) > CONTEXT_WINDOW_SIZE:
                    self.context_window.pop(0)
                self.save_session()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        Thread(target=async_generate).start()

    def format_prompt(self):
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.context_window])

    def save_session(self):
        if not self.session_file:
            self.session_file = os.path.join(SESSION_DIR, simpledialog.askstring("Save Session", "Enter session name:") + ".json")
        with open(self.session_file, "w") as f:
            json.dump(self.history, f)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.save_session()
            self.destroy()

if __name__ == "__main__":
    app = ChatGPTGUI()
    app.mainloop()
