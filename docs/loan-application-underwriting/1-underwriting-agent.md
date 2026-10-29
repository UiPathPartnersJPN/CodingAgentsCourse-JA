# 1. AI による与信審査

`uipath-agents` スキルを使って、UiBank API からローンのデータを取得し、財務指標を計算し、LLM にその結果を解釈させて与信審査の結果を生成する Python / LangGraph エージェントを生成します。

!!! info "このレッスンで作るもの"
    `loan_id` を 1 つ受け取り、**6 つの値を返す**コーデッドエージェントです。

    ```
    credit_score / risk_band / assessment_summary /
    monthly_repayment / debt_to_income_ratio / loan_to_market_ratio
    ```

    **この 6 つは、レッスン2 のアプリとレッスン3 のフローがそのまま参照します。** ひとつでも欠けると後で詰まるため、手順3 で必ず確認してください。

!!! tip "始める前に `uip login` を実行し直してください"
    **`uip` のセッションは約 1 時間で切れます。** このレッスンの所要時間はそれを超えるため、
    途中で認証エラーになることがあります。始める前に入り直しておくと確実です。

    ```bash
    uip login status --output json
    ```

    `ExpirationDate` は **UTC 表記**です。日本時間に直すには 9 時間を足してください。

## 1. ソリューションの中にプロジェクトフォルダーを作る

[レッスン0](0-environment-setup.md) で作ったソリューションの中に移動し、`LoanUnderwritingAgent` という名前の空のフォルダーを作成します。

```bash
cd LoanApplicationUnderwriting
mkdir LoanUnderwritingAgent
```

このフォルダーをコーディングエージェント（Claude Code、Codex など）で開きます。

!!! note "ソリューションの中で作業します"
    フォルダー構成はこうなります。
    ```
    LoanApplicationUnderwriting/          ← ソリューション
    ├── LoanApplicationUnderwriting.uipx
    └── LoanUnderwritingAgent/            ← いまここを作った
    ```
    プロジェクトをソリューションに**登録する**のは、生成が終わったあと（手順3 の最後）です。

## 2. エージェントの内容を説明する

作りたいものを、コーディングエージェントに平易な言葉で説明します。

```text
次の処理を行う UiPath のコーデッドエージェントを LangGraph で構築してください:

1. loan_id を入力として受け取る
2. UiBank API（{{ uibank_swagger }}、認証不要）を呼び出してローン見積を検証し、
   申込者の借入希望額（loan amount）、借入期間（loan term）、年収（yearly income）、年齢（age）を抽出する
3. 市場水準との比較のため、UiBank の全申込における平均借入額を取得する
4. 加工前の財務指標を計算して LLM に提示する: 月々の返済額、債務所得比率（月々の返済額が月収に占める割合）、
   および当該ローンが市場平均と比べてどの水準にあるか
5. LLM にそれらの指標を解釈させ、クレジットスコア（0〜100）とリスクバンド（Low / Medium / High）を付与し、
   平易な日本語での審査サマリーを生成する

6. エージェントの出力は次の 6 つとする。後続の Maestro フローとローン担当者用アプリが
   すべて参照するため、1 つも省略しないこと:
   - credit_score（number, 0〜100）
   - risk_band（string, "Low" | "Medium" | "High"）
   - assessment_summary（string）
   - monthly_repayment（number）
   - debt_to_income_ratio（number）
   - loan_to_market_ratio（number）

7. 入力は loan_id の 1 つだけとし、グラフの内部状態が入力スキーマに露出しないようにすること

5 件のケースからなる eval セットも含めてください。エージェントの名前は LoanUnderwritingAgent とします。
UiPath SDK を使用してください。
```

コーディングエージェントは `uipath-agents` スキルのコンテキストを読み取り、完全なエージェントプロジェクトを生成します。

- `main.py` — LangGraph のグラフ定義を含むエージェントのエントリーポイント（ツールはここに書かれる場合も、別の `tools.py` に分かれる場合もあります）
- `pyproject.toml` — `uipath-langchain` を依存関係に含むプロジェクト設定
- `langgraph.json` — エントリーポイントの定義
- `evaluations/` — 評価ケース

