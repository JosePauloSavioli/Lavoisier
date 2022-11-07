#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 15 11:50:24 2022

@author: jotape42p
"""

import os
import uuid
import csv
import json
import shutil
from abc import ABC
from pathlib import Path
from Crypto.Cipher import AES
from binascii import unhexlify, hexlify

# key = b'_Lavosier_ECS2_/'
def uuid_from_uuid(u, key, type_):
    
    iv = key[::-1]
    
    u_ = u.replace("-", "")
    u12 = u_[12]
    u16 = u_[16]
    u_ = u_[0:12]+u_[13:]
    u_ = u_[0:15]+u_[16:]
    d = unhexlify(u_)
    cipher = AES.new(key, AES.MODE_CFB, iv)
    if type_ == "to_ILCD1":
        new_u = hexlify(cipher.encrypt(d)).decode()
    elif type_ == "to_ECS2":
        new_u = hexlify(cipher.decrypt(d)).decode()
    new_u = new_u[0:8]+"-"+new_u[8:12]+"-"+u12+new_u[12:15]+"-"+u16+new_u[15:18]+"-"+new_u[18:30]
    return new_u

def uuid_from_string(text):
    
    seed = "2aaa7703-9d0a-4c10-b235-213cb2c70b35"  # Never change this
    if seed == "2aaa7703-9d0a-4c10-b235-213cb2c70b35":
        return str(uuid.uuid3(uuid.UUID(f"{seed}"), text))
    else:
        raise Exception(
            f"UUID seed is incorrect [{seed}], correct it to '2aaa7703-9d0a-4c10-b235-213cb2c70b35'")

def ensure_list(x, ensure_text=False):
    if isinstance(x, dict):
        if bool(x):
            if ensure_text:
                return [x] if x.get('#text') else []
            return [x]
        else:
            return []
    else:
        if ensure_text:
            return [n for n in x if n.get('#text')]
        return x

# Credits for Michael for the idea of that function
# https://blogs.blumetech.com/blumetechs-tech-blog/2011/05/faster-python-file-copy.html
def _copy_file(src, dst, buffer_size=10485760):
    buffer_size = min(buffer_size,os.path.getsize(src))
    if(buffer_size == 0):
        buffer_size = 1024

    with open(src, 'rb') as fsrc:
        with open(dst, 'wb') as fdst:
            shutil.copyfileobj(fsrc, fdst, buffer_size)

def copy_file(save_path, default_files_path, folder, id_):
    path = Path(Path(__file__).parent.parent.resolve(), default_files_path, id_+".xml")
    folder_path = Path(save_path, folder)
    folder_path.mkdir(exist_ok=True)
    _copy_file(str(path), str(folder_path)+'/'+id_+".xml")

class FieldMapping(ABC):

    _uuid_conv_spec: tuple
    _default_elem_mapping: Path
    _default_class_mapping: Path
    _save_dir = None

    _elem_mapping = None
    _class_mapping = None

    @staticmethod
    def _dict_from_file(filepath, id_=None):
        if filepath.suffix == '.csv':
            with open(Path(Path(__file__).parent.resolve(), filepath), 'r') as f:
                d = {}
                for d_ in csv.DictReader(f, delimiter=","):
                    n = d_.pop(id_)
                    d[n] = d_
                return d
        elif filepath.suffix == '.json':
            with open(Path(Path(__file__).parent.parent.resolve(), filepath), 'r') as f:
                d = json.load(f)
            return d
