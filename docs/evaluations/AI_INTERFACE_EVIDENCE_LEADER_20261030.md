# AD&C AIインターフェース研究：外部知見・現行実装・独立検収 引渡し v0.1

- 作成日：2026-10-30 JST
- 担当：AD&C 挙動品質／AIインターフェース研究
- 対象：既存 ADNC-T005（挙動品質）、T017（素材・道具入口）および T007/T015 の既存入口・完走ゲートとの接続
- 状態：**調査・実装用試験パッケージ作成。既存 main の変更なし。独立AIによる効果実測 NOT_RUN**
- 保存先：既存 Draft PR #17 の研究用ブランチ（新タスク・新PR・新DBを設けない）
- 公開範囲：公開資料・非機密の事例だけ。個人KBのURL／fileId／原本内容は転記しない

## 0. エグゼクティブサマリー／推奨する1案

**新しいAIインターフェース規則は増やさない。現行の「文脈ゲート→道具棚→完了ゲート」に、既存Q1〜Q4独立検収とT005のA/B/C試験を適用し、失敗した局所だけを修正する。**

最大の未実証は「正本に書かれていること」ではなく、(a)新しいAIが自然文の依頼から該当Skill・正本を発見できるか、(b)必要な規則と実物を取得できるか、(c)それを作業途中に適用できるか、(d)保存・読戻し・受け手の利用まで完走できるかである。

**リーダーに残す判断は1件**：既存Q1〜Q4とT005の隔離ケースで先に独立検収を実施し、**FAILの根因が確認されるまで共通標準やSkill全文を拡張しない**方針を採用するか。推奨＝採用。試験には公開・本番上書き・追加権限・新規スケジュール・費用を含めない。

## 1. 正本・最新状態の照合（2026-10-30確認）

