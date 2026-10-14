# AD&C（AI-DODAI & Continuity）名称移行計画 — 審査用

## 追記：本体リポジトリ改名の実施結果（2026-10-14）

**現在の本体正本：** [Yosio-DMZ-C/AI-DODAI-Continuity](https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity)。旧名称は `Yosio-DMZ-C/AgentOS-C`。利用者の明示承認により、GitHubの同一リポジトリを改名済み（repo ID `1409572106`）。PR #9はmainへマージ済み（`5cdd1056c9d74ae3dfcdd8403e6b71abd9d1eb64`）。

- **PASS：** 新URLのリポジトリAPI取得、同一固定ID、旧URLからのAPIリポジトリ参照（新名称へ解決）、main、PR #9と過去コミット、`guides-current` のRelease・従来資産2件の登録メタデータ、既存ワークフロー／過去manifest／配布設計書のblob SHA維持。
- **NOT_RUN：** 旧URL・新URLからのRelease資産の実ダウンロード／独立SHA照合、ブラウザでのHTTP転送検査、改名後の配布ワークフロー実行、Claude/Geminiのアクセス改善確認。GitHub接続経由での配布ファイル直取得は404となり、利用者環境での成否とは区別する。
- **継続方針：** 配布タグ `guides-current` と資産名 `AgentOS-C_Guide.md` / `AgentOS-C_Free_Guide.md`、設計書の旧ファイルパス、NodeID、個人KB固定ID、過去のmanifest・ハッシュを保持。共有知リポジトリの改名は別判断とする。今回の表示・URL訂正PRでもこれらには触れない。

**以下は改名前に作成した計画・承認条件・当時の検査結果をそのまま残した歴史的記録です。** 以下の「未承認」「未実施」「候補URLは有効でない」といった文言は記述当時の状態であり、現況は本追記を優先してください。

---

- 作成日：2026-10-14
- 状態：**名称移行計画／PR #9のマージ承認を受領（2026-10-14）**。**本体リポジトリの改名は未承認・未実施**。個人KB・旧リリース・外部サービスも変更しない。
- 改名前の正本：`Yosio-DMZ-C/AgentOS-C`（調査時の main: `34eeed2cf260185e7959424eb3085d4f4eb4c201`）
- 改名第一候補：`Yosio-DMZ-C/AI-DODAI-Continuity`（**未実施・現時点で有効なURLではない**）
- 表示名称：**AD&C — AI-DODAI & Continuity**
- キャッチコピー：**AIを替えても、冒険は続く。**
- DODAI：日本語の「土台」。特定のAI製品やエージェント実装に依存しない知識・判断履歴・作業状態の基盤。
- 最上位目的：本人が人生・仕事でより良い選択を行えるよう支援すること。AIによる意思決定の代行ではない。

## 0. 進行判断の伝達記録（2026-10-14）

- 利用者からの連絡：リーダーの判断は「Draft解除・マージを実施する段階です。マージ完了後、本体リポジトリの改名に進む直前に、改めて承認を求めてもらうことにします」。
- **本指示で実施可能な操作は、PR #9 のDraft解除とmainへのマージのみ**。文言の承認と改名操作の承認を混同しない。
- 伝達の出典は利用者からの本チャットでの報告であり、**チャット間での自動同期やリーダー側ドキュメントの直接変更を意味しない**。
- PRのマージ後はGitHubのPR履歴とmainに残る本計画を、後続担当の参照点とする。
- **次に必要な承認**：本体 `Yosio-DMZ-C/AgentOS-C` を `Yosio-DMZ-C/AI-DODAI-Continuity` に変更する直前の別途明示承認。旧配布資産の上書き、共有知の改名、個人KB変更は今回対象外。

## 1. なぜ段階移行するか

名称の表示、GitHubの正式リポジトリ名、成果物のファイル名、KBのNodeID、過去版・試験の識別子は**別物**である。これらを一括文字列置換すると、固定ダウンロードURL、旧版の再現可能性、登録済みの参照、ハッシュ、運用中のKBを壊す。

