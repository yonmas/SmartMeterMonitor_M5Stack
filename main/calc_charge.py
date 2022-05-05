def tepco(contract, power):
    """
    東京電力での電気料金計算（従量電灯B）

    基本料金
      契約アンペア数 : 基本料金
              　 10A :   286.00円
              　 15A :   429.00円
            　   20A :   572.00円
          　     30A :   858.00円
          　     40A : 1,144.00円
          　     50A : 1,430.00円
          　     60A : 1,716.00円

    従量料金
      〜120lWh : 19.88円/kWh
      〜300kWh : 26.48円/kwh
      〜       : 30.57円/kwh

    電気料金 = 基本料金 + 従量料金 + （燃料費調整額 + 再エネ発電賦課金 - 口座振替割引(55円)）
      ※ (基本料金 + 従量料金) 部分のみを計算

    Parameters
    ----------
    contract : str
        契約アンペア数
    power : float
        前回検針後の使用電力量（kWh）
    
    Returns
    -------
    fee: int
        電気料金

    """
    fee = {'10': 286.00, '15': 429.00, '20': 572.00, '30': 858.00, '40': 1144.00, '50': 1430.00, '60': 1716.00}[contract]

    if power <= 120:
        fee += 19.88 * power
    elif power <= 300:
        fee += 19.88 * 120
        fee += 26.48 * (power - 120)
    else:
        fee += 19.88 * 120
        fee += 26.48 * 180
        fee += 30.57 * (power - 120 - 180)
    return int(fee + (power * 3.36))


# 以下オリジナル

# TOKYO GASの料金計算
# https://home.tokyo-gas.co.jp/power/ryokin/tanka/index.html


def tokyo_gas_1s(contract, power):
    """
    TOKYO GAS「ずっとも電気1S」での電気料金計算

    Parameters
    ----------
    contract : str
        契約アンペア数
    power : float
        前回検針後の使用電力量（kWh）
    
    Returns
    -------
    fee: int
        電気料金
    """
    fee = {
        '10': 286.00,
        '15': 429.00,
        '20': 572.00,
        '40': 1144.00,
        '50': 1430.00,
        '60': 1716.0
    }[contract]

    if power <= 120:
        fee += 19.85 * power
    elif power <= 300:
        fee += 19.85 * 120
        fee += 25.35 * (power - 120)
    else:
        fee += 19.85 * 120
        fee += 25.35 * 300
        fee += 27.48 * (power - 120 - 300)
    return int(fee)


def tokyo_gas_1(contract, power):
    """
    TOKYO GAS「ずっとも電気1」での電気料金計算

    Parameters
    ----------
    contract : str
        契約アンペア数
    power : float
        前回検針後の使用電力量（kWh）
    
    Returns
    -------
    fee: int
        電気料金
    """
    fee = {'30': 858.00, '40': 1144.00, '50': 1430.00, '60': 1716.00}[contract]

    if power <= 140:
        fee += 23.67 * power
    elif power <= 350:
        fee += 23.67 * 140
        fee += 23.88 * (power - 140)
    else:
        fee += 23.67 * 140
        fee += 23.88 * 350
        fee += 26.41 * (power - 140 - 350)
    return int(fee)


def tokyo_gas_2(contract, power):
    """
    TOKYO GAS「ずっとも電気2」での電気料金計算

    Parameters
    ----------
    contract : str
        契約アンペア数
    power : float
        前回検針後の使用電力量（kWh）
    
    Returns
    -------
    fee: int
        電気料金
    """
    fee = 286.00
    if power <= 360:
        fee += 19.85 * power
    else:
        fee += 23.63 * 360
        fee += 26.47 * (power - 360)
    return int(fee)


if __name__ == '__main__':
    print(tokyo_gas_1('50', 339))