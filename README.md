# ENCODE
Searches for experiments on the encode website give a biosample term name and an optional target 
assay if looking for non-control experiments. Then, pulls fastq files for experiment results
and downloads them in parallel to the programs current diectory.

#Command line example for target

/path/Search.py K562 -t
