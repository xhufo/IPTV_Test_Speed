from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import m3u8
import time
import threading

from PyQt5.QtCore import QThread, pyqtSignal, QObject, QWaitCondition, QMutex, QMutexLocker


# 2. 测试链接连通性-简单ping一下，节约时间
class ConnectivityTestThread(QThread):
    log_signal1 = pyqtSignal(str)
    result_signal1 = pyqtSignal(list)
    all_finished_signal1 = pyqtSignal(list)  # 自定义信号用于发射所有结果

    def __init__(self, channels_and_urls, num_threads):
        super().__init__()
        self.channels_and_urls = channels_and_urls
        self.num_threads = num_threads
        self.batch_size = num_threads
        self.all_batch_results = []
        self.results_lock = QMutex()

    def run(self):
        # 以 batch_size 为单位分割任务
        for i in range(0, len(self.channels_and_urls), self.batch_size):
            print(f"ft loop = {i}")
            batch = self.channels_and_urls[i:i + self.batch_size]
            results = self.run_batch(batch)
            # 发射信号，更新表格
            self.result_signal1.emit(results)
            with QMutexLocker(self.results_lock):
                self.all_batch_results.extend(results)
            print(f"All results size so far: {len(self.all_batch_results)}")
            # 每个分组后暂停1秒
            time.sleep(1)
        self.all_finished_signal1.emit(self.all_batch_results)

    def run_batch(self, batch):
        results = []
        # 使用线程池执行任务
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []

            for channel_name, m3u8_url in batch:
                future = executor.submit(self.test_m3u8_connectivity, channel_name, m3u8_url)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.log_signal1.emit(f"In thread Error: {str(e)}")
        print(f"Batch results size: {len(results)}")
        return results

    # print(f"in ft batch: result = {results}")  # 调试信息

    def test_m3u8_connectivity(self, channel_name, m3u8_url, timeout=1):
        try:
            # 尝试加载 m3u8 文件
            m3u8_obj = m3u8.load(m3u8_url, timeout=timeout)

            # 检查 m3u8 文件是否成功加载
            if m3u8_obj:
                return channel_name, m3u8_url, "Yes", None
            else:
                return channel_name, m3u8_url, "No", None

        except requests.exceptions.RequestException as e:
            # 处理网络请求异常
            log_message = f"Channel {channel_name}: No (Test m3u8 Network error: {str(e)})"
            self.log_signal1.emit(log_message)  # 发送日志信号
            return channel_name, m3u8_url, "No", None

        except Exception as e:
            # 处理其他异常
            log_message = f"Channel {channel_name}: No (Test m3u8 Unknown error: {str(e)})"
            self.log_signal1.emit(log_message)  # 发送日志信号
            return channel_name, m3u8_url, "No", None
        # try:
        #     response = requests.get(m3u8_url, timeout=timeout)
        #     status = "Yes" if response.status_code == 200 else "No"
        #     log_message = f"Channel {channel_name}: {status}"
        #     self.log_signal.emit(log_message)  # 发送日志信号
        #     return (channel_name, m3u8_url, status,"")
        # except requests.RequestException as e:
        #     log_message = f"Channel {channel_name}: No (Exception: {str(e)})"
        #     self.log_signal.emit(log_message)  # 发送日志信号
        #     return (channel_name, m3u8_url, "No", "")


# def test_multiple_m3u8_connectivity(channels_and_urls, num_threads=4, log_callback=None):
#
#     results = []
#     threads = []
#
#     def worker(channel_name, m3u8_url):
#         status = test_m3u8_connectivity(channel_name, m3u8_url)
#         if log_callback:
#             log_callback(f"Channel {channel_name}: {status}")
#         results.append((channel_name, m3u8_url, status, "N/A"))
#
#     for channel_name, m3u8_url in channels_and_urls:
#         while len(threads) >= num_threads:
#             # 等待线程池中的线程完成
#             for thread in threads:
#                 thread.join()
#             threads = []
#
#         thread = threading.Thread(target=worker, args=(channel_name, m3u8_url))
#         threads.append(thread)
#         thread.start()
#
#     # 等待所有线程完成
#     for thread in threads:
#         thread.join()
#
#     return results


