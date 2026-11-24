# 第6回 解答

## 演習

- STEP 1 のツールの名前：
  - 従来のエージェント：search_materials
  - MCPエージェント：glossary_search_glossary

- STEP 2 の [tool call]：
  [tool call]   glossary_search_glossary({'query': '3レベル'})

- STEP 3 の [tool call]：
  [tool call]   fetch_fetch({'url': 'https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro.md'})
  [tool call]   glossary_search_glossary({'query': 'MCP'})

- STEP 4 の [tool call]：
  [tool call]   aws_aws___search_documentation({'search_phrase': 'Amazon S3 versioning overview'})

- 気づき・疑問：
  - MCPを利用すると、エージェント本体のコードを変更せずに、設定ファイルにサーバーを追加することで利用可能なツールを増やせる。
  - glossaryとfetchはCodespaces内で起動するMCPサーバーである。一方、AWSは外部で動作しているMCPサーバーにURLで接続する。
  - ツールの選択と引数の決定はLLMが行い、実際の処理はMCPサーバー側で実行される。
  - fetchでは一時的なHTTP通信エラーとGeminiの503エラーが発生したが、URLを直接指定して再実行すると正常に動作した。
  - AWS検索では、LLMが日本語の質問から英語の検索語を作成して検索ツールを呼び出した。

## 宿題

- 取り組んだレベル：基礎・実装・発展

- やったこと：
  - 第3回のlec03ブランチで作成したmake_quizをapp/tools.pyに移植した。
  - make_quizをMCPサーバーに登録し、glossary_make_quizとして公開した。
  - あわせてget_lecture_summaryもMCPツールとして公開した。
  - 用語が存在しない講義回を指定された場合、利用可能な講義回を案内するように改善した。
  - GeminiからMCP経由で正常入力と異常入力を試し、--traceで確認した。

- 結果：
  - MCPツール数は7個から9個に増加した。
  - 正常入力：第2回を指定し、「過学習」の確認問題と正解を生成できた。
  - [tool call] glossary_make_quiz({'lecture': 2})
  - 異常入力：第99回を指定すると、用語が登録されていないことと利用可能な回を案内した。
  - [tool call] glossary_make_quiz({'lecture': 99})
  - Geminiは架空の問題を生成せず、ツールの返り値に基づいて説明した。
  - uv run pytest -q の結果：21 passed in 4.50s。

- 気づき・疑問：
  - MCPを使うと既存のPython関数を大きく書き直さずに外部公開できる。
  - 従来はエージェントが関数を直接実行していたが、MCP方式ではサーバーを経由して実行する。
  - ツール側で入力を検証し、エラー時に明確な情報を返すことが重要である。
  - 今回の異常入力では例外を発生させず、説明文を正常な返り値として返した。
  - 今後は入力チェックをより厳密にし、LLMによる回答の正確性も評価したい。

### 基礎課題（追加検証）：get_lecture_summaryのMCP公開

- `app/mcp_server.py` に `server.tool()(tools.get_lecture_summary)` を登録した。
- MCPツール一覧で `glossary_get_lecture_summary` が公開されていることを確認した。
- `uv run python -m app.mcp_agent --trace "第2回では何を学びますか？"` を実行した。
- `[tool call] glossary_get_lecture_summary({'lecture': 2})` を確認した。
- `[tool return]` に第2回「ファインチューニングとLoRA」の講義要点が返った。
- Geminiは取得内容を使い、日本語で第2回の学習内容を説明した。
- 実行時のモデル応答は2回、入力6,108トークン、出力255トークンだった。

#### 考察

既存のPython関数をMCPサーバーに登録すると、
エージェント本体を変更せずに新しいツールを利用できることを確認した。
`--trace` により、LLMのツール選択、引数、実行結果を確認できた。

### 発展課題（追加調査）：VS CodeのMCP設定

- 調査日：2026年11月24日
- 調査対象：VS CodeのMCP設定とAgent Host向け設定
- 公式資料：https://code.visualstudio.com/docs/agents/reference/mcp-configuration

#### 調べた設定方法

1. 設定場所
   - VS Codeのワークスペース設定：`.vscode/mcp.json`
   - VS Codeのユーザー設定：ユーザープロファイル内の `mcp.json`
   - Agent Hostが直接読み込む設定：ワークスペースの `.mcp.json`
     または `~/.copilot/mcp-config.json`
2. コマンドによる起動
   - VS Codeでは `servers` 内に `type: "stdio"`、
     `command`、`args` を指定する。
3. URLによる接続
   - `type: "http"` と `url` を指定する。
4. 有効範囲
   - ワークスペース設定はそのプロジェクト用。
   - ユーザー設定は複数のワークスペースで利用できる。
   - Agent Host向けの設定はVS Code標準の設定と保存場所が異なる。

#### 演習の設定との比較

演習の `app/mcp_servers.json` は、
Python製エージェントが独自に読み込む設定ファイルであり、
サーバー定義に `mcpServers` を使用する。

一方、VS Codeの `.vscode/mcp.json` は、
サーバー定義に `servers` を使用する。

演習ではローカルサーバーを `command` と `args`、
リモートサーバーを `url` で指定した。

VS Codeではこれらに加えて、接続方式を表す
`type: "stdio"` または `type: "http"` を明示する。

#### 気づき・考察

MCPはツールとの接続方式を共通化する仕組みだが、
設定ファイルの保存場所やJSONの構造まで統一するものではない。

同じMCPサーバーでも、利用するクライアントに応じた
設定が必要になることを理解した。

今回は公式ドキュメントを調査・比較した。
VS Codeからの実際の接続試験は行っていない。
