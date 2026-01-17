import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- PARAMÈTRE DE BORDURE VALIDÉ ---
const LIMITE_HAUTE_Y = 6.53; 

// --- TEXTES ---
const MESSAGES_BAG = {
    attente: ["Bienvenue ! ✨", "Installez-vous.", "Ravi de vous voir !", "La soirée va être belle !", "Prêts pour le show ?", "J'adore l'ambiance !", "Coucou la technique ! 👷"],
    vote_off: ["Les votes sont CLOS ! 🛑", "Les jeux sont faits.", "Le podium arrive... 🏆", "Suspens... 😬", "La régie gère ! ⚡"],
    photos: ["Photos ! 📸", "Souriez !", "On partage ! 📲", "Vous êtes beaux !", "Selfie time ! 🤳"],
    danse: ["Dancefloor ! 💃", "Je sens le rythme ! 🎵", "Regardez-moi ! 🤖", "On se bouge ! 🙌", "Allez DJ ! 🔊"],
    explosion: ["Surchauffe ! 🔥", "J'ai perdu la tête... 🤯", "Rassemblement... 🧲", "Oups..."],
    cache_cache: ["Coucou ! 👋", "Me revoilà !", "Magie ! ⚡", "Je suis rapide ! 🚀"]
};

const usedMessages = {};
function getUniqueMessage(category) {
    if (!usedMessages[category]) usedMessages[category] = [];
    if (usedMessages[category].length >= MESSAGES_BAG[category].length) usedMessages[category] = [];
    let available = MESSAGES_BAG[category].filter(m => !usedMessages[category].includes(m));
    if(available.length === 0) available = MESSAGES_BAG[category];
    let msg = available[Math.floor(Math.random() * available.length)];
    usedMessages[category].push(msg);
    return msg;
}

// --- SCRIPT D'INTRODUCTION (ARRIVÉE + REGARD + RAPPROCHEMENT) ---
const introScript = [
    { time: 0.0, action: "hide_start" },
    { time: 1.0, action: "enter_stage" }, // Arrive sur l'écran
    { time: 4.0, text: "C'est calme ici... 🤔", action: "look_around" }, // Fait un tour / regarde
    { time: 7.0, text: "OH ! BONJOUR ! 😳", action: "surprise" }, // Se rapproche de l'écran
    { time: 10.0, text: "Bienvenue au " + config.titre + " ! ✨", action: "wave" },
    { time: 14.0, text: "Prêts pour la soirée ? 🎉", action: "ask" }
];

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initRobot(container));
} else {
    initRobot(container);
}

