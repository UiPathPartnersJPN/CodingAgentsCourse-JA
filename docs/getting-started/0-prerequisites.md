# 0. 前提を準備する

コースを始める前に、**UiPath テナント**と**ローカルのツール**を準備します。**所要 30 分程度です。**

---

## UiPath テナント

ご自身の UiPath 組織・テナントで演習します。演習に使う組織とテナントを決めて、**サインインできる状態**にしておいてください。

!!! success "第1部は、一般的な開発者向け権限だけで完走できます"
    **Automation Developer**（フォルダーロール）と **Allow to be Automation Developer**（テナントロール）があれば、
    第1部は最後まで進められます。開発者には通常すでに割り当てられているため、管理者への依頼は不要です。

!!! warning "第2部には、管理者による事前設定が必要です"
    第2部ではフォルダーやストレージバケットの作成、ソリューションのデプロイを行うため、**既定の開発者向け権限では足りません。**

    第2部に進む前に、[管理者向け：テナントの事前設定](../admin-setup.md)のページを**管理者の方へお渡しください。** 所要 10 分程度の作業です。

自分に何のロールが割り当てられているかは、CLI を導入したあと（[1. CLI とスキルをインストールする](1-install-the-cli-and-skills.md)以降）に確認できます。

```bash
uip admin authorization check-access <自分のメールアドレス> --output json
```

---

## ローカルのツール

!!! note "すべてを今すぐ入れる必要はありません"
    | ツール | 必要になるタイミング |
    |---|---|
    | Node.js | **第1部 レッスン1 から**（UiPath CLI に必要） |
    | Python | 第2部 レッスン1 |
    | .NET SDK | 第2部 レッスン4 |
    | UiPath Studio | 第2部 レッスン4 |

    先に進みたい場合は、**Node.js だけ入れて**第1部を始めても構いません。

---

## Node.js（LTS）

UiPath CLI と React アプリのビルドに必要です。

1. **[nodejs.org](https://nodejs.org)** から LTS 版をダウンロードします
2. 確認します

```bash
node --version
npm --version
```

!!! tip "npm が古い場合"
    Node.js の LTS に同梱される npm で問題ありませんが、古いバージョンが残っている場合は更新してください。

    ```bash
    npm install -g npm@latest
    ```

---

## Python 3.11 〜 3.13

第2部のコーデッドエージェントに必要です。

1. **[python.org/downloads](https://www.python.org/downloads/)** からダウンロードします。**Windows の場合はインストール時に「Add Python to PATH」にチェックを入れてください**
2. 確認します

```bash
python --version
```

!!! warning "バージョンに注意してください"
    UiPath のコーデッドエージェントがサポートするのは **3.11 / 3.12 / 3.13** です。
    それより新しいバージョンだと `No compatible Python installation found` で失敗します。

### uv（推奨）

コーデッドエージェントの依存関係管理に使います。コーディングエージェントが自動で導入することもありますが、先に入れておくとスムーズです。

=== "Windows (PowerShell)"
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

=== "Mac / Linux"
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

確認: `uv --version`

---

## .NET SDK 8.0

UiPath Studio のプロジェクトをビルド・実行するために必要です。

1. **[dotnet.microsoft.com/download/dotnet/8.0](https://dotnet.microsoft.com/download/dotnet/8.0)** からダウンロードします。Mac の場合は Homebrew でもインストールできます

   ```bash
   brew install --cask dotnet-sdk
   ```

2. 確認します。出力に `8.x.x` が表示されるはずです

```bash
dotnet --list-sdks
```

!!! tip "Windows — .NET が PATH に入っているか確認してください"
    インストール後に `dotnet` が認識されない場合は、PowerShell で PATH に手動で追加します。
    ```powershell
    $env:Path = "C:\Program Files\dotnet;$env:Path"
    dotnet --list-sdks
    ```
    恒久的に設定するには、システムの環境変数に追加してください。

---

## UiPath Studio

生成された XAML ワークフローを開き、実行し、デバッグするために必要です（第2部 レッスン4）。

!!! warning "Studio は Windows 専用です"
    Mac / Linux では UiPath Studio Desktop を実行できません。

    Mac / Linux をお使いの場合、**第2部 レッスン4 以外はすべて実行できます。** レッスン4 も `uip rpa` の CLI でビルド・実行・公開まで行えますが、**ワークフローを画面で確認することはできません。**

1. **[uipath.com/start-trial](https://www.uipath.com/start-trial)** からダウンロードします
2. UiPath アカウントでサインインし、Studio が起動することを確認します

---

## コーディングエージェント

どれか 1 つを選んでください（複数入れても構いません）。

```bash
# Claude Code (Anthropic)
npm install -g @anthropic-ai/claude-code

# Codex CLI (OpenAI)
npm install -g @openai/codex
```

確認: `claude --version` または `codex --version`

インストールしたら、**サインインまで済ませておいてください。**

!!! tip "Claude Code のインストールでエラーが出る場合"
    スクリプト実行権限のエラーでインストールが失敗する場合は、次を実行してください。
    ```bash
    npm config set allow-scripts=@anthropic-ai/claude-code --location=user
    ```
    そのうえで、インストールコマンドを再実行します。

---

## Git（任意）

本コースの手順に Git は必須ではありません。ただし、生成されたコードをバージョン管理したい場合は入れておくと便利です。

=== "Windows — winget（最短）"

    ```powershell
    winget install --id Git.Git -e --source winget
    ```

    利用規約への同意を求められたら `Y` を入力して Enter を押します。

=== "Windows — インストーラー"

    1. **[git-scm.com/download/win](https://git-scm.com/download/win)** にアクセスします
    2. ダウンロードしたファイルを実行します
    3. すべて既定値のままインストーラーを進めます。**"Adjusting your PATH environment"** の画面では、真ん中の選択肢 *"Git from the command line and also from 3rd-party software"* が選ばれていることを確認してください（これが既定値です）

=== "Mac"

    ```bash
    brew install git
    ```

!!! warning "PATH の変更は新しいウィンドウにしか反映されません"
    インストール後は、**開いているターミナルをすべて閉じて**から新しいウィンドウで確認してください。

    ```bash
    git --version
    ```

---

## 確認

次がすべて表示されれば準備完了です（Python / .NET / Studio は第2部までに揃っていれば構いません）。

```bash
node --version
npm --version
python --version
dotnet --list-sdks
claude --version
```

[1. CLI とスキルをインストールする](1-install-the-cli-and-skills.md) に進んでください。
