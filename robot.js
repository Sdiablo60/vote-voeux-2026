import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: ["Bienvenue ! ✨", "Installez-vous.", "La soirée va être belle !", "Prêts pour le show !", "Coucou la technique ! 👷"],
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
        console.error("ERREUR CRITIQUE:", e);
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

// --- FONCTION: GESTIONNAIRE DE TEXTURE VOLUMÉTRIQUE ---
// Crée un dégradé du blanc (opaque) au noir (transparent) pour le faisceau
function createVolumetricTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 32; canvas.height = 128;
    const ctx = canvas.getContext('2d');
    // Dégradé vertical along the beam
    const gradient = ctx.createLinearGradient(0, 0, 0, 128);
    gradient.addColorStop(0, 'rgba(255, 255, 255, 1.0)');   // Source intense
    gradient.addColorStop(0.1, 'rgba(255, 255, 255, 0.6)'); // Diminue rapidement
    gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.1)'); // Reste une traînée
    gradient.addColorStop(1, 'rgba(255, 255, 255, 0.0)');   // Disparition totale
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 32, 128);
    const texture = new THREE.CanvasTexture(canvas);
    texture.wrapS = texture.wrapT = THREE.ClampToEdgeWrapping;
    return texture;
}
const volumetricTexture = createVolumetricTexture();


