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

const usedMessages = {};
function getUniqueMessage(category) {
    if (!usedMessages[category]) usedMessages[category] = [];
    if (usedMessages[category].length >= MESSAGES_BAG[category].length) usedMessages[category] = [];
    let available = MESSAGES_BAG[category].filter(m => !usedMessages[category].includes(m));
    if(available.length === 0) available = MESSAGES_BAG[category];
    let msg = available[Math.floor(Math.random() * available.length)];
    usedMessages[category].push(msg);
    return msg;
}

const introScript = [
    { time: 0.0, action: "hide_start" },
    { time: 1.0, action: "enter_stage" },
    { time: 4.0, text: "C'est calme ici... 🤔", action: "look_around" },
    { time: 7.0, text: "OH ! BONJOUR ! 😳", action: "surprise" },
    { time: 10.0, text: "Bienvenue ! ✨", action: "wave" }
];

if (container) { initRobot(container); }

function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    container.style.position = 'fixed'; container.style.top = '0'; container.style.left = '0';
    container.style.width = '100%'; container.style.height = '100%';
    container.style.zIndex = '10'; container.style.pointerEvents = 'none';
    
    const scene = new THREE.Scene();
    
    // CAMÉRA RECULÉE (Z=14) pour voir toute la scène (Haut et Bas)
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 14); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // LUMIERE D'AMBIANCE (Pour voir les spots gris)
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5); 
    scene.add(ambientLight);
    
    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const greyMat = new THREE.MeshStandardMaterial({ color: 0xbbbbbb });
    
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
    
    const leftArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    leftArm.position.set(-0.8, -0.8, 0); leftArm.rotation.z = 0.15;
    const rightArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    rightArm.position.set(0.8, -0.8, 0); rightArm.rotation.z = -0.15;

    [head, body, leftArm, rightArm].forEach(p => {
        p.userData = { origPos: p.position.clone(), origRot: p.rotation.clone(), velocity: new THREE.Vector3(), rotVelocity: new THREE.Vector3() };
        if(p!==head && p!==body) robotGroup.add(p);
    });
    robotGroup.add(head); robotGroup.add(body);
    scene.add(robotGroup);
    const parts = [head, body, leftArm, rightArm];

    // --- CONSTRUCTION DES SPOTS (STYLE IMAGE DE REFERENCE) ---
    const stageSpots = [];
    
    // Matériau du boîtier (Gris Argenté)
    const housingMat = new THREE.MeshStandardMaterial({ color: 0xAAAAAA, roughness: 0.3, metalness: 0.6 });
    
    function createStageLight(x, y, colorInt, isBottom) {
        const group = new THREE.Group();
        group.position.set(x, y, 1); // Z=1 pour être derrière le robot mais devant le fond

        // 1. Support (U)
        const bracket = new THREE.Mesh(new THREE.TorusGeometry(0.6, 0.08, 8, 16, Math.PI), housingMat);
        bracket.rotation.z = isBottom ? 0 : Math.PI;
        group.add(bracket);

        // 2. Corps du spot (Cylindre + Boite)
        const bodyGroup = new THREE.Group();
        group.add(bodyGroup);
        
        const cyl = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.4, 0.8, 32), housingMat);
        cyl.rotation.x = Math.PI/2;
        bodyGroup.add(cyl);

        // 3. Lentille Colorée (Brillante)
        const lensGeo = new THREE.CircleGeometry(0.42, 32);
        const lensMat = new THREE.MeshBasicMaterial({ color: colorInt }); // Toujours la couleur vive
        const lens = new THREE.Mesh(lensGeo, lensMat);
        lens.position.set(0, 0, 0.41);
        bodyGroup.add(lens);

        // 4. Faisceau (Beam) - Très visible
        const beamGeo = new THREE.ConeGeometry(0.5, 25, 32, 1, true);
        beamGeo.translate(0, -12.5, 0); 
        beamGeo.rotateX(-Math.PI / 2);
        
        const beamMat = new THREE.MeshBasicMaterial({ 
            color: colorInt, 
            transparent: true, 
            opacity: 0.15, // Assez visible
            side: THREE.DoubleSide,
            blending: THREE.AdditiveBlending, // Effet lumière
            depthWrite: false
        });
        const beam = new THREE.Mesh(beamGeo, beamMat);
        beam.position.z = 0.45;
        bodyGroup.add(beam);

        // 5. Lumière réelle (SpotLight)
        const light = new THREE.SpotLight(colorInt, 10);
        light.angle = 0.2;
        light.penumbra = 0.5;
        light.distance = 40;
        bodyGroup.add(light); bodyGroup.add(light.target);

        scene.add(group);

        // Orientation : Regarde vers le centre (0,0,0)
        bodyGroup.lookAt(0, 0, 0);
        light.target.position.set(0,0,0);

        return { 
            group, beam, light, 
            baseIntensity: 10,
            flickerSpeed: Math.random() * 0.1 + 0.05,
            timeOff: Math.random() * 100
        };
    }

    // --- POSITIONS & COULEURS (SELON IMAGE) ---
    // HAUT (Y=7) - Couleurs: Jaune, Cyan, Vert, Orange
    stageSpots.push(createStageLight(-9, 7, 0xFFFF00, false));
    stageSpots.push(createStageLight(-3, 7, 0x00FFFF, false));
    stageSpots.push(createStageLight(3, 7, 0x00FF00, false));
    stageSpots.push(createStageLight(9, 7, 0xFFA500, false));

    // BAS (Y=-7) - Couleurs: Vert, Cyan, Orange, Bleu
    stageSpots.push(createStageLight(-9, -7, 0x00FF00, true));
    stageSpots.push(createStageLight(-3, -7, 0x00FFFF, true));
    stageSpots.push(createStageLight(3, -7, 0xFFA500, true));
    stageSpots.push(createStageLight(9, -7, 0x0088FF, true));

    // --- ANIMATION ---
    let time = 0;
    let targetPos = new THREE.Vector3(4, 0, 0);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        // Animation des Spots (Pulsation légère)
        stageSpots.forEach(s => {
            const pulse = Math.sin(time * 2 + s.timeOff) * 0.3 + 0.7; // 0.4 à 1.0
            s.beam.material.opacity = 0.15 * pulse;
            s.light.intensity = s.baseIntensity * pulse;
        });

        // Robot
        if (robotState === 'intro') {
            if (introIndex < introScript.length) {
                const step = introScript[introIndex];
                if (time >= step.time) { 
                    if(step.text) showBubble(step.text, 3500); 
                    if(step.action === "hide_start") robotGroup.position.set(-15, 0, 0);
                    if(step.action === "enter_stage") targetPosition.set(4.0, 0, 0);
                    if(step.action === "look_around") { smoothRotate(robotGroup, 'y', -0.5, 0.05); smoothRotate(head, 'y', 0.8, 0.05); }
                    if(step.action === "surprise") { robotGroup.position.y += 0.5; head.rotation.x = -0.3; }
                    if(step.action === "wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++; 
                }
            } else if (time > 22) { robotState = 'moving'; pickNewTarget(); nextEventTime = time + 3; }
            if (introIndex > 0 && introIndex < 3) robotGroup.position.lerp(targetPosition, 0.02);
        } 
        
        else if (robotState === 'moving') {
            robotGroup.position.y += Math.sin(time * 2) * 0.002;
            robotGroup.position.lerp(targetPos, 0.02);
            smoothRotate(robotGroup, 'y', (targetPos.x - robotGroup.position.x) * 0.05, 0.05);
            smoothRotate(robotGroup, 'z', -(targetPos.x - robotGroup.position.x) * 0.03, 0.05);
            
            if (robotGroup.position.distanceTo(targetPos) < 0.5) pickNewTarget();
            
            if (time > nextEvent) {
                const rand = Math.random();
                if (rand < 0.12) startTeleport(); 
                else if (rand < 0.22) startExplosion(); 
                else if (rand < 0.35) startDance();
                else startSpeaking(); 
            }
        }
        
        else if (robotState === 'dancing') {
            const d = time * 10;
            robotGroup.position.y = Math.abs(Math.sin(d))*0.5 - 0.5;
            robotGroup.rotation.z = Math.sin(d*0.5)*0.2;
            leftArm.rotation.z = Math.PI - 0.5 + Math.sin(d)*0.5;
            rightArm.rotation.z = -Math.PI + 0.5 - Math.sin(d)*0.5;
            head.rotation.y = Math.sin(d*2)*0.3;
        }

        else if (robotState === 'exploding') {
            let isMoving = false;
            parts.forEach(part => {
                if (part.userData.velocity.lengthSq() > 0) {
                    isMoving = true;
                    part.position.add(part.userData.velocity);
                    part.rotation.x += part.userData.rotVelocity.x;
                    part.rotation.y += part.userData.rotVelocity.y;
                    part.rotation.z += part.userData.rotVelocity.z;
                    part.userData.velocity.multiplyScalar(0.95);
                }
            });
            if (!isMoving) robotGroup.position.x += (Math.random()-0.5) * 0.1;
        }
        
        else if (robotState === 'reassembling') {
            parts.forEach(part => {
                part.position.lerp(part.userData.origPos, 0.08);
                part.rotation.x += (part.userData.origRot.x - part.rotation.x) * 0.08;
                part.rotation.y += (part.userData.origRot.y - part.rotation.y) * 0.08;
                part.rotation.z += (part.userData.origRot.z - part.rotation.z) * 0.08;
                part.userData.velocity.set(0,0,0);
            });
        }

        else if (robotState === 'speaking') {
            robotGroup.position.lerp(targetPos, 0.001); 
            smoothRotate(robotGroup, 'y', 0, 0.05); 
            mouth.scale.set(1, 1 + Math.sin(time * 20) * 0.2, 1); 
        }

        if(bubble && bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); if(robotState !== 'exploding') headPos.y += 0.8; headPos.project(camera);
            const x = (headPos.x * .5 + .5) * width; const y = (headPos.y * -.5 + .5) * height;
            bubble.style.left = Math.max(150, Math.min(width - 150, x)) + 'px';
            bubble.style.top = Math.max(50, y - 80) + 'px';
        }

        renderer.render(scene, camera);
    }

    function smoothRotate(object, axis, targetValue, speed) { object.rotation[axis] += (targetValue - object.rotation[axis]) * speed; }
    function showBubble(text, duration) { bubble.innerText = text; bubble.style.opacity = 1; setTimeout(() => bubble.style.opacity = 0, duration); }
    function pickNewTarget() { const side = Math.random() > 0.5 ? 1 : -1; targetPos.set(side * (4.2 + Math.random() * 2), (Math.random() - 0.5) * 4, 0); }
    
    function startExplosion() {
        robotState = 'exploding'; showBubble(getUniqueMessage('explosion'), 3500);
        if (Math.abs(robotGroup.position.x) > 6) robotGroup.position.x = (robotGroup.position.x > 0) ? 5 : -5;
        setTimeout(() => {
            explosionLight.intensity = 5; setTimeout(() => { explosionLight.intensity = 0; }, 200);
            parts.forEach(part => {
                part.userData.velocity.set((Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4);
                part.userData.rotVelocity.set(Math.random()*0.2, Math.random()*0.2, Math.random()*0.2);
            });
            setTimeout(() => { robotState = 'reassembling'; setTimeout(() => { robotState = 'moving'; pickNewTarget(); }, 2000); }, 3000);
        }, 1000);
    }
    function startDance() { if (config.mode !== 'photos') { startSpeaking(); return; } robotState = 'dancing'; targetPos.copy(robotGroup.position); showBubble(getUniqueMessage('danse'), 4000); setTimeout(() => { if (robotState === 'dancing') { bubble.style.opacity = 0; robotState = 'moving'; pickNewTarget(); } }, 6000); }
    function startSpeaking() { robotState = 'speaking'; targetPos.copy(robotGroup.position); showBubble(getUniqueMessage(config.mode), 4000); nextEvent = time + 3 + Math.random() * 5; setTimeout(() => { if (robotState === 'speaking') { bubble.style.opacity = 0; robotState = 'moving'; pickNewTarget(); } }, 4000); }
    function startTeleport() { robotState = 'teleporting'; showBubble(getUniqueMessage('cache_cache'), 1500); setTimeout(() => { robotGroup.visible = false; pickNewTarget(); robotGroup.position.copy(targetPos); setTimeout(() => { robotGroup.visible = true; robotState = 'moving'; }, 1000); }, 500); }

    window.addEventListener('resize', () => { width = window.innerWidth; height = window.innerHeight; renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix(); });
    animate();
}
