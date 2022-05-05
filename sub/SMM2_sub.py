from m5stack import *
from m5ui import *
import _thread
import binascii
import espnow
import gc
import math
import ntptime
import ujson
import uos
import utime
import wifiCfg


# BEEP音鳴らしスレッド関数
def beep_sound():
    while True:
        if NPD_data != 'good' : # タイムアウトで表示ミュートされてるか、初期値のままならpass
            pass
        else :
            if (now_power >= (AMPERE_LIMIT * AMPERE_RED * 100)) and (beep_on is True) :  # 警告閾値超えでBEEP ONなら
                speaker.tone(freq=220, duration=200)
                utime.sleep(2)
        utime.sleep(0.1)


# 表示OFFボタン処理スレッド関数
def turn_lcd_off():
    global lcd_off

    if lcd_off is True :
        lcd_off = False
    else :
        lcd_off = True

    if lcd_off is True :
        lcd.setBrightness(0) #バックライト輝度調整（OFF）
    else :
        lcd.setBrightness(brightness) #バックライト輝度調整

    utime.sleep(0.1)


# 表示モード切替ボタン処理スレッド関数
def flip_page():
    global page
    global disp_mode

    # ボタンが押されるたびにページをインクリメント
    page = page + 1
    if page == len(draw_page) :
        page = 0

    if draw_page[page] == draw_main :
        disp_mode = 'main'
    elif draw_page[page] == draw_graph_tp :
        disp_mode = 'graph'
    else :
        disp_mode = ''

    # ボタンエリア以外は一旦画面全消し
    lcd.rect(0 , 0, 320, 224, 0x000000, 0x000000)

    # 当該ページを表示
    draw_page[page]()

    utime.sleep(0.1)


# BEEPアイコン描画
def draw_beep_icon():
    if beep_on is True :   # BEEP ON
        lcd.roundrect(230, 224, 58, 15, 7, 0x66e6ff, 0x2acf00)
        lcd.font(lcd.FONT_Default)
        lcd.print("BEEP", 242, 226, 0xffffff)
    else :              # BEEP OFF
        lcd.roundrect(230, 224, 58, 15, 7, 0x66e6ff, 0x000000)
        lcd.font(lcd.FONT_Default)
        lcd.print("BEEP", 242, 226, 0x7b7b7b)


# BEEP音ボタン処理スレッド関数
def turn_beep_off():
    global beep_on

    if beep_on is True:
        beep_on = False
    else :
        beep_on = True

    draw_beep_icon()
    utime.sleep(0.1)


# データ受信インジケーター描画
def draw_indicator(x, y, r, step, step_max) :
    rad = 2 * math.pi * (step / step_max)
    vol = (1 -math.cos(rad)) / 2 * 0xff
    col = int('0x' + '{:x}'.format(round(vol * 0.9)) + '0000', 16)
    lcd.circle(x, y, r, col, col) 


# 【page】メインページ：瞬間電力値、検針日以降の電力量、電気代
def draw_main() :

    # 瞬間電力値の表示
    draw_w()

    # 今月（検針日を起点）の日付範囲を表示
    (x, y, w, h) = (0, 115, 320, 25)
    lcd.rect(x, y, w, h, bgcolor, bgcolor)
    
    s = '{}~{}'.format(collect[5:10], update[5:10])
    lcd.font(lcd.FONT_DejaVu24)
    lcd.print(s, lcd.CENTER, y, uncolor)

    # 今月（検針日を起点）の電力量の表示
    (x, y, w, h) = (0, 140, 140, 40)
    lcd.rect(x, y, w, h, bgcolor, bgcolor)

    if power_kwh == 0 :
        power_kwh_d = '-'
    else :
        power_kwh_d = str(int(power_kwh))
    lcd.font(lcd.FONT_DejaVu40)
    lcd.print(power_kwh_d, x + w - lcd.textWidth(power_kwh_d)-20, y + 5, color2)
    lcd.font(lcd.FONT_DejaVu24)
    lcd.print('kWh', 80,185, uncolor)

    # 今月（検針日を起点）の電気料金の表示
    (x, y, w, h) = (160, 140, 160, 40)
    lcd.rect(x, y, w, h, bgcolor, bgcolor)

    if charge == 0 :
        charge_d = '-'
    else :
        charge_d = str(int(charge))
    lcd.font(lcd.FONT_DejaVu40)
    lcd.print(charge_d, x + w - lcd.textWidth(charge_d)-20, y + 5, color2)
    lcd.font(lcd.FONT_DejaVu24)
    lcd.print('Yen', 265,185, uncolor)


