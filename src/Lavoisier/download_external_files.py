#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 16:26:36 2024

@author: jotape42p
"""

import urllib.request
import tempfile
import tarfile
import zstandard as zstd
import shutil
import hashlib
from pathlib import Path

data_version = "v1.0.0"
url = f"https://github.com/JosePauloSavioli/Lavoisier/releases/download/data-{data_version}/conversion-data-{data_version}.tar.zst"
hash_url = f"https://github.com/JosePauloSavioli/Lavoisier/releases/download/data-{data_version}/conversion-data-{data_version}.tar.zst.sha256"

path = Path(__file__).resolve().parent / "Lavoisier_Default_Files"

def verify_sha(achieve, hashfile):
    expected_hash = hashfile.read_text().strip()
    sha256 = hashlib.sha256()
    
    with achieve.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)
    received_hash = sha256.hexdigest().lower()
    
    if received_hash != expected_hash:
        print(f"{expected_hash}")
        raise RuntimeError(f"SHA-256 verification failed. {expected_hash} != {received_hash}")

def install_default_files():
    print("Downloading Lavoisier default files...")

    with tempfile.TemporaryDirectory() as tmpdir:
        hashfile = Path(tmpdir) / "hash.sha256"
        archive = Path(tmpdir) / f"conversion-data-{data_version}.tar.zst"
        extract = Path(tmpdir) / "extracted"
        
        urllib.request.urlretrieve(url, archive)
        urllib.request.urlretrieve(hash_url, hashfile)
        
        verify_sha(archive, hashfile)
        
        with archive.open("rb") as compressed:
            decompressor = zstd.ZstdDecompressor()
            with decompressor.stream_reader(compressed) as reader:
                with tarfile.open(fileobj=reader, mode="r|") as tar:
                    tar.extractall(extract, filter="data")

        source = extract / "Lavoisier_Default_Files"
        shutil.move(str(source), str(path))

    print("Lavoisier default files successfully downloaded")

