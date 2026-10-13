# AgentOS-C — AIの外に知識を残す

> **AIを乗り換えても、自分の知識は残る。**

AgentOS-Cは、利用者の知識・判断・手順・作業状態をAIサービスの外部に保存し、必要なときに別のチャットやAI環境へ渡せるようにするための、オープンな運用基盤です。新しいAIモデルではなく、既存の文書・保存先・AI機能を組み合わせる仕組みです。

## まず試す

- [5分で概要と導入手順を確認](Getting-Started.md)
- [何が実際に確認されたか](Verified-Results.md)
- [開発中の構想と将来用途](Future-Vision.md)

**初回の最小目標は「KBを生成し、検査可能な形式で受け取り、自分の保存先へバックアップする」こと**です。すべてのAIで自動更新やAI間移植ができるとは約束しません。

## 基本の使い方

1. 利用環境に合う設計書を選んでAIへ渡す。
2. `実行` と送信する。
3. 保存先・初回案を確認し、`進めて` と送信する。
4. AIが生成したZIP等を自分の非公開保存先へ保管し、必要な内容を検査する。

[公式QUICKSTART](https://github.com/Yosio-DMZ-C/AgentOS-C/blob/main/QUICKSTART.md) / [一般配布版の設計書](https://github.com/Yosio-DMZ-C/AgentOS-C/blob/main/docs/AgentOS-C_設計・構築運用指示書_一般配布版.md) / [AI無課金ユーザー版](https://github.com/Yosio-DMZ-C/AgentOS-C/blob/main/docs/AgentOS-C_設計・構築運用指示書_AI無課金ユーザー版.md)

## 実装と構想を混同しない

| 区分 | 内容 |
|---|---|
| **限定的に実証** | 一部環境で初期KB生成、ZIP受渡し、外部保存、別チャット読戻し |
| **検証中** | IDと参照の完全性、安全な更新、競合復旧、他AI間移植 |
| **構想** | 組織標準KB、対話型インストーラKB、共有知の拡充、Core Life Skills |

環境・契約・ツールによって可否は異なります。**AIの自己申告と外部成果物の独立検査を分けます。** [試験結果と限界](Verified-Results.md)を参照してください。

## このページについて

この一連のページはPR用の説明案です。詳しい技術仕様の正本は[リポジトリの設計書](https://github.com/Yosio-DMZ-C/AgentOS-C/tree/main/docs)にあります。内容を確認せず、個人KBや内部文書を公開リポジトリへ移さないでください。
