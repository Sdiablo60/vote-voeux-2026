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
        console.error("ERREUR:", e);
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
    scene.fog = new THREE.FogExp2(0x050505, 0.01); // Brouillard moins noir (gris très foncé)
    
    // CAMÉRA : Très reculée pour englober la scène
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 300);
    camera.position.set(0, 5, 55); 
    camera.lookAt(0, -5, 0); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // --- LUMIÈRES (HIGH KEY) ---
    // Ambiance forte pour voir le robot quoi qu'il arrive
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.5); 
    scene.add(ambientLight);
    
    // Spot dédié VISAGE ROBOT (Éclairage de face)
    const spotFace = new THREE.SpotLight(0xffffff, 40);
    spotFace.position.set(0, 10, 50); 
    spotFace.angle = 0.3;
    spotFace.penumbra = 0.5;
    scene.add(spotFace);

    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- LE SOL ---
    const floorY = -15; // Très bas pour dégager l'espace
    const grid = new THREE.GridHelper(500, 100, 0x444444, 0x111111);
    grid.position.y = floorY;
    scene.add(grid);
    
    const floorPlane = new THREE.Mesh(
        new THREE.PlaneGeometry(1000, 1000), 
        new THREE.MeshBasicMaterial({ color: 0x080808 }) // Sol pas totalement noir
    );
    floorPlane.rotation.x = -Math.PI / 2;
    floorPlane.position.y = floorY - 0.1;
    scene.add(floorPlane);

    // --- ROBOT (BIG HERO) ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(2.2, 2.2, 2.2); // Robot GÉANT
    // Position Z=18 : Il sort presque de l'écran, bien devant le texte
    robotGroup.position.set(0, floorY + 8, 18); 
    spotFace.target = robotGroup;

    // Matériaux légèrement brillants (emissive) pour être visibles dans le noir
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3, emissive: 0x333333 });
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
    // --- SYSTÈME LASER (CALME & ÉCARTÉ) ---
    // =========================================================
    
    const hubY = 12; // Un peu plus haut
    const laserHub = new THREE.Group();
    laserHub.position.set(0, hubY, 0);
    scene.add(laserHub);

    const hubMesh = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 0.5, 1, 32), new THREE.MeshBasicMaterial({color: 0x222222}));
    laserHub.add(hubMesh);

    const lasers = [];
    const colors = [0x00FF00, 0x00FFFF, 0x0055FF, 0xFF00FF, 0xFFFF00, 0xFF3300, 0xFFFFFF];

    for(let i=0; i<24; i++) { 
        const color = colors[Math.floor(Math.random()*colors.length)];
        
        // 1. FAISCEAU
        const coreGeo = new THREE.CylinderGeometry(0.04, 0.04, 1, 6, 1, true); 
        coreGeo.translate(0, 0.5, 0); coreGeo.rotateX(Math.PI / 2); 
        const coreMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
        const beamCore = new THREE.Mesh(coreGeo, coreMat);
        scene.add(beamCore);

        const glowGeo = new THREE.CylinderGeometry(0.2, 0.6, 1, 8, 1, true); // Très large pour bien voir
        glowGeo.translate(0, 0.5, 0); glowGeo.rotateX(Math.PI / 2); 
        const glowMat = new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
        const beamGlow = new THREE.Mesh(glowGeo, glowMat);
        scene.add(beamGlow);

        // 2. IMPACT
        const dotCoreGeo = new THREE.CircleGeometry(0.8, 16); 
        const dotCoreMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF, transparent: true, opacity: 0, blending: THREE.AdditiveBlending });
        const dotCore = new THREE.Mesh(dotCoreGeo, dotCoreMat);
        dotCore.rotation.x = -Math.PI / 2; dotCore.position.y = floorY + 0.06;
        scene.add(dotCore);

        const dotGlowGeo = new THREE.CircleGeometry(3.0, 32); 
        const dotGlowMat = new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
        const dotGlow = new THREE.Mesh(dotGlowGeo, dotGlowMat);
        dotGlow.rotation.x = -Math.PI / 2;
        scene.add(dotGlow);

        // INIT : Très loin du centre
        let startX, startZ;
        do {
            startX = (Math.random()-0.5) * 100;
            startZ = (Math.random()-0.5) * 80;
        } while (Math.abs(startX) < 25); // Zone interdite X +/- 25

        lasers.push({
            beamCore, beamGlow, dotCore, dotGlow,
            color: color,
            currentPos: new THREE.Vector3(startX, floorY + 0.05, startZ),
            targetPos: new THREE.Vector3(startX, floorY + 0.05, startZ),
            speed: 0.005 + Math.random() * 0.01, // VITESSE TRES LENTE
            isActive: false
        });
    }

    // --- ANIMATION ---
    let time = 0;
    // Cible robot : Avancé vers Z=18
    let targetPos = new THREE.Vector3(0, floorY + 8, 18); 
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;

        // --- ANIMATION LASERS (Limité et Lent) ---
        const maxActive = 6; // Seulement 6 lasers max
        const currentActive = lasers.filter(l => l.isActive).length;

        lasers.forEach((l) => {
            // Gestion ON/OFF douce
            if(Math.random() > 0.995) { // Changement rare
                if(l.isActive) l.isActive = false;
                else if(currentActive < maxActive) {
                    l.isActive = true;
                    // Nouvelle cible LOIN du centre
                    let tx, tz;
                    do {
                        tx = (Math.random()-0.5) * 150;
                        tz = (Math.random()-0.5) * 100;
                    } while (Math.abs(tx) < 25); // Protection Robot Large
                    l.targetPos.set(tx, floorY+0.05, tz);
                }
            }

            // Lerp Opacité (Fondu lent)
            const targetOp = l.isActive ? 1.0 : 0.0;
            const currentOp = l.beamGlow.material.opacity;
            const newOp = currentOp + (targetOp - currentOp) * 0.02;

            l.beamCore.material.opacity = newOp * 0.9;
            l.beamGlow.material.opacity = newOp * 0.15; // Halo discret
            l.dotCore.material.opacity = newOp * 0.8;
            l.dotGlow.material.opacity = newOp * 0.3;

            // Mouvement lent
            l.currentPos.lerp(l.targetPos, l.speed);

            // Mise à jour
            l.dotCore.position.copy(l.currentPos); l.dotCore.position.y = floorY + 0.06;
            l.dotGlow.position.copy(l.currentPos); l.dotGlow.position.y = floorY + 0.05;
            
            const source = new THREE.Vector3(0, hubY, 0);
            l.beamCore.position.copy(source); l.beamCore.lookAt(l.dotCore.position);
            l.beamGlow.position.copy(source); l.beamGlow.lookAt(l.dotGlow.position);
            
            const dist = source.distanceTo(l.dotCore.position);
            l.beamCore.scale.z = dist; l.beamGlow.scale.z = dist;
        });

        // --- ROBOT ---
        if (robotState === 'intro') {
            const script = [{t:0, a:"hide"}, {t:1, a:"enter"}, {t:4, a:"look"}, {t:7, a:"surprise"}, {t:10, a:"wave"}];
            if (introIndex < script.length) {
                if (time >= script[introIndex].t) {
                    const act = script[introIndex].a;
                    if(act=="hide") robotGroup.position.set(-50, floorY+8, 18);
                    if(act=="enter") targetPos.set(0, floorY+8, 18);
                    if(act=="look") { smoothRotate(robotGroup, 'y', -0.5, 0.05); }
                    if(act=="surprise") { robotGroup.position.y += 2.0; head.rotation.x = -0.4; }
                    if(act=="wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++;
                }
            } else if (time > 15) { robotState = 'moving'; pickNewTarget(); nextEvent = time + 2; }
            if(introIndex>0) robotGroup.position.lerp(targetPos, 0.02);
        }
        else if (robotState === 'moving') {
            robotGroup.position.y = (floorY + 8) + Math.sin(time*2)*0.2;
            robotGroup.position.lerp(targetPos, 0.01);
            
            // Regarde la caméra (0, 5, 55)
            robotGroup.lookAt(0, 5, 55); 
            
            if(robotGroup.position.distanceTo(targetPos)<1.0) pickNewTarget();
            
            if(time > nextEvent) {
                const r = Math.random();
                // PARLE TRES SOUVENT (0.7 de probabilité)
                if(r < 0.7) { 
                    robotState='speaking'; 
                    showBubble(getUniqueMessage(config.mode), 4000); 
                    setTimeout(()=>{robotState='moving';pickNewTarget();}, 4000); 
                } else {
                    pickNewTarget();
                }
                nextEvent = time + 3 + Math.random()*2; // Événement toutes les 3-5 sec
            }
        }
        else if (robotState === 'speaking') {
            // Animation bouche
            mouth.scale.set(1, 1+Math.sin(time*25)*0.5, 1);
            // Petit mouvement de tête
            head.rotation.y = Math.sin(time*5) * 0.1;
        }
        else if (robotState === 'exploding') { parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += 0.1; p.userData.velocity.multiplyScalar(0.95); }); }
        else if (robotState === 'reassembling') { parts.forEach(p => { p.position.lerp(p.userData.origPos, 0.1); p.rotation.x *= 0.9; }); }

        if(bubble && bubble.style.opacity == 1) {
            const pos = robotGroup.position.clone(); pos.y += 4.5; // Bulle encore plus haute
            pos.project(camera);
            const x = (pos.x * .5 + .5) * width; const y = (pos.y * -.5 + .5) * height;
            bubble.style.left = Math.max(100, Math.min(width-100, x)) + 'px';
            bubble.style.top = Math.max(50, y - 90) + 'px';
        }
        renderer.render(scene, camera);
    }

    function smoothRotate(obj, axis, target, speed) { obj.rotation[axis] += (target - obj.rotation[axis]) * speed; }
    function showBubble(txt, dur) { bubble.innerText = txt; bubble.style.opacity = 1; setTimeout(() => bubble.style.opacity=0, dur); }
    
    function pickNewTarget() { 
        // Zone de déplacement : Uniquement sur le devant (Z : 15 à 25)
        targetPos.set(
            (Math.random()-0.5) * 30, 
            floorY + 8, 
            15 + Math.random() * 10 
        ); 
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
    animate();
}
