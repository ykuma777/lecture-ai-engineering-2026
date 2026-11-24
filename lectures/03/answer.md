# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：第1回はLLMが主に学習済みの知識から回答した。第3回では、LLMが外部の用語集検索ツールを呼び出し、取得した定義や講義回の情報を利用して回答できるようになった。今回の実験ではLoRAとQLoRAについて用語集を検索し、回答に利用した。回答の品質が常に向上するとは限らないが、参照情報を確認できる点が異なる。
- `--trace` で見えたツール呼び出し（ツール名と引数）：LoRAとQLoRAの比較質問では `search_glossary({"query": "LoRA"})` と `search_glossary({"query": "QLoRA"})` の2回が記録された。確認問題の質問では `make_quiz({"lecture": 2})` の1回が記録された。
- 1つの質問での LLM 呼び出し回数（`requests`）：LoRAとQLoRAの比較質問は2回、確認問題の質問も2回だった。これはツール呼び出し回数とは別の指標である。
- 追加したツールと、docstring に書いた説明：`make_quiz(lecture: int)` を `app/tools.py` に実装し、`app/agent.py` に登録した。docstringには、指定回の用語から確認問題と答えを返し、「第2回の確認問題を出して」などの復習依頼に使用することを記載した。

## 宿題

### 基礎：INSTRUCTIONSとdocstringの比較

- 取り組んだレベル：基礎・実装・発展A（Google ADK）・発展B（Pi）。すべて実施済み。
- 使用モデル：gemini-3.5-flash-lite
- 質問：「LoRA と QLoRA の違いは？」

#### やったこと

1. 変更前の動作を `--trace` で記録した。
2. 実験A：INSTRUCTIONSから用語集検索を必須とする指示を削除した。
3. 実験B：search_glossaryのdocstringを、複数用語をまとめて指定する説明に変更した。
4. 変更前後のツール呼び出しと回答を比較し、各実験後に変更を復元した。

#### 結果

| 項目 | 変更前 | 実験A | 実験B |
|---|---:|---:|---:|
| search_glossary呼び出し | 2 | 2 | 1 |
| LLM呼び出し | 2 | 2 | 2 |
| 入力トークン | 1350 | 1302 | 1066 |
| 出力トークン | 179 | 188 | 188 |

- 変更前と実験Aでは、LoRAとQLoRAを別々のqueryで検索した。
- 実験Bでは、`query='LoRAとQLoRA'` の1回の検索になった。
- Python関数を直接実行し、まとめた検索語からLoRAとQLoRAの2件が取得できることを確認した。
- 実験終了後のpytestは11件すべて成功した。
- ログ：`lectures/03/results/basic_A_before.txt`、`basic_A_after_01.txt`、`basic_B_after_01.txt`

#### 気づき・疑問

- INSTRUCTIONSの検索必須指示を削除しても、今回の質問では検索回数が変わらなかった。ツールのdocstringもLLMの判断に影響した可能性がある。
- docstringだけの変更で、ツールの呼び出し回数と引数が変わった。
- 呼び出し回数の削減と検索品質の維持は別々に評価する必要がある。
- LLMの出力は揺らぐため、一般化するには複数回の実験が必要である。

### 実装：承認付き学習ログ保存ツール

- 取り組んだレベル：実装（完了）
- 使用モデル：gemini-3.5-flash-lite

#### やったこと

1. app/tools.py に save_learning_log(topic, content) を実装した。
2. 学習内容を learning_log/ にMarkdown形式で保存するようにした。
3. app/agent.py に requires_approval=True を付けて登録した。
4. output_type に DeferredToolRequests を追加した。
5. CLIで承認（y）・拒否（n）を受け付け、DeferredToolResults で処理を再開する機能を実装した。
6. 保存拒否と保存承認の両方を実際に検証した。

#### 結果

| 項目 | 拒否テスト | 承認テスト |
|---|---|---|
| 保存要求 | 発生 | 発生 |
| 承認待ち | あり | あり |
| 利用者の入力 | N | y |
| ツールの処理結果 | 拒否 | 実行成功 |
| 保存後ファイル数 | 0件 | 1件 |
| 判定 | PASS | PASS |

承認テストで作成されたファイル：
learning_log/20261102T160954393070Z_c60bab39.md

保存内容：
- テーマ：LoRA学習メモ
- 内容：LoRAは事前学習済みの重みを固定し、低ランク行列を学習する手法です。

既存の自動テストは11件すべて成功した。

#### 気づき・疑問