# 3. 对可用链接测速

# 4. 多线程测速
# qt多线程实现

class SpeedTestThread(QThread):
    log_signal2 = pyqtSignal(str)
    result_signal2 = pyqtSignal(list)  # 发射每个批次的结果
    all_finished_signal2 = pyqtSignal(list)  # 发射所有批次的结果

    def __init__(self, channels_and_urls, num_threads):
        super().__init__()
        self.channels_and_urls = channels_and_urls
        self.num_threads = num_threads
        self.batch_size = num_threads
        self.all_batch_results = []

    def run(self):
        # 以 batch_size 为单位分割任务
        for i in range(0, len(self.channels_and_urls), self.batch_size):
            print(f"speed test loop = {i}")
            batch = self.channels_and_urls[i:i + self.batch_size]
            results = self.run_batch(batch)
            # 发射信号，更新表格
            self.result_signal2.emit(results)
            self.all_batch_results.extend(results)  # 将当前批次结果添加到 all_batch_results 中
        self.all_finished_signal2.emit(self.all_batch_results)  # 发射所有结果

    def run_batch(self, batch):
        results = []
        # 使用线程池执行任务
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []

            for channel_name, m3u8_url in batch:
                future = executor.submit(self.test_m3u82_speed, channel_name, m3u8_url)
                futures.append(future)

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.log_signal2.emit(f"Error: {str(e)}")
        return results

    def test_m3u82_speed(self, channel_name, m3u8_url):
        try:
            start_time = time.time()

            short_url = m3u8_url[:50] + ('...' if len(m3u8_url) > 50 else '')
            print(f"Testing channel speed......: {channel_name}, URL: {short_url}")
            self.log_signal2.emit(f"Testing channel speed......: {channel_name}, URL: {short_url}")

            m3u8_obj = m3u8.load(m3u8_url)
            total_segments = len(m3u8_obj.segments)
            total_size = 0

            for segment in m3u8_obj.segments:
                segment_url = segment.absolute_uri
                try:
                    segment_start_time = time.time()
                    response = requests.get(segment_url, timeout=1)
                    segment_end_time = time.time()

                    segment_time = segment_end_time - segment_start_time
                    segment_size = len(response.content)
                    total_size += segment_size

                except requests.exceptions.RequestException:
                    self.log_signal2.emit(f"Segment download failed or timed out for {segment_url}")
                    return channel_name, m3u8_url, "No", None

            total_download_time = time.time() - start_time
            average_speed = total_size / total_download_time / 1024 / 1024  # MB/s

            print(f"Processed - {channel_name} ({average_speed:.2f} MB/s)")
            self.log_signal2.emit(f"Processed - {channel_name} ({average_speed:.2f} MB/s)")
            average_speed_str = f"{average_speed:.2f} MB/s"
            return channel_name, m3u8_url, "Yes", average_speed

        except Exception as e:
            print(f"Error occurred for m3u8 URL {m3u8_url}: {str(e)}")
            self.log_signal2.emit(f"Error occurred for m3u8 URL {m3u8_url}: {str(e)}")
            return channel_name, m3u8_url, "No", None


