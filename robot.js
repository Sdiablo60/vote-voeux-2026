import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- MESSAGES VARIÉS ---
const messages = [
    "Salut l'équipe ! 👋",
    "Tout le monde est bien installé ? 💺",
    "Je vérifie les objectifs... 🧐",
    "Qui a le plus beau sourire ce soir ? 📸",
    "Silence... Moteur... Ça tourne ! 🎬",
    "N'oubliez pas de voter pour votre favori ! 🗳️",
    "Quelle ambiance de folie ! 🎉",
    "Je suis Clap-E, votre assistant préféré ! 🤖",
    "Il fait chaud sous les projecteurs, non ? 💡",
    "J'espère qu'il y a des petits fours... 🍪",
    "Psst... Vous me voyez bien ? 👀",
    "C'est parti pour le show ! 🚀",
    "Wow, cette vidéo était incroyable ! 🎞️",
    "Un petit coucou aux organisateurs ! 👋",
    "Je scane la salle... Vous êtes magnifiques ! ✨"
];

// --- SCÉNARIO D'INTRO ---
const introScript = [
    { time: 1.0, text: "Hum... C'est allumé ? 🎤", action: "look_around" },
    { time: 5.0, text: "Y'a quelqu'un dans cet écran ? 🤔", action: "approach" },
    { time: 8.5, text: "TOC ! TOC ! OUVREZ ! ✊", action: "knock" },
    { time: 12.0, text: "WOUAH ! 😱 Vous êtes nombreux !", action: "recoil" },
    { time: 16.0, text: "Bienvenue au Concours Vidéo 2026 ! ✨", action: "present" }
];

if (container) {
    try { initRobot(container); } catch (e) { console.error(e); }
}

