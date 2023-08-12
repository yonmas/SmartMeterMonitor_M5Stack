def tepco(contract, power):
    """
    東京電力での電気料金計算（従量電灯B）
    2023.6.1 料金改定版

    基本料金
      10A :   295.24円   base10
      15A :   442.86円   base15
      20A :   590.48円   base20
      30A :   885.72円   base30
      40A : 1,180.96円   base40
      50A : 1,476.20円   base50
      60A : 1,771.44円   base60

    従量料金（2023.4.1の燃料費調整単価 -8.78円 込み）
      〜120lWh : 30.00円/kWh    rate1
      〜300kWh : 36.60円/kwh    rate2
      〜       : 40.69円/kwh    rate3

    燃料費調整単価（毎月更新）
      -11.21円/kWh  nenchou

    再エネ発電賦課金（〜2024.4）
      1.40円/kWh    saiene

    電気料金 = 基本料金 + 従量料金 + 燃料費調整額 + 再エネ発電賦課金（税込）

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

    base10 =  295.24
    base15 =  442.86
    base20 =  590.48
    base30 =  885.72
    base40 = 1180.96
    base50 = 1476.20
    base60 = 1771.44

    rate1  = 30.00
    rate2  = 36.60
    rate3  = 40.69

    nencho = -11.21 # 2023.8
    saisei = 1.40   # 〜 2024.4

    fee = {'10': base10, '15': base15, '20': base20, '30': base30, '40': base40, '50': base50, '60': base60}[contract]

    power = int(power)

    if power <= 120:
        fee += rate1 * power
    elif power <= 300:
        fee += rate1 * 120
        fee += rate2 * (power - 120)
    else:
        fee += rate1 * 120
        fee += rate2 * 180
        fee += rate3 * (power - 120 - 180)
    
    fee += nencho * power + int(saisei * power) # 燃料費調整額・再エネ発電賦課金 加算

    return int(fee)