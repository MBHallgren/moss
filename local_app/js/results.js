const { exec } = require('child_process');
const fs = require('fs');
const storage = require('electron-json-storage');

storage.get('currentConfig', function(error, data) {
  if (error) throw error;

  var element = document.getElementById('current-config');
  element.textContent = data.db_dir;
  var exe_path = data.exepath;
});


var configfile = "None";
document.getElementById("configfile").innerHTML = configfile;

function recompilereports() {

    var loader = document.getElementById('loader');
    loader.style.display = 'block';
    document.getElementById('loadermessage').innerHTML = "Recompiling all reports.";
    storage.get('currentConfig', function(error, data) {
          if (error) throw error;

          execstring = `python3 ${data.exepath}src/testpdf.py -db_dir ${data.db_dir} -exepath ${data.exepath}`;
          console.log(execstring)

          exec(execstring, (error, stdout, stderr) => {



            if (error) {
              //If error, change accepted ui to failure, which attached message.
              console.error(`exec error: ${error}`);
              alert(`exec error: ${error}`);
              return;
            }
            console.log(`stdout: ${stdout}`);
            console.error(`stderr: ${stderr}`);

            //Automatic change of correct system config to
            alert("All reports have finished compiling");

            loader.style.display = 'none';
            document.getElementById('loadermessage').innerHTML = "Finished recompling all reports.";

          });
    });


}

function readSingleFile(e) {
    var file = e.target.files[0];
    if (!file) {
        return;
    }
    var reader = new FileReader();
    reader.onload = function(e) {
        var contents = e.target.result;
        displayContents(contents);
    };
    reader.readAsText(file);
}

function showFinishedAnalyses() {
    storage.get('currentConfig', function(error, data) {
              if (error) throw error;

              let sql = `SELECT * FROM statustable`;
              document.getElementById('showData').innerHTML="" ;
                let db_dir = document.getElementById('current-config').innerHTML
                const db = require('better-sqlite3')(db_dir + 'moss.db');
                const sql_data_obj = db.prepare(sql).all();
                console.log(sql_data_obj);

                tableFromObj(sql_data_obj, data);
        });

}

function openPDF(id, data){
  console.log(data.db_dir + "analysis/" + document.getElementById(id).name + "/" + id + "_report.pdf");
  window.open(data.db_dir + "analysis/" + document.getElementById(id).name + "/" + id + "_report.pdf");
  //return false;
}


function tableFromObj(sql_data_obj, data) {
        var divShowData = document.getElementById('showData');
        divShowData.innerHTML = "";
		db_dir = document.getElementById('current-config').innerHTML;


        // ('Book ID', 'Book Name', 'Category' and 'Price')
        var col = [];
        for (var i = 0; i < sql_data_obj.length; i++) {
            for (var key in sql_data_obj[i]) {
                if (col.indexOf(key) === -1) {
                    col.push(key);
                }
            }
        }

        console.log(col);

        // Create a table.
        var table = document.createElement("table");
        table.innerHTML = "";

        // Create table header row using the extracted headers above.
        var tr = table.insertRow(-1);                   // table row.

        for (var i = 0; i < col.length; i++) {
            var th = document.createElement("th");      // table header.
            th.innerHTML = col[i];
            tr.appendChild(th);
        }

        // add json data to the table as rows.
        for (var i = 0; i < sql_data_obj.length; i++) {

            tr = table.insertRow(-1);

            for (var j = 0; j < col.length; j++) {
                var tabCell = tr.insertCell(-1);
                tabCell.innerHTML = sql_data_obj[i][col[j]];
            }
            if (sql_data_obj != "none") {
                var tabCell = tr.insertCell(-1);
                var img = document.createElement('img');
                img.id = sql_data_obj[i].entryid;
                img.name = sql_data_obj[i].entryid;
                img.src = data.exepath + "local_app/images/report-icon.png";
                img.setAttribute('height', '17pt');
                img.innerHTML = sql_data_obj[i].entryid;
                img.onclick = function() {openPDF(this.id, data)};
                tabCell.appendChild(img);
            };


        }



        // Now, add the newly created table with json data, to a container.
        divShowData.appendChild(table);
    }
