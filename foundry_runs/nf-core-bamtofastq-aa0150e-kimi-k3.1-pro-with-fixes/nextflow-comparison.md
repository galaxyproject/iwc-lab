# kimi-fixed vs nf-core/bamtofastq: data and feature comparison

Foundry run folder: `~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-kimi-fixed` (read-only; workflow copied to `<scratch>/compare/kimi-fixed/wf/`). nf-core reference: `<scratch>/nfcore-ref/out-<case>/`.

Source commit converted by this run: `aa0150e34a159fa9f3d0ff62128cafeaa2e5fe78`; compared against the nf-core reference of that commit: `<scratch>/nfcore-ref`

Regenerate: `compare.sh ~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-kimi-fixed`

## Workflow (static, from the YAML; heuristic)

- tool steps: **14**; inputs: alignment_samples, chromosome, skip_read_qc, alignment_stats_mode, fast_collate, reads_in_memory, reference_fasta, reference_fai, multiqc_title, multiqc_logo, reference_mode
- outputs: pre_conversion_fastqc_html<-Pre-conversion FastQC/html_file, pre_conversion_fastqc_data<-Pre-conversion FastQC/text_file, pre_conversion_fastqc_zip<-Pre-conversion FastQC/zip_file, alignment_flagstat<-Alignment flagstat/output1, alignment_idxstats<-Alignment idxstats, alignment_stats<-Select reference-mode alignment statistics/data_param, converted_reads<-Convert BAM and CRAM to FASTQ/reads, post_conversion_fastqc_html<-Post-conversion FastQC/html_file, post_conversion_fastqc_data<-Post-conversion FastQC/text_file, post_conversion_fastqc_zip<-Post-conversion FastQC/zip_file, software_versions<-Aggregate software versions/versions, multiqc_report<-Aggregate QC with MultiQC/html_report, multiqc_data<-Aggregate QC with MultiQC/stats, fastq_validation<-Format FASTQ validation report/info
- BAM list input: True
- CRAM declared on input: True
- fasta / reference input: ['reference_fasta', 'reference_fai']
- fasta wired to steps: ['Alignment statistics with reference', 'Build reference FAI when absent', 'Convert BAM and CRAM to FASTQ', 'Select supplied or rebuilt reference FAI']
- samtools idxstats: ['Alignment idxstats']
- samtools flagstat: ['Alignment flagstat']
- samtools stats: **none**
- no_stats switch gates steps: **none**
- FastQC pre-conversion (on alignments): **none**
- FastQC post-conversion: **none**
- no_read_QC switch gates steps: ['Pre-conversion FastQC', 'Post-conversion FastQC']
- single/paired detection step: **none**
- chr input: **none**
- chr filter steps: **none**
- samtools view steps (pair classes / chr): **none**
- samtools merge: **none**
- collate steps: **none**
- fastx steps: **none**
- cat (R1/R2 concat): **none**
- collate_fast / reads_in_memory wired: ['Convert BAM and CRAM to FASTQ']
- fastq_info / fastq_utils: **none**
- MultiQC: ['Aggregate QC with MultiQC']
- user-defined tools: ['Pre-conversion FastQC', 'Alignment statistics with reference', 'Alignment statistics without reference', 'Convert BAM and CRAM to FASTQ', 'Post-conversion FastQC', 'Aggregate software versions', 'Format FASTQ validation report']
- unused inputs: **none**

Self-reported planemo test: **fail** (`~/Galaxy/biohackathon-31/runs/nf-core-bamtofastq-kimi-fixed/workflow-test-result.json`)

## Case `default`

