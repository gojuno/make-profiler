function filterTarget(){var t,e,a=document.getElementById("myInput").value.toUpperCase().split(" ").join("_"),n=document.getElementById("statusTable").getElementsByTagName("tr");if(a.startsWith('"')&&a.endsWith('"'))for(a=a.substring(1,a.length-1),e=0;e<n.length;e++)(t=n[e].getElementsByTagName("td")[0])&&((t.childNodes[0].textContent||t.innerText).toUpperCase()===a?n[e].style.display="":n[e].style.display="none");else for(e=0;e<n.length;e++)(t=n[e].getElementsByTagName("td")[0])&&(-1<(t.textContent||t.innerText).toUpperCase().indexOf(a)?n[e].style.display="":n[e].style.display="none")}async function getStatus(t){let e=await fetch(t);return e.json()}function formatDate(t){var e,a;return null===t?"":(a=(t=new Date(t)).getUTCFullYear(),e=t.getUTCDate(),a+"-"+(a=(a=t.getUTCMonth()+1)<10?"0"+a:a)+"-"+(e=e<10?"0"+e:e)+" "+(a=(a=t.getUTCHours())<10?"0"+a:a)+":"+(e=(e=t.getUTCMinutes())<10?"0"+e:e)+":"+(a=(a=t.getUTCSeconds())<10?"0"+a:a))}setTimeout(function(){window.location.reload(1)},3e5),getStatus("report.json").then(t=>{var e=t.status,t=t.pipeline,t=`
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
                            <td align="center"><b>`+t.presentStatus+`</b></td>
                        </tr>
                        <tr>
                            <td>Targets total</td>
                            <td align="center">`+t.nEvents+`</td>
                        </tr>
                        <tr>
                            <td>Targets in progress</td>
                            <td align="center">`+t.nProgress+`</td>
                        </tr>
                        <tr>
                            <td>Targets frozen</td>
                            <td align="center">0</td>
                        </tr>
                        <tr>
                            <td>Targets failed</td>
                            <td align="center">`+t.nFail+`</td>
                        </tr>
                        <tr>
                            <td>Oldest completed target</td>
                            <td align="center">`+formatDate(t.oldestCompleteTime)+`</td>
                        </tr>
                    </table>
                    <h2>Target status</h2><a id="statusChart" target="_blank" href="make.svg">Status Chart</a></br>
                    <input type="text" id="myInput" onkeyup="filterTarget()" placeholder="Search for target name.." title="Type in a name" />`;let a=`
                    <table id="statusTable" class="sortable">
                        <tr class="header">
                                    <th>Target name</th>
                                    <th>Last completed date</th>
                                    <th>Status</th>
                                    <th>Status date</th>
                                    <th>Duration</th>
                                    <th>Log</th>
                        </tr>`;for(var n=0;n<e.length;n++)a=(a=(a=(a=(a=(a=(a+="<tr class="+e[n].eventType+">")+"<td>"+e[n].eventN+"<p id='description'>"+e[n].description+"</p></td>")+"<td>"+formatDate(e[n].lastEventTime)+"</td>")+"<td>"+e[n].eventType+"</td>")+"<td>"+formatDate(e[n].eventTime)+"</td>")+"<td>"+new Date(1e3*e[n].eventDuration).toISOString().slice(11,19))+"<td><a target='_blank' href="+e[n].log+">...</a></td></tr>";a+="</table>",document.getElementById("status").innerHTML=t+a});