import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: [
        "Bienvenue ! ✨", "Installez-vous.", "Ravi de vous voir !", 
        "La soirée va être belle !", "Je vérifie les réglages...", "Prêts pour le show ?",
        "C'est un plaisir.", "J'adore l'ambiance !", "Coucou la technique ! 👷"
    ],
    vote_off: [
        "Les votes sont CLOS ! 🛑", "Les jeux sont faits.", "Le podium arrive... 🏆",
        "Suspens... 😬", "Calcul en cours... 🧮", "La régie gère ! ⚡"
    ],
    photos: [
        "Photos ! 📸", "Souriez !", "On partage ! 📲", "Vous êtes beaux !", "Selfie time ! 🤳"
    ],
    danse: [
        "Dancefloor ! 💃", "Je sens le rythme ! 🎵", "Regardez-moi ! 🤖", 
        "On se bouge ! 🙌", "Allez DJ ! 🔊"
    ],
    explosion: [
        "Surchauffe ! 🔥", "J'ai perdu la tête... 🤯", "Rassemblement... 🧲", "Oups..."
    ],
    cache_cache: [
        "Coucou ! 👋", "Me revoilà !", "Magie ! ⚡", "Je suis rapide ! 🚀"
    ]
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
    { time: 4.0, text: "C'est calme ici... 🤔", action: "look_around" },
    { time: 7.0, text: "OH ! BONJOUR ! 😳", action: "surprise" },
    { time: 10.0, text: "Bienvenue au " + config.titre + " ! ✨", action: "wave" },
    { time: 14.0, text: "Prêts pour la soirée ? 🎉", action: "ask" }
];

if (container) {
    try { initRobot(container); } catch (e) { console.error(e); }
}

