nextflow.enable.dsl = 2

// Параметры задают исходный файл и папку готовых результатов.
params.input = "${projectDir}/data/words.txt"
params.outdir = "${projectDir}/results"

// Первый шаг создает файл с текстом в верхнем регистре.
process UPPERCASE {
    publishDir params.outdir, mode: 'copy'

    input:
    path source_text

    output:
    path 'uppercase.txt'

    script:
    """
    LC_ALL=C tr '[:lower:]' '[:upper:]' < "${source_text}" > uppercase.txt
    """
}

// Второй шаг получает файл первого шага и считает строки.
process COUNT_LINES {
    publishDir params.outdir, mode: 'copy'

    input:
    path upper_text

    output:
    path 'summary.txt'

    script:
    """
    awk 'END { print "Количество строк: " NR }' "${upper_text}" > summary.txt
    """
}

// Каналы передают данные между шагами в заданном порядке.
workflow {
    source = Channel.fromPath(params.input, checkIfExists: true)
    upper = UPPERCASE(source)
    COUNT_LINES(upper)
}
