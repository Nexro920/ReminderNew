import datetime
import pytz
import math
from lunarcalendar import Converter, Solar, Lunar

def get_chengdu_time():
    """获取当前成都时间（UTC+8）"""
    utc_now = datetime.datetime.now(pytz.UTC)
    chengdu_tz = pytz.timezone('Asia/Shanghai')
    chengdu_time = utc_now.astimezone(chengdu_tz)
    return chengdu_time

def equation_of_time(day_of_year):
    """简化的时间方程近似计算（分钟）"""
    B = 360.0 * (day_of_year - 81) / 365.0
    B_rad = math.radians(B)
    eot = 9.87 * math.sin(2 * B_rad) - 7.53 * math.cos(B_rad) - 1.5 * math.sin(B_rad)
    return eot

def true_solar_time(local_time, longitude):
    """计算真太阳时"""
    day_of_year = local_time.timetuple().tm_yday
    # 经度校正：每4分钟1度，成都经度104.07°E，标准经度120°E
    longitude_correction = 4 * (longitude - 120)  # 分钟
    eot = equation_of_time(day_of_year)
    # 总时间差（分钟）
    total_offset = longitude_correction + eot
    # 转换为时间增量
    solar_time = local_time + datetime.timedelta(minutes=total_offset)
    return solar_time

def time_to_12chen(solar_time):
    """将真太阳时转换为十二时辰"""
    hour = solar_time.hour + solar_time.minute / 60.0
    # 十二时辰从23:00开始，每2小时一个时辰
    chen_list = [
        ("子时", 23, 1), ("丑时", 1, 2), ("寅时", 3, 3), ("卯时", 5, 4),
        ("辰时", 7, 5), ("巳时", 9, 6), ("午时", 11, 7), ("未时", 13, 8),
        ("申时", 15, 9), ("酉时", 17, 10), ("戌时", 19, 11), ("亥时", 21, 12)
    ]
    for chen_name, start_hour, chen_number in chen_list:
        if start_hour <= hour < start_hour + 2 or (start_hour == 23 and hour >= 23):
            return chen_name, chen_number
        if hour < 1 and start_hour == 23:  # 处理0:00到1:00属于子时
            return chen_name, chen_number
    return "子时", 1  # 默认返回子时

def get_lunar_date(gregorian_date):
    """将公历日期转换为农历"""
    solar = Solar(gregorian_date.year, gregorian_date.month, gregorian_date.day)
    lunar = Converter.Solar2Lunar(solar)
    # 转换为中文格式
    lunar_months = ["正月", "二月", "三月", "四月", "五月", "六月",
                    "七月", "八月", "九月", "十月", "十一月", "十二月"]
    lunar_days = ["初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
                  "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
                  "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"]

    month_str = lunar_months[lunar.month - 1]
    day_str = lunar_days[lunar.day - 1]
    if lunar.isleap:
        month_str = f"闰{month_str}"
    return lunar.year, month_str, day_str, lunar.month, lunar.day

def get_elements(n1, n2, n3):
    elements = [
        "大安（震）（木）：平安吉祥，诸事顺遂",
        "留连（坎）（水）：事情拖延，难以决断",
        "速喜（离）（火）：喜事临门，好消息快来",
        "赤口（兑）（金）：口舌是非，易生争执",
        "小吉（巽）（木）：小有收获，平稳略好",
        "空亡（震）（木）：虚无缥缈，难有结果",
        "病符（坤）（土）：不适不顺，多有不便",
        "桃花（艮）（土）：姻缘桃花，人际和谐",
        "天德（乾）（金）：吉祥如意，贵人相助"
    ]

    # 从"大安"开始，获取对应的元素
    first_index = (n1 - 1) % len(elements)
    second_index = (n1 + n2 - 2) % len(elements)
    third_index = (n1 + n2 + n3 - 3) % len(elements)

    return elements[first_index], elements[second_index], elements[third_index]

def main():
    # 获取成都时间
    chengdu_time = get_chengdu_time()
    print(f"当前成都时间: {chengdu_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 计算真太阳时（成都经度104.07°E）
    solar_time = true_solar_time(chengdu_time, 104.07)
    print(f"成都真太阳时: {solar_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 获取农历
    # date = datetime.datetime(2025, 7, 26)
    lunar_year, lunar_month, lunar_day, lunar_month_num, lunar_day_num = get_lunar_date(chengdu_time)
    print(f"农历日期: {lunar_year}年 {lunar_month} {lunar_day}")

    # 转换为十二时辰和数字
    chen_name, chen_number = time_to_12chen(solar_time)
    print(f"对应十二时辰: {chen_name} (数字: {chen_number})")

    result = get_elements(lunar_month_num, lunar_day_num, chen_number)
    print("结果：")
    for element in result:
        print(element)

def little_liuren():
    while True:
        # 输入三个数字
        n1 = int(input("请输入第一个数字："))
        n2 = int(input("请输入第二个数字："))
        n3 = int(input("请输入第三个数字："))

        result = get_elements(n1, n2, n3)
        print("结果：")
        for element in result:
            print(element)

        # 询问用户是否继续
        continue_choice = input("是否继续？(y/n): ")
        if continue_choice.lower() != 'y':
            break

    print("程序结束。")

if __name__ == "__main__":
    main()
    little_liuren()