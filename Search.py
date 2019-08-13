#!/usr/bin/env python3
import os
import sys
import json
import argparse
import urllib.request

parser = argparse.ArgumentParser(description='Searches on the Encode website')
parser.add_argument('--target', help='name of target')
parser.add_argument("biosample", help='biosample term name')
args=parser.parse_args()

searchURL='https://www.encodeproject.org/matrix/?type=Experiment&status=released'

control=True

if args.target is not None: #If Not Control
    control=False
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
    if control==False:
        assayTitles=page['facets'][1]['terms'] 
        TFAmt=0
        for i in assayTitles:
            assay=i.get('key')
            if assay=='TF ChIP-seq':
                TFAmt=i.get('doc_count') 
                break
        if TFAmt <= 0:
            print('No experimenrs found for TF ChIP-seq. Try again')
            SystemExit
    biosamples=page['facets'][9]['terms']
    for i in biosamples:
        biosample=i.get('key')
        if biosample==args.biosample:
            resultAmt=i.get('doc_count')
            break
    if resultAmt > 0:
        print(str(resultAmt)+' experiments found.')
    else:
        print('No experiments found with that biosample. Try again.')
        SystemExit
    downloadURL=page.get('batch_download')

txtFile=urllib.request.urlopen(downloadURL)
for line in txtFile:
    print(line)


#page['facets'][0]['terms']=AssayTypes
#page['facets'][1]['terms']=AssayTitles
#page['facets'][2]['terms']=Status
#page['facets'][3]['terms']=Project
#page['facets'][4]['terms']=GenomeAssembly
#page['facets'][5]['terms']=TargetCategory
#page['facets'][6]['terms']=TargetofAssay
#page['facets'][7]['terms']=Organism
#page['facets'][8]['terms']=BiosampleClassifications
#page['facets'][9]['terms']=
#page['facets'][10]['terms']=Organ
#page['facets'][11]['terms']=Cell
#page['facets'][12]['terms']=AvailableFileTypes
#page['facets'][13]['terms']=Lab
#page['facets'][14]['terms']=AuditCategories
