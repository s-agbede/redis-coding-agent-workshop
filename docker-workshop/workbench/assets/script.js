// Adapted from redis-developer/semantic-cache-routing-workshop at 276e491d2b4dcc4b4c5a24acca85d368502cbb91.


// State
let panelState = {};
let sidebarVisible = true;
let maximizedPanelId = null;

// Initialize the workbench
function init() {
  // Set title from config
  document.getElementById('title').textContent = config.title;
  document.title = config.title;

  // Initialize panel state from config
  config.panels.forEach(panel => {
    panelState[panel.id] = { visible: panel.visible !== false };
  });

  // Initialize sidebar visibility
  sidebarVisible = config.sidebar.visible !== false;

  // Build the UI
  buildPanels();
  buildMenu();
  setupMenuToggle();
  setupPanelMessageHandlers();
  setupResizers();
}

// Build panels from config
function buildPanels() {
  const main = document.getElementById('container');
  main.innerHTML = '';

  // Create once, even if initially hidden: detaching an iframe loses its session.
  if (config.sidebar) {
    const sidebarUrl = config.sidebar.path;
    const sidebar = document.createElement('aside');
    sidebar.id = 'sidebar';
    sidebar.className = 'panel';
    sidebar.innerHTML = `
      <div class="panel-header">
        <span class="panel-title">${config.sidebar.name}</span>
        <div class="panel-controls">
          <button class="panel-control-btn sidebar-refresh-btn" title="Refresh ${config.sidebar.name}">
            <i class="fa-solid fa-rotate-right"></i>
          </button>
          <a class="panel-control-btn" href="${sidebarUrl}" target="_blank" rel="noopener noreferrer" title="Open in new tab">
            <i class="fa-solid fa-arrow-up-right-from-square"></i>
          </a>
          <button class="panel-control-btn sidebar-hide-btn" title="Hide ${config.sidebar.name}">
            <i class="fa-solid fa-eye-slash"></i>
          </button>
          <button class="panel-control-btn maximize-btn" data-panel="${config.sidebar.id}" title="Expand ${config.sidebar.name}">
            <i class="fa-solid fa-expand"></i>
          </button>
        </div>
      </div>
      <div class="panel-content">
        <div class="panel-loading" data-url="${sidebarUrl}">
          <i class="fa-solid fa-spinner"></i>
          <span>Connecting...</span>
        </div>
        <iframe title="${config.sidebar.name}" name="${config.sidebar.id}"></iframe>
      </div>
    `;
    main.appendChild(sidebar);

    // Setup sidebar refresh button
    sidebar.querySelector('.sidebar-refresh-btn').addEventListener('click', () => {
      const loadingEl = sidebar.querySelector('.panel-loading');
      const iframe = sidebar.querySelector('iframe');
      if (iframe && loadingEl) {
        loadingEl.classList.remove('hidden');
        loadPanelWithRetry(loadingEl);
      }
    });

    // Setup sidebar hide button
    sidebar.querySelector('.sidebar-hide-btn').addEventListener('click', () => {
      toggleSidebarVisibility(false);
      buildMenu(); // Update menu checkbox
    });

    // Create vertical resizer
    const verticalResizer = document.createElement('div');
    verticalResizer.id = 'verticalResizer';
    verticalResizer.className = 'resizer resizer-vertical';
    verticalResizer.innerHTML = '<div class="resizer-handle"></div>';
    main.appendChild(verticalResizer);
  }

  // Create right stack
  const rightStack = document.createElement('div');
  rightStack.className = 'right-stack';
  rightStack.id = 'rightStack';
  main.appendChild(rightStack);

  // Create panels in right stack
  buildRightStack();
}

