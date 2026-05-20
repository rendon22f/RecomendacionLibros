const formulario = document.getElementById('formularioLogin');

formulario.addEventListener('submit', function(evento) {

    evento.preventDefault();

    const usuarioIngresado =
        document.getElementById('usuario').value;

    const contrasenaIngresada =
        document.getElementById('contrasena').value;

    fetch("http://127.0.0.1:8000/login", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            username: usuarioIngresado,
            password: contrasenaIngresada
        })

    })

    .then(response => response.json())

    .then(data => {

        console.log(data);

        alert("Petición enviada correctamente");
    })

    .catch(error => {

        console.error(error);

        alert("Error al conectar con el backend");
    });

});