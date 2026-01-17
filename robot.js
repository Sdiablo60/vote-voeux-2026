import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- CONFIGURATION ET BORDURE ---
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };
const LIMITE_HAUTE_Y = 6.53; // Bordure calibrée pour votre bandeau titre

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: [
        "Bienvenue ! ✨", "Installez-vous.", "Ravi de vous voir !", 
        "La soirée va être belle !", "Je vérifie les réglages...", "Prêts pour le show ?",
        "C'est un plaisir.", "J'adore l'ambiance !", "Coucou la technique ! 👷"
    ],
    vote_off: [
        "Les votes sont CLOS ! 🛑", "Les jeux sont faits.", "Le podium arrive... 🏆",
        "Suspens... 😬", "Calcul en cours... 🧮", "La régie gère ! ⚡"
    ],
    photos: [
        "Photos ! 📸", "Souriez !", "On partage ! 📲", "Vous êtes beaux !", "Selfie time ! 🤳"
    ],
    danse: [
        "Dancefloor ! 💃", "Je sens le rythme ! 🎵", "Regardez-moi ! 🤖", 
        "On se bouge ! 🙌", "Allez DJ ! 🔊"
    ],
    explosion: [
        "Surchauffe ! 🔥", "J'ai perdu la tête... 🤯", "Rassemblement... 🧲", "Oups..."
    ],
    cache_cache: [
        "Coucou ! 👋", "Me revoilà !", "Magie ! ⚡", "Je suis rapide ! 🚀"
    ]
};

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

