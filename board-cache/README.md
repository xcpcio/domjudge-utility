# domjudge-utility/board-cache

## Usage

```bash
git clone https://github.com/XCPCIO/domjudge-utility.git

cd domjudge-utility/board-cache

pip3 install -U -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# make a copy of `config-example.yaml` and rename it to `config.yaml`
# change the appropriate configuration in `config.yaml` to match your DOMjudge configuration

python3 main.py
```

Next, you will get the list file in static HTML format in the `saved_dir` directory.

You just need to use an HTTP server, such as nginx, to enable users to access these static files.
