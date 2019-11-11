# IBICT-converter
Python converter from Ecospold2 format to ILCD.

The project aim is to convert xml data from Ecospold2 files (from ecoinvent association) to ILCD format (also xml - from jrc - open source) in the most faithful manner for updating the IBICT platform on Life Cycle Assessment datasets (called SICV), letting it import Ecospold2 format onto an ILCD database.

The convertion is in the basic format with only direct convertions done between the format fields.

A portuguese excel sheet is presented with the desired correspondence between fields in the coding, also the xsd files of each format are presented.

The convertion is based on Greendelta's converter https://github.com/GreenDelta/olca-conversion-service
