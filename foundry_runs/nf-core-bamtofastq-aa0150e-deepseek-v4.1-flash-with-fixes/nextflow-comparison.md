# deepseek-fixed vs nf-core/bamtofastq: data and feature comparison

Foundry run folder: `~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-deepseek-fixed` (read-only; workflow copied to `<scratch>/compare/deepseek-fixed/wf/`). nf-core reference: `<scratch>/nfcore-ref/out-<case>/`.

Source commit converted by this run: `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`; compared against the nf-core reference of that commit: `<scratch>/nfcore-ref`

Regenerate: `compare.sh ~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-deepseek-fixed`

## Workflow (static, from the YAML; heuristic)

- tool steps: **18**; inputs: input, fasta, layout, no_read_QC, no_stats, samtools_collate_fast, multiqc_title
- outputs: reads_paired<-zip_reads_paired/output, reads_single<-fastq_single/other, fastqc_pre_conversion<-fastqc_pre/html_file, fastqc_post_conversion_paired<-fastqc_post_paired/html_file, fastqc_post_conversion_single<-fastqc_post_single/html_file, samtools_flagstat<-flagstat/output1, samtools_idxstats<-idxstats/output, samtools_stats<-stats/output, multiqc_report<-multiqc/html_report
- BAM list input: True
- CRAM declared on input: no format restriction
- fasta / reference input: ['fasta']
- fasta wired to steps: ['fastq_mapped', 'fastq_single', 'fastq_unmapped', 'merge_unmapped']
- samtools idxstats: ['idxstats']
- samtools flagstat: ['flagstat']
- samtools stats: ['stats']
- no_stats switch gates steps: ['flagstat', 'idxstats', 'stats']
- FastQC pre-conversion (on alignments): ['fastqc_pre']
- FastQC post-conversion: ['fastqc_post_paired', 'fastqc_post_single']
- no_read_QC switch gates steps: ['fastqc_pre', 'fastqc_post_paired', 'fastqc_post_single']
- single/paired detection step: **none**
- chr input: **none**
- chr filter steps: **none**
- samtools view steps (pair classes / chr): ['view_map_map', 'view_unmap_unmap', 'view_unmap_map', 'view_map_unmap']
- samtools merge: ['merge_unmapped']
- collate steps: ['fastq_unmapped', 'fastq_mapped', 'fastq_single']
- fastx steps: **none**
- cat (R1/R2 concat): ['cat_r1', 'cat_r2']
- collate_fast / reads_in_memory wired: ['fastq_mapped', 'fastq_single', 'fastq_unmapped']
- fastq_info / fastq_utils: **none**
- MultiQC: ['multiqc']
- user-defined tools: ['merge_unmapped', 'fastq_unmapped', 'fastq_mapped', 'fastq_single']
- unused inputs: **none**

Self-reported planemo test: UNVERIFIED (no result file found)

## Case `default`

- planemo run exit: **0**; command: `<scratch>/compare/deepseek-fixed/default/command.txt`
  - input `input`: alignments (nf-core samplesheet: test, test2)
  - input `fasta`: fasta (nf-core --fasta genome.fasta)
  - input `layout`: kept from run's own test job: 'paired'
  - input `no_read_QC`: kept from run's own test job: False
  - input `no_stats`: kept from run's own test job: False
  - input `samtools_collate_fast`: kept from run's own test job: False
  - input `multiqc_title`: unset (workflow default None)
  - GAP: no chr input
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/default.nf.test.snap`): 13/13 md5 entries match

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
- **fastq_info**: nf-core 2, Galaxy 0, same numbers 0/2
  - fastqutils/test.txt: no Galaxy counterpart (0 candidates)
  - fastqutils/test2.txt: no Galaxy counterpart (0 candidates)
- **FastQC**: nf-core 6 reports (zip), Galaxy 0 data + 6 HTML; same Basic Statistics (same stage) 6/6; also same module verdicts 0/6
  - fastqc/test.post_conversion_1_fastqc.zip (post, Total Sequences 2821) = fastqc_post_conversion_paired/test__forward.html (module verdicts not equal or not available from HTML)
  - fastqc/test.post_conversion_2_fastqc.zip (post, Total Sequences 2821) = fastqc_post_conversion_paired/test__reverse.html (module verdicts not equal or not available from HTML)
  - fastqc/test.pre_conversion_fastqc.zip (pre, Total Sequences 5644) = fastqc_pre_conversion/test.html (module verdicts not equal or not available from HTML)
  - fastqc/test2.post_conversion_1_fastqc.zip (post, Total Sequences 2718) = fastqc_post_conversion_paired/test2__forward.html (module verdicts not equal or not available from HTML)
  - fastqc/test2.post_conversion_2_fastqc.zip (post, Total Sequences 2718) = fastqc_post_conversion_paired/test2__reverse.html (module verdicts not equal or not available from HTML)
  - fastqc/test2.pre_conversion_fastqc.zip (pre, Total Sequences 5436) = fastqc_pre_conversion/test2.html (module verdicts not equal or not available from HTML)
  - Galaxy FastQC reports: fastqc_post_conversion_paired/test2__forward.html (2718 seqs), fastqc_post_conversion_paired/test2__reverse.html (2718 seqs), fastqc_post_conversion_paired/test__forward.html (2821 seqs), fastqc_post_conversion_paired/test__reverse.html (2821 seqs), fastqc_pre_conversion/test.html (5644 seqs), fastqc_pre_conversion/test2.html (5436 seqs)
- **MultiQC** report present: nf-core True, Galaxy True

Inventory by content kind: nf-core {'flagstat': 2, 'idxstats': 2, 'stats': 2, 'fastqc_html': 6, 'fastqc_data': 6, 'fastq': 4, 'multiqc_html': 1, 'other': 7, 'fastq_info': 2}; Galaxy {'stats': 2, 'multiqc_html': 1, 'other': 4, 'fastq': 4, 'fastqc_html': 6, 'flagstat': 2, 'idxstats': 2}

## Case `chr`

- planemo run exit: **0**; command: `<scratch>/compare/deepseek-fixed/chr/command.txt`
  - input `input`: alignments (nf-core samplesheet: test3)
  - input `fasta`: fasta (nf-core --fasta genome.fasta)
  - input `layout`: kept from run's own test job: 'paired'
  - input `no_read_QC`: kept from run's own test job: False
  - input `no_stats`: kept from run's own test job: False
  - input `samtools_collate_fast`: kept from run's own test job: False
  - input `multiqc_title`: unset (workflow default None)
  - GAP: no chr input
  - GAP: nf-core case needs --chr 'chrX chrY X Y' but the workflow has no chr input: ran unfiltered
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/chr.nf.test.snap`): 6/6 md5 entries match

