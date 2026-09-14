# UiPath Coding Agents ワークショップ（日本語版）— サイト

コーディングエージェント（Claude Code）と `uip` CLI を使って、UiPath のエージェントと Maestro
オーケストレーションを構築する方法を、お客様・パートナー様向けに学んでいただくためのハンズオン教材です。

> **原典について**
> このリポジトリは、UiPath Partner Success が公開している
> [uipath-practice/CodingAgentsCourse](https://github.com/uipath-practice/CodingAgentsCourse)
> を日本語に翻訳したものです。構成・デザイン・演習内容は原典に準拠しています。
> 原典の更新内容は、上流リポジトリを確認のうえ随時反映してください。

[Agentic Practice Workshop](https://github.com/uipath-practice/AgenticPracticeCourse)
と同じ MkDocs ベースのフレームワークを使用しており、次の 3 点が追加されています。
非公開のナレッジベース、設定可能なトレーニング環境、そしてスクリーンショットに加えて
CLI / KB からレッスンを生成する経路です。

## 日本語版としての変更点

| 項目 | 内容 |
|---|---|
| 本文・プロンプト | `docs/` 配下の公開ページをすべて日本語化。プロンプトも日本語ですが、網羅性・具体性は原典と同等に保っています |
| 技術用語 | UiPath の製品名・機能名（Maestro、Orchestrator、Studio Web、Coded Agent など）、CLI コマンド、コード、識別子、スキーマのキー名は英語のまま |
| フォント | 日本語は **Meiryo UI**、欧文は UiPath ブランドの Inter / Nunito（`docs/stylesheets/extra.css` のフォントスタック） |
| サイト設定 | `theme.language: ja`、検索は lunr-languages の日本語トークナイザ（`plugins.search.lang: ja`） |
| 構成 | ページ構成・セクション分け・デザインは原典のまま |

## 仕組み

```
../knowledge-base/  （非公開の SSOT。このリポジトリには含まれません）
        ↓  正確なレッスンを生成するためのコンテキストとして使用
docs/*.md  →  MkDocs が HTML をビルド  →  GitHub Actions  →  gh-pages  →  GitHub Pages
```

| パス | 用途 |
|------|---------|
| `docs/` | 公開ページの本文 — 1 ページにつき `.md` ファイル 1 つ |
| `mkdocs.yml` | サイト設定と **公開用** のナビゲーション |
| `mkdocs.local.yml` | ローカル専用のナビゲーション（作成中のページを含む。gitignore 対象） |
| `main.py` | トレーニング環境の切り替え用変数（staging / prod） |
| `Master/` | 執筆ルールとテンプレート（ベースフレームワークからコピー） |
| `.claude/commands/` | 執筆用のスラッシュコマンド（ベースフレームワークからコピー） |
| `hooks/`, `scripts/` | 2 カラム表示用フック、スクリーンショットのメタデータ処理（コピー） |
| `.github/workflows/deploy.yml` | `main` への push で GitHub Pages に自動デプロイ |

ナレッジベースは、社内向けの内容が公開されることのないよう、意図的にこの公開リポジトリの
**外側**（`../knowledge-base/`）に置いています。

## 初回セットアップ

```bash
# 1. ベースリポジトリから再利用可能なフレームワークファイルを取得
./bootstrap-framework.sh

# 2. 依存関係をインストール
pip install -r requirements.txt

# 3. ローカルでプレビュー（執筆用環境 + WIP ナビ）
COURSE_ENV=staging mkdocs serve -f mkdocs.local.yml
# http://127.0.0.1:8000 を開く

# 4. リリース相当のビルド確認
COURSE_ENV=prod mkdocs build
```

## GitHub への公開

手順の詳細は **[PUBLISH-JA.md](PUBLISH-JA.md)** を参照してください。要点だけ挙げると、

```bash
gh repo create CodingAgentsCourse-JA --public --source=. --remote=origin --push
```

`main` への push で `.github/workflows/deploy.yml` が走り、`gh-pages` ブランチにデプロイされます。
リポジトリの **Settings → Pages** で、ソースが `gh-pages` ブランチになっていることを確認してください。

`site_url` は GitHub Actions がリポジトリ情報から自動的に組み立てて渡すため、`mkdocs.yml` を手で
書き換える必要はありません。

## トレーナー向けメモ（内部向け）

このセクションはトレーナー／ファシリテーター向けです。GitHub Pages にはメールアドレス単位で
アクセスを制限する仕組みがないため、管理者のみが参照すべき内容は `docs/` ではなくこの README に
置いています。この内容を `docs/` に移動したり、`mkdocs.yml` / `mkdocs.local.yml` から参照したり
しないでください。

### 環境とテナントのセットアップ

サイトの `main.py` には `COURSE_ENV` による 2 つのプロファイル（`staging` と `prod`）が定義されており、
レッスン全体で使われる `{{ training_url }}` / `{{ training_tenant }}` マクロを切り替えます。
ただし実際に存在するのは下記のクラウド環境だけで、執筆やテスト用の独立した staging の UiPath
組織／テナントはありません。`staging.uipath.com` は本コースのサポート対象外のため、日本語版では
`staging` プロファイルも `prod` と同じクラウド環境（`cloud.uipath.com`）を指すようにしてあります。
`COURSE_ENV=staging` でのローカルプレビューはこれまでどおり動作しますが、サポート対象外の URL が
レッスン本文に混入することはありません。

| 組織 | URL | テナント | 用途 |
|---|---|---|---|
| `tpenlabs` | https://cloud.uipath.com/tpenlabs | `CodingAgentsPractice` | 唯一の実環境。執筆・テストと、受講者が実際に使う環境の両方を兼ねる（CI は `COURSE_ENV=prod` でビルド） |

すべての演習は、この組織／テナント（`tpenlabs` / `CodingAgentsPractice`）内の単一の共有
Orchestrator フォルダーで実施します。

- **フォルダー名:** `CodingAgentsILT`
- **フォルダーキー:** `c30345cd-5543-46a9-b42b-0354e60b4f15`

デプロイする成果物（エージェント、コーデッドアプリ、Maestro フロー、RPA プロセス）には、すべて
`{YourName}` プレフィックスを付けます（例: `{YourName}LoanUnderwritingAgent`）。同じテナント／
フォルダーを共有する受講者同士で、パッケージ・プロセス・Orchestrator のエンティティが
衝突しないようにするためです。

### 受講者の招待

コホート開始前に、各受講者が自分のメールアドレスでログインできるよう、`tpenlabs` 組織に
招待してください。

1. `tpenlabs` 組織の **Admin** タブを開きます。
2. **Accounts and Local Groups** に移動します。
3. 各受講者をメールアドレスで招待します。
4. 招待した受講者が **CodingAgentsGroup** ローカルグループに追加されていることを確認します。
   これにより `CodingAgentsPractice` テナントと `CodingAgentsILT` フォルダーへのアクセスが
   付与されます。

### 各トレーニングの前に

- [ ] Orchestrator の **CodingAgentsILT** フォルダーに **LoanUnderwriting** ストレージバケットが
      存在することを確認する。RPA のレッスン（申込受付とデータ補完）が結果をここにアップロードするため、
      存在しないと実行が失敗します。

### TODO — 次回のコホートまでに埋める

- [ ] コホート間でリセット／クリーンアップの手順は必要か（共有フォルダーに前回分のプロセス、
      パッケージ、ジョブ、Action Center のタスクが残る）。必要な手順やスクリプトをここに記載する。
- [ ] UiBank の初期データのリセットは必要か。それとも `https://uibank-api.uipath.com` は
      コホートをまたいで安定して共有できるか。
- [ ] ワークショップの途中で受講者の資格情報／テナントアクセスを再発行する必要が生じた場合の
      連絡先は誰か。

### タイムテーブルとアジェンダ

_未整備 — レッスンごとの推奨ペースをここに追記してください。_

### 解答例／期待される出力

_未整備 — 参照実装や期待される結果をここに追記してください。_
