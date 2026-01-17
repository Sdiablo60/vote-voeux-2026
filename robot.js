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
    try {
        initRobot(container);
    } catch (e) {
        console.error("ERREUR 3D:", e);
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

// --- NOUVEAU : Générateur de texture pour le fondu des faisceaux ---
function createBeamTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 32; canvas.height = 256; // Format long pour le dégradé
    const context = canvas.getContext('2d');
    // Dégradé linéaire vertical
    const gradient = context.createLinearGradient(0, 0, 0, 256);
    gradient.addColorStop(0, 'rgba(255, 255, 255, 1.0)'); // Opaque au début
    gradient.addColorStop(1, 'rgba(255, 255, 255, 0.0)'); // Transparent à la fin
    context.fillStyle = gradient;
    context.fillRect(0, 0, 32, 256);
    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = texture.wrapT = THREE.ClampToEdgeWrapping; // Important pour ne pas répéter le dégradé
    return texture;
}
// On crée la texture une seule fois pour tous les spots
const beamFadeTexture = createBeamTexture();


function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    container.style.position = 'fixed'; container.style.top = '0'; container.style.left = '0';
    container.style.width = '100%'; container.style.height = '100%';
    container.style.zIndex = '1'; container.style.pointerEvents = 'none';
    
    const scene = new THREE.Scene();
    
    // CAMÉRA (Z=17 pour voir large)
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 150);
    camera.position.set(0, 0, 17); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // LUMIÈRES
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.5); 
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(0, 10, 10);
    scene.add(dirLight);
    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
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

    // --- SUPPORTS DJ (ÉCARTÉS) ---
    const trussMat = new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.9, roughness: 0.1 });

    function createDJStand(xPos) {
        const standGroup = new THREE.Group();
        standGroup.position.set(xPos, -7, -2); 
        // Pilier
        const height = 15;
        const pillar = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, height, 16), trussMat);
        pillar.position.y = height / 2; standGroup.add(pillar);
        // Base
        const base = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.9, 0.3, 32), trussMat);
        base.position.y = 0.15; standGroup.add(base);
        scene.add(standGroup);
        return standGroup;
    }

    // NOUVELLE POSITION : ±17 au lieu de ±13 pour écarter davantage
    const leftStand = createDJStand(-17);
    const rightStand = createDJStand(17);

    // --- SPOTS & FAISCEAUX RÉALISTES (FONDU) ---
    const stageSpots = [];
    const housingMat = new THREE.MeshStandardMaterial({ color: 0xCCCCCC, metalness: 0.5, roughness: 0.5, emissive: 0x222222 });
    const barnMat = new THREE.MeshStandardMaterial({ color: 0x333333, side: THREE.DoubleSide });
    const centerTarget = new THREE.Vector3(0,0,0);

    function createSpot(parentStand, yLocalPos, colorInt, isBottom) {
        const group = new THREE.Group();
        group.position.set(0, yLocalPos, 0.3); 
        group.scale.set(0.6, 0.6, 0.6);

        // Support et Corps
        const bracket = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.05, 8, 16, Math.PI), housingMat);
        bracket.rotation.z = isBottom ? 0 : Math.PI; group.add(bracket);
        const bodyGroup = new THREE.Group(); group.add(bodyGroup);
        const box = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.6, 0.6), housingMat);
        box.position.z = 0.3; bodyGroup.add(box);
        const cyl = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.6, 32), housingMat);
        cyl.rotation.x = Math.PI/2; cyl.position.z = -0.2; bodyGroup.add(cyl);
        const lens = new THREE.Mesh(new THREE.CircleGeometry(0.35, 32), new THREE.MeshBasicMaterial({ color: colorInt }));
        lens.position.set(0, 0, -0.51); bodyGroup.add(lens);
        const topDoor = new THREE.Mesh(new THREE.PlaneGeometry(0.6, 0.3), barnMat); topDoor.position.set(0, 0.45, -0.5); topDoor.rotation.x = Math.PI/4; bodyGroup.add(topDoor);
        const botDoor = new THREE.Mesh(new THREE.PlaneGeometry(0.6, 0.3), barnMat); botDoor.position.set(0, -0.45, -0.5); botDoor.rotation.x = -Math.PI/4; bodyGroup.add(botDoor);

        // --- NOUVEAU FAISCEAU AVEC FONDU ---
        const beamLen = 60; // Très long faisceau
        // Utilise un cône ouvert à la fin, qui commence à la taille de la lentille (0.35) et s'élargit (2.0)
        const beamGeo = new THREE.ConeGeometry(2.0, beamLen, 32, 1, true, 0, Math.PI * 2);
        // On déplace le point de pivot à la pointe du cône
        beamGeo.translate(0, -beamLen / 2, 0); 
        // On l'oriente vers l'avant
        beamGeo.rotateX(-Math.PI / 2);

        const beamMat = new THREE.MeshBasicMaterial({ 
            color: colorInt, 
            transparent: true, 
            opacity: 1.0, // L'opacité globale est gérée ici, le dégradé par alphaMap
            alphaMap: beamFadeTexture, // Application de la texture de fondu
            side: THREE.DoubleSide, // Important pour voir le fondu des deux côtés
            blending: THREE.AdditiveBlending, 
            depthWrite: false,
        });
        const beam = new THREE.Mesh(beamGeo, beamMat);
        beam.position.z = -0.52; 
        // IMPORTANT : On inverse l'échelle Z pour que la texture de fondu soit dans le bon sens (opaque près de la lentille)
        beam.scale.z = -1; 
        bodyGroup.add(beam);

        // Lumière réelle
        const light = new THREE.SpotLight(colorInt, 10);
        light.angle = 0.35; light.distance = 70; light.decay = 1.5; light.penumbra = 0.5;
        light.position.set(0, 0, -0.5);
        bodyGroup.add(light); 
        scene.add(light.target); light.target.position.copy(centerTarget);

        parentStand.add(group);
        bodyGroup.lookAt(parentStand.worldToLocal(centerTarget.clone()));

        return { group, beam, light, baseIntensity: 10, timeOff: Math.random() * 100 };
    }

    // --- PLACEMENT ---
    stageSpots.push(createSpot(leftStand, 13, 0xFFFF00, false));
    stageSpots.push(createSpot(leftStand, 4, 0x00FFFF, true));
    stageSpots.push(createSpot(rightStand, 13, 0x00FF00, false));
    stageSpots.push(createSpot(rightStand, 4, 0xFFA500, true));

    // --- ANIMATION ---
    let time = 0;
    let targetPos = new THREE.Vector3(4, 0, 0);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        stageSpots.forEach(s => {
            const pulse = Math.sin(time * 3 + s.timeOff) * 0.2 + 0.8;
            // L'opacité du matériau gère l'intensité globale du faisceau dégradé
            s.beam.material.opacity = 0.8 * pulse; 
            s.light.intensity = s.baseIntensity * pulse;
        });

        if (robotState === 'intro') {
            const script = [{t:0, a:"hide"}, {t:1, a:"enter"}, {t:4, a:"look"}, {t:7, a:"surprise"}, {t:10, a:"wave"}];
            if (introIndex < script.length) {
                if (time >= script[introIndex].t) {
                    const act = script[introIndex].a;
                    if(act=="hide") robotGroup.position.x = -15;
                    if(act=="enter") targetPos.set(4,0,0);
                    if(act=="look") { smoothRotate(robotGroup, 'y', -0.5); smoothRotate(head, 'y', 0.8); }
                    if(act=="surprise") { robotGroup.position.y += 0.5; head.rotation.x = -0.3; }
                    if(act=="wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++;
                }
            } else if (time > 15) { robotState = 'moving'; pickNewTarget(); nextEvent = time + 3; }
            if(introIndex>0) robotGroup.position.lerp(targetPos, 0.02);
        }
        else if (robotState === 'moving') {
            robotGroup.position.y += Math.sin(time*2)*0.002;
            robotGroup.position.lerp(targetPos, 0.02);
            smoothRotate(robotGroup, 'y', (targetPos.x - robotGroup.position.x)*0.05);
            smoothRotate(robotGroup, 'z', -(targetPos.x - robotGroup.position.x)*0.03);
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
            const pos = robotGroup.position.clone(); pos.y += 0.8; pos.project(camera);
            const x = (pos.x * .5 + .5) * width; const y = (pos.y * -.5 + .5) * height;
            bubble.style.left = Math.max(100, Math.min(width-100, x)) + 'px';
            bubble.style.top = Math.max(50, y - 90) + 'px';
        }
        renderer.render(scene, camera);
    }

    function smoothRotate(obj, axis, target) { obj.rotation[axis] += (target - obj.rotation[axis]) * 0.05; }
    function showBubble(txt, dur) { bubble.innerText = txt; bubble.style.opacity = 1; setTimeout(() => bubble.style.opacity=0, dur); }
    function pickNewTarget() { targetPos.set((Math.random()>0.5?1:-1)*(3.5+Math.random()*2), (Math.random()-0.5)*3, 0); }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
    animate();
}
