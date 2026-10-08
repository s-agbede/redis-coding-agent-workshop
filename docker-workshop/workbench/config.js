/**
 * Workshop Configuration
 *
 * Customize this file for your workshop. Add, remove, or modify panels
 * to match your workshop's needs.
 *
 * Sidebar fields:
 *   id      - Unique identifier for the sidebar
 *   name    - Display name shown in the panel header and menu
 *   path    - URL path to the service (e.g., '/docs/')
 *   icon    - Font Awesome icon class (e.g., 'fa-book')
 *
 * Panel fields:
 *   id      - Unique identifier for the panel
 *   name    - Display name shown in the panel header and menu
 *   path    - URL path to the service (e.g., '/vscode/')
 *   icon    - Font Awesome icon class (e.g., 'fa-code')
 *   visible - Whether the panel is visible by default (true/false)
 */

const config = {
  title: 'Build a Coding Agent',
  sidebar: {
    id: 'instructions',
    name: 'Instructions',
    path: '/guide/',
    icon: 'fa-book'
  },
  panels: [
    { id: 'vscode', name: 'Code', path: '/vscode/?folder=/workspace', icon: 'fa-code', visible: true },
    { id: 'terminal', name: 'Terminal', path: '/terminal/', icon: 'fa-terminal', visible: true },
    { id: 'app', name: 'App Preview', path: '/app/', icon: 'fa-rocket', visible: false }
  ]
};