# 瞬間電力値の表示
def draw_w() :
    # 親機〜スマートメーター間タイムアウト：グレー文字
    if NPD_data == 'timeout' :
        fc = grayout

    # 子機〜親機間タイムアウト：淡黄色文字
    elif NPD_data == 'lost' :
        fc = yellow

    # 通常受信状態
    elif NPD_data == 'good' :
        # 警告閾値超え
        if now_power >= (AMPERE_LIMIT * AMPERE_RED * 100) :
            fc = color3  # 瞬間電力文字色指定（警告時）
            if lcd_off is True :   # 閾値超え時はLCD ON
                lcd.setBrightness(brightness) #バックライト輝度調整（ON）

        # 通常表示
        else :
            fc = color1  # 瞬間電力文字色指定（通常時）
            if lcd_off is True :
                lcd.setBrightness(0) #バックライト輝度調整（OFF）

    # 瞬間電力値最大化表示モード時
    if disp_mode == 'main' :
        lcd.rect(0 , 0, 320, 110, bgcolor, bgcolor)
        # 瞬間電力値表示
        lcd.font(lcd.FONT_7seg, dist = 30, width = 6)
        lcd.print(str(now_power) + ' ', lcd.RIGHT, 0, fc)
        # W表示
        lcd.font(lcd.FONT_DejaVu40)
        lcd.print('W', 275, 60, uncolor)

    # 積算電力棒グラフ表示モード時
    elif disp_mode == 'graph' :
        lcd.rect(0 , 0, 320, 63, bgcolor, bgcolor)
        # 瞬間電力値表示
        lcd.font(lcd.FONT_7seg, dist = 14, width = 3)
        lcd.print(str(now_power) + '    ', lcd.RIGHT, 5, fc)
        # W表示
        lcd.font(lcd.FONT_DejaVu24)
        lcd.print('W', 210, 30, uncolor)


# 【page】電力量グラフ (当日と前日・30分毎)
def draw_graph_tp() : 

    draw_w()

    graph_scale = 5000      # グラフ表示倍率（ややサチる値にしてる）
    graph_red = 0.6         # グラフ橙色閾値（0.0～1.0）
    graph_orange = 0.3      # グラフ黃色閾値（0.0～1.0）
    color_today = 0x000000  # 初期値はとりあえず黒色
    color_yesterday = 0x808080  # 前日のグラフ描画色 = グレー
    color_delta = 0xe00000      # 前日からの増分のグラフ描画色 = 赤
    width = 5                   # グラフの幅

    # グリッド描画
    lcd.line(0, 64, 320, 64, 0xaeaeae)
    lcd.line(0, 206, 320, 206, 0xaeaeae)

    lcd.font(lcd.FONT_Ubuntu)
    lcd.print('00', 6, 208, 0xffffff)
    lcd.print('06', 78, 208, 0xffffff)
    lcd.print('12', 151, 208, 0xffffff)
    lcd.print('18', 223, 208, 0xffffff)
    lcd.print('24', 293, 208, 0xffffff)

    lcd.rect(0, 65, 320, 140, 0x000000, 0x000000)
    lcd.line(15 + (6 * 0), 65, 15 + (6 * 0), 206, 0x303030)
    lcd.line(15 + (6 * 12), 65, 15 + (6 * 12), 206, 0x303030)
    lcd.line(15 + (6 * 24), 65, 15 + (6 * 24), 206, 0x303030)
    lcd.line(15 + (6 * 36), 65, 15 + (6 * 36), 206, 0x303030)
    lcd.line(15 + (6 * 48), 65, 15 + (6 * 48), 206, 0x303030)
    
    # グラフ描画メイン
    # TotalPower[1][48] = TotalPower[0][0]
    for n in range(0, 48) :
        
        # 前日のグラフ高さの計算
        if ( TotalPower[1][n + 1] == 0 ) or ( TotalPower[1][n] == 0 ):
            h_power_yesterday = 0
        else :
            h_power_yesterday = round((TotalPower[1][n + 1] - TotalPower[1][n]) / 1000, 1)
            
        if h_power_yesterday <= 0 : # 基本、マイナス値は有り得ないが念のため
            height_yesterday = 0
        else :
            height_yesterday = int(h_power_yesterday * graph_scale / AMPERE_LIMIT)

        if height_yesterday > 140 : # 120を超えた値は120に丸める
            height_yesterday = 140

        # 当日のグラフ高さの計算
        if ( TotalPower[0][n + 1] == 0 ) or ( TotalPower[0][n] == 0 ):
            h_power_today = 0
        else :
            h_power_today = round((TotalPower[0][n + 1] - TotalPower[0][n]) / 1000, 1)

        if h_power_today <= 0 : # 基本、マイナス値は有り得ないが念のため
            height_today = 0
        else :
            height_today = int(h_power_today * graph_scale / AMPERE_LIMIT)
        
        if height_today > 140 : # 120を超えた値は120に丸める
            height_today = 140

        if (height_today == 0) or (height_yesterday == 0) or (height_today <= height_yesterday) : 
            height_today_delta = 0
            height_today_base = height_today
        else :
            height_today_delta = height_today - height_yesterday
            height_today_base = height_yesterday

        # グラフ高さに応じて色指定
        if height_today > (140 * graph_red) :
           color_today = 0xff8000  # 橙色
        elif height_today > (140 * graph_orange) :
           color_today = 0xffe000  # 黃色
        else :
           color_today = 0x2acf00  # 緑色
 
        x_start = (n * 6) + 16

        # グラフ描画セクション
        if height_yesterday != 0 :
            lcd.rect(x_start, 205 - height_yesterday, width, height_yesterday, color_yesterday, color_yesterday)
        if height_today_base != 0 :
            lcd.rect(x_start, 205 - height_today_base, width, height_today_base, color_today, color_today)
        if height_today_delta != 0 :
            lcd.rect(x_start, 205 - height_today, width, height_today_delta, color_delta, color_delta)


