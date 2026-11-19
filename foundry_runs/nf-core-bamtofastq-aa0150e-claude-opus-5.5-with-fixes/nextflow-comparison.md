# claude-fixed vs nf-core/bamtofastq: data and feature comparison

Foundry run folder: `~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-claude-fixed` (read-only; workflow copied to `<scratch>/compare/claude-fixed/wf/`). nf-core reference: `<scratch>/nfcore-ref/out-<case>/`.

Source commit converted by this run: `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`; compared against the nf-core reference of that commit: `<scratch>/nfcore-ref`

Regenerate: `compare.sh ~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-claude-fixed`

## Workflow (static, from the YAML; heuristic)

- tool steps: **26**; inputs: alignments, reference_fasta, run_read_qc, run_stats
- outputs: samtools_flagstat<-flagstat/output1, samtools_idxstats<-idxstats/output, samtools_stats<-stats/output, fastqc_pre_html<-fastqc_pre/html_file, fastq_paired<-zip_pairs/output, fastq_single_end<-collate_fastq_single/output, fastqc_post_paired_html<-fastqc_post_paired/html_file, fastqc_post_single_html<-fastqc_post_single/html_file, fastq_info_paired<-fastq_info_paired/output, fastq_info_single<-fastq_info_single/output, fastqc_pre_raw<-fastqc_pre/text_file, fastqc_post_paired_raw<-fastqc_post_paired/text_file, fastqc_post_single_raw<-fastqc_post_single/text_file
- BAM list input: True
- CRAM declared on input: True
- fasta / reference input: ['reference_fasta']
- fasta wired to steps: ['classify_alignment', 'stats', 'view_map_map', 'view_map_unmap', 'view_unmap_map', 'view_unmap_unmap']
- samtools idxstats: ['idxstats']
- samtools flagstat: ['flagstat']
- samtools stats: ['stats']
- no_stats switch gates steps: ['flagstat', 'idxstats', 'stats']
- FastQC pre-conversion (on alignments): **none**
- FastQC post-conversion: ['fastqc_pre', 'fastqc_post_paired', 'fastqc_post_single']
- no_read_QC switch gates steps: ['fastqc_pre', 'fastqc_post_paired', 'fastqc_post_single']
- single/paired detection step: ['classify_alignment', 'split_by_pairing']
- chr input: **none**
- chr filter steps: **none**
- samtools view steps (pair classes / chr): ['view_map_map', 'view_unmap_unmap', 'view_unmap_map', 'view_map_unmap']
- samtools merge: ['merge_unmapped']
- collate steps: ['collate_fastq_mapped', 'collate_fastq_unmapped', 'collate_fastq_single']
- fastx steps: ['collate_fastq_mapped', 'collate_fastq_unmapped', 'collate_fastq_single']
- cat (R1/R2 concat): ['cat_r1', 'cat_r2']
- collate_fast / reads_in_memory wired: **none**
- fastq_info / fastq_utils: ['fastq_info_paired', 'fastq_info_single']
- MultiQC: **none**
- user-defined tools: ['classify_alignment']
- unused inputs: **none**

Self-reported planemo test: **pass** (`~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-claude-fixed/workflow-test-result.json`)

## Case `default`

