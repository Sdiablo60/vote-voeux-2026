import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: ["Bienvenue ! ✨", "Installez-vous.", "La soirée va être belle !", "Prêts pour le show ?", "Coucou la technique ! 👷"],
    vote_off: ["Les votes sont CLOS ! 🛑", "Le podium arrive... 🏆", "Suspens... 😬"],
    photos: ["Photos ! 📸", "Souriez !", "Vous êtes beaux !", "Selfie time ! 🤳"],
    danse: ["Dancefloor ! 💃", "Je sens le rythme ! 🎵", "Allez DJ ! 🔊"],
    explosion: ["Surchauffe ! 🔥", "J'ai perdu la tête... 🤯", "Oups..."],
    cache_cache: ["Coucou ! 👋", "Me revoilà !", "Magie ! ⚡"]
};

if (container) {
    while(container.firstChild) container.removeChild(container.firstChild);
    try {
        initRobot(container);
    } catch (e) {
        console.error("ERREUR FATALE:", e);
    }
}

function getUniqueMessage(category) {
    if (!usedMessages[category]) usedMessages[category] = [];
    if (usedMessages[category].length >= MESSAGES_BAG[category].length) usedMessages[category] = [];
    let available = MESSAGES_BAG[category].filter(m => !usedMessages[category].includes(m));
    if(available.length === 0) available = MESSAGES_BAG[category];
    let msg = available[Math.floor(Math.random() * available.length)];
    usedMessages[category].push(msg);
    return msg;
}
const usedMessages = {};

