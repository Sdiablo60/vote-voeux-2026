import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');
const config = window.robotConfig || { mode: 'attente', titre: 'Événement' };

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

if (container) { initRobot(container); }

function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    const scene = new THREE.Scene();
    
    // Caméra à Z=12 pour avoir du recul
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 12); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // LUMIERE D'AMBIANCE FORTE (Pour voir les spots gris)
    const ambientLight = new THREE.AmbientLight(0xffffff, 2.0); 
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

    // --- SPOTS 3D (VISIBLE ET REPOSITIONNÉS) ---
    const stageSpots = [];
    
    // MATERIAU CLAIR (Gris Argent) pour être visible sur fond noir
    const spotMat = new THREE.MeshStandardMaterial({ 
        color: 0xC0C0C0, // Gris clair / Argent
        metalness: 0.6, 
        roughness: 0.3 
    });
    
    // Matériau Noir pour l'intérieur des volets
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x222222 });

    function createSpot(x, y, isBottom) {
        const group = new THREE.Group();
        // Z=1 pour être un peu devant le plan zéro, mais derrière le robot (si robot z=0)
        // Le robot bouge en Z, donc on met les spots en retrait ou au même niveau
        group.position.set(x, y, 0); 

        const bodySpot = new THREE.Group();
        group.add(bodySpot);

        // Boîtier Principal (Visible)
        const box = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.7, 0.8), spotMat);
        
        // Cylindre avant
        const cyl = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.5, 32), spotMat);
        cyl.rotation.x = Math.PI/2; cyl.position.z = -0.5;
        
        // Volets (Barn Doors) - Gris extérieur, Noir intérieur
        const doorGeo = new THREE.BoxGeometry(0.6, 0.05, 0.6);
        
        const topDoor = new THREE.Mesh(doorGeo, spotMat);
        topDoor.position.set(0, 0.5, -0.8); topDoor.rotation.x = Math.PI/3;
        
        const botDoor = new THREE.Mesh(doorGeo, spotMat);
        botDoor.position.set(0, -0.5, -0.8); botDoor.rotation.x = -Math.PI/3;

        bodySpot.add(box, cyl, topDoor, botDoor);

        // Faisceau Volumétrique (Beam)
        const beam = new THREE.Mesh(
            new THREE.ConeGeometry(0.8, 20, 32, 1, true), // Cône long
            new THREE.MeshBasicMaterial({ 
                color: 0xffffff, 
                transparent: true, 
                opacity: 0, 
                blending: THREE.AdditiveBlending, 
                depthWrite: false,
                side: THREE.DoubleSide
            })
        );
        beam.translateY(-10); // Décale le cône
        beam.rotateX(-Math.PI/2); // Pointe vers l'avant
        bodySpot.add(beam);

        // Lumière réelle
        const light = new THREE.SpotLight(0xffffff, 0);
        light.angle = 0.5; 
        light.penumbra = 0.4; 
        light.distance = 60;
        group.add(light); 
        group.add(light.target); // Nécessaire
        
        scene.add(group);
        
        return { 
            group, bodySpot, light, beam, 
            nextChange: Math.random() * 5, 
            isOn: false, 
            tracking: false 
        };
    }

    // --- POSITIONS AJUSTEES (DANS L'ECRAN) ---
    // Y = 4.2 pour le HAUT (descendu)
    // Y = -4.0 pour le BAS (remonté)
    const posX = [-6, -2, 2, 6];
    
    posX.forEach(x => stageSpots.push(createSpot(x, 4.2, false))); // HAUT
    posX.forEach(x => stageSpots.push(createSpot(x, -4.0, true))); // BAS

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
                // Aléatoire : Allumé ou Eteint
                s.isOn = Math.random() > 0.6; // 40% chance d'être allumé
                
                // Couleur aléatoire
                const hue = Math.random();
                s.light.color.setHSL(hue, 1, 0.5);
                s.beam.material.color.copy(s.light.color);
                
                s.nextChange = time + Math.random() * 3 + 1; // Durée état
                s.tracking = Math.random() > 0.7; // 30% chance de suivre le robot
            }

            // Transition douce lumière
            const targetInt = s.isOn ? 30 : 0;
            s.light.intensity += (targetInt - s.light.intensity) * 0.1;
            
            // Opacité du faisceau liée à l'intensité (plus visible maintenant 0.2 max)
            s.beam.material.opacity = (s.light.intensity / 30) * 0.15;
            
            // Orientation
            let lookAtPos;
            if (s.tracking) {
                lookAtPos = robotGroup.position;
            } else {
                // Position "Repos" : pointe vers le centre ou un peu au hasard
                lookAtPos = new THREE.Vector3(s.group.position.x * 0.5, 0, 0);
            }
            
            s.bodySpot.lookAt(lookAtPos);
            s.light.target.position.copy(lookAtPos);
        });

        // Mouvements Robot
        if (robotState === 'moving') {
            robotGroup.position.lerp(targetPos, 0.02);
            robotGroup.position.y += Math.sin(time*2)*0.002; // Flottement

            if (robotGroup.position.distanceTo(targetPos) < 0.5) {
                const side = Math.random() > 0.5 ? 1 : -1;
                // Reste sur les cotés (Zone > 3.5 ou < -3.5)
                targetPos.set(side * (3.5 + Math.random() * 2), (Math.random() - 0.5) * 3, 0);
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
            // Marges de sécurité pour la bulle
            bubble.style.left = Math.max(150, Math.min(width - 150, x)) + 'px';
            bubble.style.top = Math.max(50, ((vector.y * -.5 + .5) * height - 100)) + 'px';
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
