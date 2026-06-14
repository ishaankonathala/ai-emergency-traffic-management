document.addEventListener("DOMContentLoaded", () => {
    // Check if we are on dashboard page
    if (!document.getElementById("grid-fps")) return;

    const socket = io();

    // DOM Elements
    const statFps = document.getElementById("grid-fps");
    const statEmergency = document.getElementById("stat-emergency");
    const statRoute = document.getElementById("stat-route");
    const statEta = document.getElementById("stat-eta");
    const statObstruction = document.getElementById("stat-obstruction");

    const alertBanner = document.getElementById("alert-banner");
    const alertText = document.getElementById("alert-text");
    const obsAlertText = document.getElementById("obs-alert-text");
    const corridorProgressLine = document.getElementById("corridor-progress-line");

    const junctionOrder = ["Junction A", "Junction B", "Junction C", "Junction D"];

    // Socket Listener
    socket.on('state_update', (data) => {
        // System Status
        statFps.innerText = `FPS: ${data.fps.toFixed(1)}`;
        
        if (data.emergency_mode) {
            statEmergency.innerText = data.emergency_type ? data.emergency_type.toUpperCase() : "ACTIVE";
            alertBanner.classList.remove("d-none");
            alertText.innerText = `EMERGENCY: ${data.emergency_type ? data.emergency_type.toUpperCase() : "VEHICLE DETECTED"}`;
            statEta.innerText = data.eta_seconds;
            
            // Assume predicting straight down the line for the demo
            if (data.current_junction) {
                let idx = junctionOrder.indexOf(data.current_junction);
                if (idx < junctionOrder.length - 1) {
                    statRoute.innerText = `${data.current_junction} -> ${junctionOrder[idx+1]}`;
                } else {
                    statRoute.innerText = `Clearing ${data.current_junction}`;
                }
            }
        } else {
            statEmergency.innerText = "None";
            statEta.innerText = "0";
            statRoute.innerText = "Awaiting Target...";
            alertBanner.classList.add("d-none");
        }

        // Obstruction Logic
        if (data.obstruction_alert) {
            statObstruction.className = "badge bg-danger fa-fade";
            statObstruction.innerText = "BLOCKED";
            obsAlertText.innerText = data.obstruction_alert;
        } else {
            statObstruction.className = "badge bg-success";
            statObstruction.innerText = "CLEAR";
            obsAlertText.innerText = "";
        }

        // Junction Visualizer
        junctionOrder.forEach((junction, index) => {
            let state = data.junction_states[junction] || "NORMAL";
            let timer = data.junction_timers[junction] || 0;
            
            // Only show timer if not normal
            document.getElementById(`timer-${junction}`).innerText = state === "NORMAL" ? "-" : `${timer}s`;
            
            const signalDiv = document.getElementById(`signal-${junction}`);
            signalDiv.className = "signal-indicator bg-black border border-2 border-secondary rounded-circle d-inline-block p-3 mb-2 shadow";
            
            if (state === "GREEN" || state === "PREPARE GREEN") signalDiv.classList.add("signal-green");
            else if (state === "YELLOW") signalDiv.classList.add("signal-yellow");
            else if (state === "RED") signalDiv.classList.add("signal-red");
        });

        // Corridor Progress Line
        if (data.corridor_active && data.current_junction) {
            let currentIndex = junctionOrder.indexOf(data.current_junction);
            if (currentIndex !== -1) {
                // Calculate percentage
                let segmentPercentage = 100 / (junctionOrder.length - 1);
                let basePercentage = currentIndex * segmentPercentage;
                let additionalPercentage = segmentPercentage * data.marker_progress;
                corridorProgressLine.style.width = `${Math.min(100, basePercentage + additionalPercentage)}%`;
            }
        } else {
            corridorProgressLine.style.width = "0%";
        }
    });
});

// API calls for simulation
function simulateEvent(vehicleType) {
    fetch('/api/simulate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ vehicle: vehicleType })
    }).then(res => res.json())
      .then(data => console.log("Simulation triggered:", data));
}

function resetSystem() {
    fetch('/api/reset', {
        method: 'POST'
    }).then(res => res.json())
      .then(data => console.log("System reset:", data));
}
