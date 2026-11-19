set -e
D=/d/github.com/nf-core/test-datasets/raw/bamtofastq/test-datasets/data/genomics/homo_sapiens/illumina/bam
for s in test test2; do I=$D/$s.paired_end.sorted.bam
samtools view -b -f1 -F12 $I -o $s.mm.bam; samtools view -b -f12 -F256 $I -o $s.uu.bam; samtools view -b -f4 -F264 $I -o $s.um.bam; samtools view -b -f8 -F260 $I -o $s.mu.bam
samtools merge --threads 1 $s.merged.bam $s.uu.bam $s.um.bam $s.mu.bam
for k in mm merged; do samtools collate --threads 1 -O $s.$k.bam . | samtools fastq -N --threads 1 -0 $s.$k.other.fq.gz -1 $s.$k.1.fq.gz -2 $s.$k.2.fq.gz -s $s.$k.single.fq.gz 2>/dev/null; done
cat $s.mm.1.fq.gz $s.merged.1.fq.gz > ${s}_1.merged.fastq.gz; cat $s.mm.2.fq.gz $s.merged.2.fq.gz > ${s}_2.merged.fastq.gz
samtools flagstat $I > $s.flagstat; samtools idxstats $I > $s.idxstats
done; md5sum *_?.merged.fastq.gz *.flagstat *.idxstats
