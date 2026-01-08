import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- MESSAGES ALÉATOIRES (APRÈS INTRO) ---
const randomMessages = [
    "J'adore le cinéma ! 🎬",
    "Qui a le meilleur costume ce soir ? 👔",
    "N'oubliez pas de voter ! 🗳️",
    "Une petite photo ? 📸",
    "Silence... Moteur... Action ! 📢",
    "Je suis Clap-E, votre serviteur ! 🤖",
    "Quelle ambiance incroyable ! 🎉",
    "C'est mon premier tapis rouge... 😳",
    "Devinette : Quel est le comble pour une caméra ? De perdre la pellicule ! 🎞️"
];

// --- SCÉNARIO D'INTRODUCTION (Chronologique) ---
const introScript = [
    { time: 1.0, text: "Hum... C'est allumé ? 🎤", action: "look_around" },
    { time: 4.0, text: "Y'a quelqu'un dans cet écran ? 🤔", action: "approach" },
    { time: 7.0, text: "TOC ! TOC ! OUVREZ ! ✊", action: "knock" },
    { time: 10.0, text: "WOUAH ! 😱 Vous êtes nombreux !", action: "recoil" },
    { time: 14.0, text: "Bienvenue au Concours Vidéo 2026 ! ✨", action: "present" }
];

if (container) {
    try { initRobot(container); } catch (e) { console.error(e); }
}

