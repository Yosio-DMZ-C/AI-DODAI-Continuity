# AD&C 差分手順｜1.5.1 → 1.5.2

> **実行前品質ゲート：FROM=`1.5.1`、TO=`1.5.2`**。現在のKBに`ADNC_INSTALLER_VERSION: 1.5.1`が**実在**し、[UPDATE.md](UPDATE.md)の経路確認と本人承認が成立した場合だけ適用する。旧KBで導入版未確認の場合は本ガイドを使わず、[ADOPT_LEGACY.md](ADOPT_LEGACY.md)へ進む。

## 最小変更

| 対象 | 差分 | 維持 |
|---|---|---|
| `START_HERE.md` | 既存`ADNC_UPDATE_RUNBOOK`の直後に`ADNC_LEGACY_ADOPTION`の短いリンクを1行追記。検収PASS後`ADNC_INSTALLER_VERSION`を1.5.2へ | 既存のNodeID・fileId・メタデータ・知識・参照 |
| 秘書指示 | 新規タスク・日記フォルダは作らず、既存の`DAILY_CHECK.md`リンクを使い続ける | 既存の予定・日記・通知・質問 |
| `registry.json` | START_HERE該当レコードの必要なrevision/hash/sizeだけ整合 | その他レコード |

## 承認後

1. START_HERE、BUILD_PLAN、registryと変更前ID/hash、NodeIDを実取得・保存。元の版が1.5.1と厳密一致することを再検査。
2. START_HEREへ以下1行のみ重複なく追記し、旧バージョン表記を局所置換する。

```md
ADNC_LEGACY_ADOPTION: https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/blob/main/docs/updates/ADOPT_LEGACY.md
```

3. 同一fileIdに更新。必要なregistryの最小変更と変更前保存を行う。
4. Driveから再取得し、版番号・リンク・旧本文・NodeID・fileId・台帳整合がPASSで初めて`1.5.2`と報告。失敗は復旧・保留。旧KB全体の互換化や日次チェック実行は今回のスコープ外。

これは**既存のインストーラー版1.5.1からの軽微な対応追加**であり、導入版不明の旧KBをバージョン1.5.2と偽装するための手順ではない。
