import re

metadata = {
    "1": """
                <div class="bg-gray-50 p-4 rounded-xl border border-gray-100 text-sm mb-4 space-y-2">
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">⏱️ Est. Time:</span><span>2-3 hours</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">💻 Software:</span><span>Web browser</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🎯 Criteria:</span><span>Understand the central dogma, sequencing types, and standard file formats.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">✅ Exit Assess:</span><span>Pass the orientation concepts quiz.</span></div>
                </div>
""",
    "2": """
                <div class="bg-gray-50 p-4 rounded-xl border border-gray-100 text-sm mb-4 space-y-2">
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">⏱️ Est. Time:</span><span>4-6 hours</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">💻 Software:</span><span>Terminal (Bash/Zsh)</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🎯 Criteria:</span><span>Fluency in navigating directories, piping commands, and text manipulation.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🛠️ Capstone:</span><span>Write a bash script to filter and summarize a GTF annotation file.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">✅ Exit Assess:</span><span>Script runs flawlessly on test data.</span></div>
                </div>
""",
    "3": """
                <div class="bg-gray-50 p-4 rounded-xl border border-gray-100 text-sm mb-4 space-y-2">
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">⏱️ Est. Time:</span><span>2 hours</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">💻 Software:</span><span>Miniconda / Mamba</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🎯 Criteria:</span><span>Can confidently create, export, and clone isolated tool environments.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🛠️ Capstone:</span><span>Deploy an exact environment from a provided YAML file.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">✅ Exit Assess:</span><span>Environment activates without dependency conflicts.</span></div>
                </div>
""",
    "4": """
                <div class="bg-gray-50 p-4 rounded-xl border border-gray-100 text-sm mb-4 space-y-2">
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">⏱️ Est. Time:</span><span>3-4 hours</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">💻 Software:</span><span>SSH Client, Slurm</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🎯 Criteria:</span><span>Ability to submit and monitor batch jobs using appropriate resource flags.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🛠️ Capstone:</span><span>Submit, monitor, debug, and document a multi-core Slurm job.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">✅ Exit Assess:</span><span>Job completes successfully with an exit code of 0.</span></div>
                </div>
""",
    "5": """
                <div class="bg-gray-50 p-4 rounded-xl border border-gray-100 text-sm mb-4 space-y-2">
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">⏱️ Est. Time:</span><span>5-8 hours</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">💻 Software:</span><span>Snakemake / Nextflow, Docker / Singularity</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🎯 Criteria:</span><span>Understand workflow DAGs and containerized tool execution.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🛠️ Capstone:</span><span>Build a containerized Snakemake or Nextflow workflow.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">✅ Exit Assess:</span><span>Pipeline runs end-to-end on test data.</span></div>
                </div>
""",
    "6": """
                <div class="bg-gray-50 p-4 rounded-xl border border-gray-100 text-sm mb-4 space-y-2">
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">⏱️ Est. Time:</span><span>10-15 hours</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">💻 Software:</span><span>R, Seurat v5, ggplot2</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🎯 Criteria:</span><span>Mastery of the standard Seurat workflow (QC to Differential Expression).</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🛠️ Capstone:</span><span>Analyze a public PBMC dataset from raw matrices to annotated UMAP.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">✅ Exit Assess:</span><span>Produce a biologically sound annotated UMAP and marker gene list.</span></div>
                </div>
""",
    "7": """
                <div class="bg-gray-50 p-4 rounded-xl border border-gray-100 text-sm mb-4 space-y-2">
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">⏱️ Est. Time:</span><span>15-20 hours</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">💻 Software:</span><span>R, Python, CellTypist, LIANA, inferCNV</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🎯 Criteria:</span><span>Ability to execute specialized multi-omic and receptor analyses.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🛠️ Capstone:</span><span>Deconvolute bulk RNA-seq using an scRNA-seq reference.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">✅ Exit Assess:</span><span>Accurate cell fraction estimation across patient samples.</span></div>
                </div>
""",
    "8": """
                <div class="bg-gray-50 p-4 rounded-xl border border-gray-100 text-sm mb-4 space-y-2">
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">⏱️ Est. Time:</span><span>10-12 hours</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">💻 Software:</span><span>Kraken2, Bracken, Prokka, BWA, GATK</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🎯 Criteria:</span><span>Identify variants in WES data and taxonomy in metagenomes.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🛠️ Capstone:</span><span>Run taxonomic profiling and assembly on a public dataset and explain quality limitations.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">✅ Exit Assess:</span><span>Accurate generation of a VCF file or taxonomy abundance table.</span></div>
                </div>
""",
    "9": """
                <div class="bg-gray-50 p-4 rounded-xl border border-gray-100 text-sm mb-4 space-y-2">
                    <div class="flex text-orange-600 mb-2 font-bold"><svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>Advanced: complete Stages 1–6 first</div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">⏱️ Est. Time:</span><span>20+ hours</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">💻 Software:</span><span>Squidpy, Giotto, LLM APIs</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🎯 Criteria:</span><span>Master spatial coordinates, neighborhood graphs, and agentic workflows.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">🛠️ Capstone:</span><span>Compare a spatial or AI-assisted annotation method with a conventional baseline.</span></div>
                    <div class="flex items-start gap-2"><span class="font-semibold w-32 shrink-0">✅ Exit Assess:</span><span>Document validation metrics demonstrating AI performance against manual annotation.</span></div>
                </div>
"""
}

with open('/home/nmabbasi/.gemini/antigravity/scratch/OmicsHub/start-here.html', 'r') as f:
    content = f.read()

# Loop through stages 1 to 9
for i in range(1, 10):
    stage_str = f'<!-- Stage {i} -->'

    # We want to insert the metadata right before <div class="flex flex-col gap-3 mt-4">
    # which follows the <p class="text-gray-600 mb-4"> description.

    # Find the stage block
    stage_idx = content.find(stage_str)
    if stage_idx == -1:
        continue

    insert_target = '<div class="flex flex-col gap-3 mt-4">'
    target_idx = content.find(insert_target, stage_idx)

    if target_idx != -1:
        # Check if we already injected (prevent duplicate runs)
        if "⏱️ Est. Time" not in content[stage_idx:target_idx]:
            content = content[:target_idx] + metadata[str(i)] + content[target_idx:]

with open('/home/nmabbasi/.gemini/antigravity/scratch/OmicsHub/start-here.html', 'w') as f:
    f.write(content)

print("Updated start-here.html with pedagogical metadata!")
