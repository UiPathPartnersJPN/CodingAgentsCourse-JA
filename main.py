"""
MkDocs-macros モジュール — 演習で使う値をページに注入します。

なぜこれがあるのか
------------------
本コースは**自習用**です。受講者はそれぞれ自分の UiPath テナントで演習するため、
組織名やテナント名を本文に固定で書くことはできません。一方で、演習の中で作る
フォルダー名やバケット名は、コンテンツ側で決めておいたほうが手順が追いやすくなります。

そこで値を 2 種類に分けています。

1. **受講者の環境に依存する値** — 組織名・テナント名。プレースホルダーのままにし、
   受講者が自分の値に読み替えます。
2. **コンテンツが決める値** — 演習用フォルダー名・ストレージバケット名など。
   ここで一度決めれば、本文全体で一貫します。

本文側は変数を参照します。

    Orchestrator の **{{ practice_folder }}** フォルダーを開きます。

環境プロファイル
----------------
    COURSE_ENV=prod    mkdocs build     # Automation Cloud（既定）
    COURSE_ENV=staging mkdocs serve     # 教材を staging で検証するとき

既定は "prod" なので、素のビルドがそのまま公開用になります。
"""

import os

# 受講者が自分の値に読み替えるプレースホルダー
ORG_PLACEHOLDER = "<組織名>"
TENANT_PLACEHOLDER = "<テナント名>"

ENVIRONMENTS = {
    # 既定。受講者は自分の Automation Cloud テナントで演習します。
    "prod": {
        "cloud_host": "https://cloud.uipath.com",
        "env_label": "Automation Cloud",
    },
    # 教材そのものを staging で検証するとき用。
    "staging": {
        "cloud_host": "https://staging.uipath.com",
        "env_label": "検証環境（staging）",
    },
}

# 環境によらず共通の値。演習の中で作成するリソースの名前です。
# 別の名前にする場合はここだけ変えれば、本文全体に反映されます。
COMMON = {
    "practice_folder": "CodingAgentsWorkshop",
    "storage_bucket": "LoanUnderwriting",
    "uibank_api": "https://uibank-api.uipath.com",
    "uibank_swagger": "https://uibank-api.uipath.com/explorer/swagger.json",
    # 学習者からの問い合わせ窓口。公開前に差し替えてください。
}


def define_env(env):
    profile = os.getenv("COURSE_ENV", "prod").lower()
    cfg = ENVIRONMENTS.get(profile, ENVIRONMENTS["prod"])

    for key, value in cfg.items():
        env.variables[key] = value
    for key, value in COMMON.items():
        env.variables[key] = value

    env.variables["course_env"] = profile
    env.variables["org_name"] = ORG_PLACEHOLDER
    env.variables["training_tenant"] = TENANT_PLACEHOLDER

    # ログインコマンド。cloud は --organization、staging 等は --authority を使います。
    if profile == "prod":
        env.variables["login_command"] = (
            f'uip login --organization "{ORG_PLACEHOLDER}" --tenant "{TENANT_PLACEHOLDER}"'
        )
    else:
        env.variables["login_command"] = (
            f'uip login --authority {cfg["cloud_host"]} '
            f'--organization "{ORG_PLACEHOLDER}" --tenant "{TENANT_PLACEHOLDER}"'
        )
