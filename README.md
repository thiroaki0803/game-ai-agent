#  Game AI Agent
## 概要
ゲーム用のチャットボットエージェントを実行するAPI  
ローカルの開発では、基本的にはollamaという、ローカル実行可能なLLMサービスでAPIを立ち上げて任意のモデルで実行させている。  
OpenAIのAPIを使って、実行させることも可能。
## 構成
### 想定しているシーケンス
```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant LLM as LLM (OpenAI or Ollama)

    Client->>FastAPI: WebSocket接続
    activate FastAPI
    FastAPI-->>Client: 接続確立
    
    Client->>FastAPI: ゲーム開始リクエスト
    FastAPI->>LLM: ゲーム設定生成要求
    LLM-->>FastAPI: ゲーム設定
    FastAPI-->>Client: ゲーム開始・初期設定送信
    
    loop メッセージ処理
        Client->>FastAPI: メッセージ送信
        FastAPI->>LLM: メッセージ処理要求
        LLM-->>FastAPI: 生成結果
        FastAPI-->>Client: 処理結果返却
    end
    
    Client->>FastAPI: ゲーム回答送信
    FastAPI->>FastAPI: 正誤判定
    FastAPI-->>Client: 判定結果返却
    
    Client->>FastAPI: 切断
    deactivate FastAPI
```
## 開発環境の構築
### 前提条件
- docker がインストールされていること
- メモリが16GB以上はあること
    - ない場合は、OpenAIのAPIで実行するようにしてください
- "C:\Users\[ユーザー名]\.wslconfig"にて、Dockerで利用するメモリを12GBまで確保できるようにしておくこと
    - Macの場合は『Docker for Desktop』で、「Extensions」-> 「Settings」 -> 「Resources」を開き、「Memory」の欄から変更できる
- .env.defaultを.envというファイル名でコピーして、必要な値を埋めること
    - OpenAI関連の箇所は、OpenAIを利用しない場合はなくても大丈夫です
### 構築手順
docker image のビルドとコンテナの実行  
```
docker compose up --build -d
```
利用するモデルをダウンロードする  
まずは、ollamaのコンテナに入る  
```
docker exec -it ollama bash
```

その後、利用したいモデルをダウンロード(https://ollama.com/library)  
```
ollama pull llama2
```

Ollamaのコンテナを出る  
```
exit
```

APIのコンテナに入り、スタート用のシェルを実行  
```
docker exec -it game-ai-agent sh
```
MINA用のコントラクト操作用ファイルを実行する準備
```
cd app/libs/contracts
# モジュールをインストール
npm install
# コントラクトの実行ファイルをビルド
npm run build
```

keyファイルを配置
```
# それぞれのキーは管理者に確認してください
app/libs/contracts/keys/contractKey/zkbot.json
app/libs/contracts/keys/feepayerKey/zkbot.json
```

アプリケーションを実行
```
# /app配下で実行
sh start.sh
```

### 動作確認
Postmanなどで、wsに接続確認し、messageの送受信ができればOK
- URL
    - `ws://localhost:8080/api/ws`
- massageのサンプル
    - ゲームの開始
        - リクエスト
            - `{"message_type":"initialization", "game_type": "two_truth_a_lie", "sender": "system"}`
        - レスポンス
            - `{"message_type":"initialization", "message": "ゲームを始めましょう", "sender": "bot"}`
    - 質問チャット
        - リクエスト
            - `{"message_type":"chat", "message": "1番について語ってください", "sender": "user1"}`
        - レスポンス
            - `{"message_type":"chat", "message": "旅行が大好きです", "sender": "bot"}`
    - 回答チャット
        - リクエスト
            - `{"message_type":"answer", "message": "2", "sender": "user1"}`
        - レスポンス
            - `{"message_type":"result", "result": "success", "sender": "bot"}`
            - resultは現在、ランダムで"success"か"failed"が返却されます。
#### 参考
https://apidog.com/jp/blog/how-to-test-websocket-with-postman/
## 実装ルール
### Linter/Formatter
- Linter
    - pylint
- Formatter
    - Black Formatter

どちらも、vscodeの拡張機能で検索して、インストールするだけです。
### コメントルール
- 1行は72文字までとする。
- import文はコメントの直後に記述する。
- 概要のみの1行、詳細な説明の複数行を記述する。
- 1行目は概要のみ簡潔に記述する。
- 複数行の場合は、空行を挟んで説明を記述する。
- docstringと対象定義の間に空行を挟まない。
- モジュールの場合は、公開するクラス、関数などについて1行の説明を付けて一覧化する。
- クラスの場合は、何をするクラスなのかの概要、外部に公開するメソッドやインスタンス変数などを記述する。
- クラスの場合は、冒頭ではdocstringとの間に空行を挟む。
- 関数の場合は、何をするのかの概要、パラメータ、戻り値、発生する例外などについて記述する。
#### 関数でのコメント記載例
```
def func(arg1, arg2):
    """概要

    詳細説明

    :param 引数(arg1)の名前: 引数(arg1)の説明
    :param 引数(arg2)の名前: 引数(arg2)の説明
    :return: 戻り値の説明
    :raises 例外の名前: 例外の定義
    """
    value = arg1 + arg2
    return value
```

## ディレクトリ構成
```
./

├── app/ # アプリケーションのメインロジックが含まれる
│   ├── __init__.py
│   ├── main.py
│   ├── api/ # APIのロジックが含まれる
│   │   ├── dependencies.py # APIの依存関係を定義するファイル(通常、認証、認可、データベース接続の確立、設定の読み込みなどの処理を含む)
│   │   └── routes/ # FastAPIのAPIRouterを定義し、各エンドポイントのパスとハンドラー関数を登録する。
│   ├── schemas/ #Pydanticスキーマが含まれるディレクトリです。Pydanticスキーマは、データの構造や型、検証ルールを定義するために使用される。API側で受け渡されるデータの構造を表現
│   │   └── __init__.py
│   ├── services/ # アプリケーションのビジネスロジックが含まれる
│   │   └── __init__.py
│   ├── domain/ # ドメインの管理や、固有のビジネスロジックが含まれる
│   │   └── __init__.py
│   ├── core/ # 設定ファイルなど、アプリ共有の設定などコアとなるファイルを定義する
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── logging_config.py
│   ├── utils/ #  共通関数やヘルパー関数をまとめるためのユーティリティモジュール
│   │   ├── __init__.py
│   │   └── enum.py
│   └── tests/ # テストコードが含まれる(TODO)
│       ├── __init__.py
│       └── test_app.py
├── ollama/ollama # ollamaでインストールするモデルが格納される
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

