
window.syncScroll = function(element) {
    const header = document.getElementById('grid-header');
    if (header) {
        header.scrollLeft = element.scrollLeft;
    }
}
