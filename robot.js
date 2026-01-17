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

// --- GESTION ERREURS ---
if (container) {
    try {
        initRobot(container);
    } catch (e) {
        console.error("CRASH ROBOT:", e);
        // Affiche l'erreur exacte à l'écran pour le diagnostic
        container.innerHTML = `<div style='color:red; font-family:monospace; text-align:center; padding-top:50px; background:rgba(0,0,0,0.8);'>
            ERREUR: ${e.message}<br>
            <small>Vérifiez la console (F12) pour les détails.</small>
        </div>`;
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
    
    // Style forcé
    container.style.position = 'fixed'; container.style.top = '0'; container.style.left = '0';
    container.style.width = '100%'; container.style.height = '100%';
    container.style.zIndex = '1'; container.style.pointerEvents = 'none';
    
    const scene = new THREE.Scene();
    
    // CAMÉRA
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 13); // Distance de sécurité

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // LUMIÈRES (Pour éclairer les parties non-émissives)
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.0); 
    scene.add(ambientLight);
    
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(0, 5, 10);
    scene.add(dirLight);

    const explosionLight = new THREE.PointLight(0xffaa00, 0, 20);
    explosionLight.position.set(0, 0, 5);
    scene.add(explosionLight);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    // Matériaux basiques mais sûrs
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.3 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); // Yeux brillants
    const greyMat = new THREE.MeshStandardMaterial({ color: 0x888888 });
    
    // Construction Robot (Simplifiée pour éviter les erreurs de variables)
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

    // Ajout au groupe et préparation physique pour explosion
    [head, body, leftArm, rightArm].forEach(p => {
        p.userData = { 
            origPos: p.position.clone(), 
            origRot: p.rotation.clone(), 
            velocity: new THREE.Vector3() 
        };
        if(p!==head && p!==body) robotGroup.add(p);
    });
    robotGroup.add(head); robotGroup.add(body);
    scene.add(robotGroup);
    
    // Référence globale pour l'animation
    const parts = [head, body, leftArm, rightArm];

    // --- SPOTS "ULTRA VISIBLES" ---
    const stageSpots = [];
    
    // Matériau Spot : Gris Clair + Emission (Brille un peu en blanc)
    const housingMat = new THREE.MeshStandardMaterial({ 
        color: 0xCCCCCC, 
        metalness: 0.5, 
        roughness: 0.5,
        emissive: 0x222222 // Auto-éclairé
    });
    const barnMat = new THREE.MeshStandardMaterial({ color: 0x333333, side: THREE.DoubleSide });

    function createSpot(x, y, colorInt, isBottom) {
        const group = new THREE.Group();
        group.position.set(x, y, 0);

        // Support
        const bracket = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.05, 8, 16, Math.PI), housingMat);
        bracket.rotation.z = isBottom ? 0 : Math.PI;
        group.add(bracket);

        // Corps
        const bodyGroup = new THREE.Group();
        group.add(bodyGroup);
        const box = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.6, 0.6), housingMat);
        box.position.z = 0.3; bodyGroup.add(box);
        const cyl = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.6, 32), housingMat);
        cyl.rotation.x = Math.PI/2; cyl.position.z = -0.2; bodyGroup.add(cyl);

        // Lentille (BASIC MATERIAL = Brille toujours)
        const lens = new THREE.Mesh(
            new THREE.CircleGeometry(0.35, 32), 
            new THREE.MeshBasicMaterial({ color: colorInt }) 
        );
        lens.position.set(0, 0, -0.51); bodyGroup.add(lens);

        // Volets
        const doorGeo = new THREE.PlaneGeometry(0.6, 0.3);
        const topDoor = new THREE.Mesh(doorGeo, barnMat); topDoor.position.set(0, 0.45, -0.5); topDoor.rotation.x = Math.PI/4; bodyGroup.add(topDoor);
        const botDoor = new THREE.Mesh(doorGeo, barnMat); botDoor.position.set(0, -0.45, -0.5); botDoor.rotation.x = -Math.PI/4; bodyGroup.add(botDoor);

        // Faisceau (Beam)
        const beamGeo = new THREE.ConeGeometry(0.4, 20, 32, 1, true);
        beamGeo.translate(0, -10, 0); beamGeo.rotateX(-Math.PI/2);
        const beamMat = new THREE.MeshBasicMaterial({ 
            color: colorInt, 
            transparent: true, 
            opacity: 0.2, // Bien visible
            side: THREE.DoubleSide, 
            blending: THREE.AdditiveBlending, 
            depthWrite: false 
        });
        const beam = new THREE.Mesh(beamGeo, beamMat);
        beam.position.z = -0.6; bodyGroup.add(beam);

        // Lumière (Optionnelle pour l'effet visuel, mais garde pour le réalisme)
        const light = new THREE.SpotLight(colorInt, 10);
        light.angle = 0.3; light.distance = 50;
        bodyGroup.add(light); bodyGroup.add(light.target);

        scene.add(group);
        bodyGroup.lookAt(0, 0, 0); // Regarde le centre
        light.target.position.set(0,0,0);

        return { 
            group, beam, light, lens,
            baseIntensity: 10, timeOff: Math.random() * 100 
        };
    }

    // Positions et Couleurs
    const colors = [0xFFFF00, 0x00FFFF, 0x00FF00, 0xFFA500];
    // HAUT (Y=3.5)
    [-7, -2.5, 2.5, 7].forEach((x, i) => stageSpots.push(createSpot(x, 3.5, colors[i%4], false)));
    // BAS (Y=-3.5)
    [-7, -2.5, 2.5, 7].forEach((x, i) => stageSpots.push(createSpot(x, -3.5, colors[(i+2)%4], true)));

    // --- ANIMATION ---
    let time = 0;
    let targetPos = new THREE.Vector3(4, 0, 0);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;
    let introIndex = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        // Spots
        stageSpots.forEach(s => {
            const pulse = Math.sin(time * 3 + s.timeOff) * 0.2 + 0.8;
            if(s.beam) s.beam.material.opacity = 0.2 * pulse;
            if(s.light) s.light.intensity = s.baseIntensity * pulse;
        });

        // Robot Mouvement
        if (robotState === 'intro') {
            const script = [
                {t:0, a:"hide"}, {t:1, a:"enter"}, {t:4, a:"look"}, {t:7, a:"surprise"}, {t:10, a:"wave"}
            ];
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
                if(r<0.2) { 
                    robotState = 'exploding'; 
                    showBubble(getUniqueMessage('explosion'), 3000);
                    setTimeout(() => {
                        parts.forEach(p => p.userData.velocity.set((Math.random()-0.5)*0.5, (Math.random()-0.5)*0.5, (Math.random()-0.5)*0.5));
                        setTimeout(() => { robotState = 'reassembling'; setTimeout(() => { robotState='moving'; pickNewTarget(); }, 2000); }, 3000);
                    }, 500);
                } else {
                    robotState = 'speaking';
                    showBubble(getUniqueMessage(config.mode), 4000);
                    setTimeout(() => { robotState='moving'; pickNewTarget(); }, 4000);
                }
                nextEvent = time + 5 + Math.random()*5;
            }
        }
        else if (robotState === 'exploding') {
            parts.forEach(p => { p.position.add(p.userData.velocity); p.rotation.x += 0.1; p.userData.velocity.multiplyScalar(0.95); });
        }
        else if (robotState === 'reassembling') {
            parts.forEach(p => { p.position.lerp(p.userData.origPos, 0.1); p.rotation.x *= 0.9; });
        }
        else if (robotState === 'speaking') {
            robotGroup.position.lerp(targetPos, 0.01);
            mouth.scale.set(1, 1+Math.sin(time*20)*0.3, 1);
        }

        // Bulle
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
