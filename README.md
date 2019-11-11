# IBICT-converter
Python converter from Ecospold2 format to ILCD.

The project aim is to convert xml data from Ecospold2 files (from ecoinvent association) to ILCD format (also xml - from jrc - open source) in the most faithful manner for updating the Brazilian platform on Life Cycle Assessment datasets (called SICV - hosted by IBICT), letting it import the Ecospold2 format.

The conversion is in the basic format with only direct convertions done between the format fields (~30% done).

A portuguese excel sheet (Correspondence.xslx) is presented with the desired correspondence between fields in the coding, also the xsd files of each format are presented on the respective folders.

The conversion is based on Greendelta's converter https://github.com/GreenDelta/olca-conversion-service.
