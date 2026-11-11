# AD&C｜外部資料取得に制限のあるAI向けオフライン導入キット

**正式名称**：AD&C — AI-DODAI & Continuity  
**コンセプト副題**：AgentOS-C（AIをエージェントにするOS）  
**対象**：外部GitHub Markdown本文をAIが直接取得できないが、利用者によるファイル添付が許されている環境

## 配布入口（固定URL）

- **[一括ZIP｜ADNC_Offline_Installer_Current.zip](https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/releases/download/guides-current/ADNC_Offline_Installer_Current.zip)**
- **[単一Markdown代替｜ADNC_Offline_Installer_Current.md](https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/releases/download/guides-current/ADNC_Offline_Installer_Current.md)**（ZIPを展開・内部読取できないAI向け）
- [最新版の正本（LATEST.json）](updates/LATEST.json)
- [GitHub Actions配布ワークフロー](../.github/workflows/publish-guides.yml)
- [自動生成・SHA-256検証スクリプト](../scripts/build_offline_installer.py)

## 対象範囲

一括ZIPには、最初に読む案内、現行共通インストーラー本文、PROJECT_EXECUTION_STANDARD.md（§6.3.2〜§6.3.3）、LATEST.json、README／QUICKSTART、添付方法・初回導入の案内、現行の更新手順、LICENSE、SHA-256一覧のMANIFEST.json、および主要ファイルを結合したALL_IN_ONE.mdを収録します。

これは**導入資料の搬送キット**であり、利用者の構築済みKB／バックアップ、共有KBの全Playbook／素材、任意の動画制作資材、社内の規定文書を含みません。インストール済みKBの再利用・同期・個人データ移行も自動的には実施しません。

**現行インストーラーの版**は同梱LATEST.jsonと、インストーラー先頭の配布版・ADNC_INSTALLER_VERSIONの一致で検査します。ファイルのSHA-256・ZIP CRC・展開内容をビルド時とReleaseアップロード後に照合します。外部接続不能な環境では、同梱スナップショットが公開mainの真の最新状態かどうかまでは保証できません。

## 社内利用の手順

1. 人間が社内規定に従ってZIPを入手し、許可されたAIの添付機能で渡す。最初に`00_READ_ME_FIRST.md`を読み、`MANIFEST.json` と各資料を確認する。
2. ZIPをAIが開けない・内部のMarkdownを読めない場合は、単一Markdown代替を添付する。ZIPを展開しただけで全文を読めたことにはしない。
3. AIへ`実行`と指示する。新規の場合は保存先選択→接続・読書き実測→推奨案1件→本人の`進めて`→構築・保存・読戻しへ進む。許可されない外部アクセスや書込みは試行しない。
4. **既存KBの場合**、新規構築を繰り返さず、同梱`updates/UPDATE.md` または `updates/ADOPT_LEGACY.md`から更新確認を始める。更新には別途本人の承認が必要。

## 記録する検証結果

| 項目 | 判定対象 |
|---|---|
| ZIP添付／展開 | アップロードと展開・内容列挙を個別確認 |
| 原文読取 | `INSTALLER.md` と `PROJECT_EXECUTION_STANDARD.md` の本文を読めたか |
| 同梱版一致 | `LATEST.json` の版と配布版・ADNC_INSTALLER_VERSIONの一致 |
| 公開mainの最新版一致 | 外部アクセスが不可なら`NOT_RUN` |
| 保存先／構築 | 実際に必要な権限と本人承認があるか |
| 保存／読戻し | 作成した本人KBの実ファイル・内容を再取得できたか |

個人・組織の**優先適用手順が未設定**なら標準手順を使用します。未設定のみでFAILにしません。§6.3.3の手順書開発用の独立コールドスタート検査を通常インストールに一律の追加ゲートとして強制しません。新規手順書の作成・重要改訂時には別途適用します。

## 版・名称・運用上の注意

正式製品名は**AD&C**。**AgentOS-C（AIをエージェントにするOS）**は旧名としての履歴と、設計思想を示す副題として残します。これはOSソフトウェアの配布・システム権限取得・新しいLLMランタイム提供を意味しません。旧名入りの互換ファイル名や歴史資料を一斉削除・改名せず、公開インストーラーを1本に維持します。

GitHub Releaseの`guides-current`に、既存の共通ガイドと旧無料ガイド廃止案内に加えて、ZIP／単一Markdownを自動更新・再公開します。直接リンクは固定ですが、更新後の同梱版・SHAはManifestに記録します。会社の情報セキュリティ規則、Web・ダウンロード制限、ファイル検査・添付制約を迂回しません。
