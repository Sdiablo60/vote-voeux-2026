import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES (AVEC DANSE & EXPLOSION) ---
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
        "Qui a gagné selon vous ? 🤔", "Patience, patience... ⏳",
        "On attend le feu vert... 🚦"
    ],
    photos: [
        "C'est l'heure des photos ! 📸", "Envoyez vos selfies ! 🤳",
        "Je veux être sur la photo ! 🤖", "Souriez ! 😁",
        "On partage, on partage ! 📲", "Montrez vos plus beaux profils !",
        "Allez, une petite grimace ! 🤪"
    ],
    danse: [
        "C'est l'heure de danser ! 💃", "DJ, monte le son ! 🔊",
        "Regardez mon déhanché ! 🕺", "On se retrouve sur la piste ?",
        "Je suis une machine... à danser ! 🤖", "Bougez avec moi !",
        "Allez, tout le monde debout ! 🙌", "C'est ma chanson préférée ! 🎶"
    ],
    explosion: [
        "Oups ! Surchauffe système ! 🔥", "J'ai littéralement perdu la tête ! 🤯",
        "Rassemblement des pièces... 🧲", "C'est juste un petit bug d'affichage.",
        "Aie, mes circuits... ⚡", "Promis, je me recolle tout de suite."
    ]
};

// Gestionnaire de messages uniques
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