| 対象 | 実取得の事実 | 判定 |
|---|---|---|
| 基本設計 v0.4（2026-10-26） | 定義は「判断の瞬間に自然に何が参照されるか」。3機能＝文脈ゲート／道具棚／完了ゲート。固定コア＋Skill別の深度指定、GATE行を提案 | 設計資料の実取得 PASS |
| AD&C本体 main 共通標準 | \`docs/PROJECT_EXECUTION_STANDARD.md\` **v0.1.18**。AIインターフェース入口・承認境界・実行完走・人間の3工程以上のロードマップを実読戻し | 正本実装 PASS、別AI効果 NOT_RUN |
| 共有KB main | \`docs/templates/LEADER_WORKSHEET.md\`：実装・運用・効果を分離、承認済み可逆作業の完走、元工程追跡、Q1〜Q4入口・終了条件が存在 | 正本実装 PASS、別AI効果 NOT_RUN |
| Issue #13 | 公開OPEN親案件12件。T005/T017はIN_PROGRESS。最新監査でも自然文からの独立コールドスタート、実利用効果はNOT_RUN | 現行状態を確認 |
| Draft PR #17 | 4分類×5件の20ケースと4件スモーク、A内容/B実画面/C実コピーを別採点。SEC-FMT01の本番反映と独立比較は未確認 | 試験準備 PASS、実AI比較 NOT_RUN |
| T017素材入口 | 素材ID→台帳参照27/27の静的解決はリーダー報告でPASS。ただし27点の実物SHA・実利用、別AI取得はNOT_RUN | 一部PASS／最終NOT_RUN |

注：2026-10-26の基本案v0.4には当日のPRを「Draft」と記載する古い時点の記述がある。後日の main マージ・更新は、最新のGitHub実物およびIssue #13を優先する。DRIVEの非公開原本URL・fileIdは本公開資料に記載しない。

検査リンク：
- [本体共通標準 main](https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/blob/main/docs/PROJECT_EXECUTION_STANDARD.md)
- [共有KBリーダーワークシート main](https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge/blob/main/docs/templates/LEADER_WORKSHEET.md)
- [統合Issue #13](https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/issues/13)
- [T005既存20ケース試験票（Draft PR #17）](https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/blob/docs/runtime-quality-pilot-20261016/docs/evaluations/RUNTIME_OUTPUT_PILOT_CASES_v0.1.md)
- [現行main採用・効果NOT_RUNの監査記録](https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/issues/13#issuecomment-6500536564)
- [最新T005/T017監査記録](https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity/issues/13#issuecomment-6502039713)

## 2. 外部一次知見とAD&Cへの転用

### E01 文脈の位置効果＝重要情報の「発見・再提示」を測定する根拠
Liu et al. (2024), *Lost in the Middle* は、長文中の情報検索・多文書QAで、関連情報が入力の中ほどにあると性能が落ちる条件を実験で確認。AD&Cの「Skill冒頭の短い入口＋実行節目で関連箇所のみ再参照」を**検証する動機**になる。ただし研究はAD&Cの完走率や特定モデルの個別配置最適値を保証しない。
一次資料：https://aclanthology.org/2024.tacl-1.9/

### E02 「最小の十分な文脈」と段階的開示
Anthropic, *Effective context engineering for AI agents* (2025) は、長く堅い列挙ではなく、必要な情報を十分に含みつつ無駄を減らし、最小構成から失敗事例で改善することを推奨。Anthropicの*What are skills?*（2026-09-22）はSkillの動的読込（progressive disclosure）を公式に説明。2026-10-22の同社発表はAgent Skills標準のAAIFへの移管を報じる。AD&CのSkill別3段階読込・README→Skill→必要正本の経路と整合する。
**注意**：標準採用企業数などの発表値は提供元の主張であり、AD&Cの効果試験ではない。
一次資料：
- https://www.anthropic.com/research/effective-context-engineering-for-ai-agents
- https://support.claude.com/en/articles/12512176-what-are-skills
- https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation

### E03 道具の数ではなく説明・境界・返却情報の質
Anthropic, *Writing effective tools for agents* (2025) は、ツールの命名空間、明確な境界、有用な戻り値、トークン効率、実エージェント評価を重視。OpenAI, *A practical guide to building agents* (2026-01-15) は、手順を具体的な操作へ対応させ、単一エージェントで十分なら複雑な構成を増やさないことを推奨。既存道具棚について、**自然文→候補発見→実取得→入力適合→実操作→実物検収**が通るかを測り、リンクや道具を増やすこと自体を成果としない。
一次資料：
- https://www.anthropic.com/research/writing-tools-for-agents
- https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/

### E04 「正しく答えた」より最終環境の完了状態
NVIDIA (2026-09-21), *How to Evaluate AI Agents: From Tool Calls to Task Completion* は、各ツール呼出しの正誤だけでなく、実行列と最終環境状態で結果を判定すべきと整理。Pan et al. (ICML 2026), *Measuring Agents in Production* は20ケースの面接・86名の実運用者調査により、実運用では簡素な構成と人手評価が多く、信頼性が主要課題だと報告。AD&Cの「Draftや書込宣言≠正本更新」「A/B/C独立」「implementation／operation／effect分離」に適合するが、これもAD&C固有効果の証明ではない。
一次資料：
- https://developer.nvidia.com/blog/how-to-evaluate-ai-agents-from-tool-calls-to-task-completion
- https://proceedings.mlr.press/v306/pan26a.html

### E05 承認摩擦の合理化と信頼境界
MCPのTool Annotationsでは \`readOnlyHint\`、\`destructiveHint\`、\`idempotentHint\`、\`openWorldHint\` がツール性質のヒントを提供する（仕様および維持者記事、2026-03-16）。ただし**自己申告のヒントは信頼済み権限確認・事前保全・競合検査の代替ではない**。AD&Cの「低リスク・可逆・承認済みなら完走」「真の新規承認境界だけ停止」は妥当な仮説。外部ツールが副作用や送信を行う場合は別途承認・実権限を検査する。
一次資料：
- https://modelcontextprotocol.io/specification/2025-11-25/server/tools
- https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/

## 3. 実装用ミニパッケージ（既存正本への追加規則は0件）

### 3.1 まず実施する2本の独立コールドスタート試験
**使うもの**：既存のQ1〜Q4合格基準、共有KB README／関連Skill、既存T005のPASS/FAIL/NOT_RUN形式。新たなテスト基盤を作らない。

| 試験 | 新規AIへ渡す自然な依頼 | 期待する実経路と合格対象 |
|---|---|---|
| CS-01 山歩き | 「奈良の屯鶴峯と近くの神社を初心者向け2時間で周りたい。車か電車で。」 | Q1：山歩きSkillの公開入口と版を特定／Q2：説明なしで正しく発見／Q3：Skill指定順序・安全条件・根拠を適用／Q4：使えるルート・交通・不明点を提示 |
| CS-02 3D実用品 | 「壁穴2つの寸法写真からペーパーホルダー用の角度付きスペーサーを作りたい。」 | Q1：3D実用品Draft Skillを特定しActiveと誤認しない／Q2：自然文で発見／Q3：現物寸法・穴位置・G2重ね合わせ検査を守る／Q4：実寸照合できるモデルと確認項目（生成不能なら正直に未実施） |

**試験条件**：一つの試験は独立した新規チャット／別AIの初見状態で行う。評価用のSkill名、正解ルート、採点条件は試験AIへ渡さない。接続・権限がない場合はQ2/Q3を架空PASSにせずNOT_RUN。私的原本と実在の個人情報は公開試験へ使わない。既存の別AI試験実行手段がなければ、試験入力と採点票だけ保存し、本人へ大量のチャット作成作業を依頼しない。

### 3.2 ケースごとの観測票（既存T005へそのまま添付できる）
1行を以下の形式で記録する。未実行は \`NOT_RUN\`、不合格は \`FAIL\`、対象外は \`N/A(理由)\`。結果の自己申告は証拠ではない。

\`\`\`text
case_id:
AI/モデル・版・日付・初期コンテキスト:
input_exact:
entry_source / entry_version / fetched_evidence:
Q1 正本存在: PASS/FAIL/NOT_RUN
Q2 自発発見: PASS/FAIL/NOT_RUN
Q3 必要順序・規則適用: PASS/FAIL/NOT_RUN
Q4 利用者が使える成果: PASS/FAIL/NOT_RUN
implementation 正本・参照・Git・読戻し: PASS/FAIL/NOT_RUN/N/A
operation 実利用または別AI受領: PASS/FAIL/NOT_RUN/N/A
effect 手戻り・時間・追加質問: 実測値または NOT_RUN
human_extra_actions / unnecessary_approval_count:
safety_boundary_violations:
blocking_reason / next_one_action:
\`\`\`

### 3.3 既存T005との結合：新規テスト体系を増やさない
- **内容・構造 A**：H01/G01/P01/U01の4件スモーク→既存20件。必要な所見・導線・画面起点・UI一貫性を採点。
- **表示・操作 B/C**：表示確認Bとクリップボード実操作Cを分け、実押下していないCはNOT_RUN。
- **完走のA/B/C比較**：同一の承認済み低リスク架空タスク群で、A=既存安全規則、B=出口チェック、C=短い道理＋出口チェック。差は完走率・不要承認・再指示・安全違反・実際の保存/読戻しから測る。**既存のB/C UI試験と名称が衝突するので、報告では「UI-A/B/C」と「完走条件A/B/C」を必ず分離表記**。
- **SEC-FMT01**：夜間秘書の「必要な質問が実際に出るか」は、既存の差分文面・検収を再利用。本報告では夜間タスクの本番設定を触らない。次回自然実行の実際の質問有無で判定。

## 4. 順番・検収・停止（リーダーがそのまま使える）

| 順 | 作業 | PASS条件 | 停止/切戻し |
|---|---|---|---|
| 1 | mainとDraftの対象版・現在の承認を取得 | 対象・版・未完が一致 | 版不一致は対象を止めて正本照合 |
| 2 | CS-01/CS-02を独立環境で1回ずつ実施 | Q1〜Q4を原文・実取得証拠付き判定 | 権限/入口不足ならNOT_RUN。捏造不可 |
| 3 | T005既存4件スモーク→効果比較 | 同条件・原文・分母、A/B/Cを分離 | 独立環境がなければ事前準備PASS／実施NOT_RUN |
| 4 | FAILの根因のみ局所修正 | 発見不足ならREADME/Skill入口、適用不足ならProfile、完走不足なら既存Exit行の**一箇所**に限り最小差分 | 既済文面の重複追加は禁止。変更前SHA／版・revert経路保持 |
| 5 | 再試験・リーダーへ検収 | 該当FAILが改善し副作用なし、実体読戻しPASS | 安全違反や手戻り増加なら局所revert |

**無修正でよい条件**：Q2〜Q4が成立しており、追加規則なしで目標に足りる場合。**新たな明示承認**が要る公開mainマージ、権限変更、実データ外部送信、不可逆更新は自動実行対象外。

### 判定閾値（新設しない）
既存T005試験票の初回回答A目標は介入側14/20（70%）、後続の別40件は28/40（70%）。同時に対照群との差を確認する。目標数達成だけで一般化・因果効果を主張しない。Q1〜Q4は各ケースを別々に判定し、静的Q1のPASSをQ2/Q3/Q4のPASSへ転用しない。

## 5. 研究側の完了とリーダーへの残作業

| 対象 | 現状 |
|---|---|
| 既存正本・Issue・Draft PR・研究設計の取得照合 | PASS |
| 外部一次知見の取得・用途限定評価 | PASS |
| 試験入力・採点欄・順序・停止条件の実装用設計 | PASS |
| この研究パッケージの永続保存・保存先からの読戻し | 書込後に検査して確定する |
| 独立AIコールドスタートCS-01/02 | NOT_RUN |
| T005比較・B/C実操作・人手負荷削減の実証 | NOT_RUN |
| 実装変更・本番夜間タスク変更 | 実施対象外（新規変更なし） |

**リーダーへ渡す単一判断**：追加の設計会議は不要。既存Q1〜Q4試験を採用し、証拠を得てから局所修正する。未実施試験はOPENのT005/T017に保持し、DONEにしない。現行P0のT014作業を妨げない範囲で実施する。

**WHY（判断理由）**：規則本文の不足を先に決め打ちすると、読まれない規則がさらに増える。外部文献は発見・文脈選択・道具品質・最終状態評価を支持するが、AD&C固有の効果はまだ実測されていないため。

**棄却する代案**：新しい共通ルール全文／常駐エージェント／独自評価DBの新設、既存Skillへの一括規則コピー、全チャットへの手動指示貼付、単一チャット内で正解を知るAIが自己採点する比較試験。

**引継ぎの完成判定**：本ファイルのGit保存・読戻しは送信側のPASS。リーダー自身による取得、理解、試験実施、効果実測はそれぞれ別ゲートのNOT_RUNとする。
