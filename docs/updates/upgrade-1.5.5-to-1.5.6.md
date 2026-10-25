# AD&C 差分手順｜1.5.5 → 1.5.6

> **FROM=`1.5.5`、TO=`1.5.6`**。[UPDATE.md](UPDATE.md)の数値版確認・連続版経路・差分表・本人承認を適用する。本人が承認する前に個人KBを書き換えない。導入版が不明な旧KBは数値を推測せず、[ADOPT_LEGACY.md](ADOPT_LEGACY.md)の互換手順へ。

## 目的：素材仕様の正本移動（構造は無変更）

本体側に置いた素材一般仕様のコピーを、新しい正本として維持しない。**一般仕様の正本は共有KBの[制作素材 A〜D 一般仕様表 v0.1](https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge/blob/main/skills/video-production-setup/PRODUCTION_ASSETS_GENERAL_SPEC_v0.1.md)であり、[動画制作初期設定Skill（Draft）](https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge/blob/main/skills/video-production-setup/SKILL.md)から参照する。** 本体の旧表URLは互換案内として残す。

| 対象 | 差分 | 保全対象 |
|---|---|---|
| `START_HERE.md` | 現行の更新入口／共通実行標準参照を保持。今回の実保存・実読戻し検収後だけ導入版を1.5.6へ | NodeID／Drive fileId／他の版軸／既存本文 |
| 動画希望者の既存シリーズArea Context／Runbook | **既に**一般素材表の旧本体URLを参照している箇所がある場合だけ、共有KBの正本URLへ最小差分置換。制作の途中で採用物が変わっていないことを実取得して確認 | 個々の原画像／PPT／音声／権利／採用判断／既存fileId |
| registry／BUILD_PLAN | 実際に更新したファイルのsha／revision／再開位置・検収状況だけ同期 | 過去の履歴、他のタスクやレコード |
| その他のKB・素材 | **無変更**。任意の動画制作設定がない場合、素材・Context・Skillを新規作成しない | 個人の秘密値、秘書、日記、TASKS、利用者データ |

## 適用・検収

1. 本人の更新承認を受け、対象KBの`START_HERE`と必要なregistry／Context／Runbookを**実取得**する。現行fileId、改訂番号、SHAを保全し、同じ実体の既存履歴で前版を残す。
2. 上の**共有KBの原本とSkill**が取得できることを確認。取得できなければ素材ポインタの更新はNOT_RUNとし、誤ったURLで書き換えない。
3. **当該KBに動画希望が明示され、かつ旧URLの現行参照がある場合だけ**その参照先を新URLへ更新する。無希望者へ表A〜Dの素材作成／40アイコン作成／人物立ち絵作成を始めない。採用見本がない希望者への小さな候補PPTX制作は別工程であり、この更新では実行しない。
4. 書込直前の再取得で他担当による変更がないことを確認。**Driveに原子的CASがあるとは仮定しない**。変更原本だけ同一fileIdへ差分更新し、実体／registryを再取得して検収する。
5. 保存・読戻し、ID・SHA・revision保全／変更反映を確認できた区間だけ`ADNC_INSTALLER_VERSION: 1.5.6`を確定。独立AIに必要な全画像が渡ったかは別試験、未実施ならNOT_RUN。最終配布版の数値変更だけで自動生成や実素材の存在を宣言しない。

新たな画像・ロゴ・人の写真・動画・SVGスプライト・追加データベース・スケジューラ・秘書タスクをこの更新で作成しない。共有KBのDraftをActiveへ昇格しない。公開・課金・送信・削除・権限変更には従来の別承認を要する。
