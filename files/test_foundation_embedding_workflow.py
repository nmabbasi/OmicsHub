import csv, json, math, tempfile, unittest
from pathlib import Path
import foundation_embedding_workflow as w

class WorkflowTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.d=Path(self.tmp.name)
  self.emb=self.d/'embeddings.csv'; self.meta=self.d/'metadata.csv'
  self.write(self.emb,['cell_id','embedding_0','embedding_1'],[
   ['rA','0','0'],['rB','0','1'],['rC','10','10'],['rD','10','11'],['tA','0','0.1'],['tB','10','10.1']])
  # Deliberately different row order; donors held out.
  self.write(self.meta,['cell_id','donor_id','label','split'],[
   ['tB','held2','B','test'],['rC','ref2','B','train'],['rA','ref1','A','train'],['tA','held1','A','test'],['rD','ref3','B','train'],['rB','ref4','A','train']])
 def tearDown(self): self.tmp.cleanup()
 def write(self,p,header,rows):
  with open(p,'w',newline='') as f:
   x=csv.writer(f); x.writerow(header); x.writerows(rows)
 def test_known_predictions_alignment_metrics_and_json(self):
  out=self.d/'result.json'; result=w.run(self.emb,self.meta,out,k=1)
  self.assertEqual({p['cell_id']:p['prediction'] for p in result['predictions']},{'tA':'A','tB':'B'})
  self.assertEqual(result['metrics']['accuracy'],1.0); self.assertEqual(result['metrics']['macro_f1'],1.0)
  self.assertFalse(result['inference_performed']); json.loads(out.read_text(),parse_constant=lambda x: (_ for _ in ()).throw(AssertionError(x)))
 def test_duplicate_ids(self):
  self.write(self.meta,['cell_id','donor_id','label','split'],[['rA','d','A','train'],['rA','e','A','test']])
  with self.assertRaisesRegex(w.WorkflowError,'duplicate cell_id'): w.load_inputs(self.emb,self.meta)
 def test_missing_or_extra_ids(self):
  self.write(self.meta,['cell_id','donor_id','label','split'],[['z','d','A','train']])
  with self.assertRaisesRegex(w.WorkflowError,'Cell ID mismatch'): w.load_inputs(self.emb,self.meta)
 def test_metadata_reordering_does_not_change_mapping(self):
  vec,meta,_=w.load_inputs(self.emb,self.meta); pred=w.predict(vec,meta,k=1)
  self.assertEqual({x['cell_id']:x['truth'] for x in pred},{'tA':'A','tB':'B'})
 def test_nan_and_infinity_rejected(self):
  for val in ('nan','inf','-inf'):
   self.write(self.emb,['cell_id','embedding_0','embedding_1'],[['rA',val,'0']])
   self.write(self.meta,['cell_id','donor_id','label','split'],[['rA','d','A','train']])
   with self.subTest(val=val),self.assertRaisesRegex(w.WorkflowError,'NaN or infinity'): w.load_inputs(self.emb,self.meta)
 def test_donor_leakage_rejected(self):
  with open(self.meta,newline='') as f: rows=list(csv.DictReader(f))
  rows[0]['donor_id']='ref1'
  self.write(self.meta,['cell_id','donor_id','label','split'],[[r[k] for k in ['cell_id','donor_id','label','split']] for r in rows])
  with self.assertRaisesRegex(w.WorkflowError,'Donor leakage'): w.load_inputs(self.emb,self.meta)
 def test_existing_output_never_overwritten(self):
  out=self.d/'result.json'; out.write_text('keep me\n')
  with self.assertRaisesRegex(w.WorkflowError,'Refusing to overwrite'): w.run(self.emb,self.meta,out,k=1)
  self.assertEqual(out.read_text(),'keep me\n')
 def test_vote_tie_deterministic_disclosed(self):
  v={'q':[0.0],'a':[1.0],'b':[-1.0]}; m={'q':{'split':'test','label':'B','donor_id':'t'},'a':{'split':'train','label':'Z','donor_id':'a'},'b':{'split':'train','label':'A','donor_id':'b'}}
  got=w.predict(v,m,k=2)[0]
  self.assertEqual(got['prediction'],'A'); self.assertEqual(got['tied_top_labels'],['A','Z']); self.assertEqual(got['confidence_top_vote_fraction'],0.5)
 def test_invalid_split_rejected(self):
  self.write(self.meta,['cell_id','donor_id','label','split'],[['rA','d','A','validation'],['rB','d2','A','train'],['rC','d3','B','train'],['rD','d4','B','train'],['tA','d5','A','test'],['tB','d6','B','test']])
  with self.assertRaisesRegex(w.WorkflowError,'split must be'): w.load_inputs(self.emb,self.meta)

 def test_duplicate_and_blank_headers_rejected(self):
  for header in (['cell_id','embedding_0','embedding_0'],['cell_id',' ','embedding_0']):
   self.write(self.emb,header,[['rA','0','0']])
   with self.subTest(header=header),self.assertRaisesRegex(w.WorkflowError,'header'):
    w.load_inputs(self.emb,self.meta)

 def test_ragged_rows_rejected(self):
  for row in (['rA','0'],['rA','0','0','surplus']):
   self.write(self.emb,['cell_id','embedding_0','embedding_1'],[row])
   with self.subTest(row=row),self.assertRaisesRegex(w.WorkflowError,'expected exactly'):
    w.load_inputs(self.emb,self.meta)

 def test_metadata_extra_column_rejected(self):
  self.write(self.meta,['cell_id','donor_id','label','split','extra'],[['rA','d','A','train','x']])
  with self.assertRaisesRegex(w.WorkflowError,'exactly'):
   w.load_inputs(self.emb,self.meta)

 def test_malformed_utf8_is_friendly_and_no_output(self):
  self.emb.write_bytes(b'cell_id,embedding_0\nrA,0\n\xff')
  out=self.d/'result.json'
  with self.assertRaisesRegex(w.WorkflowError,'valid UTF-8 CSV'):
   w.run(self.emb,self.meta,out,k=1)
  self.assertFalse(out.exists())

 def test_huge_finite_values_fail_friendly_before_output(self):
  self.write(self.emb,['cell_id','embedding_0'],[['rA','1e308'],['rB','-1e308'],['tA','1e308']])
  self.write(self.meta,['cell_id','donor_id','label','split'],[['rA','d1','A','train'],['rB','d2','B','train'],['tA','d3','A','test']])
  out=self.d/'result.json'
  with self.assertRaisesRegex(w.WorkflowError,'overflowed.*scale'):
   w.run(self.emb,self.meta,out,k=1)
  self.assertFalse(out.exists())

if __name__=='__main__': unittest.main()
