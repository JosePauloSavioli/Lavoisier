<img src="https://github.com/JosePauloSavioli/IBICT-converter/blob/master/static/Lavoisier.png" alt="Logo Lavoisier" width="170" length="200" />


Python library for conversions between Life Cycle Assessment (LCA) inventory formats. Currently, it does both ways of conversion between EcoSpold 2 and ILCD 1 formats. Other versions and other dataset types are to be included due time as Lavoisier is a work in progress.

Lavoisier's objective is to make possible a cohesive conversion with lower loss of information between LCA inventory formats. This objective is in line with the efforts in the LCA community for a higher interoperability within data formats, in a way having a dataset of one inventory format does not limit its usability with other inventory formats.

Right now, Lavoisier is incorpored in the Brazilian Life Cycle Inventory database (namely SICV-Brasil) to make possible the conversion of Ecospold 2 datasets from Brazilian reseach to ILCD 1 format on the upload process.

The field conversion is based on Greendelta's converter https://github.com/GreenDelta/olca-conversion-service, but Lavoisier can overcome major shortcomings from OpenLCA converter, for example it can convert all parameterization model (variables and equations), can convert all possible flows with unit conversion correcting values and uncertainty and considers Pedigree Matrix influence in uncertainty.

The project is still updating frequently and feedback is welcomed. The main branch has the most stable version, while the development branch has the latest updates of the library. Tests are made mainly on Linux (Ubuntu).

## Installation

Lavoisier will require the following packages:
+ `pathlib` to help with file and diretory paths
+ `pint` to help with unit conversion
+ `xmltodict` to help with XML parsing and `ijson` to help with JSON parsing
+ `openturns` to help with uncertainty conversion
+ `pycryptodome` to help with UUID conversion

For the use of Lavoisier as an API service, it will require:
+ `fastapi` as the API framework
+ `uvicorn` as the server
+ `python-multipart` as a complement to fastapi
 
To install the dependencies beforehand, use the `requirements.txt` file, or just install the pypi version of Lavoisier.

+ Install dependent libraries
```bash
pip install -r requirements.txt
```
+ Install Lavoisier
```bash
pip install Lavoisier
```

If you want to install it via github clone, just execute the `setup.py` file. In the case of uninstalling or trying to install it by pip again, it is recomended to run as administrator or sudo, since problems related to `.pyc` files could raise. Follow the steps bellow:

+ Clone github repository
```bash
git clone https://github.com/JosePauloSavioli/Lavoisier
```
+ Go to repository and install the library
```bash
cd path/to/cloned/library
python3 setup.py install
```

## Conversion

Lavoisier works by creating a `Converter` class using the method `get_converter(input_: tuple, output: tuple, path: str, save_path: str)`. The `input_` and `output` tuples are the format and elementary flow mapping to be used in conversion. Currently, available format options are `"ILCD1"` and `"EcoSpold2"` and available elementary flow mappings are `"EF3.0"` for ILCD and `"ecoinvent3.7"` for EcoSpold 2.

The `Converter` class has the information about the two formats and is modifiable. The class attribute `elem_flow_mapping` can be changed to include a user-specific elementary flow mapping path to a file, but the file must be formatted such as GLAD's mapping files (GitHub: `UNEP-Economy-Division/GLAD-ElementaryFlowResources`). Other attributes can be set depending on the conversion being carried out. To see these attribute options one can print the converter created with `get_converter`.

To convert a dataset using the `Converter`, one can use the `convert(mode: str)` method at any given time. The `mode` is an entry to specify if the conversion is to single file(s) of the output format (`to file`) or to a single database (`to database` - available only for EcoSpold2 to ILCD1 conversion).

For example, to convert a file and a directory of files from EcoSpold 2 to ILCD 1:
```python

# To convert a file
converter = get_converter(("EcoSpold2", "ecoinvent3.7"), ("ILCD1", "EF3.0"),
                           "path_to_file", "path_to_save_directory")
converter.convert("to_file")

# To convert a directory with files
converter = get_converter(("EcoSpold2", "ecoinvent3.7"), ("ILCD1", "EF3.0"),
                           "path_to_directory", "path_to_save_directory")
converter.convert("to_file")

# To see the available options
print(converter)
```

## Support

This project was developed at the Center for Life Cycle Sustainability Assessment (GYRO) of the Federal University of Technology - Paraná (UTFPR) with the support of the Brazilian Institute of Information in Science and Technology (IBICT). It began with the support of REAL (Resource Efficiency through Application of Life Cycle Thinking) of the UN Environment and The Life Cycle Initiative funded by the European Commission. 

-> GYRO website: http://gyro.ct.utfpr.edu.br

Code developed by José Paulo Pereira das Dores Savioli. Logo created by Larissa Ugaya Mazza.

<img src=https://github.com/JosePauloSavioli/IBICT-converter/blob/master/static/logo%20gyro_email%20padr%C3%A3o.png alt="Logo GYRO" width="80" length="200" /><img src=https://github.com/JosePauloSavioli/IBICT-converter/blob/master/static/utfpr.png alt="Logo UTFPR" width="200" length="200" /><img src="https://github.com/JosePauloSavioli/IBICT-converter/blob/master/static/IBICT.png" alt="Logo IBICT" width="170" length="200" />
