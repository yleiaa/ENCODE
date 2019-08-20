#!/usr/bin/env python3
import os
import sys
import json
import argparse
import urllib.request
from time import process_time
from multiprocessing.pool import ThreadPool

def filterAudits(matrixURL):
    def build(auditDict,filter):
        addon=''
        for i in auditDict:
            if i.get('doc_count')>0:
                audit=i.get('key')
                fixed=audit.replace(' ','+')
                addon+=filter+fixed
        return addon
    errorStr=build(matrixURL['facets'][14]['terms'], '&audit.ERROR.category%21=')
    complaintStr=build(matrixURL['facets'][15]['terms'], '&audit.NOT_COMPLIANT.category%21=')
    #warningStr=build(matrixURL['facets'][16]['terms'],'&audit.WARNING.category%21=')
    fullStr=errorStr+complaintStr#+warningStr
    return fullStr
def download(link):
    urllib.request.urlretrieve(link)

parser = argparse.ArgumentParser(description='Searches on the Encode website')
parser.add_argument('--target', help='name of target protein')
parser.add_argument("biosample", help='biosample/cell name') 
args=parser.parse_args()

baseURL='https://www.encodeproject.org/matrix/?type=Experiment&status=released'

if args.target is not None: #If Not Control
    url1=baseURL+'&target.label='+args.target
    url1+='&target.label%21=Control'
    url1+='&assay_title=TF+ChIP-seq'
else: #If Control
    url1+='&assay_title=Control+ChIP-seq' 
    url1+='&target.investigated_as=control'
    url1+='&target.label=Control' 

url1+='&biosample_ontology.term_name='+args.biosample 
url2=url1+'&files.file_type=fastq'
url2=url1+'&format=json'

with urllib.request.urlopen(url2) as page:
    page=json.loads(page.read().decode())
    a=narrowAudits(page)

searchURL=url1+a+'&files.file_type=fastq'+'&format=json'

with urllib.request.urlopen(searchURL) as page:
    page=json.loads(page.read().decode())
    biosamples=page['facets'][9]['terms']
    narrowAudits(page)
    for i in biosamples:
        biosample=i.get('key')
        if biosample==args.biosample:
            resultAmt=i.get('doc_count')
            if resultAmt>0:
                print(str(resultAmt)+' results found.')
            if resultAmt < 1:
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

#!/usr/bin/env python3
import os
import sys
import json
import argparse
import urllib.request
from multiprocessing.pool import ThreadPool

def filterAudits(matrixURL):
    def build(auditDict,filter):
        addon=''
        for i in auditDict:
            if i.get('doc_count')>0:
                audit=i.get('key')
                fixed=audit.replace(' ','+')
                addon+=filter+fixed
        return addon
    errorStr=build(matrixURL['facets'][14]['terms'], '&audit.ERROR.category%21=')
    complaintStr=build(matrixURL['facets'][15]['terms'], '&audit.NOT_COMPLIANT.category%21=')
    #warningStr=build(matrixURL['facets'][16]['terms'],'&audit.WARNING.category%21=')
    fullStr=errorStr+complaintStr#+warningStr
    return fullStr

parser = argparse.ArgumentParser(description='Searches on the Encode website')
parser.add_argument('biosample', help='Biosample/cell name') 
parser.add_argument('--target', type=bool, default=False, help='Are you searching for a target protein?') 
args=parser.parse_args()

#Build Search Query
baseURL='https://www.encodeproject.org/matrix/?type=Experiment&status=released'
if args.target is False: #if it IS a control search
    url1=baseURL+'&assay_title=Control+ChIP-seq' +'&target.investigated_as=control'+'&target.label=Control' 
else:
    targetAddon='&target.label%21=Control'+'&assay_title=TF+ChIP-seq'
    url1=baseURL+targetAddon
generalAddon='&biosample_ontology.term_name='+args.biosample+'&files.file_type=fastq'
url1+=generalAddon

with urllib.request.urlopen(url1+'&format=json') as page:
    page=json.loads(page.read().decode())
    audits=filterAudits(page)

if args.target is False:
    searchURL=url1+audits+'&format=json'
else:
    with urllib.request.urlopen(url1+audits+'&format=json') as page:
        page=json.loads(page.read().decode())
        targets=page['facets'][6]['terms']
        print('Target Options:')
        for i in targets:
            if i.get('doc_count')>0:
                print(i.get('key')) #Space them out
    target=input('Enter Target: ')
    searchURL=baseURL+'&target.label='+target+targetAddon+generalAddon+audits+'&format=json'

print(searchURL)

with urllib.request.urlopen(searchURL) as page:
    page=json.loads(page.read().decode())
    biosamples=page['facets'][9]['terms']
    for i in biosamples:
        biosample=i.get('key')
        if biosample==args.biosample:
            resultAmt=i.get('doc_count')
            if resultAmt>0:
                print(str(resultAmt)+' results found.')
            if resultAmt < 1:
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
    
#page['facets'][0]['terms']=AssayTypesgit
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
#AuditCategories
#page['facets'][14]['terms']=Errors
#page['facets'][15]['terms']=Complaints
#page['facets'][16]['terms']=Warnings
