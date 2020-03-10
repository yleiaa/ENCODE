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

def parseArguments():
    parser = argparse.ArgumentParser(description='Searches on the Encode website for targets & matching controls.')
    parser.add_argument('biosample', nargs='?', help='Biosample/cell name.')
    parser.add_argument('target', nargs='?', help='Name of target protein.')
    parser.add_argument('-w', '--warnings', nargs='?', type=bool, default=False, help='Add -w to filter out experiments with warnings.')
    parser.add_argument('-d', '--directory', nargs='?', help='Enter a path to a directory you want the ßiles saved to (default is current directory).')
    return parser.parse_args()

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

def outputOptions(argList):
    print('{:60}{:}'.format('Options:','Results:'))
    for i in argList:
        if i.get('doc_count')>0:
            print('{:60}{:}'.format(i.get('key'),i.get('doc_count')))

def CheckURL(url):
    validURL=True
    try:
        urllib.request.urlopen(url)
    except urllib.request.HTTPError:
        validURL=False
    return validURL

def enterOption():
    option=input('Enter your option or press e to exit: ')
    if option=='e' or option=='E':
        print('Exiting.')
        sys.exit()
    return option.replace(' ','+')

def checkBiosample(biosample, base):
    if biosample is not None:
        biosample=biosample
    else:
        url1=base+'&format=json'
        with urllib.request.urlopen(url1) as page:
            page=json.loads(page.read().decode())
            outputOptions(page['facets'][11]['terms'])
            biosample=enterOption()
    while True:
        biosampleURL=base+'&biosample_ontology.term_name='+biosample
        validBiosample=CheckURL(biosampleURL)
        if validBiosample is True:
            break
        else:
            print('Pick a new biosample:')
            with urllib.request.urlopen(url1) as page:
                page=json.loads(page.read().decode())
                outputOptions(page['facets'][11]['terms'])
                biosample=enterOption()
    return biosample, biosampleURL

def checkTarget(target, url2):
    if target is not None:
        target=target
    else:
        url3=url2+'&format=json'
        with urllib.request.urlopen(url3) as page:
            page=json.loads(page.read().decode())
            outputOptions(page['facets'][8]['terms'])
            target=enterOption()
    while True: 
        targetURL=url2+'&target.label='+target
        validTarget=CheckURL(targetURL)
        if validTarget is True:
            break
        else:
            print('Pick a new target:')
            with urllib.request.urlopen(url2+'&format=json') as page:
                page=json.loads(page.read().decode())
                outputOptions(page['facets'][8]['terms'])
                target=enterOption()
    return target, targetURL

def main():

    args = parseArguments()

    if args.directory is None:
        directory=os.getcwd()
    else:
        directory=pathCheck(args.directory)

    base='https://www.encodeproject.org/search/?type=Experiment&status=released&target.label%21=Control&assay_title=TF+ChIP-seq&files.file_type=fastq'
    audits=checkAudits(base+'&format=json', warnings=args.warnings)

    base+=audits

    biosample, url2 = checkBiosample(args.biosample, base)
    target, targetURL = checkTarget(args.target, url2)

    directories=[]
    with urllib.request.urlopen(targetURL+'&format=json') as page:
            page=json.loads(page.read().decode())


if __name__ == '__main__':
    main()