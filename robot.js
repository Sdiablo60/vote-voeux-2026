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
    scene.background = new THREE.Color(0x000000); 
    scene.fog = new THREE.FogExp2(0x000000, 0.01); // Brouillard léger pour fondre le sol
    
    // CAMÉRA
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 400);
    // On se place à hauteur d'homme (Y=4) mais assez reculé (Z=45)
    camera.position.set(0, 4, 45); 
    // On regarde vers le haut (Y=6) pour cadrer la source sous le titre
    camera.lookAt(0, 6, 0); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // --- LUMIÈRES ---
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.0); 
    scene.add(ambientLight);
    
    // Spot Visage Robot (Lumière de face très forte)
    const spotFace = new THREE.SpotLight(0xffffff, 50);
    spotFace.position.set(0, 10, 50); 
    spotFace.angle = 0.5;
    spotFace.penumbra = 0.2;
    scene.add(spotFace);

    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- LE SOL (INFINI) ---
    const floorY = -12;
    
    const grid = new THREE.GridHelper(3000, 400, 0x666666, 0x222222);
    grid.position.y = floorY;
    scene.add(grid);
    
    const floorPlane = new THREE.Mesh(
        new THREE.PlaneGeometry(3000, 3000), 
        new THREE.MeshBasicMaterial({ color: 0x050505 }) 
    );
    floorPlane.rotation.x = -Math.PI / 2;
    floorPlane.position.y = floorY - 0.1;
    scene.add(floorPlane);

    // --- ROBOT (STAR DU SHOW) ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(2.2, 2.2, 2.2); // Très Grand
    // Position initiale : Très en avant (Z=22), bien devant le plan des lasers
    robotGroup.position.set(0, floorY + 7.5, 22); 
    spotFace.target = robotGroup;

    // Matériaux optimisés pour la lumière
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
    // --- SYSTÈME LASER (SOLID BEAMS) ---
    // =========================================================
    
    // SOURCE HAUTE (18) : Pour être collée à la barre rouge
    const hubY = 18; 
    const laserHub = new THREE.Group();
    laserHub.position.set(0, hubY, 0);
    scene.add(laserHub);

    // Cache technique (cylindre noir en haut)
    const hubMesh = new THREE.Mesh(new THREE.CylinderGeometry(2, 0.5, 2, 32), new THREE.MeshBasicMaterial({color: 0x000000}));
    laserHub.add(hubMesh);

    const lasers = [];
    const colors = [0x00FF00, 0x00FFFF, 0x0055FF, 0xFF00FF, 0xFFFF00, 0xFF3300, 0xFFFFFF];

    for(let i=0; i<20; i++) { 
        const color = colors[Math.floor(Math.random()*colors.length)];
        
        // 1. CŒUR DU FAISCEAU (Le "Fil" blanc)
        // Opaque à 100% pour ne pas faire "plastique transparent"
        const coreGeo = new THREE.CylinderGeometry(0.08, 0.08, 1, 8, 1, true); 
        coreGeo.translate(0, 0.5, 0); coreGeo.rotateX(Math.PI / 2); 
        const coreMat = new THREE.MeshBasicMaterial({ 
            color: 0xFFFFFF, 
            transparent: false, // SOLIDE
            blending: THREE.AdditiveBlending // Mélange lumineux
        });
        const beamCore = new THREE.Mesh(coreGeo, coreMat);
        scene.add(beamCore);

        // 2. HALO DU FAISCEAU (La couleur autour)
        // Large et semi-transparent pour l'effet "Glow"
        const glowGeo = new THREE.CylinderGeometry(0.4, 1.0, 1, 8, 1, true); 
        glowGeo.translate(0, 0.5, 0); glowGeo.rotateX(Math.PI / 2); 
        const glowMat = new THREE.MeshBasicMaterial({ 
            color: color, 
            transparent: true, 
            opacity: 0.4, // Suffisant pour colorer sans cacher le fond
            blending: THREE.AdditiveBlending, 
            depthWrite: false, 
            side: THREE.DoubleSide
        });
        const beamGlow = new THREE.Mesh(glowGeo, glowMat);
        scene.add(beamGlow);

        // 3. IMPACT SOL
        const dotCoreGeo = new THREE.CircleGeometry(1.0, 32); 
        const dotCoreMat = new THREE.MeshBasicMaterial({ color: 0xFFFFFF, transparent: true, opacity: 1.0, blending: THREE.AdditiveBlending });
        const dotCore = new THREE.Mesh(dotCoreGeo, dotCoreMat);
        dotCore.rotation.x = -Math.PI / 2; dotCore.position.y = floorY + 0.06;
        scene.add(dotCore);

        const dotGlowGeo = new THREE.CircleGeometry(3.0, 32); 
        const dotGlowMat = new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending, depthWrite: false });
        const dotGlow = new THREE.Mesh(dotGlowGeo, dotGlowMat);
        dotGlow.rotation.x = -Math.PI / 2;
        scene.add(dotGlow);

        // Init positions larges
        let startX, startZ;
        do {
            startX = (Math.random()-0.5) * 120;
            startZ = (Math.random()-0.5) * 80;
        } while (Math.abs(startX) < 20);

        lasers.push({
            beamCore, beamGlow, dotCore, dotGlow,
            color: color,
            currentPos: new THREE.Vector3(startX, floorY + 0.05, startZ),
            targetPos: new THREE.Vector3(startX, floorY + 0.05, startZ),
            speed: 0.02 + Math.random() * 0.03, 
            strobeSpeed: 8 + Math.random() * 15,
            strobeOffset: Math.random() * 100,
            isActive: false
        });
    }

    // --- ANIMATION ---
    let time = 0;
    // Cible Initiale : En avant (Z=22)
    let targetPos = new THREE.Vector3(0, floorY + 7.5, 22); 
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.01;

        // --- LASERS (ON/OFF RAPIDE) ---
        const maxActive = 8;
        const currentActive = lasers.filter(l => l.isActive).length;

        lasers.forEach((l) => {
            // Logique d'activation
            if(Math.random() > 0.99) { 
                if(l.isActive) l.isActive = false;
                else if(currentActive < maxActive) {
                    l.isActive = true;
                    // Nouvelle cible aléatoire
                    let tx, tz;
                    do { 
                        tx = (Math.random()-0.5) * 200; 
                        tz = (Math.random()-0.5) * 150;
                    } while (Math.abs(tx) < 30); // Zone Robot préservée
                    l.targetPos.set(tx, floorY+0.05, tz);
                }
            }

            // Gestion Opacité (Flash)
            const targetOp = l.isActive ? 1.0 : 0.0;
            // Interpolation rapide
            l.beamCore.material.opacity += (targetOp - l.beamCore.material.opacity) * 0.1;
            l.beamGlow.material.opacity = l.beamCore.material.opacity * 0.4;
            l.dotCore.material.opacity = l.beamCore.material.opacity;
            l.dotGlow.material.opacity = l.beamCore.material.opacity * 0.6;

            // Mouvement
            l.currentPos.lerp(l.targetPos, l.speed);

            // Mise à jour visuelle
            l.dotCore.position.copy(l.currentPos); l.dotCore.position.y = floorY + 0.06;
            l.dotGlow.position.copy(l.currentPos); l.dotGlow.position.y = floorY + 0.05;
            
            const source = new THREE.Vector3(0, hubY, 0);
            l.beamCore.position.copy(source); l.beamCore.lookAt(l.dotCore.position);
            l.beamGlow.position.copy(source); l.beamGlow.lookAt(l.dotGlow.position);
            
            const dist = source.distanceTo(l.dotCore.position);
            l.beamCore.scale.z = dist; l.beamGlow.scale.z = dist;
        });

        // --- ROBOT (SUPER MOBILE) ---
        if (robotState === 'intro') {
            const script = [{t:0, a:"hide"}, {t:1, a:"enter"}, {t:4, a:"look"}, {t:7, a:"surprise"}, {t:10, a:"wave"}];
            if (introIndex < script.length) {
                if (time * 2 >= script[introIndex].t) { 
                    const act = script[introIndex].a;
                    if(act=="hide") robotGroup.position.set(-60, floorY+7.5, 22);
                    if(act=="enter") targetPos.set(0, floorY+7.5, 22);
                    if(act=="look") { smoothRotate(robotGroup, 'y', -0.5, 0.05); }
                    if(act=="surprise") { robotGroup.position.y += 1.5; head.rotation.x = -0.4; }
                    if(act=="wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++;
                }
            } else if (time * 2 > 15) { robotState = 'moving'; pickNewTarget(); nextEvent = time + 3; }
            if(introIndex>0) robotGroup.position.lerp(targetPos, 0.04);
        }
        else if (robotState === 'moving') {
            robotGroup.position.y = (floorY + 7.5) + Math.sin(time*4)*0.2;
            robotGroup.position.lerp(targetPos, 0.03);
            
            // Regarde la caméra (0, 5, 55)
            robotGroup.lookAt(0, 5, 55); 
            
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
                nextEvent = time + 3 + Math.random()*2;
            }
        }
        else if (robotState === 'speaking') {
            mouth.scale.set(1, 1+Math.sin(time*25)*0.5, 1);
            robotGroup.lookAt(0, 5, 55); // Reste face caméra
        }
        
        else if (robotState === 'exploding') { parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += 0.1; p.userData.velocity.multiplyScalar(0.95); }); }
        else if (robotState === 'reassembling') { parts.forEach(p => { p.position.lerp(p.userData.origPos, 0.1); p.rotation.x *= 0.9; }); }

        if(bubble && bubble.style.opacity == 1) {
            const pos = robotGroup.position.clone(); pos.y += 5.0; 
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
        // Zone de déplacement : Devant et Large
        // X: -40 à 40
        // Z: 10 à 30 (Très proche caméra)
        targetPos.set(
            (Math.random()-0.5) * 80, 
            floorY + 7.5, 
            10 + Math.random() * 20 
        ); 
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
    animate();
}
