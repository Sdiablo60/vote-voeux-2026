import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- CONFIGURATION DES BORDURES VALIDÉES ---
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

const introScript = [
    { time: 0.0, action: "hide_start" },
    { time: 1.0, action: "enter_stage" },
    { time: 4.0, text: "C'est calme ici... 🤔", action: "look_around" },
    { time: 7.0, text: "OH ! BONJOUR ! 😳", action: "surprise" },
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
    
    // Style du container forcé
    container.style.position = 'fixed'; container.style.top = '0'; container.style.left = '0';
    container.style.width = '100vw'; container.style.height = '100vh';
    container.style.zIndex = '10'; container.style.pointerEvents = 'none';
    
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

    // --- ROBOT CONSTRUCTION ---
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

    // --- SPOTS SCÈNE ---
    const stageSpots = [];
    const spotCaseMat = new THREE.MeshStandardMaterial({ color: 0xDDDDDD, roughness: 0.4, metalness: 0.5 });
    const barnDoorMat = new THREE.MeshStandardMaterial({ color: 0x666666, side: THREE.DoubleSide });

    function createDetailedSpotFixture(color, xPos, yPos, isBottom) {
        const pivotGroup = new THREE.Group();
        pivotGroup.position.set(xPos, yPos, 0); 
        const scale = 0.5; 

        const bracket = new THREE.Mesh(new THREE.TorusGeometry(0.5 * scale, 0.05 * scale, 8, 16, Math.PI), spotCaseMat);
        bracket.rotation.z = isBottom ? 0 : Math.PI;
        pivotGroup.add(bracket);

        const bodyGroup = new THREE.Group();
        pivotGroup.add(bodyGroup);

        const rearBox = new THREE.Mesh(new THREE.BoxGeometry(0.6 * scale, 0.6 * scale, 0.8 * scale), spotCaseMat);
        rearBox.position.z = 0.4 * scale;
        bodyGroup.add(rearBox);

        const frontCyl = new THREE.Mesh(new THREE.CylinderGeometry(0.4 * scale, 0.4 * scale, 0.6 * scale, 32), spotCaseMat);
        frontCyl.rotation.x = Math.PI / 2;
        frontCyl.position.z = -0.3 * scale;
        bodyGroup.add(frontCyl);

        const lens = new THREE.Mesh(new THREE.CircleGeometry(0.35 * scale, 32), new THREE.MeshBasicMaterial({ color: color }));
        lens.position.set(0, 0, -0.61 * scale);
        bodyGroup.add(lens);

        const beamGeo = new THREE.ConeGeometry(0.4, 15, 32, 1, true);
        beamGeo.translate(0, -7.5, 0); beamGeo.rotateX(-Math.PI / 2);
        const beam = new THREE.Mesh(beamGeo, new THREE.MeshBasicMaterial({ color: color, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
        beam.position.z = -0.65 * scale;
        bodyGroup.add(beam);

        const light = new THREE.SpotLight(color, 0);
        light.angle = 0.2; light.penumbra = 0.5; light.distance = 50;
        bodyGroup.add(light);
        
        const targetObj = new THREE.Object3D();
        scene.add(targetObj);
        light.target = targetObj;

        scene.add(pivotGroup);
        return { pivot: pivotGroup, body: bodyGroup, light: light, beam: beam, lens: lens, targetObj: targetObj, baseColor: new THREE.Color(color), isOn: false, intensity: 0, mode: 'fixed', targetPos: new THREE.Vector3(), nextToggle: Math.random() * 5 };
    }

    const spotColors = [0xff0000, 0x00ff00, 0x0088ff, 0xffaa00, 0x00ffff, 0xff00ff];
    [-6, -2, 2, 6].forEach((x, i) => stageSpots.push(createDetailedSpotFixture(spotColors[i%spotColors.length], x, LIMITE_HAUTE_Y, false)));
    [-4, 0, 4].forEach((x, i) => stageSpots.push(createDetailedSpotFixture(spotColors[(i+2)%spotColors.length], x, -6.5, true)));

    // --- PARTICULES ---
    const particleCount = 200;
    const particlesGeo = new THREE.BufferGeometry();
    const posArray = new Float32Array(particleCount * 3);
    const colorArray = new Float32Array(particleCount * 3);
    const scaleArray = new Float32Array(particleCount);
    const velocityArray = []; 

    for(let i=0; i<particleCount; i++) {
        posArray[i*3] = 9999; posArray[i*3+1] = 9999; posArray[i*3+2] = 9999;
        scaleArray[i] = 0; velocityArray.push({x:0, y:0, z:0, life:0});
    }
    particlesGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    particlesGeo.setAttribute('color', new THREE.BufferAttribute(colorArray, 3));
    particlesGeo.setAttribute('scale', new THREE.BufferAttribute(scaleArray, 1));
    
    const particleMat = new THREE.PointsMaterial({
        vertexColors: true, size: 0.6, transparent: true, opacity: 0.8, depthWrite: false,
        map: (function(){ const c = document.createElement('canvas'); c.width=32; c.height=32; const ctx = c.getContext('2d'); const g = ctx.createRadialGradient(16,16,0, 16,16,16); g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle=g; ctx.fillRect(0,0,32,32); const t = new THREE.Texture(c); t.needsUpdate=true; return t; })()
    });
    const particleSystem = new THREE.Points(particlesGeo, particleMat);
    scene.add(particleSystem);

    function triggerSmoke(x, y, z, isExplosion = false) {
        const pPos = particleSystem.geometry.attributes.position.array;
        const pCol = particleSystem.geometry.attributes.color.array;
        const pScl = particleSystem.geometry.attributes.scale.array;
        for(let i=0; i<particleCount; i++) {
            pPos[i*3] = x + (Math.random()-0.5); pPos[i*3+1] = y + (Math.random()-0.5); pPos[i*3+2] = z + (Math.random()-0.5);
            const isSpark = isExplosion && Math.random() < 0.3;
            const c = isSpark ? new THREE.Color(0xffaa00) : new THREE.Color(0xaaaaaa);
            pCol[i*3] = c.r; pCol[i*3+1] = c.g; pCol[i*3+2] = c.b; pScl[i] = Math.random() * 0.8 + 0.2;
            let speed = isExplosion ? 0.2 : 0.05; velocityArray[i] = { x: (Math.random()-0.5)*speed, y: (Math.random()-0.5)*speed + (isExplosion ? 0.05 : 0.02), z: (Math.random()-0.5)*speed, life: 1.0 };
        }
        particleSystem.geometry.attributes.position.needsUpdate = true; particleSystem.geometry.attributes.color.needsUpdate = true; particleSystem.geometry.attributes.scale.needsUpdate = true;
    }

    function updateParticles() {
        const pPos = particleSystem.geometry.attributes.position.array; const pScl = particleSystem.geometry.attributes.scale.array; let active = false;
        for(let i=0; i<particleCount; i++) {
            if (velocityArray[i].life > 0) { active = true; pPos[i*3] += velocityArray[i].x; pPos[i*3+1] += velocityArray[i].y; pPos[i*3+2] += velocityArray[i].z; velocityArray[i].life -= 0.015; pScl[i] = velocityArray[i].life; if(velocityArray[i].life <= 0) pPos[i*3] = 9999; }
        }
        if(active) { particleSystem.geometry.attributes.position.needsUpdate = true; particleSystem.geometry.attributes.scale.needsUpdate = true; }
    }

    // --- LOGIQUE GÉNÉRALE ---
    let time = 0;
    let startX = (config.mode === 'attente') ? -15 : 4.0;
    let targetPosition = new THREE.Vector3(startX, 0, 0); robotGroup.position.copy(targetPosition);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let introIndex = 0; let nextEventTime = 0; let bubbleTimeout = null;

    function smoothRotate(object, axis, targetValue, speed) { object.rotation[axis] += (targetValue - object.rotation[axis]) * speed; }
    function showBubble(text, duration) { if(!bubble) return; if (bubbleTimeout) { clearTimeout(bubbleTimeout); bubbleTimeout = null; } bubble.innerText = text; bubble.style.opacity = 1; if(duration) bubbleTimeout = setTimeout(() => { if(bubble) bubble.style.opacity = 0; }, duration); }
    function hideBubble() { if(bubble) bubble.style.opacity = 0; }
    
    function pickNewTarget() { 
        const aspect = width / height; const vW = 7 * aspect; 
        const side = Math.random() > 0.5 ? 1 : -1; 
        const safeMin = 4.2; const vMax = vW * 0.55; 
        let x = side * (safeMin + Math.random() * (vMax - safeMin)); 
        let y = (Math.random() - 0.5) * 4.0; 
        targetPosition.set(x, y, 0); 
    }

    function startExplosion() {
        robotState = 'exploding'; const msg = getUniqueMessage('explosion'); showBubble(msg, 3500);
        setTimeout(() => {
            explosionLight.intensity = 5; setTimeout(() => { explosionLight.intensity = 0; }, 200);
            triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z, true);
            parts.forEach(part => {
                part.userData.velocity.set((Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4, (Math.random()-0.5)*0.4);
                part.userData.rotVelocity.set(Math.random()*0.2, Math.random()*0.2, Math.random()*0.2);
            });
            setTimeout(() => {
                robotState = 'reassembling';
                setTimeout(() => { robotState = 'moving'; pickNewTarget(); }, 2000);
            }, 3000);
        }, 1000);
    }

    function startTeleport() {
        robotState = 'teleporting'; showBubble(getUniqueMessage('cache_cache'), 1500);
        triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z, false);
        setTimeout(() => {
            robotGroup.visible = false; pickNewTarget(); robotGroup.position.copy(targetPosition);
            setTimeout(() => {
                triggerSmoke(robotGroup.position.x, robotGroup.position.y, robotGroup.position.z, false);
                robotGroup.visible = true; robotState = 'moving';
            }, 1000);
        }, 500);
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; updateParticles();

        // Spots Management
        let activeCount = 0;
        stageSpots.forEach(s => { if(s.isOn) activeCount++; });
        stageSpots.forEach((s) => {
            if (time > s.nextToggle) {
                if (s.isOn) { s.isOn = false; s.nextToggle = time + Math.random() * 2 + 1; } 
                else { if (activeCount < 3 && Math.random() > 0.5) { s.isOn = true; s.mode = (Math.random() > 0.7) ? 'track' : 'fixed'; if(s.mode === 'fixed') s.targetPos.set((Math.random()-0.5)*12, (Math.random()-0.5)*6, -2); s.nextToggle = time + Math.random() * 3 + 2; } else { s.nextToggle = time + 0.5; } }
            }
            const targetInt = s.isOn ? 30 : 0;
            s.intensity += (targetInt - s.intensity) * 0.1;
            s.light.intensity = s.intensity;
            s.beam.material.opacity = (s.isOn ? 0.08 : 0) * (s.intensity / 30);
            const baseCol = s.baseColor; s.lens.material.color.setRGB(baseCol.r * (s.isOn ? 1.5 : 0.5), baseCol.g * (s.isOn ? 1.5 : 0.5), baseCol.b * (s.isOn ? 1.5 : 0.5));
            const realTarget = (s.mode === 'track') ? robotGroup.position : s.targetPos;
            s.body.lookAt(realTarget); s.light.target.position.lerp(realTarget, 0.1); s.light.target.updateMatrixWorld();
        });

        if (robotState === 'intro') {
            if (introIndex < introScript.length) {
                const step = introScript[introIndex];
                if (time >= step.time) { 
                    if(step.text) showBubble(step.text, 3500); 
                    if(step.action === "hide_start") robotGroup.position.set(-15, 0, 0);
                    if(step.action === "enter_stage") targetPosition.set(4.0, 0, 0);
                    if(step.action === "look_around") { smoothRotate(robotGroup, 'y', -0.5, 0.05); smoothRotate(head, 'y', 0.8, 0.05); }
                    if(step.action === "surprise") { robotGroup.position.y += 0.5; head.rotation.x = -0.3; }
                    if(step.action === "wave") rightArm.rotation.z = Math.PI - 0.5;
                    introIndex++; 
                }
            } else if (time > 20) { robotState = 'moving'; pickNewTarget(); nextEventTime = time + 3; }
            if (introIndex > 0 && introIndex < 3) robotGroup.position.lerp(targetPosition, 0.02);
        } else if (robotState === 'moving') {
            robotGroup.position.lerp(targetPosition, 0.02);
            robotGroup.position.y += Math.sin(time * 2) * 0.005;
            smoothRotate(robotGroup, 'y', (targetPosition.x - robotGroup.position.x) * 0.05, 0.05);
            if (robotGroup.position.distanceTo(targetPosition) < 0.5) pickNewTarget();
            if (time > nextEventTime) {
                const r = Math.random();
                if(r < 0.15) startTeleport(); else if(r < 0.25) startExplosion(); else {
                    showBubble(getUniqueMessage(config.mode), 4000);
                    nextEventTime = time + 8;
                }
            }
        } else if (robotState === 'exploding') {
            parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += p.userData.rotVelocity.x; p.rotation.y += p.userData.rotVelocity.y; p.userData.velocity.multiplyScalar(0.95); });
        } else if (robotState === 'reassembling') {
            parts.forEach(p => { p.position.lerp(p.userData.origPos, 0.08); p.rotation.x += (p.userData.origRot.x - p.rotation.x) * 0.08; p.rotation.y += (p.userData.origRot.y - p.rotation.y) * 0.08; });
        }

        if(bubble && bubble.style.opacity == 1) {
            const headPos = robotGroup.position.clone(); headPos.y += 0.8; headPos.project(camera);
            const x = (headPos.x * .5 + .5) * width; const y = (headPos.y * -.5 + .5) * height;
            bubble.style.left = Math.max(20, Math.min(width - 270, x - 125)) + 'px';
            bubble.style.top = Math.max(80, y - 100) + 'px';
        }
        renderer.render(scene, camera);
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });
    animate();
}
