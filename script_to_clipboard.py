#!/usr/bin/env python3
"""
台本ファイルからセリフを抽出してクリップボードに連続コピーするツール

使い方:
    python script_to_clipboard.py コマ.txt --page 1    # Page 1のセリフをコピー
    python script_to_clipboard.py コマ.txt --list      # 全ページ一覧表示
"""

import argparse
import re
import subprocess
import time
import sys
from pathlib import Path


def parse_script(file_path: str) -> dict[int, list[str]]:
    """
    台本ファイルをパースしてページごとのセリフを抽出

    Args:
        file_path: 台本ファイルのパス

    Returns:
        {ページ番号: [セリフリスト]} の辞書
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pages = {}
    current_page = None

    # ページ区切りパターン: 【Page X】
    page_pattern = re.compile(r'【Page\s*(\d+)】')

    # セリフパターン: キャラ名「セリフ」、キャプション「〜」、モノローグ「〜」
    # 「」の中身のみを抽出
    dialogue_pattern = re.compile(r'(?:^|\s)(?:\S+)「([^」]+)」', re.MULTILINE)

    # ファイルを行ごとに処理
    lines = content.split('\n')

    for line in lines:
        # ページ区切りをチェック
        page_match = page_pattern.search(line)
        if page_match:
            current_page = int(page_match.group(1))
            if current_page not in pages:
                pages[current_page] = []
            continue

        # 現在のページがある場合、セリフを抽出
        if current_page is not None:
            # ト書き（）やコマ指定[]は無視
            if line.strip().startswith('（') or line.strip().startswith('['):
                continue

            # セリフを抽出: 「」の中身
            # キャラ名「セリフ」形式を検出
            match = re.search(r'.+「([^」]+)」', line)
            if match:
                dialogue = match.group(1)
                pages[current_page].append(dialogue)

    return pages


def copy_to_clipboard(text: str):
    """
    テキストをクリップボードにコピー（macOS用）

    Args:
        text: コピーするテキスト
    """
    process = subprocess.Popen(
        ['pbcopy'],
        stdin=subprocess.PIPE,
        env={'LANG': 'en_US.UTF-8'}
    )
    process.communicate(text.encode('utf-8'))


def list_pages(pages: dict[int, list[str]]):
    """
    全ページの一覧を表示

    Args:
        pages: ページごとのセリフ辞書
    """
    print("=" * 50)
    print("台本ページ一覧")
    print("=" * 50)

    for page_num in sorted(pages.keys()):
        dialogues = pages[page_num]
        print(f"\n【Page {page_num}】 ({len(dialogues)}セリフ)")
        for i, dialogue in enumerate(dialogues, 1):
            # 長いセリフは省略表示
            display = dialogue[:30] + "..." if len(dialogue) > 30 else dialogue
            print(f"  {i}. {display}")


def copy_page_dialogues(pages: dict[int, list[str]], page_num: int):
    """
    指定ページの全セリフを改行区切りでクリップボードにコピー

    Args:
        pages: ページごとのセリフ辞書
        page_num: 対象ページ番号
    """
    if page_num not in pages:
        print(f"エラー: Page {page_num} が見つかりません")
        print(f"利用可能なページ: {sorted(pages.keys())}")
        sys.exit(1)

    dialogues = pages[page_num]

    if not dialogues:
        print(f"Page {page_num} にセリフがありません")
        sys.exit(1)

    # 全セリフを空行区切りで連結
    all_text = '\n\n'.join(dialogues)
    copy_to_clipboard(all_text)

    print(f"【Page {page_num}】 {len(dialogues)}個のセリフをコピーしました")
    print("=" * 50)
    print(all_text)
    print("=" * 50)
    print("クリップボードにコピー完了！")


def main():
    parser = argparse.ArgumentParser(
        description='台本ファイルからセリフを抽出してクリップボードにコピー'
    )
    parser.add_argument('script_file', help='台本ファイル（コマ.txt）のパス')
    parser.add_argument('--page', '-p', type=int, help='抽出するページ番号')
    parser.add_argument('--list', '-l', action='store_true', help='全ページ一覧を表示')

    args = parser.parse_args()

    # ファイル存在確認
    script_path = Path(args.script_file)
    if not script_path.exists():
        print(f"エラー: ファイルが見つかりません: {args.script_file}")
        sys.exit(1)

    # 台本をパース
    pages = parse_script(str(script_path))

    if not pages:
        print("エラー: ページが見つかりません。台本フォーマットを確認してください")
        sys.exit(1)

    # 一覧表示モード
    if args.list:
        list_pages(pages)
        return

    # ページ指定がない場合はエラー
    if args.page is None:
        print("エラー: --page または --list を指定してください")
        parser.print_help()
        sys.exit(1)

    # 指定ページのセリフをコピー
    copy_page_dialogues(pages, args.page)


if __name__ == '__main__':
    main()
