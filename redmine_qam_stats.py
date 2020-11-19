import xml.etree.ElementTree as ET
import requests
import json
import datetime
# comment those out if you have python>3.7
from backports.datetime_fromisoformat import MonkeyPatch
MonkeyPatch.patch_fromisoformat()

SHIRT_SIZES = {0: 0, 1: 0.5, 2: 1.5, 3: 2.5, 4: 5.0, 5: 10.0}

POO_STATUS = ['new', 'in progress', 'resolved', 'blocked', 'closed']

REDMINE_API_KEY = # put your redmine api key here

REDMINE_POST_PUT_FOOTER = ".json?key=" + REDMINE_API_KEY

REDMINE_POST_ADDR = "https://progress.opensuse.org/issues" + REDMINE_POST_PUT_FOOTER

REDMINE_PUT_ADDR = "https://progress.opensuse.org/issues/"

POO_ADDR_START = "https://progress.opensuse.org/"

POO_FOOTER = ".xml?key=" + REDMINE_API_KEY

KNOWN_TAGS = [
    '[qam]', '[maint]', '[high]', '[urgent]', '[blue]', '[yellow]',
    '[infra]', '[tooling]', '[openqa]', '[feature]', '[functional]',
    '[newt]', '[u]', '[12sp1]', '[12sp2]', '[12sp3]', '[12sp4]', '[12sp5]',
    '[15sp1]', '[15sp2]'
]

def findMiddle(input_list):
    middle = float(len(input_list))/2
    if middle % 2 != 0:
        return input_list[int(middle - .5)]
    else:
        return input_list[int(middle)]

def getTaglessPoos():
    errorlist = []
    offset = 0
    while(True):
        addr = POO_ADDR_START + 'issues.xml?project_id=119&status_id=*&offset=' + str(offset) + '&limit=10000&limit=1000&key=' + REDMINE_API_KEY
        response = requests.get(addr)
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError:
            print('parsing error while getting new issues - empty set returned')
            return
        issue_count = len(root.findall('issue'))
        for elem in root.iter('issue'):
            ok = False
            subj = elem.find('subject').text
            tagnum = len(subj.split('[')) - 1
            for tag in KNOWN_TAGS:
                if tag in subj:
                    tagnum -= 1
            if tagnum <= 0:
                id = elem.find('id')
                errorlist.append(REDMINE_PUT_ADDR + str(id.text) + " (" + subj + ")")
        if issue_count < 100:
            break
        offset += 100
    for i in errorlist:
            print(i)

def get_qam_poo_stats(from_year=None, from_month=None):
    offset = 0
    data = {}
    tmlst = []
    large = 0
    if not from_year or not from_month:
        from_year, from_month = 2010, 1
    while (True):
        addr = POO_ADDR_START + 'issues.xml?subject=~[qam]|~[qem]|~[QAM]|~[QEM]&status_id=*&offset=' + str(
            offset) + '&limit=10000&limit=1000&key=' + REDMINE_API_KEY
        response = requests.get(addr)
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError:
            print('parsing error while getting new issues - empty set returned')
            return
        issue_count = len(root.findall('issue'))
        for elem in root.iter('issue'):
            subj = elem.find('subject').text
            start = elem.find('created_on').text
            end = elem.find('closed_on').text
            if end is None:
                continue
            end = datetime.datetime.fromisoformat(end.replace('Z', '+00:00'))
            start = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
            if (end.year < from_year and end.month < from_month) or end.year < from_year - 1:
                continue
            elapsed = (end - start).total_seconds()
            # seconds in a month
            if elapsed > 2629743.83:
                large += 1
                continue
            # issues created retroactively
            if elapsed == 0:
                continue
            data[subj] = elapsed
            tmlst.append(data[subj])
        if issue_count < 100:
            break
        offset += 100
    tmlst.sort()
    print("From " + str(from_year) + "/" + str(from_month) + ":")
    print("Tickets that took <30 days were " + str(len(tmlst)))
    print("Tickets that took >30 days were " + str(large))
    print("Tickets that take >30 days are " + str((large/(len(tmlst) + large))*100) + "% of total functional closed tickets")
    print("Median of tickets that took <30 days: " + str(findMiddle(tmlst)/(3600*24)) + " days")
    print("Mean of tickets that took <30 days: " + str((sum(tmlst)/len(tmlst))/(3600*24)) + " days")
