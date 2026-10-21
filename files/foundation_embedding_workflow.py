#!/usr/bin/env python3
"""Evaluate supplied single-cell foundation-model embedding CSV exports.

No model inference is performed. CSV formats:
 embeddings.csv: cell_id,embedding_0,...,embedding_d
 metadata.csv: cell_id,donor_id,label,split (split is train or test)
No third-party packages required.
"""
from __future__ import annotations
import argparse, csv, json, math, os, sys, tempfile
from collections import Counter, defaultdict
from pathlib import Path

MAX_CSV_BYTES = 10 * 1024 * 1024
MAX_DISTANCE_TERMS = 10_000_000

class WorkflowError(ValueError):
    pass

def read_csv(path):
    try:
        if os.path.getsize(path) > MAX_CSV_BYTES:
            raise WorkflowError(f'{path}: CSV exceeds the 10 MiB teaching-example limit')
        with open(path, newline='', encoding='utf-8') as f:
            reader=csv.reader(f, strict=True)
            header=next(reader, None)
            if not header: raise WorkflowError(f'{path}: missing CSV header')
            if any(not x.strip() for x in header): raise WorkflowError(f'{path}: CSV headers must be nonblank')
            if len(set(header)) != len(header): raise WorkflowError(f'{path}: duplicate CSV header names are not allowed')
            rows=[]
            for line,row in enumerate(reader,2):
                if len(row) != len(header):
                    raise WorkflowError(f'{path}: row {line} has {len(row)} fields; expected exactly {len(header)}')
                rows.append(dict(zip(header,row)))
        return header, rows
    except WorkflowError:
        raise
    except (OSError, UnicodeError, csv.Error) as e:
        raise WorkflowError(f'{path}: cannot read valid UTF-8 CSV ({e})') from e

def load_inputs(embedding_path, metadata_path):
    eh, er=read_csv(embedding_path); mh, mr=read_csv(metadata_path)
    if eh.count('cell_id') != 1 or mh.count('cell_id') != 1: raise WorkflowError('Both CSV files require exactly one cell_id column')
    dims=[x for x in eh if x != 'cell_id']
    if not dims or any(not x.startswith('embedding_') for x in dims): raise WorkflowError('Embeddings require one or more embedding_* dimension columns')
    for col in ('donor_id','label','split'):
        if col not in mh: raise WorkflowError(f'Metadata missing required column: {col}')
    if set(mh) != {'cell_id','donor_id','label','split'}: raise WorkflowError('Metadata columns must be exactly cell_id, donor_id, label, split')
    def unique(rows, source):
        d={}
        for r in rows:
            key=(r.get('cell_id') or '').strip()
            if not key: raise WorkflowError(f'{source}: blank cell_id')
            if key in d: raise WorkflowError(f'{source}: duplicate cell_id {key!r}')
            d[key]=r
        return d
    ed=unique(er,'embeddings'); md=unique(mr,'metadata')
    if set(ed)!=set(md):
        missing=sorted(set(md)-set(ed)); extra=sorted(set(ed)-set(md))
        raise WorkflowError(f'Cell ID mismatch: no embedding for metadata IDs {missing[:5]}; no metadata for embedding IDs {extra[:5]}')
    vectors={}
    for cell,row in ed.items():
        try: v=[float(row[k]) for k in dims]
        except (TypeError,ValueError): raise WorkflowError(f'{cell}: embedding value is not numeric')
        if not all(math.isfinite(x) for x in v): raise WorkflowError(f'{cell}: embedding contains NaN or infinity')
        vectors[cell]=v
    meta={}
    for cell,row in md.items():
        donor=(row.get('donor_id') or '').strip(); label=(row.get('label') or '').strip(); split=(row.get('split') or '').strip().lower()
        if not donor or not label: raise WorkflowError(f'{cell}: donor_id and label must be nonblank')
        if split not in ('train','test'): raise WorkflowError(f'{cell}: split must be train or test')
        meta[cell]={'donor_id':donor,'label':label,'split':split}
    train=[c for c in sorted(vectors) if meta[c]['split']=='train']; test=[c for c in sorted(vectors) if meta[c]['split']=='test']
    if not train or not test: raise WorkflowError('Need at least one reference train cell and one held-out test cell')
    train_donors={meta[c]['donor_id'] for c in train}; test_donors={meta[c]['donor_id'] for c in test}
    overlap=train_donors & test_donors
    if overlap: raise WorkflowError('Donor leakage: donor occurs in both train and test: '+', '.join(sorted(overlap)))
    return vectors,meta,dims

