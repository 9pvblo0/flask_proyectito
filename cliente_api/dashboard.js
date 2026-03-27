async function obtenerCursos() {

    const token = localStorage.getItem("token");

    if (!token) {
        alert("No estás autenticado");
        return;
    }

    const response = await fetch("http://127.0.0.1:5000/api/cursos", {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    const data = await response.json();

    // Mostrar JSON bonito (como Postman)
    document.getElementById("resultado").textContent =
        JSON.stringify(data, null, 4);
}