"""Execute every notebook in a fresh kernel without manual kernel installation."""
from pathlib import Path
import json
import os
import sys
import tempfile
import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="fraudgraph-kernel-") as directory:
    os.environ["IPYTHONDIR"] = str(Path(directory) / "ipython")
    os.environ["JUPYTER_RUNTIME_DIR"] = str(Path(directory) / "runtime")
    spec = Path(directory) / "fraudgraph"
    spec.mkdir()
    (spec / "kernel.json").write_text(json.dumps({
        "argv": [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "FraudGraph", "language": "python"}), encoding="utf-8")
    manager = KernelSpecManager(kernel_dirs=[directory])
    for path in sorted((root / "notebooks").glob("*.ipynb")):
        notebook = nbformat.read(path, as_version=4)
        client = NotebookClient(notebook, timeout=180, kernel_name="fraudgraph", resources={"metadata": {"path": str(root)}},
                                kernel_manager_class="jupyter_client.manager.KernelManager")
        client.create_kernel_manager()
        client.km.kernel_spec_manager = manager
        client.execute()
        nbformat.write(notebook, path)
        print(f"Executed {path.name}", flush=True)
