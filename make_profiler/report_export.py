from datetime import datetime
import json
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

status_list = {}
status = []

def export_report(performance, docs):
    strOutputFile = 'report.json'
    fo = open(strOutputFile, 'w', encoding="utf-8")
    n_in_progress = 0
    n_failed = 0
    n_total = 0
    oldest_completed_target = ''

    for key in performance:
        rec = performance[key]
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
            last_event_time = datetime.fromtimestamp(
                int(rec['finish_prev'])).strftime(DATE_FORMAT)
        else:
            last_event_time = ''

        if 'start_current' in rec:
            event_time = datetime.fromtimestamp(
                int(rec['finish_current'])).strftime(DATE_FORMAT)
        else:
            event_time = last_event_time

        if event_type == "completed":
            if oldest_completed_target == '':
                oldest_completed_target = event_time
            if event_time < oldest_completed_target:
                oldest_completed_target = event_time

        descr = docs.get(key, '')
        event_duration = rec.get("timing_sec", 0)

        status.append(
            {"eventN": key,
             "description": descr,
             "eventType": event_type,
             "eventTime": event_time,
             "eventDuration": event_duration,
             "lastEventTime": last_event_time,
             "log": rec["log"]
             }
        )

    if n_in_progress > 0:
        current_status = 'Up and Running'
    else:
        current_status = 'Idle'

    pipeline = {
        "nProgress": n_in_progress,
        "nEvents": n_total,
        "nFail": n_failed,
        "oldestCompleteTime": oldest_completed_target,
        "presentStatus": current_status
    }

    status_list["pipeline"] = pipeline
    status_list["status"] = status

    # not sure about this!
    fo.write(json.dumps(status_list))


    fo.close()