# 【page】電力量グラフ (随時比較・当日と直近7日間)
def draw_detail() :
    daily_cpd =  [0] * 8
    daily_tpd =  [0] * 8
    len_max = 15

    lcd.rect(0 , 0, 320, 224, 0x000000, 0x000000)
    lcd.font(lcd.FONT_Ubuntu)

    if 'tpd_time' in globals() :
        if TIME_TB.index(tpd_time) == 0 :
            index = 48
        else :
            index = TIME_TB.index(tpd_time)

        today_cpd = round((TotalPower[0][index] - TotalPower[0][0]) / 1000, 1)
        today_len_cpd = int(300 * (today_cpd/len_max))
        lcd.rect(10, 0, today_len_cpd, 20, 0xd00000, 0x800000)

        for n in range(1, 8) :
            daily_cpd[n] = round((TotalPower[n][index] - TotalPower[n][0]) / 1000, 1)
            daily_tpd[n] = round((TotalPower[n][48] - TotalPower[n][0]) / 1000, 1)
            len_cpd = int(300 * (daily_cpd[n]/len_max))
            len_tpd = int(300 * (daily_tpd[n]/len_max))
            lcd.rect(10, n * 25, len_tpd, 20, 0xa0a000, 0x000000)
            lcd.rect(10, n * 25, len_cpd, 20, 0xa0a000, 0x0000a0)

        avg_cpd = round(sum(daily_cpd) / 7, 1)
        avg_tpd = round(sum(daily_tpd) / 7, 1)
        len_cpd = int(300 * (avg_cpd/len_max))
        len_tpd = int(300 * (avg_tpd/len_max))
        lcd.rect(10, 200, len_tpd, 20, 0xa0a000, 0x000000)
        lcd.rect(10, 200, len_cpd, 20, 0xa0a000, 0x00a000)

        x = 10 + today_len_cpd -1
        lcd.line(x, 0, x, 219, 0xd00000)
        lcd.triangle(x, 219, x + 4, 223, x - 4, 223, 0xd00000, 0xd00000)

        lcd.println(' Today : {:4.1f} kWh'.format(today_cpd), 10 , 0 + 3, color = 0xc0c0c0)
        for n in range(1, 8) :
            lcd.println(' {} : {:4.1f}  {:4.1f}'.format(n, daily_cpd[n], daily_tpd[n]), 10 , (n * 25) + 3, color = 0xc0c0c0)
        lcd.println(' AVG : {:4.1f}  {:4.1f}'.format(avg_cpd, avg_tpd), 10, 200 + 3, color = 0xc0c0c0)
    

    else :
        lcd.println('tpd_time is not defined yet', 0, 0, color = 0xffffff)


