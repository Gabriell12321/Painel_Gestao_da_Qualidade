// Script para corrigir problemas nos gráficos
console.log('=== CORREÇÃO DOS GRÁFICOS RNC ===');

// Verificar se Chart.js está disponível
if (typeof Chart === 'undefined') {
    console.error('❌ Chart.js não está carregado! Carregando...');
    
    // Carregar Chart.js dinamicamente
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    script.onload = function() {
        console.log('✅ Chart.js carregado dinamicamente');
        initializeCharts();
    };
    document.head.appendChild(script);
} else {
    console.log('✅ Chart.js já está carregado');
    initializeCharts();
}

function initializeCharts() {
    // Verificar se as funções existem
    if (typeof window.loadSetorData !== 'function') {
        console.warn('⚠️ Função loadSetorData não encontrada, recriando...');
        createLoadSetorDataFunction();
    }
    
    if (typeof window.buildSetorCharts !== 'function') {
        console.warn('⚠️ Função buildSetorCharts não encontrada, recriando...');
        createBuildSetorChartsFunction();
    }
    
    // Verificar elementos do DOM
    const setorSelect = document.getElementById('setorSelect');
    if (setorSelect) {
        console.log('✅ Seletor de setor encontrado');
        
        // Adicionar event listener se não existir
        if (!setorSelect.onchange) {
            setorSelect.onchange = function() {
                console.log('Setor selecionado:', this.value);
                if (this.value) {
                    loadSetorData();
                }
            };
        }
    } else {
        console.warn('⚠️ Seletor de setor não encontrado');
    }
}

function createLoadSetorDataFunction() {
    window.loadSetorData = async function() {
        const select = document.getElementById('setorSelect');
        const setor = select ? select.value : '';
        
        if (!setor) {
            console.log('Nenhum setor selecionado');
            return;
        }
        
        console.log('Carregando dados do setor:', setor);
        
        try {
            const response = await fetch(`/api/indicadores/setor?setor=${setor}`);
            const data = await response.json();
            
            if (data.success) {
                console.log('Dados carregados:', data);
                buildSetorCharts(data, setor);
            } else {
                console.error('Erro na API:', data.message);
            }
        } catch (error) {
            console.error('Erro ao carregar dados:', error);
        }
    };
}

function createBuildSetorChartsFunction() {
    window.buildSetorCharts = function(apiData, setor) {
        console.log('Construindo gráficos para setor:', setor);
        
        try {
            const monthlyData = apiData.monthly_trend || [];
            const months = monthlyData.map(m => m.month);
            const values = monthlyData.map(m => Number(m.count || 0));
            
            // Criar gráfico mensal
            const monthlyCtx = document.getElementById('setorMonthlyChart');
            if (monthlyCtx) {
                if (window.setorMonthlyChart) {
                    window.setorMonthlyChart.destroy();
                }
                
                window.setorMonthlyChart = new Chart(monthlyCtx, {
                    type: 'line',
                    data: {
                        labels: months,
                        datasets: [{
                            label: 'RNCs',
                            data: values,
                            borderColor: 'rgba(54, 162, 235, 1)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: true }
                        }
                    }
                });
                
                console.log('✅ Gráfico mensal criado');
            }
            
        } catch (error) {
            console.error('Erro ao construir gráficos:', error);
        }
    };
}

console.log('=== FIM DA CORREÇÃO ===');
