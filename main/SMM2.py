from m5stack import *
import binascii
import calc_charge
import espnow
import logging
import machine
import ntptime
import ujson
import uos
import utime
import wifiCfg
from BP35A1 import BP35A1

# 子機のMACアドレス
esp_mac_slave1 = 'ff:ff:ff:ff:ff:ff'

# Global variables
logger = None               # Logger object
logger_name = 'SMM2'        # Logger name
level = logging.DEBUG       # Log level（'CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG')
bp35a1 = None               # BPA35A1 object
config = {}                 # Configuration
orient = lcd.LANDSCAPE      # Display orientation
ambient_client = None       # Ambient instance
max_retries = 30            # Maximum number of times to retry
default_collect_date = 1    # 検針日の初期値（検針日カレンダーがない場合）

# Colormap (tab10)
colormap = (
    0x1f77b4,  # tab:blue
    0xff7f0e,  # tab:orange
    0x2ca02c,  # tab:green
    0xd62728,  # tab:red
    0x9467bd,  # tab:purple
    0x8c564b,  # tab:brown
    0xe377c2,  # tab:pink
    0x7f7f7f,  # tab:gray
    0xbcbd22,  # tab:olive
    0x17becf,  # tab:cyan
    )

bgcolor = 0x000000      # Background color
uncolor = 0xa0a0a0      # Unit color
color1 = colormap[0]    # Current value color
color2 = colormap[1]    # Total value color
color3 = colormap[3]    # Limit over color
grayout = 0x303030

data_mute = False
ampere_limit_over = False

AMPERE_RED      = 0.7
AMPERE_LIMIT    = 40
TIMEOUT         = 20


def flip_lcd_orientation():
    """
    Aボタン : 画面の上下反転
    """
    global orient
    if orient == lcd.LANDSCAPE:
        orient = lcd.LANDSCAPE_FLIP
    else:
        orient = lcd.LANDSCAPE
    logger.info('Set screen orient: %s', orient)
    lcd.orient(orient)
    lcd.clear()

    draw_main()


def draw_main() :
    instantaneous_amperage(amperage)
    instantaneous_power(power_kw)
    collect_range(collect, update)
    monthly_power(power_kwh)
    monthly_charge(charge)


def checkWiFi(arg):
    """
    WiFi接続チェック
    """
    if not wifiCfg.is_connected():
        logger.warn('Reconnect to WiFi')
        if not wifiCfg.reconnect():
            logger.warn('Rest')
            machine.reset()


def status(message):
    """
    ステータスの表示
    """
    (x, y, w, h) = (3, 50, 237, 35)
    lcd.rect(x, y, w, h, bgcolor, bgcolor)

    logger.info(message)
    lcd.font(lcd.FONT_Ubuntu)
    lcd.print(message, lcd.CENTER, lcd.CENTER, uncolor)


def progress(percent):
    """
    プログレスバーの表示
    """
    (w, h) = lcd.screensize()
    x = (w - 6) * percent // 100
    lcd.rect(3, h - 12, x, 12, bgcolor, color1)
    lcd.rect(3 + x, h - 12, w - 6, 12, bgcolor, bgcolor)
    lcd.font(lcd.FONT_DefaultSmall, transparent=True)
    lcd.text(lcd.CENTER, h - 10, '{}%'.format(percent), uncolor)


def instantaneous_amperage(amperage):
    """
    瞬時電流計測値の表示
    """
    if ampere_limit_over :
        fc = color3
    else :
        if data_mute :
            fc = grayout
        else :
            fc = color1
        
    (x, y, w, h) = (3, 3, 113, 47)
    lcd.rect(x, y, w, h, bgcolor, bgcolor)

    amperage = str(int(amperage))
    lcd.font(lcd.FONT_DejaVu40)
    lcd.print(amperage, x + 51 - lcd.textWidth(amperage), y + 5, fc)
    lcd.font(lcd.FONT_DejaVu18)
    lcd.print('A', lcd.LASTX, y + (h - 18), uncolor)

    contract_amperage = str(int(config['contract_amperage']))
    lcd.font(lcd.FONT_DejaVu24)
    lcd.print(contract_amperage, x + 65, y + (h - 24), uncolor)
    lcd.font(lcd.FONT_DejaVu18)
    lcd.print('A', lcd.LASTX, y + (h - 18), uncolor)


