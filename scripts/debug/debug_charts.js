// Script de debug para identificar problemas nos gráficos
console.log('=== DEBUG DOS GRÁFICOS RNC ===');

// Verificar se Chart.js está carregado
if (typeof Chart === 'undefined') {
    console.error('❌ Chart.js não está carregado!');
} else {
    console.log('✅ Chart.js carregado:', Chart.version);
}

// Verificar elementos do DOM
const elements = [
    'setorSelect',
    'setorChartsContainer', 
    'setorMonthlyChart',
    'setorAccumChart',
    'setorComparisonChart',
    'setorPieChart'
];

elements.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
        console.log(`✅ Elemento ${id} encontrado`);
    } else {
        console.warn(`⚠️ Elemento ${id} NÃO encontrado`);
    }
});

// Verificar funções JavaScript
const functions = [
    'loadSetorData',
    'buildSetorCharts', 
    'buildSetorMonthlyChart',
    'buildSetorAccumChart',
    'buildSetorComparisonChart',
    'buildSetorPieChart'
];

functions.forEach(funcName => {
    if (typeof window[funcName] === 'function') {
        console.log(`✅ Função ${funcName} disponível`);
    } else {
        console.warn(`⚠️ Função ${funcName} NÃO disponível`);
    }
});

// Testar criação de gráfico simples
function testSimpleChart() {
    console.log('🧪 Testando criação de gráfico simples...');
    
    const testCanvas = document.createElement('canvas');
    testCanvas.id = 'testCanvas';
    testCanvas.width = 400;
    testCanvas.height = 200;
    document.body.appendChild(testCanvas);
    
    try {
        const testChart = new Chart(testCanvas, {
            type: 'line',
            data: {
                labels: ['Jan', 'Fev', 'Mar'],
                datasets: [{
                    label: 'Teste',
                    data: [1, 2, 3],
                    borderColor: 'rgb(75, 192, 192)'
                }]
            }
        });
        
        console.log('✅ Gráfico de teste criado com sucesso');
        testChart.destroy();
        document.body.removeChild(testCanvas);
        
    } catch (error) {
        console.error('❌ Erro ao criar gráfico de teste:', error);
    }
}

// Executar teste
setTimeout(testSimpleChart, 1000);

// Verificar se há erros no console
window.addEventListener('error', function(e) {
    console.error('❌ Erro JavaScript capturado:', e.error);
});

console.log('=== FIM DO DEBUG ===');