function initRobot(container) {
    let width = window.innerWidth;
    let height = window.innerHeight;
    
    // 1. SCÈNE
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100);
    camera.position.set(0, 0, 8); // Caméra reculée

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // 2. LUMIÈRES
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.0);
    scene.add(ambientLight);
    const dirLight = new THREE.DirectionalLight(0xffffff, 2.0);
    dirLight.position.set(5, 10, 7);
    scene.add(dirLight);

    // 3. ROBOT
    const robotGroup = new THREE.Group();
    robotGroup.scale.set(0.45, 0.45, 0.45);
    
    // Matériaux
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.2 });
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111 });

    // Tête
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), whiteMat);
    const face = new THREE.Mesh(new THREE.CircleGeometry(0.55, 32), darkMat);
    face.position.set(0, 0, 0.68);
    head.add(face);

    // Yeux
    const eyeGeo = new THREE.CircleGeometry(0.12, 32);
    const leftEye = new THREE.Mesh(eyeGeo, glowMat);
    leftEye.position.set(-0.25, 0.1, 0.70);
    head.add(leftEye);
    const rightEye = new THREE.Mesh(eyeGeo, glowMat);
    rightEye.position.set(0.25, 0.1, 0.70);
    head.add(rightEye);

    // Corps
    const body = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.55, 0.9, 32), whiteMat);
    body.position.y = -0.9;

    // Bras
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
    
    // On force le démarrage à droite (Visible tout de suite)
    let targetPosition = new THREE.Vector3(2.5, 0, 0);
    robotGroup.position.copy(targetPosition);
    
    let robotState = 'intro'; // intro, patrol, speaking, moving
    let introIndex = 0;
    let nextEventTime = 0; // Timer pour les messages aléatoires

    // --- ANIMATION ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.02; // Horloge globale

        // --- PHASE 1 : SCÉNARIO D'INTRODUCTION ---
        if (robotState === 'intro') {
            
            // Gestion du script temporel
            if (introIndex < introScript.length) {
                const step = introScript[introIndex];
                
                // Si c'est le moment de l'étape
                if (time >= step.time) {
                    // Afficher le message
                    showBubble(step.text, 3000);
                    
                    // Exécuter l'action spéciale
                    performAction(step.action);
                    
                    introIndex++;
                }
            } else if (time > 18) {
                // Fin de l'intro après 18 secondes -> Passage en mode patrouille
                robotState = 'moving';
                pickNewTarget();
            }

            // Animations spécifiques pendant l'intro
            if (time > 4 && time < 7) { 
                // Approche Zoom (Lerp vers Z=5)
                robotGroup.position.lerp(new THREE.Vector3(0, 0, 5), 0.05);
            } 
            else if (time > 7 && time < 10) {
                // Toc Toc (Vibration rapide sur Z et bras)
                robotGroup.position.z = 5 + Math.sin(time * 30) * 0.05;
                rightArm.rotation.x = -Math.PI / 2 + Math.sin(time * 20) * 0.5; // Bras levé qui frappe
            } 
            else if (time > 10 && time < 14) {
                // Recul de peur (Lerp vers position de sécurité)
                robotGroup.position.lerp(new THREE.Vector3(2.5, 0, 0), 0.05);
                rightArm.rotation.x = 0; // Bras redescend
            }

        } 
        
        // --- PHASE 2 : VIE NORMALE (Patrouille) ---
        else if (robotState === 'moving') {
            
            // Déplacement fluide vers la cible
            robotGroup.position.lerp(targetPosition, 0.01);
            
            // Orientation douce
            robotGroup.rotation.y = (targetPosition.x - robotGroup.position.x) * 0.1;
            robotGroup.rotation.z = -(targetPosition.x - robotGroup.position.x) * 0.05;
            
            // Respiration
            robotGroup.position.y += Math.sin(time * 2) * 0.002;

            // Si arrivé, changer de cible
            if (robotGroup.position.distanceTo(targetPosition) < 0.5) {
                pickNewTarget();
            }

            // Déclencheur parole aléatoire
            if (time > nextEventTime) {
                startSpeaking();
            }
        } 
        
        // --- PHASE 3 : PARLE (Immobile) ---
        else if (robotState === 'speaking') {
            // STOP TOTAL du déplacement X/Y/Z
            // Juste un petit flottement sur place
            robotGroup.position.y += Math.sin(time * 3) * 0.001;
            
            // Regarde le public
            robotGroup.rotation.set(0, 0, 0);
            
            // Gestuelle
            rightArm.rotation.z = Math.cos(time * 5) * 0.5 + 0.5; // Coucou
        }

        updateBubblePosition();
        renderer.render(scene, camera);
    }

    // --- ACTIONS ---

    function performAction(actionName) {
        if (actionName === 'look_around') {
            // Petite rotation tête (simulée par rotation du groupe pour simplifier)
            // L'animation continue dans la boucle principale
        }
    }

    function pickNewTarget() {
        // Choix d'une position sûre (Gauche ou Droite, jamais centre)
        const aspect = width / height;
        const vW = 7 * aspect; // Largeur visible approx
        
        let x, y;
        // On alterne ou aléatoire
        if (Math.random() > 0.5) {
            // Droite
            x = 2.5 + Math.random() * (vW * 0.4 - 2.5);
        } else {
            // Gauche
            x = -2.5 - Math.random() * (vW * 0.4 - 2.5);
        }
        y = (Math.random() - 0.5) * 4; // Haut/Bas
        
        targetPosition.set(x, y, 0);
    }

    function startSpeaking() {
        robotState = 'speaking';
        
        // Choisir un message
        const msg = randomMessages[Math.floor(Math.random() * randomMessages.length)];
        showBubble(msg, 5000); // 5 secondes de lecture
        
        // Calcul du prochain événement (dans 10 à 20 sec)
        nextEventTime = time + 10 + Math.random() * 10;

        // Reprise du mouvement après la lecture
        setTimeout(() => {
            if (robotState === 'speaking') {
                hideBubble();
                robotState = 'moving';
            }
        }, 5000);
    }

    function showBubble(text, duration) {
        if(!bubble) return;
        bubble.innerText = text;
        bubble.style.opacity = 1;
        // Le cache est géré par le timeout du state 'speaking' ou l'intro
        if(duration && robotState === 'intro') {
             setTimeout(() => { hideBubble(); }, duration);
        }
    }

    function hideBubble() {
        if(bubble) bubble.style.opacity = 0;
    }

    function updateBubblePosition() {
        if(!bubble || bubble.style.opacity == 0) return;
        
        const headPos = robotGroup.position.clone();
        headPos.y += 0.8; // Au dessus de la tête
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

    // Lancement
    animate();
    // Initialise le timer de parole pour l'après-intro
    nextEventTime = 20; 
}
