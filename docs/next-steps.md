# 次のステップ

!!! tip "コースはこれで終わりです"

    `uip` CLI のセットアップから始まり、エージェントの構築、そして Maestro でのオーケストレーションまでを、コーディングエージェントと一緒に進めてきました。

## 引き続き構築する

- 自分のユースケースとデータで、各レッスンをもう一度やってみましょう。本コースの UiBank は共有のデモ API ですが、**自社の API や Data Fabric エンティティに差し替える**と、そのまま社内の検証に使えます
- 同じ UiPath スキルを使って、別のコーディングエージェント（Cursor、Gemini CLI、Codex）を試してみましょう
- Maestro ソリューションに、エージェントや人的判断のステップを追加して拡張してみましょう
- 片付けがまだなら、[演習環境の片付け](cleanup.md)でテナントに残ったリソースを削除してください

## もっと詳しく

| リソース | 説明 |
|----------|------|
| [UiPath CLI ドキュメント](https://docs.uipath.com/uipath-cli) | `uip` CLI の公式リファレンスとハウツーガイド |
| [UiPath skills（GitHub）](https://github.com/UiPath/skills) | コーディングエージェント向け UiPath スキルのソース |
| [Coding Agents（UiPath）](https://www.uipath.com/developers/coding-agents) | 製品概要 |
| [UiPath Maestro ドキュメント](https://docs.uipath.com/maestro) | Flow / BPMN / Case Management のリファレンス |
| [UiPath Python SDK](https://uipath.github.io/uipath-python/) | コーデッドエージェントで使う SDK のリファレンス |
| [UiPath TypeScript SDK](https://www.npmjs.com/package/@uipath/uipath-typescript) | コーデッドアプリで使う SDK |
| [Action Center ドキュメント](https://docs.uipath.com/action-center) | 人的タスク（Human-in-the-Loop）のリファレンス |

## フィードバック

`uip` CLI や UiPath スキル自体の不具合は、次のコマンドで UiPath に直接報告できます。

```bash
uip feedback send
```