function initRobot(container) {
    if(!container) return;
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 12); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xffffff, 2.5); 
    scene.add(ambientLight);
    
    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- CONSTRUCTION DU ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000, roughness: 0.1 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const greyMat = new THREE.MeshStandardMaterial({ color: 0xbbbbbb });
    
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
        p.userData = { origPos: p.position.clone(), origRot: p.rotation.clone(), velocity: new THREE.Vector3(), rotVelocity: new THREE.Vector3() };
    });
    robotGroup.add(head); robotGroup.add(body); robotGroup.add(leftArm); robotGroup.add(rightArm);
    scene.add(robotGroup);
    const parts = [head, body, leftArm, rightArm];

    // --- SPOTS DE SCÈNE (AVEC BORDURE VALIDÉE) ---
    const stageSpots = [];
    const spotColors = [0xff0000, 0x00ff00, 0x0088ff, 0xffaa00, 0x00ffff, 0xff00ff];
    function createSpot(color, x, y, isBottom) {
        const g = new THREE.Group(); g.position.set(x, y, 0);
        const lens = new THREE.Mesh(new THREE.CircleGeometry(0.2, 16), new THREE.MeshBasicMaterial({ color: color }));
        lens.position.z = 0.1; g.add(lens);
        const beam = new THREE.Mesh(new THREE.ConeGeometry(0.4, 15, 32, 1, true), new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false }));
        beam.rotateX(-Math.PI/2); beam.position.z = -7.5; g.add(beam);
        scene.add(g);
        return { g, beam, color: new THREE.Color(color), isOn: false, nextToggle: Math.random()*5 };
    }
    [-6, -2, 2, 6].forEach((x, i) => stageSpots.push(createSpot(spotColors[i%6], x, LIMITE_HAUTE_Y, false)));

    // --- LOGIQUE PARTICULES ---
    const particleCount = 150;
    const particlesGeo = new THREE.BufferGeometry();
    const posArr = new Float32Array(particleCount * 3).fill(999);
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
    const particleSystem = new THREE.Points(particlesGeo, new THREE.PointsMaterial({ size: 0.4, color: 0xffaa00, transparent: true, opacity: 0.8 }));
    scene.add(particleSystem);
    const pVels = Array.from({length: particleCount}, () => ({v: new THREE.Vector3(), life: 0}));

    function triggerSmoke(x, y, z) {
        const positions = particlesGeo.attributes.position.array;
        pVels.forEach((p, i) => {
            positions[i*3]=x; positions[i*3+1]=y; positions[i*3+2]=z;
            p.v.set((Math.random()-0.5)*0.3, (Math.random()-0.5)*0.3, (Math.random()-0.5)*0.3);
            p.life = 1.0;
        });
        particlesGeo.attributes.position.needsUpdate = true;
    }

    // --- ÉTATS ET ANIMATIONS ---
    let time = 0;
    let targetPos = new THREE.Vector3(-15, 0, 0);
    let robotState = 'intro';
    let introIdx = 0;
    let nextEvt = 0;

    function showBubble(text, duration) { 
        if(!bubble) return; 
        bubble.innerText = text; 
        bubble.style.opacity = 1; 
        setTimeout(() => { bubble.style.opacity = 0; }, duration); 
    }

    function pickTarget() {
        const aspect = window.innerWidth / window.innerHeight;
        targetPos.set((Math.random()-0.5)*10*aspect, (Math.random()-0.5)*5, 0);
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        // Particules update
        const positions = particlesGeo.attributes.position.array;
        pVels.forEach((p, i) => {
            if(p.life > 0) {
                positions[i*3] += p.v.x; positions[i*3+1] += p.v.y; positions[i*3+2] += p.v.z;
                p.life -= 0.02; if(p.life <= 0) positions[i*3] = 999;
            }
        });
        particlesGeo.attributes.position.needsUpdate = true;

        // Spots update
        stageSpots.forEach(s => {
            if(time > s.nextToggle) { s.isOn = !s.isOn; s.nextToggle = time + Math.random()*3 + 1; }
            s.beam.material.opacity += ((s.isOn ? 0.15 : 0) - s.beam.material.opacity) * 0.1;
            s.g.lookAt(robotGroup.position);
        });

        // Robot States
        if (robotState === 'intro') {
            const step = introScript[introIdx];
            if (step && time >= step.time) {
                if(step.text) showBubble(step.text, 3000);
                if(step.action === "enter_stage") targetPos.set(0, 0, 0);
                if(step.action === "surprise") { robotGroup.position.z = 4; robotGroup.position.y = 0.5; }
                introIdx++;
            }
            if(introIdx === introScript.length) { robotState = 'moving'; pickTarget(); nextEvt = time + 5; }
            robotGroup.position.lerp(targetPos, 0.03);
        } 
        else if (robotState === 'moving') {
            robotGroup.position.lerp(targetPos, 0.02);
            robotGroup.rotation.y = Math.sin(time)*0.2;
            if(robotGroup.position.distanceTo(targetPos) < 0.5) pickTarget();
            if(time > nextEvt) {
                const r = Math.random();
                if(r < 0.2) { // Explosion
                    robotState = 'exploding'; showBubble(getUniqueMessage('explosion'), 3000);
                    triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z);
                    parts.forEach(p => { p.userData.velocity.set((Math.random()-0.5)*0.5, (Math.random()-0.5)*0.5, (Math.random()-0.5)*0.5); });
                    setTimeout(() => { robotState = 'moving'; pickTarget(); }, 3000);
                } else if(r < 0.4) { // Teleport
                    triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z);
                    robotGroup.visible = false;
                    setTimeout(() => { pickTarget(); robotGroup.position.copy(targetPos); robotGroup.visible = true; triggerSmoke(targetPos.x, targetPos.y, targetPos.z); }, 1000);
                } else {
                    showBubble(getUniqueMessage(config.mode), 4000);
                }
                nextEvt = time + 8;
            }
        }
        else if (robotState === 'exploding') {
            parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x+=0.1; p.userData.velocity.multiplyScalar(0.96); });
            parts.forEach(p => { if(time % 3 > 2.8) p.position.lerp(p.userData.origPos, 0.1); }); // Reassemble auto
        }

        // Bubble positioning
        if(bubble && bubble.style.opacity == 1) {
            const p = robotGroup.position.clone(); p.y += 1.2; p.project(camera);
            bubble.style.left = (p.x * 0.5 + 0.5) * window.innerWidth + 'px';
            bubble.style.top = (p.y * -0.5 + 0.5) * window.innerHeight + 'px';
        }

        renderer.render(scene, camera);
    }
    
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
    animate();
}