const introScript = [
    { time: 0.0, action: "hide_start" },
    { time: 1.0, action: "enter_stage" },
    { time: 4.0, text: "C'est calme ici... 🤔", action: "look_around" },
    { time: 7.0, text: "OH ! BONJOUR ! 😳", action: "surprise" },
    { time: 10.0, text: "Bienvenue au " + config.titre + " ! ✨", action: "wave" },
    { time: 14.0, text: "Prêts pour la soirée ? 🎉", action: "ask" }
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
    camera.position.set(0, 0, 11); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 1.2); 
    scene.add(hemiLight);
    
    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2, metalness: 0.1 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1, metalness: 0.5 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); 
    const greyMat = new THREE.MeshStandardMaterial({ color: 0xbbbbbb });

    function createPart(geo, mat, x, y, z, parent) {
        const mesh = new THREE.Mesh(geo, mat);
        mesh.position.set(x, y, z);
        mesh.userData.origPos = new THREE.Vector3(x, y, z);
        mesh.userData.origRot = new THREE.Euler(0, 0, 0);
        mesh.userData.velocity = new THREE.Vector3();
        mesh.userData.rotVelocity = new THREE.Vector3();
        if(parent) parent.add(mesh);
        return mesh;
    }

    const head = createPart(new THREE.SphereGeometry(0.85, 32, 32), whiteMat, 0, 0, 0, robotGroup);
    head.scale.set(1.4, 1.0, 0.75);
    const face = createPart(new THREE.SphereGeometry(0.78, 32, 32), blackMat, 0, 0, 0.55, head);
    face.scale.set(1.25, 0.85, 0.6);
    createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, -0.35, 0.15, 1.05, head);
    createPart(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat, 0.35, 0.15, 1.05, head);
    const mouth = createPart(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat, 0, -0.15, 1.05, head);
    mouth.rotation.z = Math.PI; mouth.userData.origRot.z = Math.PI;

    const body = createPart(new THREE.SphereGeometry(0.65, 32, 32), whiteMat, 0, -1.1, 0, robotGroup);
    body.scale.set(0.95, 1.1, 0.8);
    const belt = createPart(new THREE.TorusGeometry(0.62, 0.03, 16, 32), greyMat, 0, 0, 0, body);
    belt.rotation.x = Math.PI/2;

    const leftArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, -0.8, -0.8, 0, robotGroup);
    leftArm.rotation.z = 0.15; leftArm.userData.origRot.z = 0.15;
    const rightArm = createPart(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat, 0.8, -0.8, 0, robotGroup);
    rightArm.rotation.z = -0.15; rightArm.userData.origRot.z = -0.15;

    const parts = [head, body, leftArm, rightArm];
    scene.add(robotGroup);

    // --- SPOTS 3D (AVEC LIMITE 6.53) ---
    const stageSpots = [];
    const spotCaseMat = new THREE.MeshStandardMaterial({ color: 0x333333, roughness: 0.3, metalness: 0.7 });
    const barnDoorMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, side: THREE.DoubleSide });

    function createDetailedSpotFixture(color, xPos, yPos, isBottom) {
        const pivotGroup = new THREE.Group();
        pivotGroup.position.set(xPos, yPos, 0); 

        const bracket = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.05, 8, 16, Math.PI), spotCaseMat);
        bracket.rotation.z = isBottom ? 0 : Math.PI;
        pivotGroup.add(bracket);

        const bodyGroup = new THREE.Group();
        pivotGroup.add(bodyGroup);
        bodyGroup.add(new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.6, 0.8), spotCaseMat)); // Box
        
        const frontCyl = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.6, 32), spotCaseMat);
        frontCyl.rotation.x = Math.PI/2; frontCyl.position.z = -0.3;
        bodyGroup.add(frontCyl);

        const lensMat = new THREE.MeshBasicMaterial({ color: 0x000000 });
        const lens = new THREE.Mesh(new THREE.CircleGeometry(0.35, 32), lensMat);
        lens.position.z = -0.61; bodyGroup.add(lens);

        const beam = new THREE.Mesh(
            new THREE.ConeGeometry(1.0, 20, 32, 1, true),
            new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide })
        );
        beam.translate(0, -10, 0); beam.rotateX(-Math.PI/2); beam.position.z = -0.65;
        bodyGroup.add(beam);

        const light = new THREE.SpotLight(color, 0);
        light.angle = 0.3; light.distance = 50; bodyGroup.add(light);
        const targetObj = new THREE.Object3D(); scene.add(targetObj); light.target = targetObj;

        scene.add(pivotGroup);
        return { pivot: pivotGroup, body: bodyGroup, light: light, beam: beam, lens: lens, targetObj: targetObj, baseColor: new THREE.Color(color), isOn: false, intensity: 0, nextToggle: Math.random() * 5 };
    }

    // POSITIONNEMENT DES SPOTS SELON VOS BORDURES
    [-6, -2, 2, 6].forEach((x, i) => stageSpots.push(createDetailedSpotFixture(colors[i%colors.length], x, LIMITE_HAUTE_Y, false)));
    [-4, 0, 4].forEach((x, i) => stageSpots.push(createDetailedSpotFixture(colors[(i+2)%colors.length], x, -6.5, true)));

    // --- PARTICULES ---
    const particleCount = 200;
    const particlesGeo = new THREE.BufferGeometry();
    const posArray = new Float32Array(particleCount * 3).fill(9999);
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const particleSystem = new THREE.Points(particlesGeo, new THREE.PointsMaterial({ size: 0.5, color: 0xffaa00, transparent: true, opacity: 0.8 }));
    scene.add(particleSystem);
    const vels = Array.from({length: particleCount}, () => ({x:0, y:0, z:0, life:0}));

    function triggerSmoke(x, y, z, isExplosion = false) {
        const p = particlesGeo.attributes.position.array;
        for(let i=0; i<particleCount; i++) {
            p[i*3]=x; p[i*3+1]=y; p[i*3+2]=z;
            let s = isExplosion ? 0.3 : 0.05;
            vels[i] = { x:(Math.random()-0.5)*s, y:(Math.random()-0.5)*s, z:(Math.random()-0.5)*s, life:1.0 };
        }
    }

    // --- ANIMATION ET ÉTATS ---
    let time = 0, targetPosition = new THREE.Vector3(-15, 0, 0), robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let introIndex = 0, nextEventTime = 0;

    function pickNewTarget() {
        const aspect = width / height;
        // Le robot reste entre -5 et LIMITE_HAUTE_Y - 2 pour ne pas coller au titre
        targetPosition.set((Math.random()-0.5)*12*aspect, (Math.random()-0.5)*8, 0);
        if(targetPosition.y > LIMITE_HAUTE_Y - 2) targetPosition.y = LIMITE_HAUTE_Y - 3;
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        // Particules Update
        const p = particlesGeo.attributes.position.array;
        vels.forEach((v, i) => {
            if(v.life > 0) {
                p[i*3]+=v.x; p[i*3+1]+=v.y; p[i*3+2]+=v.z; v.life-=0.02;
                if(v.life<=0) p[i*3]=9999;
            }
        });
        particlesGeo.attributes.position.needsUpdate = true;

        // Spots Update
        stageSpots.forEach(s => {
            if(time > s.nextToggle) { s.isOn = !s.isOn; s.nextToggle = time + Math.random()*3 + 1; }
            s.intensity += ((s.isOn?30:0) - s.intensity) * 0.1;
            s.light.intensity = s.intensity; s.beam.material.opacity = (s.isOn?0.1:0) * (s.intensity/30);
            s.lens.material.color.setHex(s.isOn ? s.baseColor.getHex() : 0x000000);
            s.body.lookAt(robotGroup.position);
        });

        // Robot States
        if (robotState === 'intro') {
            const step = introScript[introIndex];
            if (step && time >= step.time) {
                if(step.text) { bubble.innerText = step.text; bubble.style.opacity = 1; setTimeout(()=>bubble.style.opacity=0, 3000); }
                if(step.action === "enter_stage") targetPosition.set(0, 0, 0);
                if(step.action === "surprise") { robotGroup.position.z = 5; }
                introIndex++;
            }
            if(introIndex >= introScript.length) { robotState = 'moving'; pickNewTarget(); }
            robotGroup.position.lerp(targetPosition, 0.03);
        } else if (robotState === 'moving') {
            robotGroup.position.lerp(targetPosition, 0.02);
            robotGroup.rotation.y = Math.sin(time)*0.2;
            if(robotGroup.position.distanceTo(targetPosition) < 0.5) pickNewTarget();
            if(time > nextEventTime) {
                const r = Math.random();
                if(r < 0.15) { // Explosion
                    robotState = 'exploding'; triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z, true);
                    parts.forEach(p => p.userData.velocity.set((Math.random()-0.5)*0.5, (Math.random()-0.5)*0.5, (Math.random()-0.5)*0.5));
                    setTimeout(() => { robotState = 'reassembling'; setTimeout(()=>robotState='moving', 2000); }, 2000);
                } else { 
                    bubble.innerText = getUniqueMessage(config.mode); bubble.style.opacity = 1; 
                    setTimeout(()=>bubble.style.opacity=0, 3000);
                }
                nextEventTime = time + 8;
            }
        } else if (robotState === 'exploding') {
            parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x+=0.1; p.userData.velocity.multiplyScalar(0.95); });
        } else if (robotState === 'reassembling') {
            parts.forEach(p => p.position.lerp(p.userData.origPos, 0.1));
        }

        // Bubble positioning (Sécurité titre)
        if(bubble && bubble.style.opacity == 1) {
            const p = robotGroup.position.clone(); p.y += 1.2; p.project(camera);
            let screenY = (p.y * -0.5 + 0.5) * height;
            // Bloquer la bulle sous le bandeau titre
            if(screenY < 100) screenY = 110; 
            bubble.style.top = screenY + 'px';
            bubble.style.left = (p.x * 0.5 + 0.5) * width + 'px';
        }

        renderer.render(scene, camera);
    }
    animate();
}
