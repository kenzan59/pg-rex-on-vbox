# PG-REX on VirtualBox

WSL2 上の Ubuntu で ansible-playbook を実行し、VirtualBox 上の仮想マシンを操作して PG-REX 環境を構築するプロジェクトです。

## 概要

このプロジェクトは、以下のコンポーネントを使用して PostgreSQL の高可用性クラスタ環境を構築します。

- **VirtualBox**: 仮想マシンプラットフォーム
- **Vagrant**: 仮想マシン管理
- **Ansible**: 設定管理・自動化
- **Pacemaker**: クラスタ管理
- **PostgreSQL**: データベース
- **PG-REX**: PostgreSQL レプリケーション拡張
- **VirtualBMC**: IPMI エミュレーション

## システム構成図

![PG-REX on VirtualBox](images/PG-REX-on-VirtualBox-System-Architecture.svg)

## 前提条件

### 必要なソフトウェア
- WSL2 Ubuntu
- VirtualBox
- Vagrant
- Ansible
- Python 3

### 必要なリソース
- メモリ: 最小 8 GB（各 VM 4 GB）
- ディスク容量: 最小 20 GB

## 構築手順

### 1. 仮想マシンの作成
```bash
ansible-playbook 10-vagrant.yml
```
RockyLinux 9.5 ベースの 2 台の仮想マシン（pgrex01, pgrex02）を作成します。

### 2. OS 共通設定
```bash
ansible-playbook 20-os-common-settings.yml
```
ネットワーク設定、ロケール設定（ja_JP.UTF-8）、タイムゾーン設定（Asia/Tokyo）を行います。

### 3. VirtualBMC 設定
```bash
ansible-playbook 30-virtualbmc.yml -K
```
STONITH（Shoot The Other Node In The Head）用の VirtualBMC を設定します。

### 4. Pacemaker 設定
```bash
ansible-playbook 40-pacemaker.yml
```
Pacemaker のインストールと設定を行います。

### 5. PostgreSQL 設定
```bash
ansible-playbook 50-postgresql.yml
```
PostgreSQL 17.4 をインストールし、レプリケーション設定を行います。

### 6. PG-REX 運用補助ツール設定
```bash
ansible-playbook 60-pg-rex-operation-tools.yml
```
PG-REX 運用補助ツールをインストールし、クラスタ運用に必要なスクリプトを設定します。

### 7. リソース設定
```bash
ansible-playbook 70-resource-settings.yml -K
```
Pacemakerリソース設定とクラスタ環境の最終設定を行います。

## インストール後の運用手順

### （任意）PG-REX 環境の停止
```bash
ansible-playbook 88-pg-rex-stop.yml
```
PG-REX クラスタを安全に停止します。PG-REX を手動で停止する場合、この手順は必要ありません。

### デモ環境の停止
```bash
ansible-playbook 89-demo-stop.yml -K
```
仮想マシンと VirtualBMC サービスを完全に停止します。

### デモ環境の再起動
```bash
ansible-playbook 80-demo-restart.yml
```
仮想マシンと VirtualBMC サービスを再起動します。PG-REX は手動で起動してください。

## ディレクトリ構成

```
pg-rex-on-vbox/
├── ansible.cfg                           # Ansible設定
├── inventory/pgrex.yml                   # インベントリファイル
├── vagrant/Vagrantfile                   # Vagrant設定
├── 10-vagrant.yml                        # VM作成
├── 20-os-common-settings.yml             # OS設定
├── 30-virtualbmc.yml                     # VirtualBMC設定
├── 40-pacemaker.yml                      # Pacemaker設定
├── 50-postgresql.yml                     # PostgreSQL設定
├── 60-pg-rex-operation-tools.yml         # PG-REX運用ツール
├── 70-resource-settings.yml              # リソース設定
├── 80-demo-restart.yml                   # デモ再起動
├── 88-pg-rex-stop.yml                    # PG-REX停止
├── 89-demo-stop.yml                      # デモ停止
├── ansible-*/                            # Ansibleロール定義
└── README.md                             # このファイル
```

## 重要な注意事項

⚠️ **セキュリティについて**

このプロジェクトは学習・検証目的で設計されており、設定ファイル（`inventory/pgrex.yml`）内にパスワードが平文で記載されています。

**以下の環境での使用は避けてください：**
- 商用環境
- 本番環境
- 不特定多数からアクセス可能な環境
- インターネットに公開されるネットワーク

**本番環境で使用する場合は：**
- パスワードを環境変数に移行
- Ansible Vault による暗号化
- 強固なパスワードへの変更
- 適切なネットワークセキュリティの実装

これらの対策を必ず実施してください。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
