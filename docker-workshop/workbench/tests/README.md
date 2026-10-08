Run the dependency-free regression tests from the repository root:

```sh
node --test docker-workshop/workbench/tests/*.test.cjs
```

The tests execute the browser script in Node's VM with a small DOM boundary fixture. They exercise URL validation, message provenance, panel layout, and frame navigation without requiring code-server. Live iframe reloads, editor hot-exit buffer restoration, and pointer interaction still require a running Docker workbench/browser check.
