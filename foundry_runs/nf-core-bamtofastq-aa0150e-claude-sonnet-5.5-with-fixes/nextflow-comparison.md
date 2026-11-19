# sonnet-fixed vs nf-core/bamtofastq: data and feature comparison

Foundry run folder: `~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-sonnet-fixed` (read-only; workflow copied to `<scratch>/compare/sonnet-fixed/wf/`). nf-core reference: `<scratch>/nfcore-ref/out-<case>/`.

Source commit converted by this run: `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`; compared against the nf-core reference of that commit: `<scratch>/nfcore-ref`

Regenerate: `compare.sh ~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-sonnet-fixed`

## Workflow (static, from the YAML; heuristic)

- tool steps: **11**; inputs: alignments, reference_fasta, skip_read_qc, skip_stats
- outputs: converted_reads<-pair_reads/output, flagstat<-samtools_flagstat/output1, idxstats<-samtools_idxstats/output, alignment_stats<-samtools_stats/output, fastqc_input_html<-fastqc_input/html_file, fastqc_input_data<-fastqc_input/text_file, fastqc_reads_html<-fastqc_reads/html_file, fastqc_reads_data<-fastqc_reads/text_file, fastq_integrity<-fastq_integrity/output, multiqc_report<-multiqc/html_report
- BAM list input: True
- CRAM declared on input: True
- fasta / reference input: ['reference_fasta']
- fasta wired to steps: ['convert_to_bam']
- samtools idxstats: ['samtools_idxstats']
- samtools flagstat: ['samtools_flagstat']
- samtools stats: ['samtools_stats']
- no_stats switch gates steps: ['samtools_flagstat', 'samtools_idxstats', 'samtools_stats']
- FastQC pre-conversion (on alignments): ['fastqc_input']
- FastQC post-conversion: ['fastqc_reads']
- no_read_QC switch gates steps: ['fastqc_input', 'fastqc_reads']
- single/paired detection step: **none**
- chr input: **none**
- chr filter steps: **none**
- samtools view steps (pair classes / chr): ['convert_to_bam']
- samtools merge: **none**
- collate steps: **none**
- fastx steps: ['bam_to_fastq']
- cat (R1/R2 concat): **none**
- collate_fast / reads_in_memory wired: **none**
- fastq_info / fastq_utils: ['fastq_integrity']
- MultiQC: ['multiqc']
- user-defined tools: **none**
- unused inputs: **none**

Self-reported planemo test: **pass** (`~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-sonnet-fixed/workflow-test-result.json`)

## Case `default`

