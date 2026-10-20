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

## セキュリティ補足：デスクトップCodexのフルアクセス

- ユーザー提供のWindows版ChatGPT/Codexアプリの設定SSで、`一般 > 権限 > フルアクセス` が**ON**。画面の説明では、ローカルファイル編集とネットワーク使用のコマンドを承認なしで実行できるモード。**MCPサーバーのOAuth権限とは別の設定**。
- AD&C Cloudflare点検（読み取り専用、変更前に承認）では、フルアクセスを使う必要があるかを確認し、必要性がないなら**OFFを推奨**。ただしフルアクセスをOFFにしただけでCloudflare OAuthのAPI側書込権限が制限されるわけではない。
- 既存のユーザー設定を断りなく変更しない。変更するなら本人が現在の画面で判断する。

## 2026-10-20 実機訂正：Codex「接続」はMCP設定ではない

- ユーザーが Windows ChatGPT/Codex 設定画面「**コーディング → 接続**」を表示した。実画面は「このPCを操作」「他のデバイスを操作」「SSH」、「このPCを操作できるデバイス」「接続を許可」「このPCをスリープさせない」。**リモートPC操作用の設定であって、MCPサーバー追加ではない**。前回の案内「Settings → コーディング → 接続 → MCP server」は誤り。誤認による遠隔操作許可を有効化しない。
- **次の最小確認**：ユーザーの既出プラグイン詳細画面には `MCP サーバー 1 > Cloudflare-api` の右に歯車アイコンがある。この**MCPサーバー行の歯車を開き**、その内容が接続／認証／有効化の設定なのか確認。操作前には実画面が表示されるまで設定内容を憶測で言わない。プラグイン画面へのリンク: https://chatgpt.com/plugins/plugins_6ad74d4a0554819195527e649e082852
- **Codexの直接MCP登録の公式代替手段**: [OpenAI Developer Docs MCP](https://developers.openai.com/learn/docs-mcp) の記載で、Codex CLI/IDE拡張は `codex mcp add ... --url ...` またはユーザー個人設定 `~/.codex/config.toml` の `[mcp_servers.<name>] url = "..."` によりMCPを指定できる。Windows GUIで同じ設定が読まれるか／OAuth開始画面が出るかは未実機検証なので、プラグイン側の歯車を優先し、代替を行うなら確認とバックアップを先に取る。
- Windows側では `py`/`node`/`npm` コマンドが利用できないことは確認済みであり、それらをいきなり必須としない。Secretやトークンのチャット送信禁止、無断のデプロイ禁止を維持。

## 2026-10-20 実機訂正：Web版のプラグイン「…」とデスクトップ版MCP歯車

- ユーザーが開いた **Web版のプラグイン詳細**（右上に「デスクトップアプリで開く」と表示）にある **「…」** を押しても、メニューは **「プラグインのZIPファイルをダウンロード」「新しいバージョンをアップロード」「プラグインを削除」** の3項目。**OAuth・MCP接続操作ではない**。削除や更新を押さない。
- 以前提供された **Windowsデスクトップ版のプラグイン詳細** には `MCP サーバー 1 > Cloudflare-api` 行の**右端に歯車**が映っていた。まず **Web版から「デスクトップアプリで開く」→デスクトップ版プラグイン詳細の `Cloudflare-api` 行右端の歯車**を確認する。歯車の表示結果を見て初めて接続／OAuth設定と判断する。トップの三点リーダーと混同しない。
- 上記でMCPの管理操作が出なければ、公式Codex設定 `%USERPROFILE%\\.codex\\config.toml` の `[mcp_servers.cloudflare_api]\nurl = "https://mcp.cloudflare.com/mcp"` を**本人の許可と既存ファイルの確認・バックアップを前提に**代替試験。プラグイン同梱のMCP設定との二重登録に注意する。根拠: https://developers.openai.com/learn/docs-mcp と https://developers.openai.com/ja-JP/docs/config-file/config-reference 。OAuth連携が実際に走るかはこのユーザー端末では未検証。

## 2026-10-20 実機：MCPサーバー画面の発見

- ユーザーが**Windowsデスクトップ版の設定「MCP サーバー」画面**を表示。右タイトル「MCP サーバー／外部ツールとデータソースを接続する」、タブ「プラグイン 11」「アプリ 16」「MCP 1」、右側に **「＋ サーバーを追加する」**。
- セクション「サーバー」には `node_repl` だけが一覧表示（有効）。「プラグインから」に `code-review`、`codex_apps` は表示されるが `cloudflare-api` は見当たらない。**Cloudflare公式MCPはこの画面の一覧に未登録**、前回のCodexで `search`/`execute`/`docs` が使えなかった結果と整合。
- **次の正しい一手**は画面右の **「＋ サーバーを追加する」**。次ダイアログを確認して名前 `cloudflare-api`、公式URL `https://mcp.cloudflare.com/mcp` を入力する。入力UIの名前や認証方式は未確認なので、表示を見てから案内する。現時点でOAuth接続はNOT_RUN。
- 過去の誤案内（コーディング→接続＝MCP）は撤回済み。今回のサーバー一覧の所在・ナビゲーションはユーザーの実機画面から確認した範囲のみを記載する。
- プラグイン管理画面上にMCPの設定ファイルが存在することと、CodexのMCPサーバー一覧に実登録されることは別。登録後は読み取り専用でCloudflare Worker/KVを点検する。Secretやトークンをチャットへ送らせない。

## 2026-10-20 実機：Cloudflare MCPを手動登録後「認証する」表示

- **ユーザー提供SS（登録前）**：ChatGPT Windowsアプリの設定→MCPサーバー→「＋ サーバーを追加する」→「カスタム MCP に接続する」。名前 `cloudflare-api`、タイプ「ストリーミング可能な HTTP」、URL `https://mcp.cloudflare.com/mcp`。Bearerトークン環境変数／ヘッダー／環境変数からのヘッダーは未入力のまま「保存する」を実施。
- **ユーザー提供SS（登録後）**：MCPサーバー数が **1→2**、一覧に `cloudflare-api` と `node_repl` が表示され、`cloudflare-api` は有効化ON。「**認証する**」ボタンを確認。**手動登録はPASS**、OAuthはNOT_RUNであり接続可能かは未検証。
- **次の最小操作**：一覧の `cloudflare-api` 行にある「**認証する**」を押す。Cloudflareの認証画面が出たら本人にログインと要求権限を確認してもらう。最小権限の原則を守る。画面上のアクセストークン/APIキー/秘密情報はチャットに送付させない。サードパーティ偽装を避けるため認証画面のホストがCloudflare公式ドメインかを検査。
- **登録成功と接続成功を混同しない**。認証後にMCPの`search`/`execute`の実応答が得られて初めて接続PASSとし、Worker `adnc-youtube-private`、KV `adnc-youtube-uploads`、バインディング `UPLOADS_KV` の読み取り確認を順番に実施。
- 今回の手動MCP登録はプラグイン同梱 `.mcp.json` のランタイム認識不足を回避するための**Codex本体への独立登録**。SkillやCloudflareプラグインの構造そのものが直ったとは判定しない。将来の重複登録を確認する。


## 2026-10-20 実機：OAuth認証画面、Full access初期選択

- CodexのMCP画面で `cloudflare-api` の「認証する」を押したところ、ブラウザで**Cloudflare公式 `mcp.cloudflare.com/authorize`** の「Authorize application / Grant access to Cloudflare API」画面が表示された（本人のSS確認）。
- **Client ID** は `https://chatgpt.com/oauth/codex/client.json`、**Redirect URI** は `http://127.0.0.1:<一時ポート>/callback`。127.0.0.1は本人PCへのローカルリダイレクトであり、初回デスクトップOAuthの挙動として自然。ただし正規起動かの判断はユーザーが開始した手順・ホスト名・同意画面全体を照合する。
- 画面の **Base scopes** は `Minimal` / `Read only` / `Full access` の3択で、**Full accessが初期選択**されていた。読み取り専用の初期点検では**必ず`Read only`へ変更してから`Continue`**。Full accessのまま承認を誘導しない。Advancedは必要がない限り触らず、続く確認画面で利用アカウント・権限を再確認する。
- この画面が表示されたことで **OAuth認証フロー開始はPASS** だが **OAuth承認・MCP API実呼出・Worker/KV実読取はまだNOT_RUN**。承認前に接続済みやAPI実行済みと報告しない。
- Chromeの機械翻訳では「英語を常に翻訳」を有効化しない。技術画面で機械用文字列を書き換えないため、Cloudflareは英語UIのまま手順を案内する。
- OAuthのアドレスバーには `state` 等の一時パラメータが含まれることがあるので、スクリーンショットを共有するなら**URLバーは隠す**。トークン、client_secret、APIキーをチャットに送らせない。
- 現行公式根拠: [Cloudflare公式MCP](https://developers.cloudflare.com/agents/model-context-protocol/cloudflare/servers-for-cloudflare/) / [Cloudflare MCP OAuth](https://developers.cloudflare.com/agents/model-context-protocol/protocol/authorization/)。

## 2026-10-20 実機：OAuth最終同意画面が194権限

- 本人がCloudflare MCP OAuth 1段目の `Read only` を選び `Continue`。次にCloudflare公式の「Cloudflare MCP Server wants to access your account」同意画面が表示された。**`194 total permissions` が表示されており、`Authorize` はまだ押していない。**
- この画面では `REQUIRED`：`User Read`、`Background Access`、`ADDITIONAL ACCESS` の `Edit Permissions` が表示。カテゴリ例：`Account & Billing`（7件）、`Cloudflare One / Zero Trust`（36件）、`Analytics & Logs`（6件）、`Rules & Configuration`（17件）。**読み取り専用でも横断的な閲覧権限が多数要求される**ため、AD&C目的に対して過大の可能性。
- **手順**：`Authorize` を押さず `Edit Permissions` を開く。**Worker/Workers Scripts と Workers KVに必要な閲覧権限**を優先し、Billing、Zero Trust、Logs等の無関係な任意権限を除外できるか実画面で確認。必要なAPI権限名はエディタの原文で判断し、まだ見えていない権限ラベルは作らない。
- Cloudflare公式2026-08-22更新「[Choose OAuth scopes for Wrangler and the Cloudflare API MCP server](https://developers.cloudflare.com/changelog/post/2026-08-22-wrangler-mcp-optional-oauth-scopes/)」では、必須スコープを維持したまま、Optional scopesを個別編集可能と明記。足りない権限が必要になった際は再認可する。**最初から広い全権限を付与しない**。
- `Background Access` は必須として表示され、バックグラウンド利用に関わる権限を含む。現在の画面で除外不可なら、任意権限の限定と認可取り消し手順の確認を重視する。
- 続く実機検証は `Read only` + 限定Optional権限 → OAuth許可（本人が判断）→ `search`/`execute` を読取限定で確認。認可・実読取ができるまではMCP接続をPASS扱いしない。APIキー・一時認証コード・URLバー内のOAuthパラメータは共有しない。

## 2026-10-20 実機：Chrome DevToolsの貼付防止機能

- Cloudflare OAuthの追加権限は `194 total permissions` と非常に多い。ユーザーはブラウザコンソールによるDOMのチェック項目抽出を試すことにした。
- Chrome DevTools Consoleに黄色警告 `Don't paste code into the DevTools Console that you don't understand or haven't reviewed yourself ... Type 'allow pasting' below and press Enter to allow pasting.` が実際に表示された（本人SS）。**サイト権限やCloudflare OAuthではなくChromeのSelf-XSS防止の貼付制限**。
- 例外的に、提示したコードがユーザー自身で確認済みの場合のみ、Consoleに `allow pasting` を手入力して許可できる。**外部コードの安易な貼付やOAuth画面上での不明コード実行を標準化しない**。原則はCloudflare画面内の `Search scopes` / `Read only` / `Edit Permissions` による最小権限選択。抽出コードはDOM上のチェック項目と表示テキストだけを読むこと、外部送信がないことをレビューしてから使用。
- DevToolsで得られたラベルは折り畳み／仮想スクロールで不完全な可能性があり、権限の全件検証PASSとは扱わない。認証トークン／URLバーの一時コード／Cookieをログ出力したりチャットへ貼り付けない。Cloudflare Authorizeは権限が十分絞られるまで押さない。

## 2026-10-20 段階的権限方針：Read onlyで初回接続し書込前に限定

- 本人判断: `194 total permissions` のままでも `Read only` で**最初の接続試験を進める方針**。現在はCloudflare公式OAuthの `Edit Permissions` 画面。DevToolsのDOM抽出は40個のスイッチを取得したが194件の網羅ではなく、これ以上の全項目手調査は初期接続には不要と判断。
- **ただし承認前**に、初回OAuth画面で `Read only` を選択したこと、最終の同意項目に書込や危険な権限がないことをユーザーが確認する。 `Back to Review` → `Authorize`。 `Background Access` は必須権限として表示されており、読み取りでも広範囲の機微情報へのアクセスが可能な点を説明。
- **段階的な運用**：① Read onlyでOAuth接続・API実読取試験。② 設定を変える具体的な工程が確定した段階で、必要なリソースと書込APIのOAuthスコープに限定して**再認可**。③ 安定運用時に権限を精査して不要な範囲を取り消す。Read onlyは読み取り対象が狭い意味ではなく、広いアカウント横断参照を許す場合がある。
- `Full access` を無条件で選ばず、運用指示で「変更前に確認」と書くことはOAuth/APIレベルのアクセス制御にならないと明記。
- **2026-10-20時点でOAuth完了・MCPからのWorker/KV実読取は未確認**。次工程で実応答と承認スコープを確認してPASS/FAILを記録する。Secret値や認証コードは共有しない。
