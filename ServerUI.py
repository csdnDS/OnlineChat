# FileName : ServerUI.py
# 在线聊天服务器端
import sys
import tkinter  # GUI库
import tkinter.font as tkFont   # 字体模块
import socket
import threading
import time


class ServerUI:
    local = '127.0.0.1'
    # local = '192.168.0.102'   #  用于实现不同主机之间通信
    port = 5505
    flag = False   # 连接状态标记

    def __init__(self):
        self.root = tkinter.Tk()   # 创建主窗口
        self.root.title('Python 在线聊天--服务器端')   # 设置窗口标题
        self.connection = None   # 客户端连接对象
        self.serverSock = None   # 服务器Socket对象

        # 窗口面板：用4个Frame划分不同区域
        self.frame = [
            tkinter.Frame(),   # 0-消息显示区
            tkinter.Frame(),   # 1-分隔区
            tkinter.Frame(),   # 2-输入区
            tkinter.Frame()    # 3-按钮区
        ]

        # 消息显示区域配置
        self.chatTextScrollBar = tkinter.Scrollbar(self.frame[0])   # 创建滚动条放置在frame[0]
        self.chatTextScrollBar.pack(side=tkinter.RIGHT, fill=tkinter.Y)   # 将滚动条靠右放置，竖直填充
        ft = tkFont.Font(family='Fixdsys', size=11, )  #字体样式设置
        self.chatText = tkinter.Text(self.frame[0], width=70, height=18, font=ft, wrap=tkinter.WORD)   # 创建文本框组件，指定宽度、高度、字体和换行方式（当超过文本框长度时自动按单词换行）
        self.chatText.pack(expand=1, fill=tkinter.BOTH)  # 将消息显示框撑满窗口容器

        # 配置左右消息样式
        self.chatText.tag_configure('right', justify='right', spacing3=5)
        self.chatText.tag_configure('left', justify='left', spacing3=5)

        self.chatText['yscrollcommand'] = self.chatTextScrollBar.set   # 当文本框垂直滚动时,调用滚动条的set()方法，从而更新滚动条滑块的位置
        self.chatTextScrollBar['command'] = self.chatText.yview        # 当用户拖动滚动条时，调用文本框的yview()方法，控制文本框显示的内容区域

        self.frame[0].pack(expand=1, fill=tkinter.BOTH)   # 使得聊天消息区域会随着窗口大小调整自动扩展，始终占满界面中部区域

        # 分隔标签
        tkinter.Label(self.frame[1], height=1).pack(fill=tkinter.BOTH)
        self.frame[1].pack(expand=1, fill=tkinter.BOTH)   

        # 消息输入区域配置（与消息显示区域基本类似）
        self.inputTextScrollBar = tkinter.Scrollbar(self.frame[2])
        self.inputTextScrollBar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        ft = tkFont.Font(family='Fixdsys', size=11)
        self.inputText = tkinter.Text(self.frame[2], width=70, height=8, font=ft, wrap=tkinter.WORD)
        self.inputText.pack(expand=1, fill=tkinter.BOTH)

        self.inputText['yscrollcommand'] = self.inputTextScrollBar.set   #  同消息显示区域，绑定输入框和滚动条相对位置
        self.inputTextScrollBar['command'] = self.inputText.yview

        self.frame[2].pack(expand=1, fill=tkinter.BOTH)

        # 按钮区域
        self.sendButton = tkinter.Button(self.frame[3], text='发送', width=10, command=self.sendMessage)
        self.sendButton.pack(side=tkinter.RIGHT, padx=25, pady=5)
        self.closeButton = tkinter.Button(self.frame[3], text='关闭', width=10, command=self.close)
        self.closeButton.pack(side=tkinter.RIGHT, padx=25, pady=5)
        self.frame[3].pack(expand=1, fill=tkinter.BOTH)

        self.inputText.bind("<Return>", self.enter_send)   # 回车发送消息
        self.inputText.bind("<Shift-Return>", self.newline)   # Shift+回车换行

    def enter_send(self, event):
        """回车发送消息"""
        self.sendMessage()
        return "break"

    def newline(self, event):
        """Shift+回车换行"""
        self.inputText.insert(tkinter.INSERT, '\n')
        return "break"


    def update_display(self, message, tag='normal'):
        self.chatText.config(state='normal')
        theTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        if tag == 'right':  # 服务器端发送的消息
            self.chatText.insert(tkinter.END, f'我 {theTime} 说：\n{message}\n\n', 'right')
        elif tag == 'left':  # 接收的客户端消息
            self.chatText.insert(tkinter.END, f'客户端 {theTime} 说：\n{message}\n\n', 'left')
        elif tag == 'error':
            self.chatText.insert(tkinter.END, f'[错误] {theTime} {message}\n', 'error')

        self.chatText.config(state='disabled')
        self.chatText.see(tkinter.END)


    def sendMessage(self):
        message = self.inputText.get('1.0', tkinter.END).strip()  # 获取输入内容，从第一个字符到结尾
        if not message:   # 空消息不发送
            return
        self.update_display(message, tag='right')

        # 尝试发送消息给客户端
        if self.flag and self.connection:   # 检查连接状态
            try:
                self.connection.send(message.encode('utf-8'))   # 转换为字符流发送
            except Exception as e:
                self.update_display(f'发送失败：{str(e)}\n', 'error')
                self.flag = False   # 更新连接状态
        else:
            self.update_display('未与客户端建立连接，消息未发送\n', 'error')

        self.inputText.delete('1.0', tkinter.END)   # 清空输入框

    def receiveMessage(self):
        self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # 创建TCP Socket
        try:
            self.serverSock.bind((self.local, self.port))   # 绑定IP地址和端口
            self.serverSock.listen(5)   # 监听，最大连接数为5
            self.update_display("服务器已启动，等待客户端连接...\n", 'left')
            self.connection, addr = self.serverSock.accept()   # 接受客户端连接
            self.flag = True   # 标记为已连接状态
            self.update_display(f"客户端 {addr} 已连接\n", 'left')

            while True:   # 持续接收消息
                try:
                    data = self.connection.recv(1024).decode('utf-8')   # 接收数据
                    if not data:   # 空数据跳出循环
                        break
                    self.update_display(data, tag='left')
                except Exception as e:
                    self.update_display(f'接收错误：{str(e)}\n', 'error')
                    break
        except Exception as e:
            self.update_display(f'服务器错误：{str(e)}\n', 'error')
        finally:   # 修改标志，断开连接，关闭Socket
            self.flag = False
            if self.connection:
                self.connection.close()
            self.serverSock.close()

    def startNewThread(self):
        """启动新线程处理消息接收"""
        recv_thread = threading.Thread(target=self.receiveMessage)
        recv_thread.daemon = True   # 设置为守护线程（主程序退出时自动结束）
        recv_thread.start()

    def close(self):
        if self.connection:
            self.connection.close()   # 断开客户端连接
        if self.serverSock:
            self.serverSock.close()   # 关闭服务器Socket
        self.root.destroy()    # 销毁窗口
        sys.exit()    #退出程序


def main():
    server = ServerUI()
    server.startNewThread()
    server.root.mainloop()


if __name__ == '__main__':
    main()