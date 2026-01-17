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
    // Brouillard très léger pour laisser voir la grille au loin
    scene.fog = new THREE.FogExp2(0x000000, 0.008); 
    
    // CAMÉRA
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 300);
    camera.position.set(0, 5, 45); 
    camera.lookAt(0, -2, 0); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // --- LUMIÈRES ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.0); 
    scene.add(ambientLight);
    
    // Spot Visage Robot
    const spotFace = new THREE.SpotLight(0xffffff, 30);
    spotFace.position.set(0, 15, 40); 
    spotFace.angle = 0.4;
    scene.add(spotFace);

    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- LE SOL (PETITS CARRÉS) ---
    const floorY = -14;
    
    // Grille dense : 1000 unités de large, 300 divisions = petits carrés
    const grid = new THREE.GridHelper(1000, 300, 0x666666, 0x222222);
    grid.position.y = floorY;
    scene.add(grid);
    
    // Plan noir dessous pour l'opacité
    const floorPlane = new THREE.Mesh(
        new THREE.PlaneGeometry(1000, 1000), 
        new THREE.MeshBasicMaterial({ color: 0x050505 }) 
    );
    floorPlane.rotation.x = -Math.PI / 2;
    floorPlane.position.y = floorY - 0.1;
    scene.add(floorPlane);

    // --- ROBOT (MOBILE) ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(1.8, 1.8, 1.8); 
    robotGroup.position.set(0, floorY + 6.5, 10); 
    spotFace.target = robotGroup;

    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3, emissive: 0x222222 });
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
    // --- SYSTÈME LASER (VISIBLE) ---
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
        
        // 1. FAISCEAU (Plus opaque et plus épais)
        const coreGeo = new THREE.CylinderGeometry(0.05, 0.05, 1, 6, 1, true); 
        coreGeo.translate(0, 0.5, 0); coreGeo.rotateX(Math.PI / 2); 
        const coreMat = new THREE.MeshBasicMaterial({ 
            color: 0xFFFFFF, transparent: true, opacity: 1.0, // COEUR BLANC SOLIDE
            blending: THREE.AdditiveBlending, depthWrite: false
        });
        const beamCore = new THREE.Mesh(coreGeo, coreMat);
        scene.add(beamCore);

        // Halo plus visible
        const glowGeo = new THREE.CylinderGeometry(0.2, 0.6, 1, 8, 1, true); 
        glowGeo.translate(0, 0.5, 0); glowGeo.rotateX(Math.PI / 2); 
        const glowMat = new THREE.MeshBasicMaterial({ 
            color: color, transparent: true, 
            opacity: 0.5, // HALO BIEN VISIBLE (était 0.15)
            blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide
        });
        const beamGlow = new THREE.Mesh(glowGeo, glowMat);
        scene.add(beamGlow);

        // 2. IMPACT
        const dotCoreGeo = new THREE.CircleGeometry(0.7, 16); 
        const dotCoreMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF, transparent: true, opacity: 1.0, blending: THREE.AdditiveBlending });
        const dotCore = new THREE.Mesh(dotCoreGeo, dotCoreMat);
        dotCore.rotation.x = -Math.PI / 2; dotCore.position.y = floorY + 0.06;
        scene.add(dotCore);

        const dotGlowGeo = new THREE.CircleGeometry(2.0, 32); 
        const dotGlowMat = new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending, depthWrite: false });
        const dotGlow = new THREE.Mesh(dotGlowGeo, dotGlowMat);
        dotGlow.rotation.x = -Math.PI / 2;
        scene.add(dotGlow);

        // Init positions
        let startX, startZ;
        do {
            startX = (Math.random()-0.5) * 80;
            startZ = (Math.random()-0.5) * 60;
        } while (Math.abs(startX) < 15);

        lasers.push({
            beamCore, beamGlow, dotCore, dotGlow,
            color: color,
            currentPos: new THREE.Vector3(startX, floorY + 0.05, startZ),
            targetPos: new THREE.Vector3(startX, floorY + 0.05, startZ),
            speed: 0.02 + Math.random() * 0.03, 
            strobeSpeed: 8 + Math.random() * 15,
            strobeOffset: Math.random() * 100
        });
    }

    // --- ANIMATION ---
    let time = 0;
    let targetPos = new THREE.Vector3(0, floorY + 6.5, 10); 
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;

        // --- ANIMATION LASERS ---
        const maxActive = 8;
        const currentActive = lasers.filter(l => l.isActive).length;

        lasers.forEach((l) => {
            // Gestion ON/OFF plus dynamique
            if(Math.random() > 0.99) { 
                if(l.isActive) l.isActive = false;
                else if(currentActive < maxActive) {
                    l.isActive = true;
                    let tx, tz;
                    do { // Cible toujours loin du robot
                        tx = (Math.random()-0.5) * 160; // Très large
                        tz = (Math.random()-0.5) * 100;
                    } while (Math.abs(tx) < 25); 
                    l.targetPos.set(tx, floorY+0.05, tz);
                }
            }

            // Fondu rapide pour qu'on les voit s'allumer
            const targetOp = l.isActive ? 1.0 : 0.0;
            const currentOp = l.beamGlow.material.opacity;
            // Transition plus rapide (0.05) pour plus de dynamisme
            const newOp = currentOp + (targetOp - currentOp) * 0.05;

            // Application de l'opacité (valeurs boostées)
            l.beamCore.material.opacity = newOp * 1.0; // Coeur solide
            l.beamGlow.material.opacity = newOp * 0.5; // Halo visible
            l.dotCore.material.opacity = newOp * 1.0;
            l.dotGlow.material.opacity = newOp * 0.6;

            l.currentPos.lerp(l.targetPos, l.speed);

            l.dotCore.position.copy(l.currentPos); l.dotCore.position.y = floorY + 0.06;
            l.dotGlow.position.copy(l.currentPos); l.dotGlow.position.y = floorY + 0.05;
            
            const source = new THREE.Vector3(0, hubY, 0);
            l.beamCore.position.copy(source); l.beamCore.lookAt(l.dotCore.position);
            l.beamGlow.position.copy(source); l.beamGlow.lookAt(l.dotGlow.position);
            
            const dist = source.distanceTo(l.dotCore.position);
            l.beamCore.scale.z = dist; l.beamGlow.scale.z = dist;
        });

        // --- ROBOT (MOUVEMENT AMPLIFIÉ) ---
        if (robotState === 'intro') {
            const script = [{t:0, a:"hide"}, {t:1, a:"enter"}, {t:4, a:"look"}, {t:7, a:"surprise"}, {t:10, a:"wave"}];
            if (introIndex < script.length) {
                if (time * 2 >= script[introIndex].t) { 
                    const act = script[introIndex].a;
                    if(act=="hide") robotGroup.position.set(-45, floorY+6.5, 10);
                    if(act=="enter") targetPos.set(0, floorY+6.5, 10);
                    if(act=="look") { smoothRotate(robotGroup, 'y', -0.5, 0.05); }
                    if(act=="surprise") { robotGroup.position.y += 1.0; head.rotation.x = -0.4; }
                    if(act=="wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++;
                }
            } else if (time * 2 > 15) { robotState = 'moving'; pickNewTarget(); nextEvent = time + 3; }
            if(introIndex>0) robotGroup.position.lerp(targetPos, 0.03);
        }
        else if (robotState === 'moving') {
            robotGroup.position.y = (floorY + 6.5) + Math.sin(time*4)*0.2;
            
            // VITESSE ROBOT PLUS RAPIDE (0.025 au lieu de 0.015)
            robotGroup.position.lerp(targetPos, 0.025);
            
            // Orientation fluide vers la cible
            const lookPos = targetPos.clone();
            lookPos.y = robotGroup.position.y;
            robotGroup.lookAt(lookPos);
            
            // Changement de cible fréquent
            if(robotGroup.position.distanceTo(targetPos)<2.0) pickNewTarget();
            
            if(time > nextEvent) {
                const r = Math.random();
                if(r < 0.6) { 
                    robotState='speaking'; 
                    showBubble(getUniqueMessage(config.mode), 4000); 
                    setTimeout(()=>{robotState='moving';pickNewTarget();}, 4000); 
                } else {
                    pickNewTarget();
                }
                nextEvent = time + 3 + Math.random()*3;
            }
        }
        else if (robotState === 'speaking') {
            mouth.scale.set(1, 1+Math.sin(time*25)*0.5, 1);
            // Regarde le public
            robotGroup.lookAt(new THREE.Vector3(0, 5, 50));
        }
        
        // ... (Explosion inchangée) ...
        else if (robotState === 'exploding') { parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += 0.1; p.userData.velocity.multiplyScalar(0.95); }); }
        else if (robotState === 'reassembling') { parts.forEach(p => { p.position.lerp(p.userData.origPos, 0.1); p.rotation.x *= 0.9; }); }


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
        // GRANDE ZONE DE DÉPLACEMENT
        // Le robot bouge beaucoup plus
        targetPos.set(
            (Math.random()-0.5) * 60, // Largeur +/- 30
            floorY + 6.5, 
            (Math.random()-0.5) * 20 + 5 // Profondeur -5 à +15
        ); 
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
    animate();
}