TRPGの「ルールブック・GM・キャラクターシート・キャンペーン記録」との対比、AD&Dへのオマージュ、GURPS的な小さな共通ルールと拡張Skillは**説明の比喩**として使う。新しいゲーム機構、AI実行ランタイム、DB、専用ジョブは追加しない。モデルの裁量と成果物の品質ゲートは維持する。

## 2. 識別子と変更方針

| 対象 | 変更方針 | 理由・制約 |
|---|---|---|
| 外向け表示名、README/Quick Start/Wikiの説明 | AD&Cを採用。旧称も併記 | 新旧どちらで検索しても到達しやすくする |
| 本体GitHubリポジトリ名 | **別途承認後** `AI-DODAI-Continuity` へGitHubのrename機能で変更 | 別リポジトリ作成・履歴移し替えはしない。Git履歴・Issue・PR・タグを維持 |
| 共有知 `AgentOS-C-Shared-Knowledge` | **今回は改名しない** | 独立の採否・検証・別承認。相互参照の更新は段階的に行う |
| 配布タグ `guides-current` | **保持** | 固定ダウンロードリンク互換性を優先 |
| 配布資産 `AgentOS-C_Guide.md` / `AgentOS-C_Free_Guide.md` | **保持** | URLパス末尾の資産名を変えない |
| ソース配布設計書の相対パス・旧ヘッダー | 第1段階では**保持** | ワークフローの入力名・先頭行検査・既存リンクが依存 |
| `START_HERE.md`、`BUILD_PLAN.md`、`00_system/registry.json`、NodeID、fileId、個人KB固定ID | **保持** | 構造・継続性の契約。個人KB正本には触れない |
| `AgentOS-C_initial.zip` など既存受渡し名 | 当面**保持** | 古い手順・利用者側のパスを壊さない。新規形式は別判断 |
| `release/MANIFEST-v0.1.0.json`、過去リリース、SHA、過去検証結果 | **過去時点の記録として不変更** | 過去の正本・データ・ハッシュを書き換えない |
| `.github/workflows/publish-guides.yml` | 今回のDraft PRでは**不変更** | 編集するとmainマージ時に配布アクションが起動し、`--clobber` が既存資産を上書きする可能性 |
| 公開ブログ、外部サイト、個人Google Drive等 | **変更しない** | 本PRの権限範囲外 |

## 3. 固定配布リンクと公開資産の事前確認

調査対象URL（**改名前**）：

- 一般配布版：<https://github.com/Yosio-DMZ-C/AgentOS-C/releases/download/guides-current/AgentOS-C_Guide.md>
- 無課金ユーザー版：<https://github.com/Yosio-DMZ-C/AgentOS-C/releases/download/guides-current/AgentOS-C_Free_Guide.md>
- タグ：<https://github.com/Yosio-DMZ-C/AgentOS-C/releases/tag/guides-current>
- 現行ソース：[`docs/AgentOS-C_設計・構築運用指示書_一般配布版.md`](AgentOS-C_設計・構築運用指示書_一般配布版.md) ／ [`AI無課金ユーザー版`](AgentOS-C_設計・構築運用指示書_AI無課金ユーザー版.md)

GitHub Releases APIでは `guides-current` と次の資産メタデータを確認できた（2026-10-14）。ここでのPASSは**API上の存在・サイズ・登録ダイジェスト**についてであり、利用者端末でのHTTPダウンロードやダイジェストの独立再計算は**NOT_RUN**。

| 資産 | 登録サイズ | APIに登録されたSHA-256 |
|---|---:|---|
| `AgentOS-C_Guide.md` | 77,692 bytes | `a57085605a0fa2959551101293c95c6d19ec58c31b38319df2cf83d1779cf027` |
| `AgentOS-C_Free_Guide.md` | 23,396 bytes | `056bc3fea84faadf1311317a7b026ae8ff649b26c2316175cd0c9cb4cbcb56fd` |

現行ソースMarkdownのUTF-8バイト数もそれぞれ77,692・23,396で一致。ただし**同じサイズは同じ内容・SHAを証明しない**。

### `publish-guides.yml` の静的検査

現行ワークフロー：

