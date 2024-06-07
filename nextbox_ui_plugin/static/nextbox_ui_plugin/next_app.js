(function (nx) {
    /**
     * NeXt UI base application
     */

    // Calculate topology canvas size
    // based on window size during page loading.
    // Canvas size can only be set once during page init. 
    // It does not autoscale. Page reload is required to update topology dimensions.
    if (document.body.clientWidth && document.body.clientHeight) {
        var canvasWidth = document.body.clientWidth*0.75;
        var canvasHeight = document.body.clientHeight*0.75;
    } else {
        var canvasWidth = 850;
        var canvasHeight = 750;
    };

    // Initialize topology
    var topo = new nx.graphic.Topology({
        // View dimensions
        width: canvasWidth,
        height: canvasHeight,
        // Dataprocessor is responsible for spreading 
        // the Nodes across the view.
        // 'force' dataprocessor spreads the Nodes so
        // they would be as distant from each other
        // as possible. Follow social distancing and stay healthy.
        // 'quick' dataprocessor picks random positions
        // for the Nodes.
        dataProcessor: 'force',
        // Node and Link identity key attribute name
        identityKey: 'id',
        // Node settings
        nodeConfig: {
            label: 'model.name',
            iconType:'model.icon',
            color: function(model) {
                if (model._data.is_new === 'yes') {
                    return '#148D09'
                }
            },
        },
        // Node Set settings (for future use)
        nodeSetConfig: {
            label: 'model.name',
            iconType: 'model.iconType'
        },
        // Tooltip content settings
        tooltipManagerConfig: {
            nodeTooltipContentClass: 'CustomNodeTooltip',
            linkTooltipContentClass: 'CustomLinkTooltip'
        },
        // Link settings
        linkConfig: {
            // Display Links as curves in case of 
            //multiple links between Node Pairs.
            // Set to 'parallel' to use parallel links.
            linkType: 'curve',
            sourcelabel: 'model.srcIfName',
            targetlabel: 'model.tgtIfName',
            style: function(model) {
                if (model._data.is_dead === 'yes') {
                    return { 'stroke-dasharray': '5' }
                }
            },
            color: function(model) {
                if (model._data.is_dead === 'yes') {
                    return '#E40039'
                }
                if (model._data.is_new === 'yes') {
                    return '#148D09'
                }
            },
        },
        // Display Node icon. Displays a dot if set to 'false'.
        showIcon: true,
        linkInstanceClass: 'CustomLinkClass'
    });
    
    topo.registerIcon("dead_node", "/static/nextbox_ui_plugin/img/dead_node.png", 49, 49);
    
    var Shell = nx.define(nx.ui.Application, {
        methods: {
            getContainer: function() {
                return new nx.dom.Element(document.getElementById('nx-ui-topology'));
            },
            start: function () {
                // Read topology data from variable
                topo.data(topologyData);
                
                // set initial layer alignment direction
                if (topologyData["nodes"].length > 0 & (initialLayout == 'vertical' | initialLayout == 'horizontal')) {
                    var layout = topo.getLayout('hierarchicalLayout');
                    layout.direction(initialLayout);
                    layout.levelBy(function(node, model) {
                    return model.get('layerSortPreference');
                    });
                    topo.activateLayout('hierarchicalLayout');
                };
                // Attach it to the document
                topo.attach(this);
            }
        }
    });

    nx.define('CustomNodeTooltip', nx.ui.Component, {
        properties: {
            node: {},
            topology: {}
        },
        view: {
            content: [{
                tag: 'div',
                content: [{
                    tag: 'h5',
                    content: [{
                        tag: 'a',
                        content: '{#node.model.name}',
                        props: {"href": "{#node.model.dcimDeviceLink}", "target": "_blank", "rel": "noopener noreferrer"}
                    }],
                    props: {
                        "style": "border-bottom: dotted 1px; font-size:90%; word-wrap:normal; color:#003688"
                    }
                }, {
                    tag: 'p',
                    content: [
                        {
                        tag: 'label',
                        content: 'IP: ',
                    }, {
                        tag: 'label',
                        content: '{#node.model.primaryIP}',
                    }
                    ],
                    props: {
                        "style": "font-size:80%;"
                    }
                },{
                    tag: 'p',
                    content: [
                        {
                        tag: 'label',
                        content: 'Model: ',
                    }, {
                        tag: 'label',
                        content: '{#node.model.model}',
                    }
                    ],
                    props: {
                        "style": "font-size:80%;"
                    }
                }, {
                    tag: 'p',
                    content: [{
                        tag: 'label',
                        content: 'S/N: ',
                    }, {
                        tag: 'label',
                        content: '{#node.model.serial_number}',
                    }],
                    props: {
                        "style": "font-size:80%; padding:0"
                    }
                },
            ],
            props: {
                "style": "width: 150px;"
            }
        }]
        }
    });

    nx.define('Tooltip.Node', nx.ui.Component, {
        view: function(view){
            view.content.push({
            });
            return view;
        },
        methods: {
            attach: function(args) {
                this.inherited(args);
                this.model();
            }
        }
    });

    nx.define('CustomLinkTooltip', nx.ui.Component, {
        properties: {
            link: {},
            topology: {}
        },
        view: {
            content: [{
                tag: 'div',
                content: [{
                    tag: 'h5',
                    content: [{
                        tag: 'a',
                        content: '{#link.model.label}',
                        props: {"href": "{#link.model.dcimCableURL}", "target": "_blank", "rel": "noopener noreferrer"}
                    }],
                    props: {
                        "style": "border-bottom: dotted 1px; font-size:90%; word-wrap:normal; color:#003688"
                    }
                }, {
                    tag: 'p',
                    content: [
                        {
                        tag: 'label',
                        content: 'Source Device: ',
                    }, {
                        tag: 'label',
                        content: '{#link.model.sourceDeviceName}',
                    }
                    ],
                    props: {
                        "style": "font-size:80%;"
                    }
                }, {
                    tag: 'p',
                    content: [
                        {
                        tag: 'label',
                        content: 'Source Interface: ',
                    }, {
                        tag: 'label',
                        content: '{#link.model.srcIfName}',
                    }
                    ],
                    props: {
                        "style": "font-size:80%;"
                    }
                }, {
                    tag: 'p',
                    content: [
                        {
                        tag: 'label',
                        content: 'Target Device: ',
                    }, {
                        tag: 'label',
                        content: '{#link.model.targetDeviceName}',
                    }
                    ],
                    props: {
                        "style": "font-size:80%;"
                    }
                }, {
                    tag: 'p',
                    content: [
                        {
                        tag: 'label',
                        content: 'Target Interface: ',
                    }, {
                        tag: 'label',
                        content: '{#link.model.tgtIfName}',
                    }
                    ],
                    props: {
                        "style": "font-size:80%;"
                    }
                }
            ],
            props: {
                "style": "width: 200px;"
            }
        }]
        }
    });

    nx.define('Tooltip.Link', nx.ui.Component, {
        view: function(view){
            view.content.push({
            });
            return view;
        },
        methods: {
            attach: function(args) {
                this.inherited(args);
                this.model();
            }
        }
    });

    nx.define('CustomLinkClass', nx.graphic.Topology.Link, {
        properties: {
            sourcelabel: null,
            targetlabel: null
        },
        view: function(view) {
            view.content.push({
                name: 'source',
                type: 'nx.graphic.Text',
                props: {
                    'class': 'sourcelabel',
                    'alignment-baseline': 'text-after-edge',
                    'text-anchor': 'start',
                    "style": "fill: #8d092a"
                }
            }, {
                name: 'target',
                type: 'nx.graphic.Text',
                props: {
                    'class': 'targetlabel',
                    'alignment-baseline': 'text-after-edge',
                    'text-anchor': 'end',
                    "style": "fill: #8d092a"
                }
            });
            
            return view;
        },
        methods: {
            update: function() {
                
                this.inherited();
                var el, point;
                var line = this.line();
                var angle = line.angle();
                var stageScale = this.stageScale();
                
                // pad line
                line = line.pad(18 * stageScale, 18 * stageScale);
                
                if (this.sourcelabel()) {
                    el = this.view('source');
                    point = line.start;
                    el.set('x', point.x);
                    el.set('y', point.y);
                    el.set('text', this.sourcelabel());
                    el.set('transform', 'rotate(' + angle + ' ' + point.x + ',' + point.y + ')');
                    el.setStyle('font-size', 11 * stageScale);
                }
                
                
                if (this.targetlabel()) {
                    el = this.view('target');
                    point = line.end;
                    el.set('x', point.x);
                    el.set('y', point.y);
                    el.set('text', this.targetlabel());
                    el.set('transform', 'rotate(' + angle + ' ' + point.x + ',' + point.y + ')');
                    el.setStyle('font-size', 11 * stageScale);
                }
            }
        }
    });

    var currentLayout = initialLayout;

    horizontal = function() {
        if (currentLayout === 'horizontal') {
            return;
        };
        if (topo.graph().getData()["nodes"].length < 1) {
            return;
        };
        currentLayout = 'horizontal';
        var layout = topo.getLayout('hierarchicalLayout');
        layout.direction('horizontal');
        layout.levelBy(function(node, model) {
            return model.get('layerSortPreference');
        });
        topo.activateLayout('hierarchicalLayout');
    };

    vertical = function() {
        if (currentLayout === 'vertical') {
            return;
        };
        var currentTopoData = topo.graph().getData();
        if (currentTopoData < 1) {
            return;
        };
        currentLayout = 'vertical';
        var layout = topo.getLayout('hierarchicalLayout');
        layout.direction('vertical');
        layout.levelBy(function(node, model) {
          return model.get('layerSortPreference');
        });
        topo.activateLayout('hierarchicalLayout');
    };
    showHideUndonnected = function() {
        let unconnectedNodes = []
        topologyData['nodes'].forEach(function(node){
            var isUnconnected = true
            topologyData['links'].forEach(function(link){
                if (link['source'] === node['id'] | link['target'] === node['id']) {
                    isUnconnected = false;
                    return;
                };
            });
            if (isUnconnected == true) {
                unconnectedNodes.push(node['id'])
            };
        });

        if (unconnectedNodes.length > 0) {
            unconnectedNodes.forEach(function(nodeID) {
                topo.graph().getVertex(nodeID).visible(displayUnconnected);
            });
            displayUnconnected = !displayUnconnected;
        };
    };

    showHideDeviceRoles = function(deviceRole, isVisible) {
        let devicesByRole = []
        topologyData['nodes'].forEach(function(node){
            if (node['deviceRole'] == deviceRole) {
                topo.graph().getVertex(node['id']).visible(isVisible);
            };
        });
    };

    showHideDevicesByTag = function(deviceTag, isVisible) {
        topologyData['nodes'].forEach(function(node){
            if (node['tags'].length < 1) {
                return;
            };
            node['tags'].forEach(function(tag){
                if (tag == deviceTag) {
                    topo.graph().getVertex(node['id']).visible(isVisible);
                    return;
                };
            });
        });
    };

    showHideLogicalMultiCableLinks = function() {
        topologyData['links'].forEach(function(link){
            if (link['isLogicalMultiCable']) {
                topo.getLink(link['id']).visible(displayLogicalMultiCableLinks);
            };
        });
        displayLogicalMultiCableLinks = !displayLogicalMultiCableLinks
    };

    showHidePassiveDevices = function() {
        topologyData['nodes'].forEach(function(node){
            if ('isPassive' in node) {
                if (node['isPassive']) {
                    topo.graph().getVertex(node['id']).visible(displayPassiveDevices);
                };
            };
        });
        displayPassiveDevices = !displayPassiveDevices
    };

    saveView = function (topoSaveURI, CSRFToken) {
        var topoSaveName = document.getElementById('topoSaveName').value.trim();
        var saveButton = document.getElementById('saveTopologyView');
        var saveResultLabel = document.getElementById('saveResult');
        saveButton.setAttribute('disabled', true);
        saveResultLabel.setAttribute('innerHTML', 'Processing');
        var topoData = {
            'name': topoSaveName,
            'topology': JSON.stringify(topo.data()),
            'layout_context': JSON.stringify({
                'initialLayout': initialLayout,
                'displayUnconnected': !displayUnconnected,
                'undisplayedRoles': undisplayedRoles,
                'undisplayedDeviceTags': undisplayedDeviceTags,
                'displayPassiveDevices': !displayPassiveDevices,
                'displayLogicalMultiCableLinks': displayLogicalMultiCableLinks,
                'requestGET': requestGET,
            })
        }
        $.ajax({
            type: 'POST',
            url: topoSaveURI,
            data: JSON.stringify(topoData),
            contentType: "application/json; charset=utf-8",
            headers: {'X-CSRFToken': CSRFToken},
            success: function (response) {
                saveResultLabel.innerHTML = 'Success';
                saveButton.removeAttribute('disabled');
                console.log(response);
            },
            error: function (response) {
                saveResultLabel.innerHTML = 'Failed';
                console.log(response);
            }
        })
    };

    topo.on('topologyGenerated', function(){
        showHideUndonnected();
        showHidePassiveDevices();
        if (displayPassiveDevices) {
            displayLogicalMultiCableLinks = true;
        };
        showHideLogicalMultiCableLinks();
        undisplayedRoles.forEach(function(deviceRole){
            showHideDeviceRoles(deviceRole, false);
        });
        undisplayedDeviceTags.forEach(function(deviceTag){
            showHideDevicesByTag(deviceTag, false);
        });
        topologySavedData['nodes'].forEach(function(node){
            topo.graph().getVertex(node['id']).position({'x': node.x, 'y': node.y});
        });
    });

    // Create an application instance
    var shell = new Shell();
    shell.on('resize', function() {
        topo && topo.adaptToContainer();
    });
    // Run the application
    shell.start();
})(nx);

