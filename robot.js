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
    scene.fog = new THREE.FogExp2(0x000000, 0.015);
    
    // CAMÉRA : Angle ajusté pour remonter l'horizon
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 300);
    camera.position.set(0, 3, 32); 
    // On regarde plus haut (Y=5) pour que le sol remplisse l'écran
    camera.lookAt(0, 5, 0); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // --- LUMIÈRES ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.5); 
    scene.add(ambientLight);
    
    // Spot suiveur pour le robot
    const spotRobot = new THREE.SpotLight(0xffffff, 25);
    spotRobot.position.set(0, 25, 20);
    spotRobot.angle = 0.5;
    spotRobot.penumbra = 0.5;
    spotRobot.decay = 1.5;
    scene.add(spotRobot);

    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- LE SOL (IMMENSE & REMONTÉ) ---
    const floorY = -10; 
    
    // Grille très large pour la perspective
    const grid = new THREE.GridHelper(400, 80, 0x555555, 0x111111);
    grid.position.y = floorY;
    scene.add(grid);
    
    // Plan noir géant pour éviter le trait blanc au fond
    const floorPlane = new THREE.Mesh(
        new THREE.PlaneGeometry(1000, 1000), 
        new THREE.MeshBasicMaterial({ color: 0x020202 }) 
    );
    floorPlane.rotation.x = -Math.PI / 2;
    floorPlane.position.y = floorY - 0.1;
    scene.add(floorPlane);

    // --- ROBOT (LIBÉRÉ) ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(1.6, 1.6, 1.6); // Robot plus imposant
    robotGroup.position.set(0, floorY + 5.5, 5); // Commence plus près de la caméra (Z=5)
    spotRobot.target = robotGroup; // Le spot le suit

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

    for(let i=0; i<24; i++) { 
        const color = colors[Math.floor(Math.random()*colors.length)];
        
        // 1. FAISCEAU
        const coreGeo = new THREE.CylinderGeometry(0.04, 0.04, 1, 6, 1, true); 
        coreGeo.translate(0, 0.5, 0); coreGeo.rotateX(Math.PI / 2); 
        const coreMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false });
        const beamCore = new THREE.Mesh(coreGeo, coreMat);
        scene.add(beamCore);

        const glowGeo = new THREE.CylinderGeometry(0.15, 0.5, 1, 8, 1, true); 
        glowGeo.translate(0, 0.5, 0); glowGeo.rotateX(Math.PI / 2); 
        const glowMat = new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.15, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
        const beamGlow = new THREE.Mesh(glowGeo, glowMat);
        scene.add(beamGlow);

        // 2. IMPACT AU SOL
        const dotCoreGeo = new THREE.CircleGeometry(0.6, 16); 
        const dotCoreMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending });
        const dotCore = new THREE.Mesh(dotCoreGeo, dotCoreMat);
        dotCore.rotation.x = -Math.PI / 2; dotCore.position.y = floorY + 0.06;
        scene.add(dotCore);

        const dotGlowGeo = new THREE.CircleGeometry(1.8, 32); 
        const dotGlowMat = new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false });
        const dotGlow = new THREE.Mesh(dotGlowGeo, dotGlowMat);
        dotGlow.rotation.x = -Math.PI / 2;
        scene.add(dotGlow);

        // Positionnement initial
        let startX = (Math.random()-0.5) * 80;
        let startZ = (Math.random()-0.5) * 60;

        lasers.push({
            beamCore, beamGlow, dotCore, dotGlow,
            color: color,
            currentPos: new THREE.Vector3(startX, floorY + 0.05, startZ),
            targetPos: new THREE.Vector3(startX, floorY + 0.05, startZ),
            speed: 0.03 + Math.random() * 0.05, 
            strobeSpeed: 10 + Math.random() * 20,
            strobeOffset: Math.random() * 100
        });
    }

    // --- ANIMATION ---
    let time = 0;
    let targetPos = new THREE.Vector3(0, floorY + 5.5, 5); // Cible initiale robot
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;

        // --- ANIMATION LASERS ---
        lasers.forEach((l) => {
            let flash = Math.sin(time * l.strobeSpeed + l.strobeOffset); 
            flash = (flash + 1) / 2; flash = Math.pow(flash, 3); 
            const visibility = 0.1 + flash * 0.9;

            l.beamCore.material.opacity = visibility * 0.9;
            l.beamGlow.material.opacity = visibility * 0.25;
            l.dotCore.material.opacity = visibility;
            l.dotGlow.material.opacity = visibility * 0.5;

            // Nouvelle cible si atteinte
            if (l.currentPos.distanceTo(l.targetPos) < 1) {
                // Zone très large pour les lasers
                l.targetPos.set((Math.random()-0.5) * 120, floorY + 0.05, (Math.random()-0.5) * 80);
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

        // --- ROBOT LIBRE ---
        if (robotState === 'intro') {
            const script = [{t:0, a:"hide"}, {t:1, a:"enter"}, {t:4, a:"look"}, {t:7, a:"surprise"}, {t:10, a:"wave"}];
            if (introIndex < script.length) {
                if (time >= script[introIndex].t) {
                    const act = script[introIndex].a;
                    if(act=="hide") robotGroup.position.set(-40, floorY+5.5, -10);
                    if(act=="enter") targetPos.set(0, floorY+5.5, 5); // Avance vers le centre
                    if(act=="look") { smoothRotate(robotGroup, 'y', -0.5, 0.05); smoothRotate(head, 'y', 0.8, 0.05); }
                    if(act=="surprise") { robotGroup.position.y += 1.0; head.rotation.x = -0.4; } // Saute
                    if(act=="wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++;
                }
            } else if (time > 15) { robotState = 'moving'; pickNewTarget(); nextEvent = time + 3; }
            if(introIndex>0) robotGroup.position.lerp(targetPos, 0.03);
        }
        else if (robotState === 'moving') {
            // Flottement
            robotGroup.position.y = (floorY + 5.5) + Math.sin(time*3)*0.2;
            
            // Déplacement fluide vers la cible
            robotGroup.position.lerp(targetPos, 0.015);
            
            // Le robot regarde où il va
            const lookTarget = targetPos.clone();
            lookTarget.y = robotGroup.position.y;
            robotGroup.lookAt(lookTarget);
            
            if(robotGroup.position.distanceTo(targetPos)<1.0) pickNewTarget();
            
            if(time > nextEvent) {
                const r = Math.random();
                // Explosion de joie / Danse
                if(r<0.3) { 
                    robotState='speaking'; 
                    showBubble(getUniqueMessage(config.mode), 4000); 
                    setTimeout(()=>{robotState='moving';pickNewTarget();}, 4000); 
                }
                else { 
                    // Changement de direction simple
                    pickNewTarget(); 
                }
                nextEvent = time + 4 + Math.random()*4;
            }
        }
        else if (robotState === 'speaking') { 
            // Animation quand il parle (saute sur place)
            robotGroup.position.y = (floorY + 5.5) + Math.abs(Math.sin(time*10))*0.5;
            mouth.scale.set(1, 1+Math.sin(time*20)*0.5, 1); 
        }

        if(bubble && bubble.style.opacity == 1) {
            const pos = robotGroup.position.clone(); pos.y += 3.0; // Bulle plus haute
            pos.project(camera);
            const x = (pos.x * .5 + .5) * width; const y = (pos.y * -.5 + .5) * height;
            bubble.style.left = Math.max(100, Math.min(width-100, x)) + 'px';
            bubble.style.top = Math.max(50, y - 90) + 'px';
        }
        renderer.render(scene, camera);
    }

    function smoothRotate(obj, axis, target, speed) { obj.rotation[axis] += (target - obj.rotation[axis]) * speed; }
    function showBubble(txt, dur) { bubble.innerText = txt; bubble.style.opacity = 1; setTimeout(() => bubble.style.opacity=0, dur); }
    
    // NOUVELLE LOGIQUE DE DÉPLACEMENT DU ROBOT
    function pickNewTarget() { 
        // Le robot peut aller partout sur le devant de la scène
        // X : -20 à 20 (Largeur)
        // Z : -5 à 15 (Profondeur : vient vers la caméra ou recule un peu)
        targetPos.set(
            (Math.random()-0.5) * 40, 
            floorY + 5.5, 
            (Math.random()-0.5) * 20 + 5 
        ); 
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
    animate();
}
