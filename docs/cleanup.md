# 演習環境の片付け

コースを終えたあと、またはレッスンをやり直す前に、テナントに残ったリソースを削除します。

!!! danger "削除は取り消せません"
    以下のコマンドはいずれも**元に戻せない操作**です。**必ず一覧で対象を確認してから削除してください。**
    特に `{{ practice_folder }}` 以外のフォルダーを対象にしていないか、毎回確かめてください。

## 何が残っているか

コースを最後まで進めると、テナントに次のものが残ります。

| 種類 | 名前（既定） | 作成したレッスン |
|---|---|---|
| Orchestrator フォルダー | `{{ practice_folder }}` | 0. 演習環境を準備する |
| ソリューション（Studio Web） | `LoanApplicationUnderwriting` | 0. 演習環境を準備する |
| ストレージバケット | `{{ storage_bucket }}`（中に `results.csv`） | 0 / 4 |
| プロセス | `LoanUnderwritingAgent` | 1. AI による与信審査 |
| プロセス | `LoanUnderwritingProcess` | 3. Maestro Flow |
| プロセス | `LoanApplicationDispatcher` | 4. 申込受付とデータ補完 |
| コーデッドアプリ | `loanofficerdashboard` | 2. ローン担当者レビュー用ダッシュボード |
| パッケージ | 上記それぞれの `.nupkg` | 1 / 3 / 4 |
| Action Center のタスク | 完了済みのレビュータスク | 3 / 4 |

このほか、第1部で作ったソリューションが Studio Web に残ります。

## 1. 残っているものを確認する

```bash
# プロセス
uip or processes list --folder-path "{{ practice_folder }}" --output table

# パッケージ（テナントフィード）
uip or packages list --output table

# バケット
uip or buckets list --folder-path "{{ practice_folder }}" --output table

# 未完了のタスクが残っていないか
uip tasks list --folder-path "{{ practice_folder }}" --output table
```

!!! note "バケットの中身は画面で確認します"
    バケット内のファイル一覧を取得する CLI コマンドはありません。
    **Orchestrator** → **{{ practice_folder }}** → **ストレージバケット** → **{{ storage_bucket }}** を開いて確認してください。

## 2. プロセスを削除する

`uip or processes list` で確認した**プロセスキー（GUID）**を使います。

```bash
uip or processes delete <プロセスキー> --yes --output json
```

!!! warning
    `--yes` を付けると確認なしで削除されます。**キーを貼り付ける前に、`processes list` の出力でプロセス名を照合してください。**

## 3. コーデッドアプリを削除する

アプリの削除は **Orchestrator の画面**から行います。

**Orchestrator** → **{{ practice_folder }}** → **アプリ** → `loanofficerdashboard` → 削除

## 4. バケットの中身とバケットを削除する

`results.csv` を残しておきたい場合は、先にダウンロードしてください。

**Orchestrator** → **{{ practice_folder }}** → **ストレージバケット** → **{{ storage_bucket }}** でファイルを削除します。

バケット自体を削除する場合は、キーを確認してから実行します。

```bash
uip or buckets list --folder-path "{{ practice_folder }}" --output json
uip or buckets delete <バケットキー> --output json
```

!!! note
    ファイルが残っているバケットは削除を拒否されます。`--force` を付けると**中のファイルごと削除**されます。中身を確認してから使ってください。

## 5. パッケージを削除する

パッケージはテナントフィードに残り続けます。再演習でバージョンが衝突する原因になるため、削除しておくと安全です。

**Orchestrator** → **テナント** → **パッケージ** から該当のものを削除してください。

## 6. フォルダーを削除する（管理者のみ）

!!! note "これは管理者の作業です"
    演習用フォルダーは管理者が作成したものです。**フォルダーの削除には開発者向け権限では足りません。**
    次回も演習する場合は、残しておいて構いません。中のリソースを 1〜5 で片付けてあれば、再演習できます。

中のリソースをすべて削除したあとに実行します。

```bash
uip or folders list --all --name "{{ practice_folder }}" --output json
uip or folders delete <フォルダーキー> --yes --output json
```

## 6b. ソリューションのデプロイを削除する（一括デプロイを試した場合）

[第2部の完了](loan-application-underwriting/you-did-it.md)で `uip solution deploy run` を試した場合は、
デプロイも削除します。

!!! warning "順序を守ってください"
    いきなり `uninstall` すると **`FailedUninstall`** になります。次の順で行ってください。

**① 配備先フォルダーのプロセスを削除する**

```bash
uip or processes list --folder-path "Shared/<配備先フォルダー名>" --output table
uip or processes delete <プロセスキー> --yes --output json
```

**② 配備先フォルダーを削除する**

```bash
uip or folders list --all --name "<配備先フォルダー名>" --output json
uip or folders delete <フォルダーキー> --yes --output json
```

**③ デプロイをアンインストールする**

```bash
uip solution deploy list --output table
uip solution deploy uninstall "<デプロイ名>" --yes --output json
```

`"Status": "SuccessfulUninstall"` が返れば完了です。デプロイの**履歴レコードは一覧に残ります**が、無効化されており影響はありません。

**④ ソリューション本体を Studio Web から削除する**（必要なら）

```bash
uip solution delete <SolutionId> --yes --output json
```

`SolutionId` は `LoanApplicationUnderwriting.uipx` の中にあります。

---

## 7. ローカルのプロジェクトフォルダー

次のフォルダーがローカルに残っています。不要であれば削除してください。

```
LoanApplicationUnderwriting/      # ソリューション
├── LoanUnderwritingAgent/        # レッスン1
├── LoanUnderwritingProcess/      # レッスン3
└── LoanApplicationDispatcher/    # レッスン4
loanofficerdashboard/             # レッスン2（ソリューション外）
```

`LoanApplicationUnderwriting/LoanUnderwritingAgent/.venv` と `loanofficerdashboard/node_modules` は容量が大きいため、ディスクを空けたい場合はここから削除すると効果があります。

## UiBank のデータについて

レッスン4 を実行すると、**共有のデモ API である UiBank に新しいローン見積が作成されます**（`POST /api/quotes/newquote`）。

これは他の利用者も使う共有環境です。**自分が作成したもの以外は削除しないでください。** 自分の `loan_id` は `results.csv` に記録されています。

```bash
# 自分が作成した見積を削除する場合（必要であれば）
curl -X DELETE {{ uibank_api }}/api/quotes/<loan_id>
```

!!! note
    UiBank は定期的にリセットされるため、放置しても問題はありません。削除は任意です。
