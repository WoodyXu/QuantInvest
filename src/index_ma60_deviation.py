#################################################
# 计算A股和港股主流指数的日级别收盘点位和60日均线的偏离度
# 偏离度计算公式为：(当前日收盘价 - 60日均线收盘价) / 60日均线收盘价
#################################################

import os
import time
import akshare as ak
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from config.index_code import index_dict
from config.consts import START_DATE

# 设置请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# 应用请求头到akshare的requests会话
ak.__version__  # 确保akshare已初始化
if hasattr(ak, 'session'):
    for key, value in headers.items():
        ak.session.headers[key] = value

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def calculate_ma60_and_deviation(df, date_column="date", close_column="close"):
    """
    此函数用于计算 DataFrame 中的 ma60 和 deviation 列。

    参数:
    df (pd.DataFrame): 输入的 DataFrame，应包含 '日期' 和 '收盘价' 列。

    返回:
    pd.DataFrame: 包含 ma60 和 deviation 列的 DataFrame。
    """
    df[date_column] = pd.to_datetime(df[date_column])
    df = df.sort_values(by=date_column)
    # 计算 ma60 列
    df['ma60'] = df[close_column].rolling(window=60, min_periods=60).mean()
    # 计算 ma60 偏离度列
    df['deviation'] = (df[close_column] - df['ma60']) / df['ma60']
    return df

def plot_and_save_deviation(df, START_DATE_str, name, date_column="date", deviation_column="deviation"):
    """
    该函数用于绘制并保存指数ma60偏离度的折线图。

    参数:
    df (pandas.DataFrame): 包含日期和偏离度数据的 DataFrame。
    START_DATE_str (str): 开始日期，格式为 'yyyy-mm-dd'。
    name (str): 指数名称。

    返回:
    None
    """
    # 将输入的字符串日期转换为 pandas 的 Timestamp 对象
    START_DATE = pd.Timestamp(START_DATE_str)
    latest_date = df[date_column].max()
    
    # 筛选出指定日期范围内的数据
    filtered_df = df[(df[date_column] >= START_DATE) & (df[date_column] <= latest_date)]
    
    # 获取有有效deviation值的最早日期（确保有足够数据计算MA60）
    valid_data = filtered_df.dropna(subset=[deviation_column])
    if not valid_data.empty:
        actual_start_date = valid_data[date_column].min()
    else:
        # 如果没有有效数据，使用过滤后数据的最早日期
        actual_start_date = filtered_df[date_column].min()
    
    # 创建绘图窗口
    plt.figure(figsize=(12, 6), dpi=300)
    
    # 绘制折线图
    plt.plot(filtered_df[date_column], filtered_df[deviation_column])
    
    # 设置 x 轴和 y 轴标签
    plt.xlabel(date_column)
    plt.ylabel(deviation_column)
    plt.title("{} MA60 偏离度 最新日期：{}".format(name, latest_date.strftime("%Y-%m-%d")))
    
    # 将纵轴标签设置为百分比格式
    plt.gca().yaxis.set_major_formatter(ticker.PercentFormatter(1))
    
    # 设置 x 轴范围，自适应每个指数的实际数据起始日期和最新日期
    ax = plt.gca()
    ax.set_xlim(left=actual_start_date, right=latest_date)
    
    # 设置 x 轴的刻度和日期格式
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[6, 12]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    # 获取自动生成的刻度列表并过滤掉超过最新日期的刻度
    current_ticks = ax.get_xticks()
    current_ticks = [tick for tick in current_ticks if tick <= mdates.date2num(latest_date)]
    ax.set_xticks(current_ticks)
    
    # 设置 x 轴刻度标签的字体大小和旋转角度
    plt.xticks(fontsize=8, rotation=45)
    plt.grid(True)
    
    # 在最新日期的坐标点附近添加两行文本：日期和百分比数值
    # 获取最新日期的偏离度值
    latest_deviation = filtered_df.iloc[-1][deviation_column]
    
    # 设置文本样式：红色加粗，大小适中
    text_props = dict(color='red', fontweight='bold', fontsize=10)
    
    # 计算文本位置（最新日期右侧一点）
    text_x = latest_date
    text_y = latest_deviation
    
    # 添加日期文本（第一行）
    ax.text(text_x, text_y, f'{latest_date.strftime("%Y-%m-%d")}', 
            ha='left', va='bottom', **text_props)
    
    # 添加百分比数值文本（第二行）
    ax.text(text_x, text_y - 0.01, f'{latest_deviation:.2%}', 
            ha='left', va='top', **text_props)
    
    # 保存图片到与src同一层级的pics/目录
    current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件所在的src目录
    parent_dir = os.path.dirname(current_dir)  # 获取src的父目录
    pics_dir = os.path.join(parent_dir, 'pics')  # 创建与src同一层级的pics目录
    # 创建pics目录如果不存在
    os.makedirs(pics_dir, exist_ok=True)
    filename = '{}MA60偏离度_{}.png'.format(name, latest_date.strftime("%Y-%m-%d"))
    filepath = os.path.join(pics_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    for index_info in index_dict:
        name = index_info
        code = index_dict[index_info]

        cur_daily_df = None

        if name.split("-")[0] == "港股":
            try:
                cur_daily_df = ak.stock_hk_index_daily_sina(symbol=code)[["date", "close"]]
            except Exception as e:
                print(f"获取港股 {name} ({code}) 数据失败: {e}")
        
        elif name.split("-")[0] == "A股":
            max_retries = 3
            retry_interval = 2  # 秒
            data_sources = [
                (ak.stock_zh_index_daily, "stock_zh_index_daily"),  # 首选，速度快
                (ak.stock_zh_index_daily_tx, "stock_zh_index_daily_tx"),  # 备选，速度慢但可靠
                (ak.stock_zh_index_daily_em, "stock_zh_index_daily_em")  # 最后尝试
            ]
            
            for func, source_name in data_sources:
                print(f"尝试使用 {source_name} 获取 {name} 数据...")
                
                for attempt in range(max_retries):
                    try:
                        cur_daily_df = func(symbol=code)[["date", "close"]]
                        print(f"成功使用 {source_name} 获取 {name} 数据")
                        break
                    except Exception as e:
                        print(f"使用 {source_name} 获取A股 {name} ({code}) 数据失败 (尝试 {attempt+1}/{max_retries}): {e}")
                        if attempt < max_retries - 1:
                            print(f"等待 {retry_interval} 秒后重试...")
                            time.sleep(retry_interval)
                        else:
                            print(f"已达到最大重试次数，尝试下一个数据源")
                            cur_daily_df = None
                
                if cur_daily_df is not None:
                    break
            
            if cur_daily_df is None:
                print(f"所有数据源都失败，放弃获取 {name} 数据")
        
        if cur_daily_df is not None:
            cur_daily_df = calculate_ma60_and_deviation(cur_daily_df, date_column="date", close_column="close")
            plot_and_save_deviation(cur_daily_df, START_DATE, name)
