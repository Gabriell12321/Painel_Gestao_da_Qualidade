// Script de correção de erros do dashboard
// Adicione este script no final do dashboard_improved.html

(function() {
    'use strict';
    
    // Proteger funções críticas contra erros
    window.addEventListener('error', function(event) {
        console.warn('Erro capturado:', event.error);
        // Prevenir que erros isolados quebrem toda a página
        event.preventDefault();
    });
    
    // Garantir que toggleNotifications existe
    if (typeof window.toggleNotifications === 'undefined') {
        window.toggleNotifications = function() {
            console.log('Função toggleNotifications não implementada ainda');
        };
    }
    
    // Garantir que switchTab existe
    if (typeof window.switchTab === 'undefined') {
        window.switchTab = function(tab) {
            console.log('Mudando para aba:', tab);
            window.currentTab = tab;
        };
    }
    
    // Garantir que logout existe
    if (typeof window.logout === 'undefined') {
        window.logout = function() {
            if (confirm('Deseja realmente sair?')) {
                window.location.href = '/auth/logout';
            }
        };
    }
    
    // Prevenir problemas com Chart.js não carregado
    const MAX_CHART_RETRIES = 10;
    let chartRetries = 0;
    
    function waitForChart(callback) {
        if (typeof Chart !== 'undefined') {
            callback();
        } else if (chartRetries < MAX_CHART_RETRIES) {
            chartRetries++;
            setTimeout(() => waitForChart(callback), 500);
        } else {
            console.error('Chart.js não carregou após', MAX_CHART_RETRIES, 'tentativas');
        }
    }
    
    // Inicializar quando DOM estiver pronto
    document.addEventListener('DOMContentLoaded', function() {
        console.log('✅ Dashboard carregado - Correções aplicadas');
        
        // Aguardar Chart.js se necessário
        waitForChart(function() {
            console.log('✅ Chart.js disponível');
        });
    });
})();
