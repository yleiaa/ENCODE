#!/usr/bin/env python3

# Imports ======================================================================

import os
import sys
import json
import string
import os.path
import argparse
import urllib.request
from multiprocessing.pool import ThreadPool




# Functions ====================================================================

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

def parseArguments():
    parser = argparse.ArgumentParser(description='Searches on the Encode website for targets & matching controls.')
    parser.add_argument('biosample', nargs='?', help='Biosample/cell name.')
    parser.add_argument('target', nargs='?', help='Name of target protein.')
    parser.add_argument('-w', '--warnings', nargs='?', type=bool, default=False, help='Add -w to filter out experiments with warnings.')
    parser.add_argument('-d', '--directory', nargs='?', help='Enter a path to a directory you want the ßiles saved to (default is current directory).')
    return parser.parse_args()

def checkAudits(auditURL, warnings=False):
    with urllib.request.urlopen(auditURL) as page:
        page=json.loads(page.read().decode())
        errorStr=auditStr(page['facets'][28]['terms'], '&audit.ERROR.category%21=')
        complaintStr=auditStr(page['facets'][29]['terms'], '&audit.NOT_COMPLIANT.category%21=')
        audits=errorStr+complaintStr
        if warnings is not False:
            warningStr=auditStr(page['facets'][30]['terms'],'&audit.WARNING.category%21=')
            audits+=warningStr
    return audits

def checkBiosample(biosample, url1, addOn, general, searchBase):
    if biosample is None:
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
    return biosample, url2, biosampleAdd

def checkTarget(target, biosample, url2, searchBase, biosampleAdd):
    if target is None:
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
    return target, searchURL

def collectTargetPgURLs(searchURL, baseURL):
    targetPgURLs=[]
    with urllib.request.urlopen(searchURL) as page:
        page=json.loads(page.read().decode())
        for i in page.get('@graph'):
            targetPgURLs.append(baseURL+i.get('@id')+'?format=json')
    return targetPgURLs

def collectLinksPaths(targetPgURLs, directory, target, biosample, baseURL):
    tLinks=[]
    tFullPaths=[]
    n=0
    cntlPgURLs=[]
    cFullPaths=[]
    for i in targetPgURLs:
        n+=1
        path=os.path.join(directory, target+'.'+str(n)+'.'+biosample+'.'+i[42:-13])
        try:
            os.mkdir(path)
        except OSError:
            print('Error creating a new folder.')
            sys.exit()
        with urllib.request.urlopen(i) as page:
            page=json.loads(page.read().decode())      
            for j in page['files']:
                if j.get('file_type')=='fastq':
                    tLinks.append(baseURL+j.get('href'))
                    tfullPath=os.path.join(path, target+'.'+biosample+'.'+j.get('href')[30:])
                    tFullPaths.append(tfullPath)
            cntl=page['possible_controls'][0]['@id']
            cntlPgURLs.append(baseURL+cntl+'?format=json')
            cfullPath=os.path.join(path, 'CNTL.'+biosample+'.'+cntl[13:-1]+'.fastq.gz')
            cFullPaths.append(cfullPath)

    cLinks=[]
    for i in cntlPgURLs:
        with urllib.request.urlopen(i) as page:
            page=json.loads(page.read().decode())
            for i in page['files']:
                if i.get('file_type')=='fastq':
                    cLinks.append(baseURL+i.get('href'))
    return tLinks, tFullPaths, cLinks, cFullPaths

def main():
    args = parseArguments()

    if args.directory is None:
        directory=os.getcwd()
    else:
        directory=pathCheck(args.directory)

    baseURL='https://www.encodeproject.org'
    searchBase='https://www.encodeproject.org/search/?type=Experiment&status=released'
    addOn='&target.label%21=Control'+'&assay_title=TF+ChIP-seq'
    general='&files.file_type=fastq'
    auditURL=searchBase+addOn+general+'&format=json'
    audits=checkAudits(auditURL, warnings=args.warnings)
    general+=audits+'&format=json'
    url1=searchBase+addOn+general

    biosample, url2, biosampleAdd = checkBiosample(args.biosample, url1, addOn, general, searchBase)
    target, searchURL = checkTarget(args.target, biosample, url2, searchBase, biosampleAdd)

    #EVERYTHING ABOVE SHOULD B FINE

    targetPgURLs=collectTargetPgURLs(searchURL, baseURL)
    tLinks, tFullPaths, cLinks, cFullPaths=collectLinksPaths(targetPgURLs, directory, target, biosample, baseURL)

    a = [(i, j) for i in tLinks for j in tFullPaths]
    print('Beginning target download.')
    with ThreadPool() as pool:
        results=pool.starmap(download, a)
    print('Target download completed.')

    b = [(i, j) for i in cLinks for j in cFullPaths]
    print('Beginning control download.')
    with ThreadPool() as pool:
        results=pool.starmap(download, b)
    print('Control download completed.')




# Execute ======================================================================

if __name__ == '__main__':
    main()