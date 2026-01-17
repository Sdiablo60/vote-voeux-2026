import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: ["Bienvenue ! ✨", "Installez-vous.", "Prêts ?"],
    vote_off: ["Votes CLOS !"],
    photos: ["Photos ! 📸", "Souriez !", "On partage !"],
    danse: ["Dancefloor ! 💃"],
    explosion: ["Boum !"],
    cache_cache: ["Coucou !"]
};

const usedMessages = {};
function getUniqueMessage(category) {
    if (!MESSAGES_BAG[category]) return "...";
    if (!usedMessages[category]) usedMessages[category] = [];
    if (usedMessages[category].length >= MESSAGES_BAG[category].length) usedMessages[category] = [];
    let available = MESSAGES_BAG[category].filter(m => !usedMessages[category].includes(m));
    if (available.length === 0) available = MESSAGES_BAG[category];
    let msg = available[Math.floor(Math.random() * available.length)];
    usedMessages[category].push(msg);
    return msg;
}

const introScript = [
    { time: 0.0, action: "hide_start" },
    { time: 1.0, action: "enter_stage" },
    { time: 4.0, text: "Je calibre l'écran... 📐", action: "look_around" },
    { time: 7.0, text: "Le cadre est bon cette fois ? 🟥", action: "surprise" },
    { time: 10.0, text: "Zone validée !", action: "wave" }
];

if (container) {
    while(container.firstChild) container.removeChild(container.firstChild);
    try { initRobot(container); } catch (e) { console.error(e); }
}

