#!/usr/bin/env python3
import os
import sys
import json
import string
import os.path
import argparse
import urllib.request
from multiprocessing.pool import ThreadPool

def pathCheck(pathArg):
    if os.path.exists(pathArg) is False:
        print('Invalid path.')
        sys.exit()
    elif os.path.exists(pathArg) is True:
        return pathArg

def auditStr(auditDict, auditFilter):
    s=''
    for i in auditDict:
        if i.get('doc_count')>0:
            s+=auditFilter+i.get('key').replace(' ','+')
    return s
    
def outputOptions(argList):
    print('{:60}{:}'.format('Options:','Results:'))
    for i in argList:
        if i.get('doc_count')>0:
            print('{:60}{:}'.format(i.get('key'),i.get('doc_count')))
    option=input('Enter your option or press e to exit: ')
    if option=='e' or option=='E':
        print('Exiting.')
        sys.exit()
    return option.replace(' ','+')

def CheckURL(url):
    validURL=True
    try:
        urllib.request.urlopen(url)
    except urllib.request.HTTPError:
        validURL=False
    return validURL

def download(link, path):
    urllib.request.urlretrieve(link, path)

parser = argparse.ArgumentParser(description='Searches on the Encode website for targets & matching  controls.')
parser.add_argument('biosample', nargs='?', help='Biosample/cell name.')
parser.add_argument('target', nargs='?', help='Name of target protein.')
parser.add_argument('-d', '--directory', nargs='?', help='Enter a path to a directory you want the files saved to (default is current directory).')
parser.add_argument('-w', '--warnings', nargs='?', type=bool, default=False, help='Add -w to filter out experiments with warnings.')
args=parser.parse_args()

if args.directory is None:
    directory=os.getcwd()
else:
    directory=pathCheck(args.directory)

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
        biosample=outputOptions(page['facets'][11]['terms'])

while True: #Check Biosample
    biosampleAdd='&biosample_ontology.term_name='+biosample+addOn+general
    url2=searchBase+biosampleAdd
    validBiosample=CheckURL(url2)
    if validBiosample is True:
        cntlPrefix='CNTL.'+biosample
        break
    else:
        print('Invalid biosample.')
        with urllib.request.urlopen(url1) as page:
            page=json.loads(page.read().decode())
            biosample=outputOptions(page['facets'][11]['terms'])

if args.target is not None:
    target=args.target
else:
    with urllib.request.urlopen(url2) as page:
        page=json.loads(page.read().decode())
        target=outputOptions(page['facets'][8]['terms'])

while True: #Check Target
    searchURL=searchBase+'&target.label='+target+biosampleAdd
    validTarget=CheckURL(searchURL)
    if validTarget is True:
        targetPrefix=target+'.'+biosample+'.'
        break
    else:
        print('Invalid target.')
        with urllib.request.urlopen(url2) as page:
            page=json.loads(page.read().decode())
            target=outputOptions(page['facets'][8]['terms'])

#EVERYTHING ABOVE SHOULD B FINE

targetPgURLs=[]
with urllib.request.urlopen(searchURL) as page:
    page=json.loads(page.read().decode())
    for i in page.get('@graph'):
        targetPgURLs.append(baseURL+i.get('@id')+'?format=json')

tLinks=[]
tFullPaths=[]
cntlPgURLs=[]
cFullPaths=[]
for exp in targetPgURLs:
    path=os.path.join(os.getcwd(), biosample+'.'+target+'.'+exp[42:-13])
    try:
        os.mkdir(path)
    except OSError:
        print('Error creating a new folder.')
        sys.exit()
    with urllib.request.urlopen(exp) as page:
        page=json.loads(page.read().decode())
        cntl=page['possible_controls'][0]['@id']
        cntlPgURLs.append(baseURL+cntl+'?format=json')
        cfullPath=os.path.join(path, 'CNTL.'+biosample+'.'+cntl[13:-1]+'.fastq.gz')
        for j in page['files']:
            if j.get('file_type')=='fastq':
                tLinks.append(baseURL+j.get('href'))
                tfullPath=os.path.join(path, j.get('href')[30:])
                tFullPaths.append(tfullPath)

a = [(i, j) for i in tLinks for j in tFullPaths]
print('Beginning target download.')
with ThreadPool() as pool:
    results=pool.starmap(download, a)
print('Target download completed.')

cLinks=[]
for i in cntlPgURLs:
    with urllib.request.urlopen(i) as page:
        page=json.loads(page.read().decode())
        for i in page['files']:
            if i.get('file_type')=='fastq':
                cLinks.append(baseURL+i.get('href')+'?format=json')

b = [(i, j) for i in cLinks for j in cFullPaths]
print('Beginning control download.')
with ThreadPool() as pool:
    results=pool.starmap(download, b)
print('Control download completed.')