def instantaneous_power(power_kw):
    """
    瞬時電力計測値の表示
    """
    if ampere_limit_over :
        fc = color3
    else :
        if data_mute :
            fc = grayout
        else :
            fc = color1

    (x, y, w, h) = (116, 3, 124, 47)
    lcd.rect(x, y, w, h, bgcolor, bgcolor)

    power_kw = str(int(power_kw))
    lcd.font(lcd.FONT_DejaVu40)
    lcd.print(power_kw, x + w - 20 - lcd.textWidth(power_kw), y + 5, fc)
    lcd.font(lcd.FONT_DejaVu18)
    lcd.print('W', lcd.LASTX, y + (h - 18), uncolor)


def collect_range(collect, update):
    """
    今月（検針日を起点）の日付範囲を表示
    """
    (x, y, w, h) = (3, 50, 237, 25)
    lcd.rect(x, y, w, h, bgcolor, bgcolor)

    s = '{}~{}'.format(collect[5:10], update[5:10])
    lcd.font(lcd.FONT_DejaVu18)
    lcd.print(s, int(x + (w - lcd.textWidth(s)) / 2), y + 5, uncolor)


def monthly_power(power_kwh):
    """
    今月（検針日を起点）の電力量の表示
    """
    (x, y, w, h) = (3, 75, 107, 60)
    lcd.rect(x, y, w, h, bgcolor, bgcolor)

    power_kwh = str(int(power_kwh))
    lcd.font(lcd.FONT_DejaVu40)
    lcd.print(power_kwh, x + w - lcd.textWidth(power_kwh)-15, y + 5, color2)
    lcd.font(lcd.FONT_DejaVu18)
    lcd.print('kWh', x + w - lcd.textWidth('kWh')-15, y + 40, uncolor)


def monthly_charge(charge):
    """
    今月（検針日を起点）の電気料金の表示
    """
    (x, y, w, h) = (110, 75, 130, 60)
    lcd.rect(x, y, w, h, bgcolor, bgcolor)

    charge = str(int(charge))
    lcd.font(lcd.FONT_DejaVu40)
    lcd.print(charge, x + w - lcd.textWidth(charge), y + 5, colormap[1])
    lcd.font(lcd.FONT_DejaVu18)
    lcd.print('Yen', x + w - lcd.textWidth('Yen'), y + 40, uncolor)
    

def check_timeout(np_c):
    """
    TIMEOUT秒以上、スマートメーターからのデータが途切れた場合は文字色をグレー表示
    """
    global data_mute
    if (utime.time() - np_c) >= TIMEOUT :
        data_mute = True
        instantaneous_amperage(amperage)
        instantaneous_power(power_kw)
        espnow.broadcast(data=str('TOUT')) # ESP NOW で timeout を子機に通知


def get_init_data(n) :
    history_of_power = bp35a1.InitTotalPower(n)
    init_data = bytes('ID' + str(n) + '=', 'UTF-8') + binascii.unhexlify(history_of_power)
    return(init_data)


