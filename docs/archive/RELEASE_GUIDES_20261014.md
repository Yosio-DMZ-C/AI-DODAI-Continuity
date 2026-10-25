# 配布資産の復旧用固定参照｜guides-current（2026-10-14版）

この文書は2026-10-25の公開ワークフロー修正前に、配布中の2ファイルと歴史的Git原本の一致を検査した記録。旧Release資産を削除せず、Git履歴の真正な復元先を確保する。個人KBは含まない。

| 配布ファイル（安定URLの末尾） | サイズ | 旧Releaseに登録されたSHA-256 | 復元原本（Git commit） |
|---|---:|---|---|
| `AgentOS-C_Guide.md` | 79,490 bytes | `2a45b3bf0b5da640237fba6464e97ab58b43219f129338bdbcdceb7738189c38` | `docs/AgentOS-C_設計・構築運用指示書_一般配布版.md` |
| `AgentOS-C_Free_Guide.md` | 23,396 bytes | `056bc3fea84faadf1311317a7b026ae8ff649b26c2316175cd0c9cb4cbcb56fd` | `docs/AgentOS-C_設計・構築運用指示書_AI無課金ユーザー版.md` |

**固定コミット**：[`c97bf86a9669774f678ca5342e2bfb68be6050be`](https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/commit/c97bf86a9669774f678ca5342e2bfb68be6050be)

**独立照合**：2026-10-25、GitHub connectorでこのコミットのMD本文を別々に取得しUTF-8バイト列でSHA-256を計算。両ファイルのサイズとSHAが既存Release metadataとそれぞれ完全一致（PASS）。Releaseのバイナリ直接ダウンロードによる2重照合はNOT_RUN。ただし歴史的Git原本はRelease登録済みSHAと同一の内容なので復旧元として使用可能。

**復旧方法**：このリポジトリをクローンした作業環境で、必要な原本を当該コミットから `git show 'c97bf86a9669774f678ca5342e2bfb68be6050be:<原本パス>' > <配布ファイル名>` によりUTF-8を壊さず取り出し、上記SHAを再計算。Releaseへの書き戻しは、その時点の本人承認と現状バックアップがある場合のみ。自動復元・自動削除は禁止。

**配布方針**：今後の`AgentOS-C_Guide.md`は現行の共通AD&Cインストーラーを指す。旧`AgentOS-C_Free_Guide.md`のURL／本体は歴史的互換用に保持し、新規導入の推奨版として案内しない。名称の旧表記はURL互換のため残す。
