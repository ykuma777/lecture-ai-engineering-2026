"""第1回: 素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする
    uv run python -m app.ask --chat     # 会話モード

ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors
from google.genai.types import GenerateContentResponse

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def print_token_usage(response: GenerateContentResponse) -> None:
    usage = response.usage_metadata
    if usage is not None:
        print(f"[入力トークン数] {usage.prompt_token_count}")
        print(f"[出力トークン数] {usage.candidates_token_count}")
    else:
        print("[トークン使用量] 取得できませんでした")


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    start = time.perf_counter()
    response = client.models.generate_content(model=MODEL, contents=question)
    elapsed = time.perf_counter() - start
    print(f"[API応答時間] {elapsed:.3f} 秒")
    print_token_usage(response)
    return response.text


def chat() -> None:
    client = genai.Client(api_key=get_api_key())
    chat_session = client.chats.create(model=MODEL)

    print("会話モードです。終了するには exit または quit を入力してください。")
    while True:
        question = input("質問> ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            return

        start = time.perf_counter()
        response = chat_session.send_message(question)
        elapsed = time.perf_counter() - start
        print(f"[API応答時間] {elapsed:.3f} 秒")
        print_token_usage(response)
        print(response.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--chat", action="store_true", help="会話モードで質問する")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    try:
        if args.chat:
            chat()
        else:
            question = DEFAULT_QUESTION if args.question is None else args.question
            print(f"[質問] {question}\n")
            print(ask(question))
    except (EOFError, KeyboardInterrupt):
        print()
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
