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
    // Ajout d'un brouillard très léger pour donner de la profondeur aux lasers
    scene.fog = new THREE.FogExp2(0x000000, 0.02);
    
    // Caméra : Vue plongeante pour voir le sol
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 150);
    camera.position.set(0, 5, 20); 
    camera.lookAt(0, -2, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // --- LUMIÈRES GÉNÉRALES ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5); 
    scene.add(ambientLight);
    
    // Lumière centrale pour éclairer le robot et le sol
    const centerSpot = new THREE.SpotLight(0xffffff, 10);
    centerSpot.position.set(0, 15, 5);
    centerSpot.angle = 0.5;
    centerSpot.penumbra = 0.5;
    scene.add(centerSpot);

    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- LE SOL (Pour voir les impacts de lasers) ---
    const floorGeo = new THREE.PlaneGeometry(50, 50);
    const floorMat = new THREE.MeshStandardMaterial({ 
        color: 0x111111, // Sol sombre
        roughness: 0.5,
        metalness: 0.5
    });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2; // À plat
    floor.position.y = -5; // Niveau du sol
    scene.add(floor);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    // Le robot flotte un peu au dessus du sol (-5)
    robotGroup.position.y = -2; 

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
    // --- SYSTÈME LASER "SPIDER" CENTRAL ---
    // =========================================================
    
    // Le Hub Central en haut
    const laserHub = new THREE.Group();
    laserHub.position.set(0, 9, 0); // Tout en haut au centre
    scene.add(laserHub);

    // Boîtier du laser (Visuel)
    const hubMesh = new THREE.Mesh(new THREE.CylinderGeometry(1, 0.5, 1, 32), new THREE.MeshStandardMaterial({color: 0x222222}));
    laserHub.add(hubMesh);

    // Génération des faisceaux
    const lasers = [];
    const laserColors = [0x00FF00, 0x00FFFF, 0xFF00FF, 0x0000FF, 0xFFFFFF]; // Vert, Cyan, Violet, Bleu, Blanc
    const beamCount = 20; // Nombre de faisceaux

    for (let i = 0; i < beamCount; i++) {
        const pivot = new THREE.Group();
        pivot.position.set(0, -0.5, 0); // Part du bas du hub
        laserHub.add(pivot);

        // Couleur aléatoire
        const color = laserColors[Math.floor(Math.random() * laserColors.length)];
        
        // Le Faisceau (Cylindre très fin et très long)
        // Rayon 0.05 (fin), Longueur 30 (touche le sol)
        const beamGeo = new THREE.CylinderGeometry(0.05, 0.05, 30, 8);
        beamGeo.translate(0, -15, 0); // Décalage pour que le pivot soit en haut
        
        const beamMat = new THREE.MeshBasicMaterial({ 
            color: color, 
            transparent: true, 
            opacity: 0.6,
            blending: THREE.AdditiveBlending // Effet lumineux
        });
        const beam = new THREE.Mesh(beamGeo, beamMat);
        
        // Rotation initiale aléatoire pour former un cône/pyramide
        pivot.rotation.x = (Math.random() - 0.5) * 1.5; // Dispersion X
        pivot.rotation.z = (Math.random() - 0.5) * 1.5; // Dispersion Z

        pivot.add(beam);

        // Le point lumineux au sol (Impact)
        // On place une petite sphère au bout du faisceau
        const dotGeo = new THREE.SphereGeometry(0.3, 16, 16);
        const dotMat = new THREE.MeshBasicMaterial({ color: color });
        const dot = new THREE.Mesh(dotGeo, dotMat);
        dot.position.y = -30; // Au bout du faisceau
        pivot.add(dot);

        // Données d'animation pour chaque laser
        lasers.push({
            obj: pivot,
            speedX: (Math.random() - 0.5) * 0.05,
            speedZ: (Math.random() - 0.5) * 0.05,
            rangeX: Math.random() * 1.2, // Amplitude
            rangeZ: Math.random() * 1.2,
            offsetX: Math.random() * 10,
            offsetZ: Math.random() * 10
        });
    }

    // --- ANIMATION ---
    let time = 0;
    let targetPos = new THREE.Vector3(4, -2, 0);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        // --- ANIMATION DES LASERS (Mouvement aléatoire) ---
        lasers.forEach(l => {
            // Mouvement sinusoïdal complexe pour faire "aléatoire"
            l.obj.rotation.x = Math.sin(time * 2 + l.offsetX) * l.rangeX * 0.5;
            l.obj.rotation.z = Math.cos(time * 1.5 + l.offsetZ) * l.rangeZ * 0.5;
            
            // Rotation lente du Hub entier
            laserHub.rotation.y = time * 0.2;
        });

        // --- ANIMATION ROBOT ---
        if (robotState === 'intro') {
            const script = [{t:0, a:"hide"}, {t:1, a:"enter"}, {t:4, a:"look"}, {t:7, a:"surprise"}, {t:10, a:"wave"}];
            if (introIndex < script.length) {
                if (time >= script[introIndex].t) {
                    const act = script[introIndex].a;
                    if(act=="hide") robotGroup.position.x = -15;
                    if(act=="enter") targetPos.set(4,-2,0); // Y ajusté au sol
                    if(act=="look") { smoothRotate(robotGroup, 'y', -0.5); smoothRotate(head, 'y', 0.8); }
                    if(act=="surprise") { robotGroup.position.y += 0.5; head.rotation.x = -0.3; }
                    if(act=="wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++;
                }
            } else if (time > 15) { robotState = 'moving'; pickNewTarget(); nextEvent = time + 3; }
            if(introIndex>0) robotGroup.position.lerp(targetPos, 0.02);
        }
        else if (robotState === 'moving') {
            robotGroup.position.y = -2 + Math.sin(time*2)*0.1; // Flotte
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
    function pickNewTarget() { targetPos.set((Math.random()>0.5?1:-1)*(3.5+Math.random()*2), -2, 0); }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
    animate();
}