!!! note "仮想環境もここで作られます"
    コーディングエージェントは、この手順の中で **Python の仮想環境（`.venv`）を作成し、依存関係をインストール**します。手順5 で「仮想環境を有効化します」と出てきますが、その `.venv` はここで作られたものです。

    もしターミナルを閉じて手順5 から再開し、`.venv` が無い場合は、[トラブルシューティング](../troubleshooting.md)を参照してください。

## 3. 生成されたコードをレビューする

プロジェクトを IDE で開きます。コーディングエージェントごとに生成されるコードは少しずつ異なり、構成にも幅があります。重要なのは、必要な要素が揃っているかどうかです。

**確認すべきポイント:**

- **`@tool` デコレーターの付いた 3 つの関数** — `verify_quote`、`get_average_loan_amount`、`compute_financial_metrics` に対応するものです。別ファイルの `tools.py` にあっても、すべて `main.py` の中にあっても構いません。
- **システムプロンプト** — 財務指標を総合的に解釈し、クレジットスコア・リスクバンド・審査サマリーを生成するよう LLM に指示する `SYSTEM_PROMPT` 文字列です。通常は別ファイルではなく `main.py` にインラインで、プレーンなプロンプト文字列として組み立てられます。
- **エージェントのエントリーポイント** — `langgraph.json` で定義され、`main.py:graph`（`graph = builder.compile()` の部分）を指します。

### ⚠️ 入出力の契約を必ず確認する

**このレッスンで最も重要な確認です。** `uip codedagent init` を実行したあとに生成される `entry-points.json` を開き、入力が 1 つ・出力が 6 つになっていることを確かめてください。

```bash
uip codedagent init
```

```json
{
  "entryPoints": [
    {
      "input":  { "properties": { "loan_id": { ... } } },
      "output": {
        "properties": {
          "credit_score": { ... },
          "risk_band": { ... },
          "assessment_summary": { ... },
          "monthly_repayment": { ... },
          "debt_to_income_ratio": { ... },
          "loan_to_market_ratio": { ... }
        },
        "required": [
          "credit_score", "risk_band", "assessment_summary",
          "monthly_repayment", "debt_to_income_ratio", "loan_to_market_ratio"
        ]
      }
    }
  ]
}
```

| 症状 | 原因と対処 |
|---|---|
| **出力が 3 つしかない** | プロンプトの指示が反映されていません。コーディングエージェントに「出力を 6 つにしてください」と伝えて修正させ、`uip codedagent init` をやり直してください。**ここで直さないと、レッスン3 で変数をマッピングできません** |
| **入力に `loan_id` 以外が並んでいる** | LangGraph の内部状態が入力スキーマとして公開されています。入力専用のモデルを分ける必要があります（下記） |

入力が多すぎる場合は、コーディングエージェントに次のように依頼します。

```text
グラフの内部状態が入力スキーマに露出しています。入力専用の Pydantic モデルを作り、
StateGraph の input 引数に指定して、エージェントの入力が loan_id の 1 つだけになるようにしてください。
```

### システムプロンプトを確認する

しきい値を固定のスコアに機械的に対応づけるのではなく、指標の組み合わせについて推論し、自然言語で説明を生成するよう LLM に指示しているはずです。プロンプトが機械的すぎる場合は、コーディングエージェントに次のように依頼します。

```text
システムプロンプトを修正して、固定のルールを当てはめるのではなく、複数の要因の組み合わせについて
LLM が推論するようにしてください。たとえば、DTI が高くても借入額が小さい場合と、同じ DTI で
借入額が大きい場合とでは、扱いが変わるべきです。
```

### プロジェクトをソリューションに登録する

生成とスキーマの確認が終わったら、**プロジェクトをソリューションに登録します。**

```bash
cd ..                                              # ソリューションのルートへ
uip solution projects add "LoanUnderwritingAgent" --output json
cd LoanUnderwritingAgent                           # 作業フォルダーに戻る
```

`"Status": "Added successfully"` が返り、`LoanApplicationUnderwriting.uipx` の `Projects` に
`Type: "Agent"` として登録されます。

