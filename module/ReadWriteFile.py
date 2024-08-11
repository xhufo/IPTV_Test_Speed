import os
# File read & write
# 从文件中读取频道名称和m3u8链接列表
def read_channels_and_urls_from_file(filename):
    channels_and_urls = []
    errors = []

    try:
        with open(filename, 'r', encoding='UTF-8') as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if line:
                    parts = line.split(',')
                    if len(parts) == 2:
                        channel_name, url = parts
                        if channel_name and url:
                            channels_and_urls.append((channel_name, url))
                        else:
                            errors.append(f"Line {line_number}: Missing channel name or URL.")
                    else:
                        errors.append(f"Line {line_number}: Incorrect format. Expected '频道名,链接'.")
    except FileNotFoundError:
        errors.append("File not found.")
    except Exception as e:
        errors.append(f"An error occurred: {str(e)}")

    if errors:
        error_message = "\n".join(errors)
        return None, error_message
    return channels_and_urls, None

# def write_fasttest_results_to_file(results, output_filename):
#     try:
#         print(f"writefile print:{results}")
#         with open(output_filename, 'w', encoding='UTF-8') as f:
#             for channel_name, m3u8_url, status, speed in results:
#                 if status == "Yes":
#                     print(f"write file:{channel_name},{m3u8_url},{speed}\n")
#                     f.write(f"{channel_name},{m3u8_url}\n")
#         print(f"\nSpeed test results saved to {output_filename}")
#     except Exception as e:
#         print(f"Error occurred while writing to file: {str(e)}")
#

def write_fasttest_results_to_file(results, output_filename):
    try:
        # 过滤成功的记录
        filtered_results = [(channel_name, m3u8_url, speed) for channel_name, m3u8_url, status, speed in results if status == "Yes"]
        print(f"\nwrite ft result get1: {results}")
        print(f"\nwrite ft result get2: {filtered_results}")
        # # 定义提取速度的函数
        # def extract_speed(item):
        #     _, _, speed = item
        #     try:
        #         # 尝试将速度转换为浮点数，如果失败则返回 None
        #         if isinstance(speed, (int, float)):
        #             return float(speed)
        #         elif isinstance(speed, str) and (speed.replace('.', '', 1).isdigit()):
        #             return float(speed)
        #         else:
        #             return None
        #     except ValueError:
        #         return None
        #
        # # 判断是否有有效速度值
        # has_valid_speed = any(extract_speed(item) is not None for item in filtered_results)
        #
        # if has_valid_speed:
        #     # 只有在存在有效速度值时才进行排序
        #     sorted_results = sorted(
        #         filtered_results,
        #         key=lambda item: extract_speed(item) if extract_speed(item) is not None else float('-inf'),
        #         reverse=True  # 降序排列
        #     )
        # else:
            # 如果没有有效速度值，则保持原顺序
        sorted_results = filtered_results

        # 确定两个文件名
        base_name, ext = os.path.splitext(output_filename)
        output_filename1 = output_filename
        output_filename2 = f"{base_name}_withSpeed{ext}"

        # 输出第一个文件，包含频道名和链接
        with open(output_filename1, 'w', encoding='UTF-8') as f1:
            for channel_name, m3u8_url, _ in sorted_results:
                f1.write(f"{channel_name},{m3u8_url}\n")
        print(f"\nResults saved to {output_filename1}")

        # 输出第二个文件，包含频道名、链接和速度
        with open(output_filename2, 'w', encoding='UTF-8') as f2:
            for channel_name, m3u8_url, speed in sorted_results:
                try:
                    # 如果速度为空或无效，保持原样
                    if speed is None or speed == '':
                        formatted_speed = speed
                    elif isinstance(speed, (int, float)):
                        formatted_speed = f"{speed:.2f} MB/s"
                    elif isinstance(speed, str) and (speed.replace('.', '', 1).isdigit()):
                        formatted_speed = f"{float(speed):.2f} MB/s"
                    else:
                        formatted_speed = speed
                except ValueError:
                    # 如果转换失败，使用原始值
                    formatted_speed = speed

                f2.write(f"{channel_name},{m3u8_url},{formatted_speed}\n")
        print(f"\nSpeed test results saved to {output_filename2}")

    except Exception as e:
        print(f"Error occurred while writing to file: {str(e)}")
