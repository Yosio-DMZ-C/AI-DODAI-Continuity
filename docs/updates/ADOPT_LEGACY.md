# AD&C｜旧KB向け互換導入（インストーラー版不明）

> **最初の品質ゲート：この手順は再インストールでも正式版への一括更新でもない。** 既存KBに`ADNC_INSTALLER_VERSION`が存在せず、正確な導入版を導入履歴から確定できない場合だけ使う。**最新インストーラーを導入済みと偽らない。** 既存の導入版が数値で確定するなら、[UPDATE.md](UPDATE.md)の通常差分経路を使う。

## 実行前の判定と提示

1. **利用者が指定した現在のKBだけ**を対象とする。現行`START_HERE.md`、`BUILD_PLAN.md`、`00_system/registry.json`、既存`00_system`を必要範囲で**実取得**し、NodeID、Drive fileId、元本文、台帳の扱い、共有範囲、変更前のrevision/hashを照合する。**既存の秘書設定場所を全アカウントで探索しない**。
2. `ADNC_INSTALLER_VERSION`がない場合、そのことは旧KBとして許容する。旧称・設計v1.4・配布文書の最新版・`LATEST.json`の値を「そのKBが導入した版」とは扱わない。
3. 既に`ADNC_UPDATE_STATUS_PATH`があり、参照先の`ADNC_UPDATE_PROTOCOL_VERSION`が現行値なら重複作成しない。競合、他用途ファイルとの衝突、書込権限不明なら変更せず停止。
4. 次の最小変更を表で提示して、利用者の**今回の互換導入への明示承認**を得る。承認までは読取だけ。

| 対象 | 最小差分 | 変更しないもの |
|---|---|---|
| `START_HERE.md` | 既存本文を残して、後述の`ADNC_UPDATE_STATUS_PATH`を1行だけ追加 | 現行設計、NodeID、既存fileId、各入口 |
| `00_system/ADNC_UPDATE_STATUS.md` | **小さな更新管理メモ**1件だけ新規作成 | `ADNC_INSTALLER_VERSION`は新設しない |
| `registry.json` | 現行台帳が管理するレコードだけ必要なID・revision/hash/sizeを整合 | 既存の他レコードと履歴 |
| 秘書設定 | **今回は変更対象外**。実行主体が判明した場合のみ別工程で指示を局所更新 | 既存の朝の実行、予定確認、日記、口調、通知先、時間 |

## 承認後の局所変更

1. 変更前の`START_HERE`と関連registryレコードを既存の`90_history`または実効の版履歴へ保全。NodeID・fileId・共有状態は維持。
2. **現行の`00_system`内**に`ADNC_UPDATE_STATUS.md`を次の内容で1件だけ作る。既存名があれば勝手に上書きしない。

```md
# AD&C 更新管理メモ（旧KB互換）
ADNC_ORIGIN: legacy_unversioned
ADNC_UPDATE_PROTOCOL_VERSION: 1.5.2
ADNC_UPDATE_RUNBOOK: https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/blob/main/docs/updates/UPDATE.md
ADNC_UPDATE_MANIFEST: https://raw.githubusercontent.com/Yosio-DMZ-C/AI-DODAI-Continuity/main/docs/updates/LATEST.json
ADNC_DAILY_CHECK: https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/blob/main/docs/updates/DAILY_CHECK.md
ADNC_LAST_CHECK_DAY: none
ADNC_LAST_NOTIFIED_MINOR: none
```

3. `START_HERE.md`のタイトル直後など安全な場所へ次の**1行だけ**追記する（既に同一行があれば追記不要）。**インストーラー版は追加しない**。

```md
ADNC_UPDATE_STATUS_PATH: 00_system/ADNC_UPDATE_STATUS.md
```

4. `START_HERE`を同一Drive fileIdで差分更新し、現在のregistryに登録済みなら該当するレコードを更新（新規のダミー登録はしない）。新しい更新管理メモは登録ルールに従って登録する場合のみ新規レコードを付け、既存IDを破壊しない。
5. 書き換えたファイルを**実再取得**し、元のKB、fileId、NodeID、旧本文保持、更新管理メモの`ADNC_ORIGIN`と`ADNC_UPDATE_PROTOCOL_VERSION`、registry参照整合をすべて確認する。

## 完了判定・秘書への接続

- **互換導入 PASS**：上記の実保存と読戻しがそろった状態。`ADNC_INSTALLER_VERSION`は**引き続き未確認**。旧KBの全機能がv1.5.2になったとは報告しない。
- 秘書の**定期実行指示を変更できたかは別試験**。場所が確認できない場合は`secretary_hook=NOT_RUN`。新タスクを作らない。実際に動いている既存秘書に、`START_HERE`内の`ADNC_UPDATE_STATUS_PATH`と[DAILY_CHECK.md](DAILY_CHECK.md)を参照する短い1文を**その実行元の設定に**差分追記できる場合だけ実装・読戻しする。設定先にアクセスできないなら、本人が秘書の同じチャットへ指示できる短い案内にとどめる。
- 日次の重複排除用の`ADNC_LAST_CHECK_DAY`と`ADNC_LAST_NOTIFIED_MINOR`は、秘書が実際に動き、公開版を読取・比較でき、**この小さなメモに書戻しできる場合だけ**[DAILY_CHECK.md](DAILY_CHECK.md)に従い局所更新する。すべての確認・通知が成功するまで`daily_check=NOT_RUN`。初回の互換導入だけで日次自動実行のPASSにはしない。
- 戻す場合、実行を止めてから変更した一行・小メモ・registryレコードだけを変更前の状態に差分復旧する。私的データやログを自動削除しない。

**この方式は旧KBに更新確認の入口だけを追加する「互換レイヤー」であり、旧KBから最新インストーラー全体への完全な移行手順ではない。** 後日の完全移行は、現行設計・利用中の機能の差分を独立に検査してから判断する。
