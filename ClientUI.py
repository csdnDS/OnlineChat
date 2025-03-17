# FileName : Client.py
# 在线聊天客户端
import sys
import tkinter
import tkinter.font as tkFont
import socket
import threading
import time


class ClientUI:
    local = '127.0.0.1'
    port = 5505
    flag = False   # 连接状态标记

    def __init__(self):
        self.root = tkinter.Tk()   # 创建主窗口
        self.root.title('Python在线聊天-客户端')   # 设置窗口标题
        self.clientSock = None   # 客户端Socket对象

        # 窗口面板：用4个Frame划分不同区域
        self.frame = [
            tkinter.Frame(),  # 0-消息显示区
            tkinter.Frame(),  # 1-分隔区
            tkinter.Frame(),  # 2-输入区
            tkinter.Frame()  # 3-按钮区
        ]

        # 消息显示区域配置
        self.chatTextScrollBar = tkinter.Scrollbar(self.frame[0])
        self.chatTextScrollBar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        ft = tkFont.Font(family='Fixdsys', size=11)
        self.chatText = tkinter.Text(self.frame[0], width=70, height=18, font=ft,wrap=tkinter.WORD)   # 设置文本框大小、字体样式、换行方式
        self.chatText.pack(expand=1, fill=tkinter.BOTH)

        self.chatText['yscrollcommand'] = self.chatTextScrollBar.set   # 当文本框垂直滚动时,调用滚动条的set()方法，从而更新滚动条滑块的位置
        self.chatTextScrollBar['command'] = self.chatText.yview        # 当用户拖动滚动条时，调用文本框的yview()方法，控制文本框显示的内容区域

        # 配置左右消息样式
        self.chatText.tag_configure('right', justify='right', spacing3=5)
        self.chatText.tag_configure('left', justify='left', spacing3=5)

        self.frame[0].pack(expand=1, fill=tkinter.BOTH)     # 使得聊天消息区域会随着窗口大小调整自动扩展，始终占满界面中部区域

        # 分隔标签
        tkinter.Label(self.frame[1], height=1).pack(fill=tkinter.BOTH)
        self.frame[1].pack(expand=1, fill=tkinter.BOTH)

        # 消息输入区域配置
        self.inputTextScrollBar = tkinter.Scrollbar(self.frame[2])
        self.inputTextScrollBar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        ft = tkFont.Font(family='Fixdsys', size=11)
        self.inputText = tkinter.Text(self.frame[2], width=70, height=8, font=ft, wrap=tkinter.WORD)
        self.inputText.pack(expand=1, fill=tkinter.BOTH)

        self.inputText['yscrollcommand'] = self.inputTextScrollBar.set
        self.inputTextScrollBar['command'] = self.inputText.yview

        self.frame[2].pack(expand=1, fill=tkinter.BOTH)

        # 按钮区域
        self.sendButton = tkinter.Button(self.frame[3], text='发送', width=10, command=self.sendMessage)
        self.sendButton.pack(side=tkinter.RIGHT, padx=25, pady=5)
        self.closeButton = tkinter.Button(self.frame[3], text='关闭', width=10, command=self.close)
        self.closeButton.pack(side=tkinter.RIGHT, padx=25, pady=5)
        self.frame[3].pack(expand=1, fill=tkinter.BOTH)

        self.inputText.bind("<Return>", self.enter_send)
        self.inputText.bind("<Shift-Return>", self.newline)

        # 连接服务器
        self.connect_server()


    def enter_send(self, event):
        """回车发送消息"""
        self.sendMessage()
        return "break"


    def newline(self, event):
        """Shift+回车换行"""
        self.inputText.insert(tkinter.INSERT, '\n')
        return "break"


    def connect_server(self):
        try:
            self.clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.clientSock.connect((self.local, self.port))   #   连接到服务器的端口
            self.flag = True   #   更新连接状态
            self.update_display("成功连接到服务器\n", tag='left')
            threading.Thread(target=self.receiveMessage, daemon=True).start()
        except Exception as e:
            self.update_display(f"连接失败: {str(e)}\n", tag='error')
            self.flag = False


    def update_display(self, message, tag='normal'):
        self.chatText.config(state='normal')
        theTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        if tag == 'right':  # 客户端发送的消息
            self.chatText.insert(tkinter.END, f'我 {theTime} 说：\n{message}\n\n', 'right')
        elif tag == 'left':  # 接收的服务器消息
            self.chatText.insert(tkinter.END, f'服务器 {theTime} 说：\n{message}\n\n', 'left')
        elif tag == 'error':
            self.chatText.insert(tkinter.END, f'[错误] {theTime} {message}\n', 'error')

        self.chatText.config(state='disabled')
        self.chatText.see(tkinter.END)


    def receiveMessage(self):
        while self.flag:
            try:
                data = self.clientSock.recv(1024).decode('utf-8')
                if not data:
                    break
                self.update_display(data, tag='left')  # 服务器消息左对齐
            except Exception as e:
                self.update_display(f"接收错误: {str(e)}\n", tag='error')
                break
        self.flag = False


    def sendMessage(self):
        message = self.inputText.get('1.0', tkinter.END).strip()   # 获取输入内容，从第一个字符到结尾
        if not message:   # 空消息不发送
            return
        # 显示在右侧
        self.update_display(message, tag='right')  # 客户端消息右对齐

        # 尝试发送消息给服务器端
        if self.flag and self.clientSock:   # 检查连接状态
            try:
                self.clientSock.send(message.encode('utf-8'))    # 转换为字符流发送
            except Exception as e:
                self.update_display(f"发送失败: {str(e)}\n", tag='error')
                self.flag = False   # 更新连接状态
        else:
            self.update_display("未连接到服务器，消息未发送\n", tag='error')

        self.inputText.delete('1.0', tkinter.END)   # 清空输入框


    def close(self):
        if self.clientSock:
            self.clientSock.close()
        self.root.destroy()
        sys.exit()


def main():
    client = ClientUI()
    client.root.mainloop()


if __name__ == '__main__':
    main()