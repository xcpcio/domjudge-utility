# Extract Table From PDF

## Usage

从参赛手册pdf里搞出来xlsx或者csv格式的队伍名单

```bash
git clone https://github.com/xcpcio/domjudge-utility.git

cd domjudge-utility/pdf_parser

pip3 install -U -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# make a copy of `config-example.yaml` and rename it to `config.yaml`
# change the appropriate configuration in `config.yaml` to match your DOMjudge configuration

# python3 extract.py a.pdf --auto/--pages [--format ALL/csv/xlcx] [--output ./output]
python3 extract.py -h
```
