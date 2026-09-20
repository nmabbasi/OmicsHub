"""
Expand thin tutorial pages with well-written explanatory prose sections.
Injects content BEFORE the Knowledge Check section.
No em dashes used anywhere. Uses short dashes or colons instead.
Target: every tutorial gets to 1,200+ visible prose words.
"""
import os
import re

REPO = "/home/nmabbasi/.gemini/antigravity-ide/scratch/OmicsHub"

# Each entry: filename -> dict with section title and full HTML prose block
EXPANSIONS = {

"spatial-transcriptomics-r-python.html": """
<section class="prose-expansion bg-white border-t border-gray-100 mt-10 pt-10 pb-4">
  <div class="max-w-3xl mx-auto px-2">
    <h2 class="text-2xl font-bold text-slate-900 mb-4">Why Spatial Context Changes Everything</h2>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Standard single-cell RNA sequencing dissolves tissue into a suspension of individual cells. You recover transcriptomic profiles for thousands of cells, but you lose the one thing that is often biologically decisive: where each cell sat in the original tissue. Spatial transcriptomics restores that coordinate information. Each spot or bead in a Visium slide, or each pixel in a MERFISH experiment, carries both a gene expression vector and a physical position on the tissue section.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      This matters enormously in cancer biology, neuroscience, and developmental biology. A macrophage sitting at the invasive front of a tumor behaves differently from a macrophage in the necrotic core, even if their bulk transcriptomes look similar. A neuron in layer II of the cortex expresses a different set of markers than a morphologically identical neuron in layer VI. Spatial methods let you ask which genes are enriched at tissue boundaries, which cell types co-localise with others, and whether a ligand-receptor interaction inferred from scRNA-seq data actually occurs between cells that are physically adjacent.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Choosing the Right Platform</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The two most common approaches in 2026 are capture-based methods like 10x Genomics Visium and imaging-based methods like MERFISH, seqFISH, and Xenium. Visium captures all polyadenylated RNA across the transcriptome, but each spot averages roughly 5 to 15 cells. MERFISH and Xenium measure a curated panel of a few hundred to a few thousand genes at single-cell or subcellular resolution. The choice depends on your question: if you want transcriptome-wide discovery, use Visium; if you want to resolve individual cells with a targeted panel, use an imaging platform.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      For Visium data, the standard analysis stack uses Seurat in R or Squidpy and Scanpy in Python. Both load the tissue image alongside the spot-by-gene count matrix, allowing you to overlay expression patterns directly onto the histological image. The key difference from scRNA-seq is that you must decide early whether to treat spots as pseudo-cells or to deconvolve them into constituent cell types using a reference single-cell atlas.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Deconvolution: Recovering Cell-Type Proportions from Spots</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Because each Visium spot contains multiple cells, spatially variable genes are not necessarily cell-type-specific genes. A gene may appear enriched in a particular region simply because that region contains more of a given cell type, not because that gene is upregulated in those cells. Tools like RCTD, Spotlight, and NNLS deconvolution use a reference single-cell dataset to estimate the mixture of cell types in each spot. The result is a proportion matrix: for each spot, you obtain an estimate of how much of the signal comes from each cell type.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Once you have cell-type proportions, you can ask spatially resolved questions: do T cells and tumour cells co-localise? Do fibroblasts cluster near the stromal boundary? Which regions are predominantly composed of which cell types? These questions are not answerable from single-cell data alone, and they are what make spatial transcriptomics genuinely complementary rather than redundant with scRNA-seq.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Common Pitfalls and How to Avoid Them</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      One frequent mistake is treating spatially variable genes as differentially expressed genes without accounting for spatial autocorrelation. Standard differential expression tests assume independence between observations; adjacent spots share signal because they share cells at their edges. Tools like SpatialDE and NNSVG test for spatial variability directly, using statistical models that account for this autocorrelation.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Another pitfall is neglecting tissue quality. RNA degrades rapidly after tissue removal, and sections with high background fluorescence or poor morphology will produce noisy data regardless of the analysis method. Always inspect the histological image alongside QC metrics before committing to a dataset. A saturated or compressed tissue section will introduce artefacts that no computational method can fully correct.
    </p>
    <div class="bg-blue-50 border border-blue-200 rounded-xl p-5 mt-6 mb-2">
      <p class="text-blue-900 font-semibold mb-2">When to Use Spatial Transcriptomics vs Standard scRNA-seq</p>
      <ul class="list-disc list-inside text-blue-800 space-y-1 text-sm">
        <li>Use spatial transcriptomics when tissue architecture is central to your hypothesis.</li>
        <li>Use scRNA-seq when you need transcriptome-wide profiling at true single-cell resolution with high cell numbers.</li>
        <li>Combine both when you want to annotate cell types from scRNA-seq and then map them back onto tissue using spatial data.</li>
      </ul>
    </div>
  </div>
</section>
""",

"metagenomics-kraken2-bracken.html": """
<section class="prose-expansion bg-white border-t border-gray-100 mt-10 pt-10 pb-4">
  <div class="max-w-3xl mx-auto px-2">
    <h2 class="text-2xl font-bold text-slate-900 mb-4">Understanding Taxonomic Profiling at Scale</h2>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Shotgun metagenomic sequencing generates millions of short reads from every organism present in a sample. The central challenge is assigning each read to a taxon quickly and accurately enough to be useful at typical sequencing depths. Kraken2 solves this using exact k-mer matching against a prebuilt reference database. For each read, it queries every k-mer and records which taxon, or set of taxa, contains that k-mer in the database. The taxon with the most k-mer matches is assigned as the classification.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      This approach is extremely fast because the database lookup is essentially a hash table query. Kraken2 can classify hundreds of millions of reads per hour on a single node, which is roughly 10 to 100 times faster than alignment-based tools like Centrifuge or MetaPhlAn3 on large inputs. The trade-off is precision at the strain level: when two closely related strains share most of their k-mers, Kraken2 assigns reads to their lowest common ancestor rather than guessing a strain.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Why Bracken Is Necessary After Kraken2</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      A common misconception is that the read counts Kraken2 produces are already abundance estimates. They are not. Kraken2 reports how many reads were classified at each node in the taxonomic tree, including reads that could not be resolved below genus or family. A species in your sample may have very few reads reported at its own level because most of its reads were pulled up to the genus or even phylum level due to shared k-mers with relatives.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Bracken corrects for this by redistributing reads from higher-level nodes back down to species or genus level using a Bayesian model trained on the same database. For each node in the tree, Bracken estimates what fraction of reads that landed there should have been assigned to each child node, based on the expected read length and k-mer distribution. The result is a corrected abundance table where each species or genus has a realistic estimate of its relative contribution to the sample.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Database Choice Has a Larger Effect Than Most People Expect</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      One of the strongest determinants of classification accuracy is the reference database used. If an organism is not represented in the database, every read from it will be classified as unclassified. In gut microbiome samples, for example, unclassified reads can constitute 30 to 70 percent of the total depending on the database completeness. The standard Kraken2 database built from RefSeq may miss many gut-specific or environmental strains that have been sequenced more recently.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      For most projects, the recommended approach is to build a custom database that includes NCBI RefSeq bacteria, archaea, and viruses plus the human genome for host removal, supplemented with any domain-specific sequences relevant to your samples. Database construction is time-consuming and memory-intensive, but it is a one-time cost that pays off across many projects.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Interpreting Relative Abundance: What the Numbers Actually Mean</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Relative abundance data from Kraken2 and Bracken describe the composition of the sequenced library, not necessarily the true microbial community. DNA extraction efficiency, PCR amplification bias, read length, and library preparation all introduce systematic distortions. Two organisms present at equal true abundance may show a 10-fold difference in estimated abundance if their DNA extracts differently or if their GC content causes differential amplification.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      This means that relative abundance comparisons within a sample are more reliable than absolute abundance comparisons across samples, and that cross-study comparisons require careful normalisation and ideally a shared reference mock community. When reporting results, describe what your abundance estimates represent and acknowledge the key sources of technical variation in your sample preparation workflow.
    </p>
    <div class="bg-amber-50 border border-amber-200 rounded-xl p-5 mt-6 mb-2">
      <p class="text-amber-900 font-semibold mb-2">Key Decision Points Before Running Your Analysis</p>
      <ul class="list-disc list-inside text-amber-800 space-y-1 text-sm">
        <li>Select a database that covers the organisms you expect in your samples, not just the standard RefSeq set.</li>
        <li>Set the Bracken read length to match your actual read length after trimming, not the sequencer nominal read length.</li>
        <li>Report confidence thresholds used for classification; the default 0.1 may need adjustment for your sample type.</li>
        <li>Always inspect the fraction of unclassified reads before interpreting composition results.</li>
      </ul>
    </div>
  </div>
</section>
""",

"docker-singularity-bioinformatics.html": """
<section class="prose-expansion bg-white border-t border-gray-100 mt-10 pt-10 pb-4">
  <div class="max-w-3xl mx-auto px-2">
    <h2 class="text-2xl font-bold text-slate-900 mb-4">Why Containers Solve a Real Problem in Bioinformatics</h2>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Computational biology has a reproducibility problem that predates the current conversation about AI and large language models. A pipeline that worked on one machine in 2020 often fails to produce identical results on a different machine in 2026, even when the code is unchanged. The cause is almost always the software environment: a different version of STAR, a different Bioconductor release, or a different system library that a Python package links against.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Containers address this by packaging the entire runtime environment, including the operating system layer, system libraries, and all software dependencies, into a single portable image. When you run a container, you run the exact same environment regardless of whether the host machine is running Ubuntu 20.04, CentOS 7, or macOS Sonoma. This is the difference between sharing a Conda environment file (which specifies what to install but depends on what the package repository looks like at install time) and sharing a container image (which contains the already-installed software).
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Docker vs Singularity: Why HPC Clusters Reject Docker</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Docker requires a daemon process that runs as root. On a shared HPC cluster, this is a security violation: a user who can run Docker commands can trivially mount host directories as root, escape the container, and access other users' files or the cluster file system. For this reason, virtually all academic HPC clusters prohibit Docker entirely.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Singularity, developed specifically for HPC, solves this by using a different container format with no persistent daemon. Singularity containers run as the user who launches them, not as root, and they respect the file permission system of the host. Importantly, Singularity can pull and convert Docker images directly from Docker Hub or any container registry, which means you can build your pipeline image using Docker locally or in a CI system, push it to a registry, and then pull and run it on an HPC cluster using Singularity without any changes to the image itself.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Building Bioinformatics Containers That Will Last</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The most common mistake when writing a Dockerfile for a bioinformatics pipeline is using <code>apt-get install</code> or <code>conda install</code> without pinning specific versions. A Dockerfile that says <code>conda install -c bioconda star</code> will install whatever version of STAR was most recent when the image was built. Rebuild the image six months later and you may get a different version with different default parameters. Always specify exact version numbers for every tool in your Dockerfile.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      A second consideration is image size. A naive Bioconductor installation can easily exceed 10 gigabytes. This makes images slow to pull and expensive to store. Use multi-stage builds to separate the build environment from the runtime environment, and consider Alpine-based base images for tools that do not require a full Ubuntu installation. For R-heavy pipelines, the <code>rocker</code> family of images provides well-maintained, versioned R environments as a starting point.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Integrating Containers with Workflow Managers</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Containers reach their full potential when combined with a workflow manager like Nextflow or Snakemake. Both support per-rule or per-process container directives, which means each step of your pipeline can use a different container image. A STAR alignment step uses a container with STAR and samtools. A DESeq2 step uses a container with R and Bioconductor. If a tool requires an incompatible Python version from another tool in your pipeline, there is no conflict because each tool runs in its own isolated environment.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Nextflow's <code>-with-singularity</code> and <code>-with-docker</code> flags make this switching seamless: run with Docker locally for development, then run the identical pipeline on HPC with Singularity by changing one flag. No modifications to the pipeline logic are needed. This is the closest practical approximation to a truly portable, reproducible bioinformatics workflow.
    </p>
    <div class="bg-green-50 border border-green-200 rounded-xl p-5 mt-6 mb-2">
      <p class="text-green-900 font-semibold mb-2">Container Best Practices Summary</p>
      <ul class="list-disc list-inside text-green-800 space-y-1 text-sm">
        <li>Pin every tool version in your Dockerfile using exact version numbers.</li>
        <li>Push images to a versioned registry tag, never just latest.</li>
        <li>Use Singularity on HPC clusters; build with Docker locally.</li>
        <li>Store your Dockerfile in the same repository as your pipeline code.</li>
        <li>Test that the container produces expected outputs on a reference dataset before deploying to production.</li>
      </ul>
    </div>
  </div>
</section>
""",

"long-read-pacbio-nanopore.html": """
<section class="prose-expansion bg-white border-t border-gray-100 mt-10 pt-10 pb-4">
  <div class="max-w-3xl mx-auto px-2">
    <h2 class="text-2xl font-bold text-slate-900 mb-4">What Long Reads Reveal That Short Reads Cannot</h2>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Illumina short-read sequencing produces highly accurate reads of 150 to 300 base pairs. For most routine applications, including differential expression analysis, variant calling in coding regions, and standard metagenomic profiling, this is sufficient. However, certain biological questions are structurally impossible to answer with short reads, and these are precisely the questions where long-read platforms become essential.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The most significant limitation of short reads is their inability to resolve repetitive sequences and structural variants. The human genome contains roughly 50 percent repetitive sequence, including transposable elements, centromeric repeats, and segmental duplications. When a 150 bp read falls entirely within a repetitive region, it maps to multiple locations with equal probability, and the mapper either discards it or assigns it arbitrarily. Long reads of 10 to 50 kilobases span repetitive regions and anchor to unique flanking sequence on both ends, resolving the mapping problem entirely.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">PacBio HiFi vs Oxford Nanopore: The Trade-off in 2026</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      PacBio's HiFi reads, generated using circular consensus sequencing, achieve Illumina-level accuracy (Q30 or higher, meaning fewer than 1 error per 1,000 bases) at read lengths of 10 to 25 kilobases. They are the gold standard for applications where both read length and accuracy are required, such as diploid genome assembly, full-length isoform sequencing, and structural variant discovery with high confidence.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Oxford Nanopore sequencing produces reads that are longer on average (N50 of 20 to 100 kilobases depending on library preparation) but historically had higher raw error rates around 5 to 15 percent per read. Recent chemistry versions and the R10 pore have brought single-read accuracy to Q20 to Q25, which is sufficient for many applications when reads are present in sufficient depth. Nanopore's key advantages are real-time sequencing, the ability to detect base modifications (methylation, for example) directly from the electrical signal, and portability through the MinION device. PacBio's key advantages are higher per-read accuracy and better established computational tools for genome assembly.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Full-Length Transcript Sequencing: Resolving Isoform Complexity</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Alternative splicing affects the majority of multi-exon human genes. Short-read RNA-seq can detect which exons are present in a sample, but when a transcript has 10 exons and any 3 of them can be skipped independently, the number of possible isoforms is combinatorially large. Short reads cannot determine which combinations of exon skipping events co-occur in the same transcript molecule.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Long-read isoform sequencing, using PacBio Iso-Seq or Nanopore direct RNA-seq, sequences full-length transcripts from the poly-A tail to the 5-prime cap. Each read represents a single transcript molecule, making it straightforward to determine exactly which combination of exons was present in that molecule. Tools like FLAMES and IsoSeq3 cluster and error-correct the resulting reads to produce a high-confidence isoform catalogue. This approach has revealed thousands of novel isoforms in human tissues that were completely invisible to short-read RNA-seq.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Practical Considerations Before Committing to a Long-Read Experiment</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Long-read sequencing costs considerably more per base than short-read sequencing, and the sample preparation requirements are more stringent. DNA and RNA must be of high molecular weight, as fragmented nucleic acids produce short reads that undermine the key advantage of the platform. Extraction protocols designed for short-read sequencing typically involve vortexing or bead-milling steps that shear DNA to a few kilobases; these must be replaced with gentle extraction methods such as plug-based or magnetic-bead protocols.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Before designing a long-read experiment, clearly define what question cannot be answered with short reads. If you are doing standard differential expression analysis or SNP genotyping in well-characterised regions, short reads are less expensive and the tools are more mature. If you are assembling a new genome, resolving structural rearrangements in a cancer sample, or characterising the isoform repertoire of a tissue, long reads are justified and in many cases the only viable approach.
    </p>
  </div>
</section>
""",

"reproducible-workflows-snakemake-nextflow.html": """
<section class="prose-expansion bg-white border-t border-gray-100 mt-10 pt-10 pb-4">
  <div class="max-w-3xl mx-auto px-2">
    <h2 class="text-2xl font-bold text-slate-900 mb-4">Why Shell Scripts Are Not Enough</h2>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Almost every bioinformatics project begins with a shell script. You write a few lines to trim reads, align to a reference, and count features. The script works. You run it for your 10 samples and move on to analysis. Six months later, a collaborator sends you 40 new samples and asks you to run the same pipeline. You re-run your script, and it fails partway through because one sample has a different file naming convention, one step was already completed and the output files exist but are incomplete, and you cannot easily tell which samples finished successfully.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Workflow managers like Snakemake and Nextflow solve these problems by separating the description of the pipeline from the execution logic. You define rules or processes that specify inputs, outputs, and the command to run. The workflow manager handles dependency resolution, partial re-runs, job scheduling on HPC clusters, and parallel execution automatically. You never manually manage which samples need to be re-processed; the tool determines this by checking which output files exist and which are missing or out of date.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Snakemake: A Natural Fit for Python Users</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Snakemake is written in and extends Python. If you already write Python analysis scripts, the syntax for defining rules feels familiar. Each rule specifies an input function, an output file pattern, and a shell command or Python function. Snakemake resolves the order in which rules must run by working backwards from the target output files: it asks what files are needed to produce the final output, then what files are needed to produce those files, and so on, building a directed acyclic graph of jobs.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      One of Snakemake's practical advantages is its integration with Conda. You can specify a Conda environment file for each rule, and Snakemake will create and activate that environment automatically when the rule runs. This means your STAR alignment step uses a pinned STAR version and your DESeq2 step uses a pinned Bioconductor version, with no manual environment management required. Combined with the <code>--use-singularity</code> flag, you can run each rule inside its own container for maximum isolation.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Nextflow: Portability Across Compute Environments</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Nextflow uses a dataflow programming model where each process consumes from input channels and emits to output channels. This is conceptually different from Snakemake's file-based dependency graph. The practical consequence is that Nextflow pipelines are often more portable across compute environments: the same Nextflow script can run locally, on AWS Batch, on Google Cloud, on Azure, or on an HPC cluster with SLURM or PBS by changing a configuration profile. No changes to the pipeline logic are required.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The nf-core community has built a library of over 100 peer-reviewed, community-maintained Nextflow pipelines covering standard bioinformatics workflows including RNA-seq, ChIP-seq, methylation, metagenomics, and single-cell RNA-seq. Rather than building a pipeline from scratch, you can start with an nf-core pipeline and modify it for your specific use case. Each nf-core pipeline includes automated testing, documentation, and a consistent parameter interface, which significantly reduces the time from raw data to analysed results.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Which Tool Should You Choose?</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The choice between Snakemake and Nextflow often comes down to team familiarity and compute environment. If your team works primarily in Python and runs jobs on a single HPC cluster, Snakemake is easier to learn and deploy. If your team needs pipelines that run across multiple cloud providers or you want to leverage the nf-core ecosystem, Nextflow is the better investment. Both tools are actively maintained, well-documented, and widely used in the bioinformatics community.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The most important thing is to use either one consistently rather than maintaining a collection of shell scripts. Even a basic Snakemake workflow with three rules is more reproducible, more auditable, and easier to extend than a script that chains commands together in a single file. Start small, add rules as you add pipeline steps, and version control your workflow alongside your analysis code.
    </p>
  </div>
</section>
""",

"tcr-bcr-repertoire-analysis.html": """
<section class="prose-expansion bg-white border-t border-gray-100 mt-10 pt-10 pb-4">
  <div class="max-w-3xl mx-auto px-2">
    <h2 class="text-2xl font-bold text-slate-900 mb-4">The Biology Behind T Cell and B Cell Receptor Diversity</h2>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The adaptive immune system's ability to recognise virtually any antigen depends on the extraordinary diversity of T cell receptors and B cell receptors. This diversity is generated during lymphocyte development through V(D)J recombination, a somatic process in which gene segments are randomly joined with additional nucleotide insertions and deletions at the junctions. The result is that each lymphocyte carries a unique receptor sequence, and the total number of possible TCR or BCR sequences in a single individual exceeds 10 to the power of 15.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      In practice, the circulating repertoire of any individual contains between 10 million and 100 million distinct clonotypes, each representing a unique receptor sequence present on one or more cells. When an antigen is encountered, cells with receptors that bind that antigen proliferate through clonal expansion, producing a large population of identical cells from the same precursor. Repertoire analysis measures the frequency of each clonotype in a sample, allowing you to detect clonal expansion, track antigen-specific responses, and compare repertoire diversity across conditions or time points.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Sequencing Strategies: Bulk vs Single-Cell</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Bulk repertoire sequencing using targeted amplification of V(D)J gene segments provides deep coverage of clonotype frequencies at relatively low cost per sample. Tools like MiXCR, TRUST4, and VDJtools assemble clonotypes from bulk reads and estimate their frequencies. The limitation is that you cannot link a TCR sequence to a cell's full transcriptome or to a BCR sequence in the same cell.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Single-cell V(D)J sequencing, available through the 10x Genomics Chromium platform and others, sequences the full receptor chain sequences from individual cells alongside their whole-transcriptome gene expression profiles. This allows you to ask which transcriptional states are enriched in expanded clones, whether clonally related cells have diverged in their transcriptional programs, and whether paired heavy and light chain sequences or paired alpha and beta chain sequences share features across related clones. The cost is much higher per cell than bulk sequencing, and the clonotype depth is lower, but the paired information is unique.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Diversity Metrics: What They Measure and What They Do Not</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Repertoire diversity is typically summarised using metrics borrowed from ecology, including Shannon entropy, Simpson's index, and the Chao1 estimator. Shannon entropy captures both richness (number of distinct clonotypes) and evenness (how uniformly they are distributed). A sample dominated by one or two expanded clones will have low Shannon entropy even if the total number of distinct clonotypes is large. This is the expected pattern in a strong antigen-specific response.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      A critical technical consideration is sequencing depth. Diversity estimates from shallow sequencing are strongly influenced by sampling artefacts: rare clonotypes that are present in the repertoire may simply not be sequenced, leading to underestimated richness. Rarefaction, which involves subsampling all samples to the same number of reads before calculating diversity metrics, is mandatory for fair comparisons across samples with different sequencing depths. Never compare Shannon entropy values calculated from samples with 10-fold differences in read depth without rarefaction.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Clonotype Tracking Across Time Points and Tissues</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      One of the most powerful applications of repertoire analysis is tracking the same clonotype across multiple time points or tissue compartments. In cancer immunology, you can compare the TCR repertoire in tumour-infiltrating lymphocytes to the peripheral blood to determine whether tumour-specific clones are present in the blood at detectable frequencies. In infectious disease, you can track how the repertoire changes before, during, and after pathogen clearance to identify clones that expand and then contract after resolution.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Clonotype matching across samples requires careful consideration of the matching criteria. Two sequences are considered the same clonotype if their CDR3 amino acid sequences, V gene usage, and J gene usage all match. Matching on nucleotide sequence is more stringent and identifies cells from the same precursor with certainty. Matching on amino acid sequence is more permissive and groups functionally similar but independently arising clonotypes. Your choice should depend on whether you want to track identical cells or functionally convergent responses.
    </p>
  </div>
</section>
""",

"phylogenomics-orthofinder.html": """
<section class="prose-expansion bg-white border-t border-gray-100 mt-10 pt-10 pb-4">
  <div class="max-w-3xl mx-auto px-2">
    <h2 class="text-2xl font-bold text-slate-900 mb-4">From Genomes to Phylogenies: A Conceptual Foundation</h2>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Traditional molecular phylogenetics inferred evolutionary relationships from one or a handful of genes. Phylogenomics scales this approach to entire genomes, using hundreds or thousands of conserved genes simultaneously to produce highly resolved phylogenetic trees with narrow confidence intervals. The core analytical challenge is not the tree-building itself but the gene selection and alignment: you must identify genes that are present in exactly one copy across all the species you are comparing, that have been evolving under broadly similar selective pressures, and whose sequences can be aligned reliably.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Genes that fail these criteria introduce noise or bias into the analysis. Genes that have been duplicated independently in different lineages (paralogs) will produce trees that reflect gene family history rather than species history. Genes under strong positive selection evolve rapidly in specific lineages, which can mislead tree reconstruction. Genes with regions that are unalignable due to insertions or deletions produce alignment columns of uncertain homology, which are better excluded than forced into an alignment.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">OrthoFinder: Identifying Orthologous Groups at Scale</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      OrthoFinder identifies orthologs and orthogroups across any number of input proteomes using an all-versus-all DIAMOND search followed by a graph-based clustering step. Orthogroups are groups of genes descended from a single gene in the last common ancestor of the input species. Within an orthogroup, each species may have one or more genes depending on whether duplications occurred after speciation.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The key advantage of OrthoFinder over simpler reciprocal best-hit approaches is that it uses species tree-aware orthogroup inference. Rather than comparing genes from one species to another in isolation, OrthoFinder uses a reference species tree to distinguish true orthologs (which diverged due to speciation events) from co-orthologs (which diverged due to duplication events that preceded speciation). This distinction matters greatly for functional inference: orthologs tend to share conserved function across species, while paralogs may have diverged functionally.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Selecting Markers for Tree Construction</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      After running OrthoFinder, you have a set of orthogroups. For phylogenomic tree construction, you select single-copy orthogroups, which are orthogroups where each input species contributes exactly one gene. These single-copy orthologs are the least problematic for phylogenomics because there is no ambiguity about which sequence from each species should be aligned to which. Tools like BUSCO independently assess genome or proteome completeness using a similar set of single-copy orthologs, and the overlap between OrthoFinder results and BUSCO sets provides a useful sanity check.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      A practical consideration is the number of single-copy orthologs shared across all input species. If you include a highly reduced parasite genome alongside free-living species with much larger proteomes, the number of universally single-copy genes will be small. You may need to relax the inclusion criterion from all species to a supermajority of species, accepting that some positions in the final supermatrix will be missing for certain species.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Concatenation vs Coalescence: Two Philosophies of Tree Building</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Once you have aligned your single-copy orthologs, you face a choice: should you concatenate all the alignments into a single supermatrix and build one tree, or should you build a separate tree for each gene and then summarise across those gene trees? Concatenation is computationally simpler and assumes that all genes in your supermatrix share the same evolutionary history. This assumption is violated when incomplete lineage sorting (ILS) is common, which happens when speciation events were rapid and the ancestral populations were large.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Coalescence-based methods like ASTRAL address ILS by inferring the species tree as the tree that maximises the number of gene trees that agree with it under the multi-species coalescent model. They are statistically more consistent in the presence of ILS but require a large number of informative gene trees and can be sensitive to gene tree estimation error. In practice, comparing the concatenation tree to the ASTRAL species tree for your dataset is a useful diagnostic: strong disagreements between the two suggest that ILS or other gene tree discordance is a significant factor in your data.
    </p>
  </div>
</section>
""",

"single-cell-deconvolution.html": """
<section class="prose-expansion bg-white border-t border-gray-100 mt-10 pt-10 pb-4">
  <div class="max-w-3xl mx-auto px-2">
    <h2 class="text-2xl font-bold text-slate-900 mb-4">What Deconvolution Is and Why It Matters</h2>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Bulk RNA sequencing measures the average gene expression across all cells in a sample. If your tumour sample contains 60 percent cancer cells, 20 percent T cells, and 20 percent fibroblasts, your bulk RNA-seq profile is a weighted average of the gene expression profiles of those three populations. A gene that is highly expressed in T cells but not in cancer cells will appear at moderate expression in the bulk profile, and without additional information you cannot distinguish this from a gene that is expressed at moderate levels in every cell.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Deconvolution attempts to reverse this mixing process, estimating the cellular composition of a bulk sample using a reference that specifies the gene expression signature of each cell type. The input is the bulk expression matrix and the reference signature matrix; the output is a proportion estimate for each cell type in each sample. This allows you to ask questions that bulk RNA-seq cannot answer on its own: does the fraction of cytotoxic T cells correlate with treatment response? Is the tumour macrophage proportion associated with prognosis?
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Reference-Based vs Reference-Free Deconvolution</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Reference-based methods like CIBERSORT, MuSiC, and DWLS require a signature matrix that specifies the expected expression of each marker gene in each cell type. This signature matrix can come from a published reference built from isolated cell populations, or from your own single-cell RNA-seq data from the same tissue type. The quality of the deconvolution result depends heavily on the quality and relevance of the signature matrix. A signature built from peripheral blood mononuclear cells will perform poorly when applied to tumour-infiltrating lymphocytes, which can have very different transcriptional states from their circulating counterparts.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Reference-free methods like NMF-based approaches do not require a pre-specified signature and instead learn the cell-type components directly from the data. They are useful when no appropriate reference exists, but the learned components are not labelled and must be interpreted post-hoc by examining which marker genes load strongly onto each component. This adds an interpretation step that can be subjective and requires domain knowledge.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Using Single-Cell Data as a Deconvolution Reference</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The most principled approach in 2026 is to use single-cell RNA-seq data from the same tissue type as your deconvolution reference. Tools like MuSiC and SCDC can estimate cell-type proportions in bulk samples using a matched or closely related single-cell atlas as the reference. The single-cell data provides both the cell type labels and the per-cell-type expression profiles needed to build the signature matrix.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      A critical practical consideration is that the single-cell reference should capture the same cellular states present in your bulk samples. If your bulk samples are from a disease condition and your single-cell reference was generated from healthy tissue, the disease-specific transcriptional states of infiltrating immune cells may not be well represented in the reference. In this situation, the deconvolution will estimate proportions that reflect the closest healthy cell type, potentially misclassifying activated or exhausted cells.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Validating Deconvolution Results</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Deconvolution estimates should always be validated against an independent measurement where possible. Flow cytometry data from the same samples is the gold standard for immune cell proportions. If flow cytometry data is available for a subset of your samples, correlating the deconvolution estimates against the flow cytometry proportions for the same cell types tells you how accurate the deconvolution is in your specific data context. Correlation coefficients of 0.7 or higher between deconvolution estimates and flow cytometry across samples are generally considered acceptable.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      When independent validation data is unavailable, assess internal consistency: do the estimated proportions sum to approximately one across cell types? Do biologically expected correlations hold, such as a negative correlation between tumour cell fraction and immune cell fraction? Do samples that are clinically annotated as T-cell-rich show high T cell deconvolution estimates? These sanity checks do not confirm accuracy but can detect gross failures of the deconvolution model.
    </p>
  </div>
</section>
""",

"16s-rrna-prokka-annotation.html": """
<section class="prose-expansion bg-white border-t border-gray-100 mt-10 pt-10 pb-4">
  <div class="max-w-3xl mx-auto px-2">
    <h2 class="text-2xl font-bold text-slate-900 mb-4">16S rRNA Sequencing: Surveying Microbial Communities Without Culturing</h2>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The 16S ribosomal RNA gene is present in all bacteria and archaea and contains nine hypervariable regions (V1 through V9) that differ enough between taxa to serve as taxonomic barcodes, interspersed with conserved regions that allow universal PCR amplification. By amplifying and sequencing one or more of these hypervariable regions from environmental DNA, you can survey the taxonomic composition of a microbial community without needing to culture any of its members.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The practical importance of this cannot be overstated. The vast majority of environmental bacteria, estimated at over 99 percent in many habitats, cannot be cultivated under standard laboratory conditions. Before the development of 16S amplicon sequencing, microbial ecology was largely limited to what could be grown on plates. Amplicon sequencing opened access to the uncultured majority and revealed that gut, soil, ocean, and other microbial communities are dominated by taxa entirely absent from culture collections.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Amplicon Sequence Variants vs Operational Taxonomic Units</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Historically, 16S reads were clustered at 97 percent sequence identity to form operational taxonomic units (OTUs), which roughly correspond to the species level. This threshold was chosen for practical reasons rather than biological ones, and the 97 percent boundary does not correspond to any consistent biological species definition.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Modern analysis pipelines now favour amplicon sequence variants (ASVs), generated by tools like DADA2 and Deblur. ASVs represent exact biological sequences after error correction, with each unique sequence treated as a distinct variant rather than clustered with similar sequences. ASVs offer several advantages: they are reproducible across studies (the same ASV sequence always represents the same biological variant), they have higher resolution than OTUs (two sequences that differ by one base are distinct ASVs), and they can be compared directly across datasets without re-clustering. The trade-off is that ASVs that differ by a single sequencing error are treated as different biological sequences until collapsed by error correction, which makes the quality of error correction critical.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Prokka for Whole-Genome Annotation</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Prokka is a rapid whole-genome annotation tool designed for prokaryotic genomes. Given an assembled genome (in FASTA format), Prokka predicts protein-coding genes using Prodigal, rRNA genes using Barrnap, tRNA genes using Aragorn, and signal peptides using SignalP. It then annotates predicted proteins by searching against a hierarchical set of databases, starting with species-specific databases, then genus-level databases, then a curated database of trusted proteins, and finally the general UniProtKB/Swiss-Prot database.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Prokka is fast enough to annotate a typical bacterial genome (4 to 6 megabases) in a few minutes on a standard workstation, which makes it suitable for annotating hundreds of genomes in a comparative genomics project. The output files include a GFF3 annotation file compatible with most downstream tools, a GenBank format file, a FASTA file of annotated protein sequences, and summary statistics including gene counts by category.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">When to Use 16S Amplicon Sequencing vs Metagenomics</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The choice between 16S amplicon sequencing and shotgun metagenomics depends on your research question and budget. 16S is cheaper (roughly 5 to 10 times fewer reads needed per sample), produces taxonomic profiles that are straightforward to compare across samples, and has an enormous body of reference data for gut, oral, skin, and environmental communities. Its limitations are that it cannot distinguish closely related species that share identical 16S sequences in the amplified region, it cannot provide functional information (which genes are present and in what abundance), and amplification bias can distort community composition estimates.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      Shotgun metagenomics sequences all DNA in a sample without amplification, providing both taxonomic and functional profiles at much higher resolution. It can detect viruses and eukaryotes that lack 16S genes, and it avoids PCR amplification bias entirely. The trade-off is cost (roughly 10 times more expensive per sample for equivalent community resolution), more complex bioinformatics, and greater sensitivity to host DNA contamination, which must be removed computationally before microbial analysis.
    </p>
  </div>
</section>
""",

"advanced-ai-orchestration-bioinformatics.html": """
<section class="prose-expansion bg-white border-t border-gray-100 mt-10 pt-10 pb-4">
  <div class="max-w-3xl mx-auto px-2">
    <h2 class="text-2xl font-bold text-slate-900 mb-4">What AI Orchestration Means in a Research Context</h2>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The term AI orchestration in bioinformatics refers to coordinating multiple AI components, including large language models, specialised biological AI models, and automated tool use, in a structured pipeline that can plan, execute, and evaluate multi-step research tasks. Rather than asking a model a single question and interpreting the answer manually, an orchestrated system routes queries through several agents or models, each with a defined role, and aggregates the results into a coherent output.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      In practice, this can look like a system where a planning agent receives a high-level research question, decomposes it into sub-tasks, assigns each sub-task to a specialised agent (one for literature retrieval, one for database querying, one for code generation and execution), and then synthesises the results into a summary. The biology researcher interacts with the top-level system and receives integrated outputs without needing to manage each tool individually.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Concrete Use Cases in Genomics and Multi-Omics</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      One of the most useful current applications is variant interpretation. When a whole-exome sequencing analysis identifies a list of candidate variants, an orchestrated system can automatically query ClinVar for pathogenicity classifications, pull the associated literature from PubMed, retrieve population frequency from gnomAD, check protein domain databases for functional context, and generate a structured summary for each variant. What would take a researcher several hours of manual database querying takes the orchestrated system minutes.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      A second use case is iterative single-cell analysis. A human researcher defines a broad goal, for example identifying the transcriptional programs of tumour-associated macrophages in a dataset, and the orchestrated system proposes and executes a series of analytical steps, checking the output of each step before deciding on the next. When a clustering step produces an unexpected number of clusters, the system can adjust resolution parameters and re-run without human intervention. The researcher reviews the final output rather than managing every intermediate decision.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Tool Use and Retrieval Augmented Generation</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      A large language model used alone has fixed knowledge that stops at its training cutoff. In a rapidly evolving field like bioinformatics, this is a significant limitation: a model trained in 2024 does not know about tools, datasets, or methods published in 2025. Retrieval augmented generation (RAG) addresses this by connecting the model to an external knowledge base that is queried at inference time. The model generates a query, the retrieval system finds the most relevant documents, and the model generates its response conditioned on those documents.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      For bioinformatics, a well-designed RAG system might index your institution's preprint server, curated tool documentation, and your own project notes. When you ask the system to suggest an alignment tool for a specific organism and read type, it retrieves documentation for relevant tools, compares their stated capabilities, and generates a reasoned recommendation grounded in current tool documentation rather than training data that may be months or years out of date.
    </p>
    <h3 class="text-xl font-semibold text-slate-900 mb-3 mt-8">Limitations and Responsible Use</h3>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      AI orchestration systems can fail in non-obvious ways. A system that automates variant interpretation may produce a confidently worded summary of a benign variant as pathogenic if the retrieval step returns an outdated or incorrect document. A code generation agent may produce syntactically correct code that produces subtly wrong results due to a misunderstood parameter. These failures are particularly dangerous when the output looks plausible and the researcher does not verify intermediate results.
    </p>
    <p class="text-slate-700 text-base leading-relaxed mb-4">
      The practical rule for using AI orchestration in research is to treat it as an accelerator for exploratory analysis and literature review, not as a replacement for biological judgment and manual verification of results. Always inspect intermediate outputs, validate AI-generated code against expected behaviour on test data, and cross-check AI-summarised findings against the original sources before including them in a manuscript or clinical report.
    </p>
  </div>
</section>
""",

}