function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    container.style.position = 'fixed'; container.style.top = '0'; container.style.left = '0';
    container.style.width = '100%'; container.style.height = '100%';
    container.style.zIndex = '10'; container.style.pointerEvents = 'none';
    
    const scene = new THREE.Scene();
    // CAMÉRA RECULÉE POUR VOIR LES SPOTS EN HAUT ET EN BAS
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 11); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // Lumière d'ambiance pour voir le corps gris des spots
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 1.2); 
    scene.add(hemiLight);
    
    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- ROBOT GÉOMÉTRIQUE ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2, metalness: 0.1 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1, metalness: 0.5 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); 
    const greyMat = new THREE.MeshStandardMaterial({ color: 0xbbbbbb });

    function createPart(geo, mat, x, y, z, parent) {
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(x, y, z);
        mesh.userData.origPos = new THREE.Vector3(x, y, z);
        mesh.userData.origRot = new THREE.Euler(0, 0, 0);
        mesh.userData.velocity = new THREE.Vector3();
        mesh.userData.rotVelocity = new THREE.Vector3();
        if(parent) parent.add(mesh);
        return mesh;
    }

    const head = createPart(new THREE.SphereGeometry(0.85, 32, 32), whiteMat, 0, 0, 0, robotGroup);
    head.scale.set(1.4, 1.0, 0.75);
    const face = createPart(new THREE.SphereGeometry(0.78, 32, 32), blackMat, 0, 0, 0.55, head);
    face.scale.set(1.25, 0.85, 0.6);
    const leftEye = createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, -0.35, 0.15, 1.05, head);
    const rightEye = createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, 0.35, 0.15, 1.05, head);
    const mouth = createPart(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat, 0, -0.15, 1.05, head);
    mouth.rotation.z = Math.PI; mouth.userData.origRot.z = Math.PI;
    const leftEar = createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, -1.1, 0, 0, head);
    leftEar.rotation.z = Math.PI/2; leftEar.userData.origRot.z = Math.PI/2;
    const rightEar = createPart(new THREE.CylinderGeometry(0.25, 0.25, 0.1, 16), whiteMat, 1.1, 0, 0, head);
    rightEar.rotation.z = Math.PI/2; rightEar.userData.origRot.z = Math.PI/2;

    const body = createPart(new THREE.SphereGeometry(0.65, 32, 32), whiteMat, 0, -1.1, 0, robotGroup);
    body.scale.set(0.95, 1.1, 0.8);
    const belt = createPart(new THREE.TorusGeometry(0.62, 0.03, 16, 32), greyMat, 0, 0, 0, body);
    belt.rotation.x = Math.PI/2;

    const leftArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, -0.8, -0.8, 0, robotGroup);
    leftArm.rotation.z = 0.15; leftArm.userData.origRot.z = 0.15;
    const rightArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, 0.8, -0.8, 0, robotGroup);
    rightArm.rotation.z = -0.15; rightArm.userData.origRot.z = -0.15;

    const parts = [head, body, leftArm, rightArm];
    scene.add(robotGroup);

    // --- CONSTRUCTION DU SPOT 3D RÉALISTE ---
    const stageSpots = [];
    // Matériau Gris Foncé (plus clair que le fond pour être visible)
    const spotCaseMat = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.3, metalness: 0.7 });
    const barnDoorMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, side: THREE.DoubleSide });

    function createDetailedSpotFixture(color, xPos, yPos, isBottom) {
        const pivotGroup = new THREE.Group();
        // Position Y ajustée pour être visible dans le cadre (6 et -6)
        pivotGroup.position.set(xPos, yPos, 0); 
        
        // 1. Support (U-Bracket)
        const bracketGeo = new THREE.TorusGeometry(0.5, 0.05, 8, 16, Math.PI);
        const bracket = new THREE.Mesh(bracketGeo, spotCaseMat);
        bracket.rotation.z = isBottom ? 0 : Math.PI;
        pivotGroup.add(bracket);

        // Groupe mobile (Corps du spot)
        const bodyGroup = new THREE.Group();
        pivotGroup.add(bodyGroup);

        // 2. Boîtier Arrière (Carré comme sur la photo)
        const rearBox = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.6, 0.8), spotCaseMat);
        rearBox.position.z = 0.4;
        bodyGroup.add(rearBox);

        // 3. Cylindre Avant
        const frontCyl = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.6, 32), spotCaseMat);
        frontCyl.rotation.x = Math.PI / 2;
        frontCyl.position.z = -0.3;
        bodyGroup.add(frontCyl);

        // 4. Lentille (Brillante)
        const lensGeo = new THREE.CircleGeometry(0.35, 32);
        const lensMat = new THREE.MeshBasicMaterial({ color: 0x000000 }); // Noir quand éteint
        const lens = new THREE.Mesh(lensGeo, lensMat);
        lens.position.set(0, 0, -0.61);
        bodyGroup.add(lens);

        // 5. Volets (Barn Doors)
        const doorGeo = new THREE.PlaneGeometry(0.6, 0.4);
        const topDoor = new THREE.Mesh(doorGeo, barnDoorMat);
        topDoor.position.set(0, 0.45, -0.6); topDoor.rotation.x = Math.PI/3;
        bodyGroup.add(topDoor);
        
        const botDoor = new THREE.Mesh(doorGeo, barnDoorMat);
        botDoor.position.set(0, -0.45, -0.6); botDoor.rotation.x = -Math.PI/3;
        bodyGroup.add(botDoor);

        const leftDoor = new THREE.Mesh(doorGeo, barnDoorMat);
        leftDoor.position.set(-0.45, 0, -0.6); leftDoor.rotation.y = -Math.PI/3; leftDoor.rotation.z = Math.PI/2;
        bodyGroup.add(leftDoor);

        const rightDoor = new THREE.Mesh(doorGeo, barnDoorMat);
        rightDoor.position.set(0.45, 0, -0.6); rightDoor.rotation.y = Math.PI/3; rightDoor.rotation.z = Math.PI/2;
        bodyGroup.add(rightDoor);

        // 6. Faisceau Volumétrique
        const beamGeo = new THREE.ConeGeometry(1.0, 20, 32, 1, true);
        beamGeo.translate(0, -10, 0); 
        beamGeo.rotateX(-Math.PI / 2);
        const beamMat = new THREE.MeshBasicMaterial({ 
            color: color, 
            transparent: true, 
            opacity: 0, 
            blending: THREE.AdditiveBlending, 
            depthWrite: false, 
            side: THREE.DoubleSide 
        });
        const beam = new THREE.Mesh(beamGeo, beamMat);
        beam.position.z = -0.65;
        bodyGroup.add(beam);

        // 7. Lumière Réelle
        const light = new THREE.SpotLight(color, 0);
        light.angle = 0.3; light.penumbra = 0.5; light.decay = 2; light.distance = 50;
        bodyGroup.add(light); bodyGroup.add(light.target);
        
        // Cible pour l'orientation
        const targetObj = new THREE.Object3D();
        scene.add(targetObj);
        
        scene.add(pivotGroup);

        return { 
            pivot: pivotGroup, body: bodyGroup, light: light, beam: beam, lens: lens, targetObj: targetObj,
            baseColor: new THREE.Color(color),
            isOn: false,
            intensity: 0,
            mode: 'fixed',
            targetPos: new THREE.Vector3(),
            nextToggle: Math.random() * 5
        };
    }

    // Création des spots (Répartition Haut/Bas)
    const colors = [0xff0000, 0x00ff00, 0x0088ff, 0xffaa00, 0xffffff, 0xff00ff];
    
    // Rampe HAUTE (Y=5.5)
    [-6, -2, 2, 6].forEach((x, i) => stageSpots.push(createDetailedSpotFixture(colors[i%colors.length], x, 5.5, false)));
    // Rampe BASSE (Y=-5.5)
    [-4, 0, 4].forEach((x, i) => stageSpots.push(createDetailedSpotFixture(colors[(i+2)%colors.length], x, -5.5, true)));

    // --- PARTICULES ---
    const particleCount = 300; 
    const particlesGeo = new THREE.BufferGeometry();
    const posArray = new Float32Array(particleCount * 3);
    const colorArray = new Float32Array(particleCount * 3);
    const scaleArray = new Float32Array(particleCount);
    const velocityArray = []; 
    const baseColor = new THREE.Color(0xaaaaaa); const sparkColor = new THREE.Color(0xffaa00); 

    for(let i=0; i<particleCount; i++) {
        posArray[i*3] = 9999; posArray[i*3+1] = 9999; posArray[i*3+2] = 9999;
        scaleArray[i] = 0; velocityArray.push({x:0, y:0, z:0, life:0});
    }
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    particlesGeo.setAttribute('color', new THREE.BufferAttribute(colorArray, 3));
    particlesGeo.setAttribute('scale', new THREE.BufferAttribute(scaleArray, 1));
    
    const particleMat = new THREE.PointsMaterial({
        vertexColors: true, size: 0.6, transparent: true, opacity: 0.8, depthWrite: false,
        map: (function(){ const c = document.createElement('canvas'); c.width=32; c.height=32; const ctx = c.getContext('2d'); const g = ctx.createRadialGradient(16,16,0, 16,16,16); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle=g; ctx.fillRect(0,0,32,32); const t = new THREE.Texture(c); t.needsUpdate=true; return t; })()
    });
    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);

    function triggerSmoke(x, y, z, isExplosion = false) {
        const pPos = particleSystem.geometry.attributes.position.array;
        const pCol = particleSystem.geometry.attributes.color.array;
        const pScl = particleSystem.geometry.attributes.scale.array;
        for(let i=0; i<particleCount; i++) {
            pPos[i*3] = x + (Math.random()-0.5); pPos[i*3+1] = y + (Math.random()-0.5); pPos[i*3+2] = z + (Math.random()-0.5);
            const isSpark = isExplosion && Math.random() < 0.3; const c = isSpark ? sparkColor : baseColor;
            pCol[i*3] = c.r; pCol[i*3+1] = c.g; pCol[i*3+2] = c.b; pScl[i] = Math.random() * 0.8 + 0.2;
            let speed = isExplosion ? 0.2 : 0.05; velocityArray[i] = { x: (Math.random()-0.5)*speed, y: (Math.random()-0.5)*speed + (isExplosion ? 0.05 : 0.02), z: (Math.random()-0.5)*speed, life: 1.0 };
        }
        particleSystem.geometry.attributes.position.needsUpdate = true; particleSystem.geometry.attributes.color.needsUpdate = true; particleSystem.geometry.attributes.scale.needsUpdate = true;
    }
    function updateParticles() {
        const pPos = particleSystem.geometry.attributes.position.array; const pScl = particleSystem.geometry.attributes.scale.array; let active = false;
        for(let i=0; i<particleCount; i++) {
            if (velocityArray[i].life > 0) { active = true; pPos[i*3] += velocityArray[i].x; pPos[i*3+1] += velocityArray[i].y; pPos[i*3+2] += velocityArray[i].z; velocityArray[i].life -= 0.015; pScl[i] = velocityArray[i].life; if(velocityArray[i].life <= 0) pPos[i*3] = 9999; }
        }
        if(active) { particleSystem.geometry.attributes.position.needsUpdate = true; particleSystem.geometry.attributes.scale.needsUpdate = true; }
    }

    // --- LOGIQUE GÉNÉRALE ---
    let time = 0;
    let startX = (config.mode === 'attente') ? -15 : 4.0;
    let targetPosition = new THREE.Vector3(startX, 0, 0); robotGroup.position.copy(targetPosition);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let introIndex = 0; let nextEventTime = 0; let bubbleTimeout = null;

    function smoothRotate(object, axis, targetValue, speed) { object.rotation[axis] += (targetValue - object.rotation[axis]) * speed; }
    function showBubble(text, duration) { if(!bubble) return; if (bubbleTimeout) { clearTimeout(bubbleTimeout); bubbleTimeout = null; } bubble.innerText = text; bubble.style.opacity = 1; if(duration) bubbleTimeout = setTimeout(() => { if(bubble) bubble.style.opacity = 0; }, duration); }
    function hideBubble() { if(bubble) bubble.style.opacity = 0; }
    
    function pickNewTarget() { 
        const aspect = width / height; const vW = 7 * aspect; 
        const side = Math.random() > 0.5 ? 1 : -1; 
        // Zone interdite stricte
        const safeMin = 4.2; const safeMax = vW * 0.55; 
        let x = side * (safeMin + Math.random() * (safeMax - safeMin)); 
        let y = (Math.random() - 0.5) * 4.0; 
        targetPosition.set(x, y, 0); 
    }

    // --- ACTIONS ROBOT ---
    function startExplosion() {
        robotState = 'exploding'; const msg = getUniqueMessage('explosion'); showBubble(msg, 3500);
        if (Math.abs(robotGroup.position.x) > 6) robotGroup.position.x = (robotGroup.position.x > 0) ? 5 : -5;
        setTimeout(() => {
            explosionLight.intensity = 5; setTimeout(() => { explosionLight.intensity = 0; }, 200);
            triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z, true);
            parts.forEach(part => {
                part.userData.velocity.set((Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4);
                part.userData.rotVelocity.set(Math.random()*0.2, Math.random()*0.2, Math.random()*0.2);
            });
            setTimeout(() => {
                robotState = 'reassembling';
                setTimeout(() => { robotState = 'moving'; pickNewTarget(); }, 2000);
            }, 3000);
        }, 1000);
    }

    function startDance() {
        if (config.mode !== 'photos') { startSpeaking(); return; }
        robotState = 'dancing'; targetPosition.copy(robotGroup.position);
        const msg = getUniqueMessage('danse'); showBubble(msg, 4000);
        setTimeout(() => { if (robotState === 'dancing') { hideBubble(); robotState = 'moving'; pickNewTarget(); } }, 6000);
    }

    function startSpeaking() {
        robotState = 'speaking'; targetPosition.copy(robotGroup.position);
        const msg = getUniqueMessage(config.mode); showBubble(msg, 4000);
        nextEventTime = time + 3 + Math.random() * 5;
        setTimeout(() => { if (robotState === 'speaking') { hideBubble(); robotState = 'moving'; pickNewTarget(); } }, 4000);
    }

    function startTeleport() {
        robotState = 'teleporting'; showBubble(getUniqueMessage('cache_cache'), 1500);
        triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z, false);
        setTimeout(() => {
            robotGroup.visible = false; pickNewTarget(); robotGroup.position.copy(targetPosition);
            setTimeout(() => {
                triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z, false);
                robotGroup.visible = true; robotState = 'moving';
            }, 1000);
        }, 500);
    }

    // --- ANIMATION LOOP ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 
        updateParticles();

        // GESTION DES SPOTS (DYNAMIQUE INTELLIGENTE)
        // Compter les actifs pour ne pas dépasser 3
        let activeCount = 0;
        stageSpots.forEach(s => { if(s.isOn) activeCount++; });

        stageSpots.forEach((s) => {
            // Logique de changement d'état
            if (time > s.nextToggle) {
                if (s.isOn) {
                    s.isOn = false; // On éteint
                    s.nextToggle = time + Math.random() * 2 + 1;
                } else {
                    // On allume SEULEMENT si < 3 actifs
                    if (activeCount < 3 && Math.random() > 0.5) {
                        s.isOn = true;
                        s.mode = (Math.random() > 0.7) ? 'track' : 'fixed'; // 30% chance de suivre le robot
                        if(s.mode === 'fixed') {
                            s.targetPos.set((Math.random()-0.5)*12, (Math.random()-0.5)*6, -2);
                        }
                        s.nextToggle = time + Math.random() * 3 + 2; // Reste allumé 2-5s
                    } else {
                        s.nextToggle = time + 0.5; // Réessaie vite
                    }
                }
            }

            // Animation des valeurs
            const targetInt = s.isOn ? 30 : 0;
            const targetOp = s.isOn ? 0.06 : 0; // Opacité faisceau
            
            s.intensity += (targetInt - s.intensity) * 0.1;
            s.light.intensity = s.intensity;
            s.beam.material.opacity = targetOp * (s.intensity / 30);
            
            // Lentille "Emissive"
            s.lens.material.color.setHex(s.isOn ? s.baseColor.getHex() : 0x000000);

            // Orientation
            const realTarget = (s.mode === 'track') ? robotGroup.position : s.targetPos;
            s.body.lookAt(realTarget); 
            s.light.target.position.lerp(realTarget, 0.1);
            s.light.target.updateMatrixWorld();
        });

        // Logique Robot
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
            robotGroup.position.lerp(targetPosition, 0.02);
            smoothRotate(robotGroup, 'y', (targetPosition.x - robotGroup.position.x) * 0.05, 0.05);
            smoothRotate(robotGroup, 'z', -(targetPosition.x - robotGroup.position.x) * 0.03, 0.05);
            
            if (robotGroup.position.distanceTo(targetPosition) < 0.5) pickNewTarget();
            
            if (time > nextEventTime) {
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
            robotGroup.position.lerp(targetPosition, 0.001); 
            smoothRotate(robotGroup, 'y', 0, 0.05); 
            mouth.scale.set(1, 1 + Math.sin(time * 20) * 0.2, 1); 
        }

        if(bubble && bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); if(robotState !== 'exploding') headPos.y += 0.8; headPos.project(camera);
            const x = (headPos.x * .5 + .5) * width; const y = (headPos.y * -.5 + .5) * height;
            const bubbleW = 250; const safeX = Math.max(bubbleW/2 + 20, Math.min(width - bubbleW/2 - 20, x));
            bubble.style.left = safeX + 'px'; bubble.style.top = Math.max(50, y - 80) + 'px';
        }

        renderer.render(scene, camera);
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });

    animate();
}
