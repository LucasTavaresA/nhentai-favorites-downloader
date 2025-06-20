# nhentai favorites downloader

Downloads your favorites .torrent files from nhentai.net, ignoring existing torrents.

## Usage

```sh
Usage: nhfd <download_dir>
```

## Install

- pipx (recommended):

```sh
git clone https://github.com/lucastavaresa/nhentai-favorites-downloader.git nhfd
cd nhfd
pipx install .
nhfd
```

- Without pipx you can just run the file (after all the python bullshit):

```sh
git clone https://github.com/lucastavaresa/nhentai-favorites-downloader.git nhfd
cd nhfd
python -m venv venv
source venv/bin/activate # check: https://docs.python.org/3.13/library/venv.html#how-venvs-work
pip install -r requirements.txt
python main.py
```
