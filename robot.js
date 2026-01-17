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
    scene.fog = new THREE.FogExp2(0x000000, 0.02); 
    
    // CAMÉRA : Positionnée plus loin pour écraser la perspective
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 300);
    camera.position.set(0, 3, 35); 
    camera.lookAt(0, -5, 0); // Regarde vers le bas

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // --- LUMIÈRES ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); 
    scene.add(ambientLight);
    
    // Spot Robot
    const spotRobot = new THREE.SpotLight(0xffffff, 15);
    spotRobot.position.set(0, 15, 10);
    spotRobot.angle = 0.3;
    spotRobot.penumbra = 0.5;
    scene.add(spotRobot);

    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- LE SOL (POSITION BASSE) ---
    // On descend le sol très bas pour que la ligne d'horizon descende
    const floorY = -12;
    
    const grid = new THREE.GridHelper(150, 50, 0x444444, 0x111111);
    grid.position.y = floorY;
    scene.add(grid);
    
    const floorPlane = new THREE.Mesh(
        new THREE.PlaneGeometry(400, 400),
        new THREE.MeshBasicMaterial({ color: 0x020202 }) 
    );
    floorPlane.rotation.x = -Math.PI / 2;
    floorPlane.position.y = floorY - 0.1;
    scene.add(floorPlane);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(1.1, 1.1, 1.1); // Robot bien visible
    robotGroup.position.y = floorY + 4.5; // Ajusté au nouveau sol
    spotRobot.target = robotGroup;

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
    // --- SYSTÈME LASER CHAOTIQUE ---
    // =========================================================
    
    // Source positionnée plus bas pour éviter le titre
    const hubY = 10; 
    const laserHub = new THREE.Group();
    laserHub.position.set(0, hubY, 0);
    scene.add(laserHub);

    // Cache source
    const hubMesh = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 0.2, 1, 16), new THREE.MeshBasicMaterial({color: 0x050505}));
    laserHub.add(hubMesh);

    const lasers = [];
    // Couleurs plus variées
    const colors = [0x00FF00, 0x00FFFF, 0x0000FF, 0xFF00FF, 0xFFFF00, 0xFF0000, 0xFFFFFF];

    // 24 Lasers indépendants
    for(let i=0; i<24; i++) { 
        const color = colors[Math.floor(Math.random()*colors.length)];
        
        // --- 1. LE FAISCEAU ---
        // Cœur fin
        const coreGeo = new THREE.CylinderGeometry(0.015, 0.015, 1, 6, 1, true); 
        coreGeo.translate(0, 0.5, 0); coreGeo.rotateX(Math.PI / 2); 
        const coreMat = new THREE.MeshBasicMaterial({ 
            color: 0xFFFFFF, transparent: true, opacity: 0, // Commence éteint
            blending: THREE.AdditiveBlending, depthWrite: false
        });
        const beamCore = new THREE.Mesh(coreGeo, coreMat);
        scene.add(beamCore);

        // Halo Large
        const glowGeo = new THREE.CylinderGeometry(0.04, 0.15, 1, 8, 1, true); 
        glowGeo.translate(0, 0.5, 0); glowGeo.rotateX(Math.PI / 2); 
        const glowMat = new THREE.MeshBasicMaterial({ 
            color: color, transparent: true, opacity: 0, // Commence éteint
            blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide
        });
        const beamGlow = new THREE.Mesh(glowGeo, glowMat);
        scene.add(beamGlow);

        // --- 2. L'IMPACT AU SOL (PLUS PETIT) ---
        // Point brillant
        const dotCoreGeo = new THREE.CircleGeometry(0.2, 16); // Tout petit
        const dotCoreMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF, transparent: true, opacity: 0, blending: THREE.AdditiveBlending });
        const dotCore = new THREE.Mesh(dotCoreGeo, dotCoreMat);
        dotCore.rotation.x = -Math.PI / 2;
        scene.add(dotCore);

        // Halo Sol
        const dotGlowGeo = new THREE.CircleGeometry(0.8, 32); // Réduit drastiquement (était 2.5)
        const dotGlowMat = new THREE.MeshBasicMaterial({ 
            color: color, transparent: true, opacity: 0, 
            blending: THREE.AdditiveBlending, depthWrite: false 
        });
        const dotGlow = new THREE.Mesh(dotGlowGeo, dotGlowMat);
        dotGlow.rotation.x = -Math.PI / 2;
        scene.add(dotGlow);

        // Initialisation position aléatoire
        const startX = (Math.random()-0.5) * 50;
        const startZ = (Math.random()-0.5) * 30;

        lasers.push({
            beamCore, beamGlow, dotCore, dotGlow,
            color: color,
            currentPos: new THREE.Vector3(startX, floorY + 0.05, startZ),
            targetPos: new THREE.Vector3(startX, floorY + 0.05, startZ),
            speed: 0.05 + Math.random() * 0.1, // Vitesse de déplacement
            isOn: Math.random() > 0.5, // État initial
            timer: Math.random() * 100
        });
    }

    // --- ANIMATION ---
    let time = 0;
    let targetPos = new THREE.Vector3(4, floorY + 4.5, 0);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;

        // --- LOGIQUE LASER CHAOS ---
        lasers.forEach((l) => {
            // 1. GESTION DU STROBOSCOPE / CLIGNOTEMENT
            // On change d'état (ON/OFF) aléatoirement
            if(Math.random() > 0.96) {
                l.isOn = !l.isOn;
                // Parfois on change de cible quand on clignote
                l.targetPos.set(
                    (Math.random()-0.5) * 60, // Largeur aléatoire
                    floorY + 0.05,
                    (Math.random()-0.5) * 40 // Profondeur aléatoire
                );
            }

            // Gestion de l'opacité (Transition douce ou flash)
            const targetOpacity = l.isOn ? 1 : 0;
            const currentOpacity = l.beamGlow.material.opacity;
            // Lerp pour l'opacité
            const newOpacity = currentOpacity + (targetOpacity - currentOpacity) * 0.1;

            l.beamCore.material.opacity = newOpacity * 0.9;
            l.beamGlow.material.opacity = newOpacity * 0.25; // Halo transparent
            l.dotCore.material.opacity = newOpacity * 0.9;
            l.dotGlow.material.opacity = newOpacity * 0.5;

            // 2. MOUVEMENT (Interpolation vers la cible aléatoire)
            l.currentPos.lerp(l.targetPos, l.speed);

            // Mise à jour positions objets
            l.dotCore.position.copy(l.currentPos);
            l.dotCore.position.y += 0.01; // Anti z-fighting
            l.dotGlow.position.copy(l.currentPos);
            
            // Orientation Faisceaux
            const source = new THREE.Vector3(0, hubY, 0);
            
            l.beamCore.position.copy(source);
            l.beamCore.lookAt(l.dotCore.position);
            
            l.beamGlow.position.copy(source);
            l.beamGlow.lookAt(l.dotGlow.position);
            
            // Étirement
            const dist = source.distanceTo(l.dotCore.position);
            l.beamCore.scale.z = dist;
            l.beamGlow.scale.z = dist;
        });

        // ROBOT (Suivi et Animation)
        if (robotState === 'intro') {
            const script = [{t:0, a:"hide"}, {t:1, a:"enter"}, {t:4, a:"look"}, {t:7, a:"surprise"}, {t:10, a:"wave"}];
            if (introIndex < script.length) {
                if (time >= script[introIndex].t) {
                    const act = script[introIndex].a;
                    if(act=="hide") robotGroup.position.x = -30;
                    if(act=="enter") targetPos.set(4, floorY+4.5, 0);
                    if(act=="look") { smoothRotate(robotGroup, 'y', -0.5, 0.05); smoothRotate(head, 'y', 0.8, 0.05); }
                    if(act=="surprise") { robotGroup.position.y += 0.5; head.rotation.x = -0.3; }
                    if(act=="wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++;
                }
            } else if (time > 15) { robotState = 'moving'; pickNewTarget(); nextEvent = time + 3; }
            if(introIndex>0) robotGroup.position.lerp(targetPos, 0.02);
        }
        else if (robotState === 'moving') {
            robotGroup.position.y = (floorY + 4.5) + Math.sin(time*2)*0.1;
            robotGroup.position.lerp(targetPos, 0.02);
            smoothRotate(robotGroup, 'y', (targetPos.x - robotGroup.position.x)*0.05, 0.05);
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
            const pos = robotGroup.position.clone(); pos.y += 2.5;
            pos.project(camera);
            const x = (pos.x * .5 + .5) * width; const y = (pos.y * -.5 + .5) * height;
            bubble.style.left = Math.max(100, Math.min(width-100, x)) + 'px';
            bubble.style.top = Math.max(50, y - 90) + 'px';
        }
        renderer.render(scene, camera);
    }

    function smoothRotate(obj, axis, target, speed) { obj.rotation[axis] += (target - obj.rotation[axis]) * speed; }
    function showBubble(txt, dur) { bubble.innerText = txt; bubble.style.opacity = 1; setTimeout(() => bubble.style.opacity=0, dur); }
    function pickNewTarget() { targetPos.set((Math.random()>0.5?1:-1)*(5+Math.random()*8), floorY+4.5, 0); }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
    animate();
}
