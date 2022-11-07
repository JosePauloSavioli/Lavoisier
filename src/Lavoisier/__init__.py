#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  7 01:56:19 2022

@author: jotape42p
"""

from .converter import (
    get_converter,
    SingleDatasetConverter,
    SingleHierarchicalCompressedDatasetConverter,
    MultipleSingleDatasetConverter,
    MultipleHierarchicalCompressedDatasetConverter,
    MultipleDatasetConverter,
    ConverterFactory
)

__version__ = "2.0.15"
__title__ = "Lavoisier"
__summary__ = "This package converts Life Cycle Assessment inventory formats. Lavoisier is developed by the Center of Life Cycle Sustainable Assessment (Gyro) of the Federal University of Technology - Paraná (UTFPR) and the  Brazilian Institute for Information in Science and Technology (IBICT)"
__author__ = "José Paulo Pereira das Dores Savioli"
__author_email__ = "jsavioli@alunos.utfpr.edu.br"
__license__ = "GNU General Public License v3 (GPLv3)"
