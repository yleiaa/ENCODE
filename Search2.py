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
    s=''
    for i in auditDict:
        if i.get('doc_count')>0:
            s+=auditFilter+i.get('key').replace(' ','+')
    return s

def exit(inputI):
    if inputI=='e' or inputI=='E':
        print('Exiting...')
        sys.exit()

def CheckURL(url):
    validURL=True
    try:
        urllib.request.urlopen(url)
    except urllib.request.HTTPError:
        validURL=False
        print('HTTP error')
    return validURL

def outputOptions(argList):
    print('{:60}{:}'.format('Options:','Results:'))
    for i in argList:
        if i.get('doc_count')>0:
            print('{:60}{:}'.format(i.get('key'),i.get('doc_count')))
    option=input('Enter your option or press e to exit: ')
    return option

def download(link, name):
    path=os.path.join(os.getcwd(), name)
    urllib.request.urlretrieve(link, path)

parser = argparse.ArgumentParser(description='Searches on the Encode website for targets & matching  controls.')
parser.add_argument('biosample', nargs='?', help='Biosample/cell name.')
parser.add_argument('target', nargs='?', help='Name of target protein.')
parser.add_argument('-w', '--warnings', nargs='?', type=bool, default=False, help='Add -w to filter out experiments with warnings.')
args=parser.parse_args()

baseURL='https://www.encodeproject.org'
searchBase='https://www.encodeproject.org/search/?type=Experiment&status=released'
addOn='&target.label%21=Control'+'&assay_title=TF+ChIP-seq'
general='&files.file_type=fastq'
auditURL=searchBase+addOn+general+'&format=json'

with urllib.request.urlopen(auditURL) as page:
    page=json.loads(page.read().decode())
    errorStr=auditStr(page['facets'][29]['terms'], '&audit.ERROR.category%21=')
    complaintStr=auditStr(page['facets'][30]['terms'], '&audit.NOT_COMPLIANT.category%21=')
    audits=errorStr+complaintStr
    if args.warnings is not False:
        warningStr=auditStr(page['facets'][31]['terms'],'&audit.WARNING.category%21=')
        audits+=warningStr
general+=audits+'&format=json'
url1=searchBase+addOn+general

if args.biosample is not None:
    biosample=args.biosample
else:
    with urllib.request.urlopen(url1) as page:
        page=json.loads(page.read().decode())
        biosamples=page['facets'][11]['terms']
        biosample=outputOptions(biosamples).replace(' ','+')
        exit(biosample)

while True:
    url2=searchBase+'&biosample_ontology.term_name='+biosample+addOn+general
    validBiosample=CheckURL(url2)
    if validBiosample is True:
        print('Valid biosample.')
        cntlPrefix='cntl.'+biosample
        break
    else:
        print('Invalid biosample.')
        with urllib.request.urlopen(url1) as page:
            page=json.loads(page.read().decode())
            biosamples=page['facets'][11]['terms']
            biosample=outputOptions(biosamples)
            exit(biosample)

if args.target is not None:
    target=args.target
else:
    with urllib.request.urlopen(url2) as page:
        page=json.loads(page.read().decode())
        targets=page['facets'][8]['terms']
        target=outputOptions(targets).replace(' ','+')
        exit(target)

while True:
    searchURL=searchBase+'&target.label='+target+addOn+general
    validTarget=CheckURL(searchURL)
    if validTarget is True:
        print('Valid target.')
        targetPrefix=target+'.'+biosample+'.'
        break
    else:
        print('Invalid target.')
        with urllib.request.urlopen(url2) as page:
            page=json.loads(page.read().decode())
            targets=page['facets'][8]['terms']
            target=outputOptions(targets)
            exit(target)

targetSummaries=[]
with urllib.request.urlopen(searchURL) as page:
    page=json.loads(page.read().decode())
    targetDownloads=page.get('batch_download')
    for i in page['@graph']:
        audit=i.get('audit')
        for j in audit.get('INTERNAL_ACTION'):
            if j.get('name')=='audit_experiment':
                targetSummaries.append(baseURL+j.get('path')+'?format=json')
print(str(len(targetSummaries))+' target experiments found')

cntlSummaries=[]
for i in targetSummaries:
    if CheckURL(i) is False:
        print('Error with target experiment url.')
    else:
        with urllib.request.urlopen(i) as page:
            page=json.loads(page.read().decode())
            cntl=page['possible_controls'][0]['@id']
            cntlSummaries.append(baseURL+cntl+'?format=json')
print(str(len(cntlSummaries))+' control experiments found')

cntlLinks=[]
for i in cntlSummaries:
    with urllib.request.urlopen(i) as page:
        page=json.loads(page.read().decode())
        for i in page['files']:
            if i.get('file_type')=='fastq':
                cntlLinks.append(baseURL+i.get('href')+'?format=json')

lineNum=0
targetLinks=[]
txtFile=urllib.request.urlopen(targetDownloads)
for line in txtFile:
    line=str(line.strip())
    line=line[2:-1]
    lineNum+=1
    if lineNum==1:
        path=os.path.join(os.getcwd(), targetPrefix+'metadata')
        urllib.request.urlretrieve(line, path)
    elif lineNum>1:
        targetLinks.append(line)

print(str(len(targetLinks))+' target fastq files found. Beginning download.')

targetPrefixes=[]
for i in targetLinks:
    targetPrefixes.append(targetPrefix+i[59:])
a = [(i, j) for i in targetLinks for j in targetPrefixes]
print(str(len(targetLinks))+' target fastq files found. Beginning download.')
with ThreadPool() as pool:
    results=pool.starmap(download, a)
print('Target download completed. Files saved to '+os.getcwd())

cntlPrefixes=[]
for i in cntlLinks:
    cntlPrefixes.append(cntlPrefix+i[59:-12])
b = [(i, j) for i in cntlLinks for j in cntlPrefix]
print(str(len(targetLinks))+' control fastq files found. Beginning download.')
with ThreadPool() as pool:
    results=pool.starmap(download, b)
print('Control download completed. Files saved to '+os.getcwd())
