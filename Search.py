#!/usr/bin/env python3
import os
import sys
import json
import queue
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
    try:
        urllib.request.urlretrieve(link, path)
    except urllib.request.ContentTooShortError:
        sys.exit()

parser = argparse.ArgumentParser(description='Searches on the Encode website for targets & matching controls.')
parser.add_argument('biosample', nargs='?', help='Biosample/cell name.')
parser.add_argument('target', nargs='?', help='Name of target protein.')
parser.add_argument('-w', '--warnings', nargs='?', type=bool, default=False, help='Add -w to filter out experiments with warnings.')
parser.add_argument('-d', '--directory', nargs='?', help='Enter a path to a directory you want the ßiles saved to (default is current directory).')
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
    errorStr=auditStr(page['facets'][28]['terms'], '&audit.ERROR.category%21=')
    complaintStr=auditStr(page['facets'][29]['terms'], '&audit.NOT_COMPLIANT.category%21=')
    audits=errorStr+complaintStr
    if args.warnings is not False:
        warningStr=auditStr(page['facets'][30]['terms'],'&audit.WARNING.category%21=')
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
    url3=searchBase+'&target.label='+target+biosampleAdd
    validTarget=CheckURL(url3)
    if validTarget is True:
        targetPrefix=target+'.'+biosample+'.'
        break
    else:
        print('Invalid target.')
        with urllib.request.urlopen(url2) as page:
            page=json.loads(page.read().decode())
            target=outputOptions(page['facets'][8]['terms'])

directories=[]
with urllib.request.urlopen(url3) as page:
        page=json.loads(page.read().decode())
        n=0
        for i in page['facets'][18]['terms']:
            if i['doc_count'] > 0:
                #make directory
                #change search url
                print(str(i['doc_count'])+' '+i['key']+' result(s) found')
                print(directory+'/'+i['key']+'/')
                #directories.append(directory+i['key'])
