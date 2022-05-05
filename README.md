## M5StickC/M5Stack でスマートメーター・ハッキング with Wi-SUN HAT

![Collage_Fotor](https://user-images.githubusercontent.com/104808539/166885813-86737337-00c2-421f-a8a8-5c4fb0433924.jpg)

## 概要
M5StickC Plus + Wi-SUNモジュール BP35A1 で、各家庭の小電力スマートメーターから電力使用量のデータを取得。親機、子機にいろいろ表示します。たぶん節電に役立ちます。<br>

- 瞬時電力
- 瞬時電流
- 直近検針日からの積算電力量
- 直近検針日からの電気代（基本料金＋従量料金）
- 30分ごとの使用電力量グラフ（当日、前日との比較）
- 0時からの使用電力量と直近7日間およびその平均との比較棒グラフ
- 1時間毎の使用電力量内訳（前日との比較）
- 1時間毎の使用電力量内訳（直近7日間平均との比較）

システム全体は、 @rin-ofimi さんのこちらの記事をベースにしています。Wi-SUN HAT の作者さんです。<br>
https://kitto-yakudatsu.com/archives/7206

子機のシステムは、 @rin-ofumi さんの以下のコードをベースにしています。</br>
https://github.com/rin-ofumi/m5stickc_wisun_hat

親機のシステムと全体の表示形式は、 @miyaichi さんの以下のコードをベースにしています。</br>
https://github.com/miyaichi/SmartMeter

## 部品リスト
#### 親機 ：
- M5StickC Plus (¥3,564) --> [スイッチサイエンス](https://www.switch-science.com/catalog/6470/)
- BP35A1 モジュール (¥8,620) --> [チップワンストップ](https://www.chip1stop.com/view/searchResult/SearchResultTop?classCd=&did=&cid=netcompo&keyword=BP35A1&utm_source=netcompo&utm_medium=buyNow)
- Wi-SUN HAT (¥1,650) --> [スイッチサイエンス](https://www.switch-science.com/catalog/7612/)

#### 子機 :（オプション）
- M5Stack Basic (¥5,874) --> [スイッチサイエンス](https://www.switch-science.com/catalog/7362/)

## 準備
電力会社にBルートサービスの利用開始を申し込み、認証IDとパスワードを取得する。</br>
--> [東京電力申込みサイト](https://www.tepco.co.jp/pg/consignment/liberalization/smartmeter-broute.html)

## ファイル構成
```
■■ 親機（main)：M5StickC Plus + Wi-SUN HAT(with BP35A1 module) ■■

/apps/
- SMM2.py　（メインプログラム : 子機のMACアドレスを記載）

/
- BP35A1.py （BP35A1クラス)
- smm2_main_set.json (親機設定ファイル ： ルートB情報、Ambient情報を記載)
- calc_charge.json (電気料金計算モジュール)
- calender_2022.json (月別検針日 ： 前年12月〜当年12月 の 13ヶ月)
- ambient.py (別途準備)
- logging.py (別途準備)
```
```
■■ 子機(sub)：M5Stack Basic ■■

/apps/
- SMM2_sub.py (子機メインプログラム : 親機のMACアドレスを記載)

/
- smm2_set.json (子機設定ファイル)
```

## download
[ambient.py](https://github.com/AmbientDataInc/ambient-python-lib/blob/master/ambient.py)

[logging.py](https://github.com/micropython/micropython-lib/blob/master/python-stdlib/logging/logging.py)

## おわりに
初めてGitHubに登録して、あれこれ弄っている段階ですので、至らない箇所があると思います。</br>
お気づきの点など、ビシバシご指摘いただけますとありがたいです。</br>

よしなに。
