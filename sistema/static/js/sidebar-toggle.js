/**
 * SIDEBAR TOGGLE FUNCTIONALITY
 * 
 * Gerencia o comportamento de recolher/expandir o sidebar lateral
 * Mantém o estado persistente usando localStorage
 */

(function() {
  'use strict';

  // Constantes
  const STORAGE_KEY = 'sidebarCollapsed';
  const COLLAPSED_CLASS = 'collapsed';
  const BODY_COLLAPSED_CLASS = 'sidebar-collapsed';
  const SIDEBAR_SELECTOR = '.navbar-vertical';
  const TOGGLE_BTN_SELECTOR = '.sidebar-toggle-btn';
  const FLOATING_BTN_SELECTOR = '.sidebar-toggle-floating';

  /**
   * Alterna o estado do sidebar entre recolhido e expandido
   */
  function toggleSidebar() {
    const sidebar = document.querySelector(SIDEBAR_SELECTOR);
    const body = document.body;

    if (!sidebar) {
      console.warn('Sidebar não encontrado');
      return;
    }

    // Alterna as classes
    const isCollapsed = body.classList.toggle(BODY_COLLAPSED_CLASS);
    sidebar.classList.toggle(COLLAPSED_CLASS);

    // Salva o estado no localStorage
    try {
      localStorage.setItem(STORAGE_KEY, isCollapsed.toString());
    } catch (e) {
      console.error('Erro ao salvar estado do sidebar:', e);
    }

    // Dispara evento customizado para outros scripts que possam precisar reagir
    const event = new CustomEvent('sidebarToggle', {
      detail: { collapsed: isCollapsed }
    });
    document.dispatchEvent(event);
  }

  /**
   * Restaura o estado do sidebar ao carregar a página
   * Usa a classe pré-aplicada no HTML para evitar animação no carregamento
   */
  function restoreSidebarState() {
    try {
      const isCollapsed = localStorage.getItem(STORAGE_KEY) === 'true';
      const html = document.documentElement;
      
      if (isCollapsed) {
        const sidebar = document.querySelector(SIDEBAR_SELECTOR);
        const body = document.body;

        if (sidebar) {
          // Aplica as classes de collapsed
          body.classList.add(BODY_COLLAPSED_CLASS);
          sidebar.classList.add(COLLAPSED_CLASS);
          
          // Remove a classe temporária do HTML após aplicar as classes corretas
          // Usa setTimeout para garantir que aconteça após o render
          setTimeout(() => {
            html.classList.remove('sidebar-will-collapse');
          }, 50);
        }
      } else {
        // Se não está collapsed, remove a classe do HTML imediatamente
        html.classList.remove('sidebar-will-collapse');
      }
    } catch (e) {
      console.error('Erro ao restaurar estado do sidebar:', e);
    }
  }

  /**
   * Inicializa os event listeners
   */
  function initEventListeners() {
    // Botão dentro do sidebar
    const toggleBtn = document.querySelector(TOGGLE_BTN_SELECTOR);
    if (toggleBtn) {
      toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        toggleSidebar();
      });
    }

    // Botão flutuante (quando sidebar está escondido)
    const floatingBtn = document.querySelector(FLOATING_BTN_SELECTOR);
    if (floatingBtn) {
      floatingBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        toggleSidebar();
      });
    }

    // Atalho de teclado opcional: Ctrl + B para toggle
    document.addEventListener('keydown', function(e) {
      if (e.ctrlKey && e.key === 'b') {
        e.preventDefault();
        toggleSidebar();
      }
    });
  }

  /**
   * Inicialização principal
   */
  function init() {
    // Restaura o estado imediatamente se possível (antes do DOMContentLoaded)
    // para evitar flash visual
    if (document.readyState !== 'loading') {
      restoreSidebarState();
    }
    
    // Aguarda o DOM estar pronto para event listeners
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        restoreSidebarState();
        initEventListeners();
      });
    } else {
      // DOM já está pronto
      initEventListeners();
    }
  }

  // Inicializa o módulo
  init();

  // Exporta funções para o escopo global (caso necessário)
  window.sidebarToggle = {
    toggle: toggleSidebar,
    restore: restoreSidebarState
  };

})();
