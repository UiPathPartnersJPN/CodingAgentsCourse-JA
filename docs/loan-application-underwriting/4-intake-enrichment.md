# 4. 申込受付とデータ補完

`uipath-rpa` スキルを使って、CSV から申込者データを読み込み、各ローン申込を UiBank API 経由で送信し、結果を `results.csv` に書き出す Studio の XAML ワークフローを生成します。

!!! warning "まとまった時間を確保してください"
    このワークフローは、起動した Maestro フローの**完了を待ちます**。中・高リスクの申込では Action Center の人的タスクで停止するため、**実行したらその場で承認する必要があります。**

    **30 分程度、中断せずに作業できるときに着手してください。** 詳しくは[手順5](#5-実行してテストする)で説明します。

!!! info "このレッスンで作るもの"
    ```
    loan-applications.csv
      → 各行を UiBank に申込（POST）
      → 返ってきた loan_id で Maestro フローを起動
      → フローの完了を待って final_decision を受け取る
      → results.csv に結果を書く
      → ストレージバケットにアップロード
    ```

!!! tip "始める前に `uip login` を実行し直してください"
    **`uip` のセッションは約 1 時間で切れます。** このレッスンの所要時間はそれを超えるため、
    途中で認証エラーになることがあります。始める前に入り直しておくと確実です。

    ```bash
    uip login status --output json
    ```

    `ExpirationDate` は **UTC 表記**です。日本時間に直すには 9 時間を足してください。

## 1. ソリューションの中にプロジェクトを作る

[レッスン0](0-environment-setup.md) で作ったソリューションの中で作業します。

```bash
cd LoanApplicationUnderwriting
```

ここをコーディングエージェント（Claude Code、Codex など）で開きます。プロジェクトの作成は
コーディングエージェントが `uip rpa init` で行います。

!!! note "`uip rpa init` はプロジェクト名を `--name` で渡します"
    他の `init` 系コマンドと違い、位置引数ではありません。

    ```bash
    uip rpa init --name LoanApplicationDispatcher --target-framework Portable --expression-language VisualBasic
    ```

    コーディングエージェントに任せる場合も、この形になっているか確認してください。


## 2. 自動化の内容を説明する

作りたいものを、コーディングエージェントに平易な言葉で説明します。

```text
次の処理を行う LoanApplicationDispatcher という名前の UiPath Studio の自動化を構築してください:

1. loan-applications.csv を DataTable に読み込む。列は first_name、last_name、email、
   loan_amount、loan_term、yearly_income、age
2. 各行について、UiBank API（{{ uibank_swagger }}、認証不要）の
   newquote エンドポイントにローン申込を送信する。Content-Type は
   application/x-www-form-urlencoded の POST リクエストとし、次のようにマッピングする:
   loan_amount → amount、loan_term → term、yearly_income → income、age → age、
   email → email
3. 申込が受理された場合（レスポンスの accepted が true）は、レスポンスの quoteid を loan_id として、
   {{ practice_folder }} フォルダー内のフロープロセス LoanUnderwritingProcess を開始し、
   loan_id、applicant_first_name、applicant_last_name、loan_amount、loan_term、income を
   入力として渡す。プロセスの完了を待って final_decision を受け取り、
   results.csv に 1 行を書き込む。内容は loan_id、ステータス
   （final_decision が Approved なら "Loan Approved"、そうでなければ "Loan Rejected"）、
   および申込者の全フィールド
4. 申込が却下された場合は、loan_id を空、ステータスを "Failed"、エラーを
   "Application rejected" として results.csv に 1 行を書き込む
5. 各行の処理を Try/Catch で囲む。例外が発生した場合は、loan_id を空、ステータスを
   "Failed"、例外メッセージをエラーとして results.csv に 1 行を書き込む
6. すべての行の処理が終わったら、results.csv を Orchestrator の
   {{ practice_folder }} フォルダー内の {{ storage_bucket }} ストレージバケットにアップロードする

7. ジョブの起動には Run Job アクティビティを使い、実行モードは「ジョブの完了を待機」とすること。
   Start Job アクティビティは出力引数を返さないため使わないこと。
   待機のタイムアウトは 30 分に設定すること。

8. Main.xaml の TextExpression.ReferencesForImplementation に、System.Data に加えて
   System.Data.Common のアセンブリ参照も含めること。

このプロジェクトはクロスプラットフォーム（Windows 用ではなく）として作成してください。
生成するのはプロジェクトファイルのみで構いません。
```

!!! danger "要件7 を省略しないでください"
    **Start Job アクティビティは fire-and-forget で、開始したプロセスの出力引数を返しません。** `final_decision` を受け取れないため、要件3 が実装できません。

    必要なのは **Run Job** です。実行モードは 3 つあり、選択によって挙動が変わります。

    | 実行モード | 出力引数 | 挙動 |
    |---|---|---|
    | 待機しない（None） | **返らない** | 起動して即座に次へ進む |
    | **ジョブの完了を待機（Busy）** | 返る | **ロボットがブロックされる。既定のタイムアウトは 10 分** |
    | 中断（Suspend） | 返る | ワークフローを中断して解放。**永続化の設定が必要** |

    本レッスンでは「ジョブの完了を待機」を使い、タイムアウトを 30 分に延ばします。

コーディングエージェントは `uipath-rpa` スキルのコンテキストを読み取り、完全な Studio プロジェクトを生成します。

- `Main.xaml` — ForEach ループ、HTTP リクエスト、Run Job、CSV 出力を含むメインのワークフロー
- `project.json` — プロジェクト設定とアクティビティパッケージの依存関係

## 3. 生成されたワークフローをレビューする

Studio で `Main.xaml` を開きます。次の内容が確認できるはずです。

- **Read CSV** — `loan-applications.csv` を DataTable に読み込む
- **For Each Row in Data Table** — 申込者ごとにループする
  - **Try/Catch** — 各行を囲み、失敗しても実行全体が止まらないようにする
  - **HTTP Request** — `/api/quotes/newquote` に対して、フォームエンコードされたフィールド（amount、term、income、age、email）で POST する
  - **Deserialize JSON** — レスポンスを解析して `accepted` と `quoteid` を取り出す
  - **If** — `accepted` で分岐する
  - **Run Job** — `LoanUnderwritingProcess` を起動し、完了を待って `final_decision` を受け取る
  - **Add Data Row** — 結果の行を蓄積する
- **Write CSV** — `results.csv` に書き出す
- **Upload Storage File** — バケットにアップロードする

!!! important "Run Job のプロパティを確認してください"
    **Run Job** アクティビティを開き、次の 3 点を確認します。

    | プロパティ | 期待値 |
    |---|---|
    | プロセス名 | `LoanUnderwritingProcess`（レッスン3 でデプロイした名前と**完全一致**） |
    | フォルダーパス | `{{ practice_folder }}` |
    | 実行モード | **ジョブの完了を待機**（これでないと `final_decision` が返りません） |
    | タイムアウト | 1800000 ミリ秒（30 分） |

    プロセス名が 1 文字でも違うと、実行時に「プロセスが見つからない」で失敗します。

!!! note "API の認証は不要です"
    UiBank は認証なしで使えるデモ API です。HTTP Request アクティビティの認証設定は空のままで構いません。

HTTP Request アクティビティがフォームのボディを正しく設定していない場合は、コーディングエージェントに修正を依頼します。

```text
/api/quotes/newquote への HTTP Request は、JSON ボディではなく、Content-Type
application/x-www-form-urlencoded のフォームフィールドを使う必要があります。
アクティビティを修正してください。
```

### ⚠️ ローカルでは通るが Studio Web で失敗する 2 点

次の 2 つは、**`uip rpa validate` も `uip rpa build` も成功するのに、Studio Web で開くとエラーになります。**
CLI だけで作業していると気づけないため、先に確認してください。

#### ① `System.Data.Common` のアセンブリ参照

`Main.xaml` の `TextExpression.ReferencesForImplementation` に `System.Data.Common` があるか確認します。

```xml
<TextExpression.ReferencesForImplementation>
  <sco:Collection x:TypeArguments="AssemblyReference" ...>
    <AssemblyReference>System</AssemblyReference>
    <AssemblyReference>System.Data</AssemblyReference>
    <AssemblyReference>System.Data.Common</AssemblyReference>   <!-- これが必要 -->
    ...
```

無いと、Studio Web で DataTable 変数の箇所にコンパイラ エラーが出ます。

```
error BC31424: 型 'System.Data.DataTable' は、アセンブリ 'System.Data.Common' に転送されました。
プロジェクトに 'System.Data.Common' への参照が見つかりません。
```

クロスプラットフォーム（Portable）では `System.Data.DataTable` が `System.Data.Common` に型転送されるため、
明示的な参照が必要です。`System.Data` は残したまま追加してください。

#### ② ストレージバケットのソリューションリソース宣言

このワークフローは `{{ storage_bucket }}` バケットを使います。**ソリューションで使う Orchestrator のリソースは、
ソリューション側で宣言する必要があります。**

```bash
cd ..                      # ソリューションのルートへ
uip solution resources add --source remote --kind Bucket   --name "{{ storage_bucket }}" --folder-path "{{ practice_folder }}" --output json
cd LoanApplicationDispatcher
```

`resources/solution_folder/Bucket/OrchestratorBucket/{{ storage_bucket }}.json` が生成されます。

宣言しないと、Studio Web でバケット名の欄が赤くなり次のメッセージが出ます。

```
選択したストレージ バケットはこのソリューションに含まれていません。
```

!!! info "これはソリューションの考え方そのものです"
    ソリューションは「このまとまりが何に依存しているか」を明示する単位です。バケット・アセット・キューなどを
    使う場合は、同じように `uip solution resources add` で宣言します。

    RPA プロジェクトには `bindings_v2.json` が無いため、`uip solution resources refresh` では同期されません
    （`Synced 0 resources` になります）。**明示的に追加してください。**

### プロジェクトをソリューションに登録する

```bash
cd ..                                                   # ソリューションのルートへ
uip solution projects add "LoanApplicationDispatcher" --output json
cd LoanApplicationDispatcher
```

`LoanApplicationUnderwriting.uipx` の `Projects` に `Type: "Process"` として登録されます。

### 検証する

```bash
uip rpa validate --file-path "Main.xaml" --project-dir . --output json
uip rpa build . --output json
```

!!! note "結果の読み方"
    `validate` の結果は `Data.message` に文字列で入ります。

    - 成功: `"No diagnostics found."`
    - 失敗: `"Found 1 error(s): ..."`

    **`validate` が通っても `build` で落ちることがあります。必ず両方を実行してください。**

    `build` が `"Success": true` を返せば完了です。警告（命名規則、Automation Hub URL など）は出ても問題ありません。

!!! tip "「Inefficient usage of Persistence activity」という警告について"
    Run Job を「ジョブの完了を待機」で使うと、この警告が出ます。**ロボットをブロックして待つ構成であることをツールが指摘しています。**

    本レッスンでは学習のため意図的にこの構成にしています。実運用では「中断（Suspend）」モードで永続化を使い、待機中にロボットを解放する設計を検討してください。

## 4. 実行する前に

`loan-applications.csv` がプロジェクトフォルダーにあることを確認してください。まだ作成していない場合は、次のサンプルデータを使ってコーディングエージェントに生成してもらえます。

```text
次のデータを使って、カレントフォルダーに loan-applications.csv というファイルを作成してください:

first_name,last_name,email,loan_amount,loan_term,yearly_income,age
Alice,Nguyen,alice.nguyen@example.com,15000,3,48000,34
Ben,Carter,ben.carter@example.com,50000,5,30000,40
Clara,Osei,clara.osei@example.com,70000,5,28000,29

各行の first_name、last_name、email は、上記とは異なる値に置き換えてください。
自分の名前を使っても、架空の値を作っても構いませんが、上記と同じにはしないでください。
loan_amount、loan_term、yearly_income、age は変更せずそのまま残してください。
```

!!! warning "共有のデモ環境にデータを作成します"
    このワークフローは **UiBank に新しいローン見積を作成します**（`POST /api/quotes/newquote`）。UiBank は他の利用者も使う共有のデモ API です。

    - **氏名とメールアドレスは必ず書き換えてください。** 実在する個人の情報は使わないでください
    - 金額・期間・収入・年齢はそのままで構いません（リスクバンドが分かれるよう選ばれています）
    - 作成したデータの扱いは[演習環境の片付け](../cleanup.md#uibank-のデータについて)を参照してください

## 5. 実行してテストする

!!! danger "実行したら、すぐに Action Center を開いてください"
    このワークフローは、起動した Maestro フローの**完了を待ちます**。中・高リスクの申込では Action Center の人的タスクで停止するため、**承認するまでワークフローは先に進みません。**

    **実行ボタンを押したら、ブラウザーで Action Center を開いて待機してください。** タスクが現れたら、
    **上部の「Assign to self」をクリックしてから**承認または却下します。放置するとタイムアウトします。

    !!! note "「Assign to self」を押さないとボタンが押せません"
        タスクは未割り当ての状態で作成されるため、開いただけでは READ ONLY です。
        タイムアウトは 30 分なので、ここで迷わないよう先に覚えておいてください。

!!! warning "ローカル実行は Assistant の接続先で動きます"
    **`uip rpa run` は `uip login` のセッションでは動きません。** PC にインストールされた
    **UiPath Assistant（Robot）の接続先テナント**で実行されます。

    接続先が演習テナントと違っていると、**Run Job と Upload Storage File が次のエラーで失敗します。**

    ```text
    Error code 1100
    フォルダーが存在しないか、このフォルダーへのアクセス権がユーザーにありません
    ```

    エラーメッセージはテナントの不一致を示さないため、原因に気づきにくい箇所です。

    **実行前に確認してください。** タスクトレイの **UiPath Assistant** → **設定 → Orchestrator 設定**で、
    接続先の組織・テナントが演習環境と一致しているか見てください。

    接続先を変えられない場合は、**ローカル実行（この手順5）を飛ばして、手順6 → 手順7 に進んでください。**
    Orchestrator から実行すれば `uip login` と同じテナントで動き、レッスンの目的は達成できます。

### 実行する

Studio でプロジェクトを開き、`Main.xaml` を実行します。CLI から実行する場合は次のとおりです。

```bash
uip rpa run --file-path Main.xaml --output json
```

!!! note "`uip rpa run` はファイルを指定します"
    `uip rpa build .` のようにプロジェクトディレクトリを渡すことはできません。**`--file-path` で XAML ファイルを指定してください。**

### 進行を確認する

Output パネル（または CLI の出力）で、各申込が送信されていく様子を確認できます。

```text
[Information] Loan Submitted: 6ac09c6b5686400048920435
[Information] Loan Submitted: 6ac09cae5686400048920436
[Information] Loan Submitted: 6ac09cfd5686400048920438
```

ログが途中で止まったら、**Maestro フローが人的タスクで待機しています。** Action Center でタスクを完了させてください。

```bash
# 未完了のタスクを確認する
uip tasks list --folder-path "{{ practice_folder }}" --output table
```

### 結果を確認する

実行が終わったら `results.csv` を開きます。**3 行が出力され、各行に `loan_id` があり、ステータスが `Loan Approved` または `Loan Rejected` になっていること**を確認します。

```csv
loan_id,status,first_name,last_name,email,loan_amount,loan_term,yearly_income,age,error
6ac09c6b5686400048920435,Loan Approved,...,15000,3,48000,34,
6ac09cae5686400048920436,Loan Approved,...,50000,5,30000,40,
6ac09cfd5686400048920438,Loan Rejected,...,70000,5,28000,29,
```

ストレージバケットも確認します。

**Orchestrator** → **{{ practice_folder }}** → **ストレージバケット** → **{{ storage_bucket }}** に `results.csv` があるはずです。

!!! note "この確認は画面でのみ行えます"
    バケット内のファイル一覧を取得する CLI コマンドはありません。

## 6. Orchestrator に公開する

ローカルで動作を確認できたら、Orchestrator に公開してプロセスとして登録します。

まず、プロジェクトフォルダーの *中ではなく* **隣** に `Package` フォルダーを作成します。

=== "Windows (PowerShell)"
    ```powershell
    mkdir "..\Package"
    ```

=== "Mac / Linux"
    ```bash
    mkdir "../Package"
    ```

フォルダー構成は次のようになります。

```text
LoanApplicationUnderwriting\        ← ソリューション
    LoanApplicationDispatcher\      ← Studio のプロジェクト
    Package\                        ← .nupkg の保存先
```

続いて、プロジェクトを `.nupkg` ファイルにパックします。

=== "Windows (PowerShell)"
    ```powershell
    uip rpa pack "." "..\Package"
    ```

=== "Mac / Linux"
    ```bash
    uip rpa pack "." "../Package"
    ```

パックされた `.nupkg` を Orchestrator にアップロードします。

=== "Windows (PowerShell)"
    ```powershell
    uip or packages upload "..\Package\LoanApplicationDispatcher.1.0.0.nupkg" --output json
    ```

=== "Mac / Linux"
    ```bash
    uip or packages upload "../Package/LoanApplicationDispatcher.1.0.0.nupkg" --output json
    ```

そのうえで、アップロードしたパッケージからプロセスを作成します。

```bash
uip or processes create --folder-path "{{ practice_folder }}" \
  --name "LoanApplicationDispatcher" \
  --package-key LoanApplicationDispatcher --package-version 1.0.0 --output json
```

!!! tip "コーディングエージェントに任せる場合"
    ```text
    いま構築した LoanApplicationDispatcher の Studio 自動化を公開し、
    Orchestrator のプロセスを作成してください。

    1. プロジェクトを .nupkg にパックしてください（プロジェクトの中ではなく、隣に置いた
       Package フォルダーを使用すること）。
    2. 生成されたパッケージを Orchestrator にアップロードしてください。
    3. そのパッケージから、{{ practice_folder }} フォルダー内に、プロジェクトと同じ名前で
       プロセスを作成してください（--folder-path で指定してください）。
    4. プロセスキーを報告してください。
    ```

## 7. ローン審査をエンドツーエンドで実行する

**Orchestrator** で **{{ practice_folder }}** フォルダーを開き、`LoanApplicationDispatcher` を選択して、手動で実行を開始します。

!!! danger "ここでも、実行したらすぐ Action Center を開いてください"
    Orchestrator から実行しても挙動は同じです。中・高リスクの申込で人的タスクが発生したら、
    **「Assign to self」をクリックしてから**その場で完了させてください。

`loan-applications.csv` の各申込が送信され、受理されたものについて Maestro フローが開始され、結果が返ってくる様子を確認してください。実行が完了したら `results.csv` を開き、すべての行の最終ステータスが `Loan Approved` または `Loan Rejected` になっていることを確認します。

---

## このレッスンでできたこと

- CSV から申込を読み、UiBank に送信する RPA ワークフローを構築した
- **Run Job** でレッスン3 のフローを起動し、`final_decision` を受け取った
- 結果を `results.csv` に書き、ストレージバケットにアップロードした
- **レッスン1〜4 のすべてが 1 回の実行でつながることを確認した**

[第2部の完了](you-did-it.md) に進んでください。
