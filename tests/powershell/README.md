# AD&C PowerShell 自動テスト実行手順（v0.1 / β）

> **修正時の必須参照**：修正前に[AD&C共通実行標準 §6.3.2〜§6.3.3](https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/blob/main/docs/PROJECT_EXECUTION_STANDARD.md)の現行本文を実取得し、必要な検査を行う。実装依頼はGit/設定/読戻しまでを完成条件とする。未実行工程は `NOT_RUN`。

**【目的】** AIのPowerShell修正を、Windows PowerShell 5.1とPowerShell 7の実行結果で検証できるようにする。

**【背景】** AD&C調査担当はAI環境にPowerShell本体がないため、Windows実行の証跡を作れなかった。
言語移行ではなく、既存GitHub ActionsのWindowsランナーを利用して実行・失敗ログ・再試験をつなぐ。
本キットは専用テスト基盤の初期スモーク試験であり、既存の製品用PowerShellコードの動作保証ではない。

**【必須条件】** 公開リポジトリ内の合成データのみ。APIキー、本番KB、実ユーザー環境、外部送信、権限変更をテストに含めない。Pull Requestの検収前にmainへマージしない。

## 必要資料・素材・ツール

| 役割 | 現行入口 | 必須 | 状態 |
|---|---|---|---|
| ワークフロー | `.github/workflows/test-powershell.yml` | 必須 | 提案版 |
| 実行スクリプト | `scripts/Invoke-ADnCPester.ps1` | 必須 | 提案版 |
| テスト例 | `tests/powershell/Smoke.Tests.ps1` | 必須 | 提案版 |
| テスト基盤 | Pester 5.7.1（PowerShell Gallery） | 必須 | 実行時導入 |
| Windows実行環境 | GitHub Actions `windows-2025` | 必須 | Actions実行時取得 |

## 実行方法（単一入口）

1. この4ファイルをリポジトリの相対パスどおりに配置してPRを作る。PRの変更にPowerShell関連ファイルを含めると、`AD&C PowerShell Pester (Windows)` が自動実行される。
2. GitHubのPR → **Checks** にある `PowerShell-5.1` と `PowerShell-7` を開き、両方の終了結果を確認する。実行ログを読んで失敗行を特定する。
3. Actionsの実行画面から `pester-PowerShell-5.1` / `pester-PowerShell-7` のNUnit XML成果物を取得する。両ジョブPASS、4テスト以上実行、XML出力ありを初期環境の合格条件とする。

**既存コードの試験を追加する場合**：`tests/powershell/` に `機能名.Tests.ps1` を追加し、対象の `.ps1` をテスト内で読み込んで正常系・異常系・副作用を検査する。ジョブはディレクトリ内の全 `*.Tests.ps1` を実行する。手動実行はActionsの `Run workflow` を利用する（ワークフローがデフォルトブランチへ入った後）。

**Windows PCで任意に実行する場合**：PowerShell 5.1または7でPester 5.7.1を初回だけ `Install-Module Pester -RequiredVersion 5.7.1 -Scope CurrentUser -Force -SkipPublisherCheck` で導入し、リポジトリルートから次のいずれかを実行する。

```powershell
powershell.exe -NoProfile -File .\scripts\Invoke-ADnCPester.ps1 -ExpectedMajor 5
pwsh.exe -NoProfile -File .\scripts\Invoke-ADnCPester.ps1 -ExpectedMajor 7
```

**出力**：`test-results/pester-ps5.xml` または `pester-ps7.xml`（GitHub Actionsでは7日間のArtifacts）。ログにPS本体のバージョン、Pesterのバージョン、テスト数、失敗理由が出る。実行の度にファイルは更新されるため、秘密値はテストで使用しない。

**停止条件／再開**：Pester導入不能・PSメジャー版不一致・テスト0件・1件でもFAIL・XML未生成ならそのジョブはFAIL。環境にWindowsランナーがない、GitHub権限で実行できない、または実行が確認できない場合は `NOT_RUN`。失敗時はPRの該当ログを確認し、必要な1ファイルだけ直して再実行する。Gitの復元元はPR作成前のmainコミット。公開／mainマージは別判断。

## ユーザー制作物ZIP化サンプル（小規模・透明なバックアップ）

- 対象：`scripts/Export-UserWorkArchive.ps1`、テスト：`tests/powershell/Export-UserWorkArchive.Tests.ps1`。
- 実行者が指定した**単一フォルダ**だけを見る。既定はサブフォルダをたどらない（必要な場合だけ `-Recurse`）。対象拡張子：bat、cmd、ps1、txt、md、csv、rtf、doc、docx、xls、xlsx、ppt、pptx、odt、ods、odp。
- **既定はプレビュー（ZIPは作成しない）**：対象ファイル名、件数、元データの合計バイト数を返す。ZIP作成には `-CreateArchive` の明示指定が必要。
- 既定上限は**200件・100MB**。必要な業務量に合わせた上限変更は明示指定。上限超過時はZIP作成前に終了。
- ZIPは暗号化せず、`System.IO.Compression` を使い **NoCompression** で格納（テキスト類の再圧縮も行わない）。ネットワーク送信、セキュリティ製品の設定変更、ファイル実行、特権昇格、隠しファイル取り込みをしない。元ファイルは読み取りだけ。
- フォルダ構造の相対パスを維持。既存ZIPは上書きしない。保存先は元フォルダの外、既存ローカルディレクトリであること。

プレビュー：

```powershell
.\scripts\Export-UserWorkArchive.ps1 -SourceDirectory 'C:\Work\ProjectA' -DestinationZip 'C:\Backups\ProjectA.zip' -Recurse
```

作成：

```powershell
.\scripts\Export-UserWorkArchive.ps1 -SourceDirectory 'C:\Work\ProjectA' -DestinationZip 'C:\Backups\ProjectA.zip' -Recurse -CreateArchive
```

**位置づけ**：不用意な大量処理や大量ファイル更新をしない、業務説明可能なローカルアーカイブの設計。監視ソフトの検出可否・例外承認・社内規程への適合は実環境で別判定。監視回避や暗号化の隠蔽を目的とするものではない。

**検収境界**：本キットの静的構造、Windows上のPester初期実動作、将来の業務スクリプトの動作はそれぞれ別ゲート。Windows実行ログとNUnit XMLの現物がない段階では実動作を `PASS` にしない。