if __name__ == '__main__':

    try:
        # Initialize logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

        # Initialize lcd
        lcd.clear()

        # Connecting Wi-Fi
        # status('Connecting Wi-Fi')
        lcd.orient(lcd.PORTRAIT_FLIP)
        wifiCfg.autoConnect(lcdShow=True)
        if not wifiCfg.is_connected():
            raise Exception('Can not connect to WiFi.')
        lcd.clear()
        lcd.orient(orient)

        # Start checking the WiFi connection
        machine.Timer(0).init(period=60 * 1000,
                              mode=machine.Timer.PERIODIC,
                              callback=checkWiFi)

        # ESP NOW設定
        import espnow
        espnow.init()
        espnow.add_peer(esp_mac_slave1, id = 2)
        status('ESP NOW init')

        # Set Time
        status('Set Time')
        ntp = ntptime.client(host='jp.pool.ntp.org', timezone=9)
        print('## ntp ##', ntp, type(ntp)) #####################################################

        # Start button thread
        btnA.wasPressed(flip_lcd_orientation)

        # Load configuration
        status('Load configuration')
        config_file = 'smm2_main_set.json' # 基本設定ファイル名
        mday_calendar_file = 'calendar_' + str(utime.localtime()[0]) + '.json' # 検針日カレンダーファイル名
 
        with open(config_file) as f: # 基本設定ファイルの読み込み
            config = ujson.load(f)

        is_cal = False
        for file_name in uos.listdir() : # 検針日カレンダーファイルの有無をチェック
            if file_name == mday_calendar_file :
                is_cal = True
        if is_cal : # 検針日カレンダーファイルがあれば読み込む
            with open(mday_calendar_file) as f:
                config_cal = ujson.load(f)
            logger.info('calendar file is founded !')
        else : # 検針日カレンダーファイルがなければ基本設定ファイルの値を使う
            config_cal = {'collect_date':[config['collect_date']]*13}
            logger.info('calendar file is NOT founded !')

        config.update(config_cal) # 基本設定と検針日カレンダーを結合

        for index in [
                'id', 'password', 'contract_amperage', 'collect_date',
                'charge_func'
        ]:
            if index not in config:
                raise Exception('{} is not defined in config.json'.format(index))

        if 'ambient' in config:
            for index in ['channel_id', 'write_key']:
                if index not in config['ambient']:
                    raise Exception(
                        '{} is not defined in config.json'.format(index))

        # Create objects
        status('Create objects')
        bp35a1 = BP35A1(config['id'],
                        config['password'],
                        config['contract_amperage'],
                        config['collect_date'],
                        progress_func=progress,
                        logger_name=logger_name)
        logger.info('BP35A1 config: (%s, %s, %s, %s)', config['id'],
                    config['password'], config['contract_amperage'],
                    config['collect_date']) 
        calc_charge = eval('calc_charge.{}'.format(config['charge_func']))
        logger.info('charge function: %s', calc_charge.__name__)
        if 'ambient' in config:
            import ambient
            ambient_client = ambient.Ambient(config['ambient']['channel_id'],
                                             config['ambient']['write_key'])
            logger.info('Ambient config: (%s, %s)',
                        config['ambient']['channel_id'],
                        config['ambient']['write_key'])

        # Connecting to Smart Meter
        status('Connecting SmartMeter')
        (channel, pan_id, mac_addr, lqi, coefficient) = bp35a1.open()
        logger.info('Connected. BP35A1 info: (%s, %s, %s, %s)', channel,
                    pan_id, mac_addr, lqi)

        # Start monitoring
        print('')
        status('Start monitoring')

        # 親機起動を通知
        espnow.broadcast(data='BOOT')

        amperage = power_kw = power_kwh = charge = 0
        update = collect = 'YYYY-MM-DD hh:mm:ss'
        retries = 0
        
        np_c = utime.time() - 100  # NPD タイマー
        tp_c = utime.time() - 100  # TPD タイマー
        am_c = utime.time() - 100  # Ambient タイマー
        pg_c = utime.time() - 100  # ping タイマー

        tp_flag = False
        coe_flag = False
        init_flag = [1] * 8 ## 初期値=1 としてゴミリクエストを拒否

        # メインループ
        while retries < max_retries:

            d   = espnow.recv_data()
            key = str(d[2].decode())
            if key != '' : print('recv : key =', key, end = '')

            # 'COE' 積算電力係数のリクエストに応答
            if key.startswith('COE') :
                if coe_flag == 0 :
                    espnow.send(id = 2, data=str('COE=' + str(coefficient)))
                    coe_flag = 1
                    init_flag = [0] * 8
                    tp_flag = False
                    print('')
                    print('send COE')
                    print('clear init_flag')
                else :
                    coe_flag += 1
                    print('')
                    print('coe section ### SKIP ###',coe_flag)
                    if coe_flag >= 10 :
                        coe_flag = 0
                        print('')
                        print('coe section ### RESET ###', coe_flag)

            # 'REQ' 定期積算電力量初期値のリクエストに応答
            if key.startswith('REQ') :
                n = int(key[3:4])
                print(' / ',n, init_flag[n])

                if init_flag[n] == 0 :
                    try :
                        init_flag[n] = 1
                        print('== accept a request ==', key,n,init_flag[n])
                        init_data = get_init_data(n)
                        espnow.send(id = 2, data=init_data)
                        logger.info('EPS NOW Sending ' + str('init data =' + str(init_data)))
                        print('')
                        print('send init_DATA for REQ',n,init_flag[n])
                    except Exception as e :
                        init_flag[n] = 0
                        print('error Clear init_flag',n,init_flag[n])
                        logger.error(e)
                else :
                    init_flag[n] += 1
                    print('REQ section ### SKIP ###', n,init_flag[n])
                    if init_flag[n] >= 10 :
                        init_flag[n] = 0
                        print('REQ section ### RESET ###', n,init_flag[n])

                coe_flag = 0
                print(n,init_flag)


            # 瞬時電力・瞬時電流　取得 ＆ 表示 ＆ 子機送信：Updated every 10 seconds
            if (utime.time() - np_c) >=  10 :
                logger.info('## instant amperage & power ##')
                try:
                    # 取得
                    (_, amperage) = bp35a1.instantaneous_amperage()
                    (update, power_kw) = bp35a1.instantaneous_power()
                    
                    # 警告域チェック
                    if (amperage >= AMPERE_LIMIT * AMPERE_RED) or (power_kw >= AMPERE_LIMIT * AMPERE_RED * 100) :
                        ampere_limit_over = True
                    else :
                        ampere_limit_over = False
                    data_mute = False

                    # 表示
                    instantaneous_amperage(amperage)
                    instantaneous_power(power_kw)

                    # 子機送信
                    espnow.broadcast(data=str('NPD=' + str(power_kw))) # ESP NOW で瞬時電力発信
                    logger.info('EPS NOW Sending ' + str('NPD=' + str(power_kw)))

                    print('')
                    retries = 0
                    np_c = utime.time()

                except Exception as e:
                    print('============ TTIIMMEE OOUUTT!! ============')
                    logger.error(e)
                    retries += 1
                    logger.info('## added retries by instant ## retries = ' + str(retries))

                check_timeout(np_c)

            # 積算電力量　取得 ＆ 表示 & 子機送信：Updated every 10 * 60 seconds
            if ((utime.time() - tp_c) >= (10 * 60)) or ((not tp_flag) and ((utime.time() - tp_c) >= 60)) :
                logger.info('## monthly power & monthly charge ##')
                try:
                    # 取得
                    (collect, power_kwh, created, power) = bp35a1.monthly_power()
                    charge = calc_charge(config['contract_amperage'], power_kwh)

                    # 表示
                    collect_range(collect, update)
                    monthly_power(power_kwh)
                    monthly_charge(charge)

                    # 子機送信
                    TPD = str('TPD=' + str(power) + '/' + str(created) + '/' + str(collect) + '/' + str(update) + '/' + str(power_kwh) +'/' + str(charge))
                    espnow.broadcast(data=TPD)
                    logger.info('EPS NOW Sending ' + TPD)

                    print('')
                    retries = 0
                    tp_c = utime.time()
                    tp_flag = True

                except Exception as e:
                    print('============ TTIIMMEE OOUUTT!! ============')
                    logger.error(e)
                    retries += 1
                    tp_flag = False
                    tp_c = utime.time()

                check_timeout(np_c)

            # Ambientデータ送信：Send every 30 seconds
            if (utime.time() - am_c) >= 30 :
                try:
                    if ambient_client:
                        result = ambient_client.send({
                            'd1': amperage,
                            'd2': power_kw,
                            'd3': power_kwh,
                            'd4': charge
                        })
                        if result.status_code != 200:
                            raise Exception(
                                'ambient.send() failed. status: %s',
                                result.status_code)
                        retries = 0
                        am_c = utime.time()
                except Exception as e:
                    print('============ TTIIMMEE OOUUTT!! ============')
                    logger.error(e)
                    retries += 1

            # 動作確認：Ping every 1 hour
            if (utime.time() - pg_c) >= (60 * 60) :
                bp35a1.skPing()
                pg_c = utime.time()

            utime.sleep(0.5)
            

    finally:
        print('========== system reset ==========',retries)
        machine.reset()
