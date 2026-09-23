UV_PYTHON := 3.12
export UV_PYTHON

generate-requirements: uv.lock
	# Windows-only packages have no source distributions; omit them for the Linux container lock.
	uv export --locked --no-dev --no-emit-project --no-emit-package pywin32 --no-emit-package pywin32-ctypes --output-file=requirements.txt > /dev/null
	uv tool run --with='pip<25.1' --with='pip-tools==7.4.1' 'pybuild-deps' compile --quiet --no-header --generate-hashes --output-file=requirements-build.txt requirements.txt requirements-build.in

uv.lock: pyproject.toml
	uv sync
