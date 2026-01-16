import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

// --- TEXTES ÉTENDUS ---
const MESSAGES_BAG = {
    attente: ["Bienvenue ! ✨", "Installez-vous.", "Ravi de vous voir !", "La soirée va être belle !", "Prêts pour le show ?", "J'adore l'ambiance !", "Coucou la technique ! 👷"],
    vote_off: ["Les votes sont CLOS ! 🛑", "Les jeux sont faits.", "Le podium arrive... 🏆", "Suspens... 😬", "La régie gère ! ⚡"],
    photos: ["Photos ! 📸", "Souriez !", "On partage ! 📲", "Vous êtes beaux !", "Selfie time ! 🤳"],
    danse: ["Dancefloor ! 💃", "Je sens le rythme ! 🎵", "Regardez-moi ! 🤖", "On se bouge ! 🙌"],
    explosion: ["Surchauffe ! 🔥", "J'ai perdu la tête... 🤯", "Rassemblement... 🧲"],
    cache_cache: ["Coucou ! 👋", "Me revoilà !", "Magie ! ⚡"]
};

const usedMessages = {};
function getUniqueMessage(category) {
    if (!usedMessages[category]) usedMessages[category] = [];
    if (usedMessages[category].length >= MESSAGES_BAG[category].length) usedMessages[category] = [];
    let available = MESSAGES_BAG[category].filter(m => !usedMessages[category].includes(m));
    let msg = available[Math.floor(Math.random() * available.length)];
    usedMessages[category].push(msg);
    return msg;
}

if (container) { initRobot(container); }

function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    const scene = new THREE.Scene();
    // Caméra inclinée pour bien voir le plafond et le sol
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 12); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8); 
    scene.add(ambientLight);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x000000 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat);
    head.scale.set(1.4, 1.0, 0.75);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat);
    face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6); head.add(face);
    
    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat);
    mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);

    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat);
    body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    
    const leftArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    leftArm.position.set(-0.8, -0.8, 0);
    const rightArm = new THREE.Mesh(new THREE.CapsuleGeometry(0.13, 0.5, 4, 8), whiteMat);
    rightArm.position.set(0.8, -0.8, 0);

    robotGroup.add(head, body, leftArm, rightArm);
    scene.add(robotGroup);

    // --- SPOTS 3D (RÉALISTES) ---
    const stageSpots = [];
    // Matériau gris clair pour que les boîtiers soient visibles sur le noir
    const spotMat = new THREE.MeshStandardMaterial({ color: 0x888888, metalness: 0.8, roughness: 0.2 });

    function createSpot(x, y, isBottom) {
        const group = new THREE.Group();
        group.position.set(x, y, 2); // Placé un peu en avant (z=2)

        // Boîtier (Carré + Cylindre)
        const box = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.6, 0.6), spotMat);
        const cyl = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 0.5, 16), spotMat);
        cyl.rotation.x = Math.PI/2; cyl.position.z = -0.4;
        
        // Volets (Barn Doors)
        const door = new THREE.Mesh(new THREE.PlaneGeometry(0.5, 0.3), spotMat);
        door.position.set(0, 0.4, -0.6); door.rotation.x = Math.PI/4;
        
        const bodySpot = new THREE.Group();
        bodySpot.add(box, cyl, door);
        group.add(bodySpot);

        // Faisceau
        const beam = new THREE.Mesh(
            new THREE.ConeGeometry(0.7, 15, 32, 1, true),
            new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false })
        );
        beam.translateY(-7.5); beam.rotateX(-Math.PI/2);
        bodySpot.add(beam);

        const light = new THREE.SpotLight(0xffffff, 0);
        light.angle = 0.4; light.penumbra = 0.3; group.add(light, light.target);
        
        scene.add(group);
        return { group, bodySpot, light, beam, nextChange: Math.random() * 5, isOn: false };
    }

    // Positions des spots (Haut et Bas)
    const pos = [-7, -3.5, 3.5, 7];
    pos.forEach(x => stageSpots.push(createSpot(x, 6, false)));
    pos.forEach(x => stageSpots.push(createSpot(x, -6, true)));

    // --- LOGIQUE ANIMATION ---
    let time = 0;
    let targetPos = new THREE.Vector3(4, 0, 0);
    let robotState = (config.mode === 'attente') ? 'intro' : 'moving';
    let nextEvent = 0;

    function animate() {
        requestAnimationFrame(animate);
        time += 0.015;

        // Gestion Spots
        stageSpots.forEach((s, i) => {
            if (time > s.nextChange) {
                s.isOn = !s.isOn;
                s.light.color.setHSL(Math.random(), 1, 0.6);
                s.beam.material.color.copy(s.light.color);
                s.nextChange = time + Math.random() * 3 + 1;
                s.tracking = Math.random() > 0.7; // 30% de chance de suivre le bot
            }
            const targetInt = s.isOn ? 25 : 0;
            s.light.intensity += (targetInt - s.light.intensity) * 0.1;
            s.beam.material.opacity = (s.light.intensity / 25) * 0.15;
            
            let lookAtPos = s.tracking ? robotGroup.position : new THREE.Vector3(s.group.position.x, 0, 0);
            s.bodySpot.lookAt(lookAtPos);
            s.light.target.position.copy(lookAtPos);
        });

        // Mouvements Robot
        if (robotState === 'moving') {
            robotGroup.position.lerp(targetPos, 0.02);
            if (robotGroup.position.distanceTo(targetPos) < 0.5) {
                const side = Math.random() > 0.5 ? 1 : -1;
                targetPos.set(side * (4.5 + Math.random() * 2), (Math.random() - 0.5) * 4, 0);
            }
            if (time > nextEvent) {
                const msg = getUniqueMessage(config.mode === 'photos' && Math.random() > 0.5 ? 'danse' : config.mode);
                showBubble(msg, 4000);
                nextEvent = time + 6 + Math.random() * 5;
            }
            mouth.scale.y = 1 + Math.sin(time * 20) * 0.2;
        }

        // Bulle position (anti-coupe)
        if (bubble && bubble.style.opacity == 1) {
            const vector = robotGroup.position.clone(); vector.y += 1; vector.project(camera);
            const x = (vector.x * .5 + .5) * width;
            bubble.style.left = Math.max(150, Math.min(width - 150, x)) + 'px';
            bubble.style.top = ((vector.y * -.5 + .5) * height - 80) + 'px';
        }

        renderer.render(scene, camera);
    }

    function showBubble(text, duration) {
        bubble.innerText = text; bubble.style.opacity = 1;
        setTimeout(() => bubble.style.opacity = 0, duration);
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth; height = window.innerHeight;
        renderer.setSize(width, height); camera.aspect = width / height; camera.updateProjectionMatrix();
    });

    animate();
}