- planemo run exit: **0**; command: `<scratch>/compare/sonnet-fixed/default/command.txt`
  - input `alignments`: alignments (nf-core samplesheet: test, test2)
  - input `reference_fasta`: fasta (nf-core --fasta genome.fasta)
  - input `skip_read_qc`: kept from run's own test job: False
  - input `skip_stats`: kept from run's own test job: False
  - GAP: no chr input
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/default.nf.test.snap`): 13/13 md5 entries match

### Reads (order-independent; record = name+seq+qual, /1 /2 suffix stripped for matching)

| nf-core file | nf-core records (lines) | gz | Galaxy best match | Galaxy records (lines) | gz | missing | extra | /1 /2 suffix nf/gx | verdict |
|---|---|---|---|---|---|---|---|---|---|
| reads/test2_1.merged.fastq.gz | 2718 (10872) | True | converted_reads/test2__forward.fastqsanger.gz | 2718 (10872) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test2_2.merged.fastq.gz | 2718 (10872) | True | converted_reads/test2__reverse.fastqsanger.gz | 2718 (10872) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test_1.merged.fastq.gz | 2821 (11284) | True | converted_reads/test__forward.fastqsanger.gz | 2821 (11284) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test_2.merged.fastq.gz | 2821 (11284) | True | converted_reads/test__reverse.fastqsanger.gz | 2821 (11284) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |

All reads of the case pooled: nf-core 11078 distinct records, Galaxy 11078; missing in Galaxy 0 ; extra in Galaxy 0 

### Reports

- **flagstat**: nf-core 2, Galaxy 2, same numbers 2/2
- **idxstats**: nf-core 2, Galaxy 2, same numbers 2/2
- **stats**: nf-core 2, Galaxy 2, same numbers 2/2
- **fastq_info**: nf-core 2, Galaxy 2, same numbers 2/2
- **FastQC**: nf-core 6 reports (zip), Galaxy 6 data + 6 HTML; same Basic Statistics (same stage) 4/6; also same module verdicts 4/6
  - fastqc/test.post_conversion_1_fastqc.zip (post, Total Sequences 2821) = fastqc_reads_data/test__forward.txt, fastqc_reads_html/test__forward.html
  - fastqc/test.post_conversion_2_fastqc.zip (post, Total Sequences 2821) = fastqc_reads_data/test__reverse.txt, fastqc_reads_html/test__reverse.html
  - fastqc/test.pre_conversion_fastqc.zip (pre, Total Sequences 5644): no Galaxy pre-conversion report with the same Basic Statistics; coincides with Galaxy report of the other stage: ['fastqc_input_data/test.txt', 'fastqc_input_html/test.html']
  - fastqc/test2.post_conversion_1_fastqc.zip (post, Total Sequences 2718) = fastqc_reads_data/test2__forward.txt, fastqc_reads_html/test2__forward.html
  - fastqc/test2.post_conversion_2_fastqc.zip (post, Total Sequences 2718) = fastqc_reads_data/test2__reverse.txt, fastqc_reads_html/test2__reverse.html
  - fastqc/test2.pre_conversion_fastqc.zip (pre, Total Sequences 5436): no Galaxy pre-conversion report with the same Basic Statistics; coincides with Galaxy report of the other stage: ['fastqc_input_data/test2.txt', 'fastqc_input_html/test2.html']
  - Galaxy FastQC reports: fastqc_reads_data/test2__forward.txt (2718 seqs), fastqc_reads_data/test2__reverse.txt (2718 seqs), fastqc_reads_data/test__forward.txt (2821 seqs), fastqc_reads_data/test__reverse.txt (2821 seqs), fastqc_input_data/test.txt (5644 seqs), fastqc_input_data/test2.txt (5436 seqs), fastqc_reads_html/test2__forward.html (2718 seqs), fastqc_reads_html/test2__reverse.html (2718 seqs), fastqc_reads_html/test__forward.html (2821 seqs), fastqc_reads_html/test__reverse.html (2821 seqs), fastqc_input_html/test.html (5644 seqs), fastqc_input_html/test2.html (5436 seqs)
- **MultiQC** report present: nf-core True, Galaxy True

Inventory by content kind: nf-core {'flagstat': 2, 'idxstats': 2, 'stats': 2, 'fastqc_html': 6, 'fastqc_data': 6, 'fastq': 4, 'multiqc_html': 1, 'other': 7, 'fastq_info': 2}; Galaxy {'multiqc_html': 1, 'flagstat': 2, 'fastq_info': 2, 'fastq': 4, 'fastqc_data': 6, 'stats': 2, 'idxstats': 2, 'fastqc_html': 6}

## Case `chr`

- planemo run exit: **0**; command: `<scratch>/compare/sonnet-fixed/chr/command.txt`
  - input `alignments`: alignments (nf-core samplesheet: test3)
  - input `reference_fasta`: fasta (nf-core --fasta genome.fasta)
  - input `skip_read_qc`: kept from run's own test job: False
  - input `skip_stats`: kept from run's own test job: False
  - GAP: no chr input
  - GAP: nf-core case needs --chr 'chrX chrY X Y' but the workflow has no chr input: ran unfiltered
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/chr.nf.test.snap`): 6/6 md5 entries match

