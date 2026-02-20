let sidebarOpen = false;
let timerInterval;

function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    sidebar.style.left = sidebarOpen ? "-220px" : "0";
    sidebarOpen = !sidebarOpen;
}

function startElection() {
    let time = 12 * 60 * 60; // 12 hours

    timerInterval = setInterval(() => {
        let h = Math.floor(time / 3600);
        let m = Math.floor((time % 3600) / 60);
        let s = time % 60;

        document.getElementById("timer").innerText =
            `Election Time Left: ${h}h ${m}m ${s}s`;

        time--;

        if (time < 0) {
            clearInterval(timerInterval);
            document.getElementById("timer").innerText = "Election Timeout";
        }
    }, 1000);
}

function endElection() {
    clearInterval(timerInterval);
    document.getElementById("timer").innerText = "Election Timeout";
}

function resetData() {

    if (!confirm("Are you sure? All registered users will be deleted!")) {
        return;
    }



    fetch('/reset_data')
        .then(res => res.json())
        .then(data => {
            alert("All election data reset successfully!");
        });
}

function removeAllUsers() {

    if (!confirm("Are you sure? All registered users will be deleted!")) {
        return;
    }

    fetch('/remove_all_users')
        .then(response => response.json())
        .then(data => {
            alert(data.message);
        })
        .catch(error => {
            alert("Error while removing users");
            console.log(error);
        });
}