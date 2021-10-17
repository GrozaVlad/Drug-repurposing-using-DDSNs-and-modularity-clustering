const fs = require('fs');
const readline = require('readline');
const convert = require('xml-js');
const {promisify} = require('util');
const {Client} = require('pg');

let databaseGenes = {};

function processXMLEntry() {
  // convert xml to json
  var xml = fs.readFileSync('./temporary.xml');
  var options = {compact: true, ignoreComment: true, spaces: 4};
  // console.log(xml);
  const results = JSON.parse(convert.xml2json(xml,options));
  // console.log("Here");
  let isApproved = true;
  if(results.drug.groups.group instanceof Array) {
    const approved = results.drug.groups.group.find(element => element._text === 'approved');
    if(!approved){
      isApproved = false;
    }
  } else {
    if(results.drug.groups.group._text !== 'approved') {
      isApproved = false;
    }
  }
  if(!isApproved){
    return null;
  }
  // console.log(JSON.stringify(results));
  let atc_code = '';
  if(results.drug["atc-codes"]["atc-code"]){
    if(results.drug["atc-codes"]["atc-code"] instanceof Array){
      atc_code = '{';
      for(i=0;i<results.drug["atc-codes"]["atc-code"].length;i++){
        // atc_code.push(results.drug["atc-codes"]["atc-code"][i]._attributes.code);
        atc_code+=`${results.drug["atc-codes"]["atc-code"][i]._attributes.code},`;
      }
      if(atc_code.slice(0,-1)){
        atc_code= atc_code.slice(0,-1);
     }
     atc_code+='}';
    } else {
      if(results.drug["atc-codes"]["atc-code"]._attributes){
        atc_code+=`{${results.drug["atc-codes"]["atc-code"]._attributes.code}}`;
        // atc_code.push(results.drug["atc-codes"]["atc-code"]._attributes.code);
      }
    }
  }
  let smiles_code = '';
  let inchi_code = '';
  let inchi_key = '';
  let molecular_formula = '';
  if(results.drug["calculated-properties"]){
    // console.log("MASA");
    if(results.drug["calculated-properties"]["property"]) {
    if(results.drug["calculated-properties"]["property"] instanceof Array){
      // if(results.drug["calculated-properties"]["property"]){
        // console.log(JSON.stringify(results.drug["calculated-properties"]["property"]));
        smiles_object = results.drug["calculated-properties"]["property"].find(element=>element.kind._text === 'SMILES');
        smiles_code = smiles_object ? smiles_object.value._text : '';
        inchi_code_object = results.drug["calculated-properties"]["property"].find(element=>element.kind._text === 'InChI');
        inchi_code = inchi_code_object ? inchi_code_object.value._text : '';
        inchi_key_object = results.drug["calculated-properties"]["property"].find(element=>element.kind._text === 'InChIKey');
        inchi_key = inchi_key_object ? inchi_key_object.value._text : '';
        molecular_formula_object = results.drug["calculated-properties"]["property"].find(element=>element.kind._text === 'Molecular Formula');
        molecular_formula = molecular_formula_object ? molecular_formula_object.value._text : '';
      // }
    } else if(!(results.drug["calculated-properties"]["property"] instanceof Array)){
      // if(results.drug["calculated-properties"]["property"]){
        // console.log(JSON.stringify(results.drug["calculated-properties"]["property"]));
        kind = results.drug["calculated-properties"]["property"].kind._text;
        value = results.drug["calculated-properties"]["property"].value._text;
        if(kind === 'SMILES'){
          smiles_code = value ? value : '';
        } else if(kind === 'InChI') {
          inchi_code = value ? value : '';
        } else if(kind === 'InChIKey') {
          inchi_key = value ? value : '';
        } else if(kind === 'Molecular Formula') {
          molecular_formula = value ? value : '';
        }
      // }
    } 
  }
  }
  // console.log(atc_code);
  // console.log({name: results.drug.name,
  //              cas: results.drug["cas-number"],
  //              targets: results.drug.targets});
  
  const drugName = results.drug.name._text.replace(/'/g,"''");
  let genes = '';
  if(results.drug.targets.target){
    const targets = results.drug.targets.target;
    if(targets instanceof Array){
      genes = '{';
      for(i=0;i<targets.length;i++){
        // some targets don't have polypeptide info
        if(targets[i].polypeptide){
          if(targets[i].polypeptide["gene-name"]){
            const geneName = targets[i].polypeptide["gene-name"]._text;
          //  genes.push(targets[i].polypeptide["gene-name"]._text);
           // complete genes for genes table
           if(databaseGenes[`${geneName}`])
           {
             if(targets[i].polypeptide._attributes.id){
               databaseGenes[`${geneName}`].gene_id = targets[i].polypeptide._attributes.id
             }
             databaseGenes[`${geneName}`].drugs+=`"${drugName}",`
           }else {
            databaseGenes[`${geneName}`] = {
              drugs: `{"${drugName}",`
            }
            if(targets[i].polypeptide._attributes.id){
              databaseGenes[`${geneName}`].gene_id = targets[i].polypeptide._attributes.id
            }
           }
           // complete genes for drug table 
           

           if(targets[i].actions.action) {
             if(targets[i].actions.action._text) {
              genes+= `{"${geneName}","${targets[i].actions.action._text}"},`
             }
           } else {
              genes+=`{"${geneName}","binder"},`;
           }
          }
        }
      }
      //remove last only if we have an existing element in the array, add closing parantheses
      if(genes.slice(0,-1)){
         genes= genes.slice(0,-1);
      }
      genes+='}';
    } else {
      if(targets.polypeptide){
        if(targets.polypeptide["gene-name"]){
          const geneName = targets.polypeptide["gene-name"]._text;
          if(databaseGenes[`${geneName}`])
           {
             if(targets.polypeptide._attributes.id){
               databaseGenes[`${geneName}`].gene_id = targets.polypeptide._attributes.id
             }
             databaseGenes[`${geneName}`].drugs+=`"${drugName}",`
           }else {
            databaseGenes[`${geneName}`] = {
              drugs: `{"${drugName}",`
            }
            if(targets.polypeptide._attributes.id){
              databaseGenes[`${geneName}`].gene_id = targets.polypeptide._attributes.id
            }
           }
          // genes.push(targets.polypeptide["gene-name"]._text);
          if(targets.actions.action) {

            if(targets.actions.action._text) {
              if(!geneActionTypes.includes(`${targets.actions.action._text}`)){
                console.log(`${targets.actions.action._text}`);
                geneActionTypes.push(`${targets.actions.action._text}`);
              }
             genes+= `{{"${geneName}","${targets.actions.action._text}"}}`
            }
          } else {
             genes+=`{{"${geneName}","binder"}}`;
          }
        }
      }
    }
  }
  genes = genes.replace(/'/g,"''");
  return {
    name: drugName,
    smiles_code: smiles_code ? smiles_code : "",
    inchi_code: inchi_code ? inchi_code : "",
    inchi_key: inchi_key ? inchi_key: "",
    molecular_formula: molecular_formula ? molecular_formula: "",
    cas: results.drug["cas-number"]._text,
    atc_code: atc_code ? atc_code : "",
    genes: genes
  }
}
const database_names = ['3.0','4.1','4.2','4.3','4.5.0','5.0.0','5.0.1','5.0.2','5.0.3','5.0.4','5.0.5','5.0.6','5.0.7','5.0.8','5.0.9','5.0.10','5.1.0','5.1.8'];
const geneActionTypes = [];

async function processLineByLine() {
  const connectionString = `postgres://vlad:vlad@localhost:5433/drugbank`
  const client = new Client({connectionString});
  await client.connect();
  const database = '5.0.9';
    const fileStream = fs.createReadStream(`../Desktop/drugbanks/hyperion/${database}/drugbank.xml`);
    const logger = fs.createWriteStream('./temporary.xml', {
      flags: 'a'
    });

    const truncate = promisify(fs.truncate).bind(fs);
    const loggerWrite = promisify(logger.write).bind(logger);

    const rl = readline.createInterface({
      input: fileStream,
      crlfDelay: Infinity
    });
    // Note: we use the crlfDelay option to recognize all instances of CR LF
    // ('\r\n') in input.txt as a single line break.

    for await (const line of rl) {
      // Each line in input.txt will be successively available here as `line`.
      // console.log(`${line}`);
      if(line.includes('<drug type=')){
        await truncate('temporary.xml');
        await loggerWrite(`${line}\n`);
      } else if(`${line}` === '</drug>'){
        await loggerWrite(`${line}\n`);
        const drug = processXMLEntry();
        if(drug) {
          console.log(drug);

          await client.query(`INSERT INTO public.all_drugs_info(
            name, cas, gene_target_ids_array,smiles_code,inchi_code,inchi_key,molecular_formula,atc_code,drugbank_version)
            VALUES ('${drug.name}','${drug.cas}','${drug.genes ? drug.genes: '{}'}','${drug.smiles_code}','${drug.inchi_code}','${drug.inchi_key}','${drug.molecular_formula}',
            '${drug.atc_code ? drug.atc_code : '{}'}', '${database}')`)  
        }

        
      } else {
      // write to temporary file
        await loggerWrite(`${line}\n`);
    }
    }
    // process databaseGenes
    for (const [key, value] of Object.entries(databaseGenes)) {
      // console.log(`${key}: ${value}`);
      const name = key.replace(/'/g,"''");
      
      const drugs_ids = `${value.drugs.slice(0,-1)}}`;
      // console.log({
      //   name,
      //   drugs_ids,
      //   gene_id: value.gene_id
      // });
            await client.query(`INSERT INTO public.all_genes(
          name, gene_id, drugs_ids, drugbank_version)
          VALUES ('${name}','${value.gene_id}','${drugs_ids}', '${database}')`);
    }
  await client.end();
  console.log(geneActionTypes);
  return 'ceva';
}

processLineByLine();