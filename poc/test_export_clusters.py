import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import export_clusters


class ClusterExportRegression(unittest.TestCase):
    def test_unicode_paragraph_separator_preserves_one_record_and_text(self):
        cluster={'id':'C1','name':'test','queries':['question'],
                 'evidence_files':['raw.pdf'],'search_results_top5':['raw.pdf'],
                 'description':'first\u2029second','content':'A\u2029B',
                 'create_time':'2026-10-14','evidences':[{'summary':'x\u2029y'}]}
        payload=json.dumps(cluster,ensure_ascii=False)+'\n'
        workspace=Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory(dir=workspace) as directory:
            target=Path(directory)
            self.assertTrue(target.resolve().is_relative_to(workspace))
            with patch.object(export_clusters,'docker',return_value=payload):
                self.assertEqual(export_clusters.export('/data/test.parquet',target,True),1)
            lines=(target/'clusters_full.jsonl').read_text(encoding='utf-8').splitlines()
            self.assertEqual(len(lines),1)
            self.assertEqual(json.loads(lines[0]),cluster)
            self.assertTrue((target/'clusters.csv').exists())


if __name__=='__main__':unittest.main()
