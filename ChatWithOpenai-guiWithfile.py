import openai
import os
# 设置 OPENAI_API_KEY 环境变量
os.environ["OPENAI_API_KEY"] = "sk-xxxxxxxx"
# 设置 OPENAI_BASE_URL 环境变量
os.environ["OPENAI_BASE_URL"] = "https://api.xiaoai.plus/v1"
import json
import tkinter as tk
from tkinter import scrolledtext, filedialog
from tkinter import ttk
from requests.exceptions import Timeout

def save_session_data(session_data, file_path='session_data.json'):
    with open(file_path, 'w') as file:
        json.dump(session_data, file)

def load_session_data(file_path='session_data.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        return {}

def chat_with_gpt(prompt, client, session_id, session_data):
    session_data[session_id]["messages"].append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=session_data[session_id]["messages"]
        )
    except Timeout as e:
        return "请求超时，请检查网络连接或稍后重试。"
    except openai.error.OpenAIError as e:
        return f"OpenAI API 错误: {e}"
    except Exception as e:
        return f"其他错误: {e}"

    message = response.choices[0].message.content
    session_data[session_id]["messages"].append({"role": "assistant", "content": message})
    save_session_data(session_data)
    return message

def select_session(session_data):
    if session_data:
        print("可用会话列表:")
        for session_id in session_data.keys():
            print(f"会话 {session_id}:上有 {len(session_data[session_id]['messages'])} 条消息")
        session_id = input("输入会话ID或 'new' 开始新会话: ")
        if session_id.lower() == 'new' or session_id not in session_data:
            session_id = str(max([int(sid) for sid in session_data.keys()], default=0) + 1)
            session_data[session_id] = {"messages": []}
    else:
        print("开始新的会话。")
        session_id = "1"
        session_data[session_id] = {"messages": []}
    return session_id

def load_chat_history(session_id, session_data):
    if session_id in session_data and session_data[session_id]["messages"]:
        for message in session_data[session_id]["messages"]:
            role = "You" if message["role"] == "user" else "ChatGPT"
            chat_history.config(state=tk.NORMAL)
            chat_history.insert(tk.END, f"{role}: {message['content']}\n")
            chat_history.config(state=tk.DISABLED)

def send_message():
    prompt = user_input.get("1.0", tk.END).strip()
    if prompt:
        # 检查是否有附件内容
        attachment_text = attachment_content.get().strip()
        if attachment_text:
            prompt += f"\n\n{attachment_text}"
            attachment_content.set("")  # 清空附件内容
        
        response = chat_with_gpt(prompt, client, session_id, session_data)
        chat_history.config(state=tk.NORMAL)
        chat_history.insert(tk.END, "You: " + prompt + "\n")
        chat_history.insert(tk.END, "ChatGPT: " + response + "\n\n")
        chat_history.config(state=tk.DISABLED)
        user_input.delete("1.0", tk.END)

def add_attachment():
    file_path = filedialog.askopenfilename()
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as file:
            file_content = file.read()
        attachment_content.set(f"附件内容:\n{file_content}")
        chat_history.config(state=tk.NORMAL)
        chat_history.insert(tk.END, f"附件内容:\n{file_content}\n")
        chat_history.config(state=tk.DISABLED)

def on_closing():
    save_session_data(session_data)
    root.destroy()

# 设置API客户端
client = openai.OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),  # 从环境变量中获取API密钥
    base_url=os.environ.get("OPENAI_BASE_URL")  # 从环境变量中获取API基本URL
)

session_data = load_session_data()
session_id = select_session(session_data)

# 创建主窗口
root = tk.Tk()
root.title("ChatGPT 对话")

# 设置窗口可以拉伸
root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

# 创建主框架
main_frame = ttk.Frame(root, padding="10 10 10 10")
main_frame.grid(row=0, column=0, sticky=(tk.N, tk.W, tk.E, tk.S))

# 设置主框架可以拉伸
main_frame.rowconfigure(0, weight=1)
main_frame.columnconfigure(0, weight=1)

# 创建聊天记录窗口
chat_history = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, state=tk.DISABLED, width=80, height=20)
chat_history.grid(row=0, column=0, columnspan=2, sticky=(tk.N, tk.W, tk.E, tk.S))

# 设置聊天记录窗口可以拉伸
chat_history.rowconfigure(0, weight=1)
chat_history.columnconfigure(0, weight=1)

# 加载历史对话
load_chat_history(session_id, session_data)

# 创建用户输入框
user_input = tk.Text(main_frame, height=3, width=60)
user_input.grid(row=1, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))

# 创建发送按钮
send_button = ttk.Button(main_frame, text="发送", command=send_message)
send_button.grid(row=1, column=1, padx=5, pady=5, sticky=tk.E)

# 创建添加附件按钮
attachment_content = tk.StringVar()
attachment_button = ttk.Button(main_frame, text="添加附件", command=add_attachment)
attachment_button.grid(row=2, column=0, columnspan=2, pady=5, sticky=tk.W)

# 绑定关闭事件
root.protocol("WM_DELETE_WINDOW", on_closing)

# 运行主循环
root.mainloop()