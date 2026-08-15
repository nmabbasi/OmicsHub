import os
import re

lessons_dir = "lessons"

# Template components
top_template = """

<div class="p-6 bg-blue-50 border border-blue-100 rounded-xl mb-8">
  <h4 class="text-lg font-bold text-blue-900 mb-2">Learning Objectives & Prerequisites</h4>
  <ul class="list-disc list-inside text-blue-800 space-y-1 mb-4">
    <li><strong>Prerequisites:</strong> Basic understanding of the Linux terminal and bioinformatics concepts. (See <a href="start-here.html" class="underline">Start Here</a>)</li>
    <li><strong>Objective:</strong> Master the core concepts and practical commands of this topic.</li>
    <li><strong>Expected Output:</strong> A reproducible workflow and a clear understanding of the methodology.</li>
  </ul>
</div>

"""

bottom_template = """

---

<div class="mt-10 p-8 bg-gray-50 border border-gray-200 rounded-xl">
  <h3 class="text-xl font-bold text-gray-900 mb-3">Knowledge Check & Next Steps</h3>
  <p class="text-gray-700 mb-4"><strong>Exercise:</strong> Try running the code examples on a small subset of your own data. Did you encounter any errors? Check your syntax and ensure your input files are correctly formatted.</p>
  <p class="text-gray-700"><strong>Next Step:</strong> Return to the <a href="start-here.html" class="text-blue-600 font-bold hover:underline">Start Here</a> curriculum to find the next logical tutorial in your learning path, or explore related topics in the <a href="index.html#tutorials" class="text-blue-600 hover:underline">Tutorial Library</a>.</p>
</div>
"""

for filename in os.listdir(lessons_dir):
    if filename.endswith(".md"):
        filepath = os.path.join(lessons_dir, filename)
        with open(filepath, "r") as f:
            content = f.read()
        
        # Check if already injected
        if "Learning Objectives & Prerequisites" in content:
            continue
            
        # The content has a YAML frontmatter starting and ending with ---
        # Find the second ---
        parts = content.split("---", 2)
        if len(parts) >= 3:
            # Reconstruct with top template right after frontmatter
            new_content = parts[0] + "---" + parts[1] + "---" + top_template + parts[2]
            
            # Append bottom template
            new_content += bottom_template
            
            with open(filepath, "w") as f:
                f.write(new_content)
            print(f"Injected templates into {filename}")
        else:
            print(f"Skipping {filename} due to unexpected formatting.")