# 【page】積算電力量詳細 (当日と前日・1時間毎)
def draw_table() :
    # TotalPower[1][48] = TotalPower[0][0]
    hour_power = [[0 for i in range(24)] for j in range(2)] # 24時間x(前日, 当日）

    # 描画エリアのクリアとタイトル表示
    lcd.rect(0 , 0, 320, 224, 0x000000, 0x000000)
    lcd.font(lcd.FONT_Ubuntu)
    lcd.print('AM: Tdy:Ytdy:  Diff', 0, 0, color = 0xff8000)
    lcd.print('|', 155, 0, color = 0xffffff)
    lcd.print('PM: Tdy:Ytdy:  Diff' + '\n', 167, 0, color = 0xff8000)

    for n in range(0,12) :  # 0〜11
        nn = n * 2              # 元データが30分毎なのでステップを倍に
        for i in range(0,2) :     # i=0 当日, i=1 前日
            if (TotalPower[i][(nn + 2)] == 0) or (TotalPower[i][nn] == 0) :
                hour_power[i][n] = 0
            else : # 1時間あたりの定時積算電力量（単位：kWh）
                hour_power[i][n] = round((TotalPower[i][(nn + 2)] - TotalPower[i][nn]) / 1000, 1)

            if (TotalPower[i][(nn + 24 + 2)] == 0) or (TotalPower[i][nn + 24] == 0) :
                hour_power[i][n + 12] = 0
            else : # 1時間あたりの定時積算電力量（単位：kWh）
                hour_power[i][n + 12] = round((TotalPower[i][(nn + 24 + 2)] - TotalPower[i][nn + 24]) / 1000, 1)

        # 前日同時刻との差分
        if (hour_power[0][n] == 0) or (hour_power[1][n] == 0) : # 前日か当日が0なら差分0
            diff_AM     = 0
            diff_AM_str = '--- '
        else :
            diff_AM = hour_power[0][n] - hour_power[1][n]
            diff_AM_str = '{:3.1f}'.format(diff_AM)

        if (hour_power[0][n + 12] == 0) or (hour_power[1][n + 12] == 0) : # 前日か当日が0なら差分0
            diff_PM     = 0
            diff_PM_str = '--- '
        else :
            diff_PM = hour_power[0][n + 12] - hour_power[1][n + 12]
            diff_PM_str = '{:3.1f}\n'.format(diff_PM) ## '\n' or '\r\n'

        # 電力量が前日を超えていたら赤文字、前日以下なら緑文字
        if diff_AM > 0 :
            color_diff_AM = 0xee0000 # 赤
        else : 
            color_diff_AM = 0x00ee00 # 緑
        if diff_PM > 0 :
            color_diff_PM = 0xee0000 # 赤
        else :
            color_diff_PM = 0x00ee00 # 緑

        # 描画セクション
        lcd.print(' {:02}: '.format(n), color = 0xffff00)
        lcd.print(' {:3.1f}:  {:3.1f}: '.format(hour_power[0][n], hour_power[1][n]), color = 0xffffff)
        lcd.print(diff_AM_str, 149 - lcd.textWidth(diff_AM_str), (n + 1) * 16, color = color_diff_AM)
        lcd.print(' |  ', color = 0xffffff)
        lcd.print('{:02}: '.format(n + 12), color = 0xffff00)
        lcd.print(' {:3.1f}:  {:3.1f}: '.format(hour_power[0][n + 12], hour_power[1][n + 12]), color = 0xffffff)
        lcd.print(diff_PM_str, 315 - lcd.textWidth(diff_PM_str), (n + 1) * 16, color = color_diff_PM)

    # 当日(現時刻まで)および前日の24時間積算電力量と、前日比(%)を最下段に表示
    if 'tpd_time' in globals() :
        if TIME_TB.index(tpd_time) == 0 :
            index = 24
        else :
            index = int(TIME_TB.index(tpd_time) / 2)
   
        TotalPower_of_Yesterday = 0
        TotalPower_of_Today     = 0

        for n in range(index) :
            TotalPower_of_Yesterday += hour_power[1][n]
            TotalPower_of_Today     += hour_power[0][n]
        if TotalPower_of_Yesterday != 0 :
            TotalPower_Ratio = '{:.0%}'.format(TotalPower_of_Today / TotalPower_of_Yesterday)
        else :
            TotalPower_Ratio = 'N/A'

        TotalPower_of_Yesterday = '{:.1f}'.format(TotalPower_of_Yesterday)
        TotalPower_of_Today     = '{:.1f}'.format(TotalPower_of_Today)

        lcd.font(lcd.FONT_Default)
        lcd.print('TdyTotal:         YtdyTotal:         Ratio:', 0, 211, color = 0xff8000)
        lcd.font(lcd.FONT_Ubuntu)
    #     lcd.print(TotalPower_of_Today, 102-lcd.textWidth(str(TotalPower_of_Today)), 208, color = 0xffffff)
    #     lcd.print(TotalPower_of_Yesterday, 221-lcd.textWidth(str(TotalPower_of_Yesterday)), 208, color = 0xffffff)
    #     lcd.print(TotalPower_Ratio, 319-lcd.textWidth(str(TotalPower_Ratio)), 208, color = 0xffffff)
        lcd.print(TotalPower_of_Today, 69, 208, color = 0xffffff)
        lcd.print(TotalPower_of_Yesterday, 187, 208, color = 0xffffff)
        lcd.print(TotalPower_Ratio, 274, 208, color = 0xffffff)