function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    container.style.position = 'fixed'; container.style.top = '0'; container.style.left = '0';
    container.style.width = '100%'; container.style.height = '100%';
    container.style.zIndex = '1'; container.style.pointerEvents = 'none';
    
    const scene = new THREE.Scene();
    
    // Caméra
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 150);
    camera.position.set(0, 2, 16); // Légèrement surélevée

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.toneMapping = THREE.ACESFilmicToneMapping; // Meilleur rendu des lumières
    renderer.toneMappingExposure = 1.0;
    container.appendChild(renderer.domElement);

    // Lumières d'ambiance (subtiles pour laisser la place au spot)
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.0); 
    scene.add(ambientLight);
    
    // Petite lumière de contre pour détacher le robot du fond
    const rimLight = new THREE.DirectionalLight(0xaaaaaa, 2.0);
    rimLight.position.set(0, 5, -10);
    scene.add(rimLight);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3, metalness: 0.1 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.3 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const greyMat = new THREE.MeshStandardMaterial({ color: 0x888888, metalness: 0.6 });
    
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

    // ==================================================================================
    // --- LE SPOT UNIQUE ET RÉALISTE ---
    // ==================================================================================
    
    const SPOT_COLOR = 0x0088ff; // Un bleu électrique réaliste

    // Matériaux du spot
    const housingDarkMat = new THREE.MeshStandardMaterial({ color: 0x222222, metalness: 0.8, roughness: 0.3 });
    const housingGreyMat = new THREE.MeshStandardMaterial({ color: 0x555555, metalness: 0.6, roughness: 0.4 });
    // Matériau de la lentille : Basic pour qu'elle brille toujours
    const lensMat = new THREE.MeshBasicMaterial({ color: SPOT_COLOR }); 

    // Conteneur principal du spot (permet de le positionner et l'orienter facilement)
    const mainSpotGroup = new THREE.Group();
    // Positionnement : En haut à gauche, en avant
    mainSpotGroup.position.set(-8, 10, 8); 
    scene.add(mainSpotGroup);

    // 1. Le Corps du Projecteur (Modèle 3D détaillé)
    const fixtureBody = new THREE.Group();
    mainSpotGroup.add(fixtureBody);

    // Lyre de support (U-bracket)
    const yoke = new THREE.Mesh(new THREE.TorusGeometry(0.8, 0.1, 16, 32, Math.PI), housingGreyMat);
    yoke.rotation.y = Math.PI / 2; 
    fixtureBody.add(yoke);

    // Boîtier principal (Cylindre allongé avec détails)
    const housing = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.7, 1.5, 32), housingDarkMat);
    housing.rotation.x = Math.PI / 2; // Orienté vers Z
    fixtureBody.add(housing);

    // Arrière du boîtier (Ventilation)
    const backCap = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.6, 0.2, 32), housingGreyMat);
    backCap.rotation.x = Math.PI / 2; backCap.position.z = -0.85;
    fixtureBody.add(backCap);

    // La Lentille (Brillante)
    const lensGeo = new THREE.CircleGeometry(0.55, 32);
    const lensMesh = new THREE.Mesh(lensGeo, lensMat);
    lensMesh.position.z = 0.76; // Juste au bout du boîtier
    fixtureBody.add(lensMesh);

    // Volets coupe-flux (Barndoors) pour le réalisme
    const barnDoorGeo = new THREE.PlaneGeometry(1.2, 0.5);
    const barnDoorMat = new THREE.MeshStandardMaterial({ color: 0x111111, side: THREE.DoubleSide });
    const topBarn = new THREE.Mesh(barnDoorGeo, barnDoorMat);
    topBarn.position.set(0, 0.8, 0.9); topBarn.rotation.x = Math.PI/3; fixtureBody.add(topBarn);
    const botBarn = new THREE.Mesh(barnDoorGeo, barnDoorMat);
    botBarn.position.set(0, -0.8, 0.9); botBarn.rotation.x = -Math.PI/3; fixtureBody.add(botBarn);

    // 2. Le Faisceau Volumétrique (The Realistic Beam)
    const beamLength = 60;
    // Cône tronqué : démarre à la taille de la lentille (0.55) et s'élargit (3.0)
    const beamGeo = new THREE.CylinderGeometry(0.55, 3.0, beamLength, 64, 1, true);
    // Décale le pivot au sommet pour que la rotation et la texture partent du bon endroit
    beamGeo.translate(0, -beamLength / 2, 0); 
    beamGeo.rotateX(-Math.PI / 2); // Pointe vers Z+

    const beamMat = new THREE.MeshBasicMaterial({
        color: SPOT_COLOR,
        transparent: true,
        opacity: 0.6, // Intensité globale
        alphaMap: volumetricTexture, // Le dégradé magique
        blending: THREE.AdditiveBlending, // Lumière qui s'additionne
        depthWrite: false, // Empêche les bugs d'occlusion
        side: THREE.DoubleSide
    });
    const volumetricBeam = new THREE.Mesh(beamGeo, beamMat);
    volumetricBeam.position.z = 0.8; // Départ juste devant la lentille
    // Inverse Z pour que la texture dégradée soit dans le bon sens (opaque -> transparent)
    volumetricBeam.scale.z = -1; 
    fixtureBody.add(volumetricBeam);

    // 3. La Lumière Réelle (Pour éclairer le robot)
    const actualLight = new THREE.SpotLight(SPOT_COLOR, 50); // Haute intensité
    actualLight.angle = 0.4; // Angle correspondant à peu près au faisceau
    actualLight.penumbra = 0.5; // Bords doux
    actualLight.decay = 1.5; // Atténuation réaliste
    actualLight.distance = 100;
    actualLight.position.set(0, 0, 0.8); // Source à la lentille
    
    const lightTarget = new THREE.Object3D();
    scene.add(lightTarget); lightTarget.position.set(0, 0, 0); // Cible le centre
    actualLight.target = lightTarget;
    fixtureBody.add(actualLight);

    // ORIENTATION FINALE
    // Le groupe fixtureBody contient tout (corps, lentille, faisceau, lumière) orienté vers Z+.
    // On lui dit de regarder la cible (le centre).
    fixtureBody.lookAt(lightTarget.position);

    // ==================================================================================


    // --- ANIMATION ---
    let time = 0;
    let targetPos = new THREE.Vector3(4, 0, 0);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        // Animation subtile du spot unique (respiration)
        const pulse = Math.sin(time * 2) * 0.1 + 0.9;
        volumetricBeam.material.opacity = 0.6 * pulse;
        actualLight.intensity = 50 * pulse;

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