// Build the right stack panels (called once during init)
function buildRightStack() {
  const rightStack = document.getElementById('rightStack');

  // Create all panels (resizers are added dynamically based on visibility)
  config.panels.forEach((panel) => {
    // Create panel
    const panelUrl = panel.path;
    const section = document.createElement('section');
    section.id = `panel-${panel.id}`;
    section.className = 'panel';
    section.innerHTML = `
      <div class="panel-header">
        <span class="panel-title">${panel.name}</span>
        <div class="panel-controls">
          <button class="panel-control-btn refresh-btn" data-panel="${panel.id}" title="Refresh ${panel.name}">
            <i class="fa-solid fa-rotate-right"></i>
          </button>
          <a class="panel-control-btn" href="${panelUrl}" target="_blank" rel="noopener noreferrer" title="Open in new tab">
            <i class="fa-solid fa-arrow-up-right-from-square"></i>
          </a>
          <button class="panel-control-btn hide-btn" data-panel="${panel.id}" title="Hide ${panel.name}">
            <i class="fa-solid fa-eye-slash"></i>
          </button>
          <button class="panel-control-btn maximize-btn" data-panel="${panel.id}" title="Maximize">
            <i class="fa-solid fa-expand"></i>
          </button>
        </div>
      </div>
      <div class="panel-content">
        <div class="panel-loading" data-url="${panelUrl}">
          <i class="fa-solid fa-spinner"></i>
          <span>Connecting...</span>
        </div>
        <iframe title="${panel.name}" name="${panel.id}"></iframe>
      </div>
    `;
    rightStack.appendChild(section);
  });

  // Setup panel header buttons
  setupPanelHeaderButtons();
  // Setup resizers
  setupResizers();
  // Start checking for panel availability
  startPanelLoaders();
  // Apply initial visibility
  updatePanelVisibility();
}

// Layout changes never detach frames or assign their URLs.
function updatePanelVisibility() {
  const sidebar = document.getElementById('sidebar');
  const sidebarExpanded = maximizedPanelId === config.sidebar.id;
  sidebar.style.display = sidebarVisible && (!maximizedPanelId || sidebarExpanded) ? '' : 'none';
  sidebar.classList.toggle('maximized', sidebarExpanded);
  updateMaximizeButton(sidebar, config.sidebar.name, sidebarExpanded);
  const rightVisible = !sidebarExpanded && config.panels.some(panel => panelState[panel.id]?.visible);
  document.getElementById('rightStack').style.display = rightVisible ? '' : 'none';
  document.getElementById('verticalResizer').style.display = sidebarVisible && rightVisible && !maximizedPanelId ? '' : 'none';
  sidebar.classList.toggle('only-panel', !rightVisible);

  config.panels.forEach(panel => {
    const section = document.getElementById(`panel-${panel.id}`);
    const expanded = maximizedPanelId === panel.id;
    section.style.display = panelState[panel.id]?.visible && (!maximizedPanelId || expanded) ? '' : 'none';
    section.classList.toggle('maximized', expanded);
    updateMaximizeButton(section, panel.name, expanded);
    const checkbox = document.getElementById(`menu-${panel.id}`);
    if (checkbox) checkbox.checked = panelState[panel.id]?.visible;
  });
  const sidebarCheckbox = document.getElementById('menu-sidebar');
  if (sidebarCheckbox) sidebarCheckbox.checked = sidebarVisible;
  rebuildHorizontalResizers();
}

function updateMaximizeButton(section, name, expanded) {
  const button = section.querySelector('.maximize-btn');
  button.querySelector('i').className = `fa-solid ${expanded ? 'fa-compress' : 'fa-expand'}`;
  button.title = `${expanded ? 'Restore' : 'Expand'} ${name}`;
  button.setAttribute('aria-label', button.title);
  button.setAttribute('aria-pressed', String(expanded));
}

function toggleMaximize(panelId) {
  maximizedPanelId = maximizedPanelId === panelId ? null : panelId;
  updatePanelVisibility();
}

// Rebuild horizontal resizers to connect only visible adjacent panels
function rebuildHorizontalResizers() {
  const rightStack = document.getElementById('rightStack');
  if (!rightStack) return;

  // Remove all existing horizontal resizers
  rightStack.querySelectorAll('.resizer-horizontal').forEach(r => r.remove());

  // Don't add resizers if a panel is maximized
  if (maximizedPanelId) return;

  // Get visible panels in config order
  const visiblePanels = config.panels.filter(p => panelState[p.id]?.visible);

  // Insert resizers between adjacent visible panels
  for (let i = 1; i < visiblePanels.length; i++) {
    const abovePanel = visiblePanels[i - 1];
    const belowPanel = visiblePanels[i];

    const resizer = document.createElement('div');
    resizer.className = 'resizer resizer-horizontal';
    resizer.dataset.above = abovePanel.id;
    resizer.dataset.below = belowPanel.id;
    resizer.innerHTML = '<div class="resizer-handle"></div>';

    // Insert before the below panel
    const belowSection = document.getElementById(`panel-${belowPanel.id}`);
    if (belowSection) {
      rightStack.insertBefore(resizer, belowSection);
    }
  }

  // Re-setup resizer event handlers
  setupHorizontalResizers();
}

