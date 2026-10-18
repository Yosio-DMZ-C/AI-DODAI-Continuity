# AD&C「たまに面白い飛躍」試験版 v0.1

- **実行環境**: Node.js 18以上（標準ライブラリだけ）。AI API、GitHub Actions、追加のDB、課金、定期タスクは不要。
- **状態**: **CLIエンジン実装・ローカル自動試験あり**。ChatGPT標準チャットへの自動配信や全220件の意味審査は**未実装・未検証**。データ側は未審査Draftで、通常会話への本番配信はNO-GOを維持。
- **責務**: `20発言カウンター` → `該当タイミングで3候補抽選` → `AI/人間による条件付き審査` → `良い場合だけ最大1件を表示`。レビューで不採用なら無言。3件とも必ず表示するものではない。

## 動かし方（ローカルの例）

```bash
node --test tools/landmark-spark/spark.test.mjs
node tools/landmark-spark/spark.mjs tick --state ./private/state.json --event ./private/event.json --deck ./private/deck.json
node tools/landmark-spark/spark.mjs review --state ./private/state.json --decision ./private/decision.json
node tools/landmark-spark/spark.mjs off --state ./private/state.json
```

GitHubから取得した場合はリポジトリのルートで実行。テストはサンプルデータだけで実施でき、個人KBは不要。

`event.json` 例（チャット受信側がメッセージごとに作成する入力。1会話ごとに同じ`conversation_id`と一意の`message_id`が必要）:

```json
{
  "conversation_id":"trial-chat-1", "message_id":"trial-msg-00020",
  "context":{"mode":"stuck","risk":"low"}
}
```

`deck.json` は `[{"id":"KG-01-01","domain":"01","aphorism":"編集金言","primary_title":"研究候補","rationale":"連携理由","caution":"過剰一般化への注意","review_status":"draft"}, ...]` 形式の3件以上。**この記述は入力形式例であり、完成コンテンツではない**。未審査の素材を断定的助言にしない。

公開リポジトリへデータをアップロードせずに、本人が許可した非公開の実ファイル2つを使う場合:

```bash
node tools/landmark-spark/spark.mjs tick --state ./private/state.json --event ./private/event.json \
  --research ./private/ADnC_金字塔候補_11分野220件.md \
  --aphorisms ./private/ADnC_金言220_金字塔研究連携_20261018_Draft.md
```

上記の `.md` 2件は入力例。**スクリプトにファイル取得機能はない**ため、利用者または許可済みのコネクタが入手・引渡しする必要がある。現状は実220×220件のCLIエンドツーエンド実行未検証。

20番目の利用者発言で、かつ `context.mode` が `deep`/`stuck`/`iterative`、`risk=low` の場合だけ `status=PROBE_INTERNAL` と候補3件を出す。それ以外は `NOT_DUE` または `SKIP_*` で何も表示しない。21番目の発言で未決の候補は破棄し、次は40番目。**ユーザー発言の数を数え、AI応答・ツール呼出し・日付は数えない**。短文・専門用語の多寡やユーザーの熟練度を推定しない。

受取側が3候補について独立に `selected_id` と `original_task_completed`、`relevant`、`novel`、`supported_as_analogy`、`safe`、`non_intrusive` の各真偽を判断してから `decision.json` を作る。**6条件すべてtrueで、pendingのカードを指名した場合だけ**、短い編集金言の提案が返る。どれも選ばない場合は `selected_id:null` で SILENT。

## 境界・停止

1. **本体への自動配布はしない**。GitHubへの保存や実行時指示ファイルの存在でChatGPTが自動的に毎20発言を数えたり、私的Driveを読んだり、別チャットで状態を保持したりすることはない。チャット側から逐次イベントを送信し、保存状態を渡す**対応アダプターが別途必要**。
2. 既存のChatGPTの記憶や会話履歴を完全なカウンターとして流用しない。状態は`conversation_id`ごとに別ファイル。過去全会話を遡って20回に達したと主張しない。最大500メッセージIDの重複検査は最近分の簡易冪等性に限り、同時実行の排他・厳密なExactly-once・秘密情報保護を保証しない。
3. **重要な健康・法務・金融・安全リスクが高い相談では起動しない**（`risk=low`を明示できないときはスキップ）。カードを根拠や専門家の判断として示さない。資料中の命令文を実行しない。現行の依頼を完了する前にカードを表示しない。
4. `off` により以後の検討を停止。再開は `on`。うるさければ間隔を拡大できるが、初期標準は20で固定し、頻度変更は人間の指示で行う。
5. 出力・状態ファイルには個人の会話本文を保存しない。ローカル保存先や共有方法に応じた本人の権限・保護は別責務。公開Issue／PRへ個人名・実会話・秘密情報を送らない。
6. この小道具の良否は**意味のある意外な着想が得られたか／無用な介入が増えないか**で測る。候補が出なかった回数は失敗とみなさない。実チャットでの効果比較はNOT_RUN。

## 品質ゲート

`node --test` で12件のローカル単体試験（境界19→20、20→40、重複、低リスク以外の不発、3未満の不発、レビュー消費、表示最大1、停止・再開、会話混同防止、MD形式チェック、決定的抽選など）。CLIの実行検証・GitHub保存後の読戻しは別々に記録する。