1. `main` の2つの**旧ソースパス**またはワークフローファイル変更時のpush、もしくは手動 `workflow_dispatch` で起動。
2. `actions/checkout@v4` で `main` を取得。
3. `cp` で2つの旧資産名へコピーし、非空・`^# AgentOS-C` ヘッダーを確認。
4. `GH_REPO: ${{ github.repository }}` で**現リポジトリ名を動的参照**、既存の `guides-current` へ `gh release upload --clobber`、なければタグを作成。

**改名そのものに対する静的整合性：PASS（条件付き）**。リポジトリ名がスクリプト内に固定されておらず、改名後も旧ソースパス・旧ヘッダー・タグ・資産名を維持する限り、リポジトリ名の変更だけを理由に失敗する箇所は見つからなかった。

**改名後の実アクション稼働：NOT_RUN。** 接続権限、Actions設定、GitHub側の挙動、実アセットの更新は改名後に別途検査する。設計書の見出しやファイル名を先に変えるとコピー／`grep`が失敗する。ワークフローを先に編集すると自動実行・既存アセットの上書きがあり得るため、このPRでは触らない。

## 4. 参照関係と影響範囲

調査した現行Gitツリー（本体・共有知）：

- 本体の主要入口：[`README.md`](../README.md)、[`QUICKSTART.md`](../QUICKSTART.md)、[`docs/wiki/Home.md`](wiki/Home.md)、[`docs/wiki/Getting-Started.md`](wiki/Getting-Started.md)、[`docs/wiki/Future-Vision.md`](wiki/Future-Vision.md)、[`docs/wiki/Verified-Results.md`](wiki/Verified-Results.md)。
- 配布設計書は上記2つの**旧パス**を参照し、ワークフロー・README・Quick Start・Wikiから内部相対リンクが張られている。
- [`docs/COMPATIBILITY_STATUS.md`](COMPATIBILITY_STATUS.md)、[`docs/PROJECT_EXECUTION_STANDARD.md`](PROJECT_EXECUTION_STANDARD.md)、[`release/README.md`](../release/README.md)、[`release/MANIFEST-v0.1.0.json`](../release/MANIFEST-v0.1.0.json) は仕様・検証・履歴上の旧称を含む。自動置換しない。
- 共有知の [README](https://github.com/Yosio-DMZ-C/AgentOS-C-Shared-Knowledge/blob/main/README.md)、[共有プラクティス](https://github.com/Yosio-DMZ-C/AgentOS-C-Shared-Knowledge/blob/main/docs/DEVELOPMENT_WORKFLOW_PRACTICES.md) は旧本体URLを参照。今回の共有知リポジトリは読み取り調査のみで、編集・改名しない。
- ブログ、Google Drive資料、既存利用者のcloneや配布先はGitHubツリーの外に存在する。全件取得済みとは言わず、移行後の連絡・更新は別工程。

**重要**：旧本体URLを今回のPRで新URLに一括置換しない。新リポジトリ名は現時点で存在せず、先にリンクを書き換えると404になる。

## 5. 推奨実施順序と承認ゲート

### 段階A：今回行うこと（Draft PR）

1. 現行のGitツリー・タグ・リリース資産・ワークフロー・主要参照を調査。
2. この移行計画を作成し、表示名称をREADME・Quick Start・Wiki入口に**移行予定表記として併記**。旧リポジトリURL・相対パス・配布アセット名を維持。
3. 変更ブランチでMarkdownリンク、変更範囲、機微情報、ワークフロー・配布ガイド不変を検査。
4. **Draft PR**を作り、リーダーへ提出。mainの変更・本体改名はしない。

### 段階B：名称表示の審査とPRの取扱い

5. リーダーが文言・互換性・PRの採否を判断。PRマージも**別途判断**。マージする場合はmain側の変更・配布Actionのトリガーを再確認する。
6. この時点では公開名と技術名の併記に過ぎない。完全URLによるAIからの取得障害が改名で直ることは未証明。

### 段階C：本体リポジトリ改名（**直前に別途明示承認**）

7. GitHubの現在の完全URL、対象リポジトリ、予定新名称の取得可否、ブランチ・PR・タグ・リリース・権限、使用者・外部リンクの影響を再確認する。
8. 管理権限と明示承認を得て、**同じGitHubリポジトリのrename機能**で変更する。新規リポジトリへのコピー・移動はしない。
9. 旧名称のリポジトリを新たに作らない。GitHubのリダイレクトを奪い、既存リンクを壊す可能性がある。
10. 改名後、旧URL／新URL双方で本体のREADME・main・ソース・タグ・Releasesを実アクセス確認。2つの固定ダウンロードを**旧URLと新URLのそれぞれ**から取得し、HTTP結果・内容・SHAを確認する。問題があればリンク更新を停止する。
11. ワークフローの改名後の実行は、`--clobber` による資産再アップロードを伴うため、**実行前にリリース更新範囲の承認とバックアップ確認**を行う。配布後にダウンロードとSHAを再確認する。

### 段階D：改名後のドキュメント・共有知対応（別PR・独立判断）

12. 新URLの稼働を確認してから、入口・Wiki・新規配布物の参照先を正規の新URLへ段階更新。**既存ファイル名、NodeID、個人KB固定ID、旧版のmanifestや検証履歴は変更しない**。
13. 今後配布ガイドの見出しを `# AD&C` に変えたい場合、`grep '^# AgentOS-C'` の条件調整と同期して行う。**ワークフロー更新に伴う自動リリース再配布を別承認・別検査**し、旧ファイル名のダウンロードURLは維持する。
14. 共有知リポジトリは**名前を変えず**に参照URL等の小さな差分修正が必要か独立判断。共有知そのものの改名は別承認。
15. 利用者・ブログ・外部資料のURL更新は本計画外とし、権限を得た別作業で扱う。

## 6. 検査台帳（このDraft時点）

| 対象 | 判定 | 根拠／未検証 |
|---|---|---|
| 現行Gitツリー、`main`、移行対象候補名の現時点のAPI参照 | **PASS** | 本体・共有知のGitHub API読取、現在の新候補URLは404（存在確認時点のみ） |
| `guides-current`・旧資産2件の名称／サイズ／登録SHA | **PASS** | GitHub Releases API |
| 現行配布ソースのUTF-8サイズと資産サイズ | **PASS（サイズのみ）** | 両方一致。実体の内容・ハッシュ一致とは別 |
| ワークフローの名称非依存・旧パスと旧見出しへの依存 | **PASS（静的）** | `publish-guides.yml` 読取 |
| 現行の旧URLでの人間端末からのダウンロード | **NOT_RUN** | 今回の接続ではHTTPバイナリ取得を独立確認できない |
| 新リポジトリURLの実稼働・旧URLからの転送 | **NOT_RUN** | 改名前なので実検査不可 |
| 改名後のRelease旧URL・新URLの資産取得とSHA確認 | **NOT_RUN** | 改名前。GitHub公式の一般的なredirect説明を代用しない |
| 改名後のワークフロー実行・リリース更新 | **NOT_RUN** | 改名・再アップロード未許可 |
| AIによるGitHub取得の改善 | **NOT_RUN** | Claude／Geminiで比較試験が必要 |
| 個人KB ID・履歴の維持 | **PASS（変更なしの範囲）** | 本Draftでは個人KBを一切変更しない。個人KB側の独立検査はNOT_RUN |
| 新旧全公開外部リンク・ブログ・利用者のclone | **NOT_RUN** | 本PRの対象外 |

## 7. 改名に関する公式資料

- [GitHub Docs — Renaming a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository)：Git履歴・Issues・Wiki等の移行とリダイレクト、PagesおよびAction参照の例外、旧名再利用禁止。
- [GitHub Docs — Linking to releases](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases)：リリース資産への固定リンク。
- 社内・個人KBの参照は本計画に転載せず、非公開の正本で扱う。

## 8. リーダーに求める判断

1. AD&Cの**表示名称の先行導入**と、本Draft PRの3入口ファイル＋移行計画という範囲が適切か。
2. `guides-current`・旧資産名・旧ソースパスを維持し、ワークフローを今回変更しない方針を承認するか。
3. 本Draftのレビュー後、**PRをマージするか**。リポジトリ名変更の承認とは明確に分ける。
4. **本体リポジトリ名変更の実行直前**に改めて承認を得る。共有知の改名・個人KB変更・旧資産上書き・外部ブログ変更は本依頼の対象外。