- planemo run exit: **0**; command: `<scratch>/compare/claude-fixed/default/command.txt`
  - input `alignments`: alignments (nf-core samplesheet: test, test2)
  - input `reference_fasta`: fasta (nf-core --fasta genome.fasta)
  - input `run_read_qc`: kept from run's own test job: True
  - input `run_stats`: kept from run's own test job: True
  - GAP: no chr input
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/default.nf.test.snap`): 13/13 md5 entries match
- workflow outputs with no dataset: fastq_single_end (EMPTY COLLECTION), fastqc_post_single_html (EMPTY COLLECTION), fastqc_post_single_raw (EMPTY COLLECTION), fastq_info_single (EMPTY COLLECTION)

### Reads (order-independent; record = name+seq+qual, /1 /2 suffix stripped for matching)

| nf-core file | nf-core records (lines) | gz | Galaxy best match | Galaxy records (lines) | gz | missing | extra | /1 /2 suffix nf/gx | verdict |
|---|---|---|---|---|---|---|---|---|---|
| reads/test2_1.merged.fastq.gz | 2718 (10872) | True | fastq_paired/test2__forward.fastqsanger.gz | 2718 (10872) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test2_2.merged.fastq.gz | 2718 (10872) | True | fastq_paired/test2__reverse.fastqsanger.gz | 2718 (10872) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test_1.merged.fastq.gz | 2821 (11284) | True | fastq_paired/test__forward.fastqsanger.gz | 2821 (11284) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |
| reads/test_2.merged.fastq.gz | 2821 (11284) | True | fastq_paired/test__reverse.fastqsanger.gz | 2821 (11284) | True | 0 | 0 | True/True | IDENTICAL (order-independent) |

All reads of the case pooled: nf-core 11078 distinct records, Galaxy 11078; missing in Galaxy 0 ; extra in Galaxy 0 

### Reports

- **flagstat**: nf-core 2, Galaxy 2, same numbers 2/2
- **idxstats**: nf-core 2, Galaxy 2, same numbers 2/2
- **stats**: nf-core 2, Galaxy 2, same numbers 2/2
- **fastq_info**: nf-core 2, Galaxy 2, same numbers 2/2
- **FastQC**: nf-core 6 reports (zip), Galaxy 6 data + 6 HTML; same Basic Statistics (same stage) 6/6; also same module verdicts 6/6
  - fastqc/test.post_conversion_1_fastqc.zip (post, Total Sequences 2821) = fastqc_post_paired_raw/test__forward.txt, fastqc_post_paired_html/test__forward.html
  - fastqc/test.post_conversion_2_fastqc.zip (post, Total Sequences 2821) = fastqc_post_paired_raw/test__reverse.txt, fastqc_post_paired_html/test__reverse.html
  - fastqc/test.pre_conversion_fastqc.zip (pre, Total Sequences 5644) = fastqc_pre_raw/test.txt, fastqc_pre_html/test.html
  - fastqc/test2.post_conversion_1_fastqc.zip (post, Total Sequences 2718) = fastqc_post_paired_raw/test2__forward.txt, fastqc_post_paired_html/test2__forward.html
  - fastqc/test2.post_conversion_2_fastqc.zip (post, Total Sequences 2718) = fastqc_post_paired_raw/test2__reverse.txt, fastqc_post_paired_html/test2__reverse.html
  - fastqc/test2.pre_conversion_fastqc.zip (pre, Total Sequences 5436) = fastqc_pre_raw/test2.txt, fastqc_pre_html/test2.html
  - Galaxy FastQC reports: fastqc_post_paired_raw/test2__forward.txt (2718 seqs), fastqc_post_paired_raw/test2__reverse.txt (2718 seqs), fastqc_post_paired_raw/test__forward.txt (2821 seqs), fastqc_post_paired_raw/test__reverse.txt (2821 seqs), fastqc_pre_raw/test.txt (5644 seqs), fastqc_pre_raw/test2.txt (5436 seqs), fastqc_pre_html/test.html (5644 seqs), fastqc_pre_html/test2.html (5436 seqs), fastqc_post_paired_html/test2__forward.html (2718 seqs), fastqc_post_paired_html/test2__reverse.html (2718 seqs), fastqc_post_paired_html/test__forward.html (2821 seqs), fastqc_post_paired_html/test__reverse.html (2821 seqs)
- **MultiQC** report present: nf-core True, Galaxy False

Inventory by content kind: nf-core {'flagstat': 2, 'idxstats': 2, 'stats': 2, 'fastqc_html': 6, 'fastqc_data': 6, 'fastq': 4, 'multiqc_html': 1, 'other': 7, 'fastq_info': 2}; Galaxy {'stats': 2, 'fastq_info': 2, 'fastq': 4, 'fastqc_data': 6, 'flagstat': 2, 'fastqc_html': 6, 'idxstats': 2}

## Case `chr`

- planemo run exit: **1**; command: `<scratch>/compare/claude-fixed/chr/command.txt`
  - input `alignments`: alignments (nf-core samplesheet: test3)
  - input `reference_fasta`: fasta (nf-core --fasta genome.fasta)
  - input `run_read_qc`: kept from run's own test job: True
  - input `run_stats`: kept from run's own test job: True
  - GAP: no chr input
  - GAP: nf-core case needs --chr 'chrX chrY X Y' but the workflow has no chr input: ran unfiltered
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/chr.nf.test.snap`): 6/6 md5 entries match
- failed jobs (from planemo.log): `❌ Failed job d9a67bb7dcbc8b43: toolshed.g2.bx.psu.edu/repos/devteam/samtools_stats/samtools_stats/2.0.9`

No data comparison: planemo downloaded no outputs (invocation failed).

