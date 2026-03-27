const API_URL = "http://127.0.0.1:5000";

document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const correo = document.getElementById("correo").value;
    const clave = document.getElementById("clave").value;

    try {
        const response = await fetch(`${API_URL}/api/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                correo: correo,
                clave: clave
            })
        });

        const data = await response.json();

        if (!response.ok) {
            document.getElementById("mensaje").innerText = data.msg;
            return;
        }

        // 🔥 Guardamos el JWT
        localStorage.setItem("token", data.access_token);

        // Opcional: redirigir
        window.location.href = "dashboard.html";

    } catch (error) {
        console.error(error);
    }
});