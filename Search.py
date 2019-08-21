#!/usr/bin/env python3
import os
import sys
import json
import string
import os.path
import argparse
import urllib.request
from multiprocessing.pool import ThreadPool

def auditStr(auditDict, auditFilter):
    addon=''
    for i in auditDict:
        if i.get('doc_count')>0:
            audit=i.get('key')
            fixed=audit.replace(' ','+')
            addon+=auditFilter+fixed
    return addon

def download(link, name):
    path=os.path.join(os.getcwd(), name)
    urllib.request.urlretrieve(link, path)

parser = argparse.ArgumentParser(description='Searches on the Encode website')
parser.add_argument('biosample', help='Biosample/cell name') 
parser.add_argument('-t', '--target', type=bool, nargs='?', default=False, help='Are you searching for a target protein?') 
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
    errorStr=auditStr(page['facets'][14]['terms'], '&audit.ERROR.category%21=')
    complaintStr=auditStr(page['facets'][15]['terms'], '&audit.NOT_COMPLIANT.category%21=')
audits=errorStr+complaintStr
    
if args.target is False:
    searchURL=url1+audits+'&format=json'
    prefix='CNTL.'+args.biosample+'.'
else:
    with urllib.request.urlopen(url1+audits+'&format=json') as page:
        page=json.loads(page.read().decode())
        targets=page['facets'][6]['terms']
        print('Target Options:')
        for i in targets:
            if i.get('doc_count')>0:
                print(str(i.get('doc_count'))+' results found for '+i.get('key'))
        vaildTarget=False
        target=input('Enter Target: ')
        for i in targets:
            if i.get('doc_count')>0 and target==i.get('key'):
                vaildTarget=True
                break
        if vaildTarget is False:
            print('Not a valid target. Try again.')
            sys.exit()
    prefix=target+'.'+args.biosample+'.'
    searchURL=baseURL+'&target.label='+target+targetAddon+generalAddon+audits+'&format=json'

with urllib.request.urlopen(searchURL) as page:
    page=json.loads(page.read().decode())
    biosamples=page['facets'][9]['terms']
    for i in biosamples:
        biosample=i.get('key')
        if biosample==args.biosample:
            resultAmt=i.get('doc_count')
            if resultAmt>0:
                print(str(resultAmt)+' experiments found.')
            if resultAmt < 1:
                print('No experiments found with that biosample. Try again.')
                sys.exit()
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
        #link=line.encode('ASCII')
        downloadLinks.append(line)

print(str(len(downloadLinks))+' files found:')

prefixes=[]
for i in downloadLinks:
    prefixes.append(prefix+i[59:])

a = [(i, j) for i in downloadLinks for j in prefixes]

with ThreadPool() as pool:
    results=pool.starmap(download, a)
print('Download completed.')

'''   
page['facets'][0]['terms']=AssayTypesgit
page['facets'][1]['terms']=AssayTitles
page['facets'][2]['terms']=Status
page['facets'][3]['terms']=Project
page['facets'][4]['terms']=GenomeAssembly
page['facets'][5]['terms']=TargetCategory
page['facets'][6]['terms']=TargetofAssay
page['facets'][7]['terms']=Organism
page['facets'][8]['terms']=BiosampleClassifications
page['facets'][9]['terms']=
page['facets'][10]['terms']=Organ
page['facets'][11]['terms']=Cell
page['facets'][12]['terms']=AvailableFileTypes
page['facets'][13]['terms']=Lab
#AuditCategories
page['facets'][14]['terms']=Errors
page['facets'][15]['terms']=Complaints
page['facets'][16]['terms']=Warnings
'''