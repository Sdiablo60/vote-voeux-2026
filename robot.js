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

// --- INIT SÉCURISÉE ---
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
    
    // CAMÉRA
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 200);
    camera.position.set(0, 5, 26); 
    camera.lookAt(0, -2, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // --- LUMIÈRES ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); 
    scene.add(ambientLight);
    
    // Spot puissant dédié au robot pour qu'il reste visible
    const spotRobot = new THREE.SpotLight(0xffffff, 12);
    spotRobot.position.set(0, 15, 8);
    spotRobot.angle = 0.4;
    spotRobot.penumbra = 0.5;
    scene.add(spotRobot);

    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- LE SOL ---
    const floorY = -8;
    const grid = new THREE.GridHelper(100, 40, 0x444444, 0x111111);
    grid.position.y = floorY;
    scene.add(grid);
    
    const floorPlane = new THREE.Mesh(
        new THREE.PlaneGeometry(300, 300),
        new THREE.MeshBasicMaterial({ color: 0x050505 }) 
    );
    floorPlane.rotation.x = -Math.PI / 2;
    floorPlane.position.y = floorY - 0.05;
    scene.add(floorPlane);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(1.0, 1.0, 1.0); 
    robotGroup.position.y = floorY + 4; 
    spotRobot.target = robotGroup; // Le spot suit le robot

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
    // --- SYSTÈME LASER STROBOSCOPIQUE ---
    // =========================================================
    
    // CORRECTION 1 : Source abaissée pour ne pas être cachée par le titre
    const hubY = 11; 
    const laserHub = new THREE.Group();
    laserHub.position.set(0, hubY, 0);
    scene.add(laserHub);

    // Boîtier Central
    const hubMesh = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 0.5, 1.5, 32), new THREE.MeshBasicMaterial({color: 0x111111}));
    laserHub.add(hubMesh);

    const lasers = [];
    const colors = [0x00FF00, 0x00FFFF, 0x0000FF, 0xFF00FF, 0xFFFF00, 0xFF0000];

    for(let i=0; i<24; i++) { 
        const color = colors[i % colors.length];
        
        // --- 1. LE FAISCEAU ---
        
        // A. Cœur Blanc
        const coreGeo = new THREE.CylinderGeometry(0.02, 0.02, 1, 8, 1, true); 
        coreGeo.translate(0, 0.5, 0); coreGeo.rotateX(Math.PI / 2); 
        const coreMat = new THREE.MeshBasicMaterial({ 
            color: 0xFFFFFF, transparent: true, opacity: 0.8, // Opacité de base
            blending: THREE.AdditiveBlending, depthWrite: false
        });
        const beamCore = new THREE.Mesh(coreGeo, coreMat);
        scene.add(beamCore);

        // B. Halo Coloré (CORRECTION 2 : Plus transparent pour voir le robot)
        const glowGeo = new THREE.CylinderGeometry(0.08, 0.25, 1, 8, 1, true); 
        glowGeo.translate(0, 0.5, 0); glowGeo.rotateX(Math.PI / 2); 
        const glowMat = new THREE.MeshBasicMaterial({ 
            color: color, transparent: true, 
            opacity: 0.15, // Beaucoup plus transparent par défaut
            blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide
        });
        const beamGlow = new THREE.Mesh(glowGeo, glowMat);
        scene.add(beamGlow);

        // --- 2. L'IMPACT AU SOL ---
        // A. Point Chaud
        const dotCoreGeo = new THREE.CircleGeometry(0.4, 16);
        const dotCoreMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending });
        const dotCore = new THREE.Mesh(dotCoreGeo, dotCoreMat);
        dotCore.rotation.x = -Math.PI / 2; dotCore.position.y = floorY + 0.06;
        scene.add(dotCore);

        // B. Halo Sol
        const dotGlowGeo = new THREE.CircleGeometry(2.5, 32);
        const dotGlowMat = new THREE.MeshBasicMaterial({ 
            color: color, transparent: true, opacity: 0.4, 
            blending: THREE.AdditiveBlending, depthWrite: false 
        });
        const dotGlow = new THREE.Mesh(dotGlowGeo, dotGlowMat);
        dotGlow.rotation.x = -Math.PI / 2; dotGlow.position.y = floorY + 0.05; 
        scene.add(dotGlow);

        lasers.push({
            beamCore, beamGlow, dotCore, dotGlow,
            angleBase: (Math.PI * 2 / 24) * i,
            radiusMax: 10 + Math.random() * 20,
            speed: 0.2 + Math.random() * 0.3,
            offset: Math.random() * 10,
            // Facteur aléatoire pour le stroboscope
            strobeOffset: Math.random() * Math.PI * 2
        });
    }

    // --- ANIMATION ---
    let time = 0;
    let targetPos = new THREE.Vector3(4, floorY + 4, 0);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;

        // ANIMATION LASERS STROBOSCOPIQUES
        lasers.forEach((l, idx) => {
            // Mouvement
            const r = l.radiusMax + Math.sin(time * l.speed + l.offset) * 8;
            const a = l.angleBase + time * 0.15; 
            const x = Math.cos(a) * r;
            const z = Math.sin(a) * r * 0.6; 

            // --- CORRECTION 3 & 4 : STROBOSCOPE ET TAILLE FIXE ---
            // On calcule un facteur "flash" qui change brutalement
            // Utilisation de Math.pow pour rendre le clignotement plus sec
            let flash = Math.sin(time * 15 + l.strobeOffset) * 0.5 + 0.5;
            flash = Math.pow(flash, 5); // Rend le flash très court et intense
            
            // Ajout d'un chaos aléatoire pour que ça ne soit pas trop régulier
            if(Math.random() > 0.92) flash = 0.0; // Parfois éteint
            if(Math.random() > 0.98) flash = 1.0; // Parfois Flash Max

            // Application du flash sur l'OPACITÉ (pas la taille)
            // Le halo du faisceau varie de quasi invisible (0.05) à visible (0.3)
            l.beamGlow.material.opacity = 0.05 + flash * 0.25;
            // Le coeur varie aussi
            l.beamCore.material.opacity = 0.2 + flash * 0.8;

            // Impacts au sol : On ne change PRESQUE PAS la taille (scale), juste l'opacité
            l.dotCore.position.set(x, floorY + 0.06, z);
            l.dotGlow.position.set(x, floorY + 0.05, z);
            
            l.dotCore.material.opacity = 0.2 + flash * 0.8;
            l.dotGlow.material.opacity = 0.1 + flash * 0.5;
            
            // Variation de taille très subtile pour le côté "vivant"
            const subtleScale = 1.0 + flash * 0.1;
            l.dotGlow.scale.setScalar(2.5 * subtleScale);
            l.dotCore.scale.setScalar(0.4 * subtleScale);
            
            // Orientation et étirement
            const source = new THREE.Vector3(0, hubY, 0);
            l.beamCore.position.copy(source); l.beamCore.lookAt(l.dotCore.position);
            l.beamGlow.position.copy(source); l.beamGlow.lookAt(l.dotGlow.position);
            const dist = source.distanceTo(l.dotCore.position);
            l.beamCore.scale.z = dist; l.beamGlow.scale.z = dist;
        });

        laserHub.rotation.y = time * -0.1;

        // ROBOT
        if (robotState === 'intro') {
            const script = [{t:0, a:"hide"}, {t:1, a:"enter"}, {t:4, a:"look"}, {t:7, a:"surprise"}, {t:10, a:"wave"}];
            if (introIndex < script.length) {
                if (time >= script[introIndex].t) {
                    const act = script[introIndex].a;
                    if(act=="hide") robotGroup.position.x = -25;
                    if(act=="enter") targetPos.set(4, floorY+4, 0);
                    if(act=="look") { smoothRotate(robotGroup, 'y', -0.5, 0.05); smoothRotate(head, 'y', 0.8, 0.05); }
                    if(act=="surprise") { robotGroup.position.y += 0.5; head.rotation.x = -0.3; }
                    if(act=="wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++;
                }
            } else if (time > 15) { robotState = 'moving'; pickNewTarget(); nextEvent = time + 3; }
            if(introIndex>0) robotGroup.position.lerp(targetPos, 0.02);
        }
        else if (robotState === 'moving') {
            robotGroup.position.y = (floorY + 4) + Math.sin(time*2)*0.1;
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
    function pickNewTarget() { targetPos.set((Math.random()>0.5?1:-1)*(5+Math.random()*8), floorY+4, 0); }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
    animate();
}
