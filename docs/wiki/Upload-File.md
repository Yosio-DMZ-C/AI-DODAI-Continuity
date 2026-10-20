# AIへのファイルの送り方（ダウンロード・アップロード）

**AD&Cの設計書をダウンロードし、利用するAIのチャットにファイルとして送ってください。** GitHubのページを開いたり、リンクを送ったりしただけでは、AIが内容を読めるとは限りません。

1. [導入ガイドの「設計書を選ぶ」](Getting-Started.md#1-設計書を選ぶ)から、自分に合った設計書を開きます。迷ったら「AI無課金ユーザー版」を選びます。
2. GitHubの設計書ページで **［Download raw file］（下向き矢印の保存ボタン）** を選び、ファイル（通常は `.md`）を保存します。表示によっては［Raw］を開いて保存します。**Webページ（HTML）ではなく設計書本体**を保存してください。
3. 利用するAIのチャットで **［＋］または［添付］→［ファイル］** から保存した設計書を選び、**ファイル名が入力欄に表示されたら** `実行` と送ります。

※ChatGPTの画面を例にしています。Claude・Gemini・Grokなども**保存したファイルを添付する**のが目的です。ボタン名や使える形式はAI・端末・契約条件により異なります。次の動画は参考で、メーカー公式の操作保証ではありません。

## iPhone

Safariなどで設計書をダウンロードしたら、通常は**「ファイル」アプリ →「ブラウズ」→「ダウンロード」**から探せます。ChatGPTの入力欄にある **［＋］→［ファイル］** から保存した設計書を選びます。

[![iPhoneでChatGPTにファイルを添付する動画](https://img.youtube.com/vi/9IIcpTu4uvM/hqdefault.jpg)](https://www.youtube.com/watch?v=9IIcpTu4uvM)

[動画を見る：mrhackio／iPhoneアプリでの添付（2024年・英語／旧画面）](https://www.youtube.com/watch?v=9IIcpTu4uvM) · [Apple公式：ダウンロードしたファイルの場所](https://support.apple.com/ja-jp/102440)

## Android

ブラウザで設計書を保存したら、通常は**「Files」アプリ →「ダウンロード」**から探せます。ChatGPTの入力欄の **［＋］→［ファイル］** を選び、ファイル選択画面で「ダウンロード」を開きます。

[![AndroidでChatGPTにファイルを添付する動画](https://img.youtube.com/vi/Z-sZ4vxblZM/hqdefault.jpg)](https://www.youtube.com/watch?v=Z-sZ4vxblZM)

[動画を見る：How To Android／Androidでのファイル添付（2026年・英語）](https://www.youtube.com/watch?v=Z-sZ4vxblZM) · [Google公式：Androidでファイルを探す](https://support.google.com/android/answer/9110661?hl=ja)

## Windows PC

ブラウザで設計書を保存し、通常は**「ダウンロード」フォルダー**を開きます。AIのチャットで **［＋］／［添付］→［ファイル］** を選んで保存した設計書を指定します。対応するWeb画面なら、ファイルをチャットの入力欄へドラッグする方法もあります。

[![WindowsのブラウザでChatGPTにファイルを添付する動画](https://img.youtube.com/vi/BYtSLS181oE/hqdefault.jpg)](https://www.youtube.com/watch?v=BYtSLS181oE)

[動画を見る：インプレス「できるChatGPT 改訂2版」／ファイルのアップロード（2026年・日本語）](https://www.youtube.com/watch?v=BYtSLS181oE) · [動画提供元の説明ページ](https://dekiru.net/article/27621/)

## Mac

ブラウザで設計書をダウンロードし、通常はFinderの**「ダウンロード」**から探せます。ChatGPTのWeb画面で **［＋］／［添付］→［ファイル］** を選びます。Mac用アプリの場合は、アプリ内の追加・添付メニューからファイルを選びます。

[![Macを含むPCのChatGPTファイル添付を説明する動画](https://img.youtube.com/vi/nuKgAWabYzA/hqdefault.jpg)](https://www.youtube.com/watch?v=nuKgAWabYzA)

[動画を見る：How To Fix Guide／Macを含む複数端末向け解説（2026年・英語）](https://www.youtube.com/watch?v=nuKgAWabYzA) · [OpenAI公式：macOSの添付メニュー](https://help.openai.com/ja-jp/articles/9295241-chat-bar-%E3%81%AE%E8%B5%B7%E5%8B%95%E6%96%B9%E6%B3%95)

## うまく送れないとき

- **ファイルが見つからない**：上の端末別説明で「ダウンロード」を確認してください。「写真」ではなく「ファイル」から選びます。
- **`.md` が添付できない**：AIごとの対応形式を確認してください。設計書はテキストなので、必要なら**全文をチャットに貼り付ける**方法に切り替えます。**HTMLページをそのまま添付しない**でください。
- **［＋］や［添付］がない／エラーが出る**：何度も同じ操作を繰り返さず、AIに「ファイルを添付できません。今の画面から次に押す場所を一つ教えてください」と伝えてください。画面を送れるなら[画面の撮り方（動画あり）](https://github.com/Yosio-DMZ-C/AD-C-Shared-Knowledge/blob/main/docs/USER_TO_AI_FEEDBACK_GUIDE.md)も使えます。
- **添付した後**：ファイル名が表示されていても読み取り成功とは限りません。AIに読めたか確認してください。返信の内容を見てから次の操作に進みます。

**送信前の確認**：自分で付け足したパスワード・認証コード・個人情報・会社の機密などが含まれていないことを確認してください。

参考：[OpenAI公式：ファイルアップロード](https://help.openai.com/ja-jp/articles/8555545-uploading-files-and-audio-to-chatgpt)／[OpenAI Academy：ChatGPTでファイルを使う](https://openai.com/ja-JP/academy/working-with-files/)／[GitHub公式：Rawファイルのダウンロード](https://docs.github.com/en/repositories/working-with-files/using-files/viewing-and-understanding-files)

> **検証範囲（2026-10-20）**：公式説明と、リンク先動画の検索結果・掲載情報を照合した編集Draftです。**動画の全編再生、各端末での実ダウンロード／実添付／AIによる読取、画面の最新性はNOT_RUN**。特にiPhone動画は2024年の旧画面です。表示が違うときは利用者の現在の画面を優先します。
