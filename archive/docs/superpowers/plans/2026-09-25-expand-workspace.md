# Expand workshop panels

**Goal:** Expand and restore instructions, code, terminal and app preview in both workshop phases; resize both workspace splits.

**Design:** Keep the existing Vue panels mounted and control their visibility from the Build view. One expanded panel fills the browser viewport. Restore returns to the previous split; Escape restores when focus is in the workshop document. Runtime tabs remain available when terminal or preview is expanded. Use shared, labelled Expand/Restore buttons and keyboard-accessible percentage dividers. No new dependencies or persistence changes.

**Implementation sequence:**

1. Add component integration tests for expansion, runtime switching, retained editor text and iframe identity. Add divider tests for pointer and keyboard interaction and bounds; run them before implementation.
2. Add typed PanelToggle and PanelDivider components. Wire Build and BuildPanel, using hidden panels rather than conditional mounting. Keep small-screen layouts usable.
3. Run frontend tests, strict type checking and production build. Verify actual desktop and mobile browser layouts, resizing, restoration and retained sessions.
4. Rebuild the local frontend container so the running workshop includes the controls. Keep the runtime container running.

No Git metadata is present in this workspace, so no commit or worktree is available.