### Reads (order-independent; record = name+seq+qual, /1 /2 suffix stripped for matching)

| nf-core file | nf-core records (lines) | gz | Galaxy best match | Galaxy records (lines) | gz | missing | extra | /1 /2 suffix nf/gx | verdict |
|---|---|---|---|---|---|---|---|---|---|
| reads/test3.chrX_chrY_X_Y_other.fq.gz | 572 (2288) | True | — | — | — | 572 | — | — | MISSING: no Galaxy FASTQ shares any read with this file |
| (no nf-core counterpart) | | | reads_paired/test3__forward.fastqsanger.gz | EMPTY FILE | | | | | |
| (no nf-core counterpart) | | | reads_paired/test3__reverse.fastqsanger.gz | EMPTY FILE | | | | | |

All reads of the case pooled: nf-core 572 distinct records, Galaxy 0; missing in Galaxy 572 ['K00233:65:HKTTVBBXX:5:1101:13707:7416', 'K00233:65:HKTTVBBXX:5:1101:15087:7591', 'K00233:65:HKTTVBBXX:5:1101:21450:12673', 'K00233:65:HKTTVBBXX:5:1101:2737:46012', 'K00233:65:HKTTVBBXX:5:1101:6837:43726', 'K00233:65:HKTTVBBXX:5:1102:16670:1121', 'K00233:65:HKTTVBBXX:5:1102:26849:44675', 'K00233:65:HKTTVBBXX:5:1102:29751:9578', 'K00233:65:HKTTVBBXX:5:1102:7233:27215', 'K00233:65:HKTTVBBXX:5:1103:10927:35374']; extra in Galaxy 0 

### BAM outputs

- nf-core `samtools/test3.chrX_chrY_X_Y.bam` (572 records): Galaxy identical = **False** []
### Reports

- **flagstat**: nf-core 1, Galaxy 1, same numbers 1/1
- **idxstats**: nf-core 1, Galaxy 1, same numbers 1/1
- **stats**: nf-core 1, Galaxy 1, same numbers 1/1
- **fastq_info**: nf-core 1, Galaxy 0, same numbers 0/1
  - fastqutils/test3.chrX_chrY_X_Y.txt: no Galaxy counterpart (0 candidates)
- **FastQC**: nf-core 2 reports (zip), Galaxy 0 data + 3 HTML; same Basic Statistics (same stage) 1/2; also same module verdicts 0/2
  - fastqc/test3.chrX_chrY_X_Y.post_conversion_fastqc.zip (post, Total Sequences 572): no Galaxy post-conversion report with the same Basic Statistics
  - fastqc/test3.pre_conversion_fastqc.zip (pre, Total Sequences 12473) = fastqc_pre_conversion/test3.html (module verdicts not equal or not available from HTML)
  - Galaxy FastQC reports: fastqc_post_conversion_paired/test3__forward.html (0 seqs), fastqc_post_conversion_paired/test3__reverse.html (0 seqs), fastqc_pre_conversion/test3.html (12473 seqs)
- **MultiQC** report present: nf-core True, Galaxy True

Inventory by content kind: nf-core {'bam': 1, 'flagstat': 1, 'idxstats': 1, 'stats': 1, 'fastqc_html': 2, 'fastqc_data': 2, 'fastq': 1, 'multiqc_html': 1, 'other': 7, 'fastq_info': 1}; Galaxy {'stats': 1, 'multiqc_html': 1, 'other': 2, 'empty': 2, 'fastqc_html': 3, 'flagstat': 1, 'idxstats': 1}

