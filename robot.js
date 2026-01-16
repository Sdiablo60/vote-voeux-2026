import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: [
        "Salut tout le monde ! 👋", "Tout le monde est bien installé ? 💺", 
        "Je vérifie les objectifs... 🧐", "Qui a le plus beau sourire ? 📸",
        "N'oubliez pas de voter ! 🗳️", "Quelle ambiance de folie ! 🎉",
        "Je suis Clap-E, votre assistant ! 🤖", "Il fait chaud sous les spots ! 💡",
        "Vous me voyez bien ? 👀", "C'est parti pour le show ! 🚀",
        "J'envoie des ondes positives à la Régie... 📡", "La Régie, tout est OK ? 👍",
        "Un petit coucou à l'équipe technique ! 👷"
    ],
    vote_off: [
        "Les votes sont CLOS ! 🛑", "Rien ne va plus ! 🎲",
        "Le podium arrive... 🏆", "Mais que fait la régie ? 😴",
        "Suspens insoutenable... 😬", "Je calcule les résultats... 🧮",
        "Qui a gagné selon vous ? 🤔", "Patience, patience... ⏳"
    ],
    photos: [
        "C'est l'heure des photos ! 📸", "Envoyez vos selfies ! 🤳",
        "Je veux être sur la photo ! 🤖", "Souriez ! 😁",
        "On partage, on partage ! 📲", "Montrez vos plus beaux profils !",
        "Allez, une petite grimace ! 🤪"
    ],
    danse: [
        "C'est l'heure de danser ! 💃", "DJ, monte le son ! 🔊",
        "Regardez mon déhanché ! 🕺", "Je suis le roi du dancefloor !",
        "Allez, tout le monde bouge !", "C'est ma chanson ! 🎶"
    ],
    explosion: [
        "Oups ! Surchauffe système ! 🔥", "J'ai perdu la tête ! 🤯",
        "Rassemblement des pièces... 🧲", "Petit bug graphique, désolé.",
        "Je me sens éparpillé..."
    ],
    intro: [
        "Tiens ? C'est calme ici...", "Oh ! Bonjour ! Je ne vous avais pas vus !",
        "Vous êtes là pour la soirée ?", "Bienvenue au " + config.titre + " !"
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
    { time: 4.0, text: "Tiens ? C'est calme ici... 🤔", action: "look_around" },
    { time: 7.0, text: "OH ! BONJOUR ! 😳", action: "surprise" },
    { time: 10.0, text: "Je ne vous avais pas vus ! 👋", action: "wave" },
    { time: 14.0, text: "Bienvenue à tous ! ✨", action: "present" },
    { time: 18.0, text: "Vous êtes là pour la soirée ? 🎉", action: "ask" }
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
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 8); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // --- LUMIERES ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4); 
    scene.add(ambientLight);
    
    // Flash d'explosion (caché par défaut)
    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- ROBOT GÉOMÉTRIQUE (CLAP-E) ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    
    // Matériaux Robot
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

    // --- SYSTEME DE SPOTS PHYSIQUES 3D ---
    const stageSpots = [];
    // Couleurs des 5 spots
    const spotColors = [0xff0000, 0x00ff00, 0x0088ff, 0xffaa00, 0xffffff]; 
    
    // Matériau pour le corps du spot (noir métal)
    const spotBodyMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.5, metalness: 0.8 });

    function createPhysicalSpot(color, xPos) {
        const spotGroup = new THREE.Group();
        spotGroup.position.set(xPos, 5.5, 2); // Position en haut
        
        // 1. Le corps du spot (Cylindre)
        const fixture = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.2, 0.8, 16), spotBodyMat);
        fixture.rotation.x = Math.PI / 2; // Pointer vers l'avant par défaut
        spotGroup.add(fixture);
        
        // 2. La Lentille (Emissive pour briller)
        const lensGeo = new THREE.CircleGeometry(0.28, 32);
        const lensMat = new THREE.MeshBasicMaterial({ color: color });
        const lens = new THREE.Mesh(lensGeo, lensMat);
        lens.position.set(0, -0.41, 0); // Devant le cylindre
        lens.rotation.x = Math.PI / 2;
        fixture.add(lens);

        // 3. Le Faisceau Volumétrique (Cône transparent)
        // Astuce : Un cône très long, transparent, additif
        const beamGeo = new THREE.ConeGeometry(0.8, 15, 32, 1, true); // Open ended
        beamGeo.translate(0, -7.5, 0); // Le pivot est au sommet
        beamGeo.rotateX(-Math.PI / 2); // Pointe vers l'avant
        
        const beamMat = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.08, // Très subtil
            side: THREE.DoubleSide,
            depthWrite: false, // Important pour la transparence
            blending: THREE.AdditiveBlending // Mode lumière
        });
        const beam = new THREE.Mesh(beamGeo, beamMat);
        spotGroup.add(beam);

        // 4. La Vraie Lumière (SpotLight)
        const light = new THREE.SpotLight(color, 20); // Intensité
        light.angle = 0.3;
        light.penumbra = 0.2;
        light.decay = 1.5;
        light.distance = 40;
        light.castShadow = true;
        
        // On attache la lumière au groupe pour qu'elle suive
        spotGroup.add(light);
        spotGroup.add(light.target); // Nécessaire pour ThreeJS

        scene.add(spotGroup);
        
        return { group: spotGroup, light: light, beam: beam, fixture: fixture };
    }

    // Création des 5 spots
    spotColors.forEach((col, i) => {
        // Positions : -6, -3, 0, 3, 6
        const x = (i - 2) * 3; 
        const spotObj = createPhysicalSpot(col, x);
        stageSpots.push(spotObj);
    });

    // --- PARTICULES (EXPLOSION) ---
    const particleCount = 400; 
    const particlesGeo = new THREE.BufferGeometry();
    const posArray = new Float32Array(particleCount * 3);
    const colorArray = new Float32Array(particleCount * 3);
    const scaleArray = new Float32Array(particleCount);
    const velocityArray = []; 

    const baseColor = new THREE.Color(0xaaaaaa); 
    const sparkColor = new THREE.Color(0xffaa00); 

    for(let i=0; i<particleCount; i++) {
        posArray[i*3] = 9999; posArray[i*3+1] = 9999; posArray[i*3+2] = 9999;
        scaleArray[i] = 0; velocityArray.push({x:0, y:0, z:0, life:0});
    }
    
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    particlesGeo.setAttribute('color', new THREE.BufferAttribute(colorArray, 3));
    particlesGeo.setAttribute('scale', new THREE.BufferAttribute(scaleArray, 1));

    const particleMat = new THREE.PointsMaterial({
        vertexColors: true, size: 0.6, transparent: true, opacity: 0.8, depthWrite: false,
        map: (function(){
            const c = document.createElement('canvas'); c.width=32; c.height=32;
            const ctx = c.getContext('2d');
            const g = ctx.createRadialGradient(16,16,0, 16,16,16);
            g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(1, 'rgba(255,255,255,0)');
            ctx.fillStyle=g; ctx.fillRect(0,0,32,32);
            const t = new THREE.Texture(c); t.needsUpdate=true; return t;
        })()
    });
    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);

    function triggerSmoke(x, y, z, isExplosion = false) {
        const pPos = particleSystem.geometry.attributes.position.array;
        const pCol = particleSystem.geometry.attributes.color.array;
        const pScl = particleSystem.geometry.attributes.scale.array;
        for(let i=0; i<particleCount; i++) {
            pPos[i*3] = x + (Math.random()-0.5); pPos[i*3+1] = y + (Math.random()-0.5); pPos[i*3+2] = z + (Math.random()-0.5);
            const isSpark = isExplosion && Math.random() < 0.3;
            const c = isSpark ? sparkColor : baseColor;
            pCol[i*3] = c.r; pCol[i*3+1] = c.g; pCol[i*3+2] = c.b;
            pScl[i] = Math.random() * 0.8 + 0.2;
            let speed = isExplosion ? 0.2 : 0.05;
            velocityArray[i] = { x: (Math.random()-0.5)*speed, y: (Math.random()-0.5)*speed + (isExplosion ? 0.05 : 0.02), z: (Math.random()-0.5)*speed, life: 1.0 };
        }
        particleSystem.geometry.attributes.position.needsUpdate = true;
        particleSystem.geometry.attributes.color.needsUpdate = true;
        particleSystem.geometry.attributes.scale.needsUpdate = true;
    }

    function updateParticles() {
        const pPos = particleSystem.geometry.attributes.position.array;
        const pScl = particleSystem.geometry.attributes.scale.array;
        let active = false;
        for(let i=0; i<particleCount; i++) {
            if (velocityArray[i].life > 0) {
                active = true;
                pPos[i*3] += velocityArray[i].x; pPos[i*3+1] += velocityArray[i].y; pPos[i*3+2] += velocityArray[i].z;
                velocityArray[i].life -= 0.015; pScl[i] = velocityArray[i].life;
                if(velocityArray[i].life <= 0) pPos[i*3] = 9999;
            }
        }
        if(active) {
            particleSystem.geometry.attributes.position.needsUpdate = true;
            particleSystem.geometry.attributes.scale.needsUpdate = true;
        }
    }

    // --- LOGIQUE ---
    let time = 0;
    let startX = (config.mode === 'attente') ? -15 : 4.0;
    let targetPosition = new THREE.Vector3(startX, 0, 0); 
    robotGroup.position.copy(targetPosition);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let introIndex = 0;
    let nextEventTime = 0;
    let bubbleTimeout = null;

    function smoothRotate(object, axis, targetValue, speed) {
        object.rotation[axis] += (targetValue - object.rotation[axis]) * speed;
    }

    function showBubble(text, duration) {
        if(!bubble) return;
        if (bubbleTimeout) { clearTimeout(bubbleTimeout); bubbleTimeout = null; }
        bubble.innerText = text; bubble.style.opacity = 1;
        if(duration) bubbleTimeout = setTimeout(() => { if(bubble) bubble.style.opacity = 0; }, duration);
    }

    function hideBubble() { if(bubble) bubble.style.opacity = 0; }

    function pickNewTarget() {
        const aspect = width / height; const vW = 7 * aspect; 
        const side = Math.random() > 0.5 ? 1 : -1; 
        const safeMin = 3.8; const safeMax = vW * 0.55; 
        let x = side * (safeMin + Math.random() * (safeMax - safeMin));
        let y = (Math.random() - 0.5) * 4.0;
        targetPosition.set(x, y, 0);
    }

    // --- ETATS ---
    function startExplosion() {
        robotState = 'exploding';
        const msg = getUniqueMessage('explosion');
        showBubble(msg, 3500);
        if (Math.abs(robotGroup.position.x) > 6) robotGroup.position.x = (robotGroup.position.x > 0) ? 5 : -5;
        setTimeout(() => {
            explosionLight.intensity = 5;
            setTimeout(() => { explosionLight.intensity = 0; }, 200);
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
        robotState = 'dancing';
        targetPosition.copy(robotGroup.position);
        const msg = getUniqueMessage('danse');
        showBubble(msg, 4000);
        setTimeout(() => {
            if (robotState === 'dancing') { hideBubble(); robotState = 'moving'; pickNewTarget(); }
        }, 6000);
    }

    function startSpeaking() {
        robotState = 'speaking';
        targetPosition.copy(robotGroup.position); 
        const msg = getUniqueMessage(config.mode);
        showBubble(msg, 4000); 
        nextEventTime = time + 3 + Math.random() * 5; 
        setTimeout(() => { if (robotState === 'speaking') { hideBubble(); robotState = 'moving'; pickNewTarget(); } }, 4000);
    }

    function startTeleport() {
        robotState = 'teleporting';
        showBubble("Hop ! Magie ! ✨", 1500);
        setTimeout(() => {
            robotGroup.visible = false; pickNewTarget(); robotGroup.position.copy(targetPosition);
            setTimeout(() => { robotGroup.visible = true; robotState = 'moving'; }, 1000);
        }, 500);
    }

    // --- ANIMATION LOOP ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 
        updateParticles();

        // Animation des Spots 3D (TRACKING)
        stageSpots.forEach((s, i) => {
            // Le corps du spot regarde le robot
            s.group.lookAt(robotGroup.position);
            // La lumière aussi
            s.light.target.position.copy(robotGroup.position);
            s.light.target.updateMatrixWorld();
            
            // Petit mouvement naturel (oscillation légère)
            s.group.rotation.z += Math.sin(time + i) * 0.002;
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
                if (rand < 0.10) startTeleport(); 
                else if (rand < 0.20) startExplosion(); 
                else if (rand < 0.35) startDance();
                else startSpeaking(); 
            }
        } 
        else if (robotState === 'dancing') {
            const dSpeed = time * 10;
            robotGroup.position.y = Math.abs(Math.sin(dSpeed))*0.5 - 0.5;
            robotGroup.rotation.z = Math.sin(dSpeed*0.5)*0.2;
            leftArm.rotation.z = Math.PI - 0.5 + Math.sin(dSpeed)*0.5;
            rightArm.rotation.z = -Math.PI + 0.5 - Math.sin(dSpeed)*0.5;
            head.rotation.y = Math.sin(dSpeed*2)*0.3;
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
            if (!isMoving) { robotGroup.position.x += (Math.random()-0.5) * 0.1; }
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
            const bubbleW = 250;
            const safeX = Math.max(bubbleW/2 + 20, Math.min(width - bubbleW/2 - 20, x));
            bubble.style.left = safeX + 'px';
            bubble.style.top = Math.max(50, y - 80) + 'px';
        }

        renderer.render(scene, camera);
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });

    animate();
}
