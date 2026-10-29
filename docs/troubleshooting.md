# トラブルシューティング

自習で詰まりやすい箇所と、その確認方法をまとめています。**症状から探してください。**

---

## 認証・環境

### `uip` コマンドが見つからない

CLI がインストールされていないか、PATH に入っていません。

```bash
npm install -g @uipath/cli
uip --version
```

### ログインしているはずなのに Orchestrator のコマンドが失敗する

セッションの有効期限が切れているか、別のテナントにログインしています。まず状態を確認します。

```bash
uip login status --output json
```

`Organization` と `Tenant` が演習環境のものか、`ExpirationDate` が未来かを見てください。違っていれば入り直します。

!!! warning "セッションは約 1 時間で切れます"
    各レッスンの所要時間（70〜100 分）はこれを超えるため、**レッスンの途中で必ず切れます。**

    - **`ExpirationDate` は UTC 表記です。** 日本時間に直すには 9 時間を足してください
      （例: `2026-10-19T05:30:00Z` → 日本時間 14:30）
    - `uip login` が成功しても、**戻り値に新しい `ExpirationDate` は含まれません。**
      確認するには `uip login status` を実行してください

    **各レッスンを始める前に `uip login` を実行し直す**のが確実です。

```bash
{{ login_command }}
```

!!! note
    `uip login` はブラウザーが開きます。コーディングエージェントに実行させるのではなく、**自分のターミナルで実行**してください。

### フォルダーやバケットが見つからないと言われる

[0. 演習環境を準備する](loan-application-underwriting/0-environment-setup.md)を実施していない可能性があります。存在を確認します。

```bash
uip or folders list --all --name "{{ practice_folder }}" --output json
uip or buckets list --folder-path "{{ practice_folder }}" --output json
```

---

## コーデッドエージェント（第2部 レッスン1）

### `uipath executable not found` / Python が見つからない

仮想環境が有効化されていない状態で `uip codedagent` を実行しています。**有効化してから** `setup` をやり直してください。

=== "Windows (PowerShell)"
    ```powershell
    .\.venv\Scripts\Activate.ps1
    uip codedagent setup --force
    ```

=== "Windows (コマンドプロンプト)"
    ```bat
    .venv\Scripts\activate
    uip codedagent setup --force
    ```

=== "Mac / Linux"
    ```bash
    source .venv/bin/activate
    uip codedagent setup --force
    ```

### `.venv` フォルダー自体が無い

コーディングエージェントが手順2 のプロジェクト生成時に作成します。ターミナルを閉じて手順の途中から再開した場合など、まだ作られていないことがあります。

```bash
uv venv --python 3.13
```

そのうえで上記の有効化と `uip codedagent setup --force` を実行してください。

### Orchestrator の入力引数に、見覚えのない項目がたくさん並ぶ

LangGraph の状態（`GraphState`）が、そのまま入力スキーマとして公開されています。**入力専用のモデルを分けてください。**

```python
class GraphInput(BaseModel):
    loan_id: str

builder = StateGraph(GraphState, input=GraphInput, output=GraphOutput)
```

修正したら `uip codedagent init` を実行し直し、`entry-points.json` の入力が `loan_id` だけになったことを確認します。

### `uip agent review` が FAIL を返す

評価（eval）データポイントが 0 件だと `Verdict: FAIL` になります。**スキーマやツールに問題がなくても起きる正常な結果**です。

Studio Web の実行結果パネルにある「**評価セットに追加**」ボタンで、成功した実行をそのまま評価データにできます。1件追加すれば解消します。

---

## ローコードエージェント（第1部 レッスン3）

### `uip agent refresh` が「folder must be named after the resource name」で失敗する

リソースのフォルダー名が `resource.json` の `name` と**完全一致**している必要があります。`name` が `"Analyze Files"`（スペース入り）なら、フォルダー名も `Analyze Files` でなければいけません。

```
resources/Analyze Files/resource.json    ← 正しい
resources/AnalyzeFiles/resource.json     ← 失敗する
```

### 添付ファイルを渡してエージェントを試したい

**`uip` CLI では添付ファイルを渡せません。** Studio Web のデバッグ実行か、Orchestrator のジョブ実行から試してください。`uip agent debug` も添付入力のエージェントには使えません。

---

## Maestro フロー（第2部 レッスン3）

### `validate` は通るのに、実行すると Faulted する

**最も見つけにくい不具合です。** まず原因を確認します。

```bash
uip maestro flow instance list -f <フォルダーキー> --output json
uip maestro flow instance incidents <インスタンスID> -f <フォルダーキー> --output json
```

`ErrorDetails` に次のように出ていたら、バインディングの問題です。

```
No app: <エージェント名> found in folder: {{ practice_folder }}
```

アプリを探しているのに**エージェントの名前**が出るのが特徴です。人的タスク（Action App）ノードは、`bindings[]` 配列で**最初に見つかった同名のバインディング**を拾ってしまうため、エージェントのバインディングしか無いとそれを掴みます。

