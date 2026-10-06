# MindTraceAI Updated Dashboard

The `public/` directory contains the rebuilt local-first data intelligence dashboard.

It accepts CSV, TSV, JSON, and JSONL files and creates a report with:
- dataset overview and quality metrics
- missing-value and duplicate checks
- inferred schema and field types
- numeric distributions and outlier signals
- categorical breakdowns
- searchable, sortable, paginated data preview
- downloadable JSON report

Uploaded data is processed locally in the browser. The existing `ml/` training and testing files were preserved unchanged.

## Run

```bash
npm start
```

Then open `http://localhost:3000`.