!!! tip "登録のタイミング"
    `project.uiproj`（プロジェクトのマニフェスト）は `uip codedagent init` が作るため、**init のあとでないと登録できません。**

### 使用するモデルを確認する

テナントで利用できるモデルは環境によって異なります。一覧を確認できます。

```bash
uip codedagent list-models
```

生成されたコードが指定しているモデルがこの一覧に無い場合は、一覧にあるものへ差し替えてください。判断を伴うタスクなので、**推論に強いモデル**（Anthropic の Sonnet 系、OpenAI の上位モデルなど）を選びます。

## 4. エージェントをローカルでテストする

### 1. プロジェクトフォルダーに移動する

ターミナルを開き、作成した `LoanUnderwritingAgent` フォルダーに移動します。

```bash
cd "/path/to/your/LoanUnderwritingAgent"
```

パスは、お使いのマシン上の実際の場所に置き換えてください。

### 2. テスト用のローン見積を用意する

!!! warning "固定の loan_id は使えません"
    UiBank は**共有のデモ環境**です。データは日々追加され、**ときどきリセットされます**。
    そのため、本文に特定の `loan_id` を載せても、あなたが実行する時点では存在しない可能性があります。
    **必ず自分で探してください。**

次のプロンプトをコーディングエージェントに渡してください。リスクプロファイルに幅のある見積を 3 件見つけてくれます。

```text
UiBank の Swagger ドキュメントを開いて内容を確認してください:
{{ uibank_swagger }}

ドキュメントに記載された読み取り専用のエンドポイントのみを使い、リスクプロファイルに幅がある
既存のローン見積を 3 件見つけてください。目安は次のとおりです。

- 1 件目: 債務所得比率（借入額 ÷（借入期間 × 年収））が 15% 未満
- 2 件目: 債務所得比率が 30〜35%、かつ借入額が市場平均を上回るもの
- 3 件目: 債務所得比率が 80% 以上（借入期間が 1 年の案件を探すと見つかりやすい）

要件:
- データの作成・更新・削除は一切行わないこと。
- loan_id を捏造したり、存在を確認していない ID を使い回したりしないこと。各レコードが実在することを検証すること。
- 3 件の loan_id、借入額、期間、年収、年齢、債務所得比率を表で報告すること。
```

### 3. エージェントを実行して確認する

選んだ 3 件でエージェントを実行します。

```text
いま構築した LoanUnderwritingAgent を、先ほど選んだ 3 件の loan_id でテストしてください。

1. 各 loan_id について、コーデッドエージェントを実行し、結果をそれぞれ別の出力ファイルに保存してください。

2. 各出力ファイルを読み、次の内容が含まれていることを確認してください:
   - 0 から 100 の間の credit_score
   - Low、Medium、High のいずれかの risk_band
   - 一般論ではなく、実際に指標（債務所得比率、市場平均との比較）に基づいて推論した、
     平易な言葉での審査サマリー
   - monthly_repayment、debt_to_income_ratio、loan_to_market_ratio の 3 つの数値

3. 次の表形式で報告してください: loan_id | 借入額 | 期間 | 収入 | 年齢 | クレジットスコア | リスクバンド。
   フィールドの欠落や例外の発生があれば指摘してください。
```

### 4. リスクバンドが 3 つに分かれたか確認する

!!! important "ここを飛ばさないでください"
    **3 件が Low / Medium / High に分かれていることを確認してください。** 分かれていない場合は、別の見積を選び直して実行し直します。

    レッスン3 では「Low なら自動承認、それ以外は人的レビュー」という分岐を作ります。**バンドが分かれていないと、その分岐を確認できません。**

分かれなかった場合、よくある原因は次のとおりです。

| 症状 | 原因 |
|---|---|
| 2 件以上が同じバンドになる | `risk_band` は DTI だけで決まりません。**借入額・期間・市場平均との比を LLM が総合して判断**します。DTI だけを見て選ぶと揃ってしまうことがあります |
| 狙ったより低いバンドになる | 借入額が市場平均を大きく下回っていると、リスクが低めに評価されます。**市場平均を上回る金額**の見積を選ぶと上がりやすくなります |
| 前回と判定が変わった | UiBank の平均借入額は変動します。市場平均が変われば `loan_to_market_ratio` も変わり、**同じ申込でも判定が変わります**。異常ではありません |

