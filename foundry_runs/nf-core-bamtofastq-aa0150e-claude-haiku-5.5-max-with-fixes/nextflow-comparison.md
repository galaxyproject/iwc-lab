# haiku-max-fixed vs nf-core/bamtofastq: data and feature comparison

Foundry run folder: `~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-haiku-max-fixed` (read-only; workflow copied to `<scratch>/compare/haiku-max-fixed/wf/`). nf-core reference: `<scratch>/nfcore-ref/out-<case>/`.

Source commit converted by this run: `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`; compared against the nf-core reference of that commit: `<scratch>/nfcore-ref`

Regenerate: `compare.sh ~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-haiku-max-fixed`

## Workflow (static, from the YAML; heuristic)

- tool steps: **20**; inputs: alignments, multiqc_title
- outputs: reads_paired<-paired_zip/output, reads_single<-single_filter_null/output, multiqc_report<-multiqc/html_report, fastqc_pre_conversion_html<-fastqc_pre/html_file, fastqc_post_conversion_html<-fastqc_post/html_file, samtools_flagstat<-flagstat/output1, samtools_stats<-stats/output, samtools_idxstats<-idxstats/output, fastqutils_info<-fastq_info/output
- BAM list input: True
- CRAM declared on input: no format restriction
- fasta / reference input: **none**
- fasta wired to steps: **none**
- samtools idxstats: ['idxstats']
- samtools flagstat: ['flagstat']
- samtools stats: ['stats']
- no_stats switch gates steps: **none**
- FastQC pre-conversion (on alignments): ['fastqc_pre']
- FastQC post-conversion: ['fastqc_post']
- no_read_QC switch gates steps: **none**
- single/paired detection step: **none**
- chr input: **none**
- chr filter steps: **none**
- samtools view steps (pair classes / chr): **none**
- samtools merge: **none**
- collate steps: ['single_collate']
- fastx steps: ['single_fastx', 'paired_fastx']
- cat (R1/R2 concat): **none**
- collate_fast / reads_in_memory wired: **none**
- fastq_info / fastq_utils: ['fastq_info']
- MultiQC: ['multiqc']
- user-defined tools: **none**
- unused inputs: **none**

Self-reported planemo test: **pass** (`~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-haiku-max-fixed/workflow-test-result.json`)

## Case `default`

- planemo run exit: **0**; command: `<scratch>/compare/haiku-max-fixed/default/command.txt`
  - input `alignments`: alignments (nf-core samplesheet: test, test2)
  - input `multiqc_title`: unset (workflow default None)
  - GAP: no fasta input
  - GAP: no chr input
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/default.nf.test.snap`): 13/13 md5 entries match
- workflow outputs with no dataset: reads_single (EMPTY COLLECTION)

### Reads (order-independent; record = name+seq+qual, /1 /2 suffix stripped for matching)

| nf-core file | nf-core records (lines) | gz | Galaxy best match | Galaxy records (lines) | gz | missing | extra | /1 /2 suffix nf/gx | verdict |
|---|---|---|---|---|---|---|---|---|---|
| reads/test2_1.merged.fastq.gz | 2718 (10872) | True | reads_paired/test2__forward.fastqsanger.gz | 2718 (10872) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test2_2.merged.fastq.gz | 2718 (10872) | True | reads_paired/test2__reverse.fastqsanger.gz | 2718 (10872) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test_1.merged.fastq.gz | 2821 (11284) | True | reads_paired/test__forward.fastqsanger.gz | 2821 (11284) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test_2.merged.fastq.gz | 2821 (11284) | True | reads_paired/test__reverse.fastqsanger.gz | 2821 (11284) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |

All reads of the case pooled: nf-core 11078 distinct records, Galaxy 11078; missing in Galaxy 0 ; extra in Galaxy 0 

### Reports

- **flagstat**: nf-core 2, Galaxy 2, same numbers 2/2
- **idxstats**: nf-core 2, Galaxy 2, same numbers 2/2
- **stats**: nf-core 2, Galaxy 2, same numbers 2/2
- **fastq_info**: nf-core 2, Galaxy 4, same numbers 0/2
  - fastqutils/test.txt: no Galaxy counterpart (2 candidates)
  - fastqutils/test2.txt: no Galaxy counterpart (2 candidates)
- **FastQC**: nf-core 6 reports (zip), Galaxy 0 data + 6 HTML; same Basic Statistics (same stage) 6/6; also same module verdicts 0/6
  - fastqc/test.post_conversion_1_fastqc.zip (post, Total Sequences 2821) = fastqc_post_conversion_html/test_forward.html (module verdicts not equal or not available from HTML)
  - fastqc/test.post_conversion_2_fastqc.zip (post, Total Sequences 2821) = fastqc_post_conversion_html/test_reverse.html (module verdicts not equal or not available from HTML)
  - fastqc/test.pre_conversion_fastqc.zip (pre, Total Sequences 5644) = fastqc_pre_conversion_html/test.html (module verdicts not equal or not available from HTML)
  - fastqc/test2.post_conversion_1_fastqc.zip (post, Total Sequences 2718) = fastqc_post_conversion_html/test2_forward.html (module verdicts not equal or not available from HTML)
  - fastqc/test2.post_conversion_2_fastqc.zip (post, Total Sequences 2718) = fastqc_post_conversion_html/test2_reverse.html (module verdicts not equal or not available from HTML)
  - fastqc/test2.pre_conversion_fastqc.zip (pre, Total Sequences 5436) = fastqc_pre_conversion_html/test2.html (module verdicts not equal or not available from HTML)
  - Galaxy FastQC reports: fastqc_post_conversion_html/test2_forward.html (2718 seqs), fastqc_post_conversion_html/test2_reverse.html (2718 seqs), fastqc_post_conversion_html/test_forward.html (2821 seqs), fastqc_post_conversion_html/test_reverse.html (2821 seqs), fastqc_pre_conversion_html/test.html (5644 seqs), fastqc_pre_conversion_html/test2.html (5436 seqs)
- **MultiQC** report present: nf-core True, Galaxy True

Inventory by content kind: nf-core {'flagstat': 2, 'idxstats': 2, 'stats': 2, 'fastqc_html': 6, 'fastqc_data': 6, 'fastq': 4, 'multiqc_html': 1, 'other': 7, 'fastq_info': 2}; Galaxy {'stats': 2, 'multiqc_html': 1, 'fastqc_html': 6, 'fastq': 4, 'fastq_info': 4, 'flagstat': 2, 'idxstats': 2}

## Case `chr`

- planemo run exit: **0**; command: `<scratch>/compare/haiku-max-fixed/chr/command.txt`
  - input `alignments`: alignments (nf-core samplesheet: test3)
  - input `multiqc_title`: unset (workflow default None)
  - GAP: no fasta input
  - GAP: no chr input
  - GAP: nf-core case needs --chr 'chrX chrY X Y' but the workflow has no chr input: ran unfiltered
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/chr.nf.test.snap`): 6/6 md5 entries match
- workflow outputs with no dataset: reads_paired (EMPTY COLLECTION)

