import os
import shutil
import subprocess
import tempfile
import zipfile

import gradio as gr
from git import Repo


def analyze_and_compile(repo_url):
    # Create temp workspace
    work_dir = tempfile.mkdtemp()
    repo_dir = os.path.join(work_dir, 'repo')
    output_dir = os.path.join(work_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Clone the GitHub repository
        Repo.clone_from(repo_url, repo_dir)

        # Simple static analysis: detect project type
        if os.path.exists(os.path.join(repo_dir, 'Cargo.toml')):
            project_type = 'rust'
        elif any(fname.endswith(('.c', '.cpp', '.h', '.hpp')) for root, _, files in os.walk(repo_dir) for fname in files):
            project_type = 'cpp'
        else:
            return "Unsupported project type: only Rust (Cargo.toml) or C/C++ repos supported"

        wasm_file = None
        if project_type == 'rust':
            # Compile Rust to WASM
            build_cmd = ['cargo', 'build', '--release', '--target', 'wasm32-unknown-unknown']
            subprocess.check_call(build_cmd, cwd=repo_dir)
            # Locate .wasm in target directory
            target_dir = os.path.join(repo_dir, 'target', 'wasm32-unknown-unknown', 'release')
            for f in os.listdir(target_dir):
                if f.endswith('.wasm'):
                    wasm_file = os.path.join(target_dir, f)
                    break
        else:
            # Compile C/C++ to WASM with Emscripten
            src_files = []
            for root, _, files in os.walk(repo_dir):
                for f in files:
                    if f.endswith(('.c', '.cpp')):
                        src_files.append(os.path.join(root, f))
            if not src_files:
                return "No C/C++ source files found."
            wasm_path = os.path.join(output_dir, 'a.wasm')
            emcc_cmd = ['emcc'] + src_files + ['-s', 'WASM=1', '-o', wasm_path]
            subprocess.check_call(emcc_cmd)
            wasm_file = wasm_path

        if not wasm_file or not os.path.exists(wasm_file):
            return "Compilation failed or WASM file not found."

        # Package WASM into zip
        zip_path = os.path.join(output_dir, 'wasm_package.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(wasm_file, arcname=os.path.basename(wasm_file))

        return zip_path

    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        # Cleanup cloned repo but keep output
        shutil.rmtree(repo_dir, ignore_errors=True)


def build_ui():
    with gr.Blocks() as demo:
        gr.Markdown("# GitHub-to-WASM Compiler")
        repo_input = gr.Textbox(label="GitHub Repository URL", placeholder="https://github.com/user/repo.git")
        output = gr.File(label="Download WASM Package")
        compile_btn = gr.Button("Compile to WASM")
        compile_btn.click(fn=analyze_and_compile, inputs=repo_input, outputs=output)
    return demo


demo = build_ui()
if __name__ == "__main__":
    demo.launch()