function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    // SCENE
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 8); 

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // LUMIERES
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.0);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 2.0);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // --- ROBOT ---
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    
    // Matériaux
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.2 });
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111 });

    // Modélisation
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), whiteMat);
    const face = new THREE.Mesh(new THREE.CircleGeometry(0.55, 32), darkMat);
    face.position.set(0, 0, 0.68);
    head.add(face);

    const eyeGeo = new THREE.CircleGeometry(0.12, 32);
    const leftEye = new THREE.Mesh(eyeGeo, glowMat);
    leftEye.position.set(-0.25, 0.1, 0.70);
    head.add(leftEye);
    const rightEye = new THREE.Mesh(eyeGeo, glowMat);
    rightEye.position.set(0.25, 0.1, 0.70);
    head.add(rightEye);

    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.55, 0.9, 32), whiteMat);
    body.position.y = -0.9;

    function createArm(x) {
        const g = new THREE.Group();
        g.position.set(x, -0.7, 0);
        const s = new THREE.Mesh(new THREE.SphereGeometry(0.2), blueMat);
        g.add(s);
        const a = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.5), whiteMat);
        a.position.y = -0.3;
        g.add(a);
        return g;
    }
    const leftArm = createArm(-0.6);
    const rightArm = createArm(0.6);

    robotGroup.add(head);
    robotGroup.add(body);
    robotGroup.add(leftArm);
    robotGroup.add(rightArm);
    scene.add(robotGroup);

    // --- VARIABLES DE NAVIGATION ---
    let time = 0;
    let targetPosition = new THREE.Vector3(3.5, 0, 0); // Départ à droite
    robotGroup.position.copy(targetPosition);
    
    let robotState = 'intro'; 
    let introIndex = 0;
    let nextEventTime = 0;
    let lastMsgIndex = -1;
    
    // --- VARIABLE GLOBALE POUR LE TIMER DE LA BULLE ---
    // (C'est ce qui corrige le problème de disparition)
    let bubbleTimeout = null;

    // --- ANIMATION ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.015; 

        // GESTION Z-INDEX DYNAMIQUE
        if (robotGroup.position.z > 2) {
            container.style.zIndex = "15";
        } else {
            container.style.zIndex = "1";
        }

        // --- PHASE 1 : INTRO ---
        if (robotState === 'intro') {
            if (introIndex < introScript.length) {
                const step = introScript[introIndex];
                if (time >= step.time) {
                    // On force l'affichage pour 5 secondes minimum
                    showBubble(step.text, 5000);
                    
                    introIndex++;
                }
            } else if (time > 20) {
                robotState = 'moving';
                pickNewTarget();
                nextEventTime = time + 5;
            }

            // Mouvements Intro
            if (time < 5.0) { // Regarde
                robotGroup.rotation.y = Math.sin(time) * 0.3;
            }
            else if (time >= 5.0 && time < 8.5) { // Approche
                robotGroup.position.lerp(new THREE.Vector3(0, 0, 5), 0.02);
                robotGroup.rotation.y *= 0.95; 
            } 
            else if (time >= 8.5 && time < 12.0) { // Toc Toc
                robotGroup.position.z = 5 + Math.sin(time * 20) * 0.02; 
                rightArm.rotation.x = -Math.PI/2 + Math.sin(time * 15) * 0.3; 
            } 
            else if (time >= 12.0 && time < 20) { // Recul
                robotGroup.position.lerp(new THREE.Vector3(3.5, 0, 0), 0.03);
                rightArm.rotation.x *= 0.9;
                robotGroup.rotation.y = -0.2; 
            }
        } 
        
        // --- PHASE 2 : PATROUILLE ---
        else if (robotState === 'moving') {
            robotGroup.position.lerp(targetPosition, 0.008);
            robotGroup.rotation.y += (targetPosition.x - robotGroup.position.x) * 0.05 - robotGroup.rotation.y * 0.05;
            robotGroup.rotation.z = -(targetPosition.x - robotGroup.position.x) * 0.02;
            robotGroup.position.y += Math.sin(time * 1.5) * 0.001;
            
            leftArm.rotation.x = Math.sin(time * 2) * 0.1;
            rightArm.rotation.x = -Math.sin(time * 2) * 0.1;

            if (robotGroup.position.distanceTo(targetPosition) < 0.5) {
                pickNewTarget();
            }

            if (time > nextEventTime) {
                const rand = Math.random();
                if (rand < 0.3) {
                    startInspection(); 
                } else {
                    startSpeaking();   
                }
            }
        } 
        
        // --- PHASE 3 : PARLE ---
        else if (robotState === 'speaking') {
            robotGroup.position.y += Math.sin(time * 3) * 0.001;
            robotGroup.rotation.lerp(new THREE.Vector3(0,0,0), 0.05); 
            rightArm.rotation.z = Math.cos(time * 4) * 0.4 + 0.4; 
        }

        // --- PHASE 4 : INSPECTION ---
        else if (robotState === 'inspecting') {
            const inspectPos = new THREE.Vector3(Math.sin(time)*2, 0, 4.5);
            robotGroup.position.lerp(inspectPos, 0.02);
            robotGroup.rotation.y = Math.sin(time) * 0.2; 
            
            if (time > nextEventTime) {
                robotState = 'moving';
                pickNewTarget(); 
                nextEventTime = time + 10 + Math.random() * 10;
            }
        }

        updateBubblePosition();
        renderer.render(scene, camera);
    }

    function pickNewTarget() {
        const aspect = width / height;
        const vW = 7 * aspect; 
        let x, y;
        if (Math.random() > 0.5) {
            x = 3.0 + Math.random() * (vW * 0.4 - 3.0); 
        } else {
            x = -3.0 - Math.random() * (vW * 0.4 - 3.0); 
        }
        y = (Math.random() - 0.5) * 3; 
        targetPosition.set(x, y, 0);
    }

    function startSpeaking() {
        robotState = 'speaking';
        
        let newIndex;
        do {
            newIndex = Math.floor(Math.random() * messages.length);
        } while (newIndex === lastMsgIndex);
        lastMsgIndex = newIndex;

        showBubble(messages[newIndex], 6000); // 6 secondes pour lire
        
        nextEventTime = time + 10 + Math.random() * 15; 
        
        setTimeout(() => {
            if (robotState === 'speaking') {
                hideBubble();
                robotState = 'moving';
            }
        }, 6000);
    }

    function startInspection() {
        robotState = 'inspecting';
        showBubble("Je viens voir de plus près... 🧐", 4000);
        nextEventTime = time + 6; 
    }

    // --- FONCTION D'AFFICHAGE CORRIGÉE ---
    function showBubble(text, duration) {
        if(!bubble) return;
        
        // 1. Annuler tout effacement prévu précédemment
        if (bubbleTimeout) {
            clearTimeout(bubbleTimeout);
            bubbleTimeout = null;
        }

        // 2. Afficher le nouveau texte
        bubble.innerText = text;
        bubble.style.opacity = 1;
        
        // 3. Programmer l'effacement seulement si une durée est donnée
        if(duration) {
             bubbleTimeout = setTimeout(() => { 
                 hideBubble(); 
             }, duration);
        }
    }

    function hideBubble() {
        if(bubble) bubble.style.opacity = 0;
    }

    function updateBubblePosition() {
        if(!bubble || bubble.style.opacity == 0) return;
        
        const headPos = robotGroup.position.clone();
        headPos.y += 0.8; 
        headPos.project(camera);
        
        const x = (headPos.x * .5 + .5) * width;
        const y = (headPos.y * -.5 + .5) * height;

        let finalX = Math.max(120, Math.min(width - 120, x));
        let finalY = Math.max(50, y - 80);

        bubble.style.left = finalX + 'px';
        bubble.style.top = finalY + 'px';
        bubble.style.transform = 'translate(-50%, 0)';
    }

    window.addEventListener('resize', () => {
        width = window.innerWidth;
        height = window.innerHeight;
        renderer.setSize(width, height);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
    });

    animate();
}
