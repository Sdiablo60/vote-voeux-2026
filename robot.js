import * as THREE from 'three';

// =========================================================
// 🟢 CONFIGURATION ROBOT (RETOUR AUX BASIQUES)
// =========================================================
const config = window.robotConfig || { mode: 'attente', titre: 'Événement', logo: '' };

const DUREE_LECTURE = 6000; 
const VITESSE_MOUVEMENT = 0.015; // Mouvement doux
const ECHELLE_BOT = 0.75; // Taille originale rétablie

// LIMITES ECRAN (Reste visible sans aller sur le texte)
const X_MAX_SCREEN = 12.0; 
const X_SAFE_CENTER = 6.5; 

// BANQUES DE TEXTES
const TEXTS_ATTENTE = [
    "Clap-E est prêt !", "Je scanne la salle... Tout est OK.", 
    "N'oubliez pas de voter !", "Quelle belle ambiance ce soir.",
    "Bip Bop... Je suis votre serviteur.", "Préparez-vous !",
    "Je garde un œil sur vous."
];
const TEXTS_VOTE_OFF = ["Les votes sont clos.", "Calcul en cours...", "Patience...", "Le résultat arrive."];
const TEXTS_PHOTOS = ["Souriez !", "Envoyez vos photos !", "Photo time !", "Je veux voir vos sourires !"];

let currentTextBank = config.mode === 'vote_off' ? TEXTS_VOTE_OFF : (config.mode === 'photos' ? TEXTS_PHOTOS : TEXTS_ATTENTE);

// --- CSS BULLES ---
const style = document.createElement('style');
style.innerHTML = `
    .robot-bubble-base { position: fixed; padding: 15px 25px; color: black; font-family: 'Arial', sans-serif; font-weight: bold; font-size: 20px; text-align: center; z-index: 6; pointer-events: none; transition: opacity 0.3s, transform 0.3s; transform: scale(0.9); max-width: 300px; width: max-content; }
    .bubble-speech { background: white; border-radius: 30px; border: 4px solid #E2001A; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }
    .bubble-speech::after { content: ''; position: absolute; bottom: -12px; left: 50%; transform: translateX(-50%); border-left: 10px solid transparent; border-right: 10px solid transparent; border-top: 15px solid #E2001A; }
`;
document.head.appendChild(style);

function launchFinalScene() {
    ['robot-container', 'robot-canvas-floor', 'robot-canvas-bot', 'robot-bubble'].forEach(id => { const el = document.getElementById(id); if (el) el.remove(); });
    
    const canvasBot = document.createElement('canvas'); canvasBot.id = 'robot-canvas-bot';
    document.body.appendChild(canvasBot);
    canvasBot.style.cssText = `position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 5; pointer-events: none; background: transparent;`;

    const bubbleEl = document.createElement('div'); bubbleEl.id = 'robot-bubble';
    document.body.appendChild(bubbleEl);
    
    initThreeJS(canvasBot, bubbleEl);
}

