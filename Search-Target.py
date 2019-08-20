#!/usr/bin/env python3
import os
import sys
import json
import argparse
import urllib.request
from multiprocessing.pool import ThreadPool

def download(link):
    urllib.request.urlretrieve(link)

parser = argparse.ArgumentParser(description='Searches on the Encode website')
parser.add_argument('--target', help='name of target protein')
parser.add_argument("biosample", help='biosample/cell name') 
args=parser.parse_args()

searchURL='https://www.encodeproject.org/matrix/?type=Experiment&status=released'

if args.target is not None: #If Not Control
    searchURL+='&target.label='+args.target
    searchURL+='&target.label%21=Control' #Target of Assay NOT Control
    searchURL+='&assay_title=TF+ChIP-seq'#Assay Title = TF ChIP-seq
else: #If Control
    searchURL+='&assay_title=Control+ChIP-seq' #Assay Title=Control ChIP-seq
    searchURL+='&target.investigated_as=control' #Target Category (Same # of results as Assay Title)
    searchURL+='&target.label=Control' #Target Label- Narrows it down a little to only human controls(?)

searchURL+='&biosample_ontology.term_name='+args.biosample #Biosample Term Name 
searchURL+='&files.file_type=fastq'#Available File Types
searchURL+='&format=json' #Puts in json format

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

lineNum=0
downloadLinks=[]
txtFile=urllib.request.urlopen(downloadURL)
for line in txtFile:
    line=str(line.strip())
    line=line[2:-1]
    lineNum+=1
    if lineNum==1:
        info=urllib.request.urlopen(line)
    elif lineNum>1:
        downloadLinks.append(line)

with ThreadPool() as pool:
    results=pool.map(download, downloadLinks)