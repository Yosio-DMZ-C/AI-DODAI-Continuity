# AD&C 差分手順｜1.5.0 → 1.5.1

> **実行前品質ゲート：FROM=`1.5.0`、TO=`1.5.1`（インストーラー版）**。KBの実際の導入版が**ちょうど1.5.0**で、[UPDATE.md](UPDATE.md)が指定する目標版・承認・対象KBの照合を通過したときだけ実行。1.4.0等からこの手順だけを直接使わない。すでに1.5.1なら無変更で終了。

## 変更内容

| 対象 | この版の差分 | 保持 |
|---|---|---|
| `START_HERE.md` | 更新の起動先を`ADNC_UPDATE_RUNBOOK`で指定、`ADNC_INSTALLER_VERSION`を検収後1.5.1とする | NodeID、既存の`ADNC_UPDATE_MANIFEST`、その他の内容・fileId |
| 本人の既存データ・秘書指示 | 変更なし | 全内容と現行タスク・予定 |
| `registry.json` | START_HEREの旧レコードに必要なhash/size/revision整合のみ | 他レコード・ID・履歴 |

## 実施（承認後のみ）

1. `START_HERE.md`に存在する導入版が`1.5.0`と確定し、変更前本文・fileId・registry旧記録を確保。
2. 同じ`START_HERE.md`の適切な冒頭位置（JSONメタデータ内部やコードブロック内部は避ける）へ、次の**1行だけ**追加。すでに同じ値があれば重複追加しない。

```md
ADNC_UPDATE_RUNBOOK: https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/blob/main/docs/updates/UPDATE.md
```

3. `ADNC_INSTALLER_VERSION`は`1.5.0`から`1.5.1`へ局所置換する。既存の`ADNC_UPDATE_MANIFEST`は維持。冒頭に「**アップデートして**」を受けた際は、リンク先のUPDATE.mdを**先頭の品質ゲートから実取得・適用**するという短い起動案内を1行だけ残す。
4. 同一fileIdで保存、実読戻し。START_HEREがregistryで登録済みなら当該レコードの実hash/size/revisionだけ同期・読戻しする。変更前版は既存履歴へ保全。
5. **検収**：`START_HERE`に版`1.5.1`とUPDATE.md入口があり、元のID・私的内容が保持され、台帳も整合することを確認。いずれか欠けた場合はFAIL／NOT_RUNを区別し、今回のアップデート完了とはしない。

この変更は更新指示の置き場所整理のみ。新DB、新規定期タスク、公開、共有、再インストールを伴わない。
