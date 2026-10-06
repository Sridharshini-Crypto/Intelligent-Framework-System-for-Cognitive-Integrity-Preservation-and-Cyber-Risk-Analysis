import { useMemo, useRef, useState, type DragEvent, type ChangeEvent } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import {
  AlertTriangle, ArrowDown, ArrowUp, BarChart3, Check, ChevronLeft, ChevronRight,
  Columns3, Database, Download, FileJson, FileSpreadsheet, FileText,
  Hash, Info, LayoutDashboard, ListFilter, RefreshCw, Search, ShieldCheck, Upload,
  X, CalendarDays,
} from 'lucide-react';
import { parseDataFile, formatBytes, formatNumber, type Cell, type ColumnProfile, type DatasetAnalysis } from '@/lib/data-profiler';

const queryClient = new QueryClient();
const PAGE_SIZE = 12;

function Logo() {
  return <div className="wordmark"><span className="brand-mark">M</span><span>MindTrace<span>AI</span></span></div>;
}

function FileGlyph({ extension }: { extension: string }) {
  return extension === 'JSON' || extension === 'JSONL' ? <FileJson /> : <FileSpreadsheet />;
}

function EmptyState({ onFile }: { onFile: (file: File) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');
  const handleFile = (file?: File) => {
    if (!file) return;
    const extension = file.name.toLowerCase().split('.').pop();
    if (!['csv', 'tsv', 'json', 'jsonl'].includes(extension ?? '')) {
      setError('That format is not supported. Choose a CSV, TSV, JSON, or JSONL file.');
      return;
    }
    setError('');
    onFile(file);
  };
  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault(); setDragging(false); handleFile(event.dataTransfer.files[0]);
  };
  const onChange = (event: ChangeEvent<HTMLInputElement>) => handleFile(event.target.files?.[0]);
  return (
    <>
      <div
        className={`upload-zone ${dragging ? 'is-dragging' : ''}`}
        onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        data-testid="dropzone-upload"
      >
        <input ref={inputRef} className="hidden-input" type="file" accept=".csv,.tsv,.json,.jsonl" onChange={onChange} data-testid="input-file-upload" />
        <div className="upload-inner">
          <div className="upload-icon"><Upload size={23} /></div>
          <h2>Bring a dataset into the lab</h2>
          <p>Drop a file here, or browse your local files to begin profiling.</p>
          <button className="primary-button" onClick={(event) => { event.stopPropagation(); inputRef.current?.click(); }} data-testid="button-browse-files">
            <FileText size={14} /> Browse files
          </button>
          <small>CSV · TSV · JSON · JSONL &nbsp; / &nbsp; nothing leaves your browser</small>
        </div>
      </div>
      <div className="sample-row" aria-label="Supported examples">
        <span className="sample-chip">customers.csv</span>
        <span className="sample-chip">events.jsonl</span>
        <span className="sample-chip">survey.tsv</span>
      </div>
      {error && <div className="empty-error" role="alert" data-testid="status-upload-error"><X size={17} /><div><strong>Could not use that file</strong><span>{error}</span></div></div>}
    </>
  );
}

function LoadingState() {
  return <div className="loading-shell" data-testid="status-parsing">
    <div className="skeleton" style={{ height: 96 }} />
    <div className="metrics-grid"><div className="skeleton" style={{ height: 115 }} /><div className="skeleton" style={{ height: 115 }} /><div className="skeleton" style={{ height: 115 }} /><div className="skeleton" style={{ height: 115 }} /></div>
    <div className="home-grid"><div className="skeleton" style={{ height: 350 }} /><div className="skeleton" style={{ height: 350 }} /></div>
  </div>;
}

function TypeIcon({ type }: { type: ColumnProfile['type'] }) {
  if (type === 'numeric') return <Hash />;
  if (type === 'date') return <CalendarDays />;
  if (type === 'boolean') return <Check />;
  return <FileText />;
}

