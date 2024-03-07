function showHideUndonnectedButtonInitial() {
    showHideUndonnectedButton = document.getElementById("showHideUndonnectedButton");
    if (displayUnconnected == false) {
        showHideUndonnectedButton.value = 'Display Unconnected'
    } else {
        showHideUndonnectedButton.value = 'Hide Unconnected';
    };
};

function showHideUndonnectedButtonOnClick(button) {
    if (button.value == 'Hide Unconnected') {
        button.value = 'Display Unconnected'
    } else {
        button.value = 'Hide Unconnected';
    };
    showHideUndonnected();
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