- planemo run exit: **0**; command: `<scratch>/compare/kimi-fixed/default/command.txt`
  - input `alignment_samples`: alignments (nf-core samplesheet: test, test2)
  - input `chromosome`: chr = '' (run's own 'no chr' value)
  - input `skip_read_qc`: kept from run's own test job: False
  - input `alignment_stats_mode`: kept from run's own test job: 'with_reference'
  - input `fast_collate`: kept from run's own test job: False
  - input `reads_in_memory`: kept from run's own test job: 100000
  - input `reference_fasta`: fasta (nf-core --fasta genome.fasta)
  - input `reference_fai`: fasta (nf-core --fasta genome.fasta)
  - input `multiqc_title`: kept from run's own test job: ''
  - input `multiqc_logo`: unset (workflow default None)
  - input `reference_mode`: kept from run's own test job: 'build_fai'
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
- **FastQC**: nf-core 6 reports (zip), Galaxy 12 data + 6 HTML; same Basic Statistics (same stage) 6/6; also same module verdicts 6/6
  - fastqc/test.post_conversion_1_fastqc.zip (post, Total Sequences 2821) = post_conversion_fastqc_zip/test__forward.zip, post_conversion_fastqc_data/test__forward.txt, post_conversion_fastqc_html/test__forward.html
  - fastqc/test.post_conversion_2_fastqc.zip (post, Total Sequences 2821) = post_conversion_fastqc_zip/test__reverse.zip, post_conversion_fastqc_data/test__reverse.txt, post_conversion_fastqc_html/test__reverse.html
  - fastqc/test.pre_conversion_fastqc.zip (pre, Total Sequences 5644) = pre_conversion_fastqc_zip/test.zip, pre_conversion_fastqc_data/test.txt, pre_conversion_fastqc_html/test.html
  - fastqc/test2.post_conversion_1_fastqc.zip (post, Total Sequences 2718) = post_conversion_fastqc_zip/test2__forward.zip, post_conversion_fastqc_data/test2__forward.txt, post_conversion_fastqc_html/test2__forward.html
  - fastqc/test2.post_conversion_2_fastqc.zip (post, Total Sequences 2718) = post_conversion_fastqc_zip/test2__reverse.zip, post_conversion_fastqc_data/test2__reverse.txt, post_conversion_fastqc_html/test2__reverse.html
  - fastqc/test2.pre_conversion_fastqc.zip (pre, Total Sequences 5436) = pre_conversion_fastqc_zip/test2.zip, pre_conversion_fastqc_data/test2.txt, pre_conversion_fastqc_html/test2.html
  - Galaxy FastQC reports: post_conversion_fastqc_zip/test2__forward.zip (2718 seqs), post_conversion_fastqc_zip/test2__reverse.zip (2718 seqs), post_conversion_fastqc_zip/test__forward.zip (2821 seqs), post_conversion_fastqc_zip/test__reverse.zip (2821 seqs), pre_conversion_fastqc_zip/test.zip (5644 seqs), pre_conversion_fastqc_zip/test2.zip (5436 seqs), pre_conversion_fastqc_data/test.txt (5644 seqs), pre_conversion_fastqc_data/test2.txt (5436 seqs), post_conversion_fastqc_data/test2__forward.txt (2718 seqs), post_conversion_fastqc_data/test2__reverse.txt (2718 seqs), post_conversion_fastqc_data/test__forward.txt (2821 seqs), post_conversion_fastqc_data/test__reverse.txt (2821 seqs), post_conversion_fastqc_html/test2__forward.html (2718 seqs), post_conversion_fastqc_html/test2__reverse.html (2718 seqs), post_conversion_fastqc_html/test__forward.html (2821 seqs), post_conversion_fastqc_html/test__reverse.html (2821 seqs), pre_conversion_fastqc_html/test.html (5644 seqs), pre_conversion_fastqc_html/test2.html (5436 seqs)
- **MultiQC** report present: nf-core True, Galaxy True

Inventory by content kind: nf-core {'flagstat': 2, 'idxstats': 2, 'stats': 2, 'fastqc_html': 6, 'fastqc_data': 6, 'fastq': 4, 'multiqc_html': 1, 'other': 7, 'fastq_info': 2}; Galaxy {'fastq_info': 2, 'multiqc_html': 1, 'fastqc_html': 6, 'fastq': 4, 'stats': 2, 'fastqc_data': 12, 'other': 2, 'flagstat': 2, 'idxstats': 2}

## Case `chr`

- planemo run exit: **1**; command: `<scratch>/compare/kimi-fixed/chr/command.txt`
  - input `alignment_samples`: alignments (nf-core samplesheet: test3)
  - input `chromosome`: chr = 'chrX chrY X Y' (nf-core --chr)
  - input `skip_read_qc`: kept from run's own test job: False
  - input `alignment_stats_mode`: kept from run's own test job: 'with_reference'
  - input `fast_collate`: kept from run's own test job: False
  - input `reads_in_memory`: kept from run's own test job: 100000
  - input `reference_fasta`: fasta (nf-core --fasta genome.fasta)
  - input `reference_fai`: fasta (nf-core --fasta genome.fasta)
  - input `multiqc_title`: kept from run's own test job: ''
  - input `multiqc_logo`: unset (workflow default None)
  - input `reference_mode`: kept from run's own test job: 'build_fai'
- nf-core reference vs its own nf-test snapshot (`<scratch>/nfcore-ref/src/tests/chr.nf.test.snap`): 6/6 md5 entries match
- failed jobs (from planemo.log): `❌ Failed job f9dad470e67b07cb: Exit code: 3`

No data comparison: planemo downloaded no outputs (invocation failed).

