# 第2部の完了

!!! tip "おめでとうございます！"

    申込の受付から、AI による与信審査、人的レビュー、最終判断まで、Maestro がオーケストレーションするコードファーストなローン審査パイプラインを丸ごと構築しました。

---

## 構築したもの

4 つのコンポーネントが連携し、1 本の自動化パイプラインとして動作します。

RPA ワークフローが申込者の CSV を読み込み、1 件ずつ UiBank に送信し、受理された申込ごとに Maestro Flow プロセスを開始します。フローの中では Python のエージェントが UiBank API を使って与信審査を行い、**6 つの値**を出力します。低リスクの申込は自動承認され、そこでフローは終了します。中・高リスクの申込ではフローが一時停止し、Action Center で React 製のダッシュボードが開きます。ローン担当者は AI の審査結果を確認して判断を送信します。フローはその判断を受け取り、`final_decision` を出力します。RPA はその完了を待っており、結果を `results.csv` に書き込んでストレージバケットにアップロードします。

| コンポーネント | 役割 |
|---|---|
| **コーデッドエージェント（Python / LangGraph）** | `loan_id` を受け取り、3 つのツールで UiBank API を呼び出し、財務指標を計算し、LLM を使って **6 項目**（クレジットスコア・リスクバンド・審査サマリー・月々の返済額・債務所得比率・市場平均比）を生成する |
| **Coded Action App（React / TypeScript）** | ローン担当者用ダッシュボード。Maestro から 12 個の入力すべてを受け取り、承認または却下の判断を受け付ける |
| **Maestro Flow** | エンドツーエンドのフローをオーケストレーションする。エージェントを呼び出し、リスクバンドで振り分け、人的レビュー用にアプリを開き、`final_decision` を出力する |
| **Studio RPA ワークフロー** | `loan-applications.csv` を読み込み、各行を UiBank に送信し、受理された申込ごとに Maestro Flow を開始して完了を待ち、`results.csv` を更新してストレージバケットにアップロードする |

いずれのコンポーネントも、UiPath スキルを使ってコーディングエージェントが生成し、`uip` CLI でデプロイしたものです。

---

## 結果を確認する

### 1. `results.csv`

すべての行の最終ステータスが `Loan Approved` または `Loan Rejected` のいずれかになっているはずです。ストレージバケットにも同じファイルがアップロードされています。

**Orchestrator** → **{{ practice_folder }}** → **ストレージバケット** → **{{ storage_bucket }}**

### 2. Maestro の実行トレース

Orchestrator の Maestro 実行トレースと `results.csv` を突き合わせ、**振り分けがエージェントのリスクバンドと一致していた**ことを確認してください。

- 自動承認された行 → エージェントが `Low` を返した申込
- 人的レビューを経た行 → `Medium` または `High` を返した申込

### 3. Action Center の履歴

完了したタスクの一覧から、**12 項目すべてに値が入っていた**ことを確認できます。

```bash
uip tasks list --folder-path "{{ practice_folder }}" --output table
```

---

## ソリューションとして一括デプロイしてみる

ここまでは、各レッスンでプロジェクトを**個別に**デプロイしてきました。動作を確認しながら進めるためです。

ですが 3 つのプロジェクト（エージェント・フロー・RPA）は同じソリューションの中にあるので、
**1 コマンドでまとめてデプロイできます。** これが UiPath の本来の配備単位です。

```bash
cd LoanApplicationUnderwriting

# 1. ソリューションをパッケージ化する
uip solution pack . <出力先ディレクトリ> --version 1.0.0 --output json

# 2. Orchestrator に公開する
uip solution publish <出力先ディレクトリ>/LoanApplicationUnderwriting_1.0.0.zip --output json

# 3. 新しいフォルダーを作って配備・アクティベートする
uip solution deploy run   --name "LoanUnderwritingDeploy"   --package-name "LoanApplicationUnderwriting"   --package-version "1.0.0"   --folder-name "LoanUnderwritingDemo"   --parent-folder-path "Shared"   --output json
```

`"Status": "DeploymentSucceeded"` と `"ActivationStatus": "SuccessfulActivate"` が返れば成功です。
指定したフォルダーに **3 つのプロセスが一度に作られます。**

