/**
 * Menu de Atalhos Flutuante
 * Controla abertura/fechamento do menu e interações
 */
document.addEventListener('DOMContentLoaded', function() {
  'use strict';

  const btnMenu = document.getElementById('btnMenuAtalhos');
  const overlay = document.getElementById('overlayMenuAtalhos');

  // Se os elementos não existirem (usuário não tem permissão), não executa nada
  if (!btnMenu || !overlay) {
    console.log('Menu atalhos: elementos não encontrados');
    return;
  }

  console.log('Menu atalhos: inicializado');

  // Toggle menu ao clicar no botão
  btnMenu.addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    console.log('Botão clicado');
    toggleMenu();
  });

  // Fechar menu ao clicar fora dele
  document.addEventListener('click', function(e) {
    // Só fecha se o menu estiver visível (show = true)
    if (!overlay.classList.contains('show')) {
      return;
    }
    
    // Se clicou fora do menu e fora do botão, fecha
    if (!overlay.contains(e.target) && !btnMenu.contains(e.target)) {
      closeMenu();
    }
  });

  // Fechar menu ao pressionar ESC
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && overlay.classList.contains('show')) {
      closeMenu();
    }
  });

  // Prevenir que cliques dentro do menu fechem ele
  overlay.addEventListener('click', function(e) {
    e.stopPropagation();
  });

  // Alterna entre abrir e fechar
  function toggleMenu() {
    if (overlay.classList.contains('d-none')) {
      openMenu();
    } else if (overlay.classList.contains('show')) {
      closeMenu();
    } else {
      openMenu();
    }
  }

  // Abre o menu
  function openMenu() {
    overlay.classList.remove('d-none');
    btnMenu.classList.add('active');
    
    // Delay pequeno para animação CSS funcionar
    setTimeout(function() {
      overlay.classList.add('show');
    }, 10);
  }

  // Fecha o menu
  function closeMenu() {
    overlay.classList.remove('show');
    btnMenu.classList.remove('active');
    
    // Espera animação CSS terminar antes de ocultar (d-none)
    setTimeout(function() {
      overlay.classList.add('d-none');
    }, 300); // Tempo igual à transição CSS (0.3s)
  }

});
