# 2. ローン担当者レビュー用ダッシュボード

`uipath-coded-apps` スキルを使って、Maestro の人的タスク（Human Task）のレビュー画面内でレンダリングされる React 製の Coded Action App を生成します。AI による与信審査の結果を表示し、ローン担当者が申込を承認または却下できるようにします。

!!! info "このレッスンで作るもの"
    **12 個の入力**を受け取る 2 ペイン構成のダッシュボードです。そのうち **6 個は[レッスン1](1-underwriting-agent.md) のエージェントが返す値**です。

    | 入力 | 出所 |
    |---|---|
    | `LoanId` / `ApplicantFirstName` / `ApplicantLastName` / `LoanAmount` / `LoanTerm` / `YearlyIncome` | Maestro プロセス（レッスン3） |
    | `CreditScore` / `RiskBand` / `AssessmentSummary` / `MonthlyRepayment` / `DebtToIncomeRatio` / `LoanToMarketRatio` | **レッスン1 のエージェント** |

    レッスン1 で出力を 6 つにしていないと、ここで 3 つが埋まりません。

!!! tip "始める前に `uip login` を実行し直してください"
    **`uip` のセッションは約 1 時間で切れます。** このレッスンの所要時間はそれを超えるため、
    途中で認証エラーになることがあります。始める前に入り直しておくと確実です。

    ```bash
    uip login status --output json
    ```

    `ExpirationDate` は **UTC 表記**です。日本時間に直すには 9 時間を足してください。

## 1. プロジェクトフォルダーをコーディングエージェントで開く

!!! warning "このレッスンだけソリューションの外に作ります"
    レッスン1・3・4 のプロジェクトはソリューション `LoanApplicationUnderwriting` の中に作りますが、
    **Coded Action App はソリューションの外**に作ります。

    **理由**: Coded Action App をソリューションに含めると、パッケージには入るものの
    **配備先フォルダーにアプリが作られません。** その状態でフローを実行すると、人的タスクの段階で次のエラーになります。

    ```
    ErrorCode 170015
    No app: loanofficerdashboard found in folder: ...
    ```

    そのためアプリは**独立したプロジェクトとして作り、`uip codedapp deploy` で個別にデプロイ**します。
    レッスン3 のフローは、こうしてデプロイされた**公開済みアプリ**を参照します。

レッスン1 の最後では `LoanApplicationUnderwriting/LoanUnderwritingAgent/` にいます。
**ソリューションの 1 つ外側（作業ルート）**まで戻り、`loanofficerdashboard` という名前の空のフォルダーを作成します。

```bash
cd ../..                   # LoanUnderwritingAgent → LoanApplicationUnderwriting → 作業ルート
mkdir loanofficerdashboard
```

!!! warning "`cd ..` を 1 回だけにしないでください"
    1 回だけだと `LoanApplicationUnderwriting/`（**ソリューションの中**）に着いてしまい、アプリがソリューション内に
    作られます。上の警告のとおり、レッスン3 で `ErrorCode 170015 No app: loanofficerdashboard found in folder:`
    になります。

    作成後は次の構成になります。

    ```
    <作業ルート>/
    ├── LoanApplicationUnderwriting/      ← ソリューション
    │   ├── LoanApplicationUnderwriting.uipx
    │   └── LoanUnderwritingAgent/
    └── loanofficerdashboard/             ← いまここを作った（ソリューションの外）
    ```

    別のターミナルを開いている場合は、`cd` せずに**作業ルートで直接** `mkdir loanofficerdashboard` でも構いません。

このフォルダーをコーディングエージェント（Claude Code、Codex など）で開きます。

!!! note "名前は全て小文字で統一します"
    このあと **アプリ名・パッケージ名・フォルダー名のすべてに `loanofficerdashboard` を使います。** 揃えておくと、デプロイのときに名前の食い違いで迷わずに済みます。

## 2. アプリの内容を説明する

作りたいものを、コーディングエージェントに平易な言葉で説明します。担当者に何が見えるのか、データはどこから来るのか、判断ボタンが何をするのかを具体的に伝えてください。

