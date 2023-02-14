from datetime import datetime
import json
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

status_list = {}
status = []


def export_report(performance, docs, targets):
    strOutputFile = 'report.json'
    fo = open(strOutputFile, 'w', encoding="utf-8")
    n_in_progress = 0
    n_failed = 0
    n_total = 0
    oldest_completed_target = ''

    not_started_targets = set(targets)

    for key in performance:
        if key in targets:
            # Only targets which are present in makefile are displayed
            not_started_targets.remove(key)

            rec = performance[key]
            n_total += 1
            if rec["running"]:
                # running flag has the highest priority.
                # target can be also marked as done, if it was built on previous run.
                event_type = "started"
                n_in_progress += 1
            elif rec["failed"]:
                event_type = "failed"
                n_failed += 1
            elif rec["done"]:
                event_type = "completed"
            else:
                # this usually occurs when target is completed, but corresponding file or folder is not found.
                event_type = "completed with no output"

            event_time = ""
            last_event_time = ""

            if 'start_current' in rec:
                # All the targets in the curent run have rec['finish_current']
                event_time = datetime.utcfromtimestamp(int(rec['finish_current'])).strftime(DATE_FORMAT)
                #last completed date is just an event date for completed tasks.
                if event_type == "completed" or event_type == "completed with no output":
                    last_event_time = event_time
                #otherwise let's take it from previous run
                elif ('finish_prev' in rec):
                    last_event_time = datetime.utcfromtimestamp( int(rec['finish_prev'])).strftime(DATE_FORMAT)

            else:
                # target in previous run. there is no timestamp in the current run,
                # so we use timestamp from the previous run.
                if ('finish_prev' in rec):
                    event_time = datetime.utcfromtimestamp( int(rec['finish_prev'])).strftime(DATE_FORMAT)
                    if event_type != "failed":
                        last_event_time = event_time

            if event_type == "completed":
                if oldest_completed_target == '':
                    oldest_completed_target = event_time
                if event_time < oldest_completed_target:
                    oldest_completed_target = event_time

            descr = docs.get(key, '')
            event_duration = rec.get("timing_sec", 0)

            if last_event_time == '':
                last_event_time = None

            if not "log" in rec:
                rec["log"] = ""

            status.append(
                {"targetName": key,
                 "targetDescription": descr,
                 "targetType": event_type,
                 "targetTime": event_time,
                 "targetDuration": event_duration,
                 "lastTargetCompletionTime": last_event_time,
                 "targetLog": rec["log"]
                 }
            )

    for target in not_started_targets:
        status.append({
            "targetName": target,
            "targetDescription": docs.get(target, ''),
            "targetType": "never started"
        })

    if n_in_progress > 0:
        current_status = 'Up and Running'
    else:
        current_status = 'Idle'

    n_never_started = len(not_started_targets)

    pipeline = {
        "numberOfTargetsInProgress": n_in_progress,
        "numberOfTargetsTotal": n_total + n_never_started,
        "numberOfTargetsFailed": n_failed,
        "numberOfTargetsNeverStarted": n_never_started,
        "oldestCompletionTime": oldest_completed_target,
        "presentStatus": current_status
    }

    status_list["pipeline"] = pipeline
    status_list["status"] = status

    fo.write(json.dumps(status_list))

    fo.close()
