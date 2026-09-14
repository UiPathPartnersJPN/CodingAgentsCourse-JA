# 公開手順（GitHub Pages）

このリポジトリを自分の GitHub アカウントで公開するための手順です。所要時間は 5 分ほどです。

## 0. 前提

- `git` がインストールされていること
- GitHub の [`gh` CLI](https://cli.github.com/)（推奨）、またはブラウザでの GitHub 操作

このリポジトリには翻訳前の履歴（原典の 24 コミット）がそのまま含まれています。`git log` で原典の
変更履歴をたどれるので、上流の更新を取り込みたくなったときに差分を追いやすくなっています。

---

## 1. `gh` CLI を使う場合（推奨）

zip を展開したフォルダーで、次を実行します。

```bash
cd CodingAgentsCourse-ja

# 認証（初回のみ。ブラウザが開きます）
gh auth login

# リポジトリを作成して push
gh repo create CodingAgentsCourse-JA --public --source=. --remote=origin --push
```

これだけで完了です。push をトリガーに `.github/workflows/deploy.yml` が走り、サイトがビルドされて
`gh-pages` ブランチにデプロイされます。

## 2. `gh` CLI を使わない場合

1. GitHub 上で、`CodingAgentsCourse-JA` という名前の **空の public リポジトリ** を作成します
   （README・.gitignore・ライセンスは追加しないでください）。
2. zip を展開したフォルダーで、次を実行します。

```bash
cd CodingAgentsCourse-ja
git remote add origin https://github.com/<あなたのユーザー名>/CodingAgentsCourse-JA.git
git branch -M main
git push -u origin main
```

---

## 3. GitHub Pages を有効にする

初回の push から 1〜2 分ほどでワークフローが完了し、`gh-pages` ブランチが作成されます。その後、

1. リポジトリの **Settings → Pages** を開きます
2. **Source** を **Deploy from a branch** にします
3. **Branch** を `gh-pages` / `(root)` に設定して **Save** をクリックします

数分後、次の URL で公開されます。

```
https://<あなたのユーザー名>.github.io/CodingAgentsCourse-JA/
```

**Actions** タブでビルドの成否を確認できます。

!!! note
    公開 URL（`site_url`）は GitHub Actions がリポジトリ情報から自動的に組み立てて渡すため、
    `mkdocs.yml` を手で書き換える必要はありません。

---

## 4. ローカルでプレビューする

```bash
pip install -r requirements.txt
mkdocs serve
# http://127.0.0.1:8000 を開く
```

内容を編集して `main` に push するたびに、サイトは自動的に再デプロイされます。

---

## 5. リポジトリ名を変えたい場合

`CodingAgentsCourse-JA` 以外の名前にしても、上記の手順はそのまま使えます。公開 URL も自動的に
追従します。変更が必要なのは、手順 1 または 2 のリポジトリ名だけです。

---

## 原典の更新を取り込む

```bash
git remote add upstream https://github.com/uipath-practice/CodingAgentsCourse.git
git fetch upstream
git log --oneline HEAD..upstream/main        # 原典側の新しいコミットを確認
git diff HEAD..upstream/main -- docs/        # 本文の変更点を確認
```

差分を確認したうえで、必要な箇所だけを日本語版に反映してください。翻訳コミットは 1 つにまとめて
あるため、`git diff` で「原典 → 日本語版」の対応が追いやすくなっています。