function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    container.style.position = 'fixed'; container.style.top = '0'; container.style.left = '0';
    container.style.width = '100%'; container.style.height = '100%';
    container.style.zIndex = '1'; container.style.pointerEvents = 'none';
    
    const scene = new THREE.Scene();
    // Brouillard plus dense pour mieux voir les faisceaux
    scene.fog = new THREE.FogExp2(0x000000, 0.03);
    
    // CAMÉRA : Vue grand angle plongeante
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 200);
    camera.position.set(0, 12, 26); // Plus haut et plus loin
    camera.lookAt(0, -5, 0); // Regarde le sol au centre

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // --- LUMIÈRES ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.0); 
    scene.add(ambientLight);
    
    // Spot central qui éclaire le robot et le sol
    const mainSpot = new THREE.SpotLight(0xffffff, 15);
    mainSpot.position.set(0, 20, 0);
    mainSpot.angle = 0.6;
    mainSpot.penumbra = 0.5;
    mainSpot.decay = 1.5;
    mainSpot.distance = 100;
    scene.add(mainSpot);

    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- LE SOL SIMULÉ ---
    const floorLevel = -5;
    
    // 1. Plan sombre
    const floorGeo = new THREE.PlaneGeometry(100, 100);
    const floorMat = new THREE.MeshStandardMaterial({ color: 0x080808, roughness: 0.8 });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = floorLevel;
    scene.add(floor);

    // 2. Grille de perspective (GridHelper)
    const gridHelper = new THREE.GridHelper(100, 40, 0x444444, 0x222222);
    gridHelper.position.y = floorLevel + 0.01; // Juste au dessus du sol
    scene.add(gridHelper);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    robotGroup.position.y = floorLevel + 2; // Le robot flotte au dessus du sol

    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.3 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const greyMat = new THREE.MeshStandardMaterial({ color: 0x888888 });
    
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat);
    head.scale.set(1.4, 1.0, 0.75);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat);
    face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6); head.add(face);
    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat);
    mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);
    const leftEye = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat);
    leftEye.position.set(-0.35, 0.15, 1.05); head.add(leftEye);
    const rightEye = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat);
    rightEye.position.set(0.35, 0.15, 1.05); head.add(rightEye);

    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat);
    body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    const belt = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.03, 16, 32), greyMat);
    belt.rotation.x = Math.PI/2; body.add(belt);
    
    const leftArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    leftArm.position.set(-0.8, -0.8, 0); leftArm.rotation.z = 0.15;
    const rightArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    rightArm.position.set(0.8, -0.8, 0); rightArm.rotation.z = -0.15;

    [head, body, leftArm, rightArm].forEach(p => {
        p.userData = { origPos: p.position.clone(), origRot: p.rotation.clone(), velocity: new THREE.Vector3() };
        if(p!==head && p!==body) robotGroup.add(p);
    });
    robotGroup.add(head); robotGroup.add(body);
    scene.add(robotGroup);
    const parts = [head, body, leftArm, rightArm];

    // =========================================================
    // --- SYSTÈME LASER "SPIDER" GRAND ANGLE ---
    // =========================================================
    
    const laserHubPosY = 9;
    const laserHub = new THREE.Group();
    laserHub.position.set(0, laserHubPosY, 0);
    scene.add(laserHub);

    // Boîtier visuel
    const hubMesh = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 0.8, 1.5, 32), new THREE.MeshStandardMaterial({color: 0x333333}));
    laserHub.add(hubMesh);

    const lasers = [];
    // Palette de couleurs style "Laser RGB"
    const laserColors = [0xFF0000, 0x00FF00, 0x0000FF, 0x00FFFF, 0xFF00FF, 0xFFFF00]; 
    const beamCount = 24; 

    for (let i = 0; i < beamCount; i++) {
        const pivot = new THREE.Group();
        pivot.position.set(0, -0.5, 0);
        laserHub.add(pivot);

        const color = laserColors[Math.floor(Math.random() * laserColors.length)];
        
        // Faisceau très long pour sortir de l'écran
        const beamLen = 60;
        const beamGeo = new THREE.CylinderGeometry(0.06, 0.06, beamLen, 8);
        beamGeo.translate(0, -beamLen/2, 0); 
        
        const beamMat = new THREE.MeshBasicMaterial({ 
            color: color, transparent: true, opacity: 0.7, blending: THREE.AdditiveBlending
        });
        const beam = new THREE.Mesh(beamGeo, beamMat);
        
        // DISPERSION INITIALE TRÈS LARGE
        pivot.rotation.x = (Math.random() - 0.5) * 5.0; 
        pivot.rotation.z = (Math.random() - 0.5) * 5.0;
        pivot.add(beam);

        // POINT D'IMPACT AU SOL
        // Calcul de la distance verticale vers le sol : Hub Y (9) - Sol Y (-5) = 14
        const distToFloor = laserHubPosY - floorLevel;
        const dotGeo = new THREE.SphereGeometry(0.4, 16, 16);
        const dotMat = new THREE.MeshBasicMaterial({ color: color, blending: THREE.AdditiveBlending });
        const dot = new THREE.Mesh(dotGeo, dotMat);
        // On place le point exactement à la distance du sol le long de l'axe Y local du pivot
        dot.position.y = -distToFloor; 
        // On aplatit le point pour faire une "tache" au sol
        dot.scale.set(1.5, 0.1, 1.5);
        pivot.add(dot);

        lasers.push({
            obj: pivot,
            // Vitesses et amplitudes d'animation augmentées
            offsetX: Math.random() * 10,
            offsetZ: Math.random() * 10,
            speedX: (Math.random() * 0.5 + 0.5) * (Math.random()>0.5?1:-1),
            speedZ: (Math.random() * 0.5 + 0.5) * (Math.random()>0.5?1:-1),
            range: Math.random() * 3.5 + 1.5 
        });
    }

    // --- ANIMATION ---
    let time = 0;
    let targetPos = new THREE.Vector3(4, floorLevel + 2, 0);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;

        // Animation Lasers (Balayage large et aléatoire)
        lasers.forEach(l => {
            l.obj.rotation.x += Math.sin(time * l.speedX + l.offsetX) * 0.02 * l.range;
            l.obj.rotation.z += Math.cos(time * l.speedZ + l.offsetZ) * 0.02 * l.range;
        });
        // Rotation lente du moyeu central
        laserHub.rotation.y += 0.005;

        // Robot
        if (robotState === 'intro') {
            const script = [{t:0, a:"hide"}, {t:1, a:"enter"}, {t:4, a:"look"}, {t:7, a:"surprise"}, {t:10, a:"wave"}];
            if (introIndex < script.length) {
                if (time >= script[introIndex].t) {
                    const act = script[introIndex].a;
                    if(act=="hide") robotGroup.position.x = -15;
                    if(act=="enter") targetPos.set(4,floorLevel+2,0);
                    if(act=="look") { smoothRotate(robotGroup, 'y', -0.5); smoothRotate(head, 'y', 0.8); }
                    if(act=="surprise") { robotGroup.position.y += 0.5; head.rotation.x = -0.3; }
                    if(act=="wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++;
                }
            } else if (time > 15) { robotState = 'moving'; pickNewTarget(); nextEvent = time + 3; }
            if(introIndex>0) robotGroup.position.lerp(targetPos, 0.02);
        }
        else if (robotState === 'moving') {
            robotGroup.position.y = (floorLevel + 2) + Math.sin(time*2)*0.1;
            robotGroup.position.lerp(targetPos, 0.02);
            smoothRotate(robotGroup, 'y', (targetPos.x - robotGroup.position.x)*0.05);
            if(robotGroup.position.distanceTo(targetPos)<0.5) pickNewTarget();
            if(time > nextEvent) {
                const r = Math.random();
                if(r<0.2) { robotState='exploding'; showBubble(getUniqueMessage('explosion'), 3000); setTimeout(()=>{parts.forEach(p=>p.userData.velocity.set((Math.random()-0.5)*0.5,(Math.random()-0.5)*0.5,(Math.random()-0.5)*0.5));setTimeout(()=>{robotState='reassembling';setTimeout(()=>{robotState='moving';pickNewTarget();},2000);},3000);},500); }
                else { robotState='speaking'; showBubble(getUniqueMessage(config.mode), 4000); setTimeout(()=>{robotState='moving';pickNewTarget();},4000); }
                nextEvent = time + 5 + Math.random()*5;
            }
        }
        else if (robotState === 'exploding') { parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += 0.1; p.userData.velocity.multiplyScalar(0.95); }); }
        else if (robotState === 'reassembling') { parts.forEach(p => { p.position.lerp(p.userData.origPos, 0.1); p.rotation.x *= 0.9; }); }
        else if (robotState === 'speaking') { robotGroup.position.lerp(targetPos, 0.01); mouth.scale.set(1, 1+Math.sin(time*20)*0.3, 1); }

        if(bubble && bubble.style.opacity == 1) {
            const pos = robotGroup.position.clone(); pos.y += 0.8; pos.project(camera);
            const x = (pos.x * .5 + .5) * width; const y = (pos.y * -.5 + .5) * height;
            bubble.style.left = Math.max(100, Math.min(width-100, x)) + 'px';
            bubble.style.top = Math.max(50, y - 90) + 'px';
        }
        renderer.render(scene, camera);
    }

    function smoothRotate(obj, axis, target) { obj.rotation[axis] += (target - obj.rotation[axis]) * 0.05; }
    function showBubble(txt, dur) { bubble.innerText = txt; bubble.style.opacity = 1; setTimeout(() => bubble.style.opacity=0, dur); }
    function pickNewTarget() { targetPos.set((Math.random()>0.5?1:-1)*(3.5+Math.random()*2), floorLevel+2, 0); }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
    animate();
}
