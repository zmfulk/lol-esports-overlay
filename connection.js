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

const lastSeenState = {
    blue: {picks: [], bans: []},
    red: {picks: [], bans: []}
};


// Automatically determines whose turn it is based on the complete LoL Pro Draft order
function determineActiveSlot(blueBans, redBans, bluePicks, redPicks) {
    const isValid = p => p && p.trim() !== "" && p !== "None";
    const bb = blueBans.filter(isValid).length;
    const rb = redBans.filter(isValid).length;
    const bp = bluePicks.filter(isValid).length;
    const rp = redPicks.filter(isValid).length;

    // --- PHASE 1: BANS (3 Each) ---
    if (bb === 0 && rb === 0) return { side: 'blue', type: 'ban', idx: 0 };
    if (bb === 1 && rb === 0) return { side: 'red', type: 'ban', idx: 0 };
    if (bb === 1 && rb === 1) return { side: 'blue', type: 'ban', idx: 1 };
    if (bb === 2 && rb === 1) return { side: 'red', type: 'ban', idx: 1 };
    if (bb === 2 && rb === 2) return { side: 'blue', type: 'ban', idx: 2 };
    if (bb === 3 && rb === 2) return { side: 'red', type: 'ban', idx: 2 };

    // --- PHASE 1: PICKS (3 Each) ---
    if (bb === 3 && rb === 3) {
        if (bp === 0 && rp === 0) return { side: 'blue', type: 'pick', idx: 0 };
        if (bp === 1 && rp === 0) return { side: 'red', type: 'pick', idx: 0 };
        if (bp === 1 && rp === 1) return { side: 'red', type: 'pick', idx: 1 };
        if (bp === 1 && rp === 2) return { side: 'blue', type: 'pick', idx: 1 };
        if (bp === 2 && rp === 2) return { side: 'blue', type: 'pick', idx: 2 };
        if (bp === 3 && rp === 2) return { side: 'red', type: 'pick', idx: 2 };
    }

    // --- PHASE 2: BANS (2 Each) ---
    // Note: Red bans first in the second phase!
    if (bp === 3 && rp === 3) {
        if (bb === 3 && rb === 3) return { side: 'red', type: 'ban', idx: 3 };
        if (bb === 3 && rb === 4) return { side: 'blue', type: 'ban', idx: 3 };
        if (bb === 4 && rb === 4) return { side: 'red', type: 'ban', idx: 4 };
        if (bb === 4 && rb === 5) return { side: 'blue', type: 'ban', idx: 4 };
    }

    // --- PHASE 2: PICKS (2 Each) ---
    // Note: Red picks first in the second phase!
    if (bb === 5 && rb === 5) {
        if (bp === 3 && rp === 3) return { side: 'red', type: 'pick', idx: 3 };
        if (bp === 3 && rp === 4) return { side: 'blue', type: 'pick', idx: 3 };
        if (bp === 4 && rp === 4) return { side: 'blue', type: 'pick', idx: 4 };
        if (bp === 5 && rp === 4) return { side: 'red', type: 'pick', idx: 4 };
    }

    return null; // Draft is 100% complete
}

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
                <div class="spell-container" id="${side}-spells-${i}">
                    <div class="spell" id="${side}-spell-${i}-0"></div>
                    <div class="spell" id="${side}-spell-${i}-1"></div>
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

    const spellDisplay = data.show_spells ? 'flex' : 'none';

    // --- CLEAR OLD GLOWS ---
    document.querySelectorAll('.is-picking-blue, .is-picking-red').forEach(el => {
        el.classList.remove('is-picking-blue', 'is-picking-red');
    });

    // --- APPLY NEW TEAM-COLORED GLOW ---
    const activeSlot = determineActiveSlot(data.blue.bans, data.red.bans, data.blue.picks, data.red.picks);
    if (activeSlot) {
        const slot = document.getElementById(`${activeSlot.side}-${activeSlot.type}-${activeSlot.idx}`);
        if (slot) {
            slot.classList.add(`is-picking-${activeSlot.side}`);
        }
    }

    ['blue', 'red'].forEach(side => {
        const sideData = data[side];

        sideData.picks.forEach((champName, idx) => {
            const slotEl = document.getElementById(`${side}-pick-${idx}`);
            const nameEl = document.getElementById(`${side}-player-name-${idx}`);

            if (nameEl) {
                if (sideData.use_champ_names) {
                    nameEl.textContent = (champName && champName.trim() !== "" && champName !== "None") ? champName : "";
                } else {
                    nameEl.textContent = sideData.players[idx];
                }
            }

            if (slotEl) {
                const currentChamp = (champName && champName.trim() !== "" && champName !== "None") ? champName : null;
                const prevChamp = lastSeenState[side].picks[idx];

                // Only update and animate if the champion changed
                if (currentChamp !== prevChamp) {
                    lastSeenState[side].picks[idx] = currentChamp;

                    if (currentChamp) {
                        const splashUrl = `https://ddragon.leagueoflegends.com/cdn/img/champion/loading/${currentChamp}_0.jpg`;
                        slotEl.style.backgroundImage = `url('${splashUrl}')`;
                        
                        // Restart the CSS animation
                        slotEl.classList.remove('animate-reveal');
                        void slotEl.offsetWidth; // Force DOM reflow to restart animation
                        slotEl.classList.add('animate-reveal');
                    } else {
                        slotEl.style.backgroundImage = 'none';
                        slotEl.classList.remove('animate-reveal');
                    }
                }
            }
        });

        // Render Summoner Spells
        if (sideData.spells) {
            const spellMapping = {
                "Cleanse": "Boost",
                "Ignite": "Dot",
                "Ghost": "Haste",
                "Mark": "Snowball",
                "Clarity": "Mana"
            };

            sideData.spells.forEach((playerSpells, idx) => {
                playerSpells.forEach((spellName, sIdx) => {
                    const spellEl = document.getElementById(`${side}-spell-${idx}-${sIdx}`);
                    if (spellEl) {
                        if (spellName && spellName !== "None") {
                            const mappedName = spellMapping[spellName] || spellName;
                            const fileName = mappedName.startsWith("Summoner") ? mappedName : `Summoner${mappedName}`;
                            const spellUrl = `https://ddragon.leagueoflegends.com/cdn/${ddragonVer}/img/spell/${fileName}.png`;
                            
                            spellEl.style.backgroundImage = `url('${spellUrl}')`;
                            spellEl.style.backgroundSize = 'cover';
                            spellEl.style.backgroundPosition = 'center';
                        } else {
                            spellEl.style.backgroundImage = 'none';
                        }
                    }
                });
            });
        }

        sideData.bans.forEach((champName, idx) => {
            const banEl = document.getElementById(`${side}-ban-${idx}`);
            if (banEl) {
                const currentBan = (champName && champName.trim() !== "" && champName !== "None") ? champName : null;
                const prevBan = lastSeenState[side].bans[idx];

                if (currentBan !== prevBan) {
                    lastSeenState[side].bans[idx] = currentBan;

                    if (currentBan) {
                        const iconUrl = `https://ddragon.leagueoflegends.com/cdn/${ddragonVer}/img/champion/${currentBan}.png`;
                        banEl.style.backgroundImage = `url('${iconUrl}')`;
                        banEl.style.backgroundSize = 'cover';
                        banEl.style.backgroundPosition = 'center';
                        
                        // Restart the CSS animation
                        banEl.classList.remove('animate-reveal');
                        void banEl.offsetWidth; // Force DOM reflow to restart animation
                        banEl.classList.add('animate-reveal');
                    } else {
                        banEl.style.backgroundImage = 'none';
                        banEl.classList.remove('animate-reveal');
                    }
                }
            }
        });

        for (let i = 0; i < 5; i++) {
            const spellContainer = document.getElementById(`${side}-spells-${i}`);
            if (spellContainer) spellContainer.style.display = spellDisplay;
        }
    });

    // --- OUTSIDE THE LOOP: Update Team Logos safely ---
    const blueLogoImg = document.getElementById('blue-logo-img');
    if (blueLogoImg) {
        if (data.blue.logo && data.blue.logo.trim() !== "") {
            // Adding '?t=' with the time forces OBS to reload the image immediately when changed
            blueLogoImg.src = data.blue.logo + "?t=" + new Date().getTime();
            blueLogoImg.style.display = 'block';
        } else {
            blueLogoImg.style.display = 'none';
        }
    }

    const redLogoImg = document.getElementById('red-logo-img');
    if (redLogoImg) {
        if (data.red.logo && data.red.logo.trim() !== "") {
            redLogoImg.src = data.red.logo + "?t=" + new Date().getTime();
            redLogoImg.style.display = 'block';
        } else {
            redLogoImg.style.display = 'none';
        }
    }
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