// topoSphereApp.js


function detectNBColorMode() {
    if (window.localStorage['netbox-color-mode'] === 'dark') {
        return('dark')
    } else {
        return('light')
    }
}

function setColorMode(colorMode) {
    if (colorMode === 'dark') {
        window.topoSphere.setTheme('network-blue-dark-mode');
    } else if (colorMode === 'light') {
        window.topoSphere.setTheme('network-blue');
    } else {
        console.warn(`Unsupported color mode: ${colorMode}`);
    }
}

function handleNBColorModeToggle() {
    const fromMode = detectNBColorMode();
    let toMode = 'dark';
    if (fromMode == 'dark') {
        toMode = 'light';
    }
    setColorMode(toMode);
}

function initNBColorModeToggle() {
    Array.from(document.getElementsByClassName('color-mode-toggle')).forEach(button => {
        button.addEventListener('click', handleNBColorModeToggle);
    })
}

function initTopoSphere(config) {
    // Create the topology visualization
    TopoSphere.create('topology-container', config)
    .then(instance => {
        window.topoSphere = instance;
        console.log('TopoSphere initialized and available as window.topoSphere');
    })
    .catch(error => console.error('Initialization failed:', error));
}

const topologyData = window.topologyData;
const initialLayout = window.initialLayout || 'forceDirected'; // 'layered' or 'forceDirected'

let themeName = 'network-blue';
if (detectNBColorMode() === 'dark') {
    themeName = 'network-blue-dark-mode';
}

const config = {
    data: topologyData,
    theme: themeName,
    layoutConfigAlgorithm: {
        layout: initialLayout,
        layered: {
            orientation: 'vertical', // 'horizontal' or 'vertical'
            order: 'ascending', // 'ascending' or 'descending'
            sortOrder: ['id'],
            maxNodeDistance: 10000,
            maxLayerDistance: 10000,
        },
        forceDirected: {
            iterations: 700,
            padding: 120,
        }
    },
};

// Initialize topoSphere
initTopoSphere(config);

// Initialize NB Color Mode Toggle handler
initNBColorModeToggle();
