function showHideUnconnectedButtonInitial() {
    showHideUnconnectedButton = document.getElementById("showHideUnconnectedButton");
    if (displayUnconnected == false) {
        showHideUnconnectedButton.value = 'Display Unconnected'
    } else {
        showHideUnconnectedButton.value = 'Hide Unconnected';
    };
};

function showHideUnconnectedButtonOnClick(button) {
    if (button.value == 'Hide Unconnected') {
        button.value = 'Display Unconnected'
    } else {
        button.value = 'Hide Unconnected';
    };
    showHideUnconnected();
};

function layerSelectorOnChange(checkbox){
    showHideDeviceRoles(checkbox.value, checkbox.checked);
};

function layerSelectorByTagOnChange(checkbox){
    showHideDevicesByTag(checkbox.value, checkbox.checked)
};

function showHidePassiveDevicesButtonInitial() {
    showHidePassiveDevicesButton = document.getElementById("showHidePassiveDevicesButton");
    if (displayPassiveDevices == false) {
        showHidePassiveDevicesButton.value = 'Display Passive Devices'
    } else {
        showHidePassiveDevicesButton.value = 'Hide Passive Devices';
    };
};

function showHidePassiveDevicesButtonOnClick(button) {
    if (button.value == 'Hide Passive Devices') {
        button.value = 'Display Passive Devices'
        displayLogicalMultiCableLinks = true;
        showHideLogicalMultiCableLinks();
    } else {
        button.value = 'Hide Passive Devices';
        showHideLogicalMultiCableLinks();
    };
    showHidePassiveDevices();
};
