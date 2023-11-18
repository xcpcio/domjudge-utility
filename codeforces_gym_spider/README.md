# Codeforces Spider

## Description

从Codeforces GYM 里把所有submission爬下来。

## Reference

[Codeforces API文档](https://codeforces.com/apiHelp)

## Prerequisite

到 https://codeforces.com/settings/api 创建一个新的key/secret pair，保存到credential.json中。用于调用Codeforces API获取submissions list

## Usage

```bash
git clone https://github.com/xcpcio/domjudge-utility.git

cd domjudge-utility/codeforces_gym_spider

pip3 install -U -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

python3 gao.py -h

# Initial Seeding
python gao.py <GYM ID> [--output <Output path>]

# Incremental Seeding After Failure
python gao.py <GYM ID> --submissions <submissions list that can be found under output path> [--output <Output path>]


```
