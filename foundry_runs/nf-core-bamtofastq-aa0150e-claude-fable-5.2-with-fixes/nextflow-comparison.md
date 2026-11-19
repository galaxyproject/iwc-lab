# fable-fixed vs nf-core/bamtofastq: data and feature comparison

Foundry run folder: `~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-fable-fixed` (read-only; workflow copied to `<scratch>/compare/fable-fixed/wf/`). nf-core reference: `<scratch>/nfcore-ref/out-<case>/`.

Source commit converted by this run: `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`; compared against the nf-core reference of that commit: `<scratch>/nfcore-ref`

Regenerate: `compare.sh ~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-fable-fixed`

## Workflow (static, from the YAML; heuristic)

- tool steps: **23**; inputs: Alignments
- outputs: Paired-end reads<-Pair forward and reverse/output, Single-end reads<-Single-end to FASTQ/nonspecific, Samtools flagstat<-Samtools flagstat/output1, Samtools idxstats<-Samtools idxstats/output, Samtools stats<-Samtools stats/output, FastQC pre-conversion report<-FastQC pre-conversion/html_file, FastQC pre-conversion data<-FastQC pre-conversion/text_file, FastQC post-conversion report<-FastQC post-conversion/html_file, FastQC post-conversion data<-FastQC post-conversion/text_file, FASTQ validation (paired-end)<-Validate paired FASTQ/output, FASTQ validation (single-end)<-Validate single-end FASTQ/output, MultiQC report<-MultiQC/html_report, Pairedness per sample<-Collapse pairedness/output
- BAM list input: True
- CRAM declared on input: False
- fasta / reference input: **none**
- fasta wired to steps: **none**
- samtools idxstats: ['Samtools idxstats']
- samtools flagstat: ['Samtools flagstat']
- samtools stats: ['Samtools stats']
- no_stats switch gates steps: **none**
- FastQC pre-conversion (on alignments): ['FastQC pre-conversion']
- FastQC post-conversion: ['FastQC post-conversion']
- no_read_QC switch gates steps: **none**
- single/paired detection step: ['Classify pairedness', 'Collapse pairedness', 'Split alignments by pairedness']
- chr input: **none**
- chr filter steps: **none**
- samtools view steps (pair classes / chr): ['Extract mapped pairs', 'Extract pairs with unmapped mate']
- samtools merge: **none**
- collate steps: **none**
- fastx steps: ['Mapped pairs to FASTQ', 'Unmapped-mate pairs to FASTQ', 'Single-end to FASTQ']
- cat (R1/R2 concat): ['Concatenate forward reads', 'Concatenate reverse reads']
- collate_fast / reads_in_memory wired: **none**
- fastq_info / fastq_utils: ['Validate paired FASTQ', 'Validate single-end FASTQ']
- MultiQC: ['MultiQC']
- user-defined tools: ['Classify pairedness']
- unused inputs: **none**

Self-reported planemo test: **pass** (`~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-fable-fixed/workflow-test-result.json`)

## Case `default`

- planemo run exit: **0**; command: `<scratch>/compare/fable-fixed/default/command.txt`
  - input `Alignments`: alignments (nf-core samplesheet: test, test2)
  - GAP: no fasta input
  - GAP: no chr input
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/default.nf.test.snap`): 13/13 md5 entries match
- workflow outputs with no dataset: Single-end reads (EMPTY COLLECTION), FASTQ validation (single-end) (EMPTY COLLECTION)

### Reads (order-independent; record = name+seq+qual, /1 /2 suffix stripped for matching)

| nf-core file | nf-core records (lines) | gz | Galaxy best match | Galaxy records (lines) | gz | missing | extra | /1 /2 suffix nf/gx | verdict |
|---|---|---|---|---|---|---|---|---|---|
| reads/test2_1.merged.fastq.gz | 2718 (10872) | True | Paired-end reads/test2__forward.fastqsanger.gz | 2718 (10872) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test2_2.merged.fastq.gz | 2718 (10872) | True | Paired-end reads/test2__reverse.fastqsanger.gz | 2718 (10872) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test_1.merged.fastq.gz | 2821 (11284) | True | Paired-end reads/test__forward.fastqsanger.gz | 2821 (11284) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test_2.merged.fastq.gz | 2821 (11284) | True | Paired-end reads/test__reverse.fastqsanger.gz | 2821 (11284) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |

All reads of the case pooled: nf-core 11078 distinct records, Galaxy 11078; missing in Galaxy 0 ; extra in Galaxy 0 

### Reports

- **flagstat**: nf-core 2, Galaxy 2, same numbers 2/2
- **idxstats**: nf-core 2, Galaxy 2, same numbers 2/2
- **stats**: nf-core 2, Galaxy 2, same numbers 2/2
- **fastq_info**: nf-core 2, Galaxy 2, same numbers 2/2
- **FastQC**: nf-core 6 reports (zip), Galaxy 6 data + 6 HTML; same Basic Statistics (same stage) 6/6; also same module verdicts 6/6
  - fastqc/test.post_conversion_1_fastqc.zip (post, Total Sequences 2821) = FastQC post-conversion data/test_forward.txt, FastQC post-conversion report/test_forward.html
  - fastqc/test.post_conversion_2_fastqc.zip (post, Total Sequences 2821) = FastQC post-conversion data/test_reverse.txt, FastQC post-conversion report/test_reverse.html
  - fastqc/test.pre_conversion_fastqc.zip (pre, Total Sequences 5644) = FastQC pre-conversion data/test.txt, FastQC pre-conversion report/test.html
  - fastqc/test2.post_conversion_1_fastqc.zip (post, Total Sequences 2718) = FastQC post-conversion data/test2_forward.txt, FastQC post-conversion report/test2_forward.html
  - fastqc/test2.post_conversion_2_fastqc.zip (post, Total Sequences 2718) = FastQC post-conversion data/test2_reverse.txt, FastQC post-conversion report/test2_reverse.html
  - fastqc/test2.pre_conversion_fastqc.zip (pre, Total Sequences 5436) = FastQC pre-conversion data/test2.txt, FastQC pre-conversion report/test2.html
  - Galaxy FastQC reports: FastQC post-conversion data/test2_forward.txt (2718 seqs), FastQC post-conversion data/test2_reverse.txt (2718 seqs), FastQC post-conversion data/test_forward.txt (2821 seqs), FastQC post-conversion data/test_reverse.txt (2821 seqs), FastQC pre-conversion data/test.txt (5644 seqs), FastQC pre-conversion data/test2.txt (5436 seqs), FastQC post-conversion report/test2_forward.html (2718 seqs), FastQC post-conversion report/test2_reverse.html (2718 seqs), FastQC post-conversion report/test_forward.html (2821 seqs), FastQC post-conversion report/test_reverse.html (2821 seqs), FastQC pre-conversion report/test.html (5644 seqs), FastQC pre-conversion report/test2.html (5436 seqs)
- **MultiQC** report present: nf-core True, Galaxy True

Inventory by content kind: nf-core {'flagstat': 2, 'idxstats': 2, 'stats': 2, 'fastqc_html': 6, 'fastqc_data': 6, 'fastq': 4, 'multiqc_html': 1, 'other': 7, 'fastq_info': 2}; Galaxy {'other': 1, 'multiqc_html': 1, 'fastq': 4, 'fastq_info': 2, 'idxstats': 2, 'fastqc_data': 6, 'flagstat': 2, 'stats': 2, 'fastqc_html': 6}

## Case `chr`

- planemo run exit: **0**; command: `<scratch>/compare/fable-fixed/chr/command.txt`
  - input `Alignments`: alignments (nf-core samplesheet: test3)
  - GAP: no fasta input
  - GAP: no chr input
  - GAP: nf-core case needs --chr 'chrX chrY X Y' but the workflow has no chr input: ran unfiltered
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/chr.nf.test.snap`): 6/6 md5 entries match
- workflow outputs with no dataset: Paired-end reads (EMPTY COLLECTION), FASTQ validation (paired-end) (EMPTY COLLECTION)