# 【page】積算電力量詳細 (当日と直近7日間平均・1時間毎)
def draw_table2() :
    # TotalPower[1][48] = TotalPower[0][0]
    hour_power = [[0 for i in range(24)] for j in range(8)] # 24時間x(前日, 当日）
    avg_hour_power = [0] * 24

    # 描画エリアのクリアとタイトル表示
    lcd.rect(0 , 0, 320, 224, 0x000000, 0x000000)
    lcd.font(lcd.FONT_Ubuntu)
    lcd.print('AM: Tdy:Avg7: Diff', 0, 0, color = 0x1f77b4)
    lcd.print('|', 155, 0, color = 0xffffff)
    lcd.print('PM: Tdy:Avg7: Diff' + '\n', 167, 0, color = 0x1f77b4)

    for n in range(0, 12) :  # 0〜11
        nn = n * 2              # 元データが30分毎なのでステップを倍に
        for i in range(0,8) :     # i=0 当日, i=n n日前(7日前まで) 
            if (TotalPower[i][(nn + 2)] == 0) or (TotalPower[i][nn] == 0) :
                hour_power[i][n] = 0
            else : # 1時間あたりの定時積算電力量（単位：kWh）
                hour_power[i][n] = round((TotalPower[i][(nn + 2)] - TotalPower[i][nn]) / 1000, 1)

            if (TotalPower[i][(nn + 24 + 2)] == 0) or (TotalPower[i][nn + 24] == 0) :
                hour_power[i][n + 12] = 0
            else : # 1時間あたりの定時積算電力量（単位：kWh）
                hour_power[i][n + 12] = round((TotalPower[i][(nn + 24 + 2)] - TotalPower[i][nn + 24]) / 1000, 1)

    for n in range(0, 24) :
        sum_of_hour_power = 0
        for i in range(1, 8) :
            sum_of_hour_power += hour_power[i][n]
        avg_hour_power[n] = round(sum_of_hour_power / 7, 1)

    for n in range(0,12) :  # 0〜11
        # 前日同時刻との差分
        if (hour_power[0][n] == 0) or (avg_hour_power[n] == 0) : # 前日か当日が0なら差分0
            diff_AM     = 0
            diff_AM_str = '--- '
        else :
            diff_AM = hour_power[0][n] - avg_hour_power[n]
            diff_AM_str = '{:3.1f}'.format(diff_AM)

        if (hour_power[0][n + 12] == 0) or (avg_hour_power[n + 12] == 0) : # 前日か当日が0なら差分0
            diff_PM     = 0
            diff_PM_str = '--- '
        else :
            diff_PM = hour_power[0][n + 12] - avg_hour_power[n + 12]
            diff_PM_str = '{:3.1f}\n'.format(diff_PM) ## '\n' or '\r\n'

        # 電力量が前日を超えていたら赤文字、前日以下なら緑文字
        if diff_AM > 0 :
            color_diff_AM = 0xee0000 # 赤
        else : 
            color_diff_AM = 0x00ee00 # 緑
        if diff_PM > 0 :
            color_diff_PM = 0xee0000 # 赤
        else :
            color_diff_PM = 0x00ee00 # 緑

        # 描画セクション
        lcd.print(' {:02}: '.format(n), color = 0xffff00)
        lcd.print(' {:3.1f}:  {:3.1f}: '.format(hour_power[0][n], avg_hour_power[n]), color = 0xffffff)
        lcd.print(diff_AM_str, 149 - lcd.textWidth(diff_AM_str), (n + 1) * 16, color = color_diff_AM)
        lcd.print(' |  ', color = 0xffffff)
        lcd.print('{:02}: '.format(n + 12), color = 0xffff00)
        lcd.print(' {:3.1f}:  {:3.1f}: '.format(hour_power[0][n + 12], avg_hour_power[n + 12]), color = 0xffffff)
        lcd.print(diff_PM_str, 315 - lcd.textWidth(diff_PM_str), (n + 1) * 16, color = color_diff_PM)

    print('##########')
    print(avg_hour_power)
    print(hour_power[0])
    print('##########')

    # 当日(現時刻まで)および前日の24時間積算電力量と、前日比(%)を最下段に表示
    if 'tpd_time' in globals() :
        if TIME_TB.index(tpd_time) == 0 :
            index = 24
        else :
            index = int(TIME_TB.index(tpd_time) / 2)

        TotalPower_of_avg = 0
        TotalPower_of_Today = 0

        for n in range(index) :
            TotalPower_of_avg += avg_hour_power[n]
            TotalPower_of_Today += hour_power[0][n]
        if TotalPower_of_avg != 0 :
            TotalPower_Ratio = '{:.0%}'.format(TotalPower_of_Today / TotalPower_of_avg)
        else :
            TotalPower_Ratio = 'N/A'

        TotalPower_of_avg = '{:.1f}'.format(TotalPower_of_avg)
        TotalPower_of_Today = '{:.1f}'.format(TotalPower_of_Today)

        lcd.font(lcd.FONT_Default)
        lcd.print('TdyTotal:        Avg7Total:         Ratio:', 0, 211, color = 0x1f77b4)
        lcd.font(lcd.FONT_Ubuntu)
    #     lcd.print(TotalPower_of_Today, 102-lcd.textWidth(str(TotalPower_of_Today)), 208, color = 0xffffff)
    #     lcd.print(TotalPower_of_Yesterday, 221-lcd.textWidth(str(TotalPower_of_Yesterday)), 208, color = 0xffffff)
    #     lcd.print(TotalPower_Ratio, 319-lcd.textWidth(str(TotalPower_Ratio)), 208, color = 0xffffff)
        lcd.print(TotalPower_of_Today, 69, 208, color = 0xffffff)
        lcd.print(TotalPower_of_avg, 187, 208, color = 0xffffff)
        lcd.print(TotalPower_Ratio, 274, 208, color = 0xffffff)