**対処**: アプリをソリューションリソースに登録し、アプリ用のバインディング対を `bindings[]` の**先頭**に置きます。

```bash
uip solution resources add --source remote --kind App \
  --name "<アプリ名>" --folder-path "{{ practice_folder }}" --output json
```

```json
"bindings": [
  { "id": "bindingAppName",       "name": "name",       "type": "string",
    "resource": "app", "resourceKey": "{{ practice_folder }}.<アプリ名>",
    "default": "<アプリ名>", "propertyAttribute": "name", "resourceSubType": "CodedAction" },
  { "id": "bindingAppFolderPath", "name": "folderPath", "type": "string",
    "resource": "app", "resourceKey": "{{ practice_folder }}.<アプリ名>",
    "default": "{{ practice_folder }}", "propertyAttribute": "folderPath", "resourceSubType": "CodedAction" },
  { "...エージェント用のバインディングはこの後ろに..." }
]
```

### ジョブがいつまでも「実行中」に見える

**Orchestrator のジョブ API は Maestro フローの失敗を隠すことがあります。** `uip or jobs get` が `Running` を返していても、実際には Faulted している場合があります。Maestro 側の API で確認してください（上記のコマンド）。

### パッケージを上げ直したのに、古いバージョンが実行される

`uip or processes update` には `--package-version` がありません。プロセスを作り直す必要があります。

```bash
uip or processes delete <プロセスキー> --yes --output json
uip or processes create --name "<プロセス名>" --package-key "<パッケージキー>" \
  --package-version "<新しいバージョン>" --folder-path "{{ practice_folder }}" --output json
```

---

## Action Center（人的タスク）

### タスクが作成されない

リスクバンドが `Low` だと自動承認されるため、**タスクは作成されないのが正常**です。Medium / High の申込で試してください。

タスクの有無は次で確認できます。

```bash
uip tasks list --folder-path "{{ practice_folder }}" --output json
```

### Approve / Reject のボタンが押せない（READ ONLY になっている）

タスクは **Unassigned（未割り当て）** で作成されます。**開いただけでは自分に割り当てられません。**

Action Center でタスクを開いたら、**画面上部の「Assign to self」をクリック**してください。
これで編集可能になり、Approve / Reject が押せるようになります。

!!! warning "レッスン4 では時間制限があります"
    レッスン4 の RPA は Run Job のタイムアウト（30 分）内にタスクを完了させる必要があります。
    ここで迷うと実行が失敗するため、**タスクを開いたら真っ先に「Assign to self」**を押してください。

### CLI でタスクを完了しようとすると `This action is no longer assigned to you` になる

同じ理由です。CLI から完了する場合は、先に自分に割り当てます。

```bash
# 自分のユーザー ID を調べる
uip tasks users --folder-path "{{ practice_folder }}" --output json

# 割り当ててから完了する
uip tasks assign <タスクID> --user-id <ユーザーID> --output json
uip tasks complete <タスクID> --type AppTask --action Approve \
  --folder-path "{{ practice_folder }}" --data '{"Notes":"確認しました"}' --output json
```

!!! note
    画面から操作する場合は、上記の「Assign to self」が同じ役割を果たします。

---

## RPA ワークフロー（第2部 レッスン4）

### `Error code 1100` / 「フォルダーが存在しないか、このフォルダーへのアクセス権がユーザーにありません」

**`uip rpa run` は `uip login` のセッションでは動きません。** PC にインストールされた
**UiPath Assistant（Robot）の接続先テナント**で実行されます。

Assistant が演習テナントと別のテナントに接続していると、Run Job と Upload Storage File が
このエラーで失敗します。**エラーメッセージはテナントの不一致を示さないため、原因が分かりにくい**のが厄介です。

**確認する**

1. タスクトレイの **UiPath Assistant** を開きます
2. **設定（歯車）→ Orchestrator 設定**で、接続先の組織・テナントを確認します
3. 演習テナントと違っていれば、接続し直します

ログからも確認できます。

=== "Windows (PowerShell)"
    ```powershell
    Get-Content "$env:LOCALAPPDATA\UiPath\Logs\internal\Robot.log" -Tail 50
    ```

!!! note "`uip rpa run` にテナントを指定するオプションはありません"
    `uip rpa run --help` にフォルダーやテナントを指定するフラグはなく、**Assistant の接続先がすべて**です。
    `uip login` でどのテナントにログインしていても、ローカル実行の接続先は変わりません。

**ローカル実行を飛ばす選択肢もあります**

Assistant の接続先を変えられない場合は、**ローカル実行（手順5）を省いて、手順6（Orchestrator への公開）
→ 手順7（Orchestrator からの実行）に進んでください。** Orchestrator から実行すれば `uip login` と同じ
テナントで動きます。レッスンの目的は達成できます。


### Run Job がタイムアウトする

**これが自習で最も詰まりやすい箇所です。**

