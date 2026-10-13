# AgentOS-C — AIの外に知識を残す

> **AIを乗り換えても、自分の知識は残る。**

AgentOS-Cは、利用者の知識・判断・手順・作業状態をAIサービスの外部に保存し、必要なときに別のチャットやAI環境へ渡せるようにするための、オープンな運用基盤です。新しいAIモデルではなく、既存の文書・保存先・AI機能を組み合わせる仕組みです。

## まず試す

- [5分で概要と導入手順を確認](Getting-Started.md)
- [何が実際に確認されたか](Verified-Results.md)
- [開発中の構想と将来用途](Future-Vision.md)

まずは、KBを生成し、受け取り、自分の保存先へバックアップできるところまでを小さく確認します。更新やAI間での引き継ぎについては、順次検証を進めています。

## 基本の使い方

1. 利用環境に合う設計書を選んでAIへ渡す。
2. `実行` と送信する。
3. 保存先・初回案を確認し、`進めて` と送信する。
4. AIが生成したZIP等を自分の非公開保存先へ保管し、必要な内容を検査する。

[公式QUICKSTART](https://github.com/Yosio-DMZ-C/AgentOS-C/blob/main/QUICKSTART.md) / [一般配布版の設計書](https://github.com/Yosio-DMZ-C/AgentOS-C/blob/main/docs/AgentOS-C_設計・構築運用指示書_一般配布版.md) / [AI無課金ユーザー版](https://github.com/Yosio-DMZ-C/AgentOS-C/blob/main/docs/AgentOS-C_設計・構築運用指示書_AI無課金ユーザー版.md)

## 現在できることと、これから広げること

| 区分 | 内容 |
|---|---|
| **現在確認できていること** | 一部環境で初期KBの生成、ZIPでの受渡し、外部保存、別チャットからの読戻し |
| **次に検証すること** | IDと参照の完全性、安全な更新、競合からの復旧、他AIへの移植 |
| **今後の展開** | 組織標準KB、対話型インストーラKB、共有知の拡充、Core Life Skills |

利用するAIや環境によって使える機能は異なります。実際に確認できた内容は、[実動作の検証結果](Verified-Results.md)で順次公開しています。

## さらに詳しく

より詳しい仕組みや設計については、[AgentOS-Cの設計書](https://github.com/Yosio-DMZ-C/AgentOS-C/tree/main/docs)をご覧ください。