// Séquence d'Intro
const introScript = [
    { time: 1.0, text: "Bonjour à tous ! 👋", action: "look_around" },
    { time: 4.5, text: "Je suis Clap-E, votre robot ! 🤖", action: "present" },
    { time: 8.0, text: "Je vois que la salle est pleine ! 👀", action: "look_around" },
    { time: 11.5, text: "Je vais essayer de ne pas exploser ce soir... 💣", action: "knock" },
    { time: 16.0, text: "Bienvenue : " + config.titre + " ! ✨", action: "present" },
    { time: 20.0, text: "Installez-vous, ça va commencer ! ⏳", action: "wait" }
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

    const ambientLight = new THREE.AmbientLight(0xffffff, 1.1); scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 2.5); dirLight.position.set(5, 10, 7); scene.add(dirLight);
    const screenLight = new THREE.PointLight(0x00ffff, 0.5, 4); screenLight.position.set(0, 0, 2); scene.add(screenLight);
    
    // LUMIERE D'EXPLOSION (Flash)
    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- SYSTEME DE PARTICULES (FUMÉE & ETINCELLES) ---
    const particleCount = 400; 
    const particlesGeo = new THREE.BufferGeometry();
    const posArray = new Float32Array(particleCount * 3);
    const colorArray = new Float32Array(particleCount * 3); // Pour la couleur
    const scaleArray = new Float32Array(particleCount);
    const velocityArray = []; 

    const baseColor = new THREE.Color(0xaaaaaa); // Gris fumée
    const sparkColor = new THREE.Color(0xffaa00); // Orange étincelle

    for(let i=0; i<particleCount; i++) {
        posArray[i*3] = 9999; posArray[i*3+1] = 9999; posArray[i*3+2] = 9999;
        scaleArray[i] = 0;
        velocityArray.push({x:0, y:0, z:0, life:0});
    }
    
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    particlesGeo.setAttribute('color', new THREE.BufferAttribute(colorArray, 3));
    particlesGeo.setAttribute('scale', new THREE.BufferAttribute(scaleArray, 1));

    const particleMat = new THREE.PointsMaterial({
        vertexColors: true,
        size: 0.6,
        transparent: true,
        opacity: 0.8,
        depthWrite: false, // Important pour la transparence
        map: createCircleTexture() 
    });

    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);

    function createCircleTexture() {
        const canvas = document.createElement('canvas'); canvas.width = 32; canvas.height = 32;
        const ctx = canvas.getContext('2d');
        const grad = ctx.createRadialGradient(16,16,0, 16,16,16);
        grad.addColorStop(0, 'rgba(255,255,255,1)');
        grad.addColorStop(1, 'rgba(255,255,255,0)');
        ctx.fillStyle = grad; ctx.fillRect(0,0,32,32);
        const tex = new THREE.Texture(canvas); tex.needsUpdate = true; return tex;
    }

    function triggerSmoke(x, y, z, isExplosion = false) {
        const positions = particleSystem.geometry.attributes.position.array;
        const colors = particleSystem.geometry.attributes.color.array;
        const scales = particleSystem.geometry.attributes.scale.array;
        
        for(let i=0; i<particleCount; i++) {
            // Position de départ
            positions[i*3] = x + (Math.random()-0.5);
            positions[i*3+1] = y + (Math.random()-0.5);
            positions[i*3+2] = z + (Math.random()-0.5);
            
            // Couleur : 30% de chance d'être une étincelle si c'est une explosion
            const isSpark = isExplosion && Math.random() < 0.3;
            const c = isSpark ? sparkColor : baseColor;
            colors[i*3] = c.r; colors[i*3+1] = c.g; colors[i*3+2] = c.b;
            
            scales[i] = Math.random() * 0.8 + 0.2;
            
            // Vitesse
            let speed = isExplosion ? 0.2 : 0.05;
            velocityArray[i] = {
                x: (Math.random()-0.5) * speed,
                y: (Math.random()-0.5) * speed + (isExplosion ? 0.05 : 0.02),
                z: (Math.random()-0.5) * speed,
                life: 1.0 
            };
        }
        particleSystem.geometry.attributes.position.needsUpdate = true;
        particleSystem.geometry.attributes.color.needsUpdate = true;
        particleSystem.geometry.attributes.scale.needsUpdate = true;
    }

    function updateParticles() {
        const positions = particleSystem.geometry.attributes.position.array;
        const scales = particleSystem.geometry.attributes.scale.array;
        let active = false;

        for(let i=0; i<particleCount; i++) {
            if (velocityArray[i].life > 0) {
                active = true;
                positions[i*3] += velocityArray[i].x;
                positions[i*3+1] += velocityArray[i].y;
                positions[i*3+2] += velocityArray[i].z;
                
                velocityArray[i].life -= 0.015;
                scales[i] = velocityArray[i].life; 
                
                if(velocityArray[i].life <= 0) positions[i*3] = 9999; // Cacher
            }
        }
        if(active) {
            particleSystem.geometry.attributes.position.needsUpdate = true;
            particleSystem.geometry.attributes.scale.needsUpdate = true;
        }
    }

    // --- ROBOT GÉOMÉTRIQUE (CLAP-E) ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    
    // Matériaux
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

    // --- LOGIQUE ---
    let time = 0;
    let targetPosition = new THREE.Vector3(4.0, 0, 0); 
    robotGroup.position.copy(targetPosition);
    let robotState = 'intro'; 
    let introIndex = 0;
    let nextEventTime = 0;
    let bubbleTimeout = null;

    if (config.mode !== 'attente') {
        robotState = 'moving';
        targetPosition.set(4.0, 0, 0); 
        robotGroup.position.set(4.0, 0, 0);
    }

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

    // --- DECISION DE CIBLE (LARGE Z-I : ZONE INTERDITE) ---
    function pickNewTarget() {
        const aspect = width / height; const vW = 7 * aspect; 
        const side = Math.random() > 0.5 ? 1 : -1; 
        
        // Zone interdite élargie pour le QR Code : de -3.8 à +3.8
        const safeMin = 4.2; // Très large pour éviter le QR
        const safeMax = vW * 0.55; 
        
        let x = side * (safeMin + Math.random() * (safeMax - safeMin));
        let y = (Math.random() - 0.5) * 4.0;
        targetPosition.set(x, y, 0);
    }

    // --- ETATS SPECIAUX ---

    function startTeleport() {
        robotState = 'teleporting_out';
        triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z, false);
        setTimeout(() => {
            robotGroup.visible = false;
            pickNewTarget(); 
            robotGroup.position.copy(targetPosition);
            setTimeout(() => {
                triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z, false);
                robotGroup.visible = true;
                robotState = 'moving';
            }, 1000);
        }, 200);
    }

    function startExplosion() {
        robotState = 'exploding';
        const msg = getUniqueMessage('explosion');
        showBubble(msg, 3500);
        
        // Sécurité : Si trop au bord, on recentre un peu avant d'exploser
        if (Math.abs(robotGroup.position.x) > 6) {
            robotGroup.position.x = (robotGroup.position.x > 0) ? 5 : -5;
        }

        setTimeout(() => {
            // Flash lumière
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
        robotState = 'dancing';
        targetPosition.copy(robotGroup.position); // Danse sur place
        const msg = getUniqueMessage('danse');
        showBubble(msg, 4000);
        
        setTimeout(() => {
            if (robotState === 'dancing') {
                hideBubble();
                robotState = 'moving';
                pickNewTarget();
            }
        }, 6000); // Danse pendant 6s
    }

    function startSpeaking() {
        robotState = 'speaking';
        targetPosition.copy(robotGroup.position); 
        const msg = getUniqueMessage(config.mode);
        showBubble(msg, 4000); 
        nextEventTime = time + 3 + Math.random() * 5; 
        setTimeout(() => { if (robotState === 'speaking') { hideBubble(); robotState = 'moving'; pickNewTarget(); } }, 4000);
    }

    // --- ANIMATION LOOP ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 
        updateParticles();

        if (robotState === 'intro') {
            if (introIndex < introScript.length) {
                const step = introScript[introIndex];
                if (time >= step.time) { showBubble(step.text, 3000); introIndex++; }
            } else if (time > 22) { robotState = 'moving'; pickNewTarget(); nextEventTime = time + 3; }
            if (time < 5.0) robotGroup.rotation.y = Math.sin(time) * 0.3;
            else if (time < 12.0) { robotGroup.position.lerp(new THREE.Vector3(0, 0, 5), 0.02); } 
            else { robotGroup.position.lerp(new THREE.Vector3(4.0, 0, 0), 0.03); }
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
                else if (rand < 0.35) startDance(); // Danse !
                else startSpeaking(); 
            }
        } 
        
        else if (robotState === 'dancing') {
            // Animation de danse procédurale
            const danceSpeed = time * 8;
            robotGroup.position.y = Math.abs(Math.sin(danceSpeed)) * 0.5 - 1; // Rebondit
            robotGroup.rotation.z = Math.sin(danceSpeed * 0.5) * 0.2; // Balance
            leftArm.rotation.z = Math.PI - 0.5 + Math.sin(danceSpeed) * 0.5; // Bras en l'air
            rightArm.rotation.z = -Math.PI + 0.5 - Math.sin(danceSpeed) * 0.5;
            head.rotation.y = Math.sin(danceSpeed * 2) * 0.3;
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
            if (!isMoving) { // Tremblement avant explosion
                robotGroup.position.x += (Math.random()-0.5) * 0.1;
                robotGroup.position.y += (Math.random()-0.5) * 0.1;
            }
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

        // --- BULLE INTELLIGENTE (Ne sort plus de l'écran) ---
        if(bubble && bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); 
            if(robotState !== 'exploding') headPos.y += 0.8; 
            headPos.project(camera);
            
            const x = (headPos.x * .5 + .5) * width; 
            const y = (headPos.y * -.5 + .5) * height;
            
            // On s'assure que la bulle reste dans l'écran (padding)
            const bubbleWidth = 250; 
            const safeX = Math.max(bubbleWidth/2 + 20, Math.min(width - bubbleWidth/2 - 20, x));
            
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