# 設定ファイルの存在/中身チェック関数
def setfile_chk() :
    global AMPERE_LIMIT
    global AMPERE_RED
    global TIMEOUT

    scanfile_flg = False
    for file_name in uos.listdir('/flash') :
        if file_name == 'smm2_sub_set.json' :
            scanfile_flg = True
    if scanfile_flg :
        print('>> found [smm2_sub_set.json] !')
        with open('/flash/smm2_sub_set.json' , 'r') as f :
            config = ujson.load(f)

        for index in ['AMPERE_RED', 'AMPERE_LIMIT', 'TIMEOUT'] :
            if index not in config :
                raise Exception('{} is not defined in smm2_sub_set.json'.format(index))

        AMPERE_RED = config['AMPERE_RED']
        AMPERE_LIMIT = config['AMPERE_LIMIT']
        TIMEOUT = config['TIMEOUT']
            
        if AMPERE_RED > 0 and AMPERE_RED <= 1 and AMPERE_LIMIT >= 10 and TIMEOUT > 0 :
            scanfile_flg = True
        else :
            print('>> [smm2_sub_set.json] Illegal!!')
            scanfile_flg = False
    else :
        print('>> no [smm2_sub_set.json] !')

    if scanfile_flg == False : # [smm2_sub_set.json]が読めないまたは異常値の場合はデフォルト値が設定される
        print('>> Illegal [smm2_sub_set.json] !')
        AMPERE_RED = 0.7    # デフォルト値：契約アンペア数の何割を超えたら警告 [0.1～1.0]
        AMPERE_LIMIT = 40   # デフォルト値：アンペア契約値（ブレーカー落ち警報目安で使用）
        TIMEOUT = 30        # デフォルト値：電力値更新のタイムアウト設定値(秒) この秒数以上更新無ければ電力値非表示となる

    print('- AMPERE_RED: ' + str(AMPERE_RED))
    print('- AMPERE_LIMIT: ' + str(AMPERE_LIMIT))
    print('- TIMEOUT: ' + str(TIMEOUT))

    return scanfile_flg


# 文字列が16進数かどうか判別
def _is_hex(val) :
    try:
        int(val, 16)
        return True
    except ValueError as e:
        return False


# 履歴データの初期化
def get_init_data() :
    global time_of_REQ, init_day, init_flag, coefficient
    print('')

    print(' ================================== 初期化 ==================================')

    time_of_REQ = 0
    init_day = 0
    coefficient = 0
    init_flag = [0] * 8
        
    speaker.setVolume(0.1)
    speaker.tone(330, 150)


### 変数初期設定 ###

# 親機のMACアドレス
esp_mac_master = 'ff:ff:ff:ff:ff:ff'

# 画面の明るさ
brightness = 15

# 表示モード関係
disp_mode = 'main'
NPD_data = 'timeout'
lcd_off = False
beep_on = True

# 測定値初期値
now_power = 0
power_kwh = 0
charge = 0
collect = '****-**-**'
update = '****-**-**'

# 履歴データ(30分毎：(48 + 1) * (7 + 1)日間)
TotalPower = [[0 for i in range(49)] for j in range(8)]

