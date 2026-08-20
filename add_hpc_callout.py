import glob

hpc_files = [
    "2-HPC_Basic_Commands.html",
    "hpc-submission-part1.html"
]

callout_box = """
<div class="mt-10 p-6 bg-blue-50 border border-blue-200 rounded-xl" style="margin-bottom: 2rem;">
  <h3 class="text-xl font-bold text-blue-900 mb-2">Want to learn more about HPC?</h3>
  <p class="text-blue-800 mb-4">If you want to dive deeper into cluster computing, SLURM commands, and high-performance computing best practices, visit our dedicated HPC guide.</p>
  <a href="https://nmabbasi.github.io/HPC" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-2 px-6 py-3 bg-blue-700 text-white font-bold rounded-lg hover:bg-blue-800 transition-colors">Visit HPC Guide <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg></a>
</div>
"""

for filepath in hpc_files:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if already added
        if "nmabbasi.github.io/HPC" not in content or "Want to learn more about HPC" not in content:
            # Insert right before </article>
            content = content.replace('</article>', callout_box + '\n</article>')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {filepath}")
        else:
            print(f"Already updated {filepath}")
    except Exception as e:
        print(f"Failed {filepath}: {e}")