def predict(vectors, meta, k=3):
    if k<1: raise WorkflowError('k must be >= 1')
    train=[c for c in sorted(vectors) if meta[c]['split']=='train']; test=[c for c in sorted(vectors) if meta[c]['split']=='test']
    if k>len(train): raise WorkflowError(f'k={k} exceeds reference size ({len(train)})')
    out=[]
    for q in test:
        ds=[]
        for r in train:
            try:
                terms=[(a-b)**2 for a,b in zip(vectors[q],vectors[r])]
                d=sum(terms)
            except OverflowError as e:
                raise WorkflowError('Distance calculation overflowed; review/scale embedding values before evaluating') from e
            if not math.isfinite(d): raise WorkflowError('Distance calculation overflowed; review/scale embedding values before evaluating')
            ds.append((d,r))
        ds.sort(key=lambda z:(z[0],z[1]))
        nearest=ds[:k]; counts=Counter(meta[r]['label'] for _,r in nearest)
        maxvotes=max(counts.values()); tied=sorted(label for label,n in counts.items() if n==maxvotes)
        # Tie-breaking is alphabetical and disclosed; uncertainty is top-vote fraction.
        pred=tied[0]
        out.append({'cell_id':q,'donor_id':meta[q]['donor_id'],'truth':meta[q]['label'],'prediction':pred,'confidence_top_vote_fraction':maxvotes/k,'tied_top_labels':tied,'neighbors':[{'cell_id':r,'distance_squared':d,'label':meta[r]['label']} for d,r in nearest]})
    return out

def evaluate(predictions):
    n=len(predictions); correct=sum(p['truth']==p['prediction'] for p in predictions)
    labels=sorted({p['truth'] for p in predictions}|{p['prediction'] for p in predictions})
    cm={a:{b:0 for b in labels} for a in labels}
    for p in predictions: cm[p['truth']][p['prediction']]+=1
    per={}
    for label in labels:
        tp=cm[label][label]; support=sum(cm[label].values()); predicted=sum(cm[t][label] for t in labels)
        precision=tp/predicted if predicted else 0.0; recall=tp/support if support else 0.0
        per[label]={'support':support,'precision':precision,'recall':recall,'f1':(2*precision*recall/(precision+recall) if precision+recall else 0.0)}
    macro=sum(x['f1'] for x in per.values())/len(per) if per else 0.0
    return {'n_test':n,'accuracy':correct/n if n else 0.0,'macro_f1':macro,'per_class':per,'confusion_matrix_truth_rows_prediction_columns':cm,'donor_accuracy':{d:{'n':sum(p['donor_id']==d for p in predictions),'accuracy':sum(p['donor_id']==d and p['truth']==p['prediction'] for p in predictions)/sum(p['donor_id']==d for p in predictions)} for d in sorted({p['donor_id'] for p in predictions})}}

def run(embedding_path, metadata_path, output_path, k=3):
    vectors,meta,dims=load_inputs(embedding_path,metadata_path)
    ntrain=sum(m['split']=='train' for m in meta.values()); ntest=sum(m['split']=='test' for m in meta.values())
    if ntrain*ntest*len(dims) > MAX_DISTANCE_TERMS:
        raise WorkflowError('Training/evaluation limit exceeded: train cells × test cells × dimensions must be at most 10 million distance terms; use a real ANN implementation for larger datasets')
    preds=predict(vectors,meta,k); metrics=evaluate(preds)
    payload={'workflow':'precomputed-embedding-heldout-donor-knn','inference_performed':False,'interpretation':'Metrics describe only the supplied embeddings and labels; this is not a zero-shot guarantee, causal analysis, or regulatory-network inference.','n_cells':len(vectors),'embedding_dimensions':len(dims),'train_cells':sum(m['split']=='train' for m in meta.values()),'test_cells':len(preds),'train_donors':sorted({meta[c]['donor_id'] for c in meta if meta[c]['split']=='train'}),'test_donors':sorted({meta[c]['donor_id'] for c in meta if meta[c]['split']=='test'}),'k':k,'metrics':metrics,'predictions':preds}
    try: serialized=json.dumps(payload,indent=2,allow_nan=False)+'\n'
    except (ValueError, OverflowError) as e: raise WorkflowError(f'Results cannot be represented as strict JSON: {e}') from e
    dest=Path(output_path)
    if dest.exists(): raise WorkflowError(f'Refusing to overwrite existing output: {dest}')
    dest.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive create prevents silent clobbering, including concurrent runs.
    with open(dest,'x',encoding='utf-8') as f: f.write(serialized)
    return payload

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--embeddings',required=True); p.add_argument('--metadata',required=True); p.add_argument('--output',required=True); p.add_argument('-k',type=int,default=3)
    a=p.parse_args(argv)
    try:
        result=run(a.embeddings,a.metadata,a.output,a.k); print(json.dumps({'output':a.output,'n_test':result['test_cells'],'accuracy':result['metrics']['accuracy'],'macro_f1':result['metrics']['macro_f1']},allow_nan=False)); return 0
    except (WorkflowError,OSError) as e: print(f'ERROR: {e}',file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
