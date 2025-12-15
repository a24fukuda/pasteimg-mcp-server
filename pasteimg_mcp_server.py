#!/usr/bin/env python3
"""
Pasteimg MCP Server
クリップボードから画像を受け取り、一時ディレクトリに保存するツール

使い方:
1. このスクリプトを実行
2. スクリーンショットをコピー（Win+Shift+S など）
3. 表示されたウィンドウにフォーカスを合わせてCtrl+V
4. 一時ディレクトリに保存され、パスをコピーできる
"""

import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageGrab, ImageTk


class PasteimgApp:
    def __init__(self):
        # 一時ディレクトリに保存
        self.temp_dir = Path(tempfile.gettempdir()) / "pasteimg"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.image_counter = 0
        self.saved_images: list[Path] = []
        self.preview_photos: list[ImageTk.PhotoImage] = []  # 参照保持用

        # メインウィンドウ
        self.root = tk.Tk()
        self.root.title("Pasteimg")
        self.root.geometry("500x500")
        self.root.minsize(400, 300)
        self.root.configure(bg="#2d2d2d")

        # 常に最前面に表示
        self.root.attributes("-topmost", True)

        # UI構築
        self._build_ui()

        # キーバインド
        self.root.bind("<Control-v>", self._on_paste)
        self.root.bind("<Command-v>", self._on_paste)  # macOS用

        # 終了時のクリーンアップを登録
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # スタイル設定
        style = ttk.Style()
        style.configure("TLabel", background="#2d2d2d", foreground="#ffffff")
        style.configure("TFrame", background="#2d2d2d")
        style.configure("Path.TLabel", background="#3d3d3d", foreground="#a0c4ff", padding=5)
        style.configure("PathHover.TLabel", background="#4d4d4d", foreground="#a0c4ff", padding=5)

        # ヘッダーフレーム
        header_frame = ttk.Frame(self.root, padding=(10, 10, 10, 5))
        header_frame.pack(fill=tk.X)

        # 説明ラベル
        label = ttk.Label(
            header_frame,
            text="Ctrl+V で画像を貼り付け",
            font=("", 12),
        )
        label.pack(side=tk.LEFT)

        # ステータスラベル
        self.status_label = ttk.Label(
            header_frame,
            text="",
            font=("", 9),
        )
        self.status_label.pack(side=tk.RIGHT)

        # スクロール可能なエリア (gridレイアウトで固定幅スクロールバー)
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=0, minsize=20)
        container.rowconfigure(0, weight=1)

        # Canvas + Scrollbar
        self.canvas = tk.Canvas(container, bg="#2d2d2d", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw"
        )

        self.canvas.configure(yscrollcommand=scrollbar.set)

        # キャンバス幅に合わせてフレーム幅を調整
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # マウスホイールでスクロール
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # 空の状態のメッセージ
        self.empty_label = ttk.Label(
            self.scrollable_frame,
            text="ここに画像がプレビューされます",
            anchor="center",
        )
        self.empty_label.pack(pady=50)

    def _on_canvas_configure(self, event):
        """キャンバスのリサイズ時にフレーム幅を調整"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """マウスホイールでスクロール（コンテンツがはみ出している場合のみ）"""
        if self.scrollable_frame.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_paste(self, event):
        """クリップボードから画像を取得して保存"""
        try:
            image = ImageGrab.grabclipboard()

            if image is None:
                self._update_status("クリップボードに画像がありません", error=True)
                return

            if not isinstance(image, Image.Image):
                # ファイルパスのリストの場合
                if isinstance(image, list) and image:
                    image = Image.open(image[0])
                else:
                    self._update_status("クリップボードの内容が画像ではありません", error=True)
                    return

            # 空メッセージを非表示
            if self.empty_label.winfo_exists():
                self.empty_label.destroy()

            # 連番ファイル名で保存
            self.image_counter += 1
            output_path = self.temp_dir / f"image_{self.image_counter:03d}.png"
            image.save(output_path, "PNG")
            self.saved_images.append(output_path)

            # 画像エントリを追加
            self._add_image_entry(image, output_path)

            self._update_status(f"保存しました ({self.image_counter}枚目)")

            # 最下部にスクロール
            self.root.after(50, lambda: self.canvas.yview_moveto(1.0))

        except Exception as e:
            self._update_status(f"エラー: {e}", error=True)

    def _add_image_entry(self, image: Image.Image, path: Path):
        """画像エントリをリストに追加"""
        # エントリフレーム
        entry_frame = ttk.Frame(self.scrollable_frame)
        entry_frame.pack(fill=tk.X, pady=(0, 10))

        # プレビュー画像
        max_width = 400
        max_height = 200

        ratio = min(max_width / image.width, max_height / image.height)
        if ratio < 1:
            new_size = (int(image.width * ratio), int(image.height * ratio))
            preview_image = image.resize(new_size, Image.Resampling.LANCZOS)
        else:
            preview_image = image

        photo = ImageTk.PhotoImage(preview_image)
        self.preview_photos.append(photo)  # 参照保持

        preview_label = ttk.Label(entry_frame, image=photo)
        preview_label.pack(pady=(5, 5))

        # パス表示ラベル（クリックでコピー）
        path_str = str(path)
        path_label = ttk.Label(
            entry_frame,
            text=path_str,
            style="Path.TLabel",
            font=("Consolas", 9),
            cursor="hand2",
        )
        path_label.pack(fill=tk.X, padx=5)

        # ツールチップ（全文表示）とホバーエフェクト
        self._create_tooltip(path_label, path_str)

        # クリックでコピー
        path_label.bind("<Button-1>", lambda e, p=path, lbl=path_label: self._copy_path(p, lbl))

    def _create_tooltip(self, widget, text: str):
        """ツールチップを作成"""
        tooltip = None

        def show_tooltip(event):
            nonlocal tooltip
            x, y, _, _ = widget.bbox("insert") if widget.bbox("insert") else (0, 0, 0, 0)
            x += widget.winfo_rootx() + 10
            y += widget.winfo_rooty() + widget.winfo_height() + 5

            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_attributes("-topmost", True)
            tooltip.wm_geometry(f"+{x}+{y}")

            label = tk.Label(
                tooltip,
                text=text,
                background="#ffffe0",
                foreground="#000000",
                relief="solid",
                borderwidth=1,
                font=("Consolas", 9),
                padx=5,
                pady=2,
            )
            label.pack()

        def hide_tooltip(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None

        widget.bind("<Enter>", lambda e: (show_tooltip(e), widget.configure(style="PathHover.TLabel")), add=True)
        widget.bind("<Leave>", lambda e: (hide_tooltip(e), widget.configure(style="Path.TLabel")), add=True)

    def _copy_path(self, path: Path, label: ttk.Label):
        """パスをコピーしてフィードバック表示"""
        self.root.clipboard_clear()
        self.root.clipboard_append(str(path))

        # 一時的に背景色を変えてコピー通知
        original_text = label.cget("text")
        label.configure(text="Copied!", style="Path.TLabel")
        self.root.after(500, lambda: label.configure(text=original_text))

    def _update_status(self, message: str, error: bool = False):
        """ステータスを更新"""
        self.status_label.configure(
            text=message,
            foreground="#ff6b6b" if error else "#69db7c",
        )
        print(f"[{'ERROR' if error else 'INFO'}] {message}")

    def _on_close(self):
        """アプリ終了時のクリーンアップ"""
        for path in self.saved_images:
            path.unlink(missing_ok=True)
        self.root.destroy()

    def run(self):
        """アプリケーションを実行"""
        print("Pasteimg MCP Server を起動しました")
        print(f"保存先: {self.temp_dir}")
        print("Ctrl+V で画像を貼り付けてください")
        self.root.mainloop()


def main():
    app = PasteimgApp()
    app.run()


if __name__ == "__main__":
    main()