// A pending readiness check must never overwrite a newer file navigation.
function loadPanelWithRetry(loadingEl) {
  const iframe = loadingEl.parentElement.querySelector('iframe');
  const version = Number(loadingEl.dataset.loadVersion || 0) + 1;
  loadingEl.dataset.loadVersion = String(version);
  const tryLoad = async () => {
    try {
      let response = await fetch(loadingEl.dataset.url, { method: 'HEAD' });
      if (Number(loadingEl.dataset.loadVersion) !== version) return;
      // code-server serves its workbench with GET but rejects HEAD.
      if (response.status === 405) {
        response = await fetch(loadingEl.dataset.url, { method: 'GET' });
        await response.body?.cancel();
        if (Number(loadingEl.dataset.loadVersion) !== version) return;
      }
      // Nginx provides useful startup instructions at this exact preview route.
      const previewStartupPage = loadingEl.dataset.url === '/app/' && response.status === 503;
      if (!response.ok && !previewStartupPage) throw new Error(`Panel unavailable: ${response.status}`);
      iframe.src = loadingEl.dataset.url;
      loadingEl.classList.add('hidden');
    } catch (error) {
      if (Number(loadingEl.dataset.loadVersion) === version) setTimeout(tryLoad, 1000);
    }
  };
  tryLoad();
}

// Start loading all panels
function startPanelLoaders() {
  document.querySelectorAll('.panel-loading').forEach(loadingEl => {
    loadPanelWithRetry(loadingEl);
  });
}

// Build the hamburger menu
function buildMenu() {
  const menu = document.getElementById('panelMenu');
  menu.innerHTML = '';

  // Add sidebar to menu first
  const sidebarItem = document.createElement('div');
  sidebarItem.className = 'panel-menu-item';
  sidebarItem.innerHTML = `
    <input type="checkbox" id="menu-sidebar" ${sidebarVisible ? 'checked' : ''}>
    <label for="menu-sidebar">
      <i class="fa-solid ${config.sidebar.icon}"></i>
      ${config.sidebar.name}
    </label>
  `;
  menu.appendChild(sidebarItem);

  const sidebarCheckbox = sidebarItem.querySelector('input');
  sidebarCheckbox.addEventListener('change', () => {
    toggleSidebarVisibility(sidebarCheckbox.checked);
  });

  // Add separator
  const separator = document.createElement('div');
  separator.className = 'panel-menu-separator';
  menu.appendChild(separator);

  // Add right-side panels
  config.panels.forEach(panel => {
    const item = document.createElement('div');
    item.className = 'panel-menu-item';
    item.innerHTML = `
      <input type="checkbox" id="menu-${panel.id}" ${panelState[panel.id]?.visible ? 'checked' : ''}>
      <label for="menu-${panel.id}">
        <i class="fa-solid ${panel.icon}"></i>
        ${panel.name}
      </label>
    `;
    menu.appendChild(item);

    // Handle checkbox change
    const checkbox = item.querySelector('input');
    checkbox.addEventListener('change', () => {
      togglePanelVisibility(panel.id, checkbox.checked);
    });
  });
}

// Toggle sidebar visibility
function toggleSidebarVisibility(visible) {
  sidebarVisible = visible || !Object.values(panelState).some(panel => panel.visible);
  if (!visible && maximizedPanelId === config.sidebar.id) maximizedPanelId = null;
  updatePanelVisibility();
}

// Toggle menu visibility
function setupMenuToggle() {
  const menuButton = document.getElementById('menuButton');
  const menu = document.getElementById('panelMenu');

  menuButton.addEventListener('click', (e) => {
    e.stopPropagation();
    menu.classList.toggle('hidden');
    menuButton.setAttribute('aria-expanded', String(!menu.classList.contains('hidden')));
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      menu.classList.add('hidden');
      menuButton.setAttribute('aria-expanded', 'false');
      menuButton.focus();
    }
  });

  // Close menu when clicking outside
  document.addEventListener('click', (e) => {
    if (!menu.contains(e.target) && e.target !== menuButton) {
      menu.classList.add('hidden');
      menuButton.setAttribute('aria-expanded', 'false');
    }
  });
}

// Toggle panel visibility
function togglePanelVisibility(panelId, visible) {
  panelState[panelId].visible = visible;

  // If hiding the maximized panel, un-maximize it
  if (!visible && maximizedPanelId === panelId) {
    maximizedPanelId = null;
  }

  // Keep one right panel available when Instructions is hidden.
  const visibleCount = Object.values(panelState).filter(p => p.visible).length;
  if (visibleCount === 0 && !sidebarVisible) {
    panelState[panelId].visible = true;
    const checkbox = document.getElementById(`menu-${panelId}`);
    if (checkbox) checkbox.checked = true;
    return;
  }

  updatePanelVisibility();
}

