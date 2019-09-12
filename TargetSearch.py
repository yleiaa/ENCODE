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

def outputOptions(argList):
    def exit(inputI):
        if inputI=='e' or inputI=='E':
            print('Exiting...')
            sys.exit()
    print('{:60}{:}'.format('Options:','Results:'))
    for i in argList:
        if i.get('doc_count')>0:
            print('{:60}{:}'.format(i.get('key'),i.get('doc_count')))
    option=input('Enter your option or press e to exit: ')
    exit(option)
    return option

def CheckURL(url):
    validURL=True
    try:
        urllib.request.urlopen(url)
    except urllib.request.HTTPError:
        validURL=False
    return validURL

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
        biosample=outputOptions(page['facets'][11]['terms']).replace(' ','+')

while True: #Check Biosample
    biosampleAdd='&biosample_ontology.term_name='+biosample+addOn+general
    url2=searchBase+biosampleAdd
    validBiosample=CheckURL(url2)
    if validBiosample is True:
        print('Valid biosample.')
        cntlPrefix='CNTL.'+biosample
        break
    else:
        print('Invalid biosample.')
        with urllib.request.urlopen(url1) as page:
            page=json.loads(page.read().decode())
            biosample=outputOptions(page['facets'][11]['terms']).replace(' ','+')

if args.target is not None:
    target=args.target
else:
    with urllib.request.urlopen(url2) as page:
        page=json.loads(page.read().decode())
        target=outputOptions(page['facets'][8]['terms']).replace(' ','+')
while True: #Check Target
    searchURL=searchBase+'&target.label='+target+biosampleAdd
    validTarget=CheckURL(searchURL)
    if validTarget is True:
        print('Valid target.')
        targetPrefix=target+'.'+biosample+'.'
        break
    else:
        print('Invalid target.')
        with urllib.request.urlopen(url2) as page:
            page=json.loads(page.read().decode())
            target=outputOptions(page['facets'][8]['terms']).replace(' ','+')

targetSummaries=[]
with urllib.request.urlopen(searchURL) as page:
    page=json.loads(page.read().decode())
    targetTxt=page.get('batch_download')
    for i in page.get('@graph'):
        targetSummaries.append(baseURL+i.get('@id')+'?format=json')
print(str(len(targetSummaries))+' target experiments found.')

cntlSummaries=[]
for i in targetSummaries:
    with urllib.request.urlopen(i) as page:
        page=json.loads(page.read().decode())
        cntl=page['possible_controls'][0]['@id']
        cntlSummaries.append(baseURL+cntl+'?format=json')
print(str(len(cntlSummaries))+' control experiments found.')

lineNum=0
targetLinks=[]
txtFile=urllib.request.urlopen(targetTxt)
for line in txtFile:
    line=str(line.strip())
    line=line[2:-1]
    lineNum+=1
    if lineNum==1:
        path=os.path.join(os.getcwd(), targetPrefix+'metadata')
        urllib.request.urlretrieve(line, path)
    elif lineNum>1:
        targetLinks.append(line)
print(str(len(targetLinks))+' target fastq files found.')

#EVERYTHING ABOVE IS FINE - DO NOT TOUCH

targetPrefixes=[]
for i in targetLinks:
    targetPrefixes.append(targetPrefix+i[59:])
a = [(i, j) for i in targetLinks for j in targetPrefixes]
print('Beginning target download.')

with ThreadPool() as pool:
    results=pool.starmap(download, a)
print('Target download completed. Files saved to '+os.getcwd())

cntlLinks=[]
for i in cntlSummaries:
    with urllib.request.urlopen(i) as page:
        page=json.loads(page.read().decode())
        for i in page['files']:
            if i.get('file_type')=='fastq':
                cntlLinks.append(baseURL+i.get('href')+'?format=json')
print(str(len(cntlLinks))+' control fastq files found.')

cntlPrefixes=[]
for i in cntlLinks:
    cntlPrefixes.append(cntlPrefix+'.'+i[59:-12])

b = [(i, j) for i in cntlLinks for j in cntlPrefixes]
print('Beginning control download.')

with ThreadPool() as pool:
    results=pool.starmap(download, b)
print('Control download completed. Files saved to '+os.getcwd())