### Reads (order-independent; record = name+seq+qual, /1 /2 suffix stripped for matching)

| nf-core file | nf-core records (lines) | gz | Galaxy best match | Galaxy records (lines) | gz | missing | extra | /1 /2 suffix nf/gx | verdict |
|---|---|---|---|---|---|---|---|---|---|
| reads/test3.chrX_chrY_X_Y_other.fq.gz | 572 (2288) | True | reads_single/test3.fastqsanger.gz | 12473 (49892) | True | 0 | 11901 | False/False | SUPERSET: all nf-core records present, Galaxy file has 11901 more |

All reads of the case pooled: nf-core 572 distinct records, Galaxy 12473; missing in Galaxy 0 ; extra in Galaxy 11901 ['K00233:65:HKTTVBBXX:5:1101:10094:27602', 'K00233:65:HKTTVBBXX:5:1101:10287:9332', 'K00233:65:HKTTVBBXX:5:1101:10815:46856', 'K00233:65:HKTTVBBXX:5:1101:10866:12761', 'K00233:65:HKTTVBBXX:5:1101:10896:16999', 'K00233:65:HKTTVBBXX:5:1101:11677:18001', 'K00233:65:HKTTVBBXX:5:1101:11830:25720', 'K00233:65:HKTTVBBXX:5:1101:11901:46100', 'K00233:65:HKTTVBBXX:5:1101:12154:2545', 'K00233:65:HKTTVBBXX:5:1101:12327:24437']

### BAM outputs

- nf-core `samtools/test3.chrX_chrY_X_Y.bam` (572 records): Galaxy identical = **False** []
### Reports

- **flagstat**: nf-core 1, Galaxy 1, same numbers 1/1
- **idxstats**: nf-core 1, Galaxy 1, same numbers 1/1
- **stats**: nf-core 1, Galaxy 1, same numbers 1/1
- **fastq_info**: nf-core 1, Galaxy 1, same numbers 1/1
- **FastQC**: nf-core 2 reports (zip), Galaxy 0 data + 2 HTML; same Basic Statistics (same stage) 1/2; also same module verdicts 0/2
  - fastqc/test3.chrX_chrY_X_Y.post_conversion_fastqc.zip (post, Total Sequences 572): no Galaxy post-conversion report with the same Basic Statistics
  - fastqc/test3.pre_conversion_fastqc.zip (pre, Total Sequences 12473) = fastqc_pre_conversion_html/test3.html (module verdicts not equal or not available from HTML)
  - Galaxy FastQC reports: fastqc_post_conversion_html/test3.html (12473 seqs), fastqc_pre_conversion_html/test3.html (12473 seqs)
- **MultiQC** report present: nf-core True, Galaxy True

Inventory by content kind: nf-core {'bam': 1, 'flagstat': 1, 'idxstats': 1, 'stats': 1, 'fastqc_html': 2, 'fastqc_data': 2, 'fastq': 1, 'multiqc_html': 1, 'other': 7, 'fastq_info': 1}; Galaxy {'stats': 1, 'multiqc_html': 1, 'fastq': 1, 'fastqc_html': 2, 'fastq_info': 1, 'flagstat': 1, 'idxstats': 1}