// Setup panel header buttons (maximize, hide, refresh)
function setupPanelHeaderButtons() {
  document.querySelectorAll('.panel-control-btn').forEach(control => {
    control.setAttribute('aria-label', control.title);
    if (control.tagName === 'BUTTON') control.type = 'button';
  });
  // Refresh buttons
  document.querySelectorAll('.refresh-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const panelId = btn.dataset.panel;
      const section = document.getElementById(`panel-${panelId}`);
      const loadingEl = section?.querySelector('.panel-loading');
      const iframe = section?.querySelector('iframe');
      if (iframe && loadingEl) {
        loadingEl.classList.remove('hidden');
        loadPanelWithRetry(loadingEl);
      }
    });
  });

  // Maximize buttons
  document.querySelectorAll('.maximize-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const panelId = btn.dataset.panel;
      toggleMaximize(panelId);
    });
  });

  // Hide buttons
  document.querySelectorAll('.hide-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const panelId = btn.dataset.panel;
      togglePanelVisibility(panelId, false);
      buildMenu(); // Update menu checkboxes
    });
  });
}

// Pointer capture plus disabled iframe hit-testing keeps dragging across frames reliable.
function setupResizeHandle(resizer, orientation, measure, resize) {
  resizer.tabIndex = 0;
  resizer.setAttribute('role', 'separator');
  resizer.setAttribute('aria-orientation', orientation);
  resizer.setAttribute('aria-label', orientation === 'vertical' ? 'Resize Instructions' : 'Resize panels');
  resizer.onpointerdown = event => {
    if (event.button !== 0) return;
    event.preventDefault();
    const start = orientation === 'vertical' ? event.clientX : event.clientY;
    const initial = measure();
    const frames = [...document.querySelectorAll('iframe')];
    const previousEvents = frames.map(frame => frame.style.pointerEvents);
    frames.forEach(frame => { frame.style.pointerEvents = 'none'; });
    resizer.setPointerCapture(event.pointerId);
    resizer.onpointermove = move => resize(initial, (orientation === 'vertical' ? move.clientX : move.clientY) - start);
    const finish = () => {
      frames.forEach((frame, index) => { frame.style.pointerEvents = previousEvents[index]; });
      resizer.onpointermove = null;
      resizer.onpointerup = null;
      resizer.onpointercancel = null;
      resizer.onlostpointercapture = null;
    };
    resizer.onpointerup = finish;
    resizer.onpointercancel = finish;
    resizer.onlostpointercapture = finish;
  };
  resizer.onkeydown = event => {
    const directions = orientation === 'vertical' ? { ArrowLeft: -20, ArrowRight: 20 } : { ArrowUp: -20, ArrowDown: 20 };
    if (directions[event.key]) {
      event.preventDefault();
      resize(measure(), directions[event.key]);
    }
  };
}

function setupResizers() {
  const main = document.getElementById('container');
  const sidebar = document.getElementById('sidebar');
  const resizer = document.getElementById('verticalResizer');
  setupResizeHandle(resizer, 'vertical', () => sidebar.getBoundingClientRect().width, (width, delta) => {
    const percentage = Math.max(15, Math.min(70, (width + delta) / main.getBoundingClientRect().width * 100));
    sidebar.style.width = `${percentage}%`;
    resizer.setAttribute('aria-valuenow', String(Math.round(percentage)));
  });
  setupHorizontalResizers();
}

function setupHorizontalResizers() {
  document.querySelectorAll('.right-stack .resizer-horizontal').forEach(resizer => {
    const above = document.getElementById(`panel-${resizer.dataset.above}`);
    const below = document.getElementById(`panel-${resizer.dataset.below}`);
    setupResizeHandle(resizer, 'horizontal', () => ({
      above: above.getBoundingClientRect().height,
      below: below.getBoundingClientRect().height,
      aboveWeight: Number(above.dataset.weight || 1),
      belowWeight: Number(below.dataset.weight || 1)
    }), (sizes, delta) => {
      const total = sizes.above + sizes.below;
      const height = Math.max(80, Math.min(total - 80, sizes.above + delta));
      const totalWeight = sizes.aboveWeight + sizes.belowWeight;
      above.dataset.weight = String(height / total * totalWeight);
      below.dataset.weight = String((total - height) / total * totalWeight);
      above.style.flex = `${above.dataset.weight} 1 0px`;
      below.style.flex = `${below.dataset.weight} 1 0px`;
      resizer.setAttribute('aria-valuenow', String(Math.round(height / total * 100)));
    });
  });
}

