# Test data

The local fixture copies (8 FASTQs, `genome.fa`, `genes.gtf`; ~64 MB) are not committed.
`galaxy-workflow.gxwf-tests.yml` fetches every fixture by URL from
[nf-core/test-datasets](https://github.com/nf-core/test-datasets/tree/atacseq), and
`../test-data-refs.json` lists each URL with its SHA-1.
