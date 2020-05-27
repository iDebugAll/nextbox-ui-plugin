function showHideUndonnectedButtonInitial() {
    showHideUndonnectedButton = document.getElementById("showHideUndonnectedButton");
    console.log(showHideUndonnectedButton);
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