// Only relative workspace paths are accepted; URL decoding happens once in URLSearchParams.
function validWorkspacePath(path) {
  return typeof path === 'string' && /^[a-zA-Z0-9_./ -]+$/.test(path)
    && path.split('/').every(segment => segment && segment !== '.' && segment !== '..');
}

function getWorkshopFileUrl(data, origin) {
  if (!data || typeof data !== 'object') return null;
  let path;
  let line = '1';
  let column = '1';
  if (data.type === 'open-workshop-file') {
    path = data.path;
  } else if (data.type === 'open-vscode-file' && typeof data.href === 'string') {
    let url;
    try { url = new URL(data.href, origin); } catch { return null; }
    if (url.origin !== origin || url.pathname !== '/vscode/' || url.username || url.password || url.hash) return null;
    if ([...url.searchParams.keys()].some(key => !['folder', 'goto'].includes(key))) return null;
    if (url.searchParams.getAll('goto').length !== 1 || url.searchParams.getAll('folder').length > 1) return null;
    if (url.searchParams.has('folder') && url.searchParams.get('folder') !== '/workspace') return null;
    const target = url.searchParams.get('goto');
    const match = /^\/workspace\/(.+?)(?::([1-9][0-9]*)(?::([1-9][0-9]*))?)?$/.exec(target);
    if (!match) return null;
    [, path, line = '1', column = '1'] = match;
  } else {
    return null;
  }
  if (!validWorkspacePath(path)) return null;
  // VS Code's web WorkspaceProvider reads an openFile payload, not a goto URL
  // parameter. Match its remote authority to the current code-server host.
  const file = new URL(`vscode-remote://${new URL(origin).host}/workspace/${path}:${line}:${column}`);
  const payload = [['openFile', file.href], ['gotoLineMode', 'true']];
  const query = new URLSearchParams({ folder: '/workspace', payload: JSON.stringify(payload) });
  return `/vscode/?${query}`;
}

function navigateCode(url) {
  if (!url) return;
  panelState.vscode.visible = true;
  maximizedPanelId = null;
  updatePanelVisibility();
  const panel = document.getElementById('panel-vscode');
  const frame = panel.querySelector('iframe');
  const loading = panel.querySelector('.panel-loading');
  loading.dataset.loadVersion = String(Number(loading.dataset.loadVersion || 0) + 1);
  loading.dataset.url = url;
  loading.classList.add('hidden');
  // Editor tab changes leave iframe.src unchanged, so every explicit link must
  // navigate. code-server restores buffers through its normal hot-exit lifecycle.
  frame.src = url;
}

function openWorkshopFile(path) {
  const origin = window.location.origin;
  navigateCode(getWorkshopFileUrl({ type: 'open-workshop-file', path }, origin)
    || getWorkshopFileUrl({ type: 'open-vscode-file', href: path }, origin));
}

function openVscodeFile(href) {
  navigateCode(getWorkshopFileUrl({ type: 'open-vscode-file', href }, window.location.origin));
}

// Keep existing Docsify chapter links available as a fallback to the guide.
function openDocsRoute(route) {
  if (typeof route !== 'string' || !/^#\/[a-zA-Z0-9_./-]*$/.test(route)) return;
  sidebarVisible = true;
  maximizedPanelId = null;
  updatePanelVisibility();
  const sidebar = document.getElementById('sidebar');
  const loading = sidebar.querySelector('.panel-loading');
  const frame = sidebar.querySelector('iframe');
  const url = `/docs/${route}`;
  loading.dataset.loadVersion = String(Number(loading.dataset.loadVersion || 0) + 1);
  loading.dataset.url = url;
  loading.classList.add('hidden');
  if (frame.src !== new URL(url, window.location.origin).href) frame.src = url;
}

function setupPanelMessageHandlers() {
  window.openWorkshopFile = openWorkshopFile;
  window.openWorkshopDocs = openDocsRoute;
  window.addEventListener('message', event => {
    const guide = document.getElementById('sidebar').querySelector('iframe');
    if (event.origin !== window.location.origin || event.source !== guide.contentWindow) return;
    if (event.data?.type === 'show-workshop-terminal') {
      panelState.terminal.visible = true;
      sidebarVisible = true;
      maximizedPanelId = null;
      updatePanelVisibility();
      buildMenu();
      return;
    }
    if (event.data?.type === 'open-docs-route') {
      openDocsRoute(event.data.route);
      return;
    }
    navigateCode(getWorkshopFileUrl(event.data, window.location.origin));
  });
}

// Initialize when DOM is ready
init();
