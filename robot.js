import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- CONFIGURATION ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES (AVEC NOUVELLES BLAGUES D'EXPLOSION) ---
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
    cache_cache: [
        "Coucou ! Je suis là ! 👋", "Vous m'aviez perdu ? 👻",
        "Bouh ! Surprise ! 🎃", "Téléportation réussie ! ⚡",
        "Je suis passé par le Wi-Fi ! 📶"
    ],
    explosion: [
        "Oups ! Surchauffe système ! 🔥", "J'ai littéralement perdu la tête ! 🤯",
        "Ne vous inquiétez pas, c'est normal.", "Ça fait du bien de s'aérer un peu.",
        "Je me sens un peu éparpillé ce soir...", "Rassemblement des pièces... 🧲",
        "Quelqu'un a vu mon bras gauche ? 💪", "C'est juste un petit bug d'affichage."
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

    // --- SYSTEME DE PARTICULES (FUMÉE) ---
    const particleCount = 300; // Nombre de particules
    const particlesGeo = new THREE.BufferGeometry();
    const posArray = new Float32Array(particleCount * 3);
    const scaleArray = new Float32Array(particleCount);
    const velocityArray = []; // Stockage JS pour la vitesse

    for(let i=0; i<particleCount; i++) {
        posArray[i*3] = 9999; // Caché au début
        posArray[i*3+1] = 9999;
        posArray[i*3+2] = 9999;
        scaleArray[i] = 0;
        velocityArray.push({x:0, y:0, z:0, life:0});
    }
    
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    particlesGeo.setAttribute('scale', new THREE.BufferAttribute(scaleArray, 1));

    // Shader simple pour des ronds flous (fumée)
    const particleMat = new THREE.PointsMaterial({
        color: 0xaaaaaa,
        size: 0.5,
        transparent: true,
        opacity: 0.6,
        map: createCircleTexture() // Fonction utilitaire plus bas
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
        const tex = new THREE.Texture(canvas); tex.needsUpdate = true;
        return tex;
    }

    function triggerSmoke(x, y, z) {
        const positions = particleSystem.geometry.attributes.position.array;
        const scales = particleSystem.geometry.attributes.scale.array;
        
        for(let i=0; i<particleCount; i++) {
            // Reset des particules au point d'impact
            positions[i*3] = x + (Math.random()-0.5)*1.5;
            positions[i*3+1] = y + (Math.random()-0.5)*2.0;
            positions[i*3+2] = z + (Math.random()-0.5)*1.5;
            scales[i] = Math.random() * 0.8 + 0.2;
            
            // Explosion vers le haut
            velocityArray[i] = {
                x: (Math.random()-0.5) * 0.05,
                y: Math.random() * 0.1 + 0.02,
                z: (Math.random()-0.5) * 0.05,
                life: 1.0 // Durée de vie
            };
        }
        particleSystem.geometry.attributes.position.needsUpdate = true;
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
                
                velocityArray[i].life -= 0.02;
                scales[i] = velocityArray[i].life; // Rétrécit en mourant
                
                if(velocityArray[i].life <= 0) {
                    positions[i*3] = 9999; // Cache
                }
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

    // Construction des pièces (Sauvegarde des positions initiales pour la reconstruction)
    function createPart(geo, mat, x, y, z, parent) {
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(x, y, z);
        mesh.userData.origPos = new THREE.Vector3(x, y, z);
        mesh.userData.origRot = new THREE.Euler(0, 0, 0);
        // Vecteur de vélocité pour l'explosion
        mesh.userData.velocity = new THREE.Vector3();
        mesh.userData.rotVelocity = new THREE.Vector3();
        if(parent) parent.add(mesh);
        return mesh;
    }

    // 1. TETE
    const head = createPart(new THREE.SphereGeometry(0.85, 32, 32), whiteMat, 0, 0, 0, robotGroup);
    head.scale.set(1.4, 1.0, 0.75);
    head.userData.origScale = new THREE.Vector3(1.4, 1.0, 0.75);

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

    // 2. CORPS
    const body = createPart(new THREE.SphereGeometry(0.65, 32, 32), whiteMat, 0, -1.1, 0, robotGroup);
    body.scale.set(0.95, 1.1, 0.8);
    body.userData.origScale = new THREE.Vector3(0.95, 1.1, 0.8);
    
    const belt = createPart(new THREE.TorusGeometry(0.62, 0.03, 16, 32), greyMat, 0, 0, 0, body);
    belt.rotation.x = Math.PI/2;

    // 3. BRAS
    const leftArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, -0.8, -0.8, 0, robotGroup);
    leftArm.rotation.z = 0.15; leftArm.userData.origRot.z = 0.15;
    
    const rightArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, 0.8, -0.8, 0, robotGroup);
    rightArm.rotation.z = -0.15; rightArm.userData.origRot.z = -0.15;

    // Liste des pièces détachables pour l'explosion
    const parts = [head, body, leftArm, rightArm];

    scene.add(robotGroup);

    // --- VARIABLES LOGIQUES ---
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

    function pickNewTarget() {
        const aspect = width / height; const vW = 7 * aspect; 
        const side = Math.random() > 0.5 ? 1 : -1; 
        const safeMin = 3.8; const safeMax = vW * 0.55; 
        let x = side * (safeMin + Math.random() * (safeMax - safeMin));
        let y = (Math.random() - 0.5) * 4.0;
        targetPosition.set(x, y, 0);
    }

    // --- LOGIQUE DES EFFETS SPECIAUX ---

    // 1. TELEPORTATION AVEC FUMEE
    function startTeleport() {
        robotState = 'teleporting_out';
        const msg = getUniqueMessage('cache_cache');
        showBubble(msg, 2000);
        
        // 1. Fumée au départ
        triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z);
        
        setTimeout(() => {
            // Disparition
            robotGroup.visible = false;
            pickNewTarget(); // Nouvelle position
            robotGroup.position.copy(targetPosition);
            
            // Attente avant réapparition
            setTimeout(() => {
                // 2. Fumée à l'arrivée
                triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z);
                robotGroup.visible = true;
                robotState = 'moving';
            }, 1500);
        }, 300);
    }

    // 2. EXPLOSION (SURCHAUFFE)
    function startExplosion() {
        robotState = 'exploding';
        const msg = getUniqueMessage('explosion');
        showBubble(msg, 4000);
        
        // 1. Tremblement (géré dans animate)
        setTimeout(() => {
            // 2. BOUM !
            triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z);
            
            // On donne des vitesses aléatoires à chaque membre
            parts.forEach(part => {
                part.userData.velocity.set(
                    (Math.random()-0.5) * 0.3,
                    (Math.random()-0.5) * 0.3,
                    (Math.random()-0.5) * 0.3
                );
                part.userData.rotVelocity.set(
                    Math.random() * 0.2,
                    Math.random() * 0.2,
                    Math.random() * 0.2
                );
            });
            
            // 3. Reconstruction après 3 secondes
            setTimeout(() => {
                robotState = 'reassembling';
                setTimeout(() => {
                    robotState = 'moving';
                    pickNewTarget();
                }, 2000);
            }, 3000);
            
        }, 1500); // Temps de tremblement avant explosion
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
        updateParticles(); // Met à jour la fumée

        // --- GESTION DES ETATS ---
        
        if (robotState === 'moving') {
            robotGroup.position.y += Math.sin(time * 2) * 0.002; // Flottement
            robotGroup.position.lerp(targetPosition, 0.02);
            smoothRotate(robotGroup, 'y', (targetPosition.x - robotGroup.position.x) * 0.05, 0.05);
            smoothRotate(robotGroup, 'z', -(targetPosition.x - robotGroup.position.x) * 0.03, 0.05);
            
            if (robotGroup.position.distanceTo(targetPosition) < 0.5) pickNewTarget();
            
            // DECLENCHEUR ALEATOIRE
            if (time > nextEventTime) {
                const rand = Math.random();
                if (rand < 0.15) startTeleport(); 
                else if (rand < 0.25) startExplosion(); 
                else startSpeaking(); 
            }
        } 
        
        else if (robotState === 'exploding') {
            // Tremblement avant explosion (si velocity est nulle) ou Explosion
            let isMoving = false;
            parts.forEach(part => {
                if (part.userData.velocity.lengthSq() > 0) {
                    isMoving = true;
                    part.position.add(part.userData.velocity);
                    part.rotation.x += part.userData.rotVelocity.x;
                    part.rotation.y += part.userData.rotVelocity.y;
                    part.rotation.z += part.userData.rotVelocity.z;
                    // Ralentissement (friction)
                    part.userData.velocity.multiplyScalar(0.95);
                }
            });
            
            if (!isMoving) {
                // Tremblement pré-explosion
                robotGroup.position.x += (Math.random()-0.5) * 0.1;
                robotGroup.position.y += (Math.random()-0.5) * 0.1;
            }
        }
        
        else if (robotState === 'reassembling') {
            // Retour magnétique
            parts.forEach(part => {
                part.position.lerp(part.userData.origPos, 0.05);
                // Lerp rotation manually
                part.rotation.x += (part.userData.origRot.x - part.rotation.x) * 0.05;
                part.rotation.y += (part.userData.origRot.y - part.rotation.y) * 0.05;
                part.rotation.z += (part.userData.origRot.z - part.rotation.z) * 0.05;
                // Reset velocity
                part.userData.velocity.set(0,0,0);
            });
        }

        else if (robotState === 'speaking') {
            robotGroup.position.lerp(targetPosition, 0.001); 
            smoothRotate(robotGroup, 'y', 0, 0.05); 
            mouth.scale.set(1, 1 + Math.sin(time * 20) * 0.2, 1); 
        }
        
        else if (robotState === 'intro') {
             if (introIndex < introScript.length) {
                const step = introScript[introIndex];
                if (time >= step.time) { showBubble(step.text, 3000); introIndex++; }
            } else if (time > 22) { robotState = 'moving'; pickNewTarget(); nextEventTime = time + 3; }
            if (time < 5.0) robotGroup.rotation.y = Math.sin(time) * 0.3;
            else if (time < 12.0) { robotGroup.position.lerp(new THREE.Vector3(0, 0, 5), 0.02); } 
            else { robotGroup.position.lerp(new THREE.Vector3(4.0, 0, 0), 0.03); }
        }

        // --- BULLE CADRÉE (NE SORT PLUS DE L'ECRAN) ---
        if(bubble && bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); 
            // Si on explose, la bulle reste au centre du groupe, pas sur la tête qui vole
            if (robotState !== 'exploding' && robotState !== 'reassembling') {
                headPos.y += 0.8; 
            }
            headPos.project(camera);
            
            const x = (headPos.x * .5 + .5) * width; 
            const y = (headPos.y * -.5 + .5) * height;
            
            // Padding ajusté pour que le texte reste visible
            // 200px à gauche, et on retire 300px à droite pour le texte long
            const safeX = Math.max(200, Math.min(width - 300, x));
            
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