```text
loanofficerdashboard という名前の UiPath Coded Action App を構築してください。要件は次のとおりです:

1. 12 個の入力を受け取る: LoanId（string）、ApplicantFirstName（string）、
   ApplicantLastName（string）、LoanAmount（number）、LoanTerm（number）、
   YearlyIncome（number）— これらは Maestro プロセスから渡されます — に加えて、
   コーデッドエージェントの 6 つの出力: CreditScore（number、0〜100）、RiskBand
   （string — Low / Medium / High）、AssessmentSummary（string）、
   MonthlyRepayment（number）、DebtToIncomeRatio（number）、
   LoanToMarketRatio（number）
2. 2 ペイン構成のダッシュボードを表示する: 左ペインには申込者名、LoanId、
   借入額、借入期間、年収を表示し、右ペインには CreditScore をプログレスバーで、
   RiskBand を色分けしたバッジで（緑 = Low、黄 = Medium、赤 = High）、
   AssessmentSummary をテキストブロックで、さらに 3 つの財務指標
   （月々の返済額、債務所得比率、市場平均に対する借入額の比率）を
   ラベル付きの値として表示する
3. ローン担当者がコメントを追加できる、任意入力の Notes テキストエリアを用意する
4. ローン担当者が Approve（緑）または Reject（赤）のボタンで判断を送信できるようにする。
   これらは action-schema.json の outcomes として定義し、外部 API の呼び出しは不要とする
5. UiPath のサービス（Orchestrator、Data Fabric など）は一切呼び出さないため、
   @uipath/uipath-typescript は導入しないこと。@uipath/coded-action-app だけを使うこと
6. ローカル開発時のみ有効なデモモードを用意する。localhost でのみ動作し、
   Action Center のタスクが無くても 12 個の入力すべてにサンプル値を表示すること。
   本番時の挙動は一切変更しないこと
```

!!! warning "「UiPath TypeScript SDK を使って」とは指示しないでください"
    このアプリは UiPath のサービスを一切呼び出しません。必要なのは `@uipath/coded-action-app` だけです。

    SDK（`@uipath/uipath-typescript`）を導入すると、**OAuth の External Application（クライアント ID）を作る流れに入ります。これにはテナント管理者の権限が必要**なため、権限が無いと途中で止まってしまいます。上のプロンプトでは明示的に不要と伝えています。

コーディングエージェントは `uipath-coded-apps` スキルのコンテキストを読み取り、完全なアプリプロジェクトを生成します。

- `action-schema.json` — すべての入力と `Approve` / `Reject` の outcomes を定義
- `src/components/Form.tsx` — 2 ペインレイアウトを持つフォーム本体
- `src/App.tsx` — テーマ（ライト / ダーク）の管理とレイアウトの外枠
- `package.json` — プロジェクトの依存関係
- `vite.config.ts` — `base: './'` を設定した Vite の設定ファイル

## 3. 生成されたコードをレビューする

プロジェクトを IDE で開きます。次の内容が確認できるはずです。

### `action-schema.json`

- `inputs` に **12 個**すべてが定義されている
- `outputs` に `Notes` がある
- `outcomes` に `Approve` と `Reject` がある

!!! important "6 個がエージェントの出力と対応しているか"
    `CreditScore` / `RiskBand` / `AssessmentSummary` / `MonthlyRepayment` / `DebtToIncomeRatio` / `LoanToMarketRatio` の 6 個が揃っているか確認してください。

    **足りない場合は、レッスン1 のエージェントの出力が 3 つのままです。** レッスン1 の手順3 に戻って修正してください。ここで気づけば、レッスン3 で詰まるより遥かに早く直せます。

スキーマが正しいかは、スキルに同梱されているバリデーターでも確認できます。

```bash
node <スキルのディレクトリ>/scripts/validate-action-schema.js action-schema.json
```

`action-schema.json is valid.` と出れば成功です。

### `src/components/Form.tsx`

**フォームの本体はここです。** 2 ペインレイアウト、クレジットスコアのプログレスバー、色分けされたリスクバッジが実装されているか確認します。入力はアクションスキーマのコンテキストから読み取られます。

`src/App.tsx` はテーマの切り替えと外枠だけを担当します。レイアウトを変えたいときは `Form.tsx` を見てください。

## 4. ローカルで実行する

