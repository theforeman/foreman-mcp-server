generate-requirements: uv.lock
	uv export --locked --format requirements.txt --output-file requirements-build.txt --group build --no-emit-project