- LLMがツールの呼び出しを要求しても、Python関数が直ちに実行されるわけではない。
- requires_approval=True により、Pydantic AIが承認まで実行を保留できる。
- 拒否された場合、ファイルが作成されないことを確認した。
- LLMへの指示だけでなく、プログラム側で承認を強制することが重要である。
- 保存が成功しても、LLMの付随説明には誤りがあり得る。今回、LoRAに関連する回を第5回と回答したが、正しくは第2回である。
- この承認機構はエージェント経由の呼び出しに適用される。Python関数を直接実行する場合の権限制御とは別に考える必要がある。

### 発展A：Google ADKによるエージェントの再構築

#### やったこと

1. adk_agent/glossary_agent/agent.py と __init__.py を作成した。
2. Google ADKのAgentを使い、既存のモデル・指示文・Pythonツール関数を再利用した。
3. search_glossary、get_lecture_summary、make_quiz の3つを登録した。
4. Gemini APIを利用し、Pydantic AI版と同じ質問で動作確認した。
5. ADKのセッション履歴をJSONで保存し、ツール呼び出しを解析した。

#### 結果

- 使用モデル：gemini-3.5-flash-lite
- 質問「LoRAとQLoRAの違いは？」：正常回答。search_glossaryを2回実行。
- 質問「第2回の内容から確認問題を1問出して」：正常出題。make_quizを1回実行。
- セッション内イベント数：8
- ツール呼び出し合計：3回
- ツール実行結果合計：3回
- Pydantic AI版でも同じ質問でsearch_glossaryを2回、make_quizを1回使用していた。
- 解析ログ：lectures/03/results/adk_tool_calls.txt

#### 気づき・考察

- エージェントのフレームワークが異なっても、既存のPythonツール関数を再利用できた。
- Pydantic AIはtool_plain()、Google ADKはtools=[...]でツールを登録する。
- 回答内容だけではツールを使ったか判断できない。実際の呼び出し履歴を確認することが重要である。
- 今回は両フレームワークでツール呼び出し回数が一致したが、一般化するには複数回の比較が必要である。
- ADKのイベント数とLLMの呼び出し回数は同じではない。
- 今回のADK版は保存承認ツールを登録しておらず、Pydantic AI版と機能が完全に同一ではない。

### 発展B：Piによるコーディングエージェントの実験

#### やったこと

1. CodespacesにPi 1.5.0をインストールした。
2. リポジトリ外の /tmp/aie2026_pi_lab を実験用フォルダにした。
3. 最初のモデル gemini-3.1-pro-preview ではAPIの429エラーが発生した。
4. gemini-3.5-flash-lite に変更し、実験を再実行した。
5. PiにPythonファイルの作成と実行を自然言語で依頼した。
6. Piの公開システムプロンプトと、自作エージェントのINSTRUCTIONSを比較した。

#### 結果

- Piのバージョン：1.5.0
- 成功時のモデル：gemini-3.5-flash-lite
- 作業フォルダ：/tmp/aie2026_pi_lab
- Piがwriteツールで pi_demo.py を作成した。
- 作成コード：print("Pi tool test OK")
- Piがbashツールで python3 pi_demo.py を実行した。
- 実行結果：Pi tool test OK
- Pi終了後、別のターミナルからファイルの存在、内容、実行結果を検証し、すべて成功した。
- 検証ログ：lectures/03/results/pi_demo_verify.txt

#### システムプロンプトの比較

参照先：
https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/system-prompt.ts

取得した公開ソースには、以下の特徴があった。

- 標準ツールとして read、bash、edit、write が指定されている。
- 回答を簡潔にするルールがある。
- ファイルを扱う際にはパスを明確に示すルールがある。
- プロジェクトの文脈、Skills、作業ディレクトリなどをプロンプトに組み込む仕組みがある。

自作エージェントのINSTRUCTIONSは、AIエンジニアリング講座の学習支援に特化し、用語集検索、講義要約、回答方法などを指定している。

一方、Piはコーディング作業を目的としており、汎用的なファイル操作・コマンド実行ツールを利用できる。

なお、比較した公開ソースはGitHubのmainブランチであり、インストールしたPi 1.5.0と完全に同一の実装であることまでは検証していない。

#### 気づき・考察

- エージェントの能力はLLM単体ではなく、システムプロンプト、ツール、実行環境の組み合わせによって決まる。
- Piは専用のPython関数を追加しなくても、汎用ツールを組み合わせてプログラムを作成・実行できた。
- 自作のPydantic AIエージェントは、保存前に人間の承認を必要とする仕組みを実装した。
- 今回のPi実験では、ファイル作成とbash実行が個別の承認なしに行われた。
- 汎用ツールは柔軟だが、ファイル編集やコマンド実行の権限管理が重要である。
- 今回の作業フォルダの分離は誤操作を減らすための対策であり、厳密なサンドボックスによるアクセス制限ではない。
