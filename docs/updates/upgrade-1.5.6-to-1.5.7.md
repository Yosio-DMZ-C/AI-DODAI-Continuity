# AD&C 差分手順｜1.5.6 → 1.5.7

> **FROM=`1.5.6`、TO=`1.5.7`**。必ず[UPDATE.md](UPDATE.md)のFROM→TO、全区間連続性、本人の実行承認、変更前保全・競合・同一ID更新・raw読戻しを適用する。これは配布候補の差分であり、公開mainに反映されるまで最新版とは扱わない。版不明のKBは[ADOPT_LEGACY.md](ADOPT_LEGACY.md)へ分岐する。

## 目的と適用範囲

新規AIがAD&Cの個人KBを構築した後、`50_skills` が空で共有Playbookを見つけず一般検索を先行させた事例への対策。共有カタログ・自然文ルーティングへの**参照ポインタ**と、本人が許可した場合の継続指示を既存KBへ安全に接続する。共有Skillの本文を無断複製せず、正式配布 `items=0` と利用者採用の試用Skillを区別する。

| 対象 | 差分 | 維持対象 |
|---|---|---|
| `START_HERE.md` | 共有KBの[README](https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge/blob/main/README.md)の自然文ルーティングと[catalog.json](https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge/blob/main/catalog.json)への短い固定入口を追記。既存入口が同等なら重複追加しない | NodeID、fileId、既存の更新入口、個人の優先手順、既存本文 |
| `50_skills/INDEX.md` または当該KBの既存Skill索引 | 共有Skillはリンクとして登録。現行山歩き[SKILL.md](https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge/blob/main/skills/hiking-route-search/SKILL.md)の版を実取得し、旧版表示があれば更新。共有Playbookを正式Active配布へ勝手に昇格させない | 個別Skill、既存採用状態、同一ID、他の索引項目 |
| AIのメモリ／継続指示 | 利用可能で本人が保存を認めた場合のみ、共有KBの現行READMEを一般検索前に確認し、該当Skill全文・版と個人優先手順を取得する短文を保存。保存不能ならコピー用指示を提示し未実施とする | AI製品の権限、利用者のメモリ設定、非公開データ |
| registry／Context／BUILD_PLAN | 実際に編集した既存レコードの実raw SHA・revision・依存参照・再開状態のみ同期。新規の並行正本や無関係なタスクを作らない | 他レコード、履歴、機密、既存の承認範囲 |
| 導入版 | 上記の対象KB内で**必須工程**を保存・読戻し検収できた場合だけ `ADNC_INSTALLER_VERSION: 1.5.7` に更新 | 他の版軸と旧履歴 |

## 実行と検収

1. 対象KBの現行`START_HERE`→registry/INDEX→そのKBの統合更新Playbook全文を実取得し、同一fileId・現行raw SHA・版・参照元・変更前のバイト一致保全と隔離復元の可否を確認する。公開READMEのみで私的KBの書込契約を代替しない。
2. 共有READMEのルーティング、`catalog.json`、対象Skillの本文を実取得し、版・Active/Draft・適用条件を照合。取得不能なら関連登録は`NOT_RUN`。
3. 本人が承認した変更表の範囲で、既存`START_HERE`と索引に重複しないリンクを局所追加する。書込直前に競合を再取得し、同一fileIdで変更。書込後にDrive rawを再取得して実SHAを計算し、registry・必要なINDEX/ContextのSHA/逆参照まで更新・再読戻し。復旧元が検証できない、権限拒否、安全性チェック拒否なら迂回せず当該工程を停止。
4. AIメモリ・カスタム指示は**本人の別途許可と機能実在**を確認し、保存と次チャットでの実読取を別々に検収。メモリを直接書けないAIは未保存を`PASS`としない。メモリ機能がなくてもKBリンクを保存できる環境では、その範囲の実装を続ける。
5. 依頼例「来週、大台ヶ原で景色の良い登山ルートを」で、一般Web検索前に共有ルーティング→山歩きSkill全文・版→個人優先手順の順に到達できるかを**独立AI／新チャットで**試験。山歩きの第1検索はYAMAP限定。Python検査・安全条件の適用は別々に検収し、実試験不能なら`NOT_RUN`。
6. 導入版更新、変更した正本・registry/INDEX/Contextのraw SHA一致、入口からの逆引き、復旧元を確認。未実施が必須なら当該KBの更新完了を宣言しない。完了条件とAIメモリ実装・独立効果を混同しない。

**更新時の短い継続指示（本人が保存を認める場合）**：
> AD&Cを利用中。相談では一般検索より先に共有KB https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge のREADMEの自然文ルーティングを確認し、該当するSKILL.md全文・版と個人KBの優先手順を取得して適用する。リンクや手順で詰まったら最新版を再取得し、原因と未実施工程を報告する。未取得を実施済みと称さない。

**禁止**：再インストール、既存KBの一括上書き、本人未承認のメモリ操作、共有側への個人情報転送、公開mainの無審査マージ、無承認の公開・権限変更・削除・課金・不可逆操作。個人KBの書込は既存の正本・承認・安全規則が優先する。