function initRobot(container) {
    // Reset CSS
    document.body.style.margin = "0";
    document.body.style.padding = "0";
    document.body.style.overflow = "hidden"; 
    
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    container.style.position = 'fixed'; container.style.top = '0'; container.style.left = '0';
    container.style.width = '100%'; container.style.height = '100%';
    container.style.zIndex = '10'; container.style.pointerEvents = 'none';
    
    const scene = new THREE.Scene();
    
    // CAMÉRA FIXE
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 14); // Z=14

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // LUMIÈRES
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); 
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // =========================================================
    // --- STEP 1 : CADRE DE DEBUG (CALIBRAGE VISUEL) ---
    // =========================================================
    let updateDebugBorder = () => {}; 

    if (config.mode === 'photos') {
        const borderGeo = new THREE.BufferGeometry();
        // Ligne rouge épaisse
        const borderMat = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 2 });
        const borderLine = new THREE.Line(borderGeo, borderMat);
        scene.add(borderLine);

        updateDebugBorder = () => {
            const dist = camera.position.z; 
            const vFOV = THREE.MathUtils.degToRad(camera.fov); 
            
            // Calcul des limites physiques de l'écran à Z=0
            const visibleHeight = 2 * Math.tan(vFOV / 2) * dist;
            const visibleWidth = visibleHeight * camera.aspect;

            const halfW = visibleWidth / 2;
            const halfH = visibleHeight / 2;

            // --- RÉGLAGES DE MARGES (UNITÉS 3D) ---
            // On enlève un peu en haut pour passer SOUS le titre rouge
            const marginTop = 1.8; 
            // On enlève un tout petit peu en bas pour ne pas être collé au bas de l'écran
            const marginBottom = 0.2; 
            // On prend 99% de la largeur pour être sûr que ça rentre
            const marginSide = 0.1; 

            // Coordonnées du cadre
            const topY = halfH - marginTop;
            const botY = -halfH + marginBottom;
            const leftX = -halfW + marginSide;
            const rightX = halfW - marginSide;

            const points = [
                new THREE.Vector3(leftX, topY, 0),   // Haut Gauche
                new THREE.Vector3(rightX, topY, 0),  // Haut Droite
                new THREE.Vector3(rightX, botY, 0),  // Bas Droite
                new THREE.Vector3(leftX, botY, 0),   // Bas Gauche
                new THREE.Vector3(leftX, topY, 0)    // Fermer
            ];
            borderGeo.setFromPoints(points);
        };
        updateDebugBorder(); 
    }
    // =========================================================

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.7, 0.7, 0.7);
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); 
    const greyMat = new THREE.MeshStandardMaterial({ color: 0xbbbbbb });

    function createPart(geo, mat, x, y, z, parent) {
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(x, y, z);
        mesh.userData = { origPos: new THREE.Vector3(x, y, z), origRot: new THREE.Euler(0, 0, 0) };
        if(parent) parent.add(mesh);
        return mesh;
    }

    const head = createPart(new THREE.SphereGeometry(0.85, 32, 32), whiteMat, 0, 0, 0, robotGroup);
    head.scale.set(1.4, 1.0, 0.75);
    createPart(new THREE.SphereGeometry(0.78, 32, 32), blackMat, 0, 0, 0.55, head).scale.set(1.25, 0.85, 0.6);
    createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, -0.35, 0.15, 1.05, head);
    createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, 0.35, 0.15, 1.05, head);
    const mouth = createPart(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat, 0, -0.15, 1.05, head);
    mouth.rotation.z = Math.PI;
    const lEar = createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, -1.1, 0, 0, head); lEar.rotation.z = Math.PI/2;
    const rEar = createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, 1.1, 0, 0, head); rEar.rotation.z = Math.PI/2;

    const body = createPart(new THREE.SphereGeometry(0.65, 32, 32), whiteMat, 0, -1.1, 0, robotGroup);
    body.scale.set(0.95, 1.1, 0.8);
    createPart(new THREE.TorusGeometry(0.62, 0.03, 16, 32), greyMat, 0, 0, 0, body).rotation.x = Math.PI/2;

    const leftArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, -0.8, -0.8, 0, robotGroup); leftArm.rotation.z = 0.15;
    const rightArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, 0.8, -0.8, 0, robotGroup); rightArm.rotation.z = -0.15;

    scene.add(robotGroup);

    // --- ANIMATION ---
    let time = 0;
    // On centre le robot verticalement un peu plus bas (Y=-1)
    let targetPosition = new THREE.Vector3((config.mode === 'attente' ? -15 : 0), -1, 0); 
    robotGroup.position.copy(targetPosition);
    
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let introIndex = 0; let nextEventTime = 0; let bubbleTimeout = null;

    function smoothRotate(obj, axis, target, speed) { obj.rotation[axis] += (target - obj.rotation[axis]) * speed; }
    function showBubble(text, dur) { if(!bubble) return; if(bubbleTimeout) clearTimeout(bubbleTimeout); bubble.innerText = text; bubble.style.opacity = 1; if(dur) bubbleTimeout = setTimeout(() => bubble.style.opacity=0, dur); }
    
    function pickNewTarget() { 
        const aspect = width / height; 
        const vW = 7 * aspect; 
        // Robot reste dans une zone sûre au centre
        const safeMax = vW * 0.7; 
        const x = (Math.random()>0.5?1:-1) * (2 + Math.random()*(safeMax-2));
        targetPosition.set(x, -1 + (Math.random()-0.5)*2, 0); 
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        if (robotState === 'intro') {
            if (introIndex < introScript.length) {
                const step = introScript[introIndex];
                if (time >= step.time) { 
                    if(step.text) showBubble(step.text, 3500);
                    if(step.action === "hide_start") robotGroup.position.set(-15, -1, 0);
                    if(step.action === "enter_stage") targetPosition.set(0, -1, 0);
                    if(step.action === "look_around") { smoothRotate(robotGroup, 'y', -0.5, 0.05); }
                    if(step.action === "surprise") { robotGroup.position.y += 0.5; head.rotation.x = -0.3; }
                    if(step.action === "wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++; 
                }
            } else if (time > 18) { robotState = 'moving'; pickNewTarget(); nextEventTime = time + 3; }
            if (introIndex > 0 && introIndex < 3) robotGroup.position.lerp(targetPosition, 0.02);
        } else if (robotState === 'moving') {
            robotGroup.position.y += Math.sin(time*2)*0.002;
            robotGroup.position.lerp(targetPosition, 0.02);
            smoothRotate(robotGroup, 'y', (targetPosition.x - robotGroup.position.x)*0.05, 0.05);
            
            if (robotGroup.position.distanceTo(targetPosition) < 0.5) pickNewTarget();
            if (time > nextEventTime) { 
                if(Math.random()<0.4) { 
                    showBubble(getUniqueMessage(config.mode), 4000); 
                    robotGroup.position.lerp(targetPosition, 0.001); 
                } else pickNewTarget();
                nextEventTime = time + 3 + Math.random()*5; 
            }
        }

        if(bubble && bubble.style.opacity == 1) {
            const pos = robotGroup.position.clone(); pos.y += 0.8; pos.project(camera);
            const x = (pos.x * .5 + .5) * width; const y = (pos.y * -.5 + .5) * height;
            bubble.style.left = Math.max(150, Math.min(width-150, x)) + 'px';
            bubble.style.top = Math.max(50, y - 80) + 'px';
        }

        renderer.render(scene, camera);
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
        if(config.mode === 'photos') updateDebugBorder();
    });
    animate();
}