!!! note "アプリのフォルダー内で実行してください"
    ```bash
    cd loanofficerdashboard
    ```

```bash
npm install
npm run dev
```

サーバーが正常に起動すると、次のように表示されます。

```text
  VITE v8.3.2  ready in 432 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

ポート番号は環境によって異なります（5173、5174 など）。ターミナルに表示された番号を使ってください。

表示された URL を開くと、**デモモードのサンプルデータが入った状態**でダッシュボードが表示されます。

- 左ペインに申込者名・ローン ID・借入額・期間・年収
- 右ペインにクレジットスコアのバー、リスクバンドのバッジ、審査サマリー、3 つの財務指標
- 下部に Notes の入力欄と、承認 / 却下のボタン

ボタンを押すと「デモモードで送信しました」といった表示が出ます。**Action Center のタスクは完了しません。**

!!! tip "デモモードは本番に影響しません"
    デモモードは `import.meta.env.DEV`（= `npm run dev`）かつ localhost のときだけ有効になります。
    本番ビルドでは無効になり、Action Center 上の挙動は一切変わりません。

    **レッスン3 を完成させる前にここで画面を確認しておくと、後の作業がぐっと進めやすくなります。**

## 5. ビルド・パック・パブリッシュ

```bash
npm run build
uip codedapp pack dist -n loanofficerdashboard --version 1.0.0
uip codedapp publish -t Action
```

!!! important "公開先を聞かれたら `N` を選んでください"
    `uip codedapp publish -t Action` を実行すると、次のプロンプトが出ます。

    ```text
    Publish into your Personal Workspace feed instead of the tenant feed? (y/N)
    ```

    **`N` を選択してください**（そのまま Enter でも同じです）。テナントフィードに公開されます。

    `y` を選ぶと個人用ワークスペースのフィードに公開され、**次の手順6 の
    `uip codedapp deploy --folder-key` が失敗します**（演習用フォルダーに配備できません）。

`-t Action` フラグは必須です。これによってアプリが Coded Action App として登録され、Maestro が人的タスクをこのアプリに振り向けられるようになります。

!!! warning "`-t Action` を省略しないでください"
    省略すると既定の Web アプリとして登録され、**Action Center のタスクに紐づきません。** バージョンを上げて再公開するときも、毎回必要です。

公開に成功すると、次のような情報が表示されます。

```text
Published App Details:
  Name: loanofficerdashboard
  Version: 1.0.0
  System Name: ID687881510ccc4a4bb1b629b3c303e8df
  Deploy Version: 1
```

## 6. Orchestrator にデプロイする

!!! important "ここだけはフォルダーのキー（GUID）が必要です"
    `uip codedapp deploy` は `--folder-path` に対応していません。**キーを指定する必要があります。**

まずフォルダーキーを取得します。

```bash
uip or folders list --all --name "{{ practice_folder }}" --output json
```

`Name` が `{{ practice_folder }}` のエントリーを探し、その `Key` の値をコピーしてください。

```bash
uip codedapp deploy -n loanofficerdashboard --folder-key <コピーしたキー>
```

例:

```bash
uip codedapp deploy -n loanofficerdashboard --folder-key b956f165-bcbb-4ad6-a739-d8c337b96ef7
```

これでアプリが有効になりました。レッスン 3 では、Maestro が人的レビューのステップで一時停止し、ローン担当者が入力できるようにこのアプリをレンダリングします。

### デプロイを確認する

**Orchestrator** で **{{ practice_folder }}** フォルダー → **アプリ** を開き、`loanofficerdashboard` が正常にデプロイされて表示されていることを確認してください。

!!! note "この確認は画面でのみ行えます"
    デプロイ済みアプリの一覧を取得する CLI コマンドはありません。Orchestrator の画面で確認してください。

---

## このレッスンでできたこと

- 12 入力・2 outcomes の Coded Action App を構築した
- デモモードでローカルに画面を表示し、レイアウトを確認した
- `-t Action` で公開し、**{{ practice_folder }}** フォルダーにデプロイした
- **12 入力のうち 6 つがレッスン1 のエージェント出力と対応している**ことを確認した

次は [3. Maestro Flow によるオーケストレーション](3-maestro-flow.md) で、エージェントとこのアプリをつなぎます。