function MetricCard({ label, value, sub, warning = false }: { label: string; value: string; sub: string; warning?: boolean }) {
  return <div className={`metric-card ${warning ? 'warn' : ''}`} data-testid={`metric-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <span className="metric-label">{label}</span><strong className="metric-value">{value}</strong><span className="metric-sub">{sub}</span>
  </div>;
}

function QualityPanel({ analysis }: { analysis: DatasetAnalysis }) {
  const missingRate = analysis.totalCells ? analysis.missingCells / analysis.totalCells : 0;
  return <section className="panel quality-panel" id="quality">
    <div className="panel-head"><div><h2>Quality signals</h2><p>Fast checks for the things most likely to change your read.</p></div><ShieldCheck size={20} color="#18775e" /></div>
    <div className="panel-body">
      <div className="issue">
        <div className={`issue-icon ${analysis.missingCells ? 'warn' : 'good'}`}>{analysis.missingCells ? <AlertTriangle size={15} /> : <Check size={15} />}</div>
        <div><strong>{analysis.missingCells ? `${formatNumber(analysis.missingCells)} missing values found` : 'No missing values found'}</strong><p>{analysis.missingCells ? `${(missingRate * 100).toFixed(1)}% of all cells are empty or null-like. Review affected fields before drawing conclusions.` : 'Every observed cell contains a value.'}</p></div>
      </div>
      <div className="issue">
        <div className={`issue-icon ${analysis.duplicateRows ? 'warn' : 'good'}`}>{analysis.duplicateRows ? <CopyIcon /> : <Check size={15} />}</div>
        <div><strong>{analysis.duplicateRows ? `${formatNumber(analysis.duplicateRows)} duplicate rows detected` : 'No duplicate rows detected'}</strong><p>{analysis.duplicateRows ? 'Exact row matches are counted once per repeated occurrence.' : 'No exact duplicate records were found in this pass.'}</p></div>
      </div>
      <div className="issue">
        <div className="issue-icon good"><Info size={15} /></div>
        <div><strong>Local-only profiling</strong><p>Values are parsed and summarized in this tab. MindTraceAI does not send your file anywhere.</p></div>
      </div>
    </div>
  </section>;
}

function CopyIcon() {
  return <span style={{ fontSize: 13, fontWeight: 800 }}>2×</span>;
}

function SchemaPanel({ profiles }: { profiles: ColumnProfile[] }) {
  return <section className="panel" id="schema">
    <div className="panel-head"><div><h2>Detected schema</h2><p>Inferred from observed values, not a declared data dictionary.</p></div><Columns3 size={20} color="#18775e" /></div>
    <div className="panel-body">
      <div className="schema-list">
        {profiles.map((profile) => <div className="schema-row" key={profile.name} data-testid={`schema-row-${profile.name}`}>
          <span className="schema-name" title={profile.name}>{profile.name}</span>
          <span className="type-label"><TypeIcon type={profile.type} />{profile.type}</span>
          <span className="schema-missing">{profile.missing ? `${formatNumber(profile.missing)} missing` : `${formatNumber(profile.unique)} unique`}</span>
        </div>)}
      </div>
    </div>
  </section>;
}

function NumericPanel({ profile }: { profile: ColumnProfile }) {
  const stats = profile.numeric;
  if (!stats) return null;
  const maxBin = Math.max(...stats.histogram, 1);
  return <div className="panel viz-panel" data-testid={`chart-numeric-${profile.name}`}>
    <div className="panel-head"><div><p className="field-caption"><Hash size={12} /><strong>{profile.name}</strong> · numeric distribution</p><h2>Shape at a glance</h2></div><span className="chart-meta">{formatNumber(stats.outliers)} outliers</span></div>
    <div className="panel-body">
      <div className="histogram" aria-label={`Histogram of ${profile.name}`}>
        {stats.histogram.map((count, index) => <div key={`${profile.name}-${index}`} className="hist-bar" title={`${count} rows`} style={{ height: `${Math.max(3, count / maxBin * 100)}%` }} />)}
      </div>
      <div className="hist-labels"><span>{formatNumber(stats.min, 2)}</span><span>median {formatNumber(stats.median, 2)}</span><span>{formatNumber(stats.max, 2)}</span></div>
      {stats.outliers > 0 && <div className="outlier-note"><AlertTriangle size={14} />{formatNumber(stats.outliers)} values sit outside the 1.5× IQR range.</div>}
    </div>
  </div>;
}

function CategoricalPanel({ profile }: { profile: ColumnProfile }) {
  const categories = profile.categories ?? [];
  const maxCount = categories[0]?.count ?? 1;
  return <div className="panel viz-panel" data-testid={`chart-categorical-${profile.name}`}>
    <div className="panel-head"><div><p className="field-caption"><FileText size={12} /><strong>{profile.name}</strong> · categorical breakdown</p><h2>Most common values</h2></div><span className="chart-meta">{formatNumber(profile.unique)} unique</span></div>
    <div className="panel-body"><div className="category-list">
      {categories.slice(0, 6).map((category) => <div className="category-row" key={category.value} title={`${category.value}: ${category.count}`}>
        <span className="category-name">{category.value}</span><div className="category-track"><div className="category-fill" style={{ width: `${category.count / maxCount * 100}%` }} /></div><span className="category-count">{formatNumber(category.count)}</span>
      </div>)}
      {!categories.length && <p className="hero-copy">No non-empty values to summarize.</p>}
    </div></div>
  </div>;
}

function ReportButton({ analysis }: { analysis: DatasetAnalysis }) {
  const downloadReport = () => {
    const report = {
      product: 'MindTraceAI Data Intelligence',
      generatedAt: new Date().toISOString(),
      source: { name: analysis.name, format: analysis.extension, size: analysis.size },
      overview: { rows: analysis.rows.length, columns: analysis.columns.length, missingCells: analysis.missingCells, duplicateRows: analysis.duplicateRows },
      schema: analysis.profiles.map(({ name, type, missing, unique, numeric, categories }) => ({ name, type, missing, unique, numeric, topCategories: categories })),
      note: 'Local descriptive profiling only. No model was trained or tested.',
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob); const link = document.createElement('a');
    link.href = url; link.download = `${analysis.name.replace(/\.[^.]+$/, '')}-mindtrace-report.json`; link.click(); URL.revokeObjectURL(url);
  };
  return <button className="outline-button" onClick={downloadReport} data-testid="button-download-report"><Download size={14} /> Download report</button>;
}

function DataPreview({ analysis }: { analysis: DatasetAnalysis }) {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState<{ column: string; direction: 'asc' | 'desc' } | null>(null);
  const filteredRows = useMemo(() => {
    const query = search.trim().toLowerCase();
    const rows = query ? analysis.rows.filter((row) => analysis.columns.some((column) => String(row[column] ?? '').toLowerCase().includes(query))) : analysis.rows;
    if (!sort) return rows;
    return [...rows].sort((a, b) => {
      const left = a[sort.column]; const right = b[sort.column];
      if (left === right) return 0;
      const direction = sort.direction === 'asc' ? 1 : -1;
      if (left === null || left === undefined) return -1 * direction;
      if (right === null || right === undefined) return 1 * direction;
      const numericLeft = Number(left); const numericRight = Number(right);
      if (Number.isFinite(numericLeft) && Number.isFinite(numericRight)) return (numericLeft - numericRight) * direction;
      return String(left).localeCompare(String(right)) * direction;
    });
  }, [analysis, search, sort]);
  const totalPages = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const visibleRows = filteredRows.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);
  const toggleSort = (column: string) => {
    setPage(1); setSort((current) => current?.column === column ? { column, direction: current.direction === 'asc' ? 'desc' : 'asc' } : { column, direction: 'asc' });
  };
  return <section className="panel preview-panel" id="preview">
    <div className="panel-head"><div><h2>Data preview</h2><p>Search every row, then sort by any field. Values stay in this browser tab.</p></div>
      <div className="preview-controls"><div className="search-wrap"><Search size={14} /><input className="search-input" type="search" placeholder="Find in rows…" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} data-testid="input-search-rows" /></div><ListFilter size={15} color="#68766e" /></div>
    </div>
    <div className="table-scroll"><table><thead><tr><th>Row</th>{analysis.columns.map((column) => <th key={column} onClick={() => toggleSort(column)} data-testid={`button-sort-${column}`}>{column} {sort?.column === column && (sort.direction === 'asc' ? <ArrowUp size={11} /> : <ArrowDown size={11} />)}</th>)}</tr></thead>
      <tbody>{visibleRows.map((row, rowIndex) => <tr key={`${rowIndex}-${JSON.stringify(row)}`} data-testid={`table-row-${rowIndex}`}><td className="row-index">{(safePage - 1) * PAGE_SIZE + rowIndex + 1}</td>{analysis.columns.map((column) => {
        const value: Cell = row[column]; const missing = value === null || value === undefined;
        return <td key={column} className={missing ? 'null-value' : ''} title={String(value ?? 'missing')}>{missing ? 'missing' : String(value)}</td>;
      })}</tr>)}</tbody>
    </table>
    {!visibleRows.length && <div style={{ padding: '30px 21px', color: 'hsl(var(--muted-foreground))', fontSize: 12 }}>No rows match “{search}”.</div>}
    </div>
    <div className="table-footer"><span>{formatNumber(filteredRows.length)} matching rows · {analysis.sampled ? 'preview capped for large file' : 'all parsed rows'}</span>
      <div className="pagination"><button className="page-button" disabled={safePage <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))} data-testid="button-page-previous"><ChevronLeft size={14} /></button><span className="page-button active">{safePage}</span><button className="page-button" disabled={safePage >= totalPages} onClick={() => setPage((value) => Math.min(totalPages, value + 1))} data-testid="button-page-next"><ChevronRight size={14} /></button></div>
    </div>
  </section>;
}

function Workspace({ analysis, onReset }: { analysis: DatasetAnalysis; onReset: () => void }) {
  const numeric = analysis.profiles.filter((profile) => profile.type === 'numeric');
  const categorical = analysis.profiles.filter((profile) => profile.type !== 'numeric');
  const missingRate = analysis.totalCells ? analysis.missingCells / analysis.totalCells : 0;
  return <div className="page">
    <div className="workspace-head reveal">
      <div><p className="eyebrow">Workspace / first read</p><div className="file-pill"><FileGlyph extension={analysis.extension} />{analysis.name} · {formatBytes(analysis.size)}</div><h1 style={{ marginTop: 16 }}>A clear read on <em style={{ color: '#18775e', fontStyle: 'normal' }}>{analysis.name.replace(/\.[^.]+$/, '')}</em>.</h1><p className="hero-copy">Descriptive profiling is complete. Use the signals below to understand structure and quality before you go deeper.</p></div>
      <div className="top-actions"><button className="ghost-button" onClick={onReset} data-testid="button-upload-another"><RefreshCw size={14} /> Upload another</button><ReportButton analysis={analysis} /></div>
    </div>
    <nav className="section-index" aria-label="Workspace sections">
      <a href="#overview" data-testid="link-section-overview">Overview</a><a href="#quality" data-testid="link-section-quality">Quality</a><a href="#schema" data-testid="link-section-schema">Schema</a><a href="#distributions" data-testid="link-section-distributions">Distributions</a><a href="#preview" data-testid="link-section-preview">Preview</a>
    </nav>
    <section id="overview" className="reveal reveal-delay-1">
      <div className="metrics-grid">
        <MetricCard label="Rows" value={formatNumber(analysis.rows.length)} sub={analysis.sampled ? 'parsed · charts use compact summaries' : 'records parsed'} />
        <MetricCard label="Columns" value={formatNumber(analysis.columns.length)} sub={`${analysis.profiles.filter((p) => p.type === 'numeric').length} numeric · ${analysis.profiles.filter((p) => p.type !== 'numeric').length} other`} />
        <MetricCard label="Missing cells" value={formatNumber(analysis.missingCells)} sub={`${(missingRate * 100).toFixed(1)}% of ${formatNumber(analysis.totalCells)} cells`} warning={analysis.missingCells > 0} />
        <MetricCard label="Duplicate rows" value={formatNumber(analysis.duplicateRows)} sub={analysis.duplicateRows ? 'worth reviewing' : 'none found'} warning={analysis.duplicateRows > 0} />
      </div>
    </section>
    <div className="analysis-grid reveal reveal-delay-2"><div><QualityPanel analysis={analysis} /></div><SchemaPanel profiles={analysis.profiles} /></div>
    <section id="distributions" className="reveal reveal-delay-3" style={{ marginTop: 18 }}>
      <div className="panel-head" style={{ paddingLeft: 0 }}><div><p className="eyebrow" style={{ marginBottom: 7 }}>Signals, not predictions</p><h2>Distributions & patterns</h2><p style={{ color: 'hsl(var(--muted-foreground))', fontSize: 12, margin: 0 }}>Compact views of the fields with the most descriptive signal.</p></div></div>
      <div className="viz-grid">{numeric.slice(0, 3).map((profile) => <NumericPanel profile={profile} key={profile.name} />)}{categorical.slice(0, 3).map((profile) => <CategoricalPanel profile={profile} key={profile.name} />)}</div>
      {!numeric.length && !categorical.length && <div className="panel" style={{ padding: 22 }}>There are no fields to visualize.</div>}
      {analysis.sampled && <p className="chart-meta" style={{ marginTop: 12 }}>Charts show compact 12-bin / top-value summaries calculated from the parsed file to keep the workspace responsive.</p>}
    </section>
    <DataPreview analysis={analysis} />
    <div className="download-note"><div><h3>Keep the read, not the raw file</h3><p>Download a compact JSON report with metadata, schema, quality signals, and descriptive statistics.</p></div><ReportButton analysis={analysis} /></div>
  </div>;
}

function Home({ onFile }: { onFile: (file: File) => void }) {
  return <div className="page">
    <div className="hero-row"><div><p className="eyebrow">Local-first data intelligence</p><h1>Find the shape of your data <span style={{ color: '#d97851' }}>before</span> you make a claim.</h1><p className="hero-copy">MindTraceAI turns an unfamiliar file into a calm, useful first read: structure, quality, distributions, and patterns — without pretending a generic dataset is a model.</p></div><div className="hero-meta"><span><Database size={14} /> local by default</span><span><ShieldCheck size={14} /> no upload</span></div></div>
    <EmptyState onFile={onFile} />
    <div className="home-grid"><div className="info-panel"><h3>What you will see</h3><p>A focused analysis pass designed for the first ten minutes with a new dataset.</p><div className="feature-list"><div className="feature-item"><BarChart3 size={15} /><span>Numeric distributions and outlier signals</span></div><div className="feature-item"><Columns3 size={15} /><span>Inferred schema with type confidence cues</span></div><div className="feature-item"><ShieldCheck size={15} /><span>Missingness and duplicate checks</span></div><div className="feature-item"><ListFilter size={15} /><span>Searchable, sortable data preview</span></div></div></div><div className="info-panel"><h3>Designed for a first look</h3><p>Bring the messy export, survey, event log, or customer list. MindTraceAI profiles what is there, flags what needs attention, and stops short of invented machine-learning conclusions.</p></div></div>
  </div>;
}

function App() {
  const [analysis, setAnalysis] = useState<DatasetAnalysis | null>(null);
  const [parsing, setParsing] = useState(false);
  const [error, setError] = useState('');
  const handleFile = async (file: File) => {
    setParsing(true); setError(''); setAnalysis(null);
    try { setAnalysis(await parseDataFile(file)); } catch (caught) { setError(caught instanceof Error ? caught.message : 'We could not read that file.'); } finally { setParsing(false); }
  };
  const reset = () => { setAnalysis(null); setError(''); setParsing(false); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  return <QueryClientProvider client={queryClient}><TooltipProvider><ErrorBoundary resetKey={analysis?.name ?? 'empty'}>
    <div className="app-shell">
      <aside className="rail"><div className="rail-top"><Logo /><p className="rail-kicker">Analysis lab</p><nav className="rail-nav"><a href={analysis ? '#overview' : '#upload'} data-testid="link-nav-overview"><LayoutDashboard size={16} />Overview</a><a href={analysis ? '#quality' : '#upload'} data-testid="link-nav-quality"><ShieldCheck size={16} />Quality</a><a href={analysis ? '#schema' : '#upload'} data-testid="link-nav-schema"><Columns3 size={16} />Schema</a><a href={analysis ? '#preview' : '#upload'} data-testid="link-nav-preview"><ListFilter size={16} />Preview</a></nav></div><div className="rail-bottom"><div className="local-badge"><span className="local-dot" />Local session</div><p className="rail-note">Your file is read in-browser and never sent to a server.</p></div></aside>
      <main className="main"><header className="topbar"><div className="topbar-label"><strong>MindTraceAI</strong> <span>/ {analysis ? analysis.name : 'Data Intelligence'}</span></div><div className="top-actions">{analysis && <button className="ghost-button" onClick={reset} data-testid="button-reset-top"><RefreshCw size={14} /> Reset</button>}<span className="local-badge"><span className="local-dot" /> local-only</span></div></header>
        {parsing ? <div className="page"><LoadingState /></div> : analysis ? <Workspace analysis={analysis} onReset={reset} /> : <div id="upload"><Home onFile={handleFile} />{error && <div className="page" style={{ paddingTop: 0 }}><div className="empty-error" role="alert" data-testid="status-parse-error"><X size={17} /><div><strong>That file needs another look</strong><span>{error}</span></div></div></div>}</div>}
      </main>
    </div>
  </ErrorBoundary><Toaster /></TooltipProvider></QueryClientProvider>;
}

export default App;