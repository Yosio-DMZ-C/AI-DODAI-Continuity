#!/usr/bin/env python3
"""Build AD&C offline transfer kit. No network or third-party libraries."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = "docs/AgentOS-C_設計・構築運用指示書_一般配布版.md"
ZIP_NAME = "ADNC_Offline_Installer_Current.zip"
MARKDOWN_NAME = "ADNC_Offline_Installer_Current.md"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read(path: str) -> bytes:
    file = ROOT / path
    if not file.is_file():
        raise RuntimeError(f"Required file missing: {path}")
    return file.read_bytes()


def build(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    version = json.loads(read("docs/updates/LATEST.json"))["latest_version"]
    guide = read(PRIMARY).decode("utf-8")
    header = re.search(r"(?m)^- 配布版：(\d+\.\d+\.\d+)", guide)
    setup = re.findall(r"ADNC_INSTALLER_VERSION:\s*(\d+\.\d+\.\d+)", guide)
    if not header or header.group(1) != version or not setup or any(v != version for v in setup):
        raise RuntimeError(f"Version mismatch: latest={version}, header={header}, setup={setup}")

    sources = {
        "INSTALLER.md": PRIMARY,
        "PROJECT_EXECUTION_STANDARD.md": "docs/PROJECT_EXECUTION_STANDARD.md",
        "LATEST.json": "docs/updates/LATEST.json",
        "QUICKSTART.md": "QUICKSTART.md",
        "README.md": "README.md",
        "LICENSE": "LICENSE",
        "GETTING_STARTED.md": "docs/wiki/Getting-Started.md",
        "FILE_ATTACHMENT_GUIDE.md": "docs/wiki/Upload-File.md",
        "COMMUNICATION_PLAYBOOK.md": "vendor/shared-kb/skills/communication-navigation/SKILL.md",
        "LOOP_DEVELOPMENT_PLAYBOOK.md": "vendor/shared-kb/skills/loop-development/SKILL.md",
    }
    for source in sorted((ROOT / "docs/updates").glob("*.md")):
        sources[f"updates/{source.name}"] = source.relative_to(ROOT).as_posix()

    introduction = f"""# AD&C オフライン導入キット｜最初に読む資料

- 正式製品名：AD&C — AI-DODAI & Continuity
- コンセプト副題：AgentOS-C（AIをエージェントにするOS）
- 配布版：{version}
- 配布元：https://github.com/Yosio-DMZ-C/AI-DODAI-Continuity
- 用途：外部MarkdownをAIが直接取得できない環境での手動添付
- 注意：これは**導入資料**です。インストール済みの利用者KBでもバックアップでもありません。

## 使い方

1. このZIPをAIへ添付し、¤00_READ_ME_FIRST.md¤・¤MANIFEST.json¤・¤INSTALLER.md¤を読ませます。
2. AIがZIPの展開・内部読取に対応しなければ、同じ配布先の¤ADNC_Offline_Installer_Current.md¤を**単独添付**します。主要資料を1ファイルに結合した代替です。
3. AIは添付で実際に読めた文書を根拠にし、GitHub直接取得が失敗したことを**添付ファイルの失敗**へすり替えません。
4. 新規KBの手順は¤実行¤ → 保存先選択 → 接続・読書き確認 → 推奨案1件 → ¤進めて¤ → 構築・保存・読戻し。本人の承認前には書き込みません。
5. **既存KBには再インストールしません**。¤updates/UPDATE.md¤、既存版不明なら¤updates/ADOPT_LEGACY.md¤を参照します。
6. 通常応答の実動UI・「全文」指定・メモリよりKBを優先する判断が必要な時は、同梱¤COMMUNICATION_PLAYBOOK.md¤を参照します。改善・トラブル解消時は同梱¤LOOP_DEVELOPMENT_PLAYBOOK.md¤を参照します。

## 判定