### Reads (order-independent; record = name+seq+qual, /1 /2 suffix stripped for matching)

| nf-core file | nf-core records (lines) | gz | Galaxy best match | Galaxy records (lines) | gz | missing | extra | /1 /2 suffix nf/gx | verdict |
|---|---|---|---|---|---|---|---|---|---|
| reads/test3.chrX_chrY_X_Y_other.fq.gz | 572 (2288) | True | Single-end reads/test3.fastqsanger.gz | 12473 (49892) | True | 0 | 11901 | False/False | SUPERSET: all nf-core records present, Galaxy file has 11901 more |

All reads of the case pooled: nf-core 572 distinct records, Galaxy 12473; missing in Galaxy 0 ; extra in Galaxy 11901 ['K00233:65:HKTTVBBXX:5:1101:10094:27602', 'K00233:65:HKTTVBBXX:5:1101:10287:9332', 'K00233:65:HKTTVBBXX:5:1101:10815:46856', 'K00233:65:HKTTVBBXX:5:1101:10866:12761', 'K00233:65:HKTTVBBXX:5:1101:10896:16999', 'K00233:65:HKTTVBBXX:5:1101:11677:18001', 'K00233:65:HKTTVBBXX:5:1101:11830:25720', 'K00233:65:HKTTVBBXX:5:1101:11901:46100', 'K00233:65:HKTTVBBXX:5:1101:12154:2545', 'K00233:65:HKTTVBBXX:5:1101:12327:24437']

### BAM outputs

- nf-core `samtools/test3.chrX_chrY_X_Y.bam` (572 records): Galaxy identical = **False** []
### Reports

- **flagstat**: nf-core 1, Galaxy 1, same numbers 1/1
- **idxstats**: nf-core 1, Galaxy 1, same numbers 1/1
- **stats**: nf-core 1, Galaxy 1, same numbers 1/1
- **fastq_info**: nf-core 1, Galaxy 1, same numbers 1/1
- **FastQC**: nf-core 2 reports (zip), Galaxy 2 data + 2 HTML; same Basic Statistics (same stage) 1/2; also same module verdicts 1/2
  - fastqc/test3.chrX_chrY_X_Y.post_conversion_fastqc.zip (post, Total Sequences 572): no Galaxy post-conversion report with the same Basic Statistics
  - fastqc/test3.pre_conversion_fastqc.zip (pre, Total Sequences 12473) = FastQC pre-conversion data/test3.txt, FastQC pre-conversion report/test3.html
  - Galaxy FastQC reports: FastQC post-conversion data/test3.txt (12473 seqs), FastQC pre-conversion data/test3.txt (12473 seqs), FastQC post-conversion report/test3.html (12473 seqs), FastQC pre-conversion report/test3.html (12473 seqs)
- **MultiQC** report present: nf-core True, Galaxy True

Inventory by content kind: nf-core {'bam': 1, 'flagstat': 1, 'idxstats': 1, 'stats': 1, 'fastqc_html': 2, 'fastqc_data': 2, 'fastq': 1, 'multiqc_html': 1, 'other': 7, 'fastq_info': 1}; Galaxy {'other': 1, 'multiqc_html': 1, 'fastq': 1, 'fastq_info': 1, 'idxstats': 1, 'fastqc_data': 2, 'flagstat': 1, 'stats': 1, 'fastqc_html': 2}

