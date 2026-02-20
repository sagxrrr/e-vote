function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    sidebar.classList.toggle("active");

    if (sidebar.style.right === "0px") {
        sidebar.style.right = "-220px";
    } else {
        sidebar.style.right = "0px";
    }
}

document.addEventListener("click", function(e) {
    const sidebar = document.getElementById("sidebar");
    const menubtn = document.querySelector(".menu-icon-right");

    if(
        sidebar.classList.contains("active") &&
        !sidebar.contains(e.target) &&
        !menubtn.contains(e.target)
    ) {
        sidebar.classList.remove("active");
        sidebar.style.right = "-220px";
    }
    });