- インストーラーは¤INSTALLER.md¤。§6.3.2〜§6.3.3の参照先は同梱¤PROJECT_EXECUTION_STANDARD.md¤です。外部再取得を通常の初期導入の完了要件にしません。
- 個人／組織固有の優先適用手順が¤未設定¤なら標準手順を使います。未設定のみを理由にFAILにしません。
- ¤LATEST.json¤は**同梱スナップショットの版**です。公開mainとの同一性は、外部照合できなければ¤NOT_RUN¤と区別します。
- ¤MANIFEST.json¤は各同梱ファイルのSHA-256を保持します。ZIP内を読めたことと、利用者KBの保存・読戻し成功は別判定です。
- §6.3.3の手順書**新規作成／重要改訂**用の検査を、通常初期導入へ無条件に強制しません。
- 共有KBの**標準コミュニケーションPlaybook／ループ方式Playbookの2本文だけ**を、取得時点のスナップショットとして同梱します。共有KB全体、他のオプションSkill、動画素材、個人ファイルは同梱しません。未取得を取得済みとみなしません。
- 組織の権限・セキュリティポリシーを迂回せず、許可された添付・保存経路だけを使用します。

## 制限環境での確認

**ZIP内部の全文読取**／**添付Markdown本文の読取**／**保存先書込み**／**保存後の読戻し**を別々に判定してください。
AgentOS-Cは旧名称の履歴と設計上の副題として残す呼称で、端末へ導入する実OSではありません。正式名・版数はAD&Cを用います。
""".replace("¤", chr(96))
    payloads = {"00_READ_ME_FIRST.md": introduction.encode("utf-8")}
    for target, source in sources.items():
        payloads[target] = read(source)

    parts = [
        f"# AD&C 制限環境用・単一Markdown導入資料（版 {version}）\n\n"
        "下記のBEGIN FILE〜END FILEごとに原本文書を区別してください。"
        "GitHubアクセスなしで読める添付資料です。\n\n"
    ]
    for name in ("00_READ_ME_FIRST.md", "INSTALLER.md", "PROJECT_EXECUTION_STANDARD.md",
                 "COMMUNICATION_PLAYBOOK.md", "LOOP_DEVELOPMENT_PLAYBOOK.md",
                 "LATEST.json", "QUICKSTART.md"):
        parts += [f"\n\n===== BEGIN FILE: {name} =====\n\n",
                  payloads[name].decode("utf-8"),
                  f"\n\n===== END FILE: {name} =====\n"]
    fallback_bytes = "".join(parts).encode("utf-8")
    payloads["ALL_IN_ONE.md"] = fallback_bytes

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        capture_output=True, text=True
    ).stdout.strip()
    shared_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT / "vendor/shared-kb", check=True,
        capture_output=True, text=True
    ).stdout.strip()
    manifest = {
        "shared_kb_source_repo": "Yosio-DMZ-C/AD-C-Shared-Knowledge",
        "shared_kb_source_commit": shared_commit,
        "schema_version": "1.0", "product": "AD&C",
        "subtitle": "AgentOS-C（AIをエージェントにするOS）",
        "package_type": "public-offline-installer-transport",
        "installer_version": version,
        "source_repo": "Yosio-DMZ-C/AI-DODAI-Continuity",
        "source_commit": commit,
        "not_an_installed_kb": True,
        "files": [
            {"path": name, "source": sources.get(name, "generated"),
             "bytes": len(data), "sha256": sha(data)}
            for name, data in sorted(payloads.items())
        ],
    }
    payloads["MANIFEST.json"] = (
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")

    zip_path = outdir / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for name, data in sorted(payloads.items()):
            entry = zipfile.ZipInfo(name, (2026, 11, 11, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    with zipfile.ZipFile(zip_path, "r") as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(payloads):
            raise RuntimeError("ZIP CRC / entry list mismatch")
        for entry in json.loads(archive.read("MANIFEST.json"))["files"]:
            data = archive.read(entry["path"])
            if sha(data) != entry["sha256"] or len(data) != entry["bytes"]:
                raise RuntimeError(f"ZIP SHA-256 mismatch: {entry['path']}")

    fallback_path = outdir / MARKDOWN_NAME
    fallback_path.write_bytes(fallback_bytes)
    if fallback_path.read_bytes() != payloads["ALL_IN_ONE.md"]:
        raise RuntimeError("Markdown fallback byte-level readback mismatch")
    print(json.dumps({
        "result": "PASS", "version": version, "commit": commit,
        "files": len(payloads),
        "zip": str(zip_path), "zip_sha256": sha(zip_path.read_bytes()),
        "fallback": str(fallback_path),
        "fallback_sha256": sha(fallback_path.read_bytes()),
    }, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=ROOT / "dist")
    build(parser.parse_args().outdir)
