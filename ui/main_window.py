import json
import os
import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QAction, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QFileDialog, QSizePolicy,
                             QHeaderView, QSpinBox, QProgressBar)
from PyQt5.QtCore import QThread, pyqtSignal, QFileInfo, QObject
from module.mainfunction import ConnectivityTestThread, \
    SpeedTestThread
from module.ReadWriteFile import read_channels_and_urls_from_file, write_fasttest_results_to_file
import threading
class MainWindow(QMainWindow):
    CONFIG_FILE = "config.json"

    def __init__(self):
        super().__init__()
        self.num_threads = 4  # 默认线程数量
        self.initUI()
        self.last_directory = ""  # 添加一个属性来保存上一次的目录
        self.channels_and_urls = []  # 初始化 channels_and_urls
        self.speed_test_thread = None  # 添加一个属性来保存 SpeedTestThread 实例
        self.thread = None  # 添加一个属性来保存 FastTestThread 实例
        self.speed_test_thread = None  # 添加一个属性来保存 SpeedTestThread 实例
        self.run_speedtest_after_fasttest = False  # 控制是否需要进行测速
        self.results = []
        self.lock = threading.Lock()
    def initUI(self):
        # 窗口配置
        self.setWindowTitle('IPTV检测工具V1.0')

        # 确定当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # 设置窗口图标
        # icon_path = os.path.join(current_dir, 'kenan.ico')
        # self.setWindowIcon(QIcon(icon_path))

        # 创建中央小部件并设置布局
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 第一行：打开文件按钮，检测进度，线程数量
        top_layout = QHBoxLayout()

        # 打开文件按钮
        open_button = QPushButton('打开文件', self)
        open_button.setFixedSize(90, 25)  # 调整按钮尺寸
        top_layout.addWidget(open_button)

        # 检测进度标签
        self.progress_label = QLabel('检测进度: 0/0 (0%)', self)
        top_layout.addWidget(self.progress_label)

        # 进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedSize(400, 20)  # 设置较长的进度条大小
        self.progress_bar.setRange(0, 100)  # 进度条范围为0到100
        self.progress_bar.setValue(0)  # 初始值为0
        top_layout.addWidget(self.progress_bar)

        # 添加一个小弹性空间，适当拉近进度条和线程数量
        top_layout.addStretch(10)

        # 线程数量标签
        thread_label = QLabel('线程数量:', self)
        top_layout.addWidget(thread_label)

        # 线程数量调节框
        self.thread_spinbox = QSpinBox(self)
        self.thread_spinbox.setRange(1, 20)  # 设置线程数量的范围
        self.thread_spinbox.setValue(self.num_threads)  # 设置初始值
        top_layout.addWidget(self.thread_spinbox)

        # 将这一行的布局添加到主布局中
        layout.addLayout(top_layout)

        # 链接显示区域
        link_display_label = QLabel('链接显示区域:', self)
        layout.addWidget(link_display_label)

        # 初始化表格
        self.table_widget = QTableWidget(0, 4, self)
        self.table_widget.setHorizontalHeaderLabels(['频道名', '链接', '状态', '速度'])
        layout.addWidget(self.table_widget)

        # 自适应列宽
        self.adjustTableColumns()

        # 日志显示区域
        log_display_label = QLabel('日志显示区域:', self)
        self.log_textedit = QTextEdit(self)
        layout.addWidget(log_display_label)
        layout.addWidget(self.log_textedit)

        # 结果预览框
        result_preview_label = QLabel('结果预览框:', self)
        self.result_textedit = QTextEdit(self)
        layout.addWidget(result_preview_label)
        layout.addWidget(self.result_textedit)

        # 按钮区域
        button_widget = QWidget(self)
        button_layout = QHBoxLayout(button_widget)

        fast_test_button = QPushButton('快速检测', self)
        speed_test_button = QPushButton('测速检测', self)
        save_button = QPushButton('保存结果', self)
        button_layout.addWidget(fast_test_button)
        button_layout.addWidget(speed_test_button)
        button_layout.addWidget(save_button)
        layout.addWidget(button_widget)

        # 设置窗口大小
        self.setGeometry(100, 100, 1500, 1200)
        # 设置窗口最小大小
        self.setMinimumSize(1500, 1200)

        # 连接按钮事件
        open_button.clicked.connect(self.openFile)
        fast_test_button.clicked.connect(self.fastTest)
        speed_test_button.clicked.connect(self.start_ft_speedTest)
        save_button.clicked.connect(self.saveResult)

    def adjustTableColumns(self):
        header = self.table_widget.horizontalHeader()
        # 设置列宽填充整个表格区域
        for i in range(self.table_widget.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        # 允许用户手动调整列宽
        header.setSectionResizeMode(QHeaderView.Interactive)

    def closeEvent(self, event):
        # Save settings before closing
        self.saveSettings()
        event.accept()

    def saveSettings(self):
        settings = {
            'window_geometry': self.saveGeometry().data().decode('latin1'),
            'window_state': self.saveState().data().decode('latin1'),
            'column_widths': [self.table_widget.columnWidth(i) for i in range(self.table_widget.columnCount())]
        }
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(settings, f)

    def loadSettings(self):
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, 'r') as f:
                settings = json.load(f)
                self.restoreGeometry(settings.get('window_geometry', b'').encode('latin1'))
                self.restoreState(settings.get('window_state', b'').encode('latin1'))

                # Restore column widths
                column_widths = settings.get('column_widths', [])
                for i, width in enumerate(column_widths):
                    self.table_widget.setColumnWidth(i, width)



    def initTable(self):
        self.table_widget.setRowCount(len(self.channels_and_urls))
        for row, (channel, url) in enumerate(self.channels_and_urls):
            self.table_widget.setItem(row, 0, QTableWidgetItem(channel))
            self.table_widget.setItem(row, 1, QTableWidgetItem(url))
            self.table_widget.setItem(row, 2, QTableWidgetItem('待检测'))
            self.table_widget.setItem(row, 3, QTableWidgetItem(''))

    def fastTest(self):
        self.num_threads = self.thread_spinbox.value()
        self.log_textedit.append(f"Starting fasttest tasks with {self.num_threads} threads...")

        self.thread = ConnectivityTestThread(self.channels_and_urls, self.num_threads)
        self.thread.result_signal1.connect(self.update_table_results_4_fasttest)
        self.thread.all_finished_signal1.connect(self.update_results)
        self.thread.log_signal1.connect(self.handle_log)
        # self.thread.finished_signal.connect(self.on_fasttest_finished)  # 连接到新的槽函数
        self.thread.start()

    # def on_fasttest_finished(self, results):
    #     print(f"ff Results received in on_fasttest_finished: {results}")  # 调试信息
    #     self.statusBar().showMessage('快速检测完成。请点击保存结果按钮以保存数据。')

    def on_fasttest_finished(self, results):
        self.num_threads = self.thread_spinbox.value()
        self.log_textedit.append(f"Starting speedtest tasks with {self.num_threads} threads...")

        filtered_channels_and_urls = [
            (channel_name, m3u8_url) for channel_name, m3u8_url, status, speed in results if status == "Yes"
        ]
        #print("fasttest pass and speed test start"+str(filtered_channels_and_urls))
        if filtered_channels_and_urls:
            self.speed_test_thread = SpeedTestThread(filtered_channels_and_urls, self.num_threads)
            self.speed_test_thread.result_signal2.connect(self.update_table_results_4_fasttest)
            self.speed_test_thread.log_signal2.connect(self.handle_log)
            self.speed_test_thread.all_finished_signal2.connect(self.update_results)  # 连接到新的槽函数
            self.speed_test_thread.start()
        else:
            self.log_textedit.append("没有状态为 'Yes' 的频道进行测速。")

    def start_ft_speedTest(self):
        self.num_threads = self.thread_spinbox.value()
        self.log_textedit.append(f"Starting fasttest tasks with {self.num_threads} threads...")

        self.thread = ConnectivityTestThread(self.channels_and_urls, self.num_threads)
        self.thread.result_signal1.connect(self.update_table_results_4_fasttest)
        self.thread.log_signal1.connect(self.handle_log)        
        self.thread.all_finished_signal1.connect(self.update_results)
        self.thread.all_finished_signal1.connect(self.on_fasttest_finished)  # 连接到新的槽函数
        self.thread.start()

    # def speedTest(self):
    #     if not hasattr(self, 'thread') or not self.thread.results:
    #         self.log_textedit.append('请先进行快速检测。')
    #         return

    #     self.num_threads = self.thread_spinbox.value()
    #     self.log_textedit.append(f"Starting speedtest tasks with {self.num_threads} threads...")

    #     filtered_channels_and_urls = [
    #         (channel_name, m3u8_url) for channel_name, m3u8_url, status, speed in self.thread.results if status == "Yes"
    #     ]
    #     print("fasttest pass and speed test start"+str(filtered_channels_and_urls))
    #     if filtered_channels_and_urls:
    #         self.log_textedit.append(f"Starting speedtest tasks with {self.num_threads} threads ...")
    #         self.speed_test_thread = SpeedTestThread(filtered_channels_and_urls, self.num_threads)
    #         self.speed_test_thread.result_signal.connect(self.handle_speedtest_result)
    #         self.speed_test_thread.log_signal.connect(self.handle_log)
    #         self.speed_test_thread.finished_signal.connect(self.on_speedtest_finished)  # 连接到新的槽函数
    #         self.speed_test_thread.start()
    #     else:
    #         self.log_textedit.append("没有状态为 'Yes' 的频道进行测速。")



    # def on_fasttest_finished2(self, results):
    #     print(f"ft2:fasttest Results received in on_fasttest_finished: {results}")  # 调试信息
    #     self.statusBar().showMessage('快速检测完成。')
    #     # 2. 从结果中筛选出状态为 "Yes" 的频道链接
    #     filtered_channels_and_urls = [
    #         (channel_name, m3u8_url) for channel_name, m3u8_url, status in results if status == "Yes"
    #     ]
    #     print("fasttest pass and speed test start"+filtered_channels_and_urls)
    #     if filtered_channels_and_urls:
    #         self.log_textedit.append(f"ft2: Starting speedtest tasks after fasttest with {self.num_threads} threads ...")
    #         self.speed_test_thread = SpeedTestThread(filtered_channels_and_urls, self.num_threads)
    #         self.speed_test_thread.result_signal.connect(self.handle_speedtest_result)
    #         self.speed_test_thread.log_signal.connect(self.handle_log)
    #         self.speed_test_thread.start()
    #     else:
    #         self.log_textedit.append("没有状态为 'Yes' 的频道进行测速。")
    def update_table_results_4_fasttest(self, results):
        with self.lock:
            for result in results:
                channel_name, m3u8_url, status, speed = result
                row_found = False

                # 查找是否已有对应的行
                for row in range(self.table_widget.rowCount()):
                    if (self.table_widget.item(row, 0).text() == channel_name and
                        self.table_widget.item(row, 1).text() == m3u8_url):
                        # 更新已有行的第三列和第四列
                        self.table_widget.setItem(row, 2, QTableWidgetItem(status))
                        self.table_widget.setItem(row, 3, QTableWidgetItem("N/A" if speed is None else f"{speed:.2f} MB/s"))
                        row_found = True
                        # 更新日志和预览
                        self.log_textedit.append(f"Update Table......")
                        self.log_textedit.append(f"Channel: {channel_name}, URL: {m3u8_url}, Status: {status}, Speed: {'N/A' if speed is None else f'{speed} MB/s'}")
                        self.result_textedit.append(f"Channel: {channel_name}, URL: {m3u8_url}, Status: {status}, Speed: {'N/A' if speed is None else f'{speed} MB/s'}")
                        break

        
    # def update_table_results_4_fasttest(self, results):
    #       # 遍历每一个结果，并更新 QTableWidget
    #     for result in results:
    #         channel_name, m3u8_url, status, speed = result
    #         row_position = self.table_widget.rowCount()
    #         self.table_widget.insertRow(row_position)

    #         self.table_widget.setItem(row_position, 0, QTableWidgetItem(channel_name))
    #         self.table_widget.setItem(row_position, 1, QTableWidgetItem(m3u8_url))
    #         self.table_widget.setItem(row_position, 2, QTableWidgetItem(status))
    #         self.table_widget.setItem(row_position, 3, QTableWidgetItem("N/A" if speed is None else f"{speed:.2f} MB/s"))

    #         # 更新日志和预览
    #         self.log_textedit.append(f"Update Table......")
    #         self.log_textedit.append(f"Channel: {channel_name}, URL: {m3u8_url}, Status: {status}, Speed: {'N/A' if speed is None else f'{speed} MB/s'}")
    #         self.result_textedit.append(f"Channel: {channel_name}, URL: {m3u8_url}, Status: {status}, Speed: {'N/A' if speed is None else f'{speed} MB/s'}")
    #     # # for result in results:
        # channel_name, m3u8_url, status, speed = results
        # # Update the table with results
        # for row in range(self.table_widget.rowCount()):
        #     if (self.table_widget.item(row, 0).text() == channel_name and
        #         self.table_widget.item(row, 1).text() == m3u8_url):
        #         self.table_widget.setItem(row, 2, QTableWidgetItem(status))
        #         self.table_widget.setItem(row, 3, QTableWidgetItem("N/A"))
        #         break
        # # Update the result preview
        # self.log_textedit.append(f"Channel: {channel_name}, URL: {m3u8_url}, Status: {status}")
        # self.result_textedit.append(f"Channel: {channel_name}, URL: {m3u8_url}, Status: {status}")
        # self.results.append(result)

    def update_table_results_4_speedtest(self, result):
        with self.lock:
            channel_name, m3u8_url, status, speed = result
            # Update the table with results
            for row in range(self.table_widget.rowCount()):
                if (self.table_widget.item(row, 0).text() == channel_name and
                    self.table_widget.item(row, 1).text() == m3u8_url):
                    self.table_widget.setItem(row, 2, QTableWidgetItem(status))
                    self.table_widget.setItem(row, 3, QTableWidgetItem(f"{speed:.2f} MB/s" if isinstance(speed, float) else speed))
                    break
            # Update the result preview
            speed_str = f"{speed:.2f} MB/s" if isinstance(speed, float) else speed
            self.log_textedit.append(f"Speed test result for {channel_name}: {speed_str}")
            self.result_textedit.append(f"Channel: {channel_name}, URL: {m3u8_url}, Status: {status}, {speed_str}")

    def handle_log(self, message):
        self.log_textedit.append(message)
        #print(message)

    def updateLog(self, message):
        self.log_textedit.append(message)

    def update_results(self, result):
        with self.lock:
            self.results.clear()
            self.results = result
    # Uncomment and define speedTest if needed
    # def speedTest(self):
    #     # 如果没有进行快速检测，则提示用户
    #     if not hasattr(self, 'thread') or not self.thread.isRunning():
    #         self.log_textedit.append('请先进行快速检测。')
    #         return
    #
    #     self.speed_test_thread = SpeedTestThread(self.channels_and_urls)
    #     self.speed_test_thread.progress_signal.connect(self.updateProgress)
    #     self.speed_test_thread.log_signal.connect(self.updateLog)
    #     self.speed_test_thread.start()

    def openFile(self):
        options = QFileDialog.Options()
        dialog = QFileDialog(self, "选择文件", self.last_directory)  # 设置初始目录
        dialog.setOptions(options)
        dialog.setFileMode(QFileDialog.ExistingFiles)  # 设置文件模式为“选择现有文件”
        self.log_textedit.clear()  # 清空日志区
        self.result_textedit.clear()  # 清空结果区
        if dialog.exec_():
            fileName = dialog.selectedFiles()
            if fileName:
                fileName = fileName[0]
                self.statusBar().showMessage(f'已打开文件: {fileName}')
                self.input_filename = fileName
                self.channels_and_urls, message = read_channels_and_urls_from_file(self.input_filename)

                if message:
                    # 如果有错误信息，则在状态栏显示
                    self.statusBar().showMessage(message)
                else:
                    # 如果没有错误信息，则更新表格
                    self.initTable()

                # 保存上一次的目录
                self.last_directory = QFileInfo(fileName).absolutePath()

    def saveResult(self):
        # 确保有结果可保存
        results = None

        if self.results:
            results = self.results
        else:
            # 如果没有结果，显示提示信息
            self.statusBar().showMessage('没有数据可保存。请先运行检测。')
            return

        #print(f"saveresult get results print:{results}")
        # 获取主程序的目录
        main_dir = os.path.dirname(sys.argv[0])

        # 创建 result 文件夹路径
        result_dir = os.path.join(main_dir, 'result')

        # 如果 result 文件夹不存在，则创建它
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)

        # 设置保存结果的文件路径
        file_path = os.path.join(result_dir, 'result.txt')

        try:
            # 将结果写入指定文件
            write_fasttest_results_to_file(results, file_path)
            self.statusBar().showMessage(f'结果已保存到: {file_path}')
        except Exception as e:
            self.statusBar().showMessage(f'保存结果时发生错误: {str(e)}')

    # Uncomment and define updateProgress and updateLog if needed
    # def updateProgress(self, completed, total):
    #     progress = int((completed / total) * 100)
    #     self.progress_bar.setValue(progress)
    #     self.progress_label.setText(f'检测进度: {completed}/{total} ({progress}%)')
    #

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.loadSettings()  # 在主窗口创建后加载设置
    window.show()
    sys.exit(app.exec_())
