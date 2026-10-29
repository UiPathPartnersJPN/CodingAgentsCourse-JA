# 3. 初めてのエージェントを作る

!!! tip "このレッスンの進め方"

    1. サンプルファイルを入れた作業フォルダーを用意します。
    2. UiPath のエージェントスキルを使って、コーディングエージェントにシンプルなエージェントを生成してもらいます。
    3. ソリューションのスキャフォールド、スキーマの設定、検証までの流れを観察します。
    4. **Studio Web** に公開して実行し、結果を確認します。

!!! tip "始める前に `uip login` を実行し直してください"
    **`uip` のセッションは約 1 時間で切れます。** このレッスンは生成・公開・Studio Web での実行まで行うため、
    途中で認証エラーになることがあります。始める前に入り直しておくと確実です。

    ```bash
    uip login status --output json
    ```

    `ExpirationDate` は **UTC 表記**です。日本時間に直すには 9 時間を足してください。

## ゴール

このレッスンの目的は、気の利いた何かを作ることではありません。これ以降すべてのエージェントで使うことになる **「構築して公開する」ワークフロー** を身につけることです。

小さなローコードエージェントを生成し、ソリューションがどのようにスキャフォールドされるのかを見て、実行できる状態まで持っていきます。エージェント自体はあえてシンプルにしてあります。焦点を当てたいのは「**説明する → 生成する → 検証する → 公開する → 実行する**」というループそのものだからです。

## 何を作るのか

**保険金請求の受理可否（Claims Eligibility）チェック** です。請求（FNOL）の PDF と、そこで参照されている保険証券が与えられると、エージェントは 5 つの簡易なしきい値チェックを順番に実行します。

1. **保険証券のステータス** — 証券は Current / Paid か（Lapsed / Cancelled / Expired ではないか）？
2. **本人確認** — 請求者は証券の記名被保険者と一致するか？
3. **住所** — 請求書と証券の住所は一致するか？
4. **補償期間** — 事故は証券の有効期間内に発生したか？
5. **請求期限** — 損害発生から 60 日以内に請求されているか？

このエージェントは PDF をそのまま直接読み取ります。追加のセットアップは不要です。

## 手順

### 1. 作業フォルダーを用意する

空のフォルダーを作成し、その中に `samples` フォルダーを作ります。

```bash
mkdir first-agent
cd first-agent
mkdir samples
```

下記の請求書ファイルと保険証券ファイルのペアを、`samples` フォルダーにダウンロードしてください。**各請求書は証券番号で対応する証券を参照しており、必ず対応する組み合わせで実行する必要があります。**

| 請求書（Claim） | 保険証券（Policy） | シナリオ |
| :--- | :--- | :--- |
| [CLM-2026-357861-claim.pdf](assets/claim-samples/CLM-2026-357861-claim.pdf) | [HO-5534416561.pdf](assets/claim-samples/HO-5534416561.pdf) | ムンバイ（INR）— 水濡れ損害、Rajesh Kumar Sharma |
| [CLM-2026-896147-claim.pdf](assets/claim-samples/CLM-2026-896147-claim.pdf) | [HO-3883873532.pdf](assets/claim-samples/HO-3883873532.pdf) | メルボルン（AUD）— 火災損害、Mei Lin Tan |

**入力ドキュメントにも軽く目を通しておきましょう。** エージェントが何を読み取るのかが分かると、生成されたプロンプトのレビューがしやすくなります。

<details markdown="1">
<summary>任意の手順: 自分の規約を定義する（AGENTS.md）</summary>

本格的に作り始める前に、命名規則・構造・「*ワークフローは小さく保つ。すべてを 1 つのフォルダーに詰め込まない*」といったルールを書いた小さなファイルをフォルダーに置いておきましょう。

- コーディングエージェントはこのファイルを自動的に読み、新しいセッションのたびに従ってくれます。
- プロンプトだけがすべてではありません。この Markdown ファイルはエージェントの方向づけに役立ち、**セッションをまたいでも、エージェントを変えても、出力の一貫性を保てます。**
- 現時点でファイル名は統一されていません（**`CLAUDE.md`** / **`AGENTS.md`** / **`GEMINI.md`** など）。複数のエージェントを使う予定なら、実体のファイルを 1 つだけ置き、名前が異なるエージェント向けにはシンボリックリンクを張るのがベストプラクティスです。
- 以下は出発点となるサンプルです。必要に応じて拡張してください。

