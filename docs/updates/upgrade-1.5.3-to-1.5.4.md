# AD&C 差分手順｜1.5.3 → 1.5.4

> **実行品質ゲート：FROM=`1.5.3`、TO=`1.5.4`。** 既存KBの`START_HERE.md`から導入版を実取得し、[UPDATE.md](UPDATE.md)による連続版チェック・差分表・本人承認を満たしたときだけ適用。版不明なら[ADOPT_LEGACY.md](ADOPT_LEGACY.md)へ。

## 実装する差分（希望者のみ）

1. 現行`START_HERE`、`BUILD_PLAN`、`registry`、変更対象のArea/ProjectのID・版・SHA・fileIdを実取得して変更前状態を保全。動画制作を希望していないKBは**動画用のフォルダ・Runbook・PPTを作らない**。
2. 制作中シリーズがある場合、**採用見本PPTX・良好な動画・正式ロゴ・OP/ENDING・アイキャッチ等の実体**を探し、素材ごとに採用状態・版・利用権・取得可否を区別。共有KBの[動画制作・PPT初期設定Skill（Draft）](https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge/blob/main/skills/video-production-setup/SKILL.md)は参考のみ。個人用素材を共有KBへコピーしない。
3. 既存`30_contexts/Areas`のシリーズContextに「PPTと制作設定」を追加。PPTの実ID・採用版／背景・文字・強調色HEX／フォント・日本語字形／字幕とサムネ等の使用ルール／正式素材ID・役割・版／現行1制作Runbookの参照を**取得した範囲だけ**記録する。未取得は`unknown`/`NOT_RUN`。
4. 案件ごとの採用台本・PPT・音声方式・OP・ENDING・次の工程は**既存Projects/BUILD_PLAN**へ局所保存。過去のElevenLabs利用歴だけで音声採用や新規課金の承認としない。一般音声標準も勝手に変えない。
5. 必要な場合だけ`START_HERE`／registryに当該Contextの参照を追加。保存直前に現行原本を再取得し競合があれば局所停止。**同じfileId**へ差分保存し、該当registryレコードだけ再検証する。
6. 保存・読戻し・旧情報保全・参照導線がPASSした区間のみ、`ADNC_INSTALLER_VERSION: 1.5.4`を確定。**動画の実制作、PPTレンダリング、別AIの一行再開は別試験**であり、本更新だけでPASSとしない。

## 変えないこと

初回`実行`→保存先選択→推奨1案→`進めて`、NodeID・既存ID／Drive fileId・権限・秘書・日記・タスク、旧素材・本人朗読既定・有料API／公開の承認境界。見本未取得なら「色を保存できた」「動画ができた」と宣言しない。既存プロジェクトで使った正本と、本書の更新完了は別に判定する。
