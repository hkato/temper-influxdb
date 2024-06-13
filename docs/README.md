# USB TEMPer温度計のデータをPython+InfluxDB+Grafanaで可視化する

## TEMPerって？

10年ぐらい前から売っているUSBの温度計。私のAmazon購買履歴だと2014年に購入している。

https://www.amazon.co.jp/dp/B004FI1570/

当時、こいつを会社にBYODし、最初は[MRTG](https://oss.oetiker.ch/mrtg/)にて、その後[Zabbix](https://www.zabbix.com/)でグラフ化して室温の推移を同僚に見せていた。そして色々あって必要なくなったので、ここ数年は自宅に持ち帰り引き出しの中で寝かせていた。

TEMPer自体のQiitaの記事で検索するとここらへん。古いデバイスなのでZennにはない模様。

https://qiita.com/nekyo/items/bf5d22f3741e23d3679d

https://qiita.com/zembutsu/items/9b718416f6b30a19d83c

https://qiita.com/zembutsu/items/0f8e570c4016ddb4aefa

## 再活用

というか自宅にSwitchBotの温湿度計が欲しいなぁ思って調べていたら次の記事を見つけた、

https://zenn.dev/tanny/articles/a5c0fa5c2230a7

上記に書いた様に過去はMRGTやZabbixでデバイスは古いTEMPerという感じだけど可視化したいものは同様の温度情報、今回はデバイスはそのままTEMPerで可視化プラットフォームを新たにGrafanaでやってみようという感じ。

## できたもの

https://github.com/hkato/temper-grafana

やっていることはSwitchBotの様にクラウドのAPI経由で情報を取得するのではなく、上記TEMPerの記事でも触れている既存のUSBから取得するプログラムを`subprocess`で呼び出しInfluxDBに格納。あとはSwitchBotの記事の様にGUIでゴニョゴニョ(省略)。

## 感想とか諸々

- ラズパイ3で実行しているが電源不足なのか(実は弱めの電源で利用)たまにUSBデバイスが切断される。USB延長コードを利用すると顕著。
- 実はTEMPerをメルカリに出す動作確認も兼ねてやってみたけど、送料負けする価格じゃないと売れなさそうなので引っ込めた。もう需要がない。
- SwitchBotは湿度も測れるし羨ましい。こいつは捨ててSwitchBot hub 2を買いたい。
- まあ、複数ポイントで温度を取得する場合の一つのセンサーとしてそのまま取っておくのも良いかも。
