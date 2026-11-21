#!/usr/bin/env python3
"""Legacy entrypoint; v0.3 uses setup_once.py so refresh tokens are never printed."""
if __name__ == "__main__":
    print("この旧コマンドは無効化しました。認証情報の画面表示を避けるため setup_once.py を使ってください。")
    print("python setup_once.py で事前確認、手順書は INITIAL_AUTH_GUIDE.md")
    raise SystemExit(2)