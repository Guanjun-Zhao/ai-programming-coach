"""
程序入口：启动 Qt 界面事件循环，创建并显示主窗口。

初学者可以这样理解：
1. PyQt 程序必须先有一个 QApplication（管理全局事件、字体等）。
2. 窗口要 .show() 才会出现在屏幕上。
3. app.exec() 进入「事件循环」，直到用户关闭窗口才结束；最后 sys.exit 把退出码交给操作系统。
"""

from __future__ import annotations

# sys.argv：命令行参数列表（第 0 项是脚本名）；Qt 有时用它解析显示相关选项
import sys

# QApplication：整个图形界面程序的「总管家」，必须有且通常只有一个
from PyQt6.QtWidgets import QApplication

# 自定义的主窗口类，定义在 main_window.py 里
from main_window import MainWindow


def main() -> None:
    # 把命令行参数传给 Qt（骨架项目里参数通常只有脚本路径）
    app = QApplication(sys.argv)
    # 构造主窗口对象（内部会搭界面，但此时还未显示）
    win = MainWindow()
    # 非模态显示：窗口出现在桌面上
    win.show()
    # exec() 阻塞在这里，处理鼠标键盘绘制等事件；关闭所有窗口后返回整数退出码
    sys.exit(app.exec())


# 只有「直接运行 python main.py」时才执行 main()；
# 若别的文件 import main，则不会自动弹窗（方便以后写测试）
if __name__ == "__main__":
    main()
