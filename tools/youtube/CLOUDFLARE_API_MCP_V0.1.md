# AD&C Cloudflare API操作の自動化 v0.1（2026-10-20）

## 結論

**Cloudflare公式MCPを採用する。独自のCloudflare管理API Workerは作らない。**

- 公式案内: https://developers.cloudflare.com/agents/model-context-protocol/cloudflare/servers-for-cloudflare/
- 公式MCP: `https://mcp.cloudflare.com/mcp`
- AD&C個人用・非公開プラグイン: https://chatgpt.com/plugins/plugins_6ad74d4a0554819195527e649e082852
- v0.1プラグインの設定: `mcp.json` に公式URL＋OAuth CIMD優先（DCRフォールバック）。プラグインには秘匿APIトークンを含めない。
- 個人端末は `py` / `node` / `npm` のいずれも未検出（PowerShellスクリーンショット確認）。**管理用にこれらの追加インストールは要求しない。**

## 動作範囲・現段階

Cloudflare公式MCPの `search`、`execute`、`docs` を通じて、そのOAuth許可に応じWorkers、KV、Bindings、Secrets、設定、バージョンなどのAPIにアクセス可能。**ツールがAPIを実行できるか、承認後の内容を変更できるかは実機試験が必要**。

| テスト | 判定 |
|---|---|
| Cloudflare公式MCP公開資料の確認 | PASS（公開仕様） |
| ChatGPT個人用プラグイン v0.1の作成・ファイル読戻し | PASS |
| Cloudflare OAuth連携 | NOT_RUN（本人の同意待ち） |
| MCPを使ったWorker一覧取得 | NOT_RUN |
| 対象Worker設定とKVの取得・突合 | NOT_RUN |
| 変更操作 | NOT_RUN（明示的承認前） |

## 対象識別子（公開可能情報）

- 既存Worker: `adnc-youtube-private`
- Worker URL: `https://adnc-youtube-private.yosio-hasenaka.workers.dev`
- KV: `adnc-youtube-uploads`、Binding名 `UPLOADS_KV`
- YouTube投稿先: `UCrLzqKRdeNsCpSrHPQy8Ifg`
- その他AIそろばんWorkerは**変更しない**。

## 接続からの標準操作

1. ユーザーが [AD&C Cloudflare Ops](https://chatgpt.com/plugins/plugins_6ad74d4a0554819195527e649e082852) を開き、自分で接続を開始。CloudflareのOAuth画面で必要なアカウントと権限を選ぶ。
2. **CloudflareのAPIトークン・グローバルAPIキー・Google OAuth JSON・更新トークンはチャットに送信してはならない**。プラグインパッケージにも含めない。
3. 接続後、`search` / `execute` で対象Workerの存在・現設定・KV bindingを**読み取り専用で**確認。ユーザーの意図した識別子と突合する。
4. 変更内容を差分、影響、復元策とともに提示。書込、デプロイ、Secret更新、削除には別途明示承認を得る。
5. 承認後に最小差分適用。直後に再読込しPASS/FAIL/NOT_RUNを記録。タイムアウト時のPUT/POSTを無検証で再送しない。
6. 手順案内は画面へのリンクを添え、公式の英語UI名と日本語の説明を使う。SSが既にある場合は再送依頼しない。

## セキュリティ境界

このプラグインに同梱したSkillは**AIの運用方針**であり、Cloudflareの実際の権限を技術的には制限しない。OAuthの画面で最小権限を選ぶことが必須。Workerの更新なら対象Worker単位のEditor、KV新規作成は広いKV管理権限が必要となり得る。AIそろばん等の他Workerへの書込権限を可能な限り与えない。

プラグインの作成・登録だけでユーザーのCloudflareにアクセスできるわけではない。**接続済みのツールがChatGPTから呼べることを別途実証する。**

## Google OAuth／YouTubeとの境界

本ツールは**Cloudflareの設定操作を自動化するものであって、Google OAuthを代行するものではない**。YouTubeのGoogle Desktop OAuth初回認証は別課題。長期的にはWeb OAuthへ移して端末へのPython/Node導入を不要にする。既存のYouTube WorkerコードではDrive経由が実装されているが、Driveを必須としない方式は別途開発する。

## 再利用と展開

一般利用者にはCloudflare公式MCPの接続リンクを提供し、同梱SkillやAD&C個人KBで操作対象・承認方針を管理する。個人に固有のIDを一般向けテンプレートへハードコードしない。使用できる権限・接続UIが変われば公式手順を確認して更新する。

## 実機発見：個人用MCPプラグインのChatGPT Web利用制限（2026-10-20）

- 作成済み個人用 `AD&C Cloudflare Ops v0.1` の詳細画面には **「デスクトップアプリで開く」** と表示され、紫色の開始カードを押すと `ChatGPT を開いています` の**デスクトップアプリ起動ページ**へ遷移した。**Cloudflare OAuthへ進んだわけではない**。
- OpenAIの公式プラグイン資料は「Desktop only／デスクトップアプリで開く」と表示されたプラグインは**ChatGPT Webでは実行できない**と明記。根拠: https://help.openai.com/ja-jp/articles/20001256-plugins-in-chatgpt 、https://help.openai.com/ja-jp/articles/20001497-troubleshooting-plugins-and-apps-in-chatgpt
- **ユーザーの次の操作**: PCにChatGPTデスクトップアプリがある場合は `ChatGPTを開く` を選択。ブラウザ継続ではOAuth接続不能。デスクトップアプリ未導入なら `Windows向けをダウンロード` は**追加インストールを伴う**ため本人に導入意思を確認する。Python/Node/npmは依然不要。
- v0.1のChatGPTプラグイン作成はPASSだが**ブラウザからCloudflare OAuthや管理APIを実行できるという案内は誤り**。接続とAPIテストは未実施。ユーザーがデスクトップアプリを使わない場合は**ChatGPT Webから接続できる代替設計の検証が必要**であり、無検証のURLや新しいプラグイン作成で解決済みと扱わない。
- 操作案内で、紫色のカードの「→」をCloudflare接続画面と断定しない。実際にはデスクトップ起動だった（ユーザーのスクリーンショットで確認）。

