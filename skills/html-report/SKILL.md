# AD&C｜秘書・PJ・定例の表示レポート制作Playbook v0.1.3

<!-- ADNC-HTML-REPORT-20261120 -->
**適用状態**：本人正式採用（単一HTMLの人間向けVIEW/SNAPSHOTと共通オフラインPython生成ツール）。**公開されている手順・ツールの採用**と、組織内での受入・配備・利用承認は別。組織が定めた利用権限と保存先が優先。既存の秘書専用UI／PJの正本／定例の実行結果は変更しない。

> AD&Cは「完成形のない仕組みで、完成する仕事を増やす」。HTMLを新しい正本にせず、読みやすく、戻れる形で渡す。

改訂担当だけの参照（通常利用では追加読込み不要）：

```text
EDIT_REF_PHILOSOPHY=https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge/blob/main/README.md
EDIT_REF_DESIGNER_NOTE=https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge/blob/main/templates/DESIGNER_NOTE.md
EDIT_REF_UPDATE_PLAYBOOK=https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge/blob/main/docs/DEVELOPMENT_WORKFLOW_PRACTICES.md
```

- **カスタム優先**：社内では当該組織の正式情報分類・表示・保存・承認・配布規則、個人秘書では本人の採用済み秘書Playbookを先に適用。取得不能な非公開ルールを推測しない。
- **HTML/PDF共通体裁（2026-11-21本人採用）**：人間向け公開ガイドとの配色・印刷レイアウトは[統一制作Playbook](../visual-docs/SKILL.md)を参照。公開ガイドはGit→レンダリング済み公開HTML／任意PDFだが、秘書/PJ/定例の実データ報告は**一時HTML→一時PDF→その回の1リンク**を優先し、公開GitHub/Pages、外部プレビュー、恒久Driveに自動保存しない。画面内の「PRIVATE」表示だけで秘密保護とはみなさない。
- `AI_NAV_PY_PATH=NONE`（このPythonはナビではなく**レポート生成器**）。`REPORT_RENDER_PY_PATH=./render_report.py`、`REPORT_PDF_PY_PATH=./html_to_pdf.py`（閲覧用PDFの一時出力ツール。AI_NAVではない）。
- **秘書の決定論的前処理（2026-11-22 実装）**：既存の本ディレクトリに `SECRETARY_RUNTIME_PY_PATH=./secretary_runtime.py` を追加。`python secretary_runtime.py --state /private/verified_state.json`（状態未取得なら `--state` 省略）でJSTの当日/7日間のCalendar時刻範囲、半月期H1/H2、月次40日/30日・既回答、未決定UI有無、案件状態数をJSON出力。**この低水準ヘルパーは接続・保存・PDF生成を行わず**、値が欠ける場合はUNKNOWN。ChatGPT等の連携AIは実サービスの読取・書込を別途実行する。本人情報を公開リポジトリに置かない。秘書の実行操作と保存先は非公開の統合秘書Playbookを唯一の業務正本とする。
- **秘書の日次一括生成（2026-11-23 実装試作）**：`SECRETARY_DASHBOARD_PY_PATH=./secretary_dashboard.py` を追加。現行ワークシートの10区分を含む**一時JSONを1回だけ作成**し、`python secretary_dashboard.py authorized_daily_input.json --out-dir /tmp/adnc-secretary` を1回実行する。既存 `secretary_runtime.py` のJST/月次・未決定判定、`render_report.py`、既存 `html_to_pdf.py --no-web-logo` を順に呼び、HTML・短い朝報告・JSON・ログと、利用可能ならPDFを一括生成する。10区分の欠落、根拠未提供、NOT_RUN、UNKNOWN、ERRORを別状態で保持し、PASSとされた欄に根拠文字列がない場合は `EVIDENCE_INSUFFICIENT` とする。前回区分が入力にある場合は状態・期限・次の一手の差分、実期限値がある項目は超過／本日／今後の日数と件数を計算する。入力した正本の取得、保存、メール送信、UI表示・押下は実行せず、それらをPythonの成功扱いにしない。出力は一時・非公開扱いで、実データを公開リポジトリへ入れない。PDF変換に失敗してもHTML・テキスト報告・ログ保存は独立して続け、保存できなければ標準出力にも朝報告を返す。テストは合成データのみで行い、同等定時枠でのPDF成功・実データ読取／保存・実ボタン・翌日自動実行は別途検収が必要。
- **発動条件**：「秘書の今日の報告をHTMLで」「このPJをカード化」「定例業務の週報・巡回状況をHTMLで」。専門固定出力やユーザー明示の別媒体がある場合はそちらを優先する。
- **生成対象**：`kind=secretary`（予定・判断待ち・引継ぎ）、`kind=project`（既存PJ_ID/TASK_ID・優先度・実績）、`kind=routine`（既存ROUTINE_ID/EXECUTION_ID・対象期間・例外）。PJと定例はそれぞれの管理正本・分母を保ち、単純に混ぜない。

