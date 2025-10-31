# dify_plugin_bocha_search_context

更新依赖

```bash
uv pip compile pyproject.toml -o bocha_search_context/requirements.txt
```

格式化

```bash
uv run black . -C -l 100 && uv run ruff check --fix
```

打包

```bash
uv run black . -C -l 100 && uv run ruff check --fix
uv pip compile pyproject.toml -o bocha_search_context/requirements.txt
mkdir -p difypkg
./dify-plugin-windows-amd64.exe plugin package bocha_search_context/ -o difypkg/web_search_context-0.2.0.difypkg
```