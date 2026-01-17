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
    scene.fog = new THREE.FogExp2(0x000000, 0.012); 
    
    // CAMÉRA : Reculée pour voir le robot en entier
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 300);
    camera.position.set(0, 4, 45); 
    camera.lookAt(0, -2, 0); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // --- LUMIÈRES (BOOSTÉES) ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.0); // Ambiance forte
    scene.add(ambientLight);
    
    // Spot spécial "Visage Robot"
    const spotFace = new THREE.SpotLight(0xffffff, 30);
    spotFace.position.set(0, 10, 40); // Devant le robot
    spotFace.angle = 0.5;
    spotFace.penumbra = 0.5;
    scene.add(spotFace);

    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- LE SOL ---
    const floorY = -14; // Sol bas pour dégager la vue
    
    const grid = new THREE.GridHelper(400, 80, 0x666666, 0x111111);
    grid.position.y = floorY;
    scene.add(grid);
    
    const floorPlane = new THREE.Mesh(
        new THREE.PlaneGeometry(1000, 1000), 
        new THREE.MeshBasicMaterial({ color: 0x020202 }) 
    );
    floorPlane.rotation.x = -Math.PI / 2;
    floorPlane.position.y = floorY - 0.1;
    scene.add(floorPlane);

    // --- ROBOT (HÉROS - GROS & PROCHE) ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(1.8, 1.8, 1.8); // Très gros
    // Position Z=10 : Il est très en avant, devant le plan "virtuel" du titre
    robotGroup.position.set(0, floorY + 6.5, 10); 
    spotFace.target = robotGroup;

    // Matériau émissif pour qu'il brille un peu lui-même
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2, emissive: 0x222222 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.2 });
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
    // --- SYSTÈME LASER ---
    // =========================================================
    
    const hubY = 10; 
    const laserHub = new THREE.Group();
    laserHub.position.set(0, hubY, 0);
    scene.add(laserHub);

    const hubMesh = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 0.5, 1, 32), new THREE.MeshBasicMaterial({color: 0x111111}));
    laserHub.add(hubMesh);

    const lasers = [];
    const colors = [0x00FF00, 0x00FFFF, 0x0055FF, 0xFF00FF, 0xFFFF00, 0xFF3300, 0xFFFFFF];

    for(let i=0; i<20; i++) { // 20 Lasers total
        const color = colors[Math.floor(Math.random()*colors.length)];
        
        // 1. FAISCEAU
        const coreGeo = new THREE.CylinderGeometry(0.04, 0.04, 1, 6, 1, true); 
        coreGeo.translate(0, 0.5, 0); coreGeo.rotateX(Math.PI / 2); 
        const coreMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
        const beamCore = new THREE.Mesh(coreGeo, coreMat);
        scene.add(beamCore);

        const glowGeo = new THREE.CylinderGeometry(0.15, 0.5, 1, 8, 1, true); 
        glowGeo.translate(0, 0.5, 0); glowGeo.rotateX(Math.PI / 2); 
        const glowMat = new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
        const beamGlow = new THREE.Mesh(glowGeo, glowMat);
        scene.add(beamGlow);

        // 2. IMPACT
        const dotCoreGeo = new THREE.CircleGeometry(0.6, 16); 
        const dotCoreMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF, transparent: true, opacity: 0, blending: THREE.AdditiveBlending });
        const dotCore = new THREE.Mesh(dotCoreGeo, dotCoreMat);
        dotCore.rotation.x = -Math.PI / 2; dotCore.position.y = floorY + 0.06;
        scene.add(dotCore);

        const dotGlowGeo = new THREE.CircleGeometry(1.8, 32); 
        const dotGlowMat = new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false });
        const dotGlow = new THREE.Mesh(dotGlowGeo, dotGlowMat);
        dotGlow.rotation.x = -Math.PI / 2;
        scene.add(dotGlow);

        // Initialisation loin
        lasers.push({
            beamCore, beamGlow, dotCore, dotGlow,
            currentPos: new THREE.Vector3(50, floorY + 0.05, 50),
            targetPos: new THREE.Vector3(50, floorY + 0.05, 50),
            speed: 0.01 + Math.random() * 0.02, // TRÈS LENT
            isActive: false, // Éteint par défaut
            activationTime: Math.random() * 100
        });
    }

    // --- ANIMATION ---
    let time = 0;
    // Cible robot : Z=12 pour être bien devant
    let targetPos = new THREE.Vector3(0, floorY + 6.5, 12); 
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.005; // VITESSE GLOBALE RALENTIE

        // --- ANIMATION LASERS (Limiteur de nombre) ---
        // On compte combien sont allumés
        const activeCount = lasers.filter(l => l.isActive).length;
        const maxActive = 8; // Pas plus de 8 en même temps

        lasers.forEach((l) => {
            // Gestion Activité (Allumage/Extinction progressif)
            if (Math.random() > 0.99) {
                if(l.isActive) l.isActive = false; // On éteint
                else if (activeCount < maxActive) l.isActive = true; // On allume si de la place
            }

            // Transition Opacité douce
            const targetOp = l.isActive ? 1.0 : 0.0;
            const currentOp = l.beamGlow.material.opacity;
            // Transition lente (0.02)
            const newOp = currentOp + (targetOp - currentOp) * 0.02;

            l.beamCore.material.opacity = newOp * 0.9;
            l.beamGlow.material.opacity = newOp * 0.2; // Halo discret
            l.dotCore.material.opacity = newOp * 0.8;
            l.dotGlow.material.opacity = newOp * 0.4;

            // Mouvement (Si target atteinte, on change)
            if (l.currentPos.distanceTo(l.targetPos) < 2) {
                let tx, tz;
                // GRANDE ZONE D'EXCLUSION ROBOT (Rayon 20)
                do {
                    tx = (Math.random()-0.5) * 120;
                    tz = (Math.random()-0.5) * 80;
                } while (Math.abs(tx) < 20 && Math.abs(tz) < 15); 

                l.targetPos.set(tx, floorY + 0.05, tz);
            }
            l.currentPos.lerp(l.targetPos, l.speed);

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
                if (time * 2 >= script[introIndex].t) { // time*2 car j'ai ralenti time
                    const act = script[introIndex].a;
                    if(act=="hide") robotGroup.position.x = -40;
                    if(act=="enter") targetPos.set(0, floorY+6.5, 12);
                    if(act=="look") { smoothRotate(robotGroup, 'y', -0.5, 0.05); }
                    if(act=="surprise") { robotGroup.position.y += 1.0; head.rotation.x = -0.4; }
                    if(act=="wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++;
                }
            } else if (time * 2 > 15) { robotState = 'moving'; pickNewTarget(); nextEvent = time + 3; }
            if(introIndex>0) robotGroup.position.lerp(targetPos, 0.02);
        }
        else if (robotState === 'moving') {
            robotGroup.position.y = (floorY + 6.5) + Math.sin(time*4)*0.2;
            robotGroup.position.lerp(targetPos, 0.02);
            
            // Regarde la caméra ou le public
            const lookTarget = new THREE.Vector3(0, 5, 50); // Regarde vers la caméra
            robotGroup.lookAt(lookTarget);
            
            if(robotGroup.position.distanceTo(targetPos)<1.0) pickNewTarget();
            
            if(time > nextEvent) {
                const r = Math.random();
                // PARLE PLUS SOUVENT (0.5 au lieu de 0.2)
                if(r < 0.5) { 
                    robotState='speaking'; 
                    showBubble(getUniqueMessage(config.mode), 4000); 
                    // S'arrête pour parler
                    setTimeout(()=>{robotState='moving';pickNewTarget();}, 4000); 
                } else {
                    pickNewTarget();
                }
                nextEvent = time + 3 + Math.random()*3;
            }
        }
        else if (robotState === 'speaking') {
            // Petite animation de parole
            mouth.scale.set(1, 1+Math.sin(time*30)*0.5, 1);
            // Regarde bien la caméra
            robotGroup.lookAt(new THREE.Vector3(0, 5, 50));
        }
        // ... (Explosion/Reassembling identiques) ...

        if(bubble && bubble.style.opacity == 1) {
            const pos = robotGroup.position.clone(); pos.y += 3.5; 
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
        // Zone de déplacement : Devant la scène
        targetPos.set(
            (Math.random()-0.5) * 30, // Largeur modérée
            floorY + 6.5, 
            10 + (Math.random()-0.5) * 5 // Profondeur (reste proche Z=10)
        ); 
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
    animate();
}