## 1. 観測と入力

1. 今回の権限で閲覧できる**既存の正本**から、対象期間・ID・現行状態・根拠・次の一手だけを取得。秘書は当日の日次記録と採用済み秘書Playbook、PJは採用された1つのWBSと既存タスク管理先、定例は既存の定義正本と**各回の実行記録**を使う。チャット内の未検証要約から最新状態を補完しない。
2. 個人・社内のURL、職員名、進捗などを**公開GitHubや第三者プレビュー、外部AIへ自動転送しない**。社内情報は社内承認済みのツールと保存先だけで処理する。外部公開用サンプルには架空データだけを使う。
3. 入力はUTF-8 JSON。必須：`kind`、`title`、`snapshot_date`、`source_checked_at`、`source_label`。任意：`source_url`（HTTPSのみ）、`visibility`（既定private）、`summary`、`handoff`、`items`（配列）。各itemは`title`必須、`id / priority(P0,P1,P2,OTHER) / period（定例の対象期間） / due（PJの期限） / status / owner / next_action / evidence / source_url`を任意指定。既存の元IDを入れ、新IDを採番しない。欠落は未確認と記す。
4. **分母の区別**：PJ＝対象のTASK_ID、定例＝予定された実行回ID。欠損・遅延・UNKNOWNとDONEを混同しない。進捗率を資料が提供していなければ推測計算しない。

## 2. 作成（Pythonが使える場合）

```shell
python render_report.py example_synthetic.json report.html
```

- `render_report.py`はPython標準ライブラリのみ。**外部CDN／外部フォント／外部画像／通信API不要**で、HTML・CSSとフィルタ・全文コピー用JavaScriptを一つのファイルに生成する。外部の正本の取得、ログイン、権限付与、送信、共有、実行スケジュール、本人や職員への査定、帳票の編集は行わない。
- 入力JSONは会社の許可された作業環境・フォルダに置く。元情報や実URLを**この公開リポジトリに書き戻さない**。HTMLは生成環境の一時作業場所に置いてよい。後述のPDF閲覧導線ではHTMLのDrive等への永続保存は要求しない。HTML自体を明示依頼された場合のみ権限内の保存先を使用。出力先のアクセス権は保存先システム側で保証する（HTML内のPRIVATE表示はアクセス制御ではない）。
- Pythonが禁止／利用不能なら、同じデータ項目と表示条件で権限内のHTML制作を行い、未検証機能をPASSにしない。会社にPython導入やマクロ実行を強制しない。

## 3. 人間への標準の出口：一時PDFリンク1本（2026-11-21採用）

**利用者向けの方針**：秘書／PJ／定例で「まず見やすいダッシュボード」が目的の場合、既存正本 → Pythonで単一HTMLを**内部生成** → PythonでA4縦PDFへ変換 → **実在するPDFのリンクを冒頭に1本だけ**示す。HTMLリンク、PNGリンクを同時に並べない。チャット本文の短い実績報告、秘書専用の一問一答／4択／月次案内はその後で従来どおり続ける。PDFはVIEW/SNAPSHOTであり、データ正本や操作用の4択ではない。

**実行入口（中間HTMLは利用者に提示しない）**：

```shell
python render_report.py input.json /tmp/adnc_view.html
python html_to_pdf.py /tmp/adnc_view.html --output /tmp/adnc_view.pdf
```

