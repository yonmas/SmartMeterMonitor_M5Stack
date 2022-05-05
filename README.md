# SMM2
M5StickC / M5Stack でスマートメーター・ハッキング with Wi-SUN HAT

Wi-SUN HATを含む、全体のシステムと子機表示は、@rin-ofumiさんの以下のコードをベースにしています。</br>
https://github.com/rin-ofumi/m5stickc_wisun_hat

親機のシステムと表示形式は、@miyaichiさんの以下のコードをベースにしています。</br>
https://github.com/miyaichi/SmartMeter

===　構成 ===

**■■ 親機（main)：M5StickC Plus + Wi-SUN HAT(with BP35A1 module) ■■**

/apps/

- SMM2.py　（メインプログラム : 子機のMACアドレスを記載）

/

- BP35A1.py （BP35A1クラス)
- SmartMeter.json (親機設定ファイル ： ルートB情報、Ambient情報を記載)
- calc_charge.json (電気料金計算モジュール)
- calender_2022.json (月別検針日 ： 前年12月〜当年12月 の 13ヶ月)
- ambient.py (別途準備)
- logging.py (別途準備)

**■■ 子機(sub)：M5Stack Basic ■■**

/apps/

- SMM2_sub.py (子機メインプログラム : 親機のMACアドレスを記載)

/

- smm2_set.json (子機設定ファイル)

===　構成 ===

初めてGitHubに登録して、あれこれ弄っている段階ですので、至らない箇所があると思います。</br>
お気づきの点など、ビシバシご指摘いただけますとありがたいです。</br>

よしなに。
