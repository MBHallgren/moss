const { exec } = require('child_process');
const fs = require('fs')
const storage = require('electron-json-storage');




storage.get('currentConfig', function(error, data) {
  if (error) throw error;

  var element = document.getElementById('current-config');
  element.textContent = data.db_dir;
  var element = document.getElementById('current-exepath');
  element.textContent = data.exepath;


});

function select_output(){
    var db_dir = document.getElementById('current-config').innerHTML;

    readTextFile(db_dir + "analyticalFiles/workflow.json", function(text){
        var data = JSON.parse(text);
        console.log(data);
        document.getElementById('workflowjson').innerHTML = data;

        var items = data;

        var result_flowcell = [];
        var result_kit = [];
        var result_barcoding_config_name = [];
        var result_model_version = [];

        for (var item, i = 0; item = items[i++];) {
          var flowcell = item.flowcell;
          var kit = item.kit;
          var barcoding_config_name = item.barcoding_config_name;
          var model_version = item.model_version;
          result_flowcell.push(flowcell);
          result_kit.push(kit);
          result_barcoding_config_name.push(barcoding_config_name);
          result_model_version.push(model_version);
        }

        const unique_flowcell = [...new Set(result_flowcell)];
        const unique_kit = [...new Set(result_kit)];
        const unique_barcoding_config_name = [...new Set(result_barcoding_config_name)];
        const unique_model_version = [...new Set(result_model_version)];

        var select = document.getElementById("flow-cell");
        //var unames = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"];
        for (var i = 0; i < unique_flowcell.length; i++) {
            var opt = unique_flowcell[i];
            var el = document.createElement("option");
            el.textContent = opt;
            el.value = opt;
            select.appendChild(el);
          }

        var select = document.getElementById("kit");
        //var unames = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"];
        for (var i = 0; i < unique_kit.length; i++) {
            var opt = unique_kit[i];
            var el = document.createElement("option");
            el.textContent = opt;
            el.value = opt;
            select.appendChild(el);
          }

        var select = document.getElementById("barcoding_config_name");
        //var unames = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"];
        for (var i = 0; i < unique_barcoding_config_name.length; i++) {
            var opt = unique_barcoding_config_name[i];
            var el = document.createElement("option");
            el.textContent = opt;
            el.value = opt;
            select.appendChild(el);
          }

        var select = document.getElementById("model_version");
        //var unames = ["Alpha", "Bravo", "Charlie", "Delta", "Echo"];
        for (var i = 0; i < unique_model_version.length; i++) {
            var opt = unique_model_version[i];
            var el = document.createElement("option");
            el.textContent = opt;
            el.value = opt;
            select.appendChild(el);
          }

    });
}

function start_base_calling(){

    var flowcell = document.getElementById('flow-cell').value;
    var kit = document.getElementById('kit').value;
    var barcoding_config_name = document.getElementById('barcoding_config_name').value;
    var model_version = document.getElementById('model_version').value;
    var db_dir = document.getElementById('current-config').innerHTML;

    var input = document.getElementById('fast5-input-field');
    var output_dir = document.getElementById('output-field').value;

    var single_path = input.files.item(0).path;
    var path_list = single_path.split("/");
    var path_slice= path_list.slice(1, -1);
    var input_path = "/" + path_slice.join("/") + "/";

    cmd = `guppy_basecaller -i ${input_path} -s ${output_dir}/ --flowcell ${flowcell} --kit ${kit} --device "cuda:0" --compress_fastq`;
    console.log(cmd);
    /*
    if (fs.existsSync(output_dir)) {
        console.log("Base calling has begun.");

        alert("Base calling has begun.");

        exec(cmd, (error, stdout, stderr) => {

            if (error) {
                alert(`exec error: ${error}`);
                document.getElementById('metadata-sheet-msg').innerHTML = `Basecalling has failed: ${error}`;
              console.error(`exec error: ${error}`);
              return;
            } else {
                alert("Analysis has been completed.");
                document.getElementById('metadata-sheet-msg').innerHTML = `Basecalling has been completed`;
            }

            console.log(`stdout: ${stdout}`);
            console.error(`stderr: ${stderr}`);



      });
    } else {
        alert("The given output directory does not exist");
    }*/
}

function execute_command_as_subprocess(cmd, print_msg) {
    console.log(cmd);

    console.log("Metadata Sheet Creation has begun.");

    alert("Metadata Sheet Creation has begun.");



    exec(cmd, (error, stdout, stderr) => {

        if (error) {
            alert(`exec error: ${error}`);
          console.error(`exec error: ${error}`);
          return;
        } else {
            alert("Metadata Sheet Creation has been completed.");
            document.getElementById('metadata-sheet-msg').innerHTML = print_msg;
        }

        console.log(`stdout: ${stdout}`);
        console.error(`stderr: ${stderr}`);



      });

}

function readTextFile(file, callback) {
    var rawFile = new XMLHttpRequest();
    rawFile.overrideMimeType("application/json");
    rawFile.open("GET", file, true);
    rawFile.onreadystatechange = function() {
        if (rawFile.readyState === 4 && rawFile.status == "200") {
            callback(rawFile.responseText);
        }
    }
    rawFile.send(null);
}