- `html_to_pdf.py` は**Python＋Playwright＋Chromium**を使う任意の実行ツール。利用可能な同等のHTML→PDFエンジンを使ってもよい。Python標準ライブラリだけでPDFが生成できるとは主張しない。**Pythonやブラウザーの導入を全AI・全端末へ強制しない**。各AIがその実行環境の一時ファイルリンクを提供できる場合に限り使う。
- 変換後PDFは**単一列・上から下への読み順**。スマホでページ送り／連続スクロールしやすく、A4印刷も可能にする。横段組・左右2列・4列メトリクスをPDFに残さない。長さは自然改ページ、**1ページへ圧縮しない**（6ページでもよい）。詳細折りたたみは印刷時に展開し、PDF上で押せないコピー／アクションボタンは隠す。正本リンクと日本語の文字選択は維持する。
- **公式AD&Cロゴは任意**：実取得できる場合だけ、既存公式PNG `https://campsite7.jp/wp-content/uploads/2026/11/adnc-logo-compass-wordmark-20261016-684f1714.png` または検証済みローカル原本を小さく配置。見た目の近いロゴを生成して代用しない。ネットワーク・権限・画像形式で取得できなければ**ロゴ無しでPDFを完成**させ、失敗扱いにしない。公式配色の既存デザインは維持する。
- **報告の保存・公開は原則しない（2026-11-21本人明示）**：PDF・HTMLはその会話／実行環境内の一時成果物とし、利用者には生成済みPDFの1リンクを渡す。公開GitHub/Pagesへのアップロード、Google DriveへのHTML/PDF重複・恒久保存、外部レンダリングサービスへの秘密情報送信はしない。本人が特定の保存先へ明示依頼した場合だけ、その権限内で例外処理。一般ガイドの公開原本管理とは明確に分ける。新規タスク／台帳は増やさない。公開用汎用コードに個人情報を記録しない。
- **リンク表示の条件**：PDF生成・実ファイル存在／必要最低限の表示検査ができ、実際に受け取れるリンクが得られたら `［今日の秘書ダッシュボード（PDF）］` のように**PDFだけの実リンクを最初の返答に示す**。存在しない `sandbox:` や推測したURL・過去の日付のPDFを当日版として表示しない。チャット実行環境にファイル添付経路がなければ、生成できた事実と配布不能を区別し、代替は**従来のテキスト報告だけ**とする（HTMLリンクへ勝手に切り替えて選択肢を増やさない）。
- **別用途の明示依頼は優先**：開発者がHTMLそのもの、編集用素材、本人が認可したWebレンダリングを明示要求した場合はその目的に応じHTMLを渡してよい。その際はURLの直接描画可否とDriveのファイル保存リンクを区別する。PDF単一リンクの標準が、HTMLの内部生成・保守・AI再利用を禁止するわけではない。

## 4. 最小検収と再開

1. 正本のID・件数・優先度・状態・時点・出典が、生成したHTML／PDFの表示と合うことを確認する。欠落／不明を推測で補わない。
2. PDFの生成実体・ページ数・**単一列の縦順表示**・日本語の文字表示・文字選択・元正本へのリンクを可能な範囲で検査。別スマホ実機で未検証ならその部分はNOT_RUN。ロゴの取得可否は**非致命的**。
3. 利用者に示すPDFは実存在する**1リンクだけ**。HTMLは内部中間物のまま残す。元正本・秘書の4択／月次・PJのWBS・定例の実績は不変。PDFが使えない環境でも既存日次実務とテキスト対話を止めない。
4. 結果と問題・次の一手は既存案件／日次記録へ必要な短い事実だけを戻す。新しい台帳、永続HTML、承認ゲートは作らない。未実測の手順を成功済みと記さない。

**初回の範囲限定実測（2026-11-21）**：既存11月20日秘書HTMLをPythonでChromium PDF変換して、A4・縦単一列・6ページ・文字選択可能・正本リンク9件・HTTP外部要求0件を確認。**公式ロゴのWeb取得は環境の名前解決制限で未成功**、ロゴ無しで完成。実端末での閲覧と次回日次Automationでの一気通貫PDF生成・添付はNOT_RUN。既存 `render_report.py` の架空入力での3種HTML生成PASSは保持するが、秘書現物HTMLを同Pythonが作成したとは主張しない。

## 5. 配布・社内移植時の固定境界

- 公開の**汎用Playbookとコード**は、社内の`99_inbox/`等に取り込む**候補**。組織の承認なく`approved`へ昇格させず、社内の4列List／registry／playbooks.tsvを壊さない。法人・個人の実データを付属せず、サンプルは架空データのみ。
- 社内のPJ定例管理は[組織業務計画Playbook](../project-management/SKILL.md)を優先。「正式採用」の対象は**人間用表示・制作道具**であり、組織の会議設計・監督・人事評価を勝手に変更する権限ではない。
- 運用でPython禁止、Content Security Policy（CSP）やSharePointスクリプト制限がある場合は当該枝だけ`NOT_RUN`。**セキュリティ制限を回避しない**。内容静的閲覧は継続可能なら継続する。

**検収の初期実績（2026-11-20）**：架空入力を使ったPython生成・HTMLエスケープ・HTTPS判定・3種のkind出力はローカル試験PASS。実社内環境の受入・SharePointでのHTML直接表示・ブラウザーの本人押下・別AI利用はNOT_RUN。秘書/PJの既存11月20日版HTMLは**デザイン参考の現物**であり、本Pythonで元現物が生成された証拠ではない。