# class SpeedTestThread(QThread):
#     update_log = pyqtSignal(str)
#     update_progress = pyqtSignal(str)
#     update_table = pyqtSignal(tuple)
#     finished = pyqtSignal()
#
#     def __init__(self, channels_and_urls):
#         super().__init__()
#         self.channels_and_urls = channels_and_urls
#
#     def download_m3u8(self, channel_name, m3u8_url, total_urls, index):
#         try:
#             start_time = time.time()
#
#             # 打印正在测速的频道和链接
#             short_url = m3u8_url[:50] + ('...' if len(m3u8_url) > 50 else '')
#             self.update_log.emit(f"Testing channel speed......: {channel_name}, URL: {short_url}")
#
#             m3u8_obj = m3u8.load(m3u8_url)
#             total_segments = len(m3u8_obj.segments)
#             total_size = 0
#
#             for segment in m3u8_obj.segments:
#                 segment_url = segment.absolute_uri
#                 try:
#                     segment_start_time = time.time()
#                     response = requests.get(segment_url, timeout=1)
#                     segment_end_time = time.time()
#
#                     segment_time = segment_end_time - segment_start_time
#                     segment_size = len(response.content)
#                     total_size += segment_size
#
#                 except requests.exceptions.RequestException:
#                     self.update_log.emit(f"Segment download failed or timed out for {segment_url}")
#                     return channel_name, m3u8_url, "No"
#
#             total_download_time = time.time() - start_time
#             average_speed = total_size / total_download_time / 1024 / 1024  # MB/s
#
#             self.update_log.emit(f"Processed {index}/{total_urls} - {channel_name} ({average_speed:.2f} MB/s)")
#             return channel_name, m3u8_url, average_speed
#
#         except Exception as e:
#             self.update_log.emit(f"Error occurred for m3u8 URL {m3u8_url}: {str(e)}")
#             return channel_name, m3u8_url, "No"
#
#     def run(self):
#         results = []
#         threads = []
#
#         def handle_result(result):
#             results.append(result)
#             self.update_table.emit(result)
#
#         def handle_log(message):
#             self.update_log.emit(message)
#
#         total_urls = len(self.channels_and_urls)
#
#         for index, (channel_name, m3u8_url) in enumerate(self.channels_and_urls, start=1):
#             while len(threads) >= 4:  # 可以自定义线程数量
#                 for thread in threads:
#                     thread.wait()
#                 threads = []
#
#             thread = QThread()  # 使用 QThread 创建子线程
#             worker = Worker(self.download_m3u8, channel_name, m3u8_url, total_urls, index)
#             worker.moveToThread(thread)
#             worker.result_signal.connect(handle_result)
#             worker.log_signal.connect(handle_log)
#             thread.started.connect(worker.run)
#             thread.start()
#             threads.append(thread)
#
#         for thread in threads:
#             thread.wait()
#
#         self.update_progress.emit("Speed test completed.")
#         self.finished.emit()


# def test_multiple_m3u8_speeds(channels_and_urls, num_threads=4):
#     try:
#         start_time = time.time()
#         threads = []
#         results = []
#         total_urls = len(channels_and_urls)
#
#         def worker(channel_name, m3u8_url, index):
#             result = download_m3u8(channel_name, m3u8_url, total_urls, index)
#             results.append(result)
#
#         for index, (channel_name, m3u8_url) in enumerate(channels_and_urls, start=1):
#             while len(threads) >= num_threads:
#                 for thread in threads:
#                     thread.join()
#                 threads = []
#
#             thread = threading.Thread(target=worker, args=(channel_name, m3u8_url, index))
#             threads.append(thread)
#             thread.start()
#
#         for thread in threads:
#             thread.join()
#
#         end_time = time.time()
#         total_time = end_time - start_time
#
#         print(f"Total time taken for all m3u8 URLs: {total_time:.2f} seconds")
#         return results
#
#     except Exception as e:
#         print(f"Error occurred: {str(e)}")
#         return []


# 5. 输出结果


# main run file

if __name__ == "__main__":
    input_filename = "../m3u8_urls.txt"
    output_filename = "../speed_test_results.txt"

    # 读取频道名称和m3u8链接列表
    channels_and_urls, message = read_channels_and_urls_from_file(input_filename)
    if message:
        print(f"读取文件时发生错误: {message}")
        exit(1)  # 退出程序，表示发生错误

    # 先测试连通性
    if not channels_and_urls:
        print("没有读取到有效的频道数据。")
        exit(1)

    connectivity_results = test_multiple_m3u8_connectivity(channels_and_urls, num_threads=14)

    # # 过滤连通性良好的链接 available_channels_and_urls = [(channel_name, m3u8_url) for channel_name, m3u8_url, status in
    # connectivity_results if status == "Yes"]
    #
    # if not available_channels_and_urls:
    #     print("没有可用的频道进行测速。")
    # else:
    #     # 对连通性良好的链接测速
    #     speed_test_results = test_multiple_m3u8_speeds(available_channels_and_urls, num_threads=14)
    #
    #     # 将结果写入文件
    #     write_results_to_file(speed_test_results, output_filename)
    #
    #     print(f"测速结果已保存到 {output_filename}")
