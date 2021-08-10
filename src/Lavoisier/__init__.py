#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 24 07:11:23 2021

Initialization of primary modules of Lavoisier converter

@author: jotape42p
"""

from .conversion_caller import convert_file_to_ILCD, convert_dir_to_ILCD

__version__ = "2.0.14"
__title__ = "Lavoisier"
__summary__ = "This package converts Life Cycle Assessment format Ecospold2 (ecoinvent format) to ILCD (jrc format). Files can be converted by file using the 'convert_file_to_ILCD' function or entire directory using the 'convert_dir_to_ILCD' function. Lavoisier is developed by the Center of Life Cycle Sustainable Assessment (Gyro) of the Federal University of Technology - Paraná (UTFPR) and the  Brazilian Institute for Information in Science and Technology (IBICT)"
__author__ = "José Paulo Pereira das Dores Savioli"
__author_email__ = "jsavioli@alunos.utfpr.edu.br"
__license__ = "GNU General Public License v3 (GPLv3)"
