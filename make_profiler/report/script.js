//gets input text and filters tasks on list which are including related text
function filterTarget() {
    let input, filter, table, tr, td, i, txtValue;
    input = document.getElementById("myInput");

    filter = input.value.toUpperCase().split(" ").join("_");
    table = document.getElementById("statusTable");
    tr = table.getElementsByTagName("tr");

    if (filter.startsWith('"') && filter.endsWith('"')) {
        filter = filter.substring(1, filter.length - 1)
        for (i = 0; i < tr.length; i++) {
            td = tr[i].getElementsByTagName("td")[0];
            if (td) {
                txtValue = td.childNodes[0].textContent || td.innerText;
                if (txtValue.toUpperCase() === filter) {
                    tr[i].style.display = "";
                } else {
                    tr[i].style.display = "none";
                }
            }
        }
    } else {
        for (i = 0; i < tr.length; i++) {
            td = tr[i].getElementsByTagName("td")[0];
            if (td) {
                txtValue = td.textContent || td.innerText;
                if (txtValue.toUpperCase().includes(filter)) {
                    tr[i].style.display = "";
                } else {
                    tr[i].style.display = "none";
                }
            }
        }
    }
}

//refresh page every 5 minutes
setInterval(function () {
    getStatus(url);
}, 1000 * 5 * 60);

const url = "report.json";
const errorTxt = "Something went wrong parsing report details"

async function getStatus(url) {
    await fetch(url).then((response) => {
        if (response.ok) {
            return response.json();
        }
        throw new Error(errorTxt);
    }).then((responseJson) => {
        const statusRecords = responseJson.status;
        const pipeline = responseJson.pipeline;
        const pipelineTable =
            `
                        <div id="statusReport">
                        <img class="img" src='report/Kontur_logo_main.png' />
                            <div class="vertical-center">
                                <p>PIPELINE DASHBOARD</p>
                            </div>
                        </div>
                        <h2>Pipeline Status</h2>
                        <table id="pipelineTable">
                            <tr>
                                <td><b>Present Status</b></td>
                                <td align="center"><b>${pipeline.presentStatus}</b></td>
                            </tr>
                            <tr>
                                <td>Targets total</td>
                                <td align="center">${pipeline.numberOfTargetsTotal}</td>
                            </tr>
                            <tr>
                                <td>Targets in progress</td>
                                <td align="center">${pipeline.numberOfTargetsInProgress}</td>
                            </tr>
                            <tr>
                                <td>Targets failed</td>
                                <td align="center">${pipeline.numberOfTargetsFailed}</td>
                            </tr>
                            <tr>
                                <td>Targets never started</td>
                                <td align="center">${pipeline.numberOfTargetsNeverStarted}</td>
                            </tr>
                            <tr>
                                <td>Oldest completed target</td>
                                <td align="center">${formatDate(pipeline.oldestCompletionTime)}</td>
                            </tr>
                        </table>
                        <h2>Target status</h2><a id="statusChart" target="_blank" href="make.svg">Status Chart</a></br>
                        <input type="text" id="myInput" onkeyup="filterTarget()" placeholder="Search for target name.." title="Type in a name" />`


        let statusTable = `
                        <table id="statusTable" class="sortable">
                            <tr class="header">
                                        <th>Target name</th>
                                        <th>Last completed date</th>
                                        <th>Status</th>
                                        <th>Status date</th>
                                        <th>Duration</th>
                                        <th>Log</th>
                            </tr>`

        for (let i = 0; i < statusRecords.length; i++) {
            statusTable += `<tr class=${statusRecords[i].targetType}>
            <td>${statusRecords[i].targetName}<p id='description'>${statusRecords[i].targetDescription}</p></td>
            <td>${statusRecords[i].lastTargetCompletionTime ? formatDate(statusRecords[i].lastTargetCompletionTime) : '-'}</td>
            <td>${statusRecords[i].targetType}</td>
            <td>${statusRecords[i].targetTime ? formatDate(statusRecords[i].targetTime) : '-'}</td>
            <td>${statusRecords[i].targetDuration ? new Date(statusRecords[i].targetDuration * 1000).toISOString().slice(11, 19) : '-'}</td>`;
            // toISOString Returns 2011-10-05T14:48:00.000Z From 11 to 19 gives hh:mm:ss
            statusRecords[i].targetLog ? statusTable += `<td><a target='_blank' href=${statusRecords[i].targetLog}>...</a></td></tr>` : statusTable += `<td>-</td></tr>`
        }

        statusTable += "</table>";

        const status = document.getElementById("status");
        status.innerHTML = pipelineTable + statusTable;
        sorttable.makeSortable(status.querySelector('.sortable'));
    })
        .catch((error) => {
            document.getElementById("status").innerHTML = errorTxt
            console.log(error.message)
        });
}

function formatDate(date) {
    if (!date) {
        return ""
    } else {
        date = new Date(date);
        //YYYY-mm-dd hh:mm:ss adds 0 if needed
        return date == null
            ? ""
            : ("0" + date.getDate()).slice(-2) +
            "-" +
            ("0" + (date.getMonth() + 1)).slice(-2) +
            "-" +
            date.getFullYear() +
            " " +
            ("0" + date.getHours()).slice(-2) +
            ":" +
            ("0" + date.getMinutes()).slice(-2) +
            ":" +
            ("0" + date.getSeconds()).slice(-2);
    }
}

getStatus(url);