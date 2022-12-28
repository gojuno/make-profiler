#!/usr/bin/python3

from datetime import datetime
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def escape_json_string(s):
    s=str(s)
    s = s.replace("\"", "")
    s = s.replace("'","")
    s = s.replace("\\","\\\\") # single \ to double \\
    return s


def export_report(performance,docs):
    strOutputFile = 'report.json'
    fo = open(strOutputFile, 'w', encoding="utf-8")
    n_in_progress=0
    n_failed=0
    n_total = 0
    fo.write('{\n')
    fo.write('    "status":[\n')
    for key in performance:
        rec=performance[key]
        n_total += 1
        if rec["failed"] == True:
            event_type = "failed"
            n_failed += 1
        elif rec["done"] == True:
            event_type = "completed"
        elif rec["running"] == True:
            event_type = "started"
            n_in_progress += 1
        else:
            event_type = "??unknown??"


        #event_time = datetime.fromtimestamp(int(rec['start_current'])).strftime(DATE_FORMAT)
        if 'finish_prev' in rec:
            last_event_time = datetime.fromtimestamp(int(rec['finish_prev'])).strftime(DATE_FORMAT)
        else:
            last_event_time = ''

        if 'start_current' in rec:
            event_time = datetime.fromtimestamp(int(rec['finish_current'])).strftime(DATE_FORMAT)
        else:
            event_time = last_event_time

        descr = docs.get(key, '')
        if n_total > 1:
            fo.write(',\n')
        fo.write('        {"eventN":"'+escape_json_string(key) +'",\n')
        fo.write('         "description":"' + escape_json_string(descr) + '", \n')
        fo.write('         "eventType":"'+escape_json_string(event_type)+'",\n')
        fo.write('         "eventTime":"'+escape_json_string(event_time)+'",\n')
        fo.write('         "eventDuration":' + escape_json_string(rec["timing_sec"]) + ',\n')
        if last_event_time == '':
            fo.write('         "lastEventTime":' + 'null' + ',\n')
        else:
            fo.write('         "lastEventTime":"' + last_event_time + '",\n')
        fo.write('         "log":"' + escape_json_string(rec["log"]) + '" \n')

        fo.write('        }')
    fo.write('\n')
    fo.write('    ],\n')

    if n_in_progress>0:
        current_status = 'Up and Running'
    else:
        current_status = 'Idle'

    fo.write('    "pipeline":{ \n')
    fo.write('        "nProgress":'+ str(n_in_progress)+',\n')
    fo.write('        "nEvents":'+str(n_total)+',\n')
    fo.write('        "nFail":'+str(n_failed)+',\n')
    fo.write('        "oldestCompleteTime":"2022-11-23T06:49:32.000Z",\n')
    fo.write('        "presentStatus": "'+current_status+'" \n')
    fo.write('    }\n')
    fo.write('}\n')

    fo.close()