# 履歴データ取得
coe_flag = 0
time_of_REQ = 0
time_of_REQ2 = 0
init_day = 0
init_flag = [0] * 8
send_init_REQ = 0
coefficient = 0

# カウンター、タイムアウト処理
count = 0
coe_c = 0
init_c = 0
i_step = 0
now_power_time = utime.time()

# ページ設定
draw_page = [
    draw_main,      # メインページ：瞬間電力値、検針日以降の電力量、電気代
    draw_graph_tp,  # 電力量グラフ (当日と前日・30分毎)
    draw_detail,    # 電力量グラフ (随時比較・当日と直近7日間)
    draw_table,     # 積算電力量詳細 (当日と前日・1時間毎)
    draw_table2,    # 積算電力量詳細 (当日と直近7日間平均・1時間毎)
    ]
page = 0

# Colormap (tab10)
colormap = (
    0x1f77b4,  # tab0:blue
    0xff7f0e,  # tab1:orange
    0x2ca02c,  # tab2:green
    0xd62728,  # tab3:red
    0x9467bd,  # tab4:purple
    0x8c564b,  # tab5:brown
    0xe377c2,  # tab6:pink
    0x7f7f7f,  # tab7:gray
    0xbcbd22,  # tab8:olive
    0x17becf,  # tab9:cyan
    )

# 表示色設定
bgcolor = 0x000000      # Background color
uncolor = 0xa0a0a0      # Unit color
color1 = colormap[0]    # Current value color
color2 = colormap[1]    # Total value color
color3 = colormap[3]    # Limit over color
grayout = 0x303030
yellow = 0x404000

# 時間帯インデックス(30分毎：0〜47)
TIME_TB = ["00:00:00", "00:30:00", \
           "01:00:00", "01:30:00", \
           "02:00:00", "02:30:00", \
           "03:00:00", "03:30:00", \
           "04:00:00", "04:30:00", \
           "05:00:00", "05:30:00", \
           "06:00:00", "06:30:00", \
           "07:00:00", "07:30:00", \
           "08:00:00", "08:30:00", \
           "09:00:00", "09:30:00", \
           "10:00:00", "10:30:00", \
           "11:00:00", "11:30:00", \
           "12:00:00", "12:30:00", \
           "13:00:00", "13:30:00", \
           "14:00:00", "14:30:00", \
           "15:00:00", "15:30:00", \
           "16:00:00", "16:30:00", \
           "17:00:00", "17:30:00", \
           "18:00:00", "18:30:00", \
           "19:00:00", "19:30:00", \
           "20:00:00", "20:30:00", \
           "21:00:00", "21:30:00", \
           "22:00:00", "22:30:00", \
           "23:00:00", "23:30:00"]


### 初期化 ###

# WiFi設定
wifiCfg.autoConnect(lcdShow=True)
print('>> WiFi init OK')

# WiFi & ESP NOW設定
wifiCfg.wlan_ap.active(True)
espnow.init()
espnow.add_peer(esp_mac_master, id = 1)
print('>> ESP NOW init')

# 初期設定ファイル読込み
setfile_chk()

# RTC設定
ntp = ntptime.client(host='jp.pool.ntp.org', timezone=9)
print('>> RTC init OK')

# BEEP音鳴らしスレッド起動
_thread.start_new_thread(beep_sound, ())
print('>> BEEP Sound thread ON')

# ボタン検出スレッド起動
btnA.wasReleased(turn_lcd_off)
btnB.wasReleased(flip_page)
btnC.wasReleased(turn_beep_off)
btnB.pressFor(0.8, get_init_data)
print('>> Button Check thread ON')

# 画面初期化
setScreenColor(0x000000)
lcd.setBrightness(brightness) #バックライト輝度調整
lcd.clear()

# 初期画面表示
draw_page[page]()
draw_beep_icon()
print('>> Disp init OK')


### メインループ ###

