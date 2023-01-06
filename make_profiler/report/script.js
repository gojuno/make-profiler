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
    loadStatus();
}, 1000 * 5 * 60);

loadStatus = () => {
    getStatus("report.json").then((resp) => {
        let recs = resp.status;
        let pipeline = resp.pipeline;
        let pipelineTable =
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
                                <td align="center">${pipeline.nEvents}</td>
                            </tr>
                            <tr>
                                <td>Targets in progress</td>
                                <td align="center">${pipeline.nProgress}</td>
                            </tr>
                            <tr>
                                <td>Targets frozen</td>
                                <td align="center">0</td>
                            </tr>
                            <tr>
                                <td>Targets failed</td>
                                <td align="center">${pipeline.nFail}</td>
                            </tr>
                            <tr>
                                <td>Oldest completed target</td>
                                <td align="center">${formatDate(pipeline.oldestCompleteTime)}</td>
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

        for (let i = 0; i < recs.length; i++) {
            statusTable += `<tr class=${recs[i].eventType}>
            <td>${recs[i].eventN}<p id='description'>${recs[i].description}</p></td>
            <td>${formatDate(recs[i].lastEventTime)}</td>
            <td>${recs[i].eventType}</td>
            <td>${formatDate(recs[i].eventTime)}</td>
            <td>${new Date(recs[i].eventDuration * 1000).toISOString().slice(11, 19)}</td>
            <td><a target='_blank' href=${recs[i].log}>...</a></td></tr>`;
        }

        statusTable += "</table>";

        const status = document.getElementById("status");
        status.innerHTML = pipelineTable + statusTable;
        sorttable.makeSortable(status.querySelector('.sortable'));
    })
}

async function getStatus(url) {
    let response = await fetch(url);
    return response.json();
}

function formatDate(date) {
    if (date === null) {
        return "";
    }

    date = new Date(date);
    let aaaa = date.getUTCFullYear();
    let gg = date.getUTCDate();
    let mm = (date.getUTCMonth() + 1);

    if (gg < 10)
        gg = "0" + gg;

    if (mm < 10)
        mm = "0" + mm;

    let cur_day = aaaa + "-" + mm + "-" + gg;

    let hours = date.getUTCHours()
    let minutes = date.getUTCMinutes()
    let seconds = date.getUTCSeconds();

    if (hours < 10)
        hours = "0" + hours;

    if (minutes < 10)
        minutes = "0" + minutes;

    if (seconds < 10)
        seconds = "0" + seconds;

    return cur_day + " " + hours + ":" + minutes + ":" + seconds;
}

loadStatus();