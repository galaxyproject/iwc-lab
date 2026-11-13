# glm-fixed vs nf-core/bamtofastq: data and feature comparison

Foundry run folder: `~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-glm-fixed` (read-only; workflow copied to `<scratch>/compare/glm-fixed/wf/`). nf-core reference: `<scratch>/nfcore-ref/out-<case>/`.

Source commit converted by this run: `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`; compared against the nf-core reference of that commit: `<scratch>/nfcore-ref`

Regenerate: `compare.sh ~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-glm-fixed`

## Workflow (static, from the YAML; heuristic)

- tool steps: **15**; inputs: alignments, fasta, chr, read_qc, stats, multiqc_title, multiqc_config
- outputs: paired_reads<-Build paired read collection/output, fastqc_pre_html<-FastQC on alignments/html_file, fastqc_pre_zip<-FastQC on alignments/text_file, fastqc_post_html<-FastQC on converted reads/html_file, fastqc_post_zip<-FastQC on converted reads/text_file, flagstat<-Flagstat/output1, idxstats<-Idxstats/output, stats<-Samtools stats/output, fastq_info<-FastQ info/output, multiqc_report<-MultiQC report/html_report
- BAM list input: True
- CRAM declared on input: no format restriction
- fasta / reference input: ['fasta']
- fasta wired to steps: ['samtools_stats']
- samtools idxstats: ['samtools_idxstats']
- samtools flagstat: ['samtools_flagstats']
- samtools stats: ['samtools_stats']
- no_stats switch gates steps: ['samtools_flagstats', 'samtools_idxstats', 'samtools_stats']
- FastQC pre-conversion (on alignments): ['fastqc_pre']
- FastQC post-conversion: ['fastqc_post']
- no_read_QC switch gates steps: ['fastqc_pre', 'fastqc_post', 'fastq_info', 'multiqc']
- single/paired detection step: **none**
- chr input: ['chr']
- chr filter steps: ['samtools_view_chr', 'samtools_index_chr']
- samtools view steps (pair classes / chr): ['samtools_view_chr']
- samtools merge: **none**
- collate steps: **none**
- fastx steps: **none**
- cat (R1/R2 concat): **none**
- collate_fast / reads_in_memory wired: **none**
- fastq_info / fastq_utils: ['fastq_info']
- MultiQC: ['multiqc']
- user-defined tools: **none**
- unused inputs: ['multiqc_config']

Self-reported planemo test: **pass** (`~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-glm-fixed/workflow-test-result.json`)

## Case `default`

