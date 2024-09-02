#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 13 16:26:36 2024

@author: jotape42p
"""

import fsspec
from pathlib import Path
import shutil
path = Path(Path(__file__).parent, 'Lavoisier_Default_Files/ILCD_EF30_ElementaryFlows')

def download():
    
    if path.exists():
        return
    
    path.mkdir(exist_ok=True, parents=True)
    try:
        fs = fsspec.filesystem("github", org="JosePauloSavioli", repo="Lavoisier")
        fs.get(fs.ls("src/Lavoisier/Lavoisier_Default_Files"), path.as_posix(), recursive=True)
    except:
        shutil.rmtree(path)
