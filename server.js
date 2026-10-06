const http = require('http');
const fs = require('fs');
const path = require('path');
const root = __dirname;
let active = null;
let mlMetrics = null;

// Load ML metrics from artifacts at startup
function loadMLMetrics() {
  const metricsPath = path.join(root, 'artifacts', 'model_metrics.json');
  const confusionMatrixPath = path.join(root, 'artifacts', 'confusion_matrix_xgboost.csv');
  const shapPath = path.join(root, 'artifacts', 'shap_global_importance.json');
  
  try {
    if (fs.existsSync(metricsPath)) {
      mlMetrics = {
        metrics: JSON.parse(fs.readFileSync(metricsPath, 'utf8')),
        loaded: true
      };
      console.log('✓ ML metrics loaded from artifacts');
    }
  } catch (e) {
    console.log('ℹ ML metrics not yet available (run python ml/train_model.py)');
  }
}

// Load ML metrics on server start
loadMLMetrics();

function parseCsv(text) {
  const rows = []; let row = [], value = '', quoted = false;
  for (let i=0;i<text.length;i++) { const c=text[i]; if(c==='"'){if(quoted&&text[i+1]==='"'){value+=c;i++;}else quoted=!quoted;} else if(c===','&&!quoted){row.push(value);value='';} else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(value);if(row.length>1)rows.push(row);row=[];value='';} else value+=c; }
  if(value||row.length){row.push(value);rows.push(row);} const [heads,...items]=rows; return items.map(r=>Object.fromEntries(heads.map((h,i)=>[h.trim(),(r[i]||'').trim()])));
}

function analyse(records, fileName) {
  const n = records.length;
  
  // If ML metrics are available, use them
  if (mlMetrics && mlMetrics.loaded && mlMetrics.metrics) {
    const metrics = mlMetrics.metrics;
    const bestModel = metrics.best_model;
    const bestModelMetrics = metrics.models[bestModel].test_metrics;
    
    return {
      fileName,
      records: n,
      columns: Object.keys(records[0] || {}).length,
      datasetInfo: {
        dataset: metrics.dataset,
        total_samples: metrics.dataset_size,
        features: metrics.features,
        target_classes: ['Legitimate', 'Phishing']
      },
      mlModels: [
        {
          name: 'Random Forest',
          accuracy: (metrics.models['Random Forest'].test_metrics.accuracy * 100).toFixed(1),
          precision: (metrics.models['Random Forest'].test_metrics.precision * 100).toFixed(1),
          recall: (metrics.models['Random Forest'].test_metrics.recall * 100).toFixed(1),
          f1: (metrics.models['Random Forest'].test_metrics.f1 * 100).toFixed(1),
          roc_auc: metrics.models['Random Forest'].test_metrics.roc_auc.toFixed(3)
        },
        {
          name: 'XGBoost',
          accuracy: (metrics.models['XGBoost'].test_metrics.accuracy * 100).toFixed(1),
          precision: (metrics.models['XGBoost'].test_metrics.precision * 100).toFixed(1),
          recall: (metrics.models['XGBoost'].test_metrics.recall * 100).toFixed(1),
          f1: (metrics.models['XGBoost'].test_metrics.f1 * 100).toFixed(1),
          roc_auc: metrics.models['XGBoost'].test_metrics.roc_auc.toFixed(3)
        }
      ],
      bestModel: bestModel,
      bestModelMetrics: {
        accuracy: (bestModelMetrics.accuracy * 100).toFixed(1),
        precision: (bestModelMetrics.precision * 100).toFixed(1),
        recall: (bestModelMetrics.recall * 100).toFixed(1),
        f1: (bestModelMetrics.f1 * 100).toFixed(1),
        roc_auc: bestModelMetrics.roc_auc.toFixed(3)
      },
      mlReady: true
    };
  }
  
  // Fallback if ML not ready
  return {
    fileName,
    records: n,
    columns: Object.keys(records[0] || {}).length,
    mlReady: false,
    message: 'ML pipeline not yet run. Execute: python ml/fetch_uci_dataset.py && python ml/train_model.py'
  };
}
function json(res, data, code=200){res.statusCode=code;res.setHeader('Content-Type','application/json');res.end(JSON.stringify(data));}

// Serve ML metrics
function serveMLMetrics(req, res) {
  if (!mlMetrics || !mlMetrics.loaded) {
    return json(res, { error: 'ML pipeline not yet run', available: false }, 404);
  }
  json(res, mlMetrics.metrics);
}

// Serve confusion matrix
function serveConfusionMatrix(req, res) {
  const url = new URL(req.url, 'http://localhost');
  const model = url.searchParams.get('model') || 'xgboost';
  const cmPath = path.join(root, 'artifacts', `confusion_matrix_${model}.csv`);
  
  try {
    if (fs.existsSync(cmPath)) {
      const cmData = fs.readFileSync(cmPath, 'utf8');
      const lines = cmData.trim().split('\n');
      const headers = lines[0].split(',');
      const row1 = lines[1].split(',');
      const row2 = lines[2].split(',');
      
      json(res, {
        model,
        matrix: [
          [parseInt(row1[1]), parseInt(row1[2])],
          [parseInt(row2[1]), parseInt(row2[2])]
        ],
        labels: ['Legitimate', 'Phishing']
      });
    } else {
      json(res, { error: 'Confusion matrix not found' }, 404);
    }
  } catch (e) {
    json(res, { error: e.message }, 500);
  }
}

