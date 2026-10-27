/* Panel de usuarios, visible solo para el administrador (ADMIN_EMAILS en .env).
   El servidor vuelve a comprobar el permiso en cada petición; ocultar el botón no basta.
   Usa api(), element(), enterWorkspace() y notify() de app.js. */
const botonUsuarios = element("button", "Usuarios", "ghost");
botonUsuarios.type = "button";
botonUsuarios.hidden = true;
$("#logout").before(botonUsuarios);

const dialogoUsuarios = document.createElement("dialog");
dialogoUsuarios.className = "usuarios-dialogo";
dialogoUsuarios.setAttribute("aria-labelledby", "usuarios-titulo");
dialogoUsuarios.innerHTML = `
  <div class="panel-heading"><h2 id="usuarios-titulo">Usuarios</h2><button type="button" class="ghost usuarios-cerrar" aria-label="Cerrar">✕</button></div>
  <p class="help">Crea cuentas para tu equipo. Cada persona solo ve sus propios proyectos.</p>
  <form id="nuevo-usuario">
    <label>Correo electrónico<input name="email" type="email" autocomplete="off" required maxlength="254" placeholder="persona@example.com"></label>
    <div class="form-grid">
      <label>Contraseña inicial<input name="password" type="password" autocomplete="new-password" required minlength="12" maxlength="128"></label>
      <label>Confirmar<input name="confirm" type="password" autocomplete="new-password" required minlength="12" maxlength="128"></label>
    </div>
    <p class="usuarios-ayuda">Mínimo 12 caracteres. <button type="button" class="enlace-boton" id="generar-clave">Generar una segura</button></p>
    <p class="error form-error" role="alert"></p>
    <div class="dialog-footer"><button type="submit">Crear usuario</button></div>
  </form>
  <div class="table-scroll"><table class="usuarios-tabla"><thead><tr><th>Correo</th><th>Rol</th><th>Proyectos</th><th>Experimentos</th></tr></thead><tbody></tbody></table></div>`;
document.body.append(dialogoUsuarios);
const formUsuario = dialogoUsuarios.querySelector("#nuevo-usuario");
const errorUsuario = formUsuario.querySelector(".form-error");

async function cargarUsuarios(resaltar) {
  const cuerpo = dialogoUsuarios.querySelector("tbody");
  try {
    const usuarios = await api("/admin/users");
    cuerpo.replaceChildren(...usuarios.map((usuario) => {
      const fila = element("tr", undefined, usuario.email === resaltar ? "usuario-nuevo" : undefined);
      const rol = element("td");
      rol.append(element("span", usuario.is_admin ? "Administrador" : "Usuario", usuario.is_admin ? "rol rol-admin" : "rol"));
      fila.append(element("td", usuario.email), rol, element("td", String(usuario.projects)), element("td", String(usuario.experiments)));
      return fila;
    }));
  } catch (error) {
    cuerpo.replaceChildren(element("tr")); cuerpo.firstChild.append(element("td", error.message));
  }
}

function claveSegura() {
  const letras = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789-_";
  const azar = crypto.getRandomValues(new Uint32Array(16));
  return Array.from(azar, (n) => letras[n % letras.length]).join("");
}

function mostrarClaves(visible) {
  formUsuario.querySelectorAll('input[type="password"], input[data-clave]').forEach((campo) => {
    campo.dataset.clave = "";
    campo.type = visible ? "text" : "password";
  });
}

dialogoUsuarios.querySelector("#generar-clave").addEventListener("click", () => {
  const clave = claveSegura();
  formUsuario.elements.password.value = clave;
  formUsuario.elements.confirm.value = clave;
  mostrarClaves(true);
  errorUsuario.textContent = "";
  notify("Contraseña generada: cópiala y compártela con la persona.");
});

formUsuario.addEventListener("submit", async (event) => {
  event.preventDefault();
  const boton = formUsuario.querySelector('[type="submit"]');
  const { email, password, confirm } = Object.fromEntries(new FormData(formUsuario));
  errorUsuario.textContent = "";
  if (password.length < 12) { errorUsuario.textContent = "La contraseña debe tener al menos 12 caracteres."; return; }
  if (password !== confirm) { errorUsuario.textContent = "Las contraseñas no coinciden."; return; }
  boton.disabled = true;
  try {
    const creado = await api("/admin/users", { method: "POST", body: JSON.stringify({ email, password }) });
    formUsuario.reset();
    mostrarClaves(false);
    await cargarUsuarios(creado.email);
    notify(`Usuario ${creado.email} creado.`);
  } catch (error) {
    errorUsuario.textContent = error.message;
  } finally {
    boton.disabled = false;
  }
});

botonUsuarios.addEventListener("click", async () => {
  formUsuario.reset();
  mostrarClaves(false);
  errorUsuario.textContent = "";
  dialogoUsuarios.showModal();
  await cargarUsuarios();
});
dialogoUsuarios.querySelector(".usuarios-cerrar").addEventListener("click", () => dialogoUsuarios.close());

/* El rol llega con la sesión (login y /auth/me). */
const enterWorkspaceBase = enterWorkspace;
enterWorkspace = async function (user) {
  botonUsuarios.hidden = !user.is_admin;
  await enterWorkspaceBase(user);
};
if (!$("#workspace").hidden) api("/auth/me").then((user) => { botonUsuarios.hidden = !user.is_admin; }).catch(() => {});
