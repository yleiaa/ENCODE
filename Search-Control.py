#!/usr/bin/env python3
import os
import sys
import json
import argparse
import webbrowser
import urllib.request

parser = argparse.ArgumentParser(description='Searches on the Encode website for controls')
parser.add_argument("biosample", help='biosample term name')
args=parser.parse_args()

searchURL='https://www.encodeproject.org/matrix/?type=Experiment&status=released'
searchURL+='&assay_title=Control+ChIP-seq' #Assay Title=Control ChIP-seq
searchURL+='&target.investigated_as=control' #Target Category (Same # of results as Assay Title)
searchURL+='&target.label=Control' #Target Label- Narrows it down a little to only human controls(?)
searchURL+='&biosample_ontology.term_name='+args.biosample #Biosample Term Name 
searchURL+='&files.file_type=fastq'#Available File Types
searchURL+='&format=json' #Puts in json format

#webbbrower.open(searchURL)

with urllib.request.urlopen(searchURL) as page:
    page=json.loads(page.read().decode())
    biosamples=page['facets'][9]['terms']
    for i in biosamples:
        biosample=i.get('key')
        if biosample==args.biosample:
            resultAmt=i.get('doc_count')
            if resultAmt > 0:
                print(str(resultAmt)+' experiments found.')
                break
            else:
                print('No experiments found with that biosample. Try again.')
                SystemExit
    downloadURL=page.get('batch_download')

    txtFile=urllib.request.urlopen(downloadURL)
    for line in txtFile:
        print(line)

