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

def findEnds(targetURL):
    SE = 0
    PE = 0
    with urllib.request.urlopen(targetURL+'&format=json') as page:
        page=json.loads(page.read().decode())
        for i in page['facets']:
            for j in i.get('terms'):
                k=j.get('key')
                if j.get('key') =='single-ended':
                    print(str(j.get('doc_count'))+' '+j.get('key')+' results found.')
                    SE += (j.get('doc_count'))
                if j.get('key') =='paired-ended':
                    print(str(j.get('doc_count'))+' '+j.get('key')+' results found.')
                    PE += j.get('doc_count')
    return SE, PE

def collectTargetPgURLs(url):
    targetPgURLs=[]
    with urllib.request.urlopen(url+'&format=json') as page:
        page=json.loads(page.read().decode())
        for i in page.get('@graph'):
            targetPgURLs.append('https://www.encodeproject.org/'+i.get('@id')+'?format=json')
    return targetPgURLs

def collectLinkPaths(targetPgURLs, directory, target, biosample, add):
    n=0
    tLinks=[]
    tFullPaths=[]
    cntlPgURLs=[]
    cFullPaths=[]
    cLinks=[]
    for i in targetPgURLs:
        n+=1
        path=os.path.join(directory, add+'.'+target+'.'+str(n)+'.'+biosample+'.'+i[43:-13])
        try:
            os.mkdir(path)
        except OSError:
            print('Error creating a new folder.')
            sys.exit()
        with urllib.request.urlopen(i) as page:
            page=json.loads(page.read().decode())
            for j in page['files']:
                if j.get('file_type')=='fastq':
                    tLinks.append('https://www.encodeproject.org/'+j.get('href'))
                    tfullPath=os.path.join(path, target+'.'+j.get('href')[30:])
                    tFullPaths.append(tfullPath)
            cntl=page['possible_controls'][0]['@id']
            cntlPgURLs.append('https://www.encodeproject.org/'+cntl+'?format=json')
            cfullPath=os.path.join(path, 'CNTL.'+biosample+'.'+cntl[13:-1]+'.fastq.gz')
            cFullPaths.append(cfullPath)
    for i in cntlPgURLs:
        with urllib.request.urlopen(i) as page:
            page=json.loads(page.read().decode())
            for i in page['files']:
                if i.get('file_type')=='fastq':
                    cLinks.append('https://www.encodeproject.org/'+i.get('href'))
    return tLinks, tFullPaths, cLinks, cFullPaths

def download(link, path):
    try:
        urllib.request.urlretrieve(link, path)
    except urllib.request.ContentTooShortError:
        sys.exit()
    
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

    SE, PE  = findEnds(targetURL)

    if SE > 0:
        seURL=targetURL+'&files.run_type=single-ended'
        sePgURLs=collectTargetPgURLs(seURL)
        tLinks, tFullPaths, cLinks, cFullPaths = collectLinkPaths(sePgURLs, directory, target, biosample, 'se')
       
        a = list(zip(tLinks, tFullPaths))
        print('Beginning single-ended target download.')
        with ThreadPool() as pool:
            results=pool.starmap(download, a)
        print('Single-ended target download completed.')

        b = list(zip(cLinks, cFullPaths))
        print('Beginning single-ended control download.')
        with ThreadPool() as pool:
            results=pool.starmap(download, b)
        print('Single-ended control download completed.')

    if PE > 0:
        peURL=targetURL+'&files.run_type=paired-ended'
        pePgURLs=collectTargetPgURLs(peURL)
        tLinks, tFullPaths, cLinks, cFullPaths = collectLinkPaths(pePgURLs, directory, target, biosample, 'pe')

        a = list(zip(tLinks, tFullPaths))
        print('Beginning paired-ended target download.')
        with ThreadPool() as pool:
            results=pool.starmap(download, a)
        print('Paired-ended target download completed.')

        b = list(zip(cLinks, cFullPaths))
        print('Beginning paired-ended control download.')
        with ThreadPool() as pool:
            results=pool.starmap(download, b)
        print('Paired-ended control download completed.')
        
if __name__ == '__main__':
    main()