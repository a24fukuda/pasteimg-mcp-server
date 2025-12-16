# Pasteimg

クリップボードから画像を取得し、一時ディレクトリに保存するシンプルなツールです。

## 機能

- クリップボードから画像を貼り付け（Ctrl+V）
- 画像を一時ディレクトリに自動保存
- 保存したパスをワンクリックでコピー
- 画像の個別削除・一括削除
- 常に最前面に表示

## 必要環境

- Python 3.12以上
- Windows / macOS

## インストール

```bash
git clone https://github.com/a24fukuda/pasteimg-mcp-server.git
cd pasteimg-mcp-server
```

### uv を使用する場合（推奨）

```bash
uv sync
```

### pip を使用する場合

```bash
pip install -e .
```

## 使い方

```bash
# uv を使用する場合
uv run pasteimg

# pip でインストールした場合
pasteimg
```

1. アプリを起動
2. スクリーンショットをコピー（Win+Shift+S など）
3. アプリのウィンドウにフォーカスを合わせて Ctrl+V
4. パスをクリックしてコピー

## ビルド（Windows向け実行ファイル作成）

```bash
# ビルド
.\scripts\build.bat

# 成果物のクリーンアップ
.\scripts\clean.bat
```

ビルド後、`dist\Pasteimg.exe` が生成されます。

## 開発

```bash
# 型チェック
uv run pyright

# リンター
uv run ruff check
```

## ライセンス

MIT License