```markdown
# 新しいプロジェクトを作るとき

- このワークスペースフォルダーで何かを作るよう依頼されたら、ワークスペース直下で作業せず、新しいプロジェクトフォルダー（短く、小文字、ハイフン区切り）を作成すること。
- 既存のリポジトリの内側でない限り、`git init` で初期化すること。
- 本格的な実装に入る前に、プロジェクト単位の `AGENTS.md`（このファイルのようなもの）を追加し、以降のセッションでも同じ振る舞いが保たれるようにすること。
- 実装・検証・ファイル編集はすべて、その新しいプロジェクトフォルダーの中で続けること。

# UiPath プロジェクト

- 依頼に UiPath、RPA、Orchestrator、Maestro、Studio Web、`.xaml`、`.flow`、`.bpmn`、コンテキストグラウンディング、キュー、アセット、ロボット、ジョブ、トリガー、`uip` が含まれる場合は、インストール済みの UiPath エージェントスキルを適宜使用すること。
- セットアップ、検証、ビルド、パッケージング、実行、プラットフォーム操作には uip CLI を優先して使うこと。
- UiPath Cloud / Orchestrator のリソース（パッケージ、フォルダー、キューアイテムなど）を公開・デプロイ・削除・変更する前には、必ず確認を取ること。
```
</details>

### 2. コーディングエージェントを開いて始める

そのフォルダーでコーディングエージェントを開き、以下の指示を与えてください。

```text
UiPath のエージェントスキルを使って、"claims-eligibility" という名前のローコードエージェントを生成してください。
このエージェントは、請求書（claim）と保険証券（policy）の 2 つの PDF ファイルを入力として受け取ります。
両方の PDF を読み取り、保険証券に照らして請求内容を検証します。

入力:
- in_ClaimPDF — 請求者が提出した事故受付通知（FNOL: First Notice of Loss）の請求フォーム（PDF）。
- in_PolicyPDF — その請求が参照している住宅総合保険の保険証券（PDF）。

エージェントが 2 つの入力ドキュメント間で確認すべき項目:
1. 保険証券ステータスの確認（Policy Status Check）。保険証券上の Payment Status を探します。許容されるステータスは
   "Current" と "Paid" です。"Lapsed"、"Cancelled"、"Expired" の場合はこのチェックは不合格とします。
2. 本人確認（Identity Verification）。請求書上の Claimant Name と、保険証券上の Named Insured を比較します。
   軽微な差異（愛称、ミドルネーム、軽微なスペルの揺れ）は許容します。明らかに別人を指している場合は
   このチェックは不合格とします。
3. 物件住所の一致確認（Property Address Match）。請求書と保険証券に記載された物件住所を比較します。
   表記の揺れ（例: "St." と "Street"）は正規化して比較します。異なる場合はこのチェックは不合格とします。
   本演習には独立した事故報告書が存在しないため、report_address には
   "N/A — no incident report in this exercise" を設定してください。
4. 補償期間の確認（Coverage Period Check）。Incident Date が保険証券の Effective Date 以降、かつ
   Expiration Date 以前であることを確認します。この期間外であればこのチェックは不合格とします。
   開始日当日と終了日当日はいずれも補償期間に含むものとして扱います（両端を含む）。
   なお保険証券によっては Effective Date / Expiration Date ではなく "Policy Period" として
   期間がまとめて記載されている場合があります。その場合はそこから開始日と終了日を読み取ってください。
5. 請求期限の確認（Filing Deadline Check）。Incident Date と Date of Submission の間の暦日数を計算します。
   60 日を超えている場合は、請求書に遅延理由の説明があるかどうかを確認します。説明がなければ不合格とします。

エージェントは必ず以下の構造に一致する出力を返す必要があります:

{
  "out_isEligible": "boolean — 請求が審査の対象として受理できるかどうか",
  "out_EligibilityAnalysisSummary": "string — 判定理由の簡潔でわかりやすい説明",
  "out_EligibilityChecksJSON": {
    "claim_id": "string",
    "policy_number": "string",
    "escalate": "boolean — この請求に人によるさらなる確認が必要かどうか",
    "checks": {
      "policy_status":   { "result": "pass | fail", "detail": "string" },
      "identity_match":  { "result": "pass | fail", "claimant_name": "string",
                           "policyholder_name": "string", "detail": "string" },
      "address_match":   { "result": "pass | fail", "claim_address": "string",
                           "policy_address": "string", "detail": "string" },
      "coverage_period": { "result": "pass | fail", "incident_date": "string",
                           "effective_date": "string", "expiration_date": "string", "detail": "string" },
      "filing_deadline": { "result": "pass | fail", "incident_date": "string",
                           "claim_date": "string", "days_elapsed": "number", "detail": "string" }
    }
  }
}

- すべてのチェックが合格 → out_isEligible = true、それ以外は false
- 問題が「遅延提出だが正当な理由がある」場合のみ → out_isEligible = true、"escalate" = true
- ドキュメントに明示されていない情報をエージェントが推測してはならない旨を、プロンプト内で明確に記載してください。
- これは物件損害に関する FNOL / 保険金請求の受理可否プロセスです。この業務で一般的に考慮される観点と
  業界のベストプラクティスを踏まえたプロンプトを書いてください。
- 審査サマリーは日本語で生成してください。

エージェントが処理するサンプルドキュメントが samples サブフォルダーにいくつか置かれています。
```

