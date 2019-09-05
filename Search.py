#!/usr/bin/env python3
import os
import sys
import json
import string
import os.path
import argparse
import urllib.request
from multiprocessing.pool import ThreadPool

def CheckURL(url):
    validURL=True
    try:
        urllib.request.urlopen(url)
    except urllib.request.HTTPError:
        validURL=False
        print('HTTP error')
    except urllib.request.URLError:
        validURL=False
        print('URL error')
    return validURL

def auditStr(auditDict, auditFilter):
    s=''
    for i in auditDict:
        if i.get('doc_count')>0:
            s+=auditFilter+i.get('key').replace(' ','+')
    return s

def download(link, name):
    path=os.path.join(os.getcwd(), name)
    urllib.request.urlretrieve(link, path)

parser = argparse.ArgumentParser(description='Searches the Encode website.')
parser.add_argument('biosample', nargs='?', help='Biosample/cell name.')
parser.add_argument('-t', '--target', nargs='?', default='control', help='Add -t if earching for a target protein.')
parser.add_argument('-w', '--warnings', nargs='?', type=bool, default=False, help='Add -w to filter out experiments with warnings.')
args=parser.parse_args()

baseURL='https://www.encodeproject.org/search/?type=Experiment&status=released'
if args.target is 'control':
    addOn='&assay_title=Control+ChIP-seq' +'&target.investigated_as=control'+'&target.label=Control' 
else:
    addOn='&target.label%21=Control'+'&assay_title=TF+ChIP-seq'
general='&files.file_type=fastq'
url1=baseURL+addOn+general

with urllib.request.urlopen(url1+'&format=json') as page:
    page=json.loads(page.read().decode())
    errorStr=auditStr(page['facets'][29]['terms'], '&audit.ERROR.category%21=')
    complaintStr=auditStr(page['facets'][30]['terms'], '&audit.NOT_COMPLIANT.category%21=')
    audits=errorStr+complaintStr
    if args.warnings is not False:
        warningStr=auditStr(page['facets'][31]['terms'],'&audit.WARNING.category%21=')
        audits+=warningStr

#Get Biosample
if args.biosample is not None:
    biosample=args.biosample
else:
    with urllib.request.urlopen(url1+audits+'&format=json') as page:
        page=json.loads(page.read().decode())
        biosamples=page['facets'][11]['terms']
        print('{:60}{:}'.format('Biosample:','Results:'))
        for i in biosamples:
            if i.get('doc_count')>0:
                print('{:60}{:}'.format(i.get('key'),i.get('doc_count')))
        biosample=input('Enter Biosample: ')

#Check Biosample
while True:
    biosample=biosample.replace(' ','+')
    url2=baseURL+'&biosample_ontology.term_name='+biosample+addOn+general+audits
    validBiosample=CheckURL(url2)
    if validBiosample is True:
        print('Valid biosample.')
        break
    else:
        print('Invalid biosample.')
        with urllib.request.urlopen(url1+'&format=json') as page:
            page=json.loads(page.read().decode())
            biosamples=page['facets'][11]['terms']
            print('{:60}{:}'.format('Biosample:','Results:'))
            for i in biosamples:
                if i.get('doc_count')>0:
                    print('{:60}{:}'.format(i.get('key'),i.get('doc_count')))
        biosample=input('Enter New Biosample: ')

if args.target is 'control':
    target=args.target
    searchURL=url2+'&format=json'
    prefix='CNTL'+biosample+'.'
else:
    with urllib.request.urlopen(url2+'&format=json') as page:
        page=json.loads(page.read().decode())
        targets=page['facets'][8]['terms']
        vaildTarget=False
        if args.target is not None:
            target=args.target
        else:
            print('{:60}{:}'.format('Target:','Results:'))
            for i in targets:
                if i.get('doc_count')>0:
                    print('{:60}{:}'.format(i.get('key'),i.get('doc_count')))
            target=input('Enter Target: ')

if target is not 'control':
    while True:
        target=target.replace(' ','+')
        searchURL=baseURL+'&target.label='+target+addOn+general+audits+'&format=json'
        validTarget=CheckURL(searchURL)
        if validTarget is True:
            print('Valid target.')
            prefix=target+'.'+biosample+'.'
            break
        else:
            print('Invalid target.')
            with urllib.request.urlopen(searchURL) as page:
                page=json.loads(page.read().decode())
                targets=page['facets'][8]['terms']
                print('{:60}{:}'.format('Target:','Results:'))
                for i in targets:
                    if i.get('doc_count')>0:
                        print('{:60}{:}'.format(i.get('key'),i.get('doc_count')))
            target=input('Enter New Target: ')

with urllib.request.urlopen(searchURL) as page:
    page=json.loads(page.read().decode())
    downloadURL=page.get('batch_download')

lineNum=0
downloadLinks=[]
txtFile=urllib.request.urlopen(downloadURL)
for line in txtFile:
    line=str(line.strip())
    line=line[2:-1]
    lineNum+=1
    if lineNum==1:
        path=os.path.join(os.getcwd(), prefix+'metadata')
        urllib.request.urlretrieve(line, path)
    elif lineNum>1:
        downloadLinks.append(line)

print(str(len(downloadLinks))+' files found. Beginning download.')
prefixes=[]
for i in downloadLinks:
    prefixes.append(prefix+i[59:])
a = [(i, j) for i in downloadLinks for j in prefixes]

with ThreadPool() as pool:
    results=pool.starmap(download, a)
print('Download completed. Files saved to '+os.getcwd())
