function login() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const error = document.getElementById("error");

  // Demo credentials
  const validEmail = "admin@trashure.com";
  const validPassword = "admin123";

  if (email === validEmail && password === validPassword) {
    localStorage.setItem("trashure_logged_in", "true");
    localStorage.setItem("trashure_user", email);

    window.location.href = "index.html";
  } else {
    error.textContent = "Invalid email or password";
  }
}

function checkAuth() {
  const isLoggedIn = localStorage.getItem("trashure_logged_in");

  if (isLoggedIn !== "true") {
    window.location.href = "login.html";
  }
}

function logout() {
  localStorage.removeItem("trashure_logged_in");
  localStorage.removeItem("trashure_user");
  window.location.href = "login.html";
}