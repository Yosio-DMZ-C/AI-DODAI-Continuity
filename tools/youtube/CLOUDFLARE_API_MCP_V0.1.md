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


## 2026-10-20 続報：ユーザー端末にChatGPT Desktopなし、Plus Web版での制約

- ユーザー確認：「ChatGPTデスクトップアプリはインストールしていない」。既存の個人プラグインは **Desktop only**。ブラウザの紫色カードを押してもWindowsアプリ起動画面になるだけ。**インストールを勝手に要求・実行しない**。
- [OpenAI公式：Plugins in ChatGPT](https://help.openai.com/en/articles/20001256-plugins-in-chatgpt) によると、`mcp.json` / `.mcp.json` を持つプラグインはリモートHTTPSでもDesktop-onlyになり得る。スキルだけ追加してもWeb実行可能にはならない。
- [OpenAI公式：Connecting custom MCP servers](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt)：ChatGPT Webの**フルMCPの書込機能はBusiness/Enterprise/Edu向け**。個人Plusで同じWeb接続・書込を自動化できると保証しない。
- [OpenAI公式：Sites hosting](https://help.openai.com/en/articles/20001547-hosting-a-plugin-with-chatgpt-sites)：ChatGPT SitesにMCPをホストしてWeb対応プラグインを作る経路がある。ただし[Sites作成](https://help.openai.com/en/articles/20001339-creating-and-using-chatgpt-sites)はWebの**Work**を必要とする。ユーザーは通常Workを避ける方針のため、本人の了承なく利用しない。またCloudflare APIへの実認証・接続保証はない。
- 暫定策：YouTube Worker・KV・EXPECTED_CHANNEL_IDは保全。Cloudflare管理の自動化は、**(1) ChatGPT Desktopを本人が導入して既存プラグイン接続試験、または (2) ブラウザから操作できる専用管理ページ/APIを別設計**の2案。後者はChatGPTから直接使えることを保証しない。追加実装の前に本人の優先順位を確認する。
- APIトークン／OAuth JSONはチャットへ送らせない。Workerで認証情報を扱う場合は最小スコープ、秘密保管、監査ログ、読み取り検証→承認付き書込を必須にする。

## 2026-10-20 モバイル対応調査・追加方針

- **ChatGPT公式モバイルアプリ**は iOS / Android とも利用可能。公式: https://chatgpt.com/download/ 、iOS: https://apps.apple.com/app/chatgpt/id6448311069 、Android: https://play.google.com/store/apps/details?id=com.openai.chatgpt 。
- **モバイルアプリがあることと、個人の「Desktop only」プラグインが動くことは別**。今回の `adnc-cloudflare-ops` はDesktop only表示であり、iOS/Android版でのMCP操作は未対応・未検証。OpenAI公式: https://help.openai.com/en/articles/20001256-plugins-in-chatgpt
- **カスタムMCP接続**はOpenAIの現行公式文書で「Can I connect custom MCP servers on mobile? No - web only」。しかもフルMCPは主にBusiness/Enterprise/Edu向け。個人Plus＋モバイルへの直接MCPプラグインは標準ルートとしない。公式: https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt
- **運用案（現時点）**：開発・管理者による初期構築はWindows ChatGPT Desktop＋公式Cloudflare MCPで実証（接続・権限確認は未了）。一般利用者向けAD&Cの動画アップロード／公開範囲選択／URL管理は、独立した**モバイル対応HTTPS管理画面（PWA化も検討）**を標準とする。iOS/Android/PCブラウザ共通の画面を提供し、ネイティブアプリ導入は必須にしない。既存 `videos.html` と `channel.html` を再利用する。
- 管理画面をモバイル対応にしただけでは、**ChatGPTチャットからの自動操作がモバイルで実現したことにはならない**。動画のチャット添付→YouTube直送は別実装・別試験であり、達成と主張しない。
- 将来ChatGPT/他AIのモバイルMCP対応が正式に確認できれば、アプリからの接続方式を追加する。変更の際は公式文書・利用者端末で検証してから標準化。


## 2026-10-20 実機試験 FAIL：Skillは読めるがMCPツール未公開

- **ユーザーによる実試験**：Windowsデスクトップ上のChatGPT/Codexで個人プラグイン「AD&C Cloudflare Ops」を選択。「今すぐ試す」でSkillを読み込んだが、Codexの最終応答は `Cloudflare公式MCPの search・execute・docs が利用できず、実環境の点検を実行できませんでした`。Worker/KV/変数は **NOT_RUN**。Cloudflare接続も未確認。変更はなし。
- プラグインのファイル読戻しにより、`.codex-plugin/plugin.json` の `mcpServers: './.mcp.json'`、`.mcp.json` の `cloudflare-api` URL `https://mcp.cloudflare.com/mcp` とOAuth指定は存在することを確認。**スキル読込と、MCPツールのランタイム登録は別**。OAuth未承認だけが原因とは断定しない。
- **独立した再現報告**： https://github.com/openai/codex/issues/34859 で、Windows Codex Desktopにおける「Skillは存在するがプラグインMCPが登録されない」「OAuth認証対象にサーバーがない」問題が記載されている。今回も類似現象。サーバーURLの誤りが原因と断定しない。
- **次の切分け：Codex本体へ直接MCP登録**。公式接続方法（https://learn.chatgpt.com/docs/extend/mcp）に従い、ChatGPTデスクトップの **Settings → MCP servers → Add server**。名前 `cloudflare-api`（既存プラグインMCPに登録されていないことを先に確認）、方式 **Streamable HTTP**、URL `https://mcp.cloudflare.com/mcp`。**保存→Restart→必要ならAuthenticate**。Cloudflare OAuthで必要最小限の権限を本人が承認する。/mcpまたはサーバーの状態表示で接続確認し、`search` の**読取のみ**を試す。登録済みなら二重登録せず「無効／要認証／実行不可」を確認する。
- 手動登録も不可なら**Codexのランタイム制約/不具合として切り分け**。プラグイン名変更や再作成を盲目的に繰り返さない。次の代替策（Cloudflare管理用Web UI等）は利用者に選択を求める。
- **安全**：Cloudflare Secret/API TokenやOAuth JSONの貼付禁止。APIへの書込・デプロイ・削除は実行しない。公式サーバーは検索から全Cloudflare APIを呼べるので、本人認証時の権限は必要最小限に制限する。成功と報告するにはAPIの実読取が必要。

## 2026-10-20 実機：Windows版ChatGPTの設定画面への入り口（ユーザーSS確認）

- **ユーザー提供SS1**：アプリ左下の本人アイコン → ドロップダウン内の **「設定」** を選択することで設定画面が開く。設定画面の左メニューを下にスクロールすると「コーディング」という見出しが現れる。
- **ユーザー提供SS2**：「コーディング」の下に **「接続」** が表示されている（周辺は「フック」「Codex Cloud」「コードレビュー」など）。**次に押すべき実画面の表示名は「接続」**。前回案内した Settings > MCP servers > Add server は、この利用者のアプリで実画面検証されていない名称。未確認の「MCP servers」メニューを存在すると断言しない。
- 「接続」を押した先がMCPサーバー管理なのか、一般の接続管理なのかは **NOT_RUN／次画面の確認待ち**。リンク・ボタン名・サーバー追加方法はその結果で調整。新規サーバー追加を急がず、既存 `cloudflare-api` の有無と状態を先に確認する。
- 概念整理（OpenAI公式 https://developers.openai.com/plugins/concepts/mcp-server）：**MCP（Model Context Protocol）** はAIクライアントと外部ツール/情報をつなぐ規格、**MCPサーバー**はAIにツール等を公開し、呼び出しを実行して結果を返す側。**Skill**はAIの手順・ルール、**プラグイン**はSkillと接続設定等のパッケージ。Skill読込PASSでもMCPツールの実接続PASSではない。
- 認証トークン／APIキー／OAuth JSONの送信禁止。本件は読み取り試験から再開し、書込み・デプロイ・削除は禁止のまま。