!!! note "3 件の loan_id を控えておいてください"
    ここで確定した 3 件は、**レッスン3 のテストでもそのまま使います。** 控えておいてください。
    ただし時間が空くと 404 になる可能性があります。その場合はレッスン3 で選び直してください。

## 5. エージェントをデプロイする

まず仮想環境を有効化します。

!!! info "何のために有効化するのか"
    次に実行する `uip codedagent setup` は、**`uip` が使う Python の場所を記録します。** 有効化しておくと、
    手順2 でコーディングエージェントが作った `.venv` の Python が記録されます。

    **コーディングエージェント（Claude Code など）にコマンドを実行させている場合、通常は不要です。**
    エージェントは `.venv` の Python を直接使うためです。**自分で新しいターミナルを開いて実行する場合は、
    有効化してください。** 別の Python が記録されると、`init` で import エラーが出たり、入出力スキーマが
    正しく生成されなかったりすることがあります。

=== "Windows (コマンドプロンプト)"
    ```bat
    .venv\Scripts\activate
    ```

=== "Windows (PowerShell)"
    ```powershell
    .\.venv\Scripts\Activate.ps1
    ```

=== "Mac / Linux"
    ```bash
    source .venv/bin/activate
    ```

!!! note "PowerShell で `Activate.ps1` が実行できない場合"
    実行ポリシーで止められています。**コマンドプロンプト（`cmd.exe`）から `.venv\Scripts\activate` を使えば、
    設定を変えずに済みます。** こちらをおすすめします。

    どうしても PowerShell で行う場合は次を実行しますが、これは PowerShell の実行ポリシーを**恒久的に変更**する
    操作です。企業で管理された PC では、情報システム部門の確認が必要な場合があります。

    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    ```

### エージェントを公開する

セットアップを実行します。これは、`uip` CLI が使う Python の場所を記録する操作です。

```bash
uip codedagent setup --force
```

```json
{
 "Result": "Success",
 "Code": "CodedAgentsSetup",
 "Data": {
  "PythonPath": "python",
  "Package": "uipath",
  "PackageInstalled": "Yes",
  "PackageVersion": "2.14.30"
 }
}
```

!!! note "表示される値は環境によって異なります"
    `PythonPath` と `PackageVersion` は、お使いの環境とインストール時期によって変わります。`"Result": "Success"` であれば問題ありません。

ログイン状態を確認します。

```bash
uip login status --output json
```

`Organization` と `Tenant` が演習環境のものであることを確認してください。

UiPath プロジェクトを初期化します。これによりエントリーポイント、Mermaid 図、プロジェクトマニフェストが生成されます。

```bash
uip codedagent init
```

```text
'bindings.json' already exists, skipping.
✓  Created 'entry-points.json' file with 1 entrypoint(s).
✓  Created 1 mermaid diagram file(s).
✓  Updated 'project.uiproj' file.
✓  Updated: CLAUDE.md, CLI_REFERENCE.md, SDK_REFERENCE.md, AGENTS.md, REQUIRED_STRUCTURE.md

  Entrypoint: agent
  ──────────────────────────────────────────────────

      ┌───────────┐
      │ __start__ │
      └─────┬─────┘
         │
         ▼
    ┌ node ─────────────┐
    │ verify_loan_quote │
    └─────────┬─────────┘
         │
         ▼
   ┌ node ────────────────┐
   │ get_market_benchmark │
   └───────────┬──────────┘
         │
         ▼
     ┌ node ───────────┐
     │ compute_metrics │
     └────────┬────────┘
         │
         ▼
     ┌ node ─────────┐
     │ assess_credit │
     └───────┬───────┘
         │
         ▼
       ┌─────────┐
       │ __end__ │
       └─────────┘