def inject_before_knowledge_check(html, new_section):
    """Inject new_section before the Knowledge Check heading."""
    # Try to find <h2 ... Knowledge Check
    pattern = r'(<h[23][^>]*>[^<]*Knowledge Check[^<]*</h[23]>)'
    match = re.search(pattern, html, re.IGNORECASE)
    if match:
        pos = match.start()
        return html[:pos] + new_section + "\n" + html[pos:]
    # Fallback: inject before the footer
    pattern2 = r'(<footer[^>]*>)'
    match2 = re.search(pattern2, html, re.IGNORECASE)
    if match2:
        pos = match2.start()
        return html[:pos] + new_section + "\n" + html[pos:]
    return html + new_section

changed = 0
for filename, section_html in EXPANSIONS.items():
    fpath = os.path.join(REPO, filename)
    if not os.path.exists(fpath):
        print(f"  NOT FOUND: {filename}")
        continue
    with open(fpath, "r", encoding="utf-8") as f:
        html = f.read()
    # Check if expansion already applied
    if "prose-expansion" in html:
        print(f"  Already expanded: {filename}")
        continue
    new_html = inject_before_knowledge_check(html, section_html)
    if new_html != html:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_html)
        changed += 1
        print(f"  Expanded: {filename}")
    else:
        print(f"  No insertion point found: {filename}")

print(f"\nDone. Expanded: {changed} files.")
