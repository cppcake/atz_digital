(async function() {
    try {
        const res = await fetch("/therapy/end", { method: "PUT" });
        // Optionally handle response here
    } catch (e) {
        // Optionally handle error here
    }
    setTimeout(function() {
        window.gotoUri("/");
    }, 1000);
})();