```

!!! tip "4 つのコマンドの違い"
    | コマンド | 役割 |
    |---|---|
    | `uip codedagent setup` | `uip` が使う Python の場所を記録する（環境側の設定） |
    | `uip codedagent init` | コードから入出力スキーマとマニフェストを生成する（**コードを変えたら実行し直す**） |
    | `uip codedagent deploy` | パッケージ化して、テナントのフィードに**公開**する |
    | `uip or processes create` | 公開したパッケージを、フォルダー内で**実行可能なプロセスとして登録**する（これが無いと Orchestrator からもフローからも実行できない） |

    入出力のモデルを変更したら、**必ず `init` をやり直してから** `deploy` してください。

### エージェントをデプロイする

```bash
uip codedagent deploy --tenant
```

```text
⠋ Packaging project ...
Name       : LoanUnderwritingAgent
Version    : 0.0.1
Description: Loan underwriting agent that assesses UiBank loan quotes with LLM-driven credit scoring
✓  Project successfully packaged.
⠋ Publishing most recent package: LoanUnderwritingAgent.0.0.1.nupkg ...
✓  Package published successfully!
```

### プロセスを作成する

`deploy` はパッケージをテナントのフィードに**公開しただけ**です。`Package published successfully!` と出ますが、
**この状態ではまだ実行できません。** {{ practice_folder }} フォルダーの中に「プロセス」として登録して、はじめて
Orchestrator から、そしてレッスン3 のフローから呼び出せるようになります。

まず、パッケージとそのエントリーポイントを確認します。

```bash
uip or packages list --search "LoanUnderwritingAgent" --output json
```

```bash
uip or packages entry-points "LoanUnderwritingAgent:0.0.1" --output json
```

!!! important "ここでも出力 6 項目を確認してください"
    `entry-points` の結果に含まれる `OutputArguments` に、**6 項目すべてが `required` として並んでいること**を確認してください。
    ここに現れるものが、レッスン3 のフローから参照できるすべてです。

続いてプロセスを作成します。

=== "Mac / Linux"
    ```bash
    uip or processes create \
      --name "LoanUnderwritingAgent" \
      --package-key "LoanUnderwritingAgent" \
      --package-version "0.0.1" \
      --entry-point "agent" \
      --folder-path "{{ practice_folder }}" \
      --output json
    ```

=== "Windows (PowerShell)"
    ```powershell
    uip or processes create `
      --name "LoanUnderwritingAgent" `
      --package-key "LoanUnderwritingAgent" `
      --package-version "0.0.1" `
      --entry-point "agent" `
      --folder-path "{{ practice_folder }}" `
      --output json
    ```

!!! tip "フォルダーは名前で指定できます"
    `uip or processes create` は `--folder-path` でフォルダー名を直接指定できます。GUID を調べて貼り付ける必要はありません。
    ただし**レッスン2 の `uip codedapp deploy` はキー（GUID）しか受け付けません。** そちらではキーを使います。

!!! warning "コードを直して再デプロイしたときは、プロセスのバージョンも上げてください"
    `uip codedagent deploy` で `0.0.2` を公開しても、**プロセスは作成時のバージョン（`0.0.1`）を実行し続けます。**
    直したはずの挙動が変わらないときは、ここを疑ってください。

    レッスン3 のフローが参照するのもパッケージではなく、**このプロセス**です。

### デプロイ済みエージェントを Orchestrator から実行する

**Orchestrator** で **{{ practice_folder }}** フォルダーを開き、`LoanUnderwritingAgent` を選択して、手順4 で確定した `loan_id` を入力引数に指定して実行を開始します。

ジョブの出力で、**6 項目すべて**が返っていることを確認してください。

!!! note "ローカル実行と結果が少し違うことがあります"
    LLM を使っているため、`credit_score` は実行のたびに数点ずれることがあります。**一致しているべきなのはリスクバンドと、6 項目が揃っていること**です。

    また `loan_to_market_ratio` は、UiBank の平均借入額が変動するため実行のたびに微妙に変わります。これも正常です。

---

## このレッスンでできたこと

- `loan_id` を受け取り、**6 項目を返す**コーデッドエージェントを構築した
- Orchestrator のテナントフィードに公開し、**{{ practice_folder }}** フォルダーにプロセスを作成した
- リスクプロファイルの異なる 3 件で、Low / Medium / High に分かれることを確認した

次は [2. ローン担当者レビュー用ダッシュボード](2-loan-officer-app.md) で、この 6 項目を表示する画面を作ります。
