import os

html_files = [
    "index.html", "monitor.html", "detail.html", 
    "route.html", "analytics.html", "alerts.html", "complaints.html"
]

labels = [
    "Dashboard", "Monitor", "Bin Detail", 
    "Route Optimizer", "Analytics", "Alerts", "Complaints Portal"
]

nav_html = """
<!-- INJECTED NAVIGATION HUB -->
<style>
  .floating-nav-hub {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(0,0,0,0.1);
    padding: 12px 24px;
    border-radius: 100px;
    z-index: 999999;
    display: flex;
    gap: 16px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    font-family: 'Inter', sans-serif;
  }
  .floating-nav-hub a {
    text-decoration: none;
    color: #0F172A;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;
    padding: 6px 12px;
    border-radius: 20px;
  }
  .floating-nav-hub a:hover {
    background: #0F6CBD;
    color: white;
  }
</style>
<div class="floating-nav-hub">
"""

for i in range(len(html_files)):
    nav_html += f'  <a href="{html_files[i]}">{labels[i]}</a>\n'

nav_html += "</div>\n<!-- END INJECTED NAVIGATION HUB -->\n"

public_dir = r"c:\Users\Shaurya Singh\Downloads\Frontend-waste-ai\public"

for file in html_files:
    file_path = os.path.join(public_dir, file)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Don't inject twice
        if "INJECTED NAVIGATION HUB" in content:
            continue
            
        # Inject right after <body> tag
        if "<body>" in content:
            updated_content = content.replace("<body>", f"<body>\n{nav_html}")
        elif "<body class=" in content:
            # find the end of the body tag
            body_idx = content.find("<body")
            bracket_idx = content.find(">", body_idx)
            updated_content = content[:bracket_idx+1] + f"\n{nav_html}" + content[bracket_idx+1:]
        else:
            updated_content = nav_html + content

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(updated_content)
        print(f"Injected nav into {file}")