while True:

    # 瞬間電力値の更新が[TIMEOUT]秒以上途絶えたら、電力値<薄黄色>表示　
    if utime.time() - now_power_time >= TIMEOUT : 
        if NPD_data == 'good' :
            NPD_data = 'lost'
            draw_w()
        
    # 積算電力履歴係数をリクエスト
    if coefficient == 0 :
        if coe_flag == 0 :
            espnow.send(id = 1, data='COE'+str(coe_c))
            print('send COE', init_day,coe_c)
            # utime.sleep(0.5)
            coe_flag = 1
            time_of_REQ2 = utime.time()
            coe_c += 1
            if coe_c == 10000 : coe_c = 0
        elif utime.time() - time_of_REQ2 >= 1:
            coe_flag = 0
            print('')
            print('clear COE flag', init_day)

    # 履歴データをリクエスト
    if (sum(init_flag) < 8) and (coefficient != 0) : 
        if send_init_REQ == False :
            espnow.send(id = 1, data='REQ'+str(init_day)+'_'+str(init_c))
            print('send REQ',init_day,init_c)
            send_init_REQ = True
            time_of_REQ = utime.time()
            init_c += 1
            if init_c == 10000 : init_c = 0
        elif utime.time() - time_of_REQ >= 1:
            send_init_REQ = False
            print('')
            print('clear send_init_REQ',send_init_REQ)

    # 親機からデータを受信(ESP NOW)
    d = espnow.recv_data()

    # 受信データ処理
    if (len(d[2]) > 0) :
        r_key  = str(d[2][:4].decode().strip())
        r_data = d[2][4:].strip()

        print('')
        print('Key  = ', r_key)
        print('Data = ', r_data)

        count = 0
        
        # 親機起動時処理
        if r_key == 'BOOT' :
            get_init_data()
            print('BOOT処理')

        # 親機〜スマートメーター間タイムアウト通知受信処理
        elif r_key == 'TOUT' :
            if NPD_data != 'timeout' :
                NPD_data = 'timeout'
                draw_w()

        # 積算電力履歴係数受信処理
        elif r_key == 'COE=' :
            coefficient = float(r_data.decode())
            print('recv COE')
            coe_flag = 0

        # 履歴データ受信処理
        elif r_key[:2] == 'ID' :
            d2 = binascii.hexlify(r_data)
            n = int(r_key[2:3].strip())

            print(init_flag[n],init_flag)
            if (n == init_day) and (init_flag[n] != 1) :  ###
                # init_day = n + 1    ### 要検討
                # continue            ###
            
                print('data get',n)
                print(d2)
                for k in range(0,48) :
                    if int(d2[(k*8):(k*8)+8],16) > 0x05f5e0ff :
                        TotalPower[n][k] = 0
                    else :
                        TotalPower[n][k] = int(d2[(k*8):(k*8)+8],16) * coefficient * 1000
                        print(TotalPower[n][k], end = '/')
                if n < 7 :
                    TotalPower[n + 1][48] = TotalPower[n][0]

                init_flag[n] = 1
            
                print('')
                print(n,TotalPower[n])
                print(init_flag)
                print('Init_day1',init_day)
                
                init_day = n + 1
                send_init_REQ = 0

                if init_day == 8 :
                    speaker.setVolume(0.1)
                    speaker.tone(330, 150)
                    lcd.circle(311, 231, 7, 0x2acf00, 0x2acf00)
                    i_step = 0

                # ページ再描画
                draw_page[page]()

        # 瞬間電力値受信処理
        elif r_key == 'NPD=' :
            now_power_time = utime.time()
            if not now_power == int(r_data.decode()) :
                now_power = int(r_data.decode())
                NPD_data = 'good'
                draw_w()

        # 積算電力量受信処理
        elif r_key == 'TPD=' :
            tpd_t = r_data.decode().strip().split('/')
            tpd_wh = int(float(tpd_t[0]) * 1000) 
            tpd_tt = tpd_t[1].strip().split(' ')
            tpd_date = tpd_tt[0]
            tpd_time = tpd_tt[1]
            collect = tpd_t[2]
            update = tpd_t[3]
            power_kwh = float(tpd_t[4])
            charge = tpd_t[5]

            # 日跨ぎ処理
            if TIME_TB.index(tpd_time) == 0 :
                TotalPower[0][48] = tpd_wh
            else :
                if (TIME_TB.index(tpd_time) == 1) and (TotalPower[0][2] != 0) :
                    for n in range(7, 0, -1) :
                        TotalPower[n] = TotalPower[n - 1]
                    TotalPower[0] = [0] * 49
                    TotalPower[0][0] = TotalPower[1][48]
                TotalPower[0][TIME_TB.index(tpd_time)] = tpd_wh

            # 積算電力量の最終受信日付表示
            lcd.rect(0, 225, 229, 240, 0x000000, 0x000000)
            lcd.font(lcd.FONT_Default)
            lcd.print(tpd_date + ' ' + tpd_time, 2, 226, 0x808080)

            # ページ再描画
            draw_page[page]()

    # デバグ用マーカー表示(シリアル出力)
    print('*', end ='')
    count += 1
    if count >= 80 :
        print('')
        count = 0

    # 履歴データ受信インジケーター表示
    if sum(init_flag) < 8 :
        draw_indicator(311, 231, 7, i_step, 15)
        i_step += 1
        if i_step == 15 : i_step = 0


    gc.collect()
    utime.sleep(0.1)