- planemo run exit: **0**; command: `<scratch>/compare/glm-fixed/default/command.txt`
  - input `alignments`: alignments (nf-core samplesheet: test, test2)
  - input `fasta`: fasta (nf-core --fasta genome.fasta)
  - input `chr`: chr left unset
  - input `read_qc`: kept from run's own test job: True
  - input `stats`: kept from run's own test job: True
  - input `multiqc_title`: kept from run's own test job: 'bamtofastq-glm-fixed-test'
  - input `multiqc_config`: unset (workflow default None)
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/default.nf.test.snap`): 13/13 md5 entries match

### Reads (order-independent; record = name+seq+qual, /1 /2 suffix stripped for matching)

| nf-core file | nf-core records (lines) | gz | Galaxy best match | Galaxy records (lines) | gz | missing | extra | /1 /2 suffix nf/gx | verdict |
|---|---|---|---|---|---|---|---|---|---|
| reads/test2_1.merged.fastq.gz | 2718 (10872) | True | paired_reads/test2__forward.fastqsanger.gz | 2718 (10872) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test2_2.merged.fastq.gz | 2718 (10872) | True | paired_reads/test2__reverse.fastqsanger.gz | 2718 (10872) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test_1.merged.fastq.gz | 2821 (11284) | True | paired_reads/test__forward.fastqsanger.gz | 2821 (11284) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test_2.merged.fastq.gz | 2821 (11284) | True | paired_reads/test__reverse.fastqsanger.gz | 2821 (11284) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |

All reads of the case pooled: nf-core 11078 distinct records, Galaxy 11078; missing in Galaxy 0 ; extra in Galaxy 0 

### Reports

- **flagstat**: nf-core 2, Galaxy 2, same numbers 2/2
- **idxstats**: nf-core 2, Galaxy 2, same numbers 2/2
- **stats**: nf-core 2, Galaxy 2, same numbers 2/2
- **fastq_info**: nf-core 2, Galaxy 2, same numbers 2/2
- **FastQC**: nf-core 6 reports (zip), Galaxy 6 data + 6 HTML; same Basic Statistics (same stage) 6/6; also same module verdicts 6/6
  - fastqc/test.post_conversion_1_fastqc.zip (post, Total Sequences 2821) = fastqc_post_zip/test__forward.txt, fastqc_post_html/test__forward.html
  - fastqc/test.post_conversion_2_fastqc.zip (post, Total Sequences 2821) = fastqc_post_zip/test__reverse.txt, fastqc_post_html/test__reverse.html
  - fastqc/test.pre_conversion_fastqc.zip (pre, Total Sequences 5644) = fastqc_pre_zip/test.txt, fastqc_pre_html/test.html
  - fastqc/test2.post_conversion_1_fastqc.zip (post, Total Sequences 2718) = fastqc_post_zip/test2__forward.txt, fastqc_post_html/test2__forward.html
  - fastqc/test2.post_conversion_2_fastqc.zip (post, Total Sequences 2718) = fastqc_post_zip/test2__reverse.txt, fastqc_post_html/test2__reverse.html
  - fastqc/test2.pre_conversion_fastqc.zip (pre, Total Sequences 5436) = fastqc_pre_zip/test2.txt, fastqc_pre_html/test2.html
  - Galaxy FastQC reports: fastqc_pre_zip/test.txt (5644 seqs), fastqc_pre_zip/test2.txt (5436 seqs), fastqc_post_zip/test2__forward.txt (2718 seqs), fastqc_post_zip/test2__reverse.txt (2718 seqs), fastqc_post_zip/test__forward.txt (2821 seqs), fastqc_post_zip/test__reverse.txt (2821 seqs), fastqc_post_html/test2__forward.html (2718 seqs), fastqc_post_html/test2__reverse.html (2718 seqs), fastqc_post_html/test__forward.html (2821 seqs), fastqc_post_html/test__reverse.html (2821 seqs), fastqc_pre_html/test.html (5644 seqs), fastqc_pre_html/test2.html (5436 seqs)
- **MultiQC** report present: nf-core True, Galaxy True

Inventory by content kind: nf-core {'flagstat': 2, 'idxstats': 2, 'stats': 2, 'fastqc_html': 6, 'fastqc_data': 6, 'fastq': 4, 'multiqc_html': 1, 'other': 7, 'fastq_info': 2}; Galaxy {'multiqc_html': 1, 'flagstat': 2, 'stats': 2, 'fastqc_data': 6, 'fastqc_html': 6, 'fastq': 4, 'idxstats': 2, 'fastq_info': 2}

## Case `chr`

- planemo run exit: **1**; command: `<scratch>/compare/glm-fixed/chr/command.txt`
  - input `alignments`: alignments (nf-core samplesheet: test3)
  - input `fasta`: fasta (nf-core --fasta genome.fasta)
  - input `chr`: chr = 'chrX chrY X Y' (nf-core --chr)
  - input `read_qc`: kept from run's own test job: True
  - input `stats`: kept from run's own test job: True
  - input `multiqc_title`: kept from run's own test job: 'bamtofastq-glm-fixed-test'
  - input `multiqc_config`: unset (workflow default None)
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/chr.nf.test.snap`): 6/6 md5 entries match
- failed jobs (from planemo.log): `❌ Failed job ba5983853e0445b3: toolshed.g2.bx.psu.edu/repos/devteam/samtools_stats/samtools_stats/2.0.9`

No data comparison: planemo downloaded no outputs (invocation failed).

