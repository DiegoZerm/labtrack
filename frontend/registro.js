/* Pestañas de acceso y registro de cuentas. Usa api(), enterWorkspace() y notify() de app.js. */
const pestanas = [$("#tab-login"), $("#tab-registro")];

function mostrarPestana(pestana, enfocar = false) {
  for (const actual of pestanas) {
    const activa = actual === pestana;
    actual.setAttribute("aria-selected", String(activa));
    actual.tabIndex = activa ? 0 : -1;
    $(`#${actual.getAttribute("aria-controls")}`).hidden = !activa;
  }
  $("#login-error").textContent = "";
  $("#register-error").textContent = "";
  if (enfocar) pestana.focus();
}

pestanas.forEach((pestana, indice) => {
  pestana.addEventListener("click", () => mostrarPestana(pestana));
  pestana.addEventListener("keydown", (event) => {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
    const siguiente = pestanas[(indice + (event.key === "ArrowRight" ? 1 : pestanas.length - 1)) % pestanas.length];
    mostrarPestana(siguiente, true);
  });
});

$("#register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target, button = form.querySelector('[type="submit"]');
  const { email, password, confirm } = Object.fromEntries(new FormData(form));
  $("#register-error").textContent = "";
  if (password.length < 12) {
    $("#register-error").textContent = "La contraseña debe tener al menos 12 caracteres.";
    return;
  }
  if (password !== confirm) {
    $("#register-error").textContent = "Las contraseñas no coinciden.";
    return;
  }
  button.disabled = true;
  try {
    const user = await api("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) });
    form.reset();
    mostrarPestana($("#tab-login"));
    await enterWorkspace(user);
    notify("Cuenta creada. Ya puedes registrar tu primer proyecto.");
  } catch (error) {
    $("#register-error").textContent = error.message;
  } finally {
    button.disabled = false;
  }
});