function initThreeJS(canvasBot, bubbleEl) {
    let width = window.innerWidth, height = window.innerHeight;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 100); 
    camera.position.set(0, 0, 12);

    const renderer = new THREE.WebGLRenderer({ canvas: canvasBot, antialias: true, alpha: true });
    renderer.setSize(width, height); renderer.setPixelRatio(window.devicePixelRatio);

    window.addEventListener('resize', () => { 
        const w = window.innerWidth, h = window.innerHeight;
        camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h);
    });

    // LUMIERES
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2); scene.add(ambientLight);
    const spotLight = new THREE.SpotLight(0xffffff, 1.5); spotLight.position.set(10, 20, 10); scene.add(spotLight);

    // ==========================================
    // 🤖 CONSTRUCTION DU ROBOT ORIGINAL (Clap-E v1)
    // ==========================================
    const robotGroup = new THREE.Group(); 
    robotGroup.scale.set(ECHELLE_BOT, ECHELLE_BOT, ECHELLE_BOT);
    
    // Matériaux Originaux
    const whiteMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 });
    const blackMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.2 });
    const neonMat = new THREE.MeshBasicMaterial({ color: 0x00ffff }); // Bleu Cyan original

    // Tête & Visage
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.85, 32, 32), whiteMat); head.scale.set(1.4, 1.0, 0.75);
    const face = new THREE.Mesh(new THREE.SphereGeometry(0.78, 32, 32), blackMat); face.position.z = 0.55; face.scale.set(1.25, 0.85, 0.6); head.add(face);
    
    // Yeux (Torus originaux)
    const eyeL = new THREE.Mesh(new THREE.TorusGeometry(0.12, 0.035, 8, 16, Math.PI), neonMat); eyeL.position.set(-0.35, 0.15, 1.05); head.add(eyeL);
    const eyeR = eyeL.clone(); eyeR.position.x = 0.35; head.add(eyeR);
    
    // Bouche
    const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.035, 8, 16, Math.PI), neonMat); mouth.position.set(0, -0.15, 1.05); mouth.rotation.z = Math.PI; head.add(mouth);
    
    // Corps
    const body = new THREE.Mesh(new THREE.SphereGeometry(0.65, 32, 32), whiteMat); body.position.y = -1.1; body.scale.set(0.95, 1.1, 0.8);
    
    // Bras (Capsules originales)
    const armLGroup = new THREE.Group(); armLGroup.position.set(-0.9, -0.8, 0); 
    const armL = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.4, 8, 16), whiteMat); armL.position.y = -0.2; 
    const handL = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), whiteMat); handL.position.y = -0.5; 
    armLGroup.add(armL); armLGroup.add(handL);
    
    const armRGroup = new THREE.Group(); armRGroup.position.set(0.9, -0.8, 0);
    const armR = new THREE.Mesh(new THREE.CapsuleGeometry(0.1, 0.4, 8, 16), whiteMat); armR.position.y = -0.2;
    const handR = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), whiteMat); handR.position.y = -0.5;
    armRGroup.add(armR); armRGroup.add(handR);

    // Assemblage
    robotGroup.add(head);
    robotGroup.add(body);
    robotGroup.add(armLGroup);
    robotGroup.add(armRGroup);
    
    scene.add(robotGroup);

    // --- LOGIQUE D'ANIMATION CALME ---
    let time = 0;
    let targetPos = new THREE.Vector3(0, 0, 0);
    let bubbleTimer = 0;
    let isWaving = false;

    // Position Initiale
    robotGroup.position.set(-20, 0, 0); // Hors champ gauche

    function pickTarget() {
        const side = Math.random() > 0.5 ? 1 : -1;
        const x = side * (X_SAFE_CENTER + Math.random() * (X_MAX_SCREEN - X_SAFE_CENTER));
        // Y reste proche de 0 ou monte un peu pour "flotter"
        const y = Math.sin(Date.now() * 0.001) * 2; 
        return new THREE.Vector3(x, y, 0);
    }

    targetPos = new THREE.Vector3(0, 0, 0); // Premier point : Centre (mais décalé par sécurité)

    function showBubble(txt) {
        if(!txt) return;
        bubbleEl.innerHTML = txt;
        bubbleEl.className = 'robot-bubble-base bubble-speech';
        bubbleEl.style.opacity = 1; bubbleEl.style.transform = "scale(1)";
        setTimeout(() => { bubbleEl.style.opacity = 0; bubbleEl.style.transform = "scale(0.9)"; }, 4000);
    }

    function animate() {
        requestAnimationFrame(animate);
        time += 0.02;

        // 1. Mouvement Fluide (Lerp)
        robotGroup.position.lerp(targetPos, VITESSE_MOUVEMENT);
        
        // 2. Légère oscillation (Respiration/Vol stationnaire)
        robotGroup.position.y += Math.sin(time * 2) * 0.005;
        robotGroup.rotation.z = Math.sin(time) * 0.05; // Balancement léger

        // 3. Orientation regard caméra
        robotGroup.lookAt(camera.position.x, camera.position.y, camera.position.z + 10); // Regarde devant

        // 4. Gestion Cible
        if (robotGroup.position.distanceTo(targetPos) < 1.5) {
            targetPos = pickTarget();
        }

        // 5. Animation Bras (Coucou aléatoire)
        if (Math.random() < 0.005) isWaving = true;
        
        if (isWaving) {
            armRGroup.rotation.z = Math.sin(time * 15) * 0.5;
            armRGroup.rotation.x = -0.5;
            if (Math.random() < 0.02) { isWaving = false; armRGroup.rotation.set(0,0,0); }
        } else {
            armLGroup.rotation.z = Math.sin(time * 2) * 0.1;
            armRGroup.rotation.z = -Math.sin(time * 2) * 0.1;
        }

        // 6. Parole
        if (time > bubbleTimer) {
            showBubble(currentTextBank[Math.floor(Math.random() * currentTextBank.length)]);
            bubbleTimer = time + 10 + Math.random() * 10;
        }

        // Mise à jour Bulle
        if (bubbleEl.style.opacity > 0) {
            const headPos = robotGroup.position.clone(); headPos.y += 1.8; headPos.project(camera);
            const x = (headPos.x * .5 + .5) * window.innerWidth;
            const y = (headPos.y * -.5 + .5) * window.innerHeight;
            bubbleEl.style.left = (x - bubbleEl.offsetWidth / 2) + 'px';
            bubbleEl.style.top = (y - bubbleEl.offsetHeight - 20) + 'px';
        }

        renderer.render(scene, camera);
    }
    
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', animate);
    else animate();
}
if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', launchFinalScene); } else { launchFinalScene(); }
