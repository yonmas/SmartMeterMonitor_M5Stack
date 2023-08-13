# M5StickC/M5Stack でスマートメーター・モニタリング with Wi-SUN HAT

![Collage_Fotor](https://user-images.githubusercontent.com/104808539/166885813-86737337-00c2-421f-a8a8-5c4fb0433924.jpg)

## 概要

M5StickC Plus + Wi-SUNモジュール BP35A1 で、各家庭の低圧スマート電力量メータ（スマートメータ）から電力使用量のデータを取得。親機、子機にいろいろ表示します。たぶん節電に役立ちます。  

- 瞬時電力
- 瞬時電流
- 直近検針日からの積算電力量
- 直近検針日からの電気代（基本料金＋従量料金）
- 30分ごとの使用電力量グラフ（当日、前日との比較）
- 0時からの使用電力量と直近7日間およびその平均との比較棒グラフ
- 1時間毎の使用電力量内訳（前日との比較）
- 1時間毎の使用電力量内訳（直近7日間平均との比較）

システム全体は、 @rin-ofumi さんのこちらの記事をベースにしています。Wi-SUN HAT の作者さんです。  
<https://kitto-yakudatsu.com/archives/7206>

子機のシステムは、 @rin-ofumi さんの以下のコードをベースにしています。  
<https://github.com/rin-ofumi/m5stickc_wisun_hat>

親機のシステムと全体の表示形式は、 @miyaichi さんの以下のコードをベースにしています。  
<https://github.com/miyaichi/SmartMeter>

（2023.8.13 ファーム v1.12.2 にて動作を確認。）

## 部品リスト

### 親機

- M5StickC Plus (¥3,564) --> [スイッチサイエンス](https://www.switch-science.com/catalog/6470/)
- BP35A1 モジュール (¥8,620) --> [チップワンストップ](https://www.chip1stop.com/view/searchResult/SearchResultTop?classCd=&did=&cid=netcompo&keyword=BP35A1&utm_source=netcompo&utm_medium=buyNow)
- Wi-SUN HAT (¥1,650) --> [スイッチサイエンス](https://www.switch-science.com/catalog/7612/)

### 子機 :（オプション）

- M5Stack Basic (¥5,874) --> [スイッチサイエンス](https://www.switch-science.com/catalog/7362/)  
（ファーム v1.10.1 まで対応。v1.10.2 以降では ESPNOW の仕様変更の為エラーになります。）

## 準備

電力会社にBルートサービスの利用開始を申し込み、認証IDとパスワードを取得する。  
--> [東京電力申込みサイト](https://www.tepco.co.jp/pg/consignment/liberalization/smartmeter-broute.html)

Ambient でアカウントを作成し、チャネルを作成。チャネルIDとライトキーを取得する。  
--> [Ambient](https://ambidata.io/)

## ファイル構成

```text
■■ 親機（main)：M5StickC Plus + Wi-SUN HAT(with BP35A1 module) ■■

/apps/
  +- SMM2.py

/
  +- BP35A1.py （BP35A1クラス)
  +- smm2_main_set.json (親機設定ファイル ： ルートB情報、Ambient情報を記載)
  +- calc_charge.json (電気料金計算モジュール)
  +- calender_2023.json (月別検針日 ： 前年12月〜当年12月 の 13ヶ月)
  +- ambient.py (別途準備)
  +- logging.py (別途準備)
```

```text
■■ 子機(sub)：M5Stack Basic ■■ 

/apps/
  +- SMM2_sub.py (子機メインプログラム : 親機のMACアドレスを記載)

/
  +- smm2_sub_set.json (子機設定ファイル)
```

## download

[ambient.py](https://github.com/AmbientDataInc/ambient-python-lib/blob/master/ambient.py)

[logging.py](https://github.com/micropython/micropython-lib/blob/master/python-stdlib/logging/logging.py)

## ボタンの説明

### 親機

* Aボタン : 画面の向きをフリップ

### 子機

* Aボタン : 画面表示のオン／オフ
* Bボタン : ページめくり
* Bボタン長押し : 履歴データの取得（数分かかります）
* Cボタン : 警告BEEPのオン／オフ

## 表示内容の説明

![IMG_3162](https://user-images.githubusercontent.com/104808539/167132181-2a12b02c-01de-4133-ab9a-4a698b209ea5.JPG)

メインページです。大きな数字531Wは瞬時電力量で、約10秒ごとの更新としています。中段は電気代を計算する期間。4月21日が検針日で、右側が「今日」の日付になっています。左下152kWhは、検針日以降「今日」までの電気使用量、右下4902円は電気代です。実際に請求される電気料金には燃料調整費や再エネ発電賦課金などが足し引きされます。最下端左は、直近の電力量取得時刻で30分更新。右下楕円は、アラート（使用量が閾値を超えると文字が赤くなり、アラートが鳴る）のオンオフボタン、右下はデータ取得インジケーターで、データ取得時は赤く明滅します。（@rin-ofumiさんの子機に@miyaichiさん作の親機の表示を移植）

![IMG_3166](https://user-images.githubusercontent.com/104808539/167132279-0f0c9688-e769-4601-a078-c44ec3f7a614.JPG)

最上段、「今日」の現時刻（左下の表示、20時）までの電気使用量(7.3kWh)、その下に1日前〜7日前までと、その平均（最下段）の現時刻までの使用量です。「今日」はあまり電気を使っていないことが読み取れます。グラフ全長は、それぞれの日の終日の電気使用量です。２４時が近づくにつれ、「前日以下に抑えたい！」とか、「せめて一週間の平均以下に…」などと節電モチベーションがあがります！？（オリジナル）

![IMG_3163](https://user-images.githubusercontent.com/104808539/167132326-ed05a762-ab36-4877-8aeb-e7e3b5950441.JPG)

30分ごとの電気使用量グラフです。グレーは前日分。「今日」の使用量によって、バーが緑、黄色、オレンジと変わります。赤は前日同時刻よりオーバーした分。赤が少ないので、ほぼ昨日以下であることがわかります。（@rin0ofumiさんの子機表示をカスタマイズ）

![IMG_3167](https://user-images.githubusercontent.com/104808539/167132399-956cfb8a-4300-4fce-8c4b-9f72c3684922.JPG)

1時間ごとの、「今日」と昨日の電気使用量の比較です。Diffはその差で、前日を超えた場合（プラス）は、赤文字表示。下段は現時刻までの使用量（「今日」と前日）と、その比。（オリジナル）

![IMG_3168](https://user-images.githubusercontent.com/104808539/167132453-d550f487-18a9-4da2-8b92-d355945125b7.JPG)

同じく１時間ごと、「今日」と直近７日間平均の電気使用量の比較です。(オリジナル）

![280048115_5283696261695586_122106429351052967_n](https://user-images.githubusercontent.com/104808539/167132506-0fd5e219-3638-4928-b191-7dceaad85b6d.jpg)

親機の表示です。瞬時の電流値も表示しています。1A単位と大雑把だし、ほぼ、瞬時電力値の1/100とみなせるので、レイアウトの都合上子機では割愛しました。（@miyaichiさんの表示をカスタマイズ）

## おわりに

初めてGitHubに登録して、あれこれ弄っている段階ですので、至らない箇所があると思います。  
お気づきの点など、ビシバシご指摘いただけますとありがたいです。  

どうぞよしなに。