### Reads (order-independent; record = name+seq+qual, /1 /2 suffix stripped for matching)

| nf-core file | nf-core records (lines) | gz | Galaxy best match | Galaxy records (lines) | gz | missing | extra | /1 /2 suffix nf/gx | verdict |
|---|---|---|---|---|---|---|---|---|---|
| reads/test3.chrX_chrY_X_Y_other.fq.gz | 572 (2288) | True | — | — | — | 572 | — | — | MISSING: no Galaxy FASTQ shares any read with this file |
| (no nf-core counterpart) | | | converted_reads/test3__forward.fastqsanger.gz | EMPTY FILE | | | | | |
| (no nf-core counterpart) | | | converted_reads/test3__reverse.fastqsanger.gz | EMPTY FILE | | | | | |

All reads of the case pooled: nf-core 572 distinct records, Galaxy 0; missing in Galaxy 572 ['K00233:65:HKTTVBBXX:5:1101:13707:7416', 'K00233:65:HKTTVBBXX:5:1101:15087:7591', 'K00233:65:HKTTVBBXX:5:1101:21450:12673', 'K00233:65:HKTTVBBXX:5:1101:2737:46012', 'K00233:65:HKTTVBBXX:5:1101:6837:43726', 'K00233:65:HKTTVBBXX:5:1102:16670:1121', 'K00233:65:HKTTVBBXX:5:1102:26849:44675', 'K00233:65:HKTTVBBXX:5:1102:29751:9578', 'K00233:65:HKTTVBBXX:5:1102:7233:27215', 'K00233:65:HKTTVBBXX:5:1103:10927:35374']; extra in Galaxy 0 

### BAM outputs

- nf-core `samtools/test3.chrX_chrY_X_Y.bam` (572 records): Galaxy identical = **False** []
### Reports

- **flagstat**: nf-core 1, Galaxy 1, same numbers 1/1
- **idxstats**: nf-core 1, Galaxy 1, same numbers 1/1
- **stats**: nf-core 1, Galaxy 1, same numbers 1/1
- **fastq_info**: nf-core 1, Galaxy 1, same numbers 0/1
  - fastqutils/test3.chrX_chrY_X_Y.txt vs fastq_integrity/test3.txt differ: `{"verdict": ["OK", "NOT OK"]}`
- **FastQC**: nf-core 2 reports (zip), Galaxy 3 data + 3 HTML; same Basic Statistics (same stage) 0/2; also same module verdicts 0/2
  - fastqc/test3.chrX_chrY_X_Y.post_conversion_fastqc.zip (post, Total Sequences 572): no Galaxy post-conversion report with the same Basic Statistics
  - fastqc/test3.pre_conversion_fastqc.zip (pre, Total Sequences 12473): no Galaxy pre-conversion report with the same Basic Statistics; coincides with Galaxy report of the other stage: ['fastqc_input_data/test3.txt', 'fastqc_input_html/test3.html']
  - Galaxy FastQC reports: fastqc_reads_data/test3__forward.txt (0 seqs), fastqc_reads_data/test3__reverse.txt (0 seqs), fastqc_input_data/test3.txt (12473 seqs), fastqc_reads_html/test3__forward.html (0 seqs), fastqc_reads_html/test3__reverse.html (0 seqs), fastqc_input_html/test3.html (12473 seqs)
- **MultiQC** report present: nf-core True, Galaxy True

Inventory by content kind: nf-core {'bam': 1, 'flagstat': 1, 'idxstats': 1, 'stats': 1, 'fastqc_html': 2, 'fastqc_data': 2, 'fastq': 1, 'multiqc_html': 1, 'other': 7, 'fastq_info': 1}; Galaxy {'multiqc_html': 1, 'flagstat': 1, 'fastq_info': 1, 'empty': 2, 'fastqc_data': 3, 'stats': 1, 'idxstats': 1, 'fastqc_html': 3}

