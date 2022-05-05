from m5stack import lcd
import logging
import machine
import utime
import uos

# global variables
logger = None

# decorator
def iofunc(func):
    def wrapper(obj, *args):
        if (args and (type(args[0]) != int)):
            logger.debug('> %s', args[0].strip())
        response = func(obj, *args)
        if (response):
            logger.debug('< %s', response.decode().strip())
        # utime.sleep(0.5)
        return response

    return wrapper


def skfunc(func):
    def wrapper(obj, *args, **kwds):
        logger.debug('%s', func.__name__)
        # utime.sleep(0.5)
        response = func(obj, *args, **kwds)
        if response:
            logger.info('%s: Succeed', func.__name__)
        else:
            logger.error('%s: Failed', func.__name__)
        # utime.sleep(0.5)
        return response

    return wrapper


def propfunc(func):
    def wrapper(obj, *args, **kwds):
        logger.info('%s: %s', func.__name__, args)
        response = func(obj, *args, **kwds)
        logger.info('%s: %s', func.__name__, response)
        # utime.sleep(0.5)
        return response

    return wrapper


# date time function
def day_of_week(y, m, d):
    t = (0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4)
    if m < 3:
        y -= 1
    return (y + y // 4 - y // 100 + y // 400 + t[m - 1] + d) % 7


def days_of_year(y, m, d):
    t = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if m > 2 and (y % 4 == 0) and (y % 100 == 0 or y % 400 != 0):
        d += 1
    return sum(t[:m - 1]) + d


def localtime():
    offset = 9 * 3600  # JST
    return utime.localtime()


def strftime(tm, *, fmt='{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'):
    (year, month, mday, hour, minute, second) = tm[:6]
    return fmt.format(year, month, mday, hour, minute, second)


def days_after_collect(collect_date): # 検針日からの経過日数
    (year, month, today) = localtime()[:3]
    days1 = days_of_year(year, month, today)
    if today < collect_date[month] :    # 検針日より前なら
        mday = collect_date[month - 1]      # 前月の検針日
        if month == 1 :                     # 検針日より前かつ1月なら
            return 31 - mday + today
        else :                              # 検針日より前で1月以外なら
            days2 = days_of_year(year, month - 1, mday)
    else :                              # 検針日以後なら
        mday = collect_date[month]          # 当月の検針日
        days2 = days_of_year(year, month, mday)
    return days1 - days2

#     if month == 1 and today < collect_date[month]:
#         return 31 - collect_date[month - 1] + today
#     days1 = days_of_year(year, month, today)
#     if today < collect_date[month]:
#         month -= 1
#         days2 = days_of_year(year, month, collect_date[month])
#     else:
#         days2 = days_of_year(year, month, collect_mday[month])
#     return days1 - days2

# オリジナル
# def days_after_collect(collect_mday):
#     (year, month, mday) = localtime()[:3]
#     if month == 1:
#         return 31 - collect_mday + mday
#     days1 = days_of_year(year, month, mday)
#     if mday < collect_mday:
#         month -= 1
#     days2 = days_of_year(year, month, collect_mday)
#     return days1 - days2

def last_colect_day(collect_date) : # 直近の検針日
    (year, month, today) = localtime()[:3]
    if today < collect_date[month] :    # 検針日より前なら
        mday = collect_date[month - 1]      # 前月の検針日
        if month == 1 :                     # 検針日より前かつ1月なら
            year -= 1                           # 前年
            month = 12                          # 12月
        else :                              # 検針日より前で1月以外なら
            month -= 1                          # 前月
    else :                              # 検針日以後なら
        mday = collect_date[month]          # 当月の検針日
    return strftime((year, month, mday, 0, 0, 0))

# オリジナル
# def last_colect_day(collect_mday):
#     (year, month, mday) = localtime()[:3]
#     if month == 1:
#         return (year - 1, 12, 31 - collect_mday + mday)
#     if mday < collect_mday:
#         month -= 1
#     return strftime((year, month, collect_mday, 0, 0, 0))

# クラス BP35A1 定義
class BP35A1:

    global timeout20
    global timeout60
    timeout20 = 20
    timeout60 = 60
    
    def __init__(self,
                 id,
                 password,
                 contract_amperage,
                 collect_date,
                 *,
                 progress_func=None,
                 logger_name=__name__):
        print('===== BP35A1 =====')
        global logger
        logger = logging.getLogger(logger_name)
        self.progress = progress_func if progress_func else lambda _: None

        self.uart = machine.UART(1, tx=0, rx=26)
        self.uart.init(115200, bits=8, parity=None, stop=1, timeout=2000)

        self.id = id
        self.password = password
        self.contract_amperage = int(contract_amperage)
        self.collect_date = collect_date
        self.channel = None
        self.pan_id = None
        self.mac_addr = None
        self.lqi = None

        self.ipv6_addr = None
        self.power_coefficient = None
        self.power_unit = None

        # self.timeout   = 20
        # self.timeout60 = 60

    def flash(self):
        utime.sleep(0.5)
        while self.uart.any():
            _ = self.uart.read()
        self.uart.write('\r\n')
        utime.sleep(0.5)

    def need_scan(self):
        return not (self.channel and self.pan_id and self.mac_addr
                    and self.lqi)

    def reset_scan(self):
        for file_name in uos.listdir('/flash') :
            if file_name == 'SMM2_SCAN.txt' :
                uos.remove('/flash/SMM2_SCAN.txt')
        self.channel = self.pan_id = self.mac_addr = self.lqi = None
        self.power_coefficient = None
        self.power_unit = None

# 初期化関数セクション
    @skfunc
    def skInit(self):
        return self.exec_command('SKRESET') and self.exec_command('SKSREG SFE 0') 

    # ROPT で ERXUDPデータ表示形式を確認して、バイナリモードならASCIIモードに変更
    @iofunc
    def set_WOPT(self):
        self.writeln('ROPT')
        utime.sleep(0.5)
        mode_flg = False
        while True:
            ln = self.readln()
            if ln.decode().startswith('OK 01') :
                print(' - BP35A1 ASCII Mode')
                break
            elif ln.decode().startswith('OK 00') :
                print(' - BP35A1 Binary Mode')
                mode_flg = True
                break
            utime.sleep(0.5)
        
        if mode_flg :
            self.writeln('WOPT 01')
            print('>> BP35A1 ASCII Mode set')
            utime.sleep(0.5)
            while True :    #Echo back & OK wait!
                ln = self.readln()
                if ln.decode().startswith('OK') :
                    print('>> BP35A1 ASCII Mode set OK')
                    break
        
    @skfunc
    def skVer(self): # 未使用
        return self.exec_command('SKVER')

    @skfunc
    def skTerm(self):
        return self.exec_command('SKTERM')

    @skfunc
    def skSetPasswd(self):
        return self.exec_command('SKSETPWD C ', self.password)

    @skfunc
    def skSetID(self):
        return self.exec_command('SKSETRBID ', self.id)

    # Wi-SUN_SCAN.txtの存在/中身チェック関数
    @skfunc
    def smm2_scan_filechk(self):
        # global channel
        # global panid
        # global macadr
        # global lqi

        scanfile_flg = False
        for file_name in uos.listdir('/flash') :
            if file_name == 'SMM2_SCAN.txt' :
                scanfile_flg = True
        if scanfile_flg :
            print('>> found [SMM2_SCAN.txt] !')
            with open('/flash/SMM2_SCAN.txt' , 'r') as f :
                for file_line in f :
                    filetxt = file_line.strip().split(':')
                    if filetxt[0] == 'Channel' :
                        self.channel = filetxt[1]
                        print('- Channel: ' + self.channel)
                    elif filetxt[0] == 'Pan_ID' :
                        self.pan_id = filetxt[1]
                        print('- Pan_ID: ' + self.pan_id)
                    elif filetxt[0] == 'MAC_Addr' :
                        self.mac_addr = filetxt[1]
                        print('- MAC_Addr: ' + self.mac_addr)
                    elif filetxt[0] == 'LQI' :
                        self.lqi = filetxt[1]
                        print('- LQI: ' + self.lqi)
                    elif filetxt[0] == 'COEFFICIENT' :
                        print('- COEFFICIENT: ',filetxt[1])
                        self.power_coefficient = int(filetxt[1])
                        print('- COEFFICIENT: ' + str(self.power_coefficient))
                    elif filetxt[0] == 'UNIT' :
                        print('- UNIT: ',filetxt[1])
                        self.power_unit = float(filetxt[1])
                        print('- UNIT: ' + str(self.power_unit))
            if len(self.channel) == 2 and len(self.pan_id) == 4 and len(self.mac_addr) == 16 and len(self.lqi) == 2:
                print('self.channel =', self.channel, type(self.channel))
                print('self.pan_id =', self.pan_id, type(self.pan_id))
                print('self.mac_addr =', self.mac_addr, type(self.mac_addr))
                print('self.lqi =', self.lqi, type(self.lqi))
                scanfile_flg = True
            else :
                print('>> [SMM2_SCAN.txt] Illegal!!')
                scanfile_flg = False
        else :
            print('>> no [SMM2_SCAN.txt] !')
        return scanfile_flg

    @skfunc
    def skScan(self, duration=4):
        while duration <= 7:
            self.reset_scan()
            self.writeln('SKSCAN 2 FFFFFFFF ' + str(duration))
            while True:
                ln = self.readln()
                if ln.startswith('EVENT 22'):
                    break

                if ':' in ln:
                    key, val = ln.decode().strip().split(':')[:2]
                    if key == 'Channel':
                        self.channel = val
                    elif key == 'Pan ID':
                        self.pan_id = val
                    elif key == 'Addr':
                        self.mac_addr = val
                    elif key == 'LQI':
                        self.lqi = val

            if len(str(self.channel)) == 2 and len(str(self.pan_id)) == 4 and len(str(self.mac_addr)) == 16 and len(str(self.lqi)) == 2 :
            # if self.channel and self.pan_id and self.mac_addr and self.lqi:
                print('self.channel =', self.channel, type(self.channel))
                print('self.pan_id =', self.pan_id, type(self.pan_id))
                print('self.mac_addr =', self.mac_addr, type(self.mac_addr))
                print('self.lqi =', self.lqi, type(self.lqi))
                with open('/flash/SMM2_SCAN.txt' , 'w') as f:
                    f.write('Channel:' + str(self.channel) + '\r\n')
                    f.write('Pan_ID:' + str(self.pan_id) + '\r\n')
                    f.write('MAC_Addr:' + str(self.mac_addr) + '\r\n')
                    f.write('LQI:' + str(self.lqi) + '\r\n')
                    print('>> [SMM2_SCAN.txt] maked!!')
                print('Scan All Clear!')
                scanOK = True
                return True

            duration = duration + 1

        return False

    @skfunc
    def skLL64(self):
        self.writeln('SKLL64 ' + self.mac_addr)
        while True:
            ln = self.readln()
            val = ln.decode().strip()
            if val:
                self.ipv6_addr = val
                return True

    @skfunc
    def skSetChannel(self):
        return self.exec_command('SKSREG S2 ', self.channel)

    @skfunc
    def skSetPanID(self):
        return self.exec_command('SKSREG S3 ', self.pan_id)

    @skfunc
    def skJoin(self):
        self.writeln('SKJOIN ' + self.ipv6_addr)
        while True:
            ln = self.readln()
            if ln.startswith('EVENT 24'):
                return False
            elif ln.startswith('EVENT 25'):
                return True

# read & write & exec
    @iofunc
    def readln(self, timeout = timeout20):
        s = utime.time()
        while (utime.time() - s) < timeout:
        # while (utime.time() - s) < self.timeout:
            if self.uart.any() != 0:
                return self.uart.readline()
        raise Exception('BP35A1.readln() timeout.')

    @iofunc
    def write(self, data):
        self.uart.write(data)

    @iofunc
    def writeln(self, data):
        self.uart.write(data + '\r\n')

    def exec_command(self, cmd, arg=''):
        self.writeln(cmd + arg)
        return self.wait_for_ok()

# コマンド実行 & プロパティ読み書き
    @skfunc
    def skSendTo(self, data):
        self.write('SKSENDTO 1 {0} 0E1A 1 {1:04X} '.format(
            self.ipv6_addr, len(data)))
        self.write(data)
        return True

    @propfunc
    def read_propaty(self, epc, timeout = timeout20):
        """
        プロパティ値読み出し
        """
        self.skSendTo((
            b'\x10\x81'  # EHD
            b'\x00\x01'  # TID
            b'\x05\xFF\x01'  # SEOJ
            b'\x02\x88\x01'  # DEOJ 低圧スマート電力量メータークラス
            b'\x62'  # ESV プロパティ値読み出し(62)
            b'\x01'  # OPC 1個
        ) + bytes([int(epc, 16)]) + (
            b'\x00'  # PDC Read
        ))

        return self.wait_for_data(timeout)

    @propfunc
    def write_property(self, epc, value, timeout = timeout20):
        """
        プロパティ値書き込み
        """
        self.skSendTo((
            b'\x10\x81'  # EHD
            b'\x00\x01'  # TID
            b'\x05\xFF\x01'  # SEOJ
            b'\x02\x88\x01'  # DEOJ 低圧スマート電力量メータークラス
            b'\x61'  # ESV プロパティ値書き込み(61)
            b'\x01'  # OPC 1個
        ) + bytes([int(epc, 16)]) + (
            b'\x01'  # PDC Write
        ) + bytes([value]))

        return self.wait_for_data(timeout)

# その他 (ping)
    @skfunc
    def skPing(self):
        self.writeln('SKPING ' + self.ipv6_addr)
        while True:
            ln = self.readln()
            val = ln.decode().strip()
            if val.startswith('EPONG'):
                return True

# BP35A1初期化 メイン
    def open(self):
        """
        スマートメーターへの接続
        """
        # バッファをクリア
        self.progress(0)
        self.flash()

        # BP53A1の初期化　'SKRESET' と 'SKSREG SFE 0' を実行
        self.progress(10)
        print('### skInit START ###')
        if not self.skInit():
            print('not skIinit')
            return False 
        print('skInit-end')

        # ERXUDPデータ表示形式がバイナリモードならASCIIモードへ変更
        self.progress(20)
        self.set_WOPT()

        # 以前のPANAセッション解除
        self.skTerm()

        # Bルート認証IDの設定
        self.progress(30)
        if not (self.skSetPasswd() and self.skSetID()):
            return False

        while True:
            try:
                # スマートメーターのスキャン
                self.progress(40)
                print('設定ファイルの確認', self.smm2_scan_filechk())
                if self.need_scan() :
                    print('設定ファイルがなかったのでアクティブスキャン実行')
                    if not self.skScan():
                        continue
                else :
                    print('設定ファイルがあったのでアクティブスキャンはスキップ')

                # IPV6アドレスの取得
                self.progress(50)
                if not self.skLL64():
                    continue

                # 無線CH設定、受信PAN-IDの設定
                self.progress(60)
                if not (self.skSetChannel() and self.skSetPanID()):
                    continue

                # スマートメーターに接続
                self.progress(70)
                if not self.skJoin():
                    # スキャン結果をリセット
                    self.reset_scan()
                    continue

                # 係数(D3)の取得
                self.progress(80)
                if self.power_coefficient == None :
                    self.power_coefficient = self.read_propaty('D3')
                    print('self.power_coefficient を受信した')
                    with open('/flash/SMM2_SCAN.txt' , 'a') as fc:
                        print('self.power_coefficient を書き込む')
                        fc.write('COEFFICIENT:' + str(self.power_coefficient) + '\r\n')
                        print('self.power_coefficient を書き込んだ',self.power_coefficient)
                print('## power_coefficient =',  self.power_coefficient, type(self.power_coefficient))
                utime.sleep(1)

                # 積算電力量単位(E1)の取得
                self.progress(90)
                if self.power_unit == None :
                    self.power_unit = self.read_propaty('E1')
                    print('self.power_unit を受信した')
                    with open('/flash/SMM2_SCAN.txt' , 'a') as fc:
                        print('self.power_unit を書き込む')
                        fc.write('UNIT:' + str(self.power_unit) + '\r\n')
                        print('self.power_unit を書き込んだ',str(self.power_unit))
                print('## self.power_unit =',  self.power_unit, type(self.power_unit))
                utime.sleep(1)

                self.progress(100)
                return (self.channel, self.pan_id, self.mac_addr, self.lqi, self.power_coefficient * self.power_unit)

            except Exception as e:
                logger.error(e)

    def InitTotalPower(self, n):
        """
        定期積算電力量初期値(E2)の取得（7日前まで）
        """
        retries = 0

        while retries <= 5 :
            try :
                # 積算履歴収集日１(E5)の設定
                utime.sleep(1)
                self.write_property('E5', n)
                # 積算電力量計測値履歴１(E2)の取得
                utime.sleep(1)
                (days, history_of_power) = self.read_propaty('E2', timeout60)
                return history_of_power
            except Exception as e:
                logger.error(e)
                retries += 1

        raise Exception('BP35A1.InitTotalPower() retry over.')
        
    def total_power(self): ### どこでも参照されていない？
        """
        定時積算電力量計測値(EA)の取得
        """
        utime.sleep(1)
        return self.read_propaty('EA')

    def instantaneous_power(self):
        """
        瞬時電力計測値(E7)の取得
        """
        utime.sleep(1)
        return self.read_propaty('E7')

    def instantaneous_amperage(self):
        """
        瞬時電流計測値(E8)の取得
        """
        utime.sleep(1)
        return self.read_propaty('E8')

    def monthly_power(self):
        """
        前回検針日を起点とした積算電力量計測値履歴１(E2)の取得
        """
        # 積算履歴収集日１(E5)の設定
        utime.sleep(1)
        self.write_property('E5', days_after_collect(self.collect_date))

        # 積算電力量計測値履歴１(E2)の取得
        utime.sleep(1)
        (days, collected_power) = self.read_propaty('E2', timeout60)
        (days, collected_power) = (days, int(collected_power[0:0 + 8],16) * self.power_coefficient * self.power_unit )

        # 定時積算電力量計測値(EA)の取得
        utime.sleep(1)
        (created, power) = self.read_propaty('EA')

        # 前回検針日と定時積算電力量計測値(EA)との差分
        return (last_colect_day(self.collect_date), power - collected_power, created, power)

    def close(self):
        """
        スマートメーターとの接続解除
        """
        self.skTerm()

    def wait_for_ok(self):
#         ln = None
        while True :
            if self.uart.any() != 0 :
                ln = self.readln()
                if ln.decode().startswith('OK') :
                    return True
                elif ln.decode().startswith('FAIL') :
                    return False

# データ取得_メイン
    def wait_for_data(self, timeout = timeout20):
        start = ut = utime.time()
        while ut - start < timeout:
        # while ut - start < self.timeout:
        # while utime.time() - start < self.timeout:
            if self.uart.any() != 0 :
                ln = self.readln(timeout)
                if not ln.decode().startswith('ERXUDP'):
                    continue
                
                values = ln.decode().strip().split(' ')
                if not len(values) == 9:
                    print(7)
                    continue
    
                data = values[8]
                seoj = data[8:8 + 6]
                esv = data[20:20 + 2]
                epc = data[24:24 + 2]
    
                # 低圧スマート電力量メータ(028801)
                if seoj != '028801':
                    continue
    
                # 積算電力量係数
                if esv == '72' and epc == 'D3':
                    power_coefficient = int(data[-8:], 16)
                    return power_coefficient
    
                # 積算電力量単位
                if esv == '72' and epc == 'E1':
                    power_unit = {
                        '00': 1.0,
                        '01': 0.1,
                        '02': 0.01,
                        '03': 0.001,
                        '04': 0.0001,
                        '0A': 10.0,
                        '0B': 100.0,
                        '0C': 1000.0,
                        '0D': 10000.0,
                    }[data[-2:]]
                    return power_unit
    
                # 積算電力量計測値履歴１
                if esv == '72' and epc == 'E2':
                    days = int(data[30:30 + 2], 16)
                    power = data[32:32 + 8 * 48]
                    return days, power
    
                # 積算履歴収集日１
                if esv == '71' and epc == 'E5':
                    result = int(data[-2:], 16)
                    return result
    
                # 瞬時電力値
                if esv == '72' and epc == 'E7':
                    power = int(data[-8:], 16)
                    return strftime(localtime()), power
    
                # 瞬時電流計測値
                if esv == '72' and epc == 'E8':
                    r = int(data[-8:-8 + 4], 16)
                    if r == 0x7ffe:
                        r = 0
                    t = int(data[-4:], 16)
                    if t == 0x7ffe:
                        t = 0
                    return strftime(localtime()), (r + t) / 10.0
    
                # 定時積算電力量
                if esv == '72' and epc == 'EA':
                    (year, month, mday, hour, minute,
                     second) = (int(data[-22:-22 + 4],
                                    16), int(data[-18:-18 + 2],
                                             16), int(data[-16:-16 + 2], 16),
                                int(data[-14:-14 + 2],
                                    16), int(data[-12:-12 + 2],
                                             16), int(data[-10:-10 + 2], 16))
                    created = strftime((year, month, mday, hour, minute, second))
                    power = int(data[-8:],
                                16) * self.power_coefficient * self.power_unit
                    return created, power
            
            ut = utime.time()

        raise Exception('BP35A1.wait_for_data() timeout.')

    def close(self):
        self.skTerm()


if __name__ == '__main__':
    id = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    password = 'xxxxxxxxxxxx'
    contract_amperage = "40"
    collect_date = [1] * 13

    bp35a1 = BP35A1(id, password, contract_amperage, collect_date)

    bp35a1.open()

    (datetime, data) = bp35a1.instantaneous_power()
    print('Instantaneous power {} {}W'.format(datetime, data))

    (datetime, data) = bp35a1.total_power()
    print('Total power {} {}kWh'.format(datetime, data))

    bp35a1.close()