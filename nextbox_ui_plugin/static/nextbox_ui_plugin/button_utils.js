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