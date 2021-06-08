# Lavoisier
Python library to convert from Ecospold2 format to ILCD format.

Lavoisier is a library exclusive for converting ecoinvent Ecospold2 inventories (`.spold`) to ILCD `.zip` format. The conversion is aimed essentialy for single inventory datasets gathered from EcoEditor or the own researcher's version. Lavoisier's objective is to make possible a more cohesive conversion with less information loss between the two formats and to populate ILCD repositories around the world. Right now, Lavoisier is to be incorpored on the Brazilian Life Cycle Inventory database (namely SICV-Brasil) to make possible the conversion of Ecospold2 datasets from reseach to ILCD format on upload.

The conversion is based on Greendelta's converter https://github.com/GreenDelta/olca-conversion-service, but Lavoisier can overcome some shortcomings from OpenLCA converter such as loss of Pedigree matrix uncertainty and coefficient information, some input flows not converted and loss of all parameters and mathematical equations.

The project is still testing using testpypi and updating frequently, but feedback is wanted and welcomed from users. The pypi repo is currently https://test.pypi.org/project/Lavoisier/. Tests are made mainly on Linux (Ubuntu).

Important information about Ecospold2 and ILCD formats before conversion:

1. It is better to use 'Unknown' files instead of allocated ones:

   ILCD don't handle well linkage information due to the fact that there is no structure for a linking between processes and exchanges embeded in its xml files. Because of that, any conversion would loss linkage information present in the files of ecoinvent linked databases (a.k.a. the input information about the process that produces it is lost). Some way around it is to place additional namespace variables in the ILCD to make it store linking information, as done by a linked file on OpenLCA when it is exported as ILCD, but this is not addressed in this library. 

2. Market datasets and Market Groups datasets:

   Both this datasets are specific of linked ecoinvent databases and are not feasible in ILCD. Lavoisier still can manage to convert such files but there is loss of all linkage information such as original ecoinvent provider, which renders the result not so usefull for real life practicioners. Market datasets are made by the linking process of ecoinvent and are fully complete only within the database it was created.

3. Usefulness of ILCD files

   There are several reasons why one practicioner or repository could use ILCD. The main factor is that it is an OpenSource format and not bounded to any company for its development, but there are more reasons, such as that it produces standalone inventories (inventories with all information required inside it, thus not depending on other files or a database structure to be complete) that are great for data repositories, since they are a collection of different datasets and doesn't have any linking between them. ILCD files are more useful for finding specific processes then creating a hole background database with it, especially with regional datasets that can be connected via software to an existing background database or as a replacement of some of its datasets. 

## Installation

Lavoisier will require the following packages:
+`lxml`
+`cfunits`
 
Since there are problems for a pip installation with the requirements, it is recommended to intall through this process using pip.

+ Install both dependent libraries
```python
pip install lxml
pip install cfunits
```
+ Install Lavoisier
```bash
python3 pip install -i https://test.pypi.org/simple/ Lavoisier
```

The library cfunits can raise some problems since it is based on a C library. See more details on https://ncas-cms.github.io/cfunits/installation.html.

## Functions

Lavoisier has two main functions:
+ For converting files
```python
# Lavoisier.convert_file_to_ILCD(path_to_file, path_to_save_dir)
# Example:
Lavoisier.convert_file_to_ILCD('/home/user_name/Documents/my_spold_file.spold', '/home/user_name/Documents/ILCD_save_folder')
```
+ For converting entire directories of files
```python
# Lavoisier.convert_dir_to_ILCD(path_to_dir, path_to_save_dir)
# Example:
Lavoisier.convert_dir_to_ILCD('/home/user_name/Documents/SpoldDirectory', '/home/user_name/Documents/ILCD_save_folder')
```

It is important to use absolute paths and to make sure that the save path already exists.

## Support

This projects were done by the GYRO laboratory from the Federal University of Technology - Paraná (UTFPR) with the Brazilian Institute of Information in Science and Technology (IBICT) and the help of Embrapa. 