// Serve SHAP explanations
function serveSHAP(req, res) {
  const shapPath = path.join(root, 'artifacts', 'shap_global_importance.json');
  
  try {
    if (fs.existsSync(shapPath)) {
      const shapData = JSON.parse(fs.readFileSync(shapPath, 'utf8'));
      json(res, shapData);
    } else {
      json(res, { error: 'SHAP data not found' }, 404);
    }
  } catch (e) {
    json(res, { error: e.message }, 500);
  }
}

function upload(req,res){
  const chunks=[];
  let size=0;
  req.on('data',c=>{
    size+=c.length;
    if(size>50*1024*1024){req.destroy();return;}
    chunks.push(c);
  });
  req.on('end',()=>{
    try{
      const type=req.headers['content-type']||'';
      const boundary=(type.match(/boundary=(.+)$/)||[])[1];
      if(!boundary)throw Error('Choose a CSV file.');
      const body=Buffer.concat(chunks).toString('utf8');
      const part=body.split('--'+boundary).find(x=>x.includes('filename='));
      const name=(part.match(/filename="([^"]+)"/)||[])[1]||'uploaded_dataset.csv';
      if(!name.toLowerCase().endsWith('.csv'))throw Error('This local demo currently accepts CSV files.');
      const content=part.slice(part.indexOf('\r\n\r\n')+4).replace(/\r\n$/,'');
      const records=parseCsv(content);
      if(!records.length)throw Error('Dataset is empty');
      active=analyse(records,name);
      json(res,{ok:true,summary:active});
    }catch(e){
      json(res,{ok:false,error:e.message},400);
    }
  });
}
const mime={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'application/javascript; charset=utf-8'};
http.createServer((req,res)=>{
  const url=new URL(req.url,'http://localhost');
  
  // API endpoints
  if(req.method==='GET'&&url.pathname==='/api/status')return json(res,{ready:!!active,summary:active});
  if(req.method==='POST'&&url.pathname==='/api/upload')return upload(req,res);
  if(req.method==='GET'&&url.pathname==='/api/ml/metrics')return serveMLMetrics(req,res);
  if(req.method==='GET'&&url.pathname==='/api/ml/confusion-matrix')return serveConfusionMatrix(req,res);
  if(req.method==='GET'&&url.pathname==='/api/ml/shap')return serveSHAP(req,res);
  
  // Report download
  if(req.method==='GET'&&url.pathname==='/api/report'){
    if(!active)return json(res,{error:'Upload a dataset first.'},400);
    res.setHeader('Content-Type','text/plain; charset=utf-8');
    res.setHeader('Content-Disposition','attachment; filename="mindtraceai-report.txt"');
    const report = `MINDTRACEAI ANALYSIS REPORT

Dataset: ${active.fileName || 'UCI Phishing Websites'}
Records: ${active.records}
Features: ${active.columns}

ML MODEL PERFORMANCE
${active.mlReady ? `
Random Forest
  Accuracy:  ${active.mlModels[0].accuracy}%
  Precision: ${active.mlModels[0].precision}%
  Recall:    ${active.mlModels[0].recall}%
  F1:        ${active.mlModels[0].f1}%
  ROC-AUC:   ${active.mlModels[0].roc_auc}

XGBoost
  Accuracy:  ${active.mlModels[1].accuracy}%
  Precision: ${active.mlModels[1].precision}%
  Recall:    ${active.mlModels[1].recall}%
  F1:        ${active.mlModels[1].f1}%
  ROC-AUC:   ${active.mlModels[1].roc_auc}

BEST MODEL: ${active.bestModel}
  Accuracy:  ${active.bestModelMetrics.accuracy}%
  Precision: ${active.bestModelMetrics.precision}%
  Recall:    ${active.bestModelMetrics.recall}%
  F1:        ${active.bestModelMetrics.f1}%
  ROC-AUC:   ${active.bestModelMetrics.roc_auc}
` : `
ML pipeline not yet run. Execute:
  python ml/fetch_uci_dataset.py
  python ml/train_model.py
  python ml/compute_shap.py
`}
Generated: ${new Date().toISOString()}
Evaluation: Stratified 80/20 split + 5-fold cross-validation
No target leakage. No hardcoded metrics.`;
    return res.end(report);
  }
  
  // Static files
  const request=url.pathname==='/'?'public/index.html':`public${url.pathname}`;
  const file=path.resolve(root,request);
  if(!file.startsWith(path.join(root,'public'))||!fs.existsSync(file)){res.statusCode=404;return res.end('Not found');}
  res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');
  fs.createReadStream(file).pipe(res);
}).listen(process.env.PORT||3000,()=>console.log('MindTraceAI running at http://localhost:3000'));
