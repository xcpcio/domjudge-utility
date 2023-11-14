# Extract Table From PDF

## Usage

从参赛手册pdf里搞出来xlsx或者csv格式的队伍名单

```bash
git clone https://github.com/xcpcio/domjudge-utility.git

cd domjudge-utility/pdf_parser

pip3 install -U -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

```

## Example

* [48沈阳手册parse示例](../tests/pdf_parser)

```

python3 extract.py -h

python3 extract.py a.pdf --auto/--pages [--format ALL/csv/xlcx] [--output ./output]

```