Run Job を「ジョブの完了を待機」（`Busy`）で使うと、起動した Maestro フローが完了するまでロボットがブロックされます。中・高リスクの申込では Action Center の人的タスクで停止するため、**承認するまで待ち続けます。既定のタイムアウトは 10 分です。**

**対処（どちらでも可）**

1. **実行したらすぐに Action Center を開き、その場でタスクを完了させる**（推奨）
2. `TimeoutMS` を延ばす（例: 1800000 = 30 分）

### `final_decision` が空のまま results.csv に書かれる

Run Job の実行モードが「待機しない」（`None`）になっています。**この モードでは出力引数が返りません。** 「ジョブの完了を待機」（`Busy`）に変更してください。

!!! warning "Start Job アクティビティは使えません"
    よく似た名前の **Start Job** アクティビティは fire-and-forget で、**開始したプロセスの出力引数を返しません。**
    `final_decision` を受け取るには **Run Job** を使う必要があります。

### `uip rpa validate` の結果の読み方

結果は `Data.message` に文字列で入ります。`Data.errors` のような配列はありません。

```bash
uip rpa validate --file-path "Main.xaml" --project-dir . --output json
```

- 成功: `"No diagnostics found."`
- 失敗: `"Found 1 error(s):\n[error] ... | activity: 1.219"`

`validate` が通っても `build` で落ちることがあります。**必ず両方を実行してください。**

```bash
uip rpa build . --output json
```

---

## Studio Web

### ローカルでは通るのに Studio Web でコンパイル エラーになる

```
error BC31424: 型 'System.Data.DataTable' は、アセンブリ 'System.Data.Common' に転送されました。
```

`Main.xaml` の `TextExpression.ReferencesForImplementation` に **`System.Data.Common`** を追加してください。
`System.Data` は残したままで構いません。詳しくは[レッスン4](loan-application-underwriting/4-intake-enrichment.md)。

### 「選択したストレージ バケットはこのソリューションに含まれていません」

ソリューションで使う Orchestrator リソースは、ソリューション側で宣言が必要です。

```bash
uip solution resources add --source remote --kind Bucket   --name "{{ storage_bucket }}" --folder-path "{{ practice_folder }}" --output json
```

### `uip solution upload` が HTTP 500 で失敗する

```
Failed during overwrite-solution: HTTP 500 on POST .../Solution/<id>/Overwrite
Could not find a part of the path '/storage/azure/.../.project/...'
```

**Studio Web で一度開いたソリューションは、CLI から上書きできなくなります。** ブラウザーのタブを閉じても解消しません。

**対処**: `.uipx` の `SolutionId` を新しい GUID に書き換えて `uip solution upload` すると、新規ソリューションとして
作成されます。古いほうは削除してください。

```bash
uip solution delete <古い SolutionId> --yes --output json
```

読み出し（`uip solution download`）は引き続き可能です。

### フローに「結果「Reject」には下流のノードがありません」と出る

**正常です。無視してください。** 人的タスクの判断は、そのあとの判定ノードが `status` を見て分岐します。

**この警告を消そうとしないでください。** 出力ポートを outcome ごとに分けると `validate` は通りますが、
**実行時に誤った経路を通ります**（条件式のない分岐が 2 本生成されるため）。詳しくは[レッスン3](loan-application-underwriting/3-maestro-flow.md)。

---

## UiBank API（テストデータ）

### `loan_id` が 404 になる

UiBank は**共有のデモ環境**です。データは日々追加され、**ときどきリセットされます**。本コース執筆時点で確認した ID も、あなたが実行する時点では存在しない可能性があります。

存在を確認するには次を実行します。

```bash
curl -s -o /dev/null -w "%{http_code}\n" {{ uibank_api }}/api/quotes/<loan_id>
```

404 なら、[レッスン3](loan-application-underwriting/3-maestro-flow.md)の手順に従って**自分で新しい見積を作成**してください。

### リスクバンドが Low / Medium / High に分かれない

これは失敗ではありません。`risk_band` は **LLM が借入額・期間・債務所得比率・市場平均との比を総合して判断**するため、債務所得比率（DTI）だけで狙ったバンドになるとは限りません。

さらに、**UiBank の平均借入額は変動します**。市場平均が変わると `loan_to_market_ratio` が変わり、**同じ申込内容でも判定が変わります**。

**対処**: 入力値を調整して実行し直してください。目安は次のとおりですが、確実ではありません。

| 狙うバンド | DTI の目安 | 補足 |
|---|---|---|
| Low | 15% 未満 | 借入額が市場平均を下回ると下がりやすい |
| Medium | 30〜35% | 借入期間が長いほど Medium に寄りやすい |
| High | 80% 以上 | 借入期間を短く（1年）すると DTI が跳ね上がる |

---

## 解決しないとき

1. 実行したコマンドと、そのときの出力（`--output json` 付き）を控える
2. [演習環境の片付け](cleanup.md)で該当のリソースを削除し、そのレッスンをやり直す

`uip` CLI や UiPath スキル自体の不具合と思われる場合は、次のコマンドで UiPath に直接報告できます。

```bash
uip feedback send
```
