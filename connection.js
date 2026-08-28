const bluePicksContainer = document.getElementById('blue-picks');
const redPicksContainer = document.getElementById('red-picks');
const blueBansContainer = document.getElementById('blue-bans');
const redBansContainer = document.getElementById('red-bans');

const blueCoachEl = document.getElementById('blue-coach');
const redCoachEl = document.getElementById('red-coach');
const blueLogoEl = document.getElementById('blue-logo');
const redLogoEl = document.getElementById('red-logo');
const sponsorEl = document.getElementById('sponsor-text');
const patchEl = document.getElementById('patch-version');

const blueCoachPlateEl = document.getElementById('blue-coach-plate');
const redCoachPlateEl = document.getElementById('red-coach-plate');

function initializeDraftDOM() {
    const makePicks = (container, side) => {
        if (!container) return;
        container.innerHTML = '';
        for (let i = 0; i < 5; i++) {
            const slot = document.createElement('div');
            slot.classList.add('pick-slot');
            slot.id = `${side}-pick-${i}`;
            
            slot.style.borderTop = side === 'blue' ? "4px solid #0a5be8" : "4px solid #e80a0a";

            slot.innerHTML = `
                <div class="player-name" id="${side}-player-name-${i}">PLAYER ${i + 1}</div>
                <div class="slot-icons">
                    <div class="spell"></div>
                    <div class="spell"></div>
                </div>
            `;
            container.appendChild(slot);
        }
    };

    const makeBans = (container, side) => {
        if (!container) return;
        container.innerHTML = '';
        for (let i = 0; i < 5; i++) {
            const slot = document.createElement('div');
            slot.classList.add('ban-slot');
            slot.id = `${side}-ban-${i}`;
            slot.style.borderBottom = side === 'blue' ? "2px solid #0a5be8" : "2px solid #e80a0a";
            container.appendChild(slot);
        }
    };

    makePicks(bluePicksContainer, 'blue');
    makePicks(redPicksContainer, 'red');
    makeBans(blueBansContainer, 'blue');
    makeBans(redBansContainer, 'red');
}

function updateOverlay(data) {
    const ddragonVer = data.ddragon_version || "14.1.1";

    const displayStyle = data.show_coaches ? 'block' : 'none';
    if (blueCoachPlateEl) blueCoachPlateEl.style.display = displayStyle;
    if (redCoachPlateEl) redCoachPlateEl.style.display = displayStyle;

    if (patchEl) patchEl.textContent = data.patch;
    if (sponsorEl) sponsorEl.textContent = data.sponsor;
    if (blueCoachEl) blueCoachEl.textContent = data.blue.coach;
    if (redCoachEl) redCoachEl.textContent = data.red.coach;
    if (blueLogoEl) blueLogoEl.textContent = data.blue.name;
    if (redLogoEl) redLogoEl.textContent = data.red.name;

    ['blue', 'red'].forEach(side => {
        const sideData = data[side];

        sideData.picks.forEach((champName, idx) => {
            const slotEl = document.getElementById(`${side}-pick-${idx}`);
            const nameEl = document.getElementById(`${side}-player-name-${idx}`);

            if (nameEl) nameEl.textContent = sideData.players[idx];

            if (slotEl) {
                if (champName && champName.trim() !== "" && champName !== "None") {
                    const splashUrl = `https://ddragon.leagueoflegends.com/cdn/img/champion/loading/${champName}_0.jpg`;
                    slotEl.style.backgroundImage = `url('${splashUrl}')`;
                } else {
                    slotEl.style.backgroundImage = 'none';
                }
            }
        });

        sideData.bans.forEach((champName, idx) => {
            const banEl = document.getElementById(`${side}-ban-${idx}`);
            if (banEl) {
                if (champName && champName.trim() !== "" && champName !== "None") {
                    const iconUrl = `https://ddragon.leagueoflegends.com/cdn/${ddragonVer}/img/champion/${champName}.png`;
                    banEl.style.backgroundImage = `url('${iconUrl}')`;
                    banEl.style.backgroundSize = 'cover';
                    banEl.style.backgroundPosition = 'center';
                } else {
                    banEl.style.backgroundImage = 'none';
                }
            }
        });
    });
}

let socket;
function connectWebSocket() {
    socket = new WebSocket('ws://localhost:8765');
    socket.onopen = () => console.log('Connected to LoL Broadcast Controller');
    socket.onmessage = (event) => updateOverlay(JSON.parse(event.data));
    socket.onclose = () => setTimeout(connectWebSocket, 2000);
    socket.onerror = () => socket.close();
}

window.addEventListener('DOMContentLoaded', () => {
    initializeDraftDOM();
    connectWebSocket();
});