# imgfile

A tool to compress folders or single files into PNG images and extract them back.

## how to use

First, install dependencies:
```bash
pip install -r requirements.txt
```

## GUI

To run the graphical application:
```bash
python app.py
```

## CLI

To run the command-line interface:
```bash
python cli.py
```

The CLI supports:
- Compressing folders or single files to PNG
- Extracting PNG to folders or single files
- Multiple compression methods: lzma, bz2, zlib, zip_lzma, zip_bz2
