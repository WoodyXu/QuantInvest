#################################################
# 计算A股和港股主流指数的日级别收盘点位和60日均线的偏离度
# 偏离度计算公式为：(当前日收盘价 - 60日均线收盘价) / 60日均线收盘价
#################################################

import os
import akshare as ak
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

index_dict = {
    "港股-恒生指数": "HSI",

    "A股-上证指数": "sh000001",
    "A股-创业板指": "sz399006",
    "A股-全指信息": "sh000993",
    "A股-中证500": "sh000905",
    "A股-全指医药": "sh000991",
    "A股-全指消费": "sh000990",
    "A股-中证红利": "sh000922",
    "A股-沪深300": "sh000300",
}

start_date = "2015-01-01"

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

def plot_and_save_deviation(df, start_date_str, name, date_column="date", deviation_column="deviation"):
    """
    该函数用于绘制并保存指数ma60偏离度的折线图。

    参数:
    df (pandas.DataFrame): 包含日期和偏离度数据的 DataFrame。
    start_date_str (str): 开始日期，格式为 'yyyy-mm-dd'。
    name (str): 指数名称。

    返回:
    None
    """
    # 将输入的字符串日期转换为 pandas 的 Timestamp 对象
    start_date = pd.Timestamp(start_date_str)
    latest_date = df[date_column].max()
    
    # 筛选出指定日期范围内的数据
    filtered_df = df[(df[date_column] >= start_date) & (df[date_column] <= latest_date)]
    
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
    
    # 设置 x 轴的刻度和日期格式
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator(bymonth=[6, 12]))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    # 设置 x 轴刻度标签的字体大小和旋转角度
    plt.xticks(fontsize=8, rotation=45)
    plt.grid(True)
    # 保存图片到当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filename = '{}MA60偏离度_{}.png'.format(name, latest_date.strftime("%Y-%m-%d"))
    filepath = os.path.join(current_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')

if __name__ == "__main__":
    for index_info in index_dict:
        name = index_info
        code = index_dict[index_info]

        cur_daily_df = None

        if name.split("-")[0] == "港股" and code in ak.stock_hk_index_spot_em()["代码"]:
            cur_daily_df = ak.stock_hk_index_daily_em(symbol=code)[["date", "latest"]]
            cur_daily_df.columns = ["date", "close"]
        
        elif name.split("-")[0] == "A股":
            cur_daily_df = ak.stock_zh_index_daily_em(symbol=code)[["date", "close"]]
            print(name + '\n\n')
            print(cur_daily_df.tail())
        
        if cur_daily_df is not None:
            cur_daily_df = calculate_ma60_and_deviation(cur_daily_df, date_column="date", close_column="close")
            plot_and_save_deviation(cur_daily_df, start_date, name)
