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

// --- TEXTURE HALO ---
function createGlowTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 64; canvas.height = 64;
    const ctx = canvas.getContext('2d');
    const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    grad.addColorStop(0, 'rgba(255, 255, 255, 1)'); 
    grad.addColorStop(0.3, 'rgba(255, 255, 255, 0.4)');
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)'); 
    ctx.fillStyle = grad;
    ctx.fillRect(0,0,64,64);
    return new THREE.CanvasTexture(canvas);
}
const glowTexture = createGlowTexture();

function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    container.style.position = 'fixed'; container.style.top = '0'; container.style.left = '0';
    container.style.width = '100%'; container.style.height = '100%';
    container.style.zIndex = '1'; container.style.pointerEvents = 'none';
    
    const scene = new THREE.Scene();
    // Brouillard plus présent pour cacher la ligne d'horizon
    scene.fog = new THREE.FogExp2(0x000000, 0.035);
    
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 150);
    // CAMÉRA BAISSÉE (Y=2) pour remonter l'horizon visuel
    camera.position.set(0, 2, 24); 
    // Elle regarde un peu plus haut (Y=2) pour centrer l'action
    camera.lookAt(0, 2, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // --- LUMIÈRES ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); 
    scene.add(ambientLight);
    
    const spotRobot = new THREE.SpotLight(0xffffff, 8);
    spotRobot.position.set(0, 10, 10);
    scene.add(spotRobot);

    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- LE SOL (Remonté) ---
    // On le remonte à Y = -4 pour qu'il prenne plus de place
    const floorY = -4;
    
    // Grille plus grande
    const grid = new THREE.GridHelper(120, 60, 0x444444, 0x111111);
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
    robotGroup.scale.set(1.0, 1.0, 1.0); // Robot un peu plus gros
    robotGroup.position.y = floorY; // Posé pile sur le sol

    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.3 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const greyMat = new THREE.MeshStandardMaterial({ color: 0x888888 });
    
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat);
    head.scale.set(1.4, 1.0, 0.75);
    // Tête remontée pour être bien visible
    head.position.y = 2.2; 
    
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat);
    face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6); head.add(face);
    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat);
    mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);
    const leftEye = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat);
    leftEye.position.set(-0.35, 0.15, 1.05); head.add(leftEye);
    const rightEye = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat);
    rightEye.position.set(0.35, 0.15, 1.05); head.add(rightEye);

    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat);
    body.position.y = 1.1; // Corps remonté
    body.scale.set(0.95, 1.1, 0.8);
    const belt = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.03, 16, 32), greyMat);
    belt.rotation.x = Math.PI/2; body.add(belt);
    
    const leftArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    leftArm.position.set(-0.8, 1.2, 0); leftArm.rotation.z = 0.15;
    const rightArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    rightArm.position.set(0.8, 1.2, 0); rightArm.rotation.z = -0.15;

    [head, body, leftArm, rightArm].forEach(p => {
        p.userData = { origPos: p.position.clone(), origRot: p.rotation.clone(), velocity: new THREE.Vector3() };
        if(p!==head && p!==body) robotGroup.add(p);
    });
    robotGroup.add(head); robotGroup.add(body); robotGroup.add(leftArm); robotGroup.add(rightArm);
    scene.add(robotGroup);
    const parts = [head, body, leftArm, rightArm];

    // =========================================================
    // --- SYSTÈME LASER SPIDER ---
    // =========================================================
    
    const hubY = 16; // Source encore plus haute pour l'angle
    const laserHub = new THREE.Group();
    laserHub.position.set(0, hubY, 0);
    scene.add(laserHub);

    // Boîtier
    const hubMesh = new THREE.Mesh(new THREE.CylinderGeometry(2, 0.5, 1.5, 32), new THREE.MeshBasicMaterial({color: 0x111111}));
    laserHub.add(hubMesh);

    const lasers = [];
    const colors = [0x00FF00, 0x00FFFF, 0x0000FF, 0xFF00FF, 0xFFFF00, 0xFF0000];

    for(let i=0; i<24; i++) { 
        const color = colors[i % colors.length];
        
        // 1. FAISCEAU
        const beamGeo = new THREE.CylinderGeometry(0.03, 0.08, 1, 8, 1, true); // Plus fin en haut
        beamGeo.translate(0, 0.5, 0); 
        beamGeo.rotateX(Math.PI / 2); 
        
        const beamMat = new THREE.MeshBasicMaterial({ 
            color: color, 
            transparent: true, 
            opacity: 0.3, // Belle transparence
            blending: THREE.AdditiveBlending,
            depthWrite: false,
            side: THREE.DoubleSide
        });
        const beam = new THREE.Mesh(beamGeo, beamMat);
        scene.add(beam); 

        // 2. IMPACT AU SOL
        const spriteMat = new THREE.SpriteMaterial({ 
            map: glowTexture,
            color: color, 
            transparent: true, 
            opacity: 0.9,
            blending: THREE.AdditiveBlending
        });
        const dot = new THREE.Sprite(spriteMat);
        dot.scale.set(4, 4, 1); 
        dot.position.y = floorY + 0.05; 
        scene.add(dot);

        lasers.push({
            beam: beam,
            dot: dot,
            angleBase: (Math.PI * 2 / 24) * i,
            radiusMax: 10 + Math.random() * 25, // Rayon large pour remplir l'écran
            speed: 0.2 + Math.random() * 0.3,
            offset: Math.random() * 10
        });
    }

    // --- ANIMATION ---
    let time = 0;
    let targetPos = new THREE.Vector3(4, floorY, 0);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;

        // ANIMATION LASERS
        lasers.forEach((l, idx) => {
            const r = l.radiusMax + Math.sin(time * l.speed + l.offset) * 8;
            const a = l.angleBase + time * 0.1;

            // Coordonnées au sol
            const x = Math.cos(a) * r;
            const z = Math.sin(a) * (r * 0.6); // Ovale pour la perspective

            // 1. Déplacer l'impact
            l.dot.position.set(x, floorY + 0.05, z);
            l.dot.material.opacity = 0.6 + Math.sin(time * 3 + idx) * 0.3; // Scintillement
            
            // 2. Orienter faisceau
            l.beam.position.set(0, hubY, 0); 
            l.beam.lookAt(l.dot.position);   
            
            // 3. Étirer
            const dist = l.beam.position.distanceTo(l.dot.position);
            l.beam.scale.z = dist; 
        });

        laserHub.rotation.y = time * -0.05;

        // ROBOT (Ajusté au sol Y = -4)
        if (robotState === 'intro') {
            const script = [{t:0, a:"hide"}, {t:1, a:"enter"}, {t:4, a:"look"}, {t:7, a:"surprise"}, {t:10, a:"wave"}];
            if (introIndex < script.length) {
                if (time >= script[introIndex].t) {
                    const act = script[introIndex].a;
                    if(act=="hide") robotGroup.position.x = -25;
                    if(act=="enter") targetPos.set(4, floorY, 0);
                    if(act=="look") { smoothRotate(robotGroup, 'y', -0.5, 0.05); smoothRotate(head, 'y', 0.8, 0.05); }
                    if(act=="surprise") { robotGroup.position.y += 0.5; head.rotation.x = -0.3; }
                    if(act=="wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++;
                }
            } else if (time > 15) { robotState = 'moving'; pickNewTarget(); nextEvent = time + 3; }
            if(introIndex>0) robotGroup.position.lerp(targetPos, 0.02);
        }
        else if (robotState === 'moving') {
            robotGroup.position.y = floorY + Math.sin(time*2)*0.1;
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
            const pos = robotGroup.position.clone(); pos.y += 2.5; // Ajusté pour le robot plus grand
            pos.project(camera);
            const x = (pos.x * .5 + .5) * width; const y = (pos.y * -.5 + .5) * height;
            bubble.style.left = Math.max(100, Math.min(width-100, x)) + 'px';
            bubble.style.top = Math.max(50, y - 90) + 'px';
        }
        renderer.render(scene, camera);
    }

    function smoothRotate(obj, axis, target, speed) { obj.rotation[axis] += (target - obj.rotation[axis]) * speed; }
    function showBubble(txt, dur) { bubble.innerText = txt; bubble.style.opacity = 1; setTimeout(() => bubble.style.opacity=0, dur); }
    function pickNewTarget() { targetPos.set((Math.random()>0.5?1:-1)*(5+Math.random()*8), floorY, 0); }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
    animate();
}
