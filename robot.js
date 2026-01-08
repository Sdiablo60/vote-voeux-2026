import * as THREE from 'three';

const container = document.getElementById('robot-container');
const bubble = document.getElementById('robot-bubble');

// --- MESSAGES DU SCÉNARIO D'INTRO ---
const introScript = [
    { time: 1, text: "Oh... ? Il y a quelqu'un ? 🤔" },
    // (Entre temps 3 et 5 il s'approche)
    { time: 5, text: "TOC ! TOC ! ✊ Vous m'entendez ?" },
    // (Entre temps 8 et 10 il recule)
    { time: 10.5, text: "Wouah ! 🤩 Mais vous êtes nombreux !" },
    { time: 14, text: "Bienvenue au grand concours vidéo 2026 ! ✨" }
];

// --- MESSAGES POUR LA SUITE (BOUCLE) ---
// Mélange de présentations, blagues et interactions
const engagementMessages = [
    "Je me présente (pour les retardataires) : Clap-E, votre hôte ! 🤖",
    "Alors, qui a apporté le popcorn ? 🍿",
    "Silence sur le plateau... ça va commencer ! 🤫",
    "Une blague de cinéma ? Pourquoi le film est-il allé en prison ? Parce qu'il a été 'capturé' ! 🥁",
    "N'oubliez pas : votre vote est décisif ! 🗳️",
    "Je vois des favoris dans la salle... 👀",
    "Devinette : J'ai un œil mais je ne vois rien. Qui suis-je ? ... Une caméra ! (Bon ok, moi j'en ai deux).",
    "Quelle ambiance incroyable ce soir ! 🎉",
    "Je suis Clap-E, le robot qui aime les happy ends ! 🎬"
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
    camera.position.set(0, 0, 8); // Recul caméra standard

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
    // Taille standard (45%)
    const standardScale = 0.45;
    // Taille "Toc Toc" (plus gros, 70%)
    const knockScale = 0.7;
    
    robotGroup.scale.set(standardScale, standardScale, standardScale);
    
    // Matériaux
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
    const blueMat = new THREE.MeshStandardMaterial({ color: 0x3388ff, roughness: 0.2 });
    const glowMat = new THREE.MeshBasicMaterial({ color: 0x00ffff });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111 });

    // Construction
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

    // --- VARIABLES D'ÉTAT ET DE NAVIGATION ---
    let time = 0;
    let introStep = 0; // Étape du scénario d'intro
    let introFinished = false;
    
    // États possibles : 'intro_waiting', 'intro_approaching', 'intro_knocking', 'intro_retreating', 'engaged_moving', 'engaged_speaking'
    let robotState = 'intro_waiting'; 

    // Position Cible pour la navigation
    let targetPosition = new THREE.Vector3(0, 0, 0);
    let currentSide = (Math.random() > 0.5) ? 'left' : 'right';
    // Position cible pour le "Toc Toc" (proche caméra, légèrement décalé du centre)
    const knockPosition = new THREE.Vector3(1, 0.5, 3.5); 

    // Timers pour la phase d'engagement
    let engagementTimer = 0;
    let teleportTimer = 0;

    // Initialisation position de départ (visible sur le côté)
    pickTargetOnCurrentSide();
    robotGroup.position.copy(targetPosition);

    // --- FONCTIONS UTILITAIRES ---
    function pickTargetOnCurrentSide() {
        const aspect = width / height;
        const vH = 7; 
        const vW = vH * aspect;
        let minX, maxX;
        // Zone de sécurité stricte autour du texte central
        if (currentSide === 'left') { minX = -vW * 0.45; maxX = -2.5; } 
        else { minX = 2.5; maxX = vW * 0.45; }
        targetPosition.set(
            Math.random() * (maxX - minX) + minX,
            (Math.random() - 0.5) * vH * 0.8,
            0 // Z est toujours 0 en mode normal
        );
    }

    function showBubble(text, duration = 4000) {
        if(!bubble) return;
        bubble.innerText = text;
        bubble.style.opacity = 1;
        setTimeout(() => { hideBubble(); }, duration);
    }

    function hideBubble() {
        if(bubble) bubble.style.opacity = 0;
    }

    function updateBubblePosition() {
        if(!bubble || bubble.style.opacity == 0) return;
        const headPos = robotGroup.position.clone();
        headPos.y += 0.7; // Au dessus de la tête
        headPos.project(camera);
        const x = (headPos.x * .5 + .5) * width;
        const y = (headPos.y * -.5 + .5) * height;
        // Garde la bulle dans l'écran (marges ajustées pour le zoom)
        let finalX = Math.max(140, Math.min(width - 140, x));
        let finalY = Math.max(80, y - 120);
        bubble.style.left = finalX + 'px';
        bubble.style.top = finalY + 'px';
        bubble.style.transform = 'translate(-50%, 0)';
    }

    // --- BOUCLE D'ANIMATION PRINCIPALE ---
    function animate() {
        requestAnimationFrame(animate);
        time += 0.02;

        // GESTION DU SCÉNARIO D'INTRODUCTION (Basé sur le temps)
        if (!introFinished) {
            // Déclenchement des bulles du scénario
            if (introStep < introScript.length && time > introScript[introStep].time) {
                showBubble(introScript[introStep].text, 3500);
                introStep++;
            }

            // Changement d'état du robot selon le temps
            if (time > 3 && time < 5 && robotState !== 'intro_approaching') {
                robotState = 'intro_approaching';
                hideBubble(); // Cache la bulle pendant le mouvement rapide
            } else if (time > 5 && time < 8 && robotState !== 'intro_knocking') {
                robotState = 'intro_knocking';
            } else if (time > 8 && time < 10.5 && robotState !== 'intro_retreating') {
                robotState = 'intro_retreating';
                hideBubble();
                pickTargetOnCurrentSide(); // Prépare le point de retour
            } else if (time > 17 && !introFinished) {
                introFinished = true;
                robotState = 'engaged_moving'; // Fin de l'intro, début de la boucle
            }
        }

        // --- MACHINES À ÉTATS DU ROBOT ---

        switch (robotState) {
            // --- PHASES D'INTRODUCTION ---
            case 'intro_waiting':
                // Regarde autour, l'air confus
                robotGroup.rotation.y = Math.sin(time * 1.5) * 0.3;
                robotGroup.rotation.x = Math.sin(time * 2) * 0.1;
                rightArm.rotation.z = Math.sin(time * 3) * 0.1; // Se gratte la tête ?
                break;

            case 'intro_approaching':
                // Fonce vers la caméra et grossit
                robotGroup.position.lerp(knockPosition, 0.05);
                // Lerp manuel pour l'échelle
                robotGroup.scale.x += (knockScale - robotGroup.scale.x) * 0.05;
                robotGroup.scale.y = robotGroup.scale.z = robotGroup.scale.x;
                // Regarde droit devant
                robotGroup.rotation.set(0,0,0);
                break;

            case 'intro_knocking':
                // Est proche, fait le geste de toquer
                // Petit mouvement rapide d'avant en arrière sur Z
                robotGroup.position.z = knockPosition.z + Math.sin(time * 20) * 0.05;
                // Le bras droit toque
                rightArm.rotation.x = -Math.abs(Math.sin(time * 15)) * 0.8;
                rightArm.rotation.z = 0.2;
                break;

            case 'intro_retreating':
                // Recule vers sa position de patrouille et reprend sa taille normale
                robotGroup.position.lerp(targetPosition, 0.05);
                 // Lerp manuel pour l'échelle inverse
                robotGroup.scale.x += (standardScale - robotGroup.scale.x) * 0.05;
                robotGroup.scale.y = robotGroup.scale.z = robotGroup.scale.x;
                 // Regarde la foule (la caméra) en reculant
                 robotGroup.rotation.y *= 0.9;
                break;

            // --- PHASES D'ENGAGEMENT (BOUCLE NORMALE) ---
            case 'engaged_moving':
                engagementTimer += 0.02;
                teleportTimer += 0.02;

                // Mouvement fluide de patrouille latérale
                robotGroup.position.lerp(targetPosition, 0.015);
                // Orientation douce
                robotGroup.rotation.y += (targetPosition.x - robotGroup.position.x) * 0.02 - robotGroup.rotation.y * 0.02;
                robotGroup.rotation.z = (robotGroup.position.x - targetPosition.x) * 0.05;

                // Animation standard (vol + bras)
                robotGroup.position.y += Math.sin(time * 2) * 0.002;
                rightArm.rotation.x = Math.sin(time * 3) * 0.2;
                leftArm.rotation.x = -Math.sin(time * 3) * 0.2;

                // Nouvelle cible si atteint
                if (robotGroup.position.distanceTo(targetPosition) < 0.5) pickTargetOnCurrentSide();

                // Déclencheur parole (toutes les 7-10s approx)
                if (engagementTimer > 7 + Math.random()*3) {
                    robotState = 'engaged_speaking';
                    engagementTimer = 0;
                    // Choisir un message aléatoire
                    const msg = engagementMessages[Math.floor(Math.random() * engagementMessages.length)];
                    showBubble(msg, 5000);
                    // Retour au mouvement après 5s
                    setTimeout(() => { if(robotState === 'engaged_speaking') robotState = 'engaged_moving'; }, 5000);
                }
                // Déclencheur téléportation (changement de côté)
                if (teleportTimer > 15) {
                   // (Simplifié ici pour ne pas alourdir le code : il change juste de cible de l'autre côté)
                   currentSide = (currentSide === 'left') ? 'right' : 'left';
                   pickTargetOnCurrentSide();
                   // Petit effet "hop" pour marquer le changement
                   robotGroup.position.y += 0.5;
                   teleportTimer = 0;
                }
                break;

            case 'engaged_speaking':
                // Immobile, regarde la caméra, fait des gestes
                robotGroup.position.lerp(targetPosition, 0.005); // Freine doucement
                robotGroup.rotation.y *= 0.9; // Revient de face
                robotGroup.rotation.z *= 0.9;
                robotGroup.position.y += Math.sin(time * 3) * 0.001; // Flottement léger
                // Gestes aléatoires des bras
                rightArm.rotation.z = Math.sin(time * 4) * 0.3 + 0.3;
                leftArm.rotation.z = Math.cos(time * 3) * 0.3 - 0.3;
                break;
        }

        updateBubblePosition();
        renderer.render(scene, camera);
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
