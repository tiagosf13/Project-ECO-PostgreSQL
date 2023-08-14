function logout(arg) {
    fetch(`/logout?param=${arg}`, {
        method: 'POST'
    }).then(function(response) {
        if (response.redirected) {
            window.location.href = response.url;
        }
    }).catch(function(error) {
        console.log(error);
    });
}

document.querySelector('a[href="/logout"]').addEventListener('click', function(e) {
    e.preventDefault();
    logout(id_);
});