!!! important "「両端を含む」の 1 文は重要です"
    サンプルの 1 件は、**事故日が保険証券の満了日とちょうど同じ日**です。この 1 文がないと、LLM の解釈によって「期間内」と判定されたり「期間外」と判定されたりして、**実行のたびに結果が変わります。**

    境界の扱いを明示しておくのは、LLM にルールを任せるときの基本的な作法です。

### 3. スキャフォールドの様子を見る

コーディングエージェントは、おおむね次の順序で作業を進めます（各ステップを都度承認してください）。

- **ソリューション** を作成し、その中にエージェントを初期化する
- エージェントプロジェクトをソリューションに追加する
- **システムプロンプト** を記述し、**入出力スキーマ** を設定する（ファイル入力 2 つ、出力 3 つ）
- 組み込みの **Analyze Files** ツールを追加する（添付ファイルを読むために必要）
- **validate** を実行して、その構成が Studio Web でサポートされていることを確認する

できあがる構成はおおむね次のとおりです。

```
claims-eligibility-solution/
├── claims-eligibility-solution.uipx
└── claims-eligibility/
    ├── agent.json                              ← プロンプトとスキーマ（手で編集するのはここ）
    ├── entry-points.json                       ← 自動生成
    ├── bindings_v2.json                        ← 自動生成
    └── resources/Analyze Files/resource.json   ← 組み込みツール
```

!!! warning "`Analyze Files` のフォルダー名にはスペースが入ります"
    リソースのフォルダー名は、`resource.json` の `name` と**完全に一致**している必要があります。`name` が `"Analyze Files"` なので、**フォルダー名も `Analyze Files`（スペース入り）** でなければいけません。

    ```
    resources/Analyze Files/resource.json    ← 正しい
    resources/AnalyzeFiles/resource.json     ← uip agent refresh が失敗します
    ```

    `folder must be named after the resource name "Analyze Files"` というエラーが出たら、フォルダー名を直してください。

!!! info "添付ファイルの扱い"
    ここで重要な制約があります。**添付ファイル入力は、プロンプト上ではメタデータしか参照できません。** 中身を読むには、UiPath 組み込みの **Analyze Files** ツールを呼び出す必要があります。

    そのため、システムプロンプトには「受理可否を判断する前に、必ず両方の PDF に対して Analyze Files を呼び出すこと」が明記されているはずです。生成物を確認するときに見ておいてください。

### 4. アップロードして Studio Web で開く

エージェントのビルドとローカル検証が完了しました。続けて次のように尋ねます。

```text
いいですね！ このエージェントを Studio Web で実行するには、次に何をすればよいですか？
```

エージェントは次のように提案してくれます。

```text
以下のコマンドでソリューションをアップロードしてください:

   $ uip solution upload claims-eligibility-solution --output json

これで DesignerUrl が返ってくるはずです。

その URL を Studio Web で開き、claims-eligibility エージェントを開いて、run / test の画面で次の値を指定してください:
   in_ClaimPDF: samples/ にある請求書 PDF のいずれか
   in_PolicyPDF: それに対応する保険証券 PDF
```

コマンドを実行し、返ってきた `DesignerUrl` をブラウザーで開いてください。

### 5. サンプルの請求書を実行する

!!! warning "この実行は画面から行う必要があります"
    **添付ファイルは `uip` CLI 経由で渡せません。** `uip agent debug` も添付入力のエージェントには使えないため、**Studio Web のデバッグ実行か Orchestrator のジョブ実行**でテストしてください。

Studio Web で **Debug** をクリックし、2 つのファイル入力を指定してエージェントを実行します。

1. **in_ClaimPDF** に `CLM-2026-896147-claim.pdf` を指定します。
2. **in_PolicyPDF** に `HO-3883873532.pdf` を指定します。
3. **Run**（または **Save & Debug**）を選択します。

実行が完了したら出力を開きます。スキーマで定義した 3 つのフィールド（`out_isEligible`、`out_EligibilityAnalysisSummary`、`out_EligibilityChecksJSON`）が確認できます。

請求 `CLM-2026-896147` の場合、エージェントは **受理不可（ineligible）** と判断するはずです。この請求は 60 日の期限を大きく過ぎてから提出されているためです。

```json
{
  "out_isEligible": false,
  "out_EligibilityAnalysisSummary": "請求 CLM-2026-896147 は審査の対象として受理できません。5 つの受理可否チェックのうち 4 つは合格しています。……一方で請求期限のチェックは不合格です。この請求は事故日から 83 暦日が経過してから提出されており、60 日以内という提出要件を超えています。……",
  "out_EligibilityChecksJSON": {
    "claim_id": "CLM-2026-896147",
    "policy_number": "HO-3883873532",
    "escalate": false,
    "checks": {
      "policy_status":   { "result": "pass", "detail": "……" },
      "identity_match":  { "result": "pass", "claimant_name": "Mei Lin Tan",
                           "policyholder_name": "Mei Lin Tan", "detail": "……" },
      "address_match":   { "result": "pass", "claim_address": "4/16 Chapel Street, St Kilda, VIC 3182",
                           "policy_address": "4/16 Chapel Street, St Kilda, VIC 3182", "detail": "……" },
      "coverage_period": { "result": "pass", "incident_date": "14/04/2026",
                           "effective_date": "14/04/2025", "expiration_date": "14/04/2026", "detail": "……" },
      "filing_deadline": { "result": "fail", "incident_date": "14/04/2026",
                           "claim_date": "06/07/2026", "days_elapsed": 83, "detail": "……" }
    }
  }
}
```

!!! note "文言は毎回変わります"
    LLM を使っているため、`detail` や要約のテキストは生成されるものであり、一字一句同じにはなりません。**一致しているべきなのは構造と、各チェックの `result` です。**

### 6. 確認するポイント

| 項目 | 期待値 |
|---|---|
| `out_isEligible` | `false` |
| `policy_status` | `pass` |
| `identity_match` | `pass` |
| `address_match` | `pass` |
| **`coverage_period`** | **`pass`**（事故日が満了日と同じ日。「両端を含む」の指示が効いているか） |
| `filing_deadline` | `fail` / `days_elapsed` が 83 |

`coverage_period` が `fail` になった場合は、プロンプトに「両端を含む」の 1 文が入っているか確認してください。

もう 1 組のサンプル（`CLM-2026-357861-claim.pdf` と `HO-5534416561.pdf`）でも試してみましょう。

### 7. 評価セットに追加しておく（推奨）

Studio Web の実行結果パネルに「**評価セットに追加**」ボタンがあります。**成功した実行をそのまま評価データにできます。**

追加しておくと、あとでエージェントを変更したときに、同じ入力で結果が変わっていないかを確認できます。

**できれば 5 件以上**追加してください。理由は下記のとおりです。

!!! tip "`uip agent review` を試すなら"
    エージェントの構成を自己採点するコマンドがあります。

    ```bash
    uip agent review claims-eligibility-solution/claims-eligibility --output json
    ```

    **評価データが足りないと `Verdict: FAIL` が返ります。** スキーマやツールに問題がなくても起きる、仕様どおりの結果です。

    | 評価データ | 結果 |
    |---|---|
    | 0 件 | `FAIL`（評価セットが無い） |
    | 1〜4 件 | `FAIL` / `TOO_FEW_EVALS` — *"Minimum recommended is 5."* |
    | 5 件以上 | この指摘は出なくなる |

    本レッスンのエージェントは入力が PDF 2 つなので、**評価データを 5 件揃えるにはサンプルの組み合わせを増やす必要があります。** そこまでやるかは任意です。

    ここで重要なのは「**FAIL の中身を読む**」習慣です。`Issues[].RuleId` を見れば、スキーマやツールの問題なのか、単に評価データが足りないだけなのかが分かります。

---

## このレッスンでできたこと

- ローコードエージェントを生成し、プロンプトと入出力スキーマを設定した
- 組み込みの Analyze Files ツールで PDF を読ませた
- Studio Web に公開し、サンプルの請求で実行して結果を確認した
- **「説明する → 生成する → 検証する → 公開する → 実行する」のループを 1 周した**

これ以降のすべての土台ができました。[第1部の完了](you-did-it.md) に進んでください。