!!! warning "ローン担当者ダッシュボードは含まれません"
    レッスン2 で説明したとおり、**Coded Action App はソリューションに含めても配備先フォルダーにアプリが作られません。**
    そのため、この一括デプロイだけではフローの人的タスクが動きません（`170015 No app ... found in folder`）。

    アプリは `uip codedapp deploy` で個別にデプロイし、フローはそのアプリを参照する必要があります。
    本コースの手順はそうなっています。

!!! tip "片付けの順序に注意してください"
    デプロイを削除するときは、**プロセスを消す → フォルダーを消す → `uip solution deploy uninstall`** の順で行ってください。
    いきなり `uninstall` すると `FailedUninstall` になります。詳しくは[演習環境の片付け](../cleanup.md)をご覧ください。

---

## さらに発展させるには

**与信ロジックを改善する**

現在は、LLM が 3 つの財務指標を総合的に解釈しています。市場平均に対する借入額の比率をより重視するようシステムプロンプトを調整したり、高収入の若年層と中程度の収入の年配層とを区別して扱うようにしてみてください。同じサンプルプロファイルで再テストし、リスクバンドがどう変わるかを観察しましょう。

**極端なケース向けに自動却下の経路を追加する**

現状では、中・高リスクの申込はすべてローン担当者に回されます。Maestro Flow に条件を追加し、`credit_score < 20` の場合はその場で自動的に却下するようにしてみましょう。明らかなケースを除外でき、担当者のキューを減らせます。

**React アプリを拡張する**

3 つの財務指標を小さなチャートで表示するセクションをダッシュボードに追加してみましょう。DTI をバー、クレジットスコアをゲージ、市場平均に対する借入額の比率を比較線で示す、といった具合です。AI の推奨の裏側にある数値を、ローン担当者がより深く把握できるようになります。

**却下の経路を通知につなぐ**

却下が記録されたあと、申込者にメールを送る Integration Service のステップを追加してみましょう。Maestro Flow の却下終了状態のあとにノードを 1 つ足すだけ、コネクタの呼び出し 1 回で済みます。

**待機の設計を見直す**

レッスン4 の RPA は「ジョブの完了を待機」でロボットをブロックしています。これは学習のための構成です。実運用に近づけるなら、**中断（Suspend）モード**で永続化を使い、待機中にロボットを解放する設計を試してみてください。Workflow Analyzer が出していた `Inefficient usage of Persistence activity` の警告も解消します。

**テストデータを自社のものに差し替える**

本コースの UiBank は共有のデモ API で、データが変動します。**自社の API や Data Fabric エンティティに差し替える**と、判定が安定し、そのまま社内の検証に使えます。

---

## もっと詳しく

| リソース | 説明 |
|---|---|
| [UiPath Studio のドキュメント](https://docs.uipath.com/studio) | Studio の XAML ワークフロー、アクティビティライブラリ、Orchestrator への公開 |
| [UiPath Coded Agents のドキュメント](https://docs.uipath.com/automation-cloud/docs/coded-agents) | Python エージェントのフレームワーク — LangGraph 連携、ツール定義、UiPath AI Trust Layer |
| [UiPath Python SDK](https://uipath.github.io/uipath-python/) | コーデッドエージェントで使う SDK のリファレンス |
| [UiPath Apps のドキュメント](https://docs.uipath.com/apps) | React / TypeScript のアプリ開発、`action-schema.json`、入力と outcome のパターン |
| [UiPath Maestro のドキュメント](https://docs.uipath.com/maestro) | Flow の構造、ノードの種類、条件式、変数のマッピング |
| [LangGraph のドキュメント](https://langchain-ai.github.io/langgraph/) | グラフベースのエージェントフレームワーク — ノード、エッジ、ツール呼び出し、状態管理 |
| [UiPath CLI リファレンス](https://docs.uipath.com/uipath-cli) | スキャフォールド、実行、パック、公開のための全コマンドリファレンス |
| [Action Center のドキュメント](https://docs.uipath.com/action-center) | 人的タスク（Human-in-the-Loop）のリファレンス |

---

## 片付け

コースを終えたら、テナントに残ったリソースを削除できます。

[**演習環境の片付け**](../cleanup.md) — プロセス、パッケージ、アプリ、バケット、フォルダーの削除手順

やり直したい場合も、該当のリソースだけ削除して、そのレッスンから再開できます。

---

!!! info "フィードバックをお寄せください"
    `uip` CLI や UiPath スキル自体の不具合は、`uip feedback send` で UiPath に直接報告できます。

[**次のステップへ**](../next-steps.md)
