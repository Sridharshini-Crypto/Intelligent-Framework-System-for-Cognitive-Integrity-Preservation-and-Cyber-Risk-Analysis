export type Cell = string | number | boolean | null;
export type DataRow = Record<string, Cell>;
export type ColumnType = 'numeric' | 'categorical' | 'date' | 'boolean';

export interface NumericStats {
  min: number;
  max: number;
  mean: number;
  median: number;
  q1: number;
  q3: number;
  outliers: number;
  histogram: number[];
}

export interface CategoryStats {
  value: string;
  count: number;
}

export interface ColumnProfile {
  name: string;
  type: ColumnType;
  missing: number;
  unique: number;
  sample: string;
  numeric?: NumericStats;
  categories?: CategoryStats[];
}

export interface DatasetAnalysis {
  name: string;
  extension: string;
  size: number;
  rows: DataRow[];
  columns: string[];
  profiles: ColumnProfile[];
  duplicateRows: number;
  totalCells: number;
  missingCells: number;
  sampled: boolean;
  parsedAt: string;
}

const NULL_MARKERS = new Set(['', 'null', 'undefined', 'na', 'n/a', 'none', 'nil', '-']);

function isMissing(value: unknown): boolean {
  return value === null || value === undefined || (typeof value === 'string' && NULL_MARKERS.has(value.trim().toLowerCase()));
}

function normalizeValue(value: unknown): Cell {
  if (isMissing(value)) return null;
  if (typeof value === 'number' || typeof value === 'boolean') return value;
  return String(value).trim();
}

function parseDelimited(text: string, delimiter: string): DataRow[] {
  const records: string[][] = [];
  let row: string[] = [];
  let cell = '';
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (char === '"' && quoted && next === '"') { cell += '"'; index += 1; continue; }
    if (char === '"') { quoted = !quoted; continue; }
    if (char === delimiter && !quoted) { row.push(cell); cell = ''; continue; }
    if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && next === '\n') index += 1;
      row.push(cell); cell = '';
      if (row.some((item) => item.trim() !== '')) records.push(row);
      row = [];
      continue;
    }
    cell += char;
  }
  if (cell.length || row.length) { row.push(cell); if (row.some((item) => item.trim() !== '')) records.push(row); }
  if (records.length < 2) throw new Error('The file needs a header row and at least one data row.');
  const headers = records[0].map((header, index) => header.trim() || `column_${index + 1}`);
  const seen = new Map<string, number>();
  const uniqueHeaders = headers.map((header) => {
    const count = seen.get(header) ?? 0;
    seen.set(header, count + 1);
    return count ? `${header}_${count + 1}` : header;
  });
  return records.slice(1).map((values) => Object.fromEntries(uniqueHeaders.map((header, index) => [header, normalizeValue(values[index] ?? null)])));
}

function parseJson(text: string, isJsonl: boolean): DataRow[] {
  let parsed: unknown;
  if (isJsonl) {
    parsed = text.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
  } else {
    parsed = JSON.parse(text);
  }
  const list = Array.isArray(parsed) ? parsed : [parsed];
  const objects = list.filter((item): item is Record<string, unknown> => item !== null && typeof item === 'object' && !Array.isArray(item));
  if (!objects.length) throw new Error('JSON should contain an array of objects, or one object per line.');
  const columns = Array.from(new Set(objects.flatMap((item) => Object.keys(item))));
  return objects.map((item) => Object.fromEntries(columns.map((column) => [column, normalizeValue(item[column])])));
}

function toNumber(value: Cell): number | null {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value !== 'string' || !value.trim()) return null;
  const cleaned = value.replace(/[$,%\s,]/g, '');
  const result = Number(cleaned);
  return Number.isFinite(result) ? result : null;
}

function percentile(values: number[], fraction: number): number {
  const position = (values.length - 1) * fraction;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return values[lower] ?? 0;
  return (values[lower] ?? 0) + ((values[upper] ?? 0) - (values[lower] ?? 0)) * (position - lower);
}

