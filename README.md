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

### 動作確認時のソフトウェアのバージョン
- Windows 11 Home 24H2
- VirtualBox : 7.1.8
- Vagrant : 2.4.5
- WSL2 : 2.5.7.0
  - Ubuntu : 24.04 LTS
- Proxy なし
  - Proxy 環境下での構築手順は未検証

### 必要なリソース
- メモリ: 最小 8 GB（各 VM 4 GB）
- ディスク容量: 最小 20 GB

## 事前準備

### VirtualBox、Vagrant、WSL2 のインストール

以下のソフトウェアをインストールします。

- VirtualBox
  - https://www.virtualbox.org/wiki/Downloads
- Vagrant
  - https://www.vagrantup.com/downloads
- WSL2
  - https://learn.microsoft.com/ja-jp/windows/wsl/install

### SEP（Symantec Endpoint Protection）の設定

Windows 端末で SEP（Symantec Endpoint Protection）が有効である場合、Ubuntu の `apt` コマンドが失敗します。
以下のリンクを参考に、SEP の設定を「IPトラフィックを許可する」に変更します。

- https://qiita.com/2done/items/65760129ba4792687798

### Ubuntu のインストール

WSL2 で Ubuntu 24.04（以下、Ubuntu）をインストールします。

```powershell
> wsl --install Ubuntu-24.04
```

Ubuntu のインストール後、ユーザー名とパスワードを設定します。

### WSL2 設定ファイルの編集

Ansible Playbook を利用するため、Ubuntu の `/etc/wsl.conf` に `[automount]` の要素を追加します。

```bash
$ sudo vi /etc/wsl.conf
```

`/etc/wsl.conf` の内容：
```ini
[boot]
systemd=true

[user]
default=testuser

[automount]
options="metadata"
```

`[automount]` セクションにより、Windows ファイルシステム（`/mnt/c`）配下でも、playbook や ssh 鍵のパーミッションが正しく設定可能になります。

### Proxy 設定

Proxy 環境下で使用する場合は、以下の設定が必要です。

`/etc/environment`
```
http_proxy=http://PROXY:8080/
https_proxy=http://PROXY:8080/
```

`$HOME/.bashrc`
```bash
export http_proxy=http://PROXY:8080/
export https_proxy=http://PROXY:8080/
export HTTP_PROXY=http://PROXY:8080/
export HTTPS_PROXY=https://PROXY:8080/
export WSLENV=VAGRANT_CWD/p:http_proxy:https_proxy
```

`/etc/apt/apt.conf.d/proxy.conf`
```
Acquire::http::proxy "http://PROXY:8080/";
Acquire::https::proxy "http://PROXY:8080/";
```

`git`
```bash
$ git config --global http.proxy http://PROXY:8080
$ git config --global https.proxy http://PROXY:8080
```

### WSL2 の再起動

設定を反映させるため、WSL2 を一度終了し、起動します。

```powershell
$ exit
> wsl --shutdown
> wsl -d Ubuntu-24.04
```

### Ubuntu のソフトウェアの更新

```bash
$ sudo apt update
$ sudo apt upgrade
```

### Ansible のインストール

```bash
$ sudo apt install software-properties-common
$ sudo add-apt-repository --yes --update ppa:ansible/ansible
$ sudo apt install ansible
$ ansible --version
```

### 追加パッケージのインストール

```bash
$ sudo apt install -y python3 python3-netaddr python3-passlib python3-venv unzip
```

以下、Ubuntu の作業ディレクトリで作業します。

### リポジトリの取得

```bash
$ git clone --recursive https://github.com/kenzan59/pg-rex-on-vbox.git
```

## 構築手順

### 1. 仮想マシンの作成

RockyLinux ベースの 2 台の仮想マシン（pgrex01, pgrex02）を作成します。

```bash
$ ansible-playbook 10-vagrant.yml
```

### 2. OS 共通設定

ネットワーク設定、ロケール設定（ja_JP.UTF-8）、タイムゾーン設定（Asia/Tokyo）を行います。

```bash
$ ansible-playbook 20-os-common-settings.yml
```

### 3. VirtualBMC 設定

STONITH（Shoot The Other Node In The Head）用の VirtualBMC を設定します。

```bash
$ ansible-playbook 30-virtualbmc.yml -K
```

### 4. Pacemaker 設定

Pacemaker のインストールと設定を行います。

```bash
$ ansible-playbook 40-pacemaker.yml
```

### 5. PostgreSQL 設定

PostgreSQL をインストールし、レプリケーション設定を行います。

```bash
$ ansible-playbook 50-postgresql.yml
```

### 6. PG-REX 運用補助ツール設定

PG-REX 運用補助ツールをインストールし、クラスタ運用に必要なスクリプトを設定します。

```bash
$ ansible-playbook 60-pg-rex-operation-tools.yml
```

### 7. リソース設定

Pacemaker リソース設定とクラスタ環境の最終設定を行います。

```bash
$ ansible-playbook 70-resource-settings.yml -K
```

## PG-REX の起動

Windows で Tera Term を起動し、pgrex01 に SSH 接続します。 pgrex01 に SSH 接続する場合は localhost:2231、pgrex02 に SSH 接続する場合は localhost:2232 です。

pgrex01 を Primary ノードとして起動します。

```bash
[vagrant@pgrex01 ~]$ su -
パスワード:
[root@pgrex01 ~]# ls
pm_pcsgen_env.csv  pm_pcsgen_env.sh  pm_pcsgen_env.xml 
[root@pgrex01 ~]# pg-rex_primary_start pm_pcsgen_env.xml
1. Pacemaker および Corosync が停止していることを確認
...[OK]
1. 稼働中の Primary が存在していないことを確認
...[OK]
1. 起動禁止フラグの存在を確認
...[OK]
1. HAクラスタ の作成
Destroying cluster on hosts: 'pgrex01', 'pgrex02'...
pgrex02: Successfully destroyed cluster
pgrex01: Successfully destroyed cluster
Requesting remove 'pcsd settings' from 'pgrex01', 'pgrex02'
pgrex01: successful removal of the file 'pcsd settings'
pgrex02: successful removal of the file 'pcsd settings'
Sending 'corosync authkey', 'pacemaker authkey' to 'pgrex01', 'pgrex02'
pgrex01: successful distribution of the file 'corosync authkey'
pgrex01: successful distribution of the file 'pacemaker authkey'
pgrex02: successful distribution of the file 'corosync authkey'
pgrex02: successful distribution of the file 'pacemaker authkey'
Sending 'corosync.conf' to 'pgrex01', 'pgrex02'
pgrex01: successful distribution of the file 'corosync.conf'
pgrex02: successful distribution of the file 'corosync.conf'
Cluster has been successfully set up.
...[OK]
1. Pacemaker 起動
Starting Cluster...
Waiting for node(s) to start...
Started
...[OK]
1. リソース定義 xml ファイルの反映
CIB updated
...[OK]
Warning: If node(s) 'pgrex02' are not powered off or they do have access to shared resources, data corruption and/or cluster failure may occur
Warning: If node 'pgrex02' is not powered off or it does have access to shared resources, data corruption and/or cluster failure may occur
Quorum unblocked
Waiting for nodes canceled
1. Primary の起動確認
...[OK]
ノード(pgrex01)が Primary として起動しました
[root@pgrex01 ~]#
```

pgrex02 を Standby ノードとして起動します。

```bash
[vagrant@pgrex02 ~]$ su -
パスワード:
[root@pgrex02 ~]# pg-rex_standby_start
1. Pacemaker および Corosync が停止していることを確認
...[OK]
2. 稼働中の Primary が存在していることを確認
...[OK]
3. 起動禁止フラグが存在しないことを確認
...[OK]
4. DB クラスタの状態を確認
4.1 現在のDBクラスタのまま起動が可能か確認
DB クラスタが存在していません
...[NG]
4.2 巻き戻しを実行することで起動が可能か確認
DB クラスタが存在していません
...[NG]
4.3 ベースバックアップを取得することが可能か確認
...[OK]

以下の方法で起動が可能です
b) ベースバックアップを取得してStandbyを起動
q) Standbyの起動を中止する
起動方法を選択してください(b/q) b 
5. IC-LAN が接続されていることを確認
...[OK]
6. Primary からベースバックアップ取得
NOTICE:  all required WAL segments have been archived
23120/23120 kB (100%), 1/1 テーブル空間
...[OK]
7. Primary のアーカイブディレクトリと同期
000000010000000000000002.partial
00000002.history
000000020000000000000003.00000028.backup
000000010000000000000001
000000020000000000000002
000000020000000000000003
...[OK]
8. Standby の起動 (アーカイブリカバリ対象 WAL セグメント数: 1)
Starting Cluster...
...[OK]
9. Standby の起動確認
...[OK]
ノード(pgrex02)が Standby として起動しました
[root@pgrex02 ~]#
```

pgrex01（または pgrex02）で、pcs status --full コマンドを実行します。

```bash
[root@pgrex01 ~]# pcs status --full
Cluster name: pgrex_cluster
Cluster Summary:
  * Stack: corosync (Pacemaker is running)
  * Current DC: pgrex01 (1) (version 2.1.9-1.el9-49aab9983) - partition with quorum
  * Last updated: Fri Jun  6 23:22:21 2025 on pgrex01
  * Last change:  Fri Jun  6 23:09:18 2025 by root via root on pgrex01
  * 2 nodes configured
  * 11 resource instances configured

Node List:
  * Node pgrex01 (1): online, feature set 3.19.6
  * Node pgrex02 (2): online, feature set 3.19.6

Full List of Resources:
  * Clone Set: pgsql-clone [pgsql] (promotable):
    * pgsql     (ocf:linuxhajp:pgsql):   Promoted pgrex01
    * pgsql     (ocf:linuxhajp:pgsql):   Unpromoted pgrex02
  * Resource Group: primary-group:
    * ipaddr-primary    (ocf:heartbeat:IPaddr2):         Started pgrex01
    * ipaddr-replication        (ocf:heartbeat:IPaddr2):         Started pgrex01
  * ipaddr-standby      (ocf:heartbeat:IPaddr2):         Started pgrex02
  * Clone Set: ping-clone [ping]:
    * ping      (ocf:pacemaker:ping):    Started pgrex01
    * ping      (ocf:pacemaker:ping):    Started pgrex02
  * Clone Set: storage-mon-clone [storage-mon]:
    * storage-mon       (ocf:heartbeat:storage-mon):     Started pgrex01
    * storage-mon       (ocf:heartbeat:storage-mon):     Started pgrex02
  * fence1-ipmilan      (stonith:fence_ipmilan):         Started pgrex02
  * fence2-ipmilan      (stonith:fence_ipmilan):         Started pgrex01

Node Attributes:
  * Node: pgrex01 (1):
    * master-pgsql                      : 1000
    * pgsql-data-status                 : LATEST
    * pgsql-master-baseline             : 00000000020000A0
    * pgsql-status                      : PRI
    * ping-status                       : 1
  * Node: pgrex02 (2):
    * master-pgsql                      : 100
    * pgsql-data-status                 : STREAMING|SYNC
    * pgsql-status                      : HS:sync
    * ping-status                       : 1

Migration Summary:

Fencing History:
  * turning off of pgrex02 successful: delegate=a human, client=stonith_admin.58679, origin=pgrex01, completed='2025-06-06 23:07:14.357124 +09:00'

Tickets:

PCSD Status:
  pgrex01: Online
  pgrex02: Online

Daemon Status:
  corosync: active/disabled
  pacemaker: active/disabled
  pcsd: active/enabled
[root@pgrex01 ~]#
```

## 運用手順

### Ubuntu から PostgreSQL への接続

postgresql-client をインストールします。

```bash
$ sudo apt install -y postgresql-common
$ sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
$ sudo apt install -y postgresql-client-17
$ psql --version
psql (PostgreSQL) 17.5 (Ubuntu 17.5-1.pgdg24.04+1)
```

Ubuntu から Service LAN の仮想 IP へ接続します。パスワードは `postgres` です。

```bash
psql -h 192.168.76.201 -U postgres -d postgres
Password for user postgres:
psql (17.5 (Ubuntu 17.5-1.pgdg24.04+1), server 17.4)
Type "help" for help.

postgres=#
```

### PG-REX の停止

PG-REX を停止します。PG-REX を手動で停止する場合、この手順は必要ありません。

```bash
$ ansible-playbook 88-pg-rex-stop.yml
```

### クラスタ環境の停止

仮想マシンと VirtualBMC サービスを完全に停止します。

```bash
$ ansible-playbook 89-demo-stop.yml -K
```

### クラスタ環境の再起動

仮想マシンと VirtualBMC サービスを再起動します。

```bash
$ ansible-playbook 80-demo-restart.yml -K
```

再起動後、PG-REX を手動で起動してください。

### クラスタ環境の完全削除

環境の停止後、環境を完全に削除したい場合は、`vagrant.exe destroy` コマンドで仮想マシンを削除します。

```bash
$ cd vagrant
$ vagrant.exe destroy
    pgrex02: Are you sure you want to destroy the 'pgrex02' VM? [y/N] y
==> pgrex02: Destroying VM and associated drives...
    pgrex01: Are you sure you want to destroy the 'pgrex01' VM? [y/N] y
==> pgrex01: Destroying VM and associated drives...
```

Vagrant によって作成したネットワークについては、VirtualBox GUI 画面 → ツール → ネットワーク を確認し、不要な項目があれば削除してください。

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

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
