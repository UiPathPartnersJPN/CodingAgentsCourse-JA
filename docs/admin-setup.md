# 管理者向け：テナントの事前設定

!!! info "このページは受講者向けではありません"
    本コースの**第2部**を受講者が進めるには、UiPath テナントの管理者による事前設定が必要です。
    **このページをそのまま管理者の方へお渡しください。** 所要 10 分程度です。

    **第1部は、この設定なしで進められます。** 一般的な開発者向け権限（Automation Developer）があれば完走できます。

---

## なぜ必要なのか

第2部では、受講者がストレージバケットを作成し、作ったソリューションとコーデッドアプリをデプロイします。
これらは**開発者向けの既定ロールには含まれていない**操作です。フォルダーの作成に至っては、
テナント管理者でなければ実行できません。

| 第2部で行う操作 | 必要な権限 | Automation Developer に含まれるか |
|---|---|---|
| フォルダーの作成 | `Folders – 作成`（テナント） | **いいえ** |
| ストレージバケットの作成 | `Storage Buckets – 作成` | **いいえ**（表示のみ） |
| ソリューションのデプロイ | `Solution deployments – 作成` | **いいえ** |
| コーデッドアプリのテナント公開 | `App Versions – 作成` | **いいえ**（表示のみ） |

!!! note "受講者にテナント管理者権限は不要です"
    以下の手順は、**受講者を Orchestrator 管理者にせずに**演習を完走させるためのものです。
    受講者の作業は、手順1 で作るフォルダーの中に閉じます。

---

## 1. 演習用フォルダーを作る

受講者はこのフォルダーの中だけで作業します。**名前は `{{ practice_folder }}` にしてください。**
コース本文がこの名前を前提に書かれています。

=== "Orchestrator の画面"

    1. **Orchestrator** → 左メニューの **フォルダー** を開きます
    2. **追加** から `{{ practice_folder }}` という名前でフォルダーを作成します

=== "CLI"

    ```bash
    uip or folders create "{{ practice_folder }}" --output json
    ```

!!! warning "サブフォルダーにしないでください"
    必ず**ルート直下**に作ってください。サブフォルダーにすると、受講者が実行するコマンドの
    `--folder-path` に完全修飾パス（`親/{{ practice_folder }}`）が必要になり、**本文の手順が
    そのままでは通らなくなります。**

!!! tip "別の名前にする場合"
    受講者に**その名前を伝えてください。** 本文中の `{{ practice_folder }}` をすべて
    読み替えてもらう必要があります。

---

## 2. カスタムロールを 1 つ作る

コーデッドアプリをテナントに公開するための権限です。**この権限だけを持つ既定ロールが存在しない**ため、
ロールを 1 つ作ります。

=== "Orchestrator の画面"

    1. **テナント** → **管理** → **ロール** → **追加**
    2. 名前を `Coded App Publisher`、種類を **テナント** にします
    3. **App Versions** の **作成** にチェックを入れて保存します

=== "CLI"

    ```bash
    uip or roles create --name "Coded App Publisher" --type Tenant --output json
    ```

    返ってきた `Key` を使って権限を追加します。

    ```bash
    uip or roles update <Key> --add-permissions "AppVersions.Create" --output json
    ```

---

## 3. 受講者にロールを割り当てる

受講者 1 人につき、次の 5 つを割り当てます。

| ロール | 種類 | 割り当て先 | 用途 |
|---|---|---|---|
| **Automation Developer** | フォルダー | `{{ practice_folder }}` | 開発作業全般 |
| **Allow to be Automation Developer** | テナント | — | パッケージとソリューションの公開（**第1部から必要**） |
| **Folder Administrator** | フォルダー | `{{ practice_folder }}` | ストレージバケットの作成・削除 |
| **Solutions Administrator** | テナント | — | ソリューションのデプロイ |
| **Coded App Publisher** | テナント | — | 手順2 で作成したもの |

!!! note "上の 2 つは第1部でも必要です"
    `Automation Developer` と `Allow to be Automation Developer` は対になっており、開発者には
    通常すでに割り当てられています。**この 2 つだけで第1部は完走できます。**
    残りの 3 つが、第2部のために追加で必要なものです。

=== "Orchestrator の画面"

    - **テナントロール**（Allow to be Automation Developer / Solutions Administrator / Coded App Publisher）
      **テナント** → **管理** → **アカウントとグループ** から受講者を選び、ロールを割り当てます

    - **フォルダーロール**（Automation Developer / Folder Administrator）
      `{{ practice_folder }}` フォルダーを開き、**設定** → **ユーザーの割り当て** から受講者を追加します

=== "CLI"

    ```bash
    # ロールのキーを調べる
    uip or roles list --output table

    # 受講者のユーザーキーを調べる
    uip or users list --output table

    # テナントロール
    uip or users assign-roles <ユーザーキー> \
      --role-keys "<Allow to be Automation Developer>,<Solutions Administrator>,<Coded App Publisher>"

    # フォルダーロール
    uip or users assign --user-key <ユーザーキー> --folder-path "{{ practice_folder }}" \
      --role-keys "<Automation Developer>,<Folder Administrator>"
    ```

---

## 4. 受講者側で確認する

受講者が次を実行すると、自分に何が割り当てられているかを確認できます。

```bash
uip admin authorization check-access <受講者のメールアドレス> --output json
```

---

## ライセンスとテナントの要件

ロールとは別に、次が必要です。

| 項目 | 内容 |
|---|---|
| **ユーザーライセンス** | **Automation Developer**（名前付きユーザー）。第2部 レッスン4 は UiPath Assistant 経由のアテンデッド実行を行うため、アテンデッド実行権を含むライセンスが必要です |
| **プラットフォームティア** | Maestro は **Basic ティアでは利用できません。** Standard または Enterprise が必要です |
| **消費ユニット** | エージェントの実行ごとに LLM を呼び出します。Community / Trial では**組織あたり 1 日 500 LLM コール**の上限があります |
| **リージョン** | コーデッドアプリは**スイス・UAE・一部の US / EU リージョンでは利用できません。** Public Sector も対象外です |

テナントで有効になっているサービスは、次で確認できます。

```bash
uip admin organizations services list --output table
```

`apps` `agents` `studio` が **Enabled** であることを確認してください。

---

## 片付け

コース終了後に演習リソースを削除する手順は、[演習環境の片付け](cleanup.md)にあります。

!!! note "フォルダー自体の削除は管理者が行います"
    受講者はフォルダーの中身（プロセス・バケット・デプロイ）を片付けられますが、**フォルダーそのものは削除できません。**
    次回も使う場合は、手順2 のカスタムロールとあわせてそのまま残して構いません。