function profileColumn(name: string, rows: DataRow[]): ColumnProfile {
  const values = rows.map((row) => row[name] ?? null);
  const present = values.filter((value) => !isMissing(value));
  const missing = values.length - present.length;
  const unique = new Set(present.map((value) => String(value))).size;
  const sample = present.length ? String(present[0]).slice(0, 80) : 'No values';
  const numberValues = present.map(toNumber).filter((value): value is number => value !== null);
  const boolValues = present.filter((value) => typeof value === 'boolean' || /^(true|false)$/i.test(String(value)));
  const dateValues = present.filter((value) => {
    if (typeof value === 'number') return false;
    const string = String(value);
    return /^\d{4}[-/]\d{1,2}[-/]\d{1,2}/.test(string) || /^\d{1,2}\/\d{1,2}\/\d{4}/.test(string);
  });
  let type: ColumnType = 'categorical';
  if (present.length && boolValues.length / present.length > .92) type = 'boolean';
  else if (present.length && numberValues.length / present.length > .88 && unique > 2) type = 'numeric';
  else if (present.length && dateValues.length / present.length > .8) type = 'date';

  const profile: ColumnProfile = { name, type, missing, unique, sample };
  if (type === 'numeric') {
    const sorted = [...numberValues].sort((a, b) => a - b);
    const q1 = percentile(sorted, .25); const q3 = percentile(sorted, .75); const iqr = q3 - q1;
    const low = q1 - 1.5 * iqr; const high = q3 + 1.5 * iqr;
    const min = sorted[0] ?? 0; const max = sorted[sorted.length - 1] ?? 0;
    const bins = Array.from({ length: 12 }, () => 0);
    const width = max === min ? 1 : (max - min) / bins.length;
    numberValues.forEach((value) => bins[Math.min(bins.length - 1, Math.max(0, Math.floor((value - min) / width)))] += 1);
    profile.numeric = {
      min, max, mean: numberValues.reduce((sum, value) => sum + value, 0) / numberValues.length,
      median: percentile(sorted, .5), q1, q3,
      outliers: numberValues.filter((value) => value < low || value > high).length, histogram: bins,
    };
  } else {
    const counts = new Map<string, number>();
    present.forEach((value) => counts.set(String(value), (counts.get(String(value)) ?? 0) + 1));
    profile.categories = Array.from(counts.entries()).map(([value, count]) => ({ value, count })).sort((a, b) => b.count - a.count).slice(0, 8);
  }
  return profile;
}

export async function parseDataFile(file: File): Promise<DatasetAnalysis> {
  const text = await file.text();
  if (!text.trim()) throw new Error('This file is empty. Choose a file with a header and some records.');
  const lower = file.name.toLowerCase();
  const extension = lower.split('.').pop() ?? 'data';
  let rows: DataRow[];
  try {
    if (extension === 'json' || extension === 'jsonl') rows = parseJson(text, extension === 'jsonl');
    else if (extension === 'tsv') rows = parseDelimited(text, '\t');
    else if (extension === 'csv' || !extension) rows = parseDelimited(text, ',');
    else throw new Error(`.${extension} files are not supported. Try CSV, TSV, JSON, or JSONL.`);
  } catch (error) {
    if (error instanceof Error && error.message.includes('not supported')) throw error;
    throw new Error('We could not parse this file. Check that it is valid tabular data with consistent records.');
  }
  if (!rows.length) throw new Error('No records found after parsing this file.');
  const columns = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
  const profiles = columns.map((column) => profileColumn(column, rows));
  const duplicateRows = rows.length - new Set(rows.map((row) => JSON.stringify(columns.map((column) => row[column] ?? null)))).size;
  const missingCells = profiles.reduce((sum, profile) => sum + profile.missing, 0);
  return {
    name: file.name, extension: extension.toUpperCase(), size: file.size, rows, columns, profiles, duplicateRows,
    totalCells: rows.length * columns.length, missingCells, sampled: rows.length > 5000, parsedAt: new Date().toISOString(),
  };
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatNumber(value: number, digits = 0): string {
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: digits }